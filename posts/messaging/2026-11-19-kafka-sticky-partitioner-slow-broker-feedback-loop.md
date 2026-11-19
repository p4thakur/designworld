---
date: 2026-11-19
company: Apache Kafka
topic: Kafka's keyless-record partitioner went from round robin (<=2.3) to the KIP-480 sticky partitioner (2.4), which switched partitions on new-batch creation. Batches close sooner on fast brokers, so slow brokers kept the producer's attention longest and got the most data. KIP-794 (3.3) moved the switch to a byte count (batch.size) and weights the next partition by inverse queue depth.
category: messaging
post_type: structured
opening_style: the_decision
slug: kafka-sticky-partitioner-slow-broker-feedback-loop
---

## Sources

- Kafka 2.3, [clients/.../internals/DefaultPartitioner.java](https://github.com/apache/kafka/blob/2.3/clients/src/main/java/org/apache/kafka/clients/producer/internals/DefaultPartitioner.java) - primary: "If no partition or key is present choose a partition in a round-robin fashion"; one `AtomicInteger` per topic, `Utils.toPositive(nextValue) % availablePartitions.size()`.
- Kafka 2.4, [DefaultPartitioner.java](https://github.com/apache/kafka/blob/2.4/clients/src/main/java/org/apache/kafka/clients/producer/internals/DefaultPartitioner.java) and [StickyPartitionCache.java](https://github.com/apache/kafka/blob/2.4/clients/src/main/java/org/apache/kafka/clients/producer/internals/StickyPartitionCache.java) - primary: "choose the sticky partition that changes when the batch is full"; `onNewBatch()` calls `nextPartition()`, which loops on a random available partition `while (newPart == null || newPart.equals(oldPart))`. In [KafkaProducer.java](https://github.com/apache/kafka/blob/2.4/clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java), `if (result.abortForNewBatch)` triggers `partitioner.onNewBatch(...)` and the record is re-partitioned before append.
- Kafka 2.4, [docs/upgrade.html](https://github.com/apache/kafka/blob/2.4/docs/upgrade.html) - primary: "When a new batch is created, a new partition is chosen. This decreases latency to produce, but it may result in uneven distribution of records across partitions in edge cases."
- Kafka trunk, [BuiltInPartitioner.java](https://github.com/apache/kafka/blob/trunk/clients/src/main/java/org/apache/kafka/clients/producer/internals/BuiltInPartitioner.java) - primary: "described in detail in KIP-794"; `if (producedBytes >= stickyBatchSize && enableSwitch || producedBytes >= stickyBatchSize * 2)` switches partition; the source comment's `linger.ms=500, 12KB in 500ms, batch.size=16KB` example on avoiding 4KB fractional batches; the cumulative frequency table example "0 3 1 -> 4 1 3 -> 4 5 8" with `Arrays.binarySearch`. [RecordAccumulator.java](https://github.com/apache/kafka/blob/trunk/clients/src/main/java/org/apache/kafka/clients/producer/internals/RecordAccumulator.java) passes `batchSize` as `stickyBatchSize` and drops a partition from the queue-size list when `readyTimeMs - drainTimeMs > partitionAvailabilityTimeoutMs`.
- Kafka trunk, [ProducerConfig.java](https://github.com/apache/kafka/blob/trunk/clients/src/main/java/org/apache/kafka/clients/producer/ProducerConfig.java) - primary: `partitioner.adaptive.partitioning.enable` default `true` ("produce more messages to partitions hosted on faster brokers"), `partitioner.availability.timeout.ms` default `0` ("this logic is disabled"), `batch.size` default `16384`.
- Kafka 3.3, [docs/upgrade.html](https://github.com/apache/kafka/blob/3.3/docs/upgrade.html) - primary, "Notable changes in 3.3.1": "improved to avoid pathological behavior when one or more brokers are slow"; old behavior restorable via `partitioner.class=org.apache.kafka.clients.producer.internals.DefaultPartitioner`, which is `@Deprecated` in 3.3.
- Confluent, ["Apache Kafka Producer Improvements with the Sticky Partitioner"](https://www.confluent.io/blog/apache-kafka-producer-improvements-sticky-partitioner/) - secondary for the benchmark: p99 at about half of the default with 3 producers at 1,000 msg/s, gap visible from 16 partitions. **Read via search-result excerpts only**: confluent.io, cwiki.apache.org (KIP-480 / KIP-794 pages) and issues.apache.org (KAFKA-10888) were not reachable from this run. The "slower brokers get more data, a positive feedback loop" framing of KIP-794's motivation also comes from search excerpts of the KIP page.

**Key primary-source detail:** the 2.4 switch is driven by `abortForNewBatch`, a property of the accumulator and sender, not of the data. The 3.3 code switches on `producedBytes`, and may wait up to `2 * batch.size` so it does not cut a batch that isn't ready yet (the source comment's 12 KB + 4 KB example).

Derived/interpretive (author's reading): the step-by-step "fast broker drains a part-filled batch, slow broker's batch waits until 16 KB" walk-through is my explanation of why batch-creation frequency tracks broker latency, consistent with the KIP-794 motivation but not quoted from it. Not a specific company incident.

---

## LinkedIn Post

Kafka 3.3 changed what the producer listens to before it switches partitions. It stopped listening to the network and started counting bytes.

That sounds tiny. It fixed a loop that sent the most data to the slowest broker.

Some background. Records with no key used to go round robin: one counter per topic, counter % partitions. With 16+ partitions every batch got a sliver, so you paid for lots of tiny requests.

KIP-480, in 2.4, fixed that with the sticky partitioner. Stay on one partition until a new batch has to be created, then jump to a random other one. In the code, an append that returns abortForNewBatch calls onNewBatch(), and the record is re-partitioned. Confluent's benchmark showed p99 latency at about half of round robin with 3 producers at 1,000 msg/s.

Here's the root cause of what went wrong. "A new batch was created" is a network event, not a data event. A batch closes when it's full or when the sender drains it.

On a fast broker the sender drains a part-filled batch as soon as linger.ms runs out. The next record needs a new batch, so the producer switches after a few KB.

On a slow broker the in-flight slots are full and the batch sits in the accumulator. It keeps taking records until it hits batch.size, 16,384 bytes. The producer stays on that partition the longest.

So the time spent on each partition tracked its broker's latency. The slow broker got more records, which made it slower, so it got even more. The 2.4 upgrade notes had already warned about "uneven distribution of records across partitions in edge cases."

KIP-794, in 3.3, moved the trigger. BuiltInPartitioner counts producedBytes and switches once it reaches batch.size, whatever the sender is doing. If the current batch isn't ready, the switch can wait until 2x batch.size, so the producer doesn't cut a 4 KB scrap.

Then it uses the queue lengths it already tracks. Queue sizes 0, 3, 1 get inverted to 4, 1, 3 and summed to 4, 5, 8. A random number in [0, 8) goes through a binary search. The backed-up partition gets picked 1 time in 8, the empty one 4 in 8. Adaptive partitioning is on by default. There's also partitioner.availability.timeout.ms, off by default, which drops a broker's partitions entirely if it stops draining for that long.

The old DefaultPartitioner is now @Deprecated.

When a switch is triggered by "this finished," the slowest component gets to decide how long the work stays with it. If you want fair distribution, count the work you hand out, not the completions you get back.

#ApacheKafka #DistributedSystems #SystemDesign #Messaging

---

## Twitter Version

Kafka 2.4's sticky partitioner switched partitions whenever a new batch was created.

The catch: batches close fast on a fast broker (drained after linger.ms) and slowly on a slow one (they wait until 16 KB is full).

So the slowest broker kept the producer's attention longest, got the most records, and got slower.

Kafka 3.3 (KIP-794) switches after batch.size bytes instead, and picks the next partition weighted by inverse queue depth: queues 0,3,1 → odds 4/8, 1/8, 3/8.

Count the work you hand out, not the completions you get back.

---

## Diagram

See `2026-11-19-kafka-sticky-partitioner-slow-broker-feedback-loop.excalidraw` (structured before/after: three columns, "<=2.3 round robin -> 2.4 sticky on new batch -> 3.3 bytes + weighted pick", each naming its switch trigger. Below 2.4, a dashed amber panel walks the fast-vs-slow-broker feedback loop. Below 3.3, a navy panel shows the cumulative frequency table "0 3 1 -> 4 1 3 -> 4 5 8" and the resulting 4/8, 1/8, 3/8 odds. Palette: slate + amber + teal/navy, no red/green.)
