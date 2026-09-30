---
date: 2026-09-30
company: Cloudflare
topic: Cloudflare's HTTP analytics pipeline outgrew Postgres RollupDB plus a 12-node Citus cluster, and a Flink replacement failed on zoneId key skew, a fold bottleneck and checkpointing. Cloudflare moved rollups into ClickHouse materialized views, tuned index granularity to 32, and shut both old systems down.
category: storage
post_type: structured
opening_style: shared_pain_point
slug: cloudflare-clickhouse-http-analytics-flink-citus
---

## Sources

- Cloudflare Blog, [HTTP Analytics for 6M requests per second using ClickHouse](https://blog.cloudflare.com/http-analytics-for-6m-requests-per-second-using-clickhouse/) — primary source: Postgres/Citus/RollupDB pipeline, Flink attempt, ClickHouse replacement, shutdown of RollupDB and the 12-node Citus cluster, index granularity 32 (-50% latency, ~3x throughput).
- Alexander Bocharov, [ClickHouse Meetup talk slides (Apr 2018)](https://www.slideshare.net/slideshow/http-analytics-for-6m-requests-per-second-using-clickhouse-by-alexander-bocharov/95620756) and [Altinity talk page](https://altinity.com/presentations/2018/5/1/http-analytics-for-6m-requests-per-second-using-clickhouse) — 1,630B message size, 150+ fields, Flink failure reasons (zoneId key skew, fold bottleneck, checkpointing, debuggability), RollupDB rollup levels, 3x replication.
- Cloudflare Blog, [Scaling out PostgreSQL for CloudFlare Analytics using CitusDB](https://blog.cloudflare.com/scaling-out-postgresql-for-cloudflare-analytics-using-citusdb) — earlier Citus-era context.

**Note on sourcing:** direct fetches of blog.cloudflare.com, clickhouse.com and slideshare were blocked by this environment's egress policy. Facts come from search-indexed excerpts of these primary sources; the Kafka partition count (106) was seen only in a search summary and is deliberately not used in the post.

**Key primary-source detail:** index granularity of 32 vs the 8,192 default, chosen because dashboard queries return only a few rows.

---

## LinkedIn Post

At 6 million HTTP requests per second, Cloudflare's analytics pipeline had a problem that no amount of tuning fixed: the traffic wasn't spread evenly, and the pipeline assumed it was.

The original design was reasonable. Every edge request became a Kafka message (1,630 bytes, 150+ fields). Go consumers aggregated them per zone per minute and wrote the results into a single Postgres instance called RollupDB, which rolled minutes up into hours, days and months. A 12-node Citus cluster served the reads behind the customer dashboard.

Then the team tried to replace the aggregation layer with Apache Flink. It worked at small volume. At full volume it hit three walls. The stream was keyed by zoneId, and a handful of very large zones dominated the load, so a few Flink workers did most of the work while the rest idled. The fold operation became the bottleneck. And checkpointing degraded throughput as the state grew. Debugging it was slow enough that time to market slipped.

So Cloudflare made an unusual call: stop aggregating in the stream at all. Insert the raw-ish rows straight into ClickHouse and let materialized views produce the rollups inside the database. The messy crons and aggregation consumers went away. Everything was stored with at least 3x replication.

The detail that only shows up in the talk: the aggregated tables use an index granularity of 32 instead of ClickHouse's default 8,192. The default is tuned for scanning millions of rows. A dashboard query for one zone returns a handful of rows, so reading 8,192-row blocks to find them wastes almost all the I/O. Dropping to 32 cut query latency by 50% and raised throughput about 3x.

The result: the Postgres RollupDB instance and the 12-node Citus cluster were shut down.

The lesson isn't "ClickHouse is fast." It's that the failed Flink attempt and the old Postgres design shared one flaw. Both aggregated before storing, and both keyed the work by zone, so the biggest customers set the ceiling for everyone. Moving the rollup to where the data already lives removed the hot key from the pipeline entirely.

#SystemDesign #ClickHouse #DataEngineering #Cloudflare

**Character count: 2147 / 3,000**

---

## Twitter / X Thread

1/ Cloudflare's analytics pipeline handled 6M HTTP requests per second. Each one a 1,630-byte Kafka message with 150+ fields. The old design: Go consumers -> a single Postgres RollupDB -> a 12-node Citus cluster.

2/ They tried Flink to replace the aggregation layer. Fine at small scale. At full scale: the stream was keyed by zoneId, a few huge zones skewed the load, the fold op became the bottleneck, and checkpointing dragged throughput.

3/ The fix wasn't a better stream processor. It was no stream aggregation at all. Insert into ClickHouse, let materialized views build the rollups. No more crons or aggregation consumers.

4/ The detail from the talk: index granularity 32 instead of the default 8,192. Dashboard queries return a few rows, so smaller blocks mean far less wasted I/O. Result: -50% latency, ~3x throughput.

5/ Postgres RollupDB and the 12-node Citus cluster were shut down. Both old designs aggregated before storing and keyed by zone, so the biggest customers set the ceiling. Move the rollup to where the data lives.
