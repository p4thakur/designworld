---
date: 2026-10-08
company: Netflix
topic: Hystrix's static thresholds replaced by adaptive concurrency limits borrowed from TCP congestion control (Vegas, Gradient2).
category: stability
post_type: confessional
opening_style: cold_fact
slug: netflix-hystrix-to-adaptive-concurrency-limits
---

## Sources

- GitHub, [Netflix/Hystrix README](https://github.com/Netflix/Hystrix) - primary: maintenance-mode notice, final release 1.5.18, "more adaptive implementations that react to an application's real time performance", resilience4j for new projects.
- GitHub, [Netflix/concurrency-limits README](https://github.com/Netflix/concurrency-limits) - primary: Little's Law framing, TCP congestion window analogy, Vegas queue estimate and alpha/beta thresholds, Gradient2 long/short average design, why stress-test limits go stale.
- Netflix Tech Blog, [Performance Under Load](https://netflixtechblog.medium.com/performance-under-load-3e6fa9a60581) - primary announcement; only its existence and framing were confirmed via search (medium.com blocked by egress policy).

**Note on sourcing:** the two GitHub READMEs were read directly. Numbers not in those READMEs were left out.

**Key primary-source detail:** Gradient2 exists because minimum-latency baselines (used by Vegas) drift and bias, so the fix is comparing long- and short-term averages rather than trusting one best-ever sample.

---

## LinkedIn Post

Hystrix is in maintenance mode. Netflix's own README says so, and says why: the focus moved to "more adaptive implementations that react to an application's real time performance."

Hystrix was the circuit breaker that taught a generation of engineers to protect a service from its dependencies. It worked by configuration: thread pool sizes, timeouts, error thresholds. Someone picked those numbers, usually after a load test, and they were right on the day they were picked.

Then the fleet auto-scaled, a dependency got a new release, an instance type changed. The tipping point moved and the numbers didn't. Netflix's concurrency-limits README puts the problem plainly: a limit derived from a stress test goes stale quickly in an auto-scaling system, and a concurrency limit is hard to set because you'd need to understand the hardware and how it scales.

So the next idea wasn't a better number. It was no number at all.

Little's Law says concurrency equals throughput times latency. Every service has a true limit set by some hard resource, CPU cores for example, and past that limit extra requests don't get served faster. They queue, and latency is the first thing to show it.

Netflix borrowed from TCP. Each node treats its concurrency limit like a congestion window and estimates it live. The Vegas algorithm compares the best latency ever seen against the latest sample, estimates the queue as L x (1 - minRTT / sampleRTT), and nudges the limit up by 1 when the queue is under alpha (2-3 requests) or down by 1 when it's over beta (4-6). Gradient2 goes further because a minimum-latency baseline drifts: it compares a long-term and a short-term moving average and cuts hard when the gap persists.

Nobody tunes it. The service finds its own ceiling and keeps finding it as the ceiling moves.

Hystrix wasn't wrong. It encoded the best answer available: ask a human for the number. What changed is that the number stopped holding still.

#SystemDesign #Resilience #Netflix #DistributedSystems

(2004 characters)

---

## Twitter Version

Hystrix is in maintenance mode. Netflix's README says the focus moved to "more adaptive implementations that react to an application's real time performance."

Hystrix ran on configured numbers: pool sizes, timeouts, thresholds, picked after a load test. Auto-scaling and new releases moved the real limit. The numbers stayed.

The replacement, concurrency-limits, has no number. Each node treats its limit like a TCP congestion window.

Vegas: queue = L x (1 - minRTT/sampleRTT). Under 2-3, limit +1. Over 4-6, limit -1. Gradient2 compares long and short moving averages so a drifting latency baseline doesn't fool it.

Hystrix wasn't wrong. It asked a human for the number. The number stopped holding still.

---

## Diagram

See `2026-10-08-netflix-hystrix-to-adaptive-concurrency-limits.excalidraw` (timeline: static limit goes stale as the real ceiling moves, vs adaptive limit tracking it).
