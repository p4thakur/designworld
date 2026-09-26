---
date: 2026-09-26
company: Uber
topic: Uber's Graphite/Carbon/Whisper metrics stack had no replication (a dead disk permanently deleted its metrics) and needed manual resharding to grow; swapping in Cassandra, ElasticSearch, and statsite still wasn't enough, so Uber built its own time series platform, M3, whose query engine processes columnar Blocks across many series at once instead of looping per series — the actual mechanism behind going from a fragile single-region setup to 6.6 billion time series and ~8.5 billion queried datapoints/sec
category: infrastructure
post_type: structured
opening_style: shared_pain_point
slug: uber-m3-time-series-metrics-platform
---

## Sources

- Uber Engineering Blog, ["M3: Uber's Open Source, Large-scale Metrics Platform for Prometheus"](https://www.uber.com/blog/m3/) — Uber's own primary post introducing M3: confirms the late-2014 Graphite/Carbon/Whisper stack, the lack of replication (a single node's disk failure meant permanent loss of its metrics), the manual resharding process required to grow the cluster, the interim statsite+Cassandra(Date Tiered Compaction Strategy)+ElasticSearch stack that still proved inadequate, the 2018 open-source release, and current scale figures: 6.6 billion time series, 500 million metrics/sec aggregated, 20 million metrics/sec persisted via quorum write to three replicas per region.
- Uber Engineering Blog, ["The Billion Data Point Challenge: Building a Query Engine for High Cardinality Time Series Data"](https://eng.uber.com/billion-data-point-challenge/) — Uber's primary source on the M3 Query engine: confirms the DAG-based compilation of both M3QL and PromQL, the Block abstraction (columnar chunks of many time series over a fixed time window that the engine processes in one pass), and the November 2018 measured throughput of ~2,500 queries/sec, ~8.5 billion datapoints/sec, ~35 Gbps.
- M3 official documentation (m3db.io), ["Storage Engine"](https://m3db.io/docs/architecture/m3db/engine/) and ["Overview"](https://m3db.io/docs/architecture/m3db/overview/) — project documentation maintained by the M3DB authors (Uber-originated, now via the M3 open source project): confirms M3TSZ as a Gorilla-paper-derived (Facebook) streaming XOR compression variant for float64 values, configurable lossy/lossless, achieving 1.45 bytes/datapoint on Uber's production workloads — a 40% improvement over standard TSZ.
- M3 documentation, ["Fetching and querying"](https://m3db.io/docs/architecture/m3query/fanout/) and project overview (m3db.io) — corroborates the M3 Coordinator/M3 Aggregator split, with M3 Aggregator performing stateful stream-based downsampling using etcd for leader election and aggregation-window tracking to guarantee at-least-once delivery of downsampled metrics through failover.
- Rob Skillington (M3DB co-creator), comment thread, Hacker News (news.ycombinator.com/item?id=21453757) — primary-source-adjacent confirmation from an M3 creator of the billions-of-samples ingestion scale referenced in the engineering blog.

**Note on sourcing:** direct fetches of uber.com and eng.uber.com were blocked by this environment's network egress policy at write time. The facts above are drawn from search-indexed excerpts of Uber's own engineering blog posts and the M3 project's own documentation site (m3db.io), cross-checked against each other for consistency (the 1.45 bytes/datapoint, 40%-over-TSZ, DAG/Block, and etcd-leader-election details appear consistently across the primary docs and are not just restated by summary sites).

**Key primary-source detail (not in most summaries):** most retellings of "Uber built its own metrics database" stop at "Graphite didn't scale, so they wrote M3." The mechanism-level reason it's actually faster isn't just "distributed" — the interim Cassandra+ElasticSearch stack was distributed too, and it still wasn't enough. The real shift is in the query engine's data structure: instead of fetching and iterating each time series independently to answer a question, M3 Query assembles a Block — a columnar slice holding many series across one time window — and runs the computation once, over the whole block. That's the difference between a system that scales by adding more machines to do the same per-series work, and one that changed what "one unit of work" means.

---

## LinkedIn Post

Every company that outgrows Graphite hits the same wall: Whisper was built to survive a slow disk, not a dead one.

By late 2014, every service, host, and piece of infrastructure at Uber was writing metrics into a sharded Carbon cluster backed by Whisper files. It worked until it didn't: there was no replication, so a single disk failure permanently deleted every metric that node held. Growing the cluster meant a manual resharding job. Neither problem gets better with scale — both get worse, on a system that's already load-bearing for on-call.

Uber's first fix was the obvious one: swap in components with a reputation for scale. Statsite for aggregation, Cassandra (Date Tiered Compaction Strategy) for storage, ElasticSearch for indexing. All battle-tested, all open source, all a mismatch for this shape of data. Operational burden climbed, cost climbed, and the feature set metrics teams actually needed — per-metric retention policies, real per-series compression, a query engine that could reason about billions of points at once — kept outrunning what a general-purpose store could do without heavy babysitting.

So Uber built M3 from scratch, open-sourcing it in 2018. The easy-to-miss part: M3's query engine doesn't iterate time series one at a time. It compiles both M3QL and PromQL into a DAG, then organizes results into Blocks — columnar chunks spanning many series over a fixed time window — so a query runs as one pass over a block instead of a loop over every series it touches. That's the actual difference between "distributed" and fast at this cardinality. Underneath, M3DB compresses floats with M3TSZ, a Gorilla-style XOR variant that hits 1.45 bytes per datapoint, 40% better than stock TSZ, while a separate M3 Aggregator uses etcd for leader election so stream-based downsampling still guarantees at-least-once delivery through failover.

The result: M3 now holds over 6.6 billion time series, ingesting 500 million metrics/sec and persisting 20 million/sec via quorum writes across three replicas. Its query engine serves roughly 2,500 queries/sec — about 8.5 billion datapoints/sec, ~35 Gbps.

Uber didn't rebuild because Cassandra and ElasticSearch are bad databases. They rebuilt because "store whatever shape of data shows up" and "answer any question across billions of correlated series in milliseconds" are different problems, and only one of those tools was ever designed for the second one.

#SystemDesign #Observability #Uber #TimeSeriesDB

**Character count: 2,482 / 3,000 ✓**

---

## Twitter Version

Whisper files don't replicate. So at Uber, one dead disk didn't just slow a metric down — it deleted it. Forever.

That was the state of Uber's Graphite/Carbon stack by late 2014. No replication, manual resharding, and it only got worse as usage grew.

The "safe" fix was Cassandra + ElasticSearch + statsite — all proven, all open source. It still wasn't enough. Cost and ops burden kept climbing faster than the feature set (per-metric retention, real compression, fast cross-series queries) could keep up.

So Uber built M3 instead. Query engine compiles M3QL/PromQL into a DAG, then works in Blocks — columnar chunks across many series at once, not a per-series loop. M3TSZ (Gorilla-style XOR) gets floats down to 1.45 bytes/datapoint.

Today: 6.6B time series, 500M metrics/sec in, ~8.5B datapoints/sec out at query time.

Not a bad-database story. A "the query pattern needed a different data structure" story.
