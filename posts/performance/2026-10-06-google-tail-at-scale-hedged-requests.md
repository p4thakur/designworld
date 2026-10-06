---
date: 2026-10-06
company: Google
topic: Google's "The Tail at Scale" (Dean and Barroso) — why fan-out turns a 1% slow server into a 63% slow request, and how hedged requests cut BigTable p99.9 from 1,800 ms to 74 ms for ~2% extra load.
category: performance
post_type: contrarian
opening_style: challenge_assumption
slug: google-tail-at-scale-hedged-requests
---

## Sources

- Jeffrey Dean and Luiz André Barroso, [The Tail at Scale](https://cacm.acm.org/research/the-tail-at-scale/), Communications of the ACM, 2013 — primary source: the fan-out arithmetic, hedged requests, tied requests, and the BigTable benchmark.
- Secondary summaries surfaced via search (Adrian Colyer's "morning paper", Java Code Geeks, DEV Community write-ups) — used only to cross-check the 63%, 10 ms, 1,800 ms → 74 ms and ~2% figures.

**Note on sourcing:** cacm.acm.org and most blog domains were blocked by this environment's egress policy, so the paper itself was not opened in this run. All figures were confirmed only through search-indexed excerpts and multiple secondary write-ups that agree with each other. Please re-check the figures against the paper before publishing, especially the benchmark setup (1,000-key read across 100 servers, hedge sent after 10 ms) and whether the paper's 74 ms is quoted at p99.9.

**Key primary-source detail:** the paper's 1% → 63% arithmetic is not about bad servers. Every server can be "99% fast" and the user-facing request is still slow most of the time, purely from fan-out.

---

## LinkedIn Post

Everyone says a 99% fast service is a fast service. Google's tail-latency paper shows why that stops being true the moment a request fans out.

Take a server where 1 request in 100 takes over a second. Fine. Now make one user request wait on 100 of those servers in parallel. The chance that at least one is slow is 1 - 0.99^100, about 63%. Nothing got worse. The system just multiplies the odds.

The obvious fix is to make the slow server not slow. In Dean and Barroso's paper, the authors argue that at this scale you often cannot. Garbage collection, background compaction, shared-resource contention and queueing all produce slowness that is intermittent and hard to remove one by one. So Google designed around it instead.

The contrarian move is the hedged request. Send the request to one replica. If it has not answered after a short delay, send the same request to a second replica, take whichever answer lands first, and cancel the other.

Sending duplicate requests sounds like what you do right before an outage. The paper's point is that the delay is the whole trick. Wait roughly as long as a healthy request takes (the 95th percentile), and only the slowest few percent ever trigger a second copy.

In their BigTable benchmark, reading 1,000 keys spread across 100 servers, hedging after a 10 ms delay cut the 99.9th percentile from 1,800 ms to 74 ms. The cost was about 2% more requests.

That asymmetry is the real lesson. You are not buying speed with capacity. You are buying it with a small amount of redundant work aimed only at the requests that were already going to hurt.

The paper goes further with tied requests: enqueue the request on two servers at once, each told about the other, so whichever starts first cancels its twin. No waiting for a timer at all.

Hedging has rules. The operation has to be safe to run twice. And it is not a cure for overload: if most requests are slow because you are out of capacity, most requests will hedge and you make it worse.

We default to treating latency as a bug to fix inside each component. At fan-out scale it is a statistic to manage across them.

#SystemDesign #DistributedSystems #Performance #TailLatency

**Character count: 2,181 / 3,000**

---

## Twitter / X Thread

1/ A server that is fast 99% of the time sounds fast. Put 100 of them behind one request and 63% of requests hit at least one slow server. 1 - 0.99^100.

2/ Google's "The Tail at Scale" argues you cannot fix every source of slowness: GC, compaction, contention, queueing. So design around it.

3/ Hedged requests: send to one replica, wait about the p95, then send the same request to a second. First answer wins, cancel the other.

4/ BigTable benchmark (1,000 keys, 100 servers, hedge after 10 ms): p99.9 went from 1,800 ms to 74 ms for roughly 2% extra requests.

5/ Catches: the operation must be safe to repeat, and hedging an overloaded system just adds load. Latency at fan-out scale is a statistic to manage, not a bug to fix.
