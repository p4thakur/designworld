<!-- sources -->
<!-- Primary: -->
<!--   Paul Tarjan (Stripe), "Scaling your API with rate limiters" — https://stripe.com/blog/rate-limiters -->
<!--   Same post, full text + code mirrored as a gist by the author — -->
<!--     https://gist.github.com/ptarjan/e38f45f2dfe601419ca3af937fff574d (dated 2017-03-29) -->
<!-- Note: direct WebFetch of stripe.com/blog/rate-limiters returned HTTP 403 under this session's egress -->
<!-- policy (same class of gateway-level denial hit on prior posts in this series). The author's own gist -->
<!-- mirror of the same post — including the full Ruby reference implementation and raw Lua scripts — was -->
<!-- fetched directly and used as the primary source for every mechanism-level detail below. -->
<!-- Corroborating: -->
<!--   "This Is How Stripe Does Rate Limiting to Build Scalable APIs" (newsletter.systemdesign.one/p/rate-limiter) -->
<!--   Arpit Bhayani, LinkedIn post summarizing Stripe's 4-tier rate limiting -->
<!--     (linkedin.com/posts/arpitbhayani_did-you-know-stripe-has-4-tiers-of-rate-limiting-activity-7349414155197571072-dQJ1) -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Stripe runs 4 rate limiters in production, layered: (a) request rate limiter (token bucket, per API key), -->
<!--    (b) concurrent requests limiter (per API key), (c) fleet usage load shedder (same concurrency mechanism, -->
<!--    global key), (d) worker utilization load shedder (probabilistic, based on infra metrics). -->
<!-- 2. Token bucket: REPLENISH_RATE = 100 requests/sec, CAPACITY = 5x replenish rate = 500 tokens (5s of burst). -->
<!--    Two Redis keys per user (token count, last-refill timestamp); refill computed lazily at request time -->
<!--    (tokens = min(capacity, tokens + elapsed*rate)) rather than a running background timer per key. Read- -->
<!--    compute-write executes as a single atomic Redis Lua script (EVAL) to prevent races between concurrent -->
<!--    requests for the same key landing on different app nodes. Keys TTL after fill_time*2 (fill_time = -->
<!--    capacity/rate = 5s here, so TTL = 10s) so idle keys don't accumulate in Redis forever. -->
<!-- 3. Concurrent requests limiter: TTL/staleness window = 60s, CAPACITY = 100 concurrent requests per user. -->
<!--    Implemented as a Redis sorted set keyed per user, storing each in-flight request's unique ID scored by -->
<!--    its start timestamp. A Lua script first runs ZREMRANGEBYSCORE to evict entries older than the staleness -->
<!--    window (so a request whose process crashed before it could signal completion doesn't hold its slot -->
<!--    forever), then checks set cardinality against the cap, then ZADDs the new request atomically. -->
<!-- 4. Fleet usage load shedder: reuses the exact same sorted-set concurrency-limiter mechanism, but keyed -->
<!--    globally instead of per-user, to catch aggregate fleet-wide overload even when every individual customer -->
<!--    is within their own limits. Returns HTTP 503 once triggered. -->
<!-- 5. Worker utilization load shedder: probabilistic shedding driven by live worker-utilization metrics. -->
<!--    Thresholds: END_OF_GOOD_UTILIZATION = 0.7, START_OF_BAD_UTILIZATION = 0.8. Timing constants: -->
<!--    NUMBER_OF_SECONDS_BEFORE_SHEDDING_STARTS = 28, NUMBER_OF_SECONDS_TO_SHED_ALL_TRAFFIC = 120 -- i.e. a -->
<!--    92-second ramp from 0% to 100% drop probability rather than a hard on/off cutoff at one utilization -->
<!--    number (a hard cutoff is prone to oscillation: shed traffic drops utilization back under the line, all -->
<!--    shed traffic returns at once, utilization spikes back over the line). -->
<!-- 6. Failure mode: Redis itself failing is handled by "failing open" -- requests are allowed through unchecked -->
<!--    rather than rejected -- observed at approximately a 0.01% failure rate in production. -->

# Stripe's Layered Rate Limiters: One Number Can't Catch Every Shape of Overload

**Date:** 2026-08-05
**Company:** Stripe
**Category:** stability
**Post type:** structured case study
**Opening style:** shared_pain_point
**Slug:** stripe-layered-rate-limiters
**Character count (LinkedIn):** ~2825

---

## LinkedIn Post

Every API serving thousands of independent tenants has the same problem: one customer's misbehaving integration can eat capacity meant for everyone else. Stripe published the mechanics of how they stop that, and it isn't one rate limit — it's four, stacked, each catching a different shape of overload.

Why not just cap requests-per-second per key and stop there? That number only bounds how fast requests start — it says nothing about requests already running. A customer under 100 req/s can still hit a slow endpoint enough to have dozens of calls in flight at once, each holding a worker for seconds, until the shared pool is gone and every other customer's fast requests queue behind it. Rate and concurrency are different shapes of the same resource; one number can't police both.

Layer one: a token bucket per API key. Instead of a background timer refilling every key forever, Stripe stores two values per key in Redis — token count, last-refill time — and computes the refill lazily, only when a request arrives: tokens = min(capacity, tokens + elapsed × rate). Read-compute-write is one atomic Lua script, so no two nodes can race the same bucket. Rate: 100/sec. Capacity: 500 — five seconds of burst, because real traffic arrives in clusters, not a metronome.

Layer two catches what a token bucket structurally can't: concurrency. Every in-flight request's ID sits in a Redis sorted set scored by start time. Cardinality is "how many of this key's requests are running now," capped at 100. Before checking that cap, the same script evicts anything older than 60 seconds — a request that crashes mid-flight and never signals "done" can't leak a slot forever.

Neither layer is fleet-aware when many customers are each fine but collectively too much. Two more act globally: one reuses the concurrency limiter with a shared key instead of per-user, shedding with a 503 past an aggregate cap. The last watches worker utilization and ramps shed probability 0% to 100% over 92 seconds instead of a hard cutoff — a hard line oscillates: load drops, utilization falls under it, shed traffic returns at once, spikes past it again. A gradual ramp damps that loop instead of triggering it.

The tradeoff none of this removes: every request now costs a Redis round trip. When Redis is unreachable, Stripe fails open — lets requests through rather than reject everyone during a blip. Measured at roughly 0.01% of requests: a bet that Redis's uptime beats an outage where the safety net takes down what it was protecting.

One limit catches one shape of overload. Real overload is too fast, too long, too many at once, and too much in aggregate, all at once — which is why the fix was four limiters, each matched to how the same resource actually runs out.

Sources in comments.

#SystemDesign #API #DistributedSystems #Stripe

---

## Twitter / X Version

1/ Every multi-tenant API has this problem: one customer's misbehaving script eats capacity meant for everyone else. Stripe published exactly how they stop it — and it isn't one rate limit. It's four, stacked, each catching a different shape of overload.

2/ Why not just cap requests/sec per key and stop there? That only bounds how fast requests *start*. A customer under the limit can still have dozens of slow requests running at once, each holding a worker for seconds — rate and concurrency are different resources, and one number can't police both.

3/ Layer 1: token bucket per key in Redis — 100/sec refill, 500 burst capacity. Refill is computed lazily at request time (tokens = min(cap, tokens + elapsed×rate)), not a background timer per key. Read-compute-write runs as one atomic Lua script so concurrent nodes can't race the same bucket.

4/ Layer 2: concurrency. Every in-flight request's ID sits in a Redis sorted set scored by start time; cardinality = requests running now, capped at 100. Before checking that cap, the script evicts anything older than 60s — so a crashed request can't leak a slot forever.

5/ Layers 3 and 4 work fleet-wide, not per-customer: a global version of the concurrency limiter sheds with a 503 past an aggregate cap, and a worker-utilization shedder ramps drop probability 0%→100% over 92 seconds instead of a hard cutoff — a hard line oscillates, a ramp damps it.

6/ What none of this removes: every request now costs a Redis round trip. When Redis itself is unreachable, Stripe fails open rather than reject everyone — measured at ~0.01% of requests. One limiter catches one failure shape. Real overload arrives in all of them at once.

---

## Excalidraw Diagram

**File:** 2026-08-05-stripe-layered-rate-limiters.excalidraw
**Type:** Sequence flow / architecture snapshot — a single request moving left to right through 4 independent limiter layers, each labeled with its own mechanism and numbers, with the two distinct reject paths (429 vs 503) shown underneath.
**Color scheme:** Four distinct colors (blue, purple, amber, red) for the four layers rather than a single accent — deliberately not a red=bad/green=good split, since no layer is "wrong"; each is a different, valid defense for a different failure shape. Red is reserved only for the reject-path captions, where it's actually marking a rejection.
**Screenshottable stat:** "100 req/s token bucket, 500 burst · 100 concurrent requests per key · 92-second shed ramp (28s→120s) · fails open at ~0.01% of requests."

### Layout

```
Title: "Stripe's Layered Rate Limiters: One Number Can't Catch Every Shape of Overload"
Subtitle: "A request moving through 4 independent limiters, each matched to a different way the same worker pool runs out"

[BOX 1 — blue, "LAYER 1 — TOKEN BUCKET (per API key)"]
  Redis: token count + last-refill timestamp per key.
  Refill computed lazily at request time: tokens = min(cap, tokens + elapsed × rate)
  rate: 100/s, burst cap: 500 (5s)
  Read-compute-write = 1 atomic Redis Lua script

  --arrow-->

[BOX 2 — purple, "LAYER 2 — CONCURRENCY CAP (per API key)"]
  Redis sorted set: request ID → start timestamp.
  Cardinality = requests running now for this key. Cap: 100.
  Before checking cap, script evicts entries >60s old — a crashed request can't leak a slot forever.

  --arrow-->

[BOX 3 — amber, "LAYER 3 — FLEET LOAD SHEDDER (global)"]
  Same sorted-set mechanism, but ONE shared key instead of one per customer.
  Catches: many tenants each individually fine, collectively too much for the fleet.
  Past aggregate cap → 503.

  --arrow-->

[BOX 4 — red, "LAYER 4 — WORKER UTILIZATION SHEDDER (global)"]
  Probabilistic shed based on actual worker utilization.
  0.7 = good, 0.8 = bad.
  Ramps drop probability 0%→100% over 92s (28s grace, full shed by 120s) — a hard cutoff at one number oscillates; a ramp damps it.

[Below boxes 1-2]  "reject path: 429 Too Many Requests (per-key limits exceeded)"
[Below boxes 3-4]  "reject path: 503 Service Unavailable (fleet-wide shedding)"

[FOOTNOTE]
The tradeoff none of these four remove: every request now costs a Redis round trip before it's allowed to run.
When Redis itself is unreachable, Stripe fails open — lets requests through unchecked rather than reject everyone
during a Redis blip. Measured at roughly 0.01% of requests: a bet that Redis's own uptime beats an outage where
the safety net takes down what it was protecting.
```
