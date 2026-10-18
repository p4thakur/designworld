---
date: 2026-10-18
company: RabbitMQ (Broadcom/VMware)
topic: Why RabbitMQ 4.0 removed classic queue mirroring - quorum queues drop the catch-up sync, add a default delivery limit of 20, and charge in disk writes, RAM index and odd-sized clusters.
category: messaging
post_type: structured
opening_style: cold_fact
slug: rabbitmq-quorum-queues-replace-mirroring
---

## Sources

- GitHub, [rabbitmq/rabbitmq-website - docs/quorum-queues/index.md](https://github.com/rabbitmq/rabbitmq-website/blob/main/docs/quorum-queues/index.md) - primary: mirroring removed in 4.0 (deprecated 2021, removed 2024); follower resumes replication with no catch-up; delivery-limit default 20 in 4.0 and unlimited in 3.13.x; prefetch caveat; node-count failure table; 32 bytes per message index; disk persistence and throughput notes.

**Key primary-source detail:** the poison-message section warns that with prefetch above 1, all outstanding unacknowledged deliveries can be discarded together if they were requeued as a group, so a crash loop can drop innocent messages. Secondary summaries only mention "delivery limit".

---

## LinkedIn Post

RabbitMQ 4.0 deleted classic queue mirroring, the feature that used to replicate a queue across nodes. It was deprecated in 2021 and removed in 2024.

The replacement is the quorum queue, built on Raft. The interesting part is not that it uses consensus. It's which operational problems disappeared as a side effect.

First, rejoining. RabbitMQ's docs say a failed follower "will automatically resume log replication at the point they left off," so there's no special catch-up process and "no impact on leader availability as was the case with classic mirrored queues." Bringing a replica back used to cost the queue some availability. Now a replica is just a log that's behind.

Second, the poison message. A message that makes a consumer requeue it repeatedly is never acknowledged, so it never leaves. In 3.13.x there was no limit on this. Starting with 4.0, a quorum queue's delivery limit defaults to 20. After that the message is dropped, or dead-lettered if a DLX is configured. Restoring the old behavior means setting x-delivery-limit=-1, and the docs add: "This is not recommended."

There's a catch buried in that section. With a prefetch above 1, all outstanding unacknowledged deliveries can be discarded together if they were requeued as a group, for example when a consumer instance dies repeatedly. A crash loop can drop messages that were never the poison.

Third, the bill. Quorum queues persist every message to disk before doing anything else, regardless of delivery mode. Throughput falls as message size grows and as members are added. A cluster of 3 tolerates 1 failure; a cluster of 4 also tolerates only 1, which is why the docs say even-sized groups don't help and recommend an odd number, with performance tailing off past 5 and no more than 7 nodes advised.

Memory is the quiet one. Each queue keeps an in-memory index of at least 32 bytes per message. That's about 1 MB for every 30,000 messages, whatever their size. A million-message backlog costs at least 32 MB of index per queue, and a thousand backed-up queues multiply that.

The migration reads as a trade of failure modes. Mirroring paid for rejoins with availability. Quorum queues pay with refusal: no majority, no writes.

Data safety instead of availability, stated plainly in the docs: "Generally quorum queues favours data consistency over availability."

#RabbitMQ #DistributedSystems #Messaging #SystemDesign

---

## Twitter Version

RabbitMQ 4.0 removed classic queue mirroring (deprecated 2021, removed 2024). Quorum queues, built on Raft, replace it.

What went away: the catch-up. A rejoining follower just resumes log replication where it left off, with "no impact on leader availability as was the case with classic mirrored queues."

What got added: a poison-message brake. delivery-limit defaults to 20 in 4.0. In 3.13.x there was none.

Catch: with prefetch > 1, a crash loop can discard every unacked delivery requeued together, not just the poison one.

The bill: every message hits disk first, ~1 MB of RAM index per 30,000 messages, 3 nodes tolerate 1 failure and 4 still tolerate 1.

Mirroring stalled. Quorum queues refuse.

---

## Diagram

See `2026-10-18-rabbitmq-quorum-queues-replace-mirroring.excalidraw` (before/after comparison: mirrored classic vs quorum queue, with the cost row).
