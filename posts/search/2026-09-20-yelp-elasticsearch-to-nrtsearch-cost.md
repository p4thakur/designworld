---
date: 2026-09-20
company: Yelp
topic: Yelp retired its original Lucene-based search backend for Elasticsearch in 2017 for the shared tooling and ecosystem, then by 2021 had to build its own gRPC-on-Lucene search engine, Nrtsearch, because Elasticsearch's per-document replication and self-managed shard placement made scaling read replicas linearly more expensive and hot-spotted — quietly rebuilding the same primary/replica-on-Lucene shape it had left behind, with EBS-volume reattachment standing in for full S3 snapshot downloads
category: search
post_type: confessional
opening_style: cold_fact
slug: yelp-elasticsearch-to-nrtsearch-cost
---

## Sources

- Yelp Engineering Blog: ["Nrtsearch: Yelp's Fast, Scalable and Cost Effective Search Engine"](https://engineeringblog.yelp.com/2021/09/nrtsearch-yelps-fast-scalable-and-cost-effective-search-engine.html) (Sept 2021) — primary source for why Elasticsearch's document-based replication and self-managed shard placement stopped scaling for Yelp, the Nrtsearch primary/replica-on-Lucene-NRT architecture, the phased 1%→100% dark-launch migration process, and the results (30-50% improvement in p50/p95/p99 latency, up to 40% infrastructure cost reduction on some workloads, 90%+ of Elasticsearch traffic migrated).
- Yelp Engineering Blog: ["Moving Yelp's Core Business Search to Elasticsearch"](https://engineeringblog.yelp.com/2017/06/moving-yelps-core-business-search-to-elasticsearch.html) (June 29, 2017) — primary source for the system Nrtsearch effectively replaced: a custom backend built directly on Apache Lucene, using a master/slave design where the master snapshotted the Lucene index and uploaded it to S3, and slaves downloaded those snapshots periodically to serve live traffic.
- Yelp/nrtsearch GitHub repository and README ([github.com/Yelp/nrtsearch](https://github.com/Yelp/nrtsearch)) — corroborates the primary/replica split, Lucene near-real-time (NRT) segment replication over gRPC, and EBS-backed segment storage with S3 as the backup/restore path.
- Independent secondary write-ups summarizing both the 2017 and 2021 Yelp posts (search-indexed excerpts referencing the original blog content directly) corroborate the specific percentages and the dark-launch rollout mechanics.

**Note on sourcing:** Direct fetch of engineeringblog.yelp.com, arpitbhayani.me, theblueprint.dev, qbox.io, and pretalx.com was blocked by this environment's network egress policy at write time. The facts above are drawn from search-indexed excerpts of both original Yelp engineering blog posts (2017 and 2021), cross-checked against Yelp's own open-source GitHub repository and README for Nrtsearch, which independently confirms the architecture described in those excerpts.

**Key primary-source detail (not in most summaries):** Every retelling of the Nrtsearch story describes it as "Yelp built a faster Lucene-based replacement for Elasticsearch." What that skips is that Yelp had already run almost exactly this shape of system before Elasticsearch ever showed up: its original core business search backend was a single primary indexing documents, taking periodic snapshots of the Lucene index, and uploading them to S3 for read replicas to download. Yelp deliberately retired that design for Elasticsearch in 2017. The 2021 fix isn't a new architecture — it's a return to the pre-2017 shape, made to actually work at scale by two upgrades the old system never had: gRPC-shipped incremental Lucene segments instead of full periodic S3 snapshots, and EBS-volume reattachment, so a dead replica recovers in seconds by grabbing its own still-intact volume instead of re-downloading a full segment set from S3.

---

## LinkedIn Post

In 2017, Yelp retired the search engine it had run since its early days and moved onto Elasticsearch. By 2021, it had built a brand new search engine again — to get away from Elasticsearch.

Nothing broke overnight. Yelp's original core business search ran on a custom backend built straight on Apache Lucene: a single primary indexed documents and took periodic snapshots, uploaded to S3, and read replicas downloaded those snapshots to serve live traffic. It was one of the oldest systems still running in production, and moving to Elasticsearch in 2017 made sense — a standard, well-supported engine every new search use case at Yelp could share instead of more hand-rolled Lucene plumbing.

The problem showed up as Yelp kept onboarding more use cases onto the same clusters. Elasticsearch replicates by document: every replica indexes every write itself, so adding a replica to handle more read traffic also adds indexing CPU, whether that replica needed it or not. Shard placement was Elasticsearch's call, not Yelp's, so some nodes sat lightly loaded while others held the shards that took most of the traffic. And scaling out meant migrating shards off nodes that were still serving live search — you couldn't cleanly add capacity under load.

The fix Yelp shipped, Nrtsearch, is a gRPC server on top of Lucene where one primary does all the indexing and segment merging, and replicas just pull finished segments and serve queries. Segments live on an EBS volume, so a dead replica gets its volume reattached to a fresh box in seconds instead of re-downloading everything from S3.

Rolled out gradually — 1% dark-launched traffic ramping to 100%, smallest indexes first — it cut p50/p95/p99 latency 30-50%, cut infrastructure cost up to 40% on some workloads, and now carries over 90% of what used to run on Elasticsearch.

Look closely and the fix isn't really a new idea. It's the same primary/replica-on-Lucene shape Yelp walked away from in 2017, rebuilt with gRPC segment shipping and EBS reattachment instead of full S3 snapshots. Sometimes going back isn't failure. It's arriving with the tools the first version needed.

#SystemDesign #Search #Elasticsearch #Lucene

**Character count: 2,181 / 3,000 ✓**
**First ~155 chars (mobile hook):** "In 2017, Yelp retired the search engine it had run since its early days and moved onto Elasticsearch. By 2021, it had built a brand new search engine again..." ✓

---

## Twitter / X Thread

1/ In 2017, Yelp moved its core search off a system it had run since its early days and onto Elasticsearch. By 2021, it built a new search engine — to get away from Elasticsearch.

2/ The old system: one primary indexed docs, snapshotted the Lucene index to S3, replicas downloaded and served reads. Elasticsearch was supposed to be the upgrade — shared, standard, no more hand-rolled Lucene plumbing.

3/ The catch: Elasticsearch replicates per document. Every replica re-indexes every write itself. Add a replica for more read capacity, and you also add indexing CPU you didn't need.

4/ Shard placement wasn't Yelp's call either — some nodes idled while others held all the hot shards. Autoscaling meant migrating shards off nodes still serving live traffic.

5/ Their fix, Nrtsearch: one primary indexes and merges segments, replicas just pull finished segments over gRPC and serve queries. Segments live on EBS — a dead replica's volume reattaches to a new box in seconds, no S3 re-download needed.

6/ Rolled out via 1%→100% dark launch: 30-50% cut in p50/p95/p99 latency, up to 40% lower infra cost, 90%+ of Elasticsearch traffic migrated.

7/ It's not really a new architecture. It's the pre-2017 primary/replica-on-Lucene shape again — just with gRPC segment shipping and EBS reattachment instead of full S3 snapshots.

---

## Diagram

See: `2026-09-20-yelp-elasticsearch-to-nrtsearch-cost.excalidraw`

Type: Timeline of the system's evolution (confessional style) — four stages left to right (Pre-2017 custom Lucene backend → 2017 Elasticsearch adopted → 2018-2020 the cracks → 2021 Nrtsearch), connected by a single timeline spine arrow, with a numbers callout beneath and a closing reflection line. Focuses on the human/organizational cause (onboarding more use cases onto shared clusters) rather than just architecture boxes.
Color scheme: slate gray for the pre-2017 system (it wasn't bad, just old), indigo for the 2017 Elasticsearch move (a deliberate, reasonable upgrade at the time), mustard/gold for the 2018-2020 cracks stage (friction and cost, not a red "failure"), plum/magenta for the 2021 Nrtsearch stage (something genuinely new). Deliberately avoids red=bad/green=good, and avoids reusing blue/amber/teal/green from the prior post's diagram.
Key screenshottable numbers: 30-50% p50/p95/p99 latency improvement, up to 40% infrastructure cost reduction, 90%+ of Elasticsearch traffic migrated, 1%→100% dark-launch rollout.
