---
date: 2026-06-28
company: Netflix
topic: Tudum's CQRS+Kafka read model replaced by RAW Hollow in-memory store
category: infrastructure
post_type: confessional
opening_style: cold_fact
slug: netflix-tudum-cqrs-kafka-to-raw-hollow
---

## Sources

- Netflix TechBlog: [Netflix Tudum Architecture: from CQRS with Kafka to CQRS with RAW Hollow](https://netflixtechblog.com/netflix-tudum-architecture-from-cqrs-with-kafka-to-cqrs-with-raw-hollow-86d141b72e52)
- Netflix OSS: [Hollow — in-memory dataset distribution](https://hollow.how/)
- InfoQ: [Netflix Revamps Tudum's CQRS Architecture with RAW Hollow In-Memory Object Store](https://www.infoq.com/news/2025/08/netflix-tudum-cqrs-raw-hollow/)

**Key primary-source detail (not in summaries):** RAW Hollow supports both eventual consistency by default *and* strong consistency scoped to an individual request. You can serve most reads from the in-memory snapshot and opt into freshness only for the requests that need it. Almost no CQRS systems offer that flexibility at the read layer — it's usually one mode or the other.

---

## LinkedIn Post

Netflix's Tudum team had a textbook CQRS stack. Kafka for events. Cassandra for the read model. Three separate systems keeping data in sync.

Then someone measured the actual dataset.

Three years of Tudum content — every editorial, every show detail, every fan article — fit in an Apache Iceberg table. Compressed with Hollow's encoding, it came to 130MB. That's 25% of the uncompressed size. The entire read model fit in a single JVM heap.

The architecture wasn't wrong when they designed it. Tudum serves 20 million users, and when you're building at that scale without knowing how much data you'll accumulate, CQRS with Kafka is a defensible choice. You get write/read separation, event durability, horizontal scale on the read side. These are correct tools.

The operational reality was harder to defend. When a writer hit "Preview," the change had to propagate through Kafka, get consumed by downstream services, update Cassandra, and clear the cache. That process took minutes. On an editorial platform, waiting minutes to see your own changes isn't a latency problem — it's a workflow problem.

The realization, when it arrived, was uncomfortable: they'd stood up three distributed systems to serve a dataset that fit in a single instance's heap.

So they rebuilt around RAW Hollow, Netflix's in-memory object store. One producer computes and publishes the dataset as a compressed snapshot. Every instance holds the full read model in memory — no Cassandra queries, no Kafka consumer lag, no cache invalidation to coordinate. Reads are O(1). When data changes, delta-compressed updates propagate across instances. Preview now takes seconds.

One detail from the blog that doesn't appear in any summary: RAW Hollow supports both eventual consistency by default and strong consistency scoped to an individual request. You can let most reads use the cached in-memory snapshot and opt into freshness only when you need it. Most CQRS systems don't give you that option at the read layer.

The CQRS + Kafka setup wasn't a mistake. It was an appropriate design given what they knew. But the lesson is worth sitting with: before you build a distributed read model, measure the dataset. Sometimes the right architecture is the one that fits in RAM.

#SystemDesign #Netflix #DistributedSystems #SoftwareEngineering

**Character count: ~2,194 / 3,000 ✓**
**First 140 chars (mobile hook):** "Netflix's Tudum team had a textbook CQRS stack. Kafka for events. Cassandra for the read model. Three separate systems keeping data in sync." ✓
