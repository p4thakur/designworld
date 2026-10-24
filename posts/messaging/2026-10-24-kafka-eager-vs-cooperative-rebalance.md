---
date: 2026-10-24
company: Apache Kafka
topic: Consumer group rebalancing - eager revokes everything, cooperative moves only what must move, static membership avoids restarts counting as leaves.
category: messaging
post_type: narrative
opening_style: mid_scene
slug: kafka-eager-vs-cooperative-consumer-rebalance
---

## Sources

- Apache Kafka source, [ConsumerPartitionAssignor.java](https://github.com/apache/kafka/blob/trunk/clients/src/main/java/org/apache/kafka/clients/consumer/ConsumerPartitionAssignor.java) - primary: `RebalanceProtocol` EAGER ("requires a consumer to always revoke all its owned partitions before participating in a rebalance event", "allows a complete reshuffling") vs COOPERATIVE ("allows a consumer to retain its currently owned partitions", "should not reassign any owned partitions immediately").
- Apache Kafka source, [CooperativeStickyAssignor.java](https://github.com/apache/kafka/blob/trunk/clients/src/main/java/org/apache/kafka/clients/consumer/CooperativeStickyAssignor.java) - primary: moving partitions are removed from the new assignment until the previous owner releases them; all consumers must use it; upgrade from 2.3 or earlier needs a specific path.
- Apache Kafka source, [CommonClientConfigs.java](https://github.com/apache/kafka/blob/trunk/clients/src/main/java/org/apache/kafka/clients/CommonClientConfigs.java) and [ConsumerConfig.java](https://github.com/apache/kafka/blob/trunk/clients/src/main/java/org/apache/kafka/clients/consumer/ConsumerConfig.java) - primary: `group.instance.id` static member docs, `session.timeout.ms` 45000, `max.poll.interval.ms` 300000, default assignors `[RangeAssignor, CooperativeStickyAssignor]`.

**Note on sourcing:** only GitHub-hosted sources were reachable (cwiki.apache.org, kafka.apache.org and confluent.io failed DNS). KIP text and Confluent benchmarks were NOT used; everything below is from the client source and javadoc. The "two rebalances" sequence is the behavior the assignor code implies, not a sentence in the javadoc.

**Key primary-source detail:** a static member that exceeds `max.poll.interval.ms` is not reassigned immediately. It stops heartbeating and is reassigned only after `session.timeout.ms`, "mirroring the behavior of a static consumer which has shutdown".

---

## LinkedIn Post

A deploy rolls through a consumer group, one pod at a time. Each pod restarts, rejoins, and the whole group pauses. Then the next pod restarts. Lag climbs on partitions that never had anything to do with the pod that just died.

That is the eager rebalance protocol working exactly as designed. The client source says it "requires a consumer to always revoke all its owned partitions before participating in a rebalance event." In exchange it "allows a complete reshuffling of the assignment." Every member lets go of everything, then waits to be told what it owns now.

The design made sense. If nobody holds anything while assignments are computed, no partition can have two owners. It is the simplest way to be correct. The price is that a one-pod change pauses the entire group, and a rolling restart of N pods can trigger it N times.

Cooperative rebalancing flips the contract. A consumer "retain[s] its currently owned partitions" and the assignor "should not reassign any owned partitions immediately." In CooperativeStickyAssignor, a partition that is moving is removed from the new assignment until its old owner has released it. First round: only the movers are revoked. Next round: they land on their new owners. Everything else keeps consuming.

Two catches, both in the source. It costs an extra rebalance round. And every consumer must use the assignor, so upgrading from 2.3 or earlier needs a specific path rather than a config flip.

Separate problem: restarts that should not count as leaving. Setting `group.instance.id` makes a consumer a static member, "to avoid group rebalances caused by transient unavailability (e.g. process restarts)". The detail worth knowing: if a static member blows past `max.poll.interval.ms`, its partitions are not taken back immediately. They move after `session.timeout.ms`, the same as if it had shut down. Slow handlers are treated like dead pods, just later.

Neither fix removes the tradeoff. Stop-the-world was the price of simplicity, and cooperative moves that price into extra rounds and a coordinated upgrade.

#Kafka #SystemDesign #Messaging #Backend

---

## Twitter Version

Rolling restart a Kafka consumer group and lag spikes on partitions that never moved.

Eager rebalance: every member revokes ALL owned partitions before the rebalance. Simple, correct, no double owners. But one pod change pauses the whole group, N restarts can mean N pauses.

Cooperative: only partitions that must move are revoked, then assigned in a later round. The rest keep consuming. Cost: extra round, and all consumers must opt in.

Static membership (group.instance.id): restarts don't count as leaving. Exceed max.poll.interval.ms and partitions still wait out session.timeout.ms (45s default) before moving.

---

## Diagram

See `2026-10-24-kafka-eager-vs-cooperative-rebalance.excalidraw` (side-by-side protocol flows with the static-membership callout).
