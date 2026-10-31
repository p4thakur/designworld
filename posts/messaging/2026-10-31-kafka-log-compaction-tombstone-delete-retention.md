---
date: 2026-10-31
company: Apache Kafka
topic: A compacted Kafka topic keeps the last value per key, but tombstones are deleted after delete.retention.ms (default 24 hours), so a consumer that lags longer silently misses deletes and keeps zombie state.
category: messaging
post_type: contrarian
opening_style: cold_fact
slug: kafka-log-compaction-tombstone-delete-retention
---

## Sources

- GitHub, [apache/kafka - docs/design/design.md, "Log Compaction"](https://github.com/apache/kafka/blob/trunk/docs/design/design.md) - primary: guarantees, tombstone behavior, `delete.retention.ms` default, log cleaner mechanics (24 bytes per entry, 8GB buffer ~ 366GB of head), active segment never compacted, `max.compaction.lag.ms` caveats.

**Key primary-source detail:** guarantee #4 in the design doc states that a consumer can miss delete markers if it lags by more than `delete.retention.ms`, because tombstone removal happens concurrently with reads.

**Note on sourcing:** only the Kafka design doc (GitHub-hosted) was reachable; kafka.apache.org was blocked. The cache-with-zombie-rows scenario is an illustrative inference from guarantee #4, not a reported incident.

---

## LinkedIn Post

A compacted Kafka topic with 8GB of cleaner buffer can clean around 366GB of log head in one pass. The summary behind that is a hash table at exactly 24 bytes per key.

That is a lot of engineering for a topic that still has a delete problem most teams never read about.

The common mental model: a compacted topic is a table. One row per key, latest value wins, rebuild any cache from it at any time. The design doc does promise the last value for every key. It does not promise that deletes survive.

A delete in Kafka is a record with a key and a null payload, a tombstone. Compaction removes every earlier record for that key. Then the tombstone itself is removed after `delete.retention.ms`, which defaults to 24 hours.

Guarantee #4 in the design doc spells out the consequence: a consumer sees all the delete markers only if it reaches the head of the log in less than that window. Because tombstone removal runs concurrently with reads, a consumer that lags longer can miss them.

So picture a service cache that was down for a weekend. It restarts, replays from its last offset, and the user deleted on Saturday never arrives as a delete. The prior records for that key are gone, the tombstone is gone, and the cache still holds the old row. Nothing errors. The state is just wrong.

Two more details make this harder to reason about. Offsets never change, so a compacted topic has holes, and a read at a deleted offset just returns the next one. And the active segment is never compacted, so the newest records, including a fresh tombstone, stay uncompacted until the segment rolls. Setting `max.compaction.lag.ms` forces that roll, but the doc is clear that the deadline is not a hard guarantee. It depends on cleaner threads being free.

The fix is not clever. Treat `delete.retention.ms` as a contract with your slowest consumer: longer than the worst outage you plan to survive, or a rule that any consumer behind it rebuilds from scratch. Alert on lag against that number, not against zero.

A compacted topic is a log with a memory of the present. It is not a table, and it forgets the deletions first.

#ApacheKafka #SystemDesign #DataEngineering #DistributedSystems

---

## Twitter Version

A compacted Kafka topic is not a table.

Compaction keeps the last value per key. A delete is a null-payload record (tombstone), and the tombstone itself is removed after delete.retention.ms. Default: 24 hours.

Kafka's own doc: a consumer that lags longer than that can miss the delete.

Cache down all weekend, restart, replay. The user deleted Saturday is never deleted in your cache. No error.

Treat delete.retention.ms as a contract with your slowest consumer. Alert on lag against it.

---

## Diagram

See `2026-10-31-kafka-log-compaction-tombstone-delete-retention.excalidraw` (timeline: delete at t0, tombstone removed at t0+24h, consumer returning after 24h never sees it).
