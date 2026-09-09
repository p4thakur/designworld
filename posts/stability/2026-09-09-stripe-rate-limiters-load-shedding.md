---
date: 2026-09-09
company: Stripe
topic: Four rate limiters, not one — token bucket, concurrency limiter, and two load shedders, where the last one had to be built to react slowly on purpose
category: stability
post_type: narrative
opening_style: specific_number
slug: stripe-rate-limiters-load-shedding
---

## Sources

- Stripe Engineering Blog: ["Scaling your API with rate limiters"](https://stripe.com/blog/rate-limiters) (Paul Tarjan, March 30, 2017)
- GitHub Gist by the post's author: ["0-rate-limiters.md"](https://gist.github.com/ptarjan/e38f45f2dfe601419ca3af937fff574d) — reference pseudocode for all four limiters
- Stripe Docs: ["Rate limits"](https://docs.stripe.com/rate-limits)
- System Design newsletter summary: ["This Is How Stripe Does Rate Limiting to Build Scalable APIs"](https://newsletter.systemdesign.one/p/rate-limiter)

**Key primary-source detail (not in most summaries):** The fourth limiter — the worker-utilization load shedder — isn't just a threshold trigger. It treats 0.7–0.8 utilization as a deliberate dead zone with no action, waits a fixed 28 seconds of sustained bad utilization before shedding any traffic, and changes its shedding amount as a derivative capped at 1/120th per second in either direction. The post is explicit about why: a shedder that reacts immediately creates its own feedback loop — shed hard, load drops, shedding turns off, load spikes back up, repeat — so the last line of defense against cascading failure had to be engineered to move slower than the failure it's defending against.

**Note on sourcing:** `stripe.com` was not reachable from this environment's network egress policy at write time. The specific numbers above — 100 req/s token bucket refill rate with a 500-request burst capacity, the 100 concurrent in-flight request cap per account, the 0.7/0.8 utilization dead zone, the 28-second delay before shedding starts, the 1/120th-per-second ramp cap, the Redis sorted-set implementation for both the concurrency limiter and the global load shedder, and the "fail open" policy on Redis unavailability — come from the author's own companion GitHub gist (identical implementation details to the blog post, published by the same engineer, Paul Tarjan) cross-checked against independent third-party summaries of the original post, rather than a single secondary source.

---

## LinkedIn Post

Stripe runs four different rate limiters in production. Only one of them limits how fast you can send requests.

The first is the one everyone builds: a token bucket per API key. 100 requests per second, a burst capacity of 500, tracked in Redis with two keys — tokens and a timestamp — refilled through an atomic Lua script. Go over it, get a 429. It solves exactly one failure mode: a client sending too many requests too fast.

It doesn't solve the next one. A client can stay under 100 req/s and still open 200 requests at once, each one slow, each one holding a worker hostage. So there's a second limiter: cap concurrent in-flight requests per account at 100, tracked with a Redis sorted set — drop in a random ID when a request starts, remove it when it finishes, reject if the set's too big before you add.

Neither protects the platform from itself. If one endpoint gets slow across every account at once — a downstream dependency, a bad deploy — no single customer is over their limit, but the fleet is drowning anyway. So the third limiter isn't scoped to a user at all. Same sorted-set trick, but against a global key, shedding low-priority traffic — analytics, reporting — before it touches charges and money movement. A 503, not a 429, because nobody did anything wrong.

The fourth one is where the real design problem shows up: what happens when the fix for overload becomes its own failure mode? Stripe's utilization-based shedder treats 0.7–0.8 worker utilization as a dead zone, waits 28 seconds of sustained bad utilization before shedding anything, and ramps the shedding amount up or down as a derivative capped at 1/120th per second. Not because caution is free — because a shedder that reacts instantly creates its own oscillation: shed hard, load drops, shedding turns off, load spikes right back, repeat forever.

Underneath all four: if Redis itself is unavailable, everything fails open. The system built to protect availability doesn't get to become the reason for the outage.

No customer did anything wrong at any of these four layers. Four different shapes of the same problem, four different tools, and a shedder that had to be taught patience — because speed was the thing that had been breaking it.

#Stripe #SystemDesign #RateLimiting #DistributedSystems

**Character count: ~2,290 / 3,000 ✓**
**First 140 chars (mobile hook):** "Stripe runs four different rate limiters in production. Only one of them limits how fast you can send requests." ✓

---

## Twitter / X Thread

1/ Stripe runs four different rate limiters in production. Only one of them limits how fast you can send requests.

2/ #1: token bucket per API key. 100 req/s refill, burst of 500, an atomic Lua script against two Redis keys. Solves one thing: a client sending too many requests too fast.

3/ #2: concurrency limiter. Max 100 in-flight requests per account, tracked in a Redis sorted set. Because you can stay under the rate limit and still open 200 slow requests at once.

4/ #3: a global load shedder. Same sorted-set trick, but scoped to the whole fleet — sheds analytics/reporting traffic before it touches charges. Returns 503, not 429, because no one broke a limit.

5/ #4 is the interesting one: a utilization shedder with a dead zone between 0.7 and 0.8, a 28-second delay before it sheds anything, and a ramp capped at 1/120th per second. React faster and the shedder starts oscillating on its own.

6/ Underneath all four: if Redis goes down, fail open. A system built to protect availability doesn't get to become the outage.

7/ Four failure shapes, four tools, and a shedder that had to be taught patience — because speed was what broke it in the first place.

---

## Diagram

See: `2026-09-09-stripe-rate-limiters-load-shedding.excalidraw`

Type: Sequence flow (narrative style, 4 stages, last stage emphasized as the failure point being defused)
Color scheme: Sky blue (token bucket) → Violet (concurrency limiter) → Gold (global shedder) → Green (utilization shedder, oversized callout) — no red/green good-bad pairing, palette and layout distinct from the last two stability posts
Key screenshottable number: 0.7–0.8 utilization dead zone, 28-second delay before shedding, ramp capped at 1/120th per second
