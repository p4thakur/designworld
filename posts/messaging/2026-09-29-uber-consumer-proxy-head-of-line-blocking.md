---
date: 2026-09-29
company: Uber
topic: Uber stopped letting services talk to Kafka directly and built a push-based Consumer Proxy (uForwarder) whose out-of-order commit tracker detects and clears head-of-line blocking that a partition-ordered consumer can never escape
category: messaging
post_type: narrative
opening_style: cold_fact
slug: uber-consumer-proxy-head-of-line-blocking
---

## Sources

- Uber Engineering, ["Enabling Seamless Kafka Async Queuing with Consumer Proxy"](https://www.uber.com/us/en/blog/kafka-async-queuing-with-consumer-proxy/) — the original design: push each message over gRPC, consumer returns the result, proxy owns offsets.
- Uber Engineering, ["Introducing uForwarder: The Consumer Proxy for Kafka Async Queuing"](https://www.uber.com/us/en/blog/introducing-ufowarder/) — production lessons: hardware efficiency, consumer isolation, head-of-line blocking detection and mitigation, delayed processing; 1,000+ consumer services onboarded.
- [github.com/uber/uForwarder](https://github.com/uber/uForwarder) — open-source repo: at-least-once delivery, out-of-order processing, retry and dead-letter queues, independent scaling of partitions and consumer instances.
- InfoQ, ["Uforwarder: Uber's Scalable Kafka Consumer Proxy"](https://www.infoq.com/news/2026/02/uber-uforwarder-kafka-push-proxy/) (Feb 2026) — secondary coverage.

**Note on sourcing:** uber.com, infoq.com and other blog hosts were blocked by this environment's egress policy at write time. Facts come from the GitHub README (fetched) and search-indexed excerpts of Uber's posts. No numbers beyond those excerpts are used.

**Key detail (rarely in summaries):** Kafka's commit is a single number per partition, so one poison message pins it. The tracker's mitigation cancels the message's in-flight and future gRPC retries first, and only then dead-letters it and marks it COMMITTED. Cancelling first prevents a late retry from succeeding after the message is already in the DLQ.

---

## LinkedIn Post

Uber runs Kafka at a scale of trillions of messages and petabytes a day. More than 1,000 downstream services read from it. And Uber decided that none of them should be talking to Kafka directly.

The reason is a property of Kafka that is easy to forget. A consumer commits one number per partition: the offset it has finished up to. Everything before it is done, everything after it is not. That is what makes the log simple, and it is also a trap. If message 102 keeps failing, the consumer can retry it forever, or skip it and risk data loss. Messages 103 to 500 sit behind it, perfectly healthy and going nowhere. This is head-of-line blocking.

The usual escape is more partitions, because parallelism in Kafka is capped by partition count. That works until it doesn't: partition counts are painful to change, and every extra partition is a cost on the brokers whether or not the consumer needs it.

Uber's Consumer Proxy flips the model. The proxy reads from Kafka and pushes each message, individually, to a consumer instance over gRPC. The service handles it and returns an ack or a nack. The service never sees an offset, never joins a consumer group, never gets rebalanced. Its thread count no longer depends on the partition count.

The interesting part is the bookkeeping. Because messages now complete out of order, the proxy keeps an out-of-order commit tracker: a status per offset, per partition. It only commits to Kafka when every earlier offset has been acked or nacked. So if 102 is stuck while 103 to 105 finish, those three sit in the tracker as done but uncommittable. That gap is the detection signal. A watermark that stops moving while later offsets keep completing is head-of-line blocking, visible in a data structure instead of a pager.

Mitigation follows a strict order. Mark the offset CANCELED. Cancel its in-flight gRPC requests and any future retries. Send it to the dead-letter queue. Then mark it COMMITTED and let the watermark jump. Cancelling comes first so a late retry cannot succeed after the message is already in the DLQ.

Isolation follows the same instinct. When a downstream dependency is down or rate-limited, only the affected partitions are buffered. The rest keep flowing.

The tradeoff is real: a new hop, a new fleet to run, and ordering given up on purpose. Uber judged that cheaper than 1,000 teams each learning Kafka's consumer semantics the hard way.

#Kafka #SystemDesign #DistributedSystems #Uber

**Character count: 2,456 / 3,000**

---

## Twitter / X Thread

1/ Uber moves trillions of Kafka messages a day. 1,000+ services consume them. None of them talk to Kafka directly.

2/ Why: Kafka commits one offset per partition. If message 102 keeps failing, 103 to 500 wait behind it, healthy and stuck. Head-of-line blocking.

3/ Uber's Consumer Proxy pushes each message over gRPC instead. Services never see offsets or consumer groups, and scale threads independently of partitions.

4/ The trick: an out-of-order commit tracker. Status per offset. Commit only when all earlier ones are acked or nacked. A watermark that stalls while later offsets finish is the blocking signal.

5/ Fix, in order: mark CANCELED, cancel in-flight and future retries, send to DLQ, mark COMMITTED. Cancel first so a late retry can't win after the DLQ write.

6/ Cost: an extra hop, a fleet to run, ordering given up on purpose. Cheaper than 1,000 teams learning Kafka's consumer semantics.

---

## Diagram

See: `2026-09-29-uber-consumer-proxy-head-of-line-blocking.excalidraw`

Type: sequence/state strip (narrative). Offsets 100 to 107 shown with tracker statuses, stuck watermark at 102, then the four-step mitigation. Palette: green/violet/amber for healthy states, red only for the stuck offset, blue for the mitigation.
