<!-- sources -->
<!-- Primary: -->
<!--   Netflix Technology Blog, "Zuul 2 : The Netflix Journey to Asynchronous, Non-Blocking Systems" (Apr 19, 2017) -->
<!--   URL: https://netflixtechblog.com/zuul-2-the-netflix-journey-to-asynchronous-non-blocking-systems-45947377fb5c -->
<!--   Netflix Technology Blog, "Curbing Connection Churn in Zuul" (Aug 2023) -->
<!--   URL: https://netflixtechblog.com/curbing-connection-churn-in-zuul-2feb273a3598 -->
<!--   Netflix Technology Blog, "Open Sourcing Zuul 2" (May 21, 2018) -->
<!--   URL: https://netflixtechblog.com/open-sourcing-zuul-2-82ea476cb2b3 -->
<!-- Note: direct WebFetch of netflixtechblog.com and medium.com/netflix-techblog returned HTTP 403 under this -->
<!-- session's egress policy (same recurring failure mode documented in earlier posts in this repo, e.g. the -->
<!-- 2026-07-18 Etsy post, 2026-07-22 Spotify post, and 2026-07-23 Instagram post). Facts below are cross-checked -->
<!-- across multiple independent WebSearch result excerpts that directly quote or closely paraphrase the three -->
<!-- primary netflixtechblog.com posts, corroborated by: -->
<!--   InfoQ, "Netflix Zuul 2: The Journey to Asynchronous, Non-blocking Systems" (Oct 2016) -->
<!--   https://www.infoq.com/news/2016/10/netflix-zuul-asynch-nonblocking -->
<!--   Arthur Gonigberg (former Netflix Zuul team engineer), "Zuul 2.0: The Journey to Non-Blocking" -->
<!--   https://arthur.gonigberg.com/2017/10/02/zuul-2-non-blocking/ -->
<!--   Netflix/zuul GitHub wiki, "How It Works 2.0" -->
<!--   https://github.com/Netflix/zuul/wiki/How-It-Works-2.0 -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Zuul is Netflix's edge gateway: the front door for all requests into Netflix's cloud, handling routing, -->
<!--    retries, filtering, and cross-region failover. Zuul 1 (running since ~2013) was built on the Java Servlet -->
<!--    model: one thread per connection, with I/O executed by a worker thread while the request thread blocks. -->
<!-- 2. The specific failure mode that motivated the rewrite: when backend service latency increased or client -->
<!--    devices retried after errors, the count of active connections and threads climbed together — each slow -->
<!--    backend call held a thread hostage longer, and retries added new incoming connections at the same moment -->
<!--    thread capacity was already shrinking (a retry storm compounding thread-pool exhaustion). -->
<!-- 3. Zuul 2 mechanism: async, non-blocking, built on Netty. Uses one event loop per CPU core rather than a -->
<!--    thread per connection; each event loop uses callbacks and, on Linux, Netty's EpollEventLoop (edge- -->
<!--    triggered, via JNI epoll syscall) for higher throughput than the generic NIO loop. Zuul also keeps a -->
<!--    separate outbound connection pool per host per event loop specifically to avoid inter-thread context -->
<!--    switching on the backend-calling side too. -->
<!-- 4. Measured production result (2017 post, after months in production) was NOT uniform across clusters: on -->
<!--    the Zuul cluster fronting Netflix's logging/analytics pipeline (write-heavy traffic, large requests, -->
<!--    small responses — an I/O-bound profile), Netty-based Zuul 2 measured roughly 25% higher throughput at -->
<!--    roughly 25% lower CPU utilization than blocking Zuul 1. On the cluster fronting the API service, which -->
<!--    does substantial on-box CPU work per request (metrics calculation, logging, request/response encryption -->
<!--    and compression), there was no efficiency gain — essentially equivalent capacity and CPU. -->
<!-- 5. Tradeoff explicitly named in the primary post: the async/callback-based system is "much more complex to -->
<!--    debug, code, and test" than the blocking model it replaced. -->
<!-- 6. By 2018 (Open Sourcing Zuul 2 post) Netflix's Cloud Gateway team operated 80+ clusters of Zuul 2 routing -->
<!--    to roughly 100 backend service clusters, over 1 million requests/second in aggregate. -->
<!-- 7. 2023 evolution ("Curbing Connection Churn in Zuul"): because each event loop keeps its own per-host -->
<!--    connection pool, total connection count scales as instances × event loops per instance × backend hosts — -->
<!--    a combinatorial multiplication worsened by autoscaling constantly opening and closing connections as -->
<!--    instances came and went. The fix: HTTP/2 multiplexing between Zuul and backend services (many logical -->
<!--    requests share one physical TCP connection) plus a subsetting algorithm so each Zuul instance connects to -->
<!--    only a bounded subset of backend hosts instead of all of them, while keeping load balancing even. Result: -->
<!--    peak connection counts dropped by roughly a factor of 10 across all three AWS regions Netflix operates -->
<!--    in; some individual Zuul shards saw a reduction of as much as 13 million connections at peak; tens of -->
<!--    millions of connections were eliminated in total, with no loss of resiliency or load-balancing quality. -->
<!-- Mechanism-level explanation of *why* an event loop is shaped like the "many concurrent slow waits" access -->
<!--   pattern (holding pending state as callback data on a fixed thread count, versus a thread blocked on I/O -->
<!--   holding an OS-scheduled stack for the whole wait) is standard event-loop/epoll internals knowledge, used -->
<!--   here to go one level deeper than either primary post, per the skill's sourcing guidance. -->

# Netflix's Zuul: Two Rewrites, Two Different Multiplications

**Date:** 2026-07-28
**Company:** Netflix
**Category:** microservices
**Post type:** structured
**Opening style:** shared_pain_point
**Slug:** netflix-zuul2-nonblocking-connection-churn
**Character count (LinkedIn):** ~2,900

---

## LinkedIn Post

Every reverse proxy has the same nightmare: a backend gets slow, and the thing meant to protect you from it runs out of capacity right along with it.

Zuul is the front door for every request into Netflix's cloud — routing, retries, filtering, region failover. Through 2013 it ran as Zuul 1: one thread per connection, built on the Servlet model. A worker thread grabs a connection and blocks until the backend call returns.

The failure mode: when a backend slowed down, every in-flight request held its thread hostage longer. Devices, seeing timeouts, retried — adding connections at the exact moment Zuul had the least spare thread capacity. Thread exhaustion and retry storms fed each other. Bigger pools don't fix this: you can only add so many OS threads before context-switching eats the gains, and no pool is big enough for retries stacking on an already-degraded backend.

Netflix rewrote it as Zuul 2: async, non-blocking, on Netty. Instead of a thread pinned to a connection for its whole lifetime, one event loop per CPU core (Linux's edge-triggered epoll underneath) cycles through thousands of connections, firing a callback only when a socket has data, stepping away instantly when a backend hasn't answered. A slow backend no longer parks a thread — one callback just fires later. The problem was shaped like "thousands of concurrent slow waits," and an event loop holds thousands of pending waits on a handful of threads, not thousands of threads each holding one wait.

The gain wasn't universal — the detail that makes this real. Fronting Netflix's logging pipeline (write-heavy, large requests, small responses), Netty-based Zuul measured roughly 25% higher throughput at 25% lower CPU. Fronting the API service, doing real on-box work per request (metrics, encryption, compression), there was no gain at all. An event loop only wins when the wait is I/O; CPU-heavy handler work still blocks the event-loop thread, same as before.

Not free either way: Netflix calls the callback-based system "much more complex to debug, code, and test." A stuck request no longer sits on a blocked thread with a clean stack trace — it's scattered across callback state.

The event loop fixed thread exhaustion. By 2023 a different multiplication caught up: each event loop keeps its own per-host pool, and instances × event loops × backend hosts multiplies out fast, worsened by autoscaling constantly opening and closing connections. The fix: HTTP/2 multiplexing between Zuul and backends, plus subsetting so each instance connects to only a bounded slice of hosts. Peak connections dropped roughly 10x across all three regions — some shards cut by up to 13 million connections at peak.

Two rewrites, same idea: the primitive that scales with traffic is whatever you multiply requests by. Fix threads, and the multiplication just moves to connections.

#SystemDesign #Netflix #APIGateway #DistributedSystems

---

## Twitter / X Version

Netflix's API gateway, Zuul, used to run one thread per connection. When a backend slowed down, every stuck request held its thread hostage — and retries piled more connections on top, right when thread capacity was lowest. Thread exhaustion feeding a retry storm.

Bigger thread pools don't fix that. You run out of OS threads before you run out of retries.

The fix: Zuul 2, rewritten on Netty. One event loop per CPU core, epoll underneath, callbacks instead of blocked threads. A slow backend just means a callback fires later — no thread parked waiting.

The catch: it only helped where the wait was I/O. On their logging-pipeline cluster: +25% throughput, -25% CPU. On the API cluster, which does real per-request work (encryption, compression), zero gain — CPU-bound work still blocks the event loop same as before.

And it's harder to debug: no more clean stack trace on a stuck request, just scattered callback state.

Fixing threads just moved the bottleneck. By 2023, connection count (instances × event loops × backend hosts) had exploded. Fix #2: HTTP/2 multiplexing + subsetting. Peak connections down ~10x, some shards cut by 13M.

The primitive that scales with traffic is whatever you multiply requests by. Fix one, and it moves to the next.

---

## Excalidraw Diagram

**File:** 2026-07-28-netflix-zuul2-nonblocking-connection-churn.excalidraw
**Type:** Two-phase migration timeline (structured case study) — left half shows the 2013→2017 thread-to-event-loop rewrite with its measured before/after numbers, right half shows the 2017→2023 connection-churn rewrite, unified by one mechanism callout underneath.
**Color scheme:** Rose/red for Zuul 1's blocking-thread failure mode (a real bottleneck, not a strawman), teal for the Zuul 2 non-blocking fix, blue for the measured I/O-bound vs. CPU-bound result split, amber for the second bottleneck (connection churn) that the first fix didn't touch, purple for its fix (H2 multiplexing + subsetting). Slate for the unifying mechanism explainer — deliberately not red/green, since both rewrites were correct engineering for the bottleneck they targeted.
**Screenshottable stat:** "Zuul 1 → Zuul 2: +25% throughput / −25% CPU on I/O-bound traffic, 0% gain on CPU-bound traffic. Zuul 2 → 2023 fix: peak connections down ~10x, some shards cut by 13M."

### Layout

```
Title: "Netflix's Zuul: Two Rewrites, Two Different Multiplications"
Subtitle: "2013: thread-per-connection · 2017: event-loop rewrite (Zuul 2) · 2023: connection-churn fix — same gateway, two ceilings"

PHASE 1 (2013 → 2017): THE THREAD BOTTLENECK

[ZUUL 1 — blocking]                 →        [ZUUL 2 — non-blocking]              [MEASURED RESULT]
Thread per connection. Backend               One event loop per CPU core,          Logging pipeline (I/O-bound):
slows → thread blocked longer →              Linux epoll underneath. Callback      +25% throughput, −25% CPU
device retries → more incoming               fires when a socket has data;
connections → fewer free threads.            a slow backend just delays a          API cluster (CPU-heavy per
Thread exhaustion feeds retry storm.         callback, never parks a thread.        request): 0% gain — event loop
                                                                                     only wins when the wait is I/O.

PHASE 2 (2017 → 2023): THE CONNECTION BOTTLENECK

[THE NEW MULTIPLICATION]                                    →        [THE FIX]
The event loop fixed threads, but each event                          HTTP/2 multiplexing (many logical requests
loop keeps its own per-host pool. instances ×                         share one TCP connection) + subsetting (each
event loops × backend hosts multiplies fast —                         instance only connects to a bounded slice of
worsened by autoscaling opening/closing                               backend hosts). Peak connections: −10x across
connections constantly.                                                all 3 regions, some shards cut by up to 13M.

[MECHANISM CALLOUT]
The primitive that scales with traffic is whatever you multiply requests by. Thread-per-connection multiplies by
concurrent slow waits — an event loop fixes that by holding waits as callback state, not threads. But the fix
introduces a new multiplication (instances × loops × hosts), which is why the same gateway needed a second rewrite.

Footer: Source: Netflix TechBlog, "Zuul 2: The Netflix Journey to Asynchronous, Non-Blocking Systems" (2017) and
"Curbing Connection Churn in Zuul" (2023).
```
