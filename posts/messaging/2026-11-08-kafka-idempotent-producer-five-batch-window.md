---
date: 2026-11-08
company: Apache Kafka
topic: Idempotent producer - broker dedups retries by exact sequence range but keeps only 5 batches per producer, which is why max in-flight is capped at 5; sequence gaps raise OutOfOrderSequenceException; dedup is scoped to one producer epoch.
category: messaging
post_type: narrative
opening_style: number_that_doesnt_add_up
slug: kafka-idempotent-producer-five-batch-window
---

## Sources

- GitHub, apache/kafka [ProducerConfig.java](https://github.com/apache/kafka/blob/trunk/clients/src/main/java/org/apache/kafka/clients/producer/ProducerConfig.java) - primary: enable.idempotence and max.in.flight docs ("broker only retains at most 5 batches for each producer"), defaults (acks=all, retries=Integer.MAX_VALUE, delivery.timeout.ms=120000, idempotence=true, in-flight=5), ConfigException when in-flight > 5.
- GitHub, apache/kafka [ProducerStateEntry.java](https://github.com/apache/kafka/blob/trunk/storage/src/main/java/org/apache/kafka/storage/internals/log/ProducerStateEntry.java) - primary: NUM_BATCHES_TO_RETAIN = 5, oldest removed when full, findDuplicateBatch matches exact sequence range and requires same epoch.
- GitHub, apache/kafka [ProducerAppendInfo.java](https://github.com/apache/kafka/blob/trunk/storage/src/main/java/org/apache/kafka/storage/internals/log/ProducerAppendInfo.java) - primary: checkSequence throws OutOfOrderSequenceException; new epoch with non-zero sequence rejected.

**Key primary-source detail:** the in-flight cap of 5 is derived from the broker's 5-batch dedup memory (NUM_BATCHES_TO_RETAIN), not from tuning.

Note: KIP-98 on cwiki.apache.org was unreachable (domain not allowed in the session network); all facts come from the source code. The opening scenario is generic, no company incident is claimed.

---

## LinkedIn Post

Kafka's producer can have 5 requests in flight on one connection. The broker remembers exactly 5 batches per producer. That is not a coincidence.

Start with the failure. A producer sends batch A, then batch B, on the same connection. A fails with a transient error and gets retried. B has already landed. Now the log reads B, A. The config docs say it plainly: with max.in.flight.requests.per.connection above 1 and idempotence off, "there is a risk of message reordering after a failed send due to retries."

The other failure is quieter. A write succeeds, the ack is lost, the producer retries, and the log holds two copies. The docs for enable.idempotence describe the off state the same way: retries "may write duplicates of the retried message in the stream."

The fix is bookkeeping, not magic. Each producer gets an ID and an epoch, and every batch carries a sequence number. The broker keeps a small queue of recent batches per producer. When a retry arrives, it looks for a cached batch with the exact same sequence range. If it finds one, the write is a duplicate, and the broker answers with the original result instead of appending again.

Here is the part that gets skipped. That queue has a fixed size. In ProducerStateEntry, NUM_BATCHES_TO_RETAIN is 5, and when the queue is full the broker drops the oldest entry to make room. The producer config docs spell out the consequence: in-flight is capped at 5 "because broker only retains at most 5 batches for each producer. If the value is more than 5, previous batches may be removed on broker side."

So the in-flight limit is not a tuning suggestion. A sixth outstanding batch could push out the one whose retry the broker needs to recognize. The client enforces it: set idempotence explicitly with more than 5 in flight and you get a ConfigException, "must be set to at most 5."

Ordering comes from the same sequence numbers. A batch must continue exactly where the last one ended. Otherwise the broker throws OutOfOrderSequenceException and the producer finds out something was lost or skipped, instead of silently writing around the hole.

One detail the code shows: if the producer epoch differs, duplicate lookup returns nothing, and a new epoch must start at sequence 0. Dedup is scoped to one producer session. A restarted producer with a new ID gets no protection for what the old one sent.

Today this is on by default. enable.idempotence is true, acks is all, retries is Integer.MAX_VALUE, in-flight is 5. But set acks=1 or retries=0 without saying anything about idempotence, and it is quietly turned off, with no error.

No one designed 5 as a performance sweet spot. It is the size of a memory the broker agreed to keep. The tradeoff did not go away: more pipelining costs more broker state, and the cap is where the two meet.

#ApacheKafka #DistributedSystems #SystemDesign #BackendEngineering

---

## Twitter Version

Kafka's producer allows 5 in-flight requests per connection. The broker remembers exactly 5 batches per producer. Same number, on purpose.

Without idempotence, a retry of batch A after B landed gives you B, A. A lost ack plus a retry gives you duplicates.

The fix: producer ID + epoch, a sequence number on every batch. Broker keeps a queue of recent batches and matches a retry by exact sequence range. Match = duplicate, return the old result.

The queue is NUM_BATCHES_TO_RETAIN = 5. Oldest is dropped when full. So the client caps in-flight at 5 "because broker only retains at most 5 batches for each producer." Set more, get a ConfigException.

Gap in sequence? OutOfOrderSequenceException. New epoch? Must start at 0, so dedup never spans producer sessions.

Default today: idempotence on. But acks=1 or retries=0 silently turns it off.

---

## Diagram

See `2026-11-08-kafka-idempotent-producer-five-batch-window.excalidraw` (sequence flow: retry with broker's 5-batch window, matched vs evicted).
