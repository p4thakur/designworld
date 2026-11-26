---
date: 2026-11-26
company: Prometheus (classic vs native histograms, histogram_quantile)
topic: A classic Prometheus histogram stores one counter series per fixed `le` bucket, and the boundaries are chosen at instrumentation time. `histogram_quantile()` finds the bucket that holds the requested rank and assumes the observations are spread evenly inside it, so the estimate is `bucketStart + (bucketEnd - bucketStart) * (rank / count)`. The error is therefore bounded only by the bucket's width. In the Prometheus docs' own example, every request takes about 220ms, but buckets at 200ms and 300ms produce a p95 of 295ms, right on a 300ms SLO. After a 100ms regression the true p95 is about 320ms and the estimate is 443ms. If the quantile falls in the +Inf bucket, the function returns the upper bound of the second-highest bucket, so a Go service on `DefBuckets` can never show a p99 above 10s. Native histograms (experimental in v2.40, November 2022, stable in v3.8, still opt-in to scrape until v4) use exponential buckets: the same two cases estimate 228ms and 323ms. The docs now open with "If you can, use native histograms."
category: observability
post_type: confessional
opening_style: specific_number
slug: prometheus-histogram-quantile-bucket-interpolation
---

## Sources

- prometheus/docs main, [docs/practices/histograms.md](https://raw.githubusercontent.com/prometheus/docs/main/docs/practices/histograms.md) ("Histograms and summaries"). Primary.
  - Opening: "The most important lesson to learn from this document is simple: If you can, use native histograms and prefer them over both classic histograms and summaries."
  - On the original model: "Historically, a sample in the Prometheus world was just a timestamped floating point value... On the one hand, this approach has worked quite well... On the other hand, it suffers from many limitations, especially when it comes to histograms. Thus, much later in Prometheus's lifetime, native histograms were introduced."
  - Quantile error example: request durations "almost all very close to 220ms". With classic buckets `{le="0.1"}`, `{le="0.2"}`, `{le="0.3"}`, `{le="0.45"}`, "The interpolation would estimate 295ms in this case... the classic histogram gives you the impression that you are very close to breaching it, but in reality you are still doing quite well." The native histogram with `NativeHistogramBucketFactor` 1.1 puts the spike in a bucket of roughly 210–229ms and estimates 228ms.
  - After "a fixed amount of 100ms" is added: the native bucket is 297–324ms with an estimate of 323ms, "an almost perfect guess". The classic estimate "is estimated to be 443ms, far away from the correct value close to 320ms."
  - Comparison table: classic histogram quantile error "is limited by the width of the bucket the quantile is located in". Required configuration: "Pick buckets suitable for the expected range of observed values and the desired queries."
  - On summaries: `avg(http_request_duration_seconds{quantile="0.95"}) // BAD!`, because averaging precomputed quantiles "yields statistically nonsensical values."
- prometheus/prometheus main, [docs/querying/functions.md](https://raw.githubusercontent.com/prometheus/prometheus/main/docs/querying/functions.md), `histogram_quantile()`. Primary. For classic histograms "it assumes a uniform distribution of observations within the bucket (also called _linear interpolation_)". Special case: "If a quantile is located in the highest bucket, the upper bound of the second highest bucket is returned." Native histograms with standard schemas use "exponential interpolation".
- prometheus/prometheus main, [promql/quantile.go](https://raw.githubusercontent.com/prometheus/prometheus/main/promql/quantile.go), `BucketQuantile`. Primary. `case b == len(buckets)-1: quantile = buckets[len(buckets)-2].UpperBound` and `quantile = bucketStart + (bucketEnd-bucketStart)*(rank/count)`.
- prometheus/client_golang main, [prometheus/histogram.go](https://raw.githubusercontent.com/prometheus/client_golang/main/prometheus/histogram.go). Primary. `var DefBuckets = []float64{.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10}`, with the comment "Most likely, however, you will be required to define buckets customized to your use case."
- prometheus/docs main, [docs/specs/native_histograms.md](https://raw.githubusercontent.com/prometheus/docs/main/docs/specs/native_histograms.md). Primary.
  - "Native histograms were introduced as an experimental feature in November 2022... The first version of the Prometheus server supporting native histograms was v2.40.0... Starting with v3.8.0, native histograms are supported as a stable feature. However, scraping native histograms still has to be activated explicitly via the `scrape_native_histograms` configuration setting... (From v4 on, both `scrape_native_histograms` and `send_native_histograms` will default to `true`.)"
  - Schema comment: "each bucket boundary is the previous boundary times 2^(2^-n)". Valid schemas are -4 to 8, plus -53 for custom buckets (NHCB). The suggested default bucket limit is 160.
  - "Interpolation within a bucket": "In classic histograms, this interpolation happens in a linear fashion. It is based on the assumption that observations are equally distributed within the bucket. In reality, this assumption might be far off."
- Not used: prometheus.io (including the 2026-02-14 blog post "Modernizing Prometheus: composite samples") was blocked by this session's network settings. Everything above was read from the GitHub source of the same pages.

**Key primary-source detail:** `histogram_quantile` has a hard ceiling. When the requested rank lands in the `+Inf` bucket, `BucketQuantile` returns `buckets[len(buckets)-2].UpperBound`, which is the second-highest boundary, not an estimate. With Go's `DefBuckets` that value is `10`. A service whose real p99 is 40 seconds graphs a flat p99 of exactly 10s.

Derived/interpretive (the author's reading, not stated verbatim by a source): "the bucket list is a guess about future latency, made on the day the metric was written" is the author's framing. The line that the 295ms reading would page someone is an inference from the docs' remark that the reading looks "very close to breaching" a 300ms SLO. The 40s example uses the documented highest-bucket rule. The docs do not discuss that specific case.

---

## LinkedIn Post

Every request took 220ms. Prometheus reported the p95 as 295ms, 5ms under a 300ms SLO.

That example comes from Prometheus's own documentation, and nothing in it is broken. It's how a classic histogram works.

A classic histogram is a set of counters, one per bucket boundary: le="0.2", le="0.3", and so on. That fit the original Prometheus model, where every sample was a single float. Buckets became ordinary time series, so they could be summed across instances, which summaries can't do. For years that was the right trade.

The cost is that you pick the boundaries when you write the instrumentation, before you have seen any traffic.

At query time, histogram_quantile finds the bucket that holds the 95th-percentile rank and assumes the requests inside it are spread evenly. The estimate is the bucket start plus its width times rank over count. With every request at 220ms, the 95th-percentile rank lands 95% of the way through the 200–300ms bucket. That's 295ms. The real value could be anywhere from 200 to 300, and the function has no way to tell.

The docs then add 100ms to every request. The real p95 becomes about 320ms. The estimate becomes 443ms.

There is also a ceiling. If the rank lands in the +Inf bucket, the function returns the second-highest boundary. Go's default buckets end at 10, so a service with a 40-second p99 graphs a flat 10s.

The fix took years. Native histograms shipped as experimental in v2.40 in November 2022 and became stable in v3.8. Their buckets are exponential, each boundary the previous one times 2^(2^-schema), so you choose a resolution instead of boundaries. On the same two cases they estimate 228ms and 323ms. Scraping them is still opt-in until v4.

The histograms page now opens with: "If you can, use native histograms and prefer them over both classic histograms and summaries."

The original designers weren't careless. They wrote down what this choice costs, with the exact numbers. Most of us copied DefBuckets and never read that part, and our latency graphs have been rounding to whatever bucket list we chose at the start.

#Prometheus #Observability #SRE

---

## Twitter Version

Every request takes 220ms. A classic Prometheus histogram with buckets at 200ms and 300ms reports p95 = 295ms.

That's the example in Prometheus's own docs.

histogram_quantile assumes the requests in a bucket are spread evenly. Its error can be as large as the bucket is wide, and the boundaries were chosen before any traffic existed.

Add 100ms to every request and the real p95 is about 320ms. The estimate is 443ms.

If the quantile lands in +Inf, you get the second-highest boundary back. With Go's DefBuckets your p99 can never exceed 10s.

Native histograms (v2.40 experimental, v3.8 stable) estimate the same two cases at 228ms and 323ms. The docs now open with "If you can, use native histograms."

---

## Diagram

See `2026-11-26-prometheus-histogram-quantile-bucket-interpolation.excalidraw`. It's a confessional timeline with a "what the graph said" inset. The top band is a horizontal timeline: "Original model: one float per sample → buckets as series (worked, aggregatable)", then "Nov 2022 · v2.40 native histograms (experimental)", then "v3.8 stable, still opt-in", then "v4: on by default". Below it is a number-line comparison. A 200–300ms bucket is drawn as a wide slate band, with a thin plum spike at 220ms marked "truth", an amber marker at 295ms marked "classic estimate" and a teal marker at 228ms marked "native". A second row shows the +100ms shift: truth 320, classic 443, native 323. A footer callout carries the screenshot detail: "quantile in +Inf bucket → returns second-highest bound. Go DefBuckets → p99 tops out at 10s." Palette: slate, amber, teal and plum, with no red or green.
