---
date: 2026-11-25
company: Apache Kafka (producer acks, broker min.insync.replicas, Partition.scala)
topic: In Kafka, `acks=all` means the leader waits for every replica that is currently in the ISR (in-sync replica set), not every replica of the partition. The ISR shrinks on its own. A follower is removed once it has not caught up to the leader's log end offset for `replica.lag.time.max.ms` (30s by default, 10s before 2.5). The broker and topic default `min.insync.replicas` is 1. The only produce-path guard is `if (inSyncSize < minIsr && requiredAcks == -1) throw NotEnoughReplicasException`, and with minIsr = 1 a live leader can never fail it. So once the ISR shrinks to the leader alone, `acks=all` gives you the durability of `acks=1` and nothing tells the producer. Kafka 3.0 made `acks=all` the producer default (KIP-679). It did not change the broker's `min.insync.replicas` default.
category: messaging
post_type: contrarian
opening_style: challenge_assumption
slug: kafka-acks-all-min-insync-replicas-default-one
---

## Sources

- apache/kafka trunk, [clients/.../producer/ProducerConfig.java](https://raw.githubusercontent.com/apache/kafka/trunk/clients/src/main/java/org/apache/kafka/clients/producer/ProducerConfig.java). Primary.
  - `ACKS_DOC`, on `acks=all`: "the leader will wait for the full set of in-sync replicas to acknowledge the record. This guarantees that the record will not be lost as long as at least one in-sync replica remains alive."
  - `ACKS_DOC`, on `acks=1`: "should the leader fail immediately after acknowledging the record but before the followers have replicated it then the record will be lost."
  - `.define(ACKS_CONFIG, Type.STRING, "all", ...)`, so the producer default is `all`.
- apache/kafka trunk, [clients/.../common/config/TopicConfig.java](https://raw.githubusercontent.com/apache/kafka/trunk/clients/src/main/java/org/apache/kafka/common/config/TopicConfig.java). Primary. `MIN_IN_SYNC_REPLICAS_DOC`: "If acks=all and the current ISR set is smaller than this effective minimum, then the producer will raise an exception (either NotEnoughReplicas or NotEnoughReplicasAfterAppend)." It also says the "typical scenario" is "a replication factor of 3, set min.insync.replicas to 2, and produce with acks of 'all'."
- apache/kafka trunk, [server-common/.../ServerLogConfigs.java](https://raw.githubusercontent.com/apache/kafka/trunk/server-common/src/main/java/org/apache/kafka/server/config/ServerLogConfigs.java). Primary. `MIN_IN_SYNC_REPLICAS_DEFAULT = 1`. [storage/.../LogConfig.java](https://raw.githubusercontent.com/apache/kafka/trunk/storage/src/main/java/org/apache/kafka/storage/internals/log/LogConfig.java) uses the same default for the topic-level config and has `DEFAULT_UNCLEAN_LEADER_ELECTION_ENABLE = false`.
- apache/kafka trunk, [server/.../ReplicationConfigs.java](https://raw.githubusercontent.com/apache/kafka/trunk/server/src/main/java/org/apache/kafka/server/config/ReplicationConfigs.java). Primary. `REPLICA_LAG_TIME_MAX_MS_DEFAULT = 30000L`, with the doc text: "If a follower hasn't sent any fetch requests or hasn't consumed up to the leader's log end offset for at least this time, the leader will remove the follower from ISR."
- apache/kafka trunk, [core/.../cluster/Partition.scala](https://raw.githubusercontent.com/apache/kafka/trunk/core/src/main/scala/kafka/cluster/Partition.scala). Primary.
  - `appendRecordsToLeader`: `if (inSyncSize < minIsr && requiredAcks == -1) { throw new NotEnoughReplicasException(...) }`, with the comment "Avoid writing to leader if there are not enough insync replicas to make it safe".
  - `checkEnoughReplicasReachOffset`: `if (minIsr <= curMaximalIsr.size) (true, Errors.NONE) else (true, Errors.NOT_ENOUGH_REPLICAS_AFTER_APPEND)`, with the comment "the request was already appended locally and then added to the purgatory before the ISR was shrunk".
  - `metricsGroup.newGauge("UnderMinIsr", () => if (isUnderMinIsr) 1 else 0, tags)`, the per-partition gauge that reports when the ISR is below min.insync.replicas.
  - `getOutOfSyncReplicas` / `isFollowerOutOfSync`: "Stuck followers: If the leo of the replica hasn't been updated for maxLagMs ms... Slow followers: If the replica has not read up to the leo within the last maxLagMs ms... Both these cases are handled by checking the lastCaughtUpTimeMs."
- Kafka [2.5 docs/upgrade.html](https://raw.githubusercontent.com/apache/kafka/2.5/docs/upgrade.html). Primary. "the default value of zookeeper.session.timeout.ms has been increased from 6s to 18s and replica.lag.time.max.ms from 10s to 30s."
- Kafka [3.0 docs/upgrade.html](https://raw.githubusercontent.com/apache/kafka/3.0/docs/upgrade.html). Primary. "The producer has stronger delivery guarantees by default: idempotence is enabled and acks is set to all instead of 1. See KIP-679." It also notes KAFKA-13598: in 3.0.0 and 3.1.0 the idempotence default was not actually applied, but "the bug did not affect the acks=all change."
- Kafka [0.11.0 docs/upgrade.html](https://raw.githubusercontent.com/apache/kafka/0.11.0/docs/upgrade.html). Primary. "Unclean leader election is now disabled by default. The new default favors durability over availability."
- Not used: the KIP-679 and KIP-537 wiki pages on cwiki.apache.org were blocked in this session's network settings. Both changes are cited only through the upgrade notes above.

**Key primary-source detail:** the guard that rejects an unsafe `acks=all` write is one comparison, `inSyncSize < minIsr`. The ISR always contains the leader, so with the default `minIsr = 1` that comparison can never be true while the leader is serving writes. The ISR can shrink from {1,2,3} to {1} through ordinary removals driven by `lastCaughtUpTimeMs`, and `acks=all` keeps returning success throughout.

Derived/interpretive (the author's reading of the code and configs, not stated verbatim by a source): the three-step ISR shrink scenario in the diagram is an illustration and not a specific incident. "acks is a producer setting, durability is a topic setting" is the author's framing. The point that the 3.0 default change made `acks=all` common without changing `min.insync.replicas` comes from comparing the two defaults. No source says it in those words.

---

## LinkedIn Post

acks=all doesn't mean all replicas. On a default Kafka cluster it can mean exactly one.

The word "all" refers to the in-sync replica set (ISR), and the ISR is not fixed. The leader removes any follower that hasn't caught up to its log end offset within replica.lag.time.max.ms. That's 30 seconds by default, and it was 10 before Kafka 2.5. A GC pause, a slow disk, or a broker in the middle of a rolling restart is enough to get a follower dropped.

Here is the check that's supposed to catch an unsafe write, from Partition.scala:

if (inSyncSize < minIsr && requiredAcks == -1) throw NotEnoughReplicasException

min.insync.replicas defaults to 1, on the broker and on the topic. The ISR always includes the leader, so inSyncSize < 1 can never be true while a leader is accepting writes.

So you get this. Replication factor 3, ISR {1,2,3}. Broker 3 stalls and drops out. Broker 2 falls behind during a deploy and drops out. The ISR is {1}. Every acks=all write now waits for exactly one ack, the leader's own, and the producer gets a clean success each time. That's acks=1 durability. No error, no warning, and the metric that would show it is UnderMinIsr, which can't fire because the minimum is 1.

If broker 1 dies now, you have two bad outcomes to pick from. Unclean leader election has been off by default since 0.11, so the partition goes offline. If someone turned it back on to "fix" that, a lagging replica becomes leader and the writes you were told were safe are gone.

Kafka 3.0 (KIP-679) made acks=all the producer default. So more teams now have the setting that sounds safe, while the broker still ships with the floor that makes it optional.

The fix is what the Kafka docs call the "typical scenario": RF=3, min.insync.replicas=2, acks=all. Once the ISR drops to 1, writes fail with NotEnoughReplicas instead of quietly getting weaker. Don't set it to 3. With 3, one broker restart blocks every write.

The default habit is to treat durability as a client setting, because the client is the code we own. In Kafka it isn't. acks decides how long the producer waits. min.insync.replicas decides whether that wait means anything. Only the second one is set on the topic, and it ships set to 1.

#Kafka #DistributedSystems #EventStreaming

---

## Twitter Version

acks=all in Kafka doesn't mean all replicas. It means all replicas in the ISR, and the ISR can shrink to just the leader.

The guard is one line: if (inSyncSize < minIsr && acks == -1) reject.

min.insync.replicas defaults to 1. A live leader is always in its own ISR, so that check never fires.

RF=3, two followers lag for more than 30s, the ISR is {leader}. acks=all now behaves like acks=1 and the producer still gets success every time.

Kafka 3.0 made acks=all the producer default. The broker's min.insync.replicas default is still 1.

Set it to 2 on RF=3 topics. acks decides how long you wait. min.insync.replicas decides whether waiting protects anything.

---

## Diagram

See `2026-11-25-kafka-acks-all-min-insync-replicas-default-one.excalidraw`. It's a contrarian side-by-side. The left column, "What acks=all sounds like", shows a leader with three acks from all three brokers. The right column, "What min.insync.replicas=1 allows", is a three-step ISR shrink strip: {1,2,3}, then {1,2} after broker 3 lags for more than 30s, then {1} after broker 2 lags for more than 30s. Each step is marked "acks=all → SUCCESS", and the last one is labeled "= acks=1 durability". Under both columns sits the guard line `inSyncSize < minIsr  →  1 < 1 is never true`, which is the screenshot detail. A footer bar shows the fix: RF=3, min.insync.replicas=2, acks=all, so ISR {1} gives NotEnoughReplicas. Palette: teal, burnt orange and charcoal, with no red or green.
