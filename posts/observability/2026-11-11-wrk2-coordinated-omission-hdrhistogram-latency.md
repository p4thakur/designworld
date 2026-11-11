---
date: 2026-11-11
company: wrk2 (Gil Tene)
topic: Coordinated Omission - closed-loop load generators stop sending during a server stall, so the stall vanishes from p99; wrk2 fixes it by recording latency from the planned (constant-rate) start time.
category: observability
post_type: structured
opening_style: shared_pain_point
slug: wrk2-coordinated-omission-hdrhistogram-latency
---

## Sources

- GitHub, giltene/wrk2 [README.md](https://github.com/giltene/wrk2/blob/master/README.md) - primary: "A note about wrk2's latency measurement technique", Example 2 (1.4 s ^Z on httpd, -t2 -c100 -R2000, 30 s): corrected p50 8.61 ms / p99 1.27 s vs uncorrected p50 3.02 ms / p99 6.04 ms / p99.9 1.41 s, Total count = 39500 in both histograms; +/- ~1 ms accuracy from OS sleep behavior.
- GitHub, giltene/wrk2 [src/wrk.c](https://github.com/giltene/wrk2/blob/master/src/wrk.c) - primary: `usec_to_next_send` (next_start_time = thread_start + complete / throughput), `catch_up_throughput = throughput * 2`, `response_complete` recording `now - expected_latency_start` into latency_histogram and actual timing into u_latency_histogram.
- GitHub, giltene/wrk2 [src/wrk.h](https://github.com/giltene/wrk2/blob/master/src/wrk.h) - primary: `CALIBRATE_DELAY_MS 10000`.

**Key primary-source detail:** both histograms in Example 2 hold the exact same 39,500 requests. Nothing is dropped; only the point where the stopwatch starts differs, and that alone moves p99 from 6.04 ms to 1.27 s. Also: wrk2 catches up after a stall at exactly 2x the planned per-connection rate.

Derived (author's arithmetic, not stated in the README): ~2,800 requests planned during the stall (1.4 s x 2,000/s); ~100 in-flight requests (one per connection) / 39,500 = ~0.25%, which matches the uncorrected histogram jumping only at p99.9.

---

## LinkedIn Post

Every load test has the same blind spot: when the server freezes, the load generator politely stops asking. So the freeze barely shows up in your p99.

Gil Tene's wrk2 README has the cleanest demo of this I know. One run, 100 connections, 2,000 requests/sec for 30 seconds. Midway, he hits ^Z on the Apache process and pauses it for about 1.4 seconds.

Same run, same server, same 39,500 recorded requests, two histograms:

Measured from when each request was actually sent: p50 3.02 ms, p99 6.04 ms.
Measured from when it should have been sent: p50 8.61 ms, p99 1.27 s.

Same data. One p99 is over 200x the other.

The root cause is how classic load generators like wrk (as of 2014) time a request: from the first byte sent to the full response. That sounds right. But each connection only sends its next request after the previous one returns. During the stall, each of the 100 connections has exactly one request in flight. Those 100 requests record ~1.4 s. The ~2,800 requests the plan said to send during that window (1.4 s x 2,000/s) are never sent on time, so they are never timed. 100 out of 39,500 is about 0.25%, which is why the uncorrected histogram stays at 6 ms through p99 and only jumps to 1.41 s at p99.9.

Tene calls this Coordinated Omission. The tester coordinates with the server to skip measurement exactly when things are worst.

The fix in wrk2 is not fancier sampling. It is a schedule. You pass -R for a target rate, and each connection gets a plan: request n should start at thread_start + n / throughput. Latency is recorded as now minus that planned start, not the actual send time. When a connection falls behind, it sends at catch_up_throughput, set to 2x the normal rate in the source, until it is back on plan, and those late requests carry their queueing delay into the histogram.

A few details only show up in the code. Calibration runs for 10 seconds (CALIBRATE_DELAY_MS = 10000) and is then discarded, so short runs say little. Both histograms are HdrHistograms, so every sample is recorded without loss. The README is also honest that timing is only accurate to about +/- 1 ms because of OS sleep behavior.

The lesson is bigger than benchmarking. Any latency metric that measures from "when I started the work" instead of "when the user asked" will hide queueing. That includes a lot of server-side middleware timers.

Your users don't wait from the moment you start. They wait from the moment they asked.

#Observability #Performance #SystemDesign #Latency

---

## Twitter Version

Your load test has a blind spot: when the server freezes, the load generator stops asking.

wrk2 README demo: 100 connections, 2,000 req/s, Apache paused ~1.4 s with ^Z.

Same 39,500 requests, two stopwatches:
Timed from actual send: p99 6.04 ms
Timed from planned send: p99 1.27 s

Why: each connection waits for its response before sending the next. During the stall, only 100 requests are in flight. The ~2,800 that should have gone out are never timed.

Gil Tene calls it Coordinated Omission. wrk2's fix: a constant-rate plan, latency = now - planned start, catch up at 2x rate.

Users wait from when they asked, not from when you started.

---

## Diagram

See `2026-11-11-wrk2-coordinated-omission-hdrhistogram-latency.excalidraw` (before/after comparison: same run, two stopwatches, percentile ladder side by side; color = stopwatch, not good/bad).
