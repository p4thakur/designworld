---
date: 2026-06-28
company: Netflix
topic: Tudum CQRS+Kafka to RAW Hollow
---

## Twitter / X Thread

1/ Netflix's Tudum team built textbook CQRS: Kafka for events, Cassandra for the read model, cache invalidation coordinating between them.

Then they measured their actual dataset.

2/ Three years of content — every show detail, every editorial. Stored in Apache Iceberg, compressed with Hollow: 130MB. That's 25% of the raw size. The entire read model fit in a single JVM heap.

3/ The architecture wasn't wrong. Tudum serves 20M users. CQRS with Kafka is a defensible call at that scale. But the ops reality was rough: hitting "Preview" meant Kafka propagation → Cassandra update → cache invalidation. Minutes of lag on every edit.

4/ The realization: they'd built three distributed systems to serve a dataset that fits in RAM.

5/ The fix: RAW Hollow. One producer pushes a compressed snapshot to every instance. Reads are O(1) — no Cassandra, no Kafka lag, no cache to coordinate. Delta updates when data changes. Preview now takes seconds.

6/ Detail from the engineering blog that I haven't seen in any writeup: RAW Hollow supports eventual consistency by default, but lets you opt into strong consistency per individual request. Most CQRS systems force you to pick one mode globally. This doesn't.

7/ Lesson: before you build a distributed read model, measure the dataset. Sometimes the right architecture is the one that fits in a heap.
