<!-- sources -->
<!-- Primary (fetched directly, no corroboration workaround needed this time): -->
<!--   Datadog Engineering Blog, "Introducing Husky, Datadog's third-generation event store" -->
<!--     https://www.datadoghq.com/blog/engineering/introducing-husky/ -->
<!--   Datadog Engineering Blog, "Inside Husky's query engine: Real-time access to 100 trillion events" -->
<!--     https://www.datadoghq.com/blog/engineering/husky-query-architecture/ -->
<!--   Datadog Engineering Blog, "Husky: Efficient compaction at Datadog scale" -->
<!--     https://www.datadoghq.com/blog/engineering/husky-storage-compaction/ -->
<!--   Datadog Engineering Blog, "Husky: Exactly-once ingestion and multi-tenancy at scale" -->
<!--     https://www.datadoghq.com/blog/engineering/husky-deep-dive/ -->
<!-- Corroborating: -->
<!--   InfoQ, "Datadog Creates Scalable Data Ingestion Architecture" -->
<!--     https://www.infoq.com/news/2023/06/datadog-husky-data-ingestion/ -->
<!-- Key verifiable details (pulled directly from the primary blog posts above): -->
<!-- 1. Gen 1 was a multi-tenant, Elasticsearch-like cluster with storage and compute on shared nodes. A single -->
<!--   misbehaving tenant could disrupt every other tenant's experience; scaling operations often worsened things -->
<!--   because overwhelmed nodes had to stream data to each other. -->
<!-- 2. Gen 2 introduced a shard router that assessed each tenant's rolling 5-minute data volume and isolated -->
<!--   tenants onto dedicated shards, with stateless storage nodes (with replicas) and a custom query engine. -->
<!--   This stopped cascading failures but left gaps: bursts on one shard still degraded colocated tenants, there -->
<!--   was no hot/cold data distinction, and high-cardinality fields (stack traces, UUIDs) and features like -->
<!--   windowing functions, array functions, and DDSketch storage weren't well supported. -->
<!-- 3. Husky (gen 3) is described as an "unbundled, distributed, schemaless, vectorized column store... designed -->
<!--   from the ground up around commodity object storage." Writers are stateless nodes that read Kafka, buffer -->
<!--   in memory, and upload to blob storage (S3). Compactors merge small files into larger ones, LSM-tree style. -->
<!--   Readers are stateless leaf nodes that query individual files. A FoundationDB-backed metadata store provides -->
<!--   strictly serializable transactions for consistent file visibility. It took "over a year and a half" from -->
<!--   first line of code to one product fully migrated. -->
<!-- 4. Isolation became a query-time decision: query pools can be sliced by product, tenant, or human vs. -->
<!--   automated traffic, independent of how data was ingested. -->
<!-- 5. Husky now handles "100 trillion events" queryable in real time, and billions of queries a day. -->
<!-- 6. Latency tradeoff, stated directly in the query-architecture post: Husky's median query latency increased -->
<!--   by "a few hundred milliseconds" versus the legacy system (remote object storage loses to local SSD for the -->
<!--   common case), while max/p99/p95 latencies dropped dramatically. Reported figures: p50/p75 fragment-query -->
<!--   latency ~2ms, p90 ~6ms, p95 ~20ms, p99 257ms, max observed 12.82 seconds. -->
<!-- 7. Data-pruning funnel, from a stated sample of 1,000 query fragments: 300 pruned at the metadata-service -->
<!--   level, 560 pruned by the result cache, 78 pruned via column metadata, 28 pruned via other caches — leaving -->
<!--   only 34 fragments that require an actual data read, and just 4 (0.4%) that trigger a blob storage fetch. -->
<!--   On average, only 0.6% of the underlying data is scanned per query. -->
<!-- 8. From the compaction post: writers produce fragments of "a maximum of a few thousand events"; compaction -->
<!--   merges these up toward roughly one million rows per final fragment — about a 1,000x increase in fragment -->
<!--   size. "Locality compaction" (a best-effort, LSM-hybrid pass layered on top of size-tiered compaction) cut -->
<!--   query-worker replica counts by 30% on rollout — described as the most expensive part of the system. -->
<!--   Compaction throughput runs at "dozens of GB of data every second," with thousands of fragments compacting -->
<!--   concurrently, one GET request per input fragment. -->

# Datadog Rebuilt Its Log Storage Twice. The Third Rewrite Traded a Slower Median for a Faster Tail.

**Date:** 2026-08-17
**Company:** Datadog
**Category:** storage
**Post type:** structured
**Opening style:** cold_fact
**Slug:** datadog-husky-columnar-storage-migration
**Character count (LinkedIn):** ~2360

---

## LinkedIn Post

Datadog's logging platform processes more than 100 trillion events a day and answers billions of queries. Five years ago, one misbehaving customer could still degrade query performance for every other tenant packed onto the same cluster.

That was generation one: a multi-tenant, Elasticsearch-like system where storage and compute lived on the same nodes. A tenant streaming a burst of high-cardinality data didn't just slow its own queries — it dragged its neighbors down too, and rebalancing the cluster to fix it often made things worse, since overwhelmed nodes had to stream data to each other mid-rebalance.

Generation two fixed the blast radius. A shard router measured each tenant's rolling five-minute volume and isolated them onto dedicated shards, with stateless storage nodes and a custom query engine in front. Cascading failures mostly stopped. But new limits showed up: a burst on one shard still degraded everyone colocated on it, there was no split between hot and cold data, and the system couldn't cheaply handle high-cardinality fields like stack traces and UUIDs, or features like windowing and sketch-based aggregation.

The fix wasn't a smarter shard router. It was giving up on nodes owning both storage and compute at all. Husky, generation three, is an unbundled, schemaless column store built on commodity object storage — S3 underneath, FoundationDB holding metadata for strictly serializable file visibility, writers and readers that never talk to each other directly. Isolation stopped being an ingestion-time decision and became a query-time one: a query pool can be sliced by product, by tenant, or even by human versus automated traffic.

It took a year and a half from first commit to one fully migrated product. The tradeoff was real — median query latency rose by a few hundred milliseconds, because remote object storage loses to local SSD in the common case. In exchange, the tail collapsed. p99 queries now return in 257ms. And on a sample of 1,000 query fragments, only 34 ever need an actual data read; just 4 touch blob storage at all. On average, a query scans 0.6% of the underlying data.

Datadog chose a slower median to buy a dramatically shorter tail — the opposite of what most teams protect when a migration risks touching the common case.

Sources in comments.

#SystemDesign #Datadog #DistributedSystems #Observability

---

## Twitter / X Version

1/ Datadog's logging platform processes 100+ trillion events a day. Five years ago, one noisy customer could still tank query performance for every other tenant sharing its cluster.

2/ Gen one: multi-tenant, Elasticsearch-like, storage and compute on the same nodes. A tenant streaming high-cardinality data dragged its neighbors down with it — and rebalancing to fix it often made things worse, since overwhelmed nodes had to stream data to each other mid-rebalance.

3/ Gen two isolated tenants onto dedicated shards based on rolling 5-minute volume. Cascading failures mostly stopped. But a burst on one shard still hurt everyone colocated on it, hot/cold data wasn't distinguished, and high-cardinality fields (stack traces, UUIDs) stayed expensive.

4/ The real fix wasn't a smarter shard router. It was giving up on nodes owning both storage and compute. Husky (gen 3): unbundled column store on S3, FoundationDB for metadata, writers and readers that never talk directly. Isolation became a query-time slice, not an ingestion-time one.

5/ Took 1.5 years from first commit to one migrated product. Median latency rose a few hundred ms — remote object storage loses to local SSD on the common case.

6/ In exchange: p99 now 257ms. On 1,000 sample query fragments, only 34 ever need a real data read; just 4 touch blob storage. Average query scans 0.6% of the underlying data.

7/ Datadog bought a shorter tail by accepting a slower median — the opposite of what most teams protect when a migration threatens to regress the common case.

---

## Excalidraw Diagram

**File:** 2026-08-17-datadog-husky-columnar-storage-migration.excalidraw
**Type:** Migration timeline — three horizontal stages (Gen 1 → Gen 2 → Husky), paired with a 4-box pruning funnel showing what happens to 1,000 sample query fragments, and a footer stating the latency tradeoff.
**Color scheme:** Warm stone for Gen 1 (deliberately not "bad" — it was the right design for Datadog's early scale). Cyan for Gen 2, marking real progress without claiming it was the finished answer. Emerald for Husky/Gen 3 and the pruning-funnel boxes, tying the query-time payoff back to the architecture that enabled it. Amber breaks the emerald run on the funnel's final box, to make the single most screenshottable number (0.6%) visually pop. Violet footer, distinct from every box color, so the "result" band reads as commentary rather than another pipeline stage.
**Screenshottable stat:** "p99 query latency: 257ms. Of 1,000 sample query fragments, only 4 ever touch blob storage. On average, 0.6% of the underlying data gets scanned per query."

### Layout

```
Title: "Datadog Rebuilt Its Log Storage Twice. The Third Rewrite Traded a Slower Median for a Faster Tail."
Subtitle: "Datadog's own engineering blog: two generations of multi-tenant clusters hit isolation and cardinality
limits before Husky unbundled storage from compute entirely"

[ROW 1 — THREE GENERATIONS OF DATADOG'S LOG STORAGE, top, 3 boxes left to right]
  Box 1 (stone): "GEN 1 — SHARED CLUSTER. Elasticsearch-like, multi-tenant. Storage and compute live on the
    same nodes. One noisy tenant streaming high-cardinality data degrades every neighbor sharing its cluster.
    Rebalancing to fix it often makes it worse."
  --arrow (gray)-->
  Box 2 (cyan): "GEN 2 — SHARD ROUTER. Tenants isolated onto dedicated shards by rolling 5-minute volume.
    Cascading failures mostly stop. But no hot/cold split, and high-cardinality fields like stack traces and
    UUIDs stay expensive."
  --arrow (gray)-->
  Box 3 (emerald): "GEN 3 — HUSKY. Unbundled column store on top of S3. FoundationDB holds metadata for
    consistent file visibility. Writers and readers never talk directly. Isolation becomes a query-time slice,
    not an ingestion-time one. 1.5 years to first migrated product."

[ROW 2 — WHERE 1,000 QUERY FRAGMENTS ACTUALLY GO, middle, 4 boxes left to right]
  Box 1 (emerald): "1,000 sample query fragments start the search."
  --arrow (emerald)-->
  Box 2 (emerald): "34 need an actual data read, after metadata, result-cache, and column-stat pruning."
  --arrow (emerald)-->
  Box 3 (emerald): "Just 4 ever trigger a blob storage fetch — 0.4% of the sample."
  --arrow (amber)-->
  Box 4 (amber): "On average, only 0.6% of the underlying data gets scanned per query."

[FOOTER, violet band, full width]
  "Result: median query latency rose a few hundred milliseconds on Husky — remote object storage loses to
  local SSD in the common case. In exchange, p99 fell to 257ms. 'Datadog chose a slower median to buy a
  dramatically shorter tail — the opposite of what most teams protect when a migration threatens the common
  case.'"
```
