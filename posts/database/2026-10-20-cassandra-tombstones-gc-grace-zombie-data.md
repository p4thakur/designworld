---
date: 2026-10-20
company: Apache Cassandra
topic: Tombstones, gc_grace_seconds and how a delete comes back from the dead.
category: database
post_type: narrative
opening_style: mid_scene
slug: cassandra-tombstones-gc-grace-zombie-data
---

## Sources

- Apache Cassandra, [Tombstones documentation](https://github.com/apache/cassandra/blob/trunk/doc/modules/cassandra/pages/managing/operating/compaction/tombstones.adoc) - primary: deletion is an insert, zombie scenario, `gc_grace_seconds` default 864000, hinted handoff does not replay mutations for tombstoned data in the grace period, the three conditions to drop a tombstone.
- Apache Cassandra, [Compaction overview](https://github.com/apache/cassandra/blob/trunk/doc/modules/cassandra/pages/managing/operating/compaction/overview.adoc) - primary: TTL expiry becomes a tombstone that stays at least `gc_grace_seconds`, `tombstone_threshold` default 0.2, tombstone and data kept in the same data directory so a lost disk cannot undelete data.
- Apache Cassandra, [cassandra.yaml](https://github.com/apache/cassandra/blob/trunk/conf/cassandra.yaml) - primary: `tombstone_warn_threshold: 1000`, `tombstone_failure_threshold: 100000`, and the comment explaining why scanned tombstones are held in memory.

**Note on sourcing:** only GitHub-hosted docs and config were reachable from this environment, so every number comes from those three files. The 3-replica timeline is an illustration of the documented behavior, not an incident report.

**Key primary-source detail:** a tombstone is dropped only if every SSTable holding older data for that partition takes part in the same compaction. Passing `gc_grace_seconds` is necessary, not sufficient. And the yaml explains the scan limits: tombstones seen during a scan are kept in memory so the coordinator can pass them to other replicas.

---

## LinkedIn Post

A user deletes their account on Monday. Three weeks later, the account is back.

Nobody restored a backup. Cassandra did exactly what it was designed to do.

Cassandra never removes data when you delete it. It treats a deletion as an insertion: a timestamped marker called a tombstone, written through the normal write path to SSTables on the replicas. Immutable files cannot be edited, and replicas that are offline cannot be told anything. So the delete has to be a fact that travels.

Now take 3 replicas and one of them is down during the delete. Two nodes write the tombstone. The third still holds the original value and has no idea.

If the other two purged the tombstone right away, the cluster would have two nodes saying "nothing here" and one saying "value". When the third node returns, repair sees data with no marker against it and spreads it back. The docs call this a zombie.

The guard is gc_grace_seconds, 864000 by default. Ten days. A tombstone survives compaction until that window closes, which gives a dead node time to come back and learn about the delete. Hinted handoff does not replay mutations for tombstoned data during that window, so the replay path does not rescue you either.

The part that surprises people: once the window closes, the tombstone is not gone. It is merely eligible. It is only dropped when the SSTable holding it, plus every SSTable containing older data for that partition, land in the same compaction. A TTL makes this worse. Expired data becomes a tombstone that stays for at least gc_grace_seconds, and mixed TTLs scatter a partition across files that never compact together.

So the second failure is the opposite one. Delete-heavy workloads, queues especially, pile up tombstones that reads have to scan. The yaml says why they cost memory: during a scan they are held in the heap so the coordinator can pass them to other replicas. Defaults warn at 1,000 tombstones in a read and fail the query at 100,000.

And the first failure comes back if a node stays down past ten days. Its old data gets repaired back into the cluster.

Both dangers come from one decision: a delete that must outlive every replica's absence. The tradeoffs don't disappear. They move to a repair schedule that has to finish inside the grace period.

#Cassandra #SystemDesign #Databases #DistributedSystems

---

## Twitter Version

A user deletes their account. Weeks later it's back.

Cassandra treats a delete as an insert: a timestamped tombstone. If one of 3 replicas is down, it never sees it.

Purge the tombstone too early and repair copies the old value back. The docs call it a zombie.

Guard: gc_grace_seconds, default 864000 (10 days). Repair must finish inside it.

But past the window the tombstone is only eligible. It drops only when all SSTables with older data for that partition compact together.

Too few drops and reads hit warn at 1,000 tombstones, fail at 100,000.

---

## Diagram

See `2026-10-20-cassandra-tombstones-gc-grace-zombie-data.excalidraw` (sequence timeline across 3 replicas: delete, tombstone purge after 10 days, and the downed replica returning with the old value).
