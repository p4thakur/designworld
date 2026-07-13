<!-- sources -->
<!-- Primary: -->
<!--   Lyft Engineering Blog, "Announcing Envoy: C++ L7 proxy and communication bus" (Matt Klein) -->
<!--   URL: https://eng.lyft.com/announcing-envoy-c-l7-proxy-and-communication-bus-92520b6c8191 -->
<!--   Lyft Engineering Blog, "Envoy joins the CNCF" (Matt Klein) -->
<!--   URL: https://eng.lyft.com/envoy-joins-the-cncf-dc18baefbc22 -->
<!-- Note: direct fetch of eng.lyft.com and mattklein123.dev returned HTTP 403 under this session's egress -->
<!-- policy (same class of gateway-level denial hit on the DoorDash and Backblaze posts). Facts below were -->
<!-- cross-checked across multiple independent search-result excerpts that quote the primary Lyft blog posts -->
<!-- directly, plus corroborating conference/press material covering the same story: -->
<!--   InfoQ, "Q&A with Matt Klein on Creating Envoy at Lyft" (2017) — https://www.infoq.com/news/2017/01/lyft-envoy/ -->
<!--   InfoQ, "Envoy Service Mesh Case Study: Mitigating Cascading Failure at Lyft" — https://www.infoq.com/articles/envoy-service-mesh-cascading-failure/ -->
<!--   Matt Klein, "5 years of Envoy OSS" — https://mattklein123.dev/2021/09/14/5-years-envoy-oss/ -->
<!--   Lyft Engineering Blog / SREcon17 Americas, Matt Klein, "Lyft's Envoy: Experiences Operating a Large Service Mesh" -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. When Matt Klein joined Lyft in May 2015, the company had already deployed 30+ microservices, on a fairly -->
<!--    standard stack for the time: AWS ELBs for edge load balancing, plus a "mishmash" of hand-rolled, -->
<!--    per-language client libraries (PHP, Python, etc.) for service-to-service calls, each with its own retry -->
<!--    logic and its own stats/logging implementation. -->
<!-- 2. ELB and CloudWatch could not report p50/p99 latency for service calls. When a request failed or was slow, -->
<!--    engineers had no reliable way to tell whether the problem was the client library, the network, or the -->
<!--    downstream service — the network had effectively become a black box. Developers grew wary of putting -->
<!--    synchronous service calls in high-traffic critical paths because failures were sporadic and hard to -->
<!--    diagnose. -->
<!-- 3. As the service count grew, so did exposure to cascading failure / accidental internal denial-of-service: -->
<!--    a single slow or failing downstream could trigger a retry storm from all its callers, taking down -->
<!--    services that were otherwise healthy. -->
<!-- 4. Lyft's fix was Envoy: an out-of-process C++ proxy deployed as a sidecar next to every service, giving -->
<!--    identical stats, logging, tracing, service discovery, retries, timeouts, and circuit breaking regardless -->
<!--    of the application's language. Per Lyft's cascading-failure case study, the specific mitigation for retry -->
<!--    storms is aggressive circuit breaking on retry volume — capping concurrent retries/connections a sidecar -->
<!--    will allow into a struggling service, so failures degrade instead of compounding. -->
<!-- 5. Development took roughly a year and a half. By early summer 2016 — around the September 2016 -->
<!--    open-source announcement — Envoy was fully deployed at Lyft, forming a mesh between over 100 services and -->
<!--    transiting millions of requests per second. By September 2017, when Lyft donated Envoy to the CNCF, it -->
<!--    ran on thousands of nodes across those 100+ services, aggregating over 2 million requests per second and -->
<!--    powering every system at Lyft. Envoy graduated to a top-level CNCF project in November 2018 and became -->
<!--    the data plane underneath Istio and AWS App Mesh. -->

# Lyft Had 30 Microservices and Was Already Afraid of Its Own Network. That Fear Built Envoy.

**Date:** 2026-07-13
**Company:** Lyft
**Category:** microservices
**Post type:** narrative
**Opening style:** mid_scene
**Slug:** lyft-envoy-service-mesh-origin
**Character count (LinkedIn):** ~2,420

---

## LinkedIn Post

By 2015, Lyft had about 30 microservices — not a lot, even by that year's standards — and its own engineers were already wary of putting a single service call in a critical path. Not because the services were slow. Because when a call failed, nobody could say why.

The stack was ordinary for the time: AWS ELBs out front, and behind them a mishmash of hand-rolled client libraries — one in PHP, one in Python — each with its own retry logic, its own logging, its own idea of what a "stat" even meant. ELB and CloudWatch couldn't report p50 or p99 latency at all. When a request was slow, there was no way to see where the time went: client library, network, or the service on the other end. The network had quietly become a black box, and every language spoke a different dialect of it.

Growth made this worse, not better. More services meant more chances for one struggling dependency to trigger a retry storm — every caller hammering it at once, pulling down services that were otherwise fine. It's the standard failure mode of microservices at scale, and Lyft was hitting it early, with barely 30 services.

The fix wasn't a better library. It was getting out of the library business entirely. Envoy runs as a separate process next to every service — a sidecar — so retries, timeouts, service discovery, and stats look identical no matter what language the app is written in. Crucially, it can cap how many concurrent retries a struggling downstream is allowed to absorb, so a slow dependency degrades instead of dragging the whole mesh down with it.

It took about a year and a half to build. By the September 2016 open-source launch, Envoy was already meshing over 100 services and moving millions of requests a second. A year later, when Lyft donated it to the CNCF, that had grown to thousands of nodes and 2 million-plus requests a second — every system at Lyft, routed through it. Istio and AWS App Mesh would later build on Envoy as their own data plane.

The sidecar didn't make the network simple. It added a proxy hop to every single call in the system. What it did was move the complexity somewhere everyone could see, instrument once, and fix in one place — instead of copy-pasted into thirty different client libraries, in two different languages, each drifting further from the others.

#SystemDesign #ServiceMesh #Envoy #Microservices #Lyft

---

## Twitter / X Version

1/ By 2015 Lyft had about 30 microservices, and its own engineers were already wary of putting a single service call in a critical path. Not because it was slow — because when it failed, nobody could say why.

2/ The stack was ordinary: AWS ELBs plus a pile of per-language client libraries (PHP, Python...), each with its own retries, its own logging. ELB/CloudWatch couldn't even report p50/p99 latency. The network had quietly become a black box.

3/ Growth made it worse: one struggling dependency could trigger a retry storm that pulled down services that were otherwise fine. Classic microservices failure mode — Lyft hit it with barely 30 services.

4/ The fix wasn't a better library. Lyft built Envoy: a sidecar proxy next to every service, language-agnostic, uniform stats/retries/timeouts, and able to cap concurrent retries so a slow dependency degrades instead of cascading.

5/ ~1.5 years to build. Sept 2016 open-source launch: 100+ services meshed, millions of req/sec. A year later: thousands of nodes, 2M+ req/sec, every system at Lyft. Istio and AWS App Mesh later adopted Envoy as their own data plane.

6/ The sidecar didn't make the network simple — it added a hop to every call. It just moved the complexity somewhere everyone could see and fix once, instead of copy-pasted into thirty client libraries.

---

## Excalidraw Diagram

**File:** 2026-07-13-lyft-envoy-service-mesh-origin.excalidraw
**Type:** Sequence flow, before/after side by side (narrative) — a request's path through Service A → client layer → Service B, shown for the pre-Envoy world and the post-Envoy world, with the failure/black-box point called out on the left and the retry-cap fix called out on the right.
**Color scheme:** Amber for the pre-Envoy world (not a villain — a normal stack for a 30-service company in 2015), violet for Envoy and the post-sidecar world, red only for the single "black box" failure callout, emerald reserved for the results bar. No red/green good/bad pairing across the whole diagram.
**Screenshottable stat:** "30 services (2015) → 100+ services meshed, millions of req/sec (Sept 2016) → thousands of nodes, 2M+ req/sec, every system at Lyft (Sept 2017, CNCF). Istio and AWS App Mesh later adopted Envoy as their own data plane."

### Layout

```
Title: "Lyft Had 30 Microservices and Was Already Afraid of Its Own Network. That Fear Built Envoy."
Subtitle: "Before Envoy: a black-box network and a client library per language. After: one sidecar, uniform everywhere, retries capped before they cascade."

[BEFORE ENVOY — 2015, ~30 services]              [AFTER ENVOY — Sept 2016 launch, 100+ services meshed]
Service A (Python)                                Service A (any language)
   |                                                  |
Python client lib                                 Envoy sidecar — uniform stats
(own retries, own stats)                             |
   |                                               Envoy sidecar — retries capped,
AWS ELB                                            circuit breaker before cascade
   |  ⚠ no p50/p99 here                               |
   |  failure = black box                          Service B (any language)
Service B (PHP)

Every language: its own retry logic, its own      Same sidecar regardless of app language. A
stats. ELB/CloudWatch can't show p50/p99. Devs    struggling downstream degrades — Envoy caps
avoid critical-path service calls — nobody can    concurrent retries into it — instead of every
tell why a call failed.                           caller's retry storm taking it fully down.

[RESULT — screenshottable]
30 services (2015) → 100+ services meshed, millions of req/sec (Sept 2016) → thousands of nodes,
2M+ req/sec, every system at Lyft (Sept 2017, CNCF). Istio and AWS App Mesh later adopted Envoy
as their own data plane.
```
