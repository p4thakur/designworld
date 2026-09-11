---
date: 2026-09-11
company: DoorDash
topic: DoorDash rebuilt its ML feature store to be clusterless — and got there by turning OFF the clustering feature already built into the datastore they adopted
category: storage
post_type: contrarian
opening_style: challenge_assumption
slug: doordash-clusterless-feature-store-kvrocks
---

## Sources

- DoorDash Engineering: ["Lessons learned building DoorDash's clusterless ML feature store"](https://careersatdoordash.com/blog/doordash-clusterless-ml-feature-store/), May 2026
- DoorDash Engineering: ["Building a Scalable ML Feature Store with Redis"](https://careersatdoordash.com/blog/building-a-gigascale-ml-feature-store-with-redis/), April 2025
- DoorDash Engineering: ["How We Applied Client-Side Caching to Improve Feature Store Performance by 70%"](https://careersatdoordash.com/blog/how-we-applied-client-side-caching/), January 2025
- DoorDash Engineering (@DoorDashEng) on X, announcing the clusterless system: ["At DoorDash scale, vertical scaling hit its limit... clusterless ML Feature Store serving 1.6B+ features/sec at 50ms P999"](https://x.com/DoorDashEng/status/2056845071857975796)

**Key primary-source detail (not in most summaries):** Apache Kvrocks — the RocksDB-backed, Redis-protocol-compatible store DoorDash adopted for the rebuild — ships with native Redis Cluster support out of the box. DoorDash's engineers deliberately did not use it. The blog is explicit that turning on Kvrocks' built-in clustering would have reintroduced the exact state-and-coordination overhead they were trying to eliminate, so they built a separate stateless "clusterless" layer instead — offline per-shard RocksDB backups checkpointed to S3, pulled directly by stateless serving nodes, with a thin control-plane component (their Redis Cluster Manager) handling only routing.

**Note on sourcing:** Direct fetch of `careersatdoordash.com` was blocked by this environment's network egress policy at write time. The specific numbers and architecture details above — 1.6B+ features/sec at 50ms P999, the parquet-to-S3-to-per-shard-indexer-to-RocksDB-backup pipeline, the explicit rejection of Kvrocks' native clustering, the client-side connection/topology overhead of the prior large Redis clusters, and the 3x capacity gain from custom string/protobuf/Snappy serialization in the predecessor system — are drawn from search-indexed excerpts and direct quotes of the primary DoorDash Engineering blog posts and DoorDash's own engineering-team social post announcing the system, cross-checked against independent secondary write-ups citing the same posts.

---

## LinkedIn Post

Everyone assumes the way to scale a Redis-based feature store is a bigger, smarter Redis Cluster. DoorDash's ML infrastructure team found the opposite: Redis Cluster itself was the ceiling.

By early 2025, DoorDash's feature store — serving real-time inputs like consumer, merchant, and item features to models ranking every order — already handled tens of millions of reads per second across billions of daily requests, built on sharded Redis clusters split by use case (search, DeepRed, and more). They'd already squeezed it hard: a custom serialization scheme mixing raw strings, protobuf, and Snappy compression roughly tripled capacity on the same hardware.

But the ceiling wasn't throughput. It was the cluster itself. Every client had to hold open connections to every shard and track cluster topology metadata directly — the more shards they added to scale, the more connection and metadata overhead every single client carried. Scaling out made the system harder to operate, not easier.

So in the redesign, DoorDash's engineers made a deliberately unusual call: when they adopted Apache Kvrocks — a Redis-protocol-compatible store built on RocksDB — they didn't turn on its clustering. Kvrocks ships with native Redis clustering built in. They rejected it, because clustering carries exactly the state and coordination overhead they were trying to escape.

Instead they built it clusterless. An offline pipeline bakes feature data into per-shard RocksDB backups — batch jobs land parquet in S3, per-shard indexers build the backups, checkpoints go back to S3. Serving nodes are stateless: they pull backups straight from S3 and answer reads, while a separate control-plane layer, their Redis Cluster Manager, does nothing but routing — fully decoupled from where the data actually lives.

The result: 1.6 billion-plus feature reads served per second at 50ms P999 — and horizontal scaling that no longer means adding operational weight to every client in the fleet.

The Redis cluster wasn't a bad design. It was the right one for the scale it was built for. The lesson here is narrower than "avoid clustering": sometimes the bottleneck isn't the store, it's that state and serving got fused together, and the fix is prying them apart.

#SystemDesign #DoorDash #MachineLearning #DistributedSystems

**Character count: ~2,323 / 3,000 ✓**
**First 140 chars (mobile hook):** "Everyone assumes the way to scale a Redis-based feature store is a bigger, smarter Redis Cluster. DoorDash's ML infrastructure team found th" ✓

---

## Twitter / X Thread

1/ Everyone assumes you scale a Redis-based feature store by building a bigger, better Redis Cluster. DoorDash's ML team discovered the cluster itself was the bottleneck.

2/ Their store already served tens of millions of reads/sec across billions of requests/day — sharded by use case, capacity already tripled via custom serialization (raw strings + protobuf + Snappy).

3/ The real ceiling: every client held open connections to every shard and tracked cluster topology directly. More shards to scale = more overhead per client. Scaling out made the system harder to run, not easier.

4/ Their fix, when they moved to Apache Kvrocks (RocksDB under a Redis-compatible protocol): they turned OFF Kvrocks' built-in clustering. Clustering meant state + coordination — the exact problem they were escaping.

5/ Instead: fully clusterless. Batch jobs write parquet to S3 → per-shard indexers build RocksDB backups → stateless serving nodes just pull backups from S3 and serve reads. A separate control plane only routes.

6/ Result: 1.6B+ features served per second at 50ms P999.

7/ The old Redis cluster wasn't wrong — it was right for its era. The fix wasn't "avoid clustering." It was separating state from serving, after they'd been fused together the whole time.

---

## Diagram

See: `2026-09-11-doordash-clusterless-feature-store-kvrocks.excalidraw`

Type: Side-by-side architecture snapshot (contrarian style) — "the obvious fix" vs "what they built," with a rejection arrow between them and a banner calling out the headline number
Color scheme: Slate gray (the obvious fix — scale the Redis Cluster harder; not wrong, just the default path) vs violet (what DoorDash actually built — clusterless Kvrocks + S3); amber banner for the throughput number. No red/green good-bad pairing.
Key screenshottable number: 1.6B+ feature reads/sec at 50ms P999, plus the detail that Kvrocks' own native clustering was available and deliberately left off
