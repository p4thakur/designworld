<!-- sources -->
<!-- Primary: -->
<!--   Apache Kafka Wiki, "KIP-500: Replace ZooKeeper with a Self-Managed Metadata Quorum" -->
<!--   URL: https://cwiki.apache.org/confluence/display/KAFKA/KIP-500:+Replace+ZooKeeper+with+a+Self-Managed+Metadata+Quorum -->
<!--   Apache Kafka Wiki, "KIP-833: Mark KRaft as Production Ready" -->
<!--   URL: https://cwiki.apache.org/confluence/display/KAFKA/KIP-833:+Mark+KRaft+as+Production+Ready -->
<!--   Apache Kafka JIRA, "KAFKA-6879: Controller deadlock following session expiration" -->
<!--   URL: https://issues.apache.org/jira/browse/KAFKA-6879 -->
<!-- Note: direct fetch of confluent.io and cwiki.apache.org returned HTTP 403 under this session's egress -->
<!-- policy (same class of gateway-level denial hit on prior posts in this series). Facts below were -->
<!-- cross-checked across multiple independent search-result excerpts that quote or closely paraphrase the -->
<!-- KIP-500 motivation section and Confluent's own engineering coverage directly, plus corroborating -->
<!-- secondary sources: -->
<!--   Confluent Blog, "Kafka Needs No Keeper: Removing the ZooKeeper Dependency" — -->
<!--     https://www.confluent.io/blog/removing-zookeeper-dependency-in-kafka/ -->
<!--   Confluent Blog, "Apache Kafka Supports 200K Partitions Per Cluster" — -->
<!--     https://www.confluent.io/blog/apache-kafka-supports-200k-partitions-per-cluster/ -->
<!--   Towards Data Science, "Kafka No Longer Requires ZooKeeper" — -->
<!--     https://towardsdatascience.com/kafka-no-longer-requires-zookeeper-ebfbf3862104/ -->
<!--   Apache Kafka JIRA, "KAFKA-8151: Broker hangs and lockups after Zookeeper outages" — -->
<!--     https://issues.apache.org/jira/browse/KAFKA-8151 -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Kafka's original architecture (from its 2011 LinkedIn origins) used ZooKeeper for controller election, -->
<!--    broker liveness (ephemeral znodes), and as the source of truth for topic/partition/replica/ISR metadata. -->
<!-- 2. On controller failover, the newly elected controller must load the full cluster metadata state from -->
<!--    ZooKeeper into memory before it can issue any LeaderAndIsr directives — a reload that scales with total -->
<!--    partition count. The KIP-500 motivation section states this reload could push failover past 20 minutes -->
<!--    on large clusters, and cites this as a hard practical ceiling on how many partitions a single cluster -->
<!--    could hold (independent coverage puts the practical ceiling around roughly 200,000 partitions per -->
<!--    ZooKeeper-backed cluster). -->
<!-- 3. ZooKeeper watches are one-time triggers: once fired, a client must re-register to observe future changes. -->
<!--    Combined with the controller's own RPC-based metadata propagation (UpdateMetadataRequest), every single -->
<!--    metadata change fanned out to every broker — work that scaled with partition count on every update, not -->
<!--    only on failover. -->
<!-- 4. KIP-500 (proposed 2019) replaced this with a self-managed metadata quorum: controller nodes participate -->
<!--    directly in a Raft group over an internal __cluster_metadata log. Standby controllers are Raft followers -->
<!--    continuously replaying that log, so they already hold near-complete state before any leader election -->
<!--    occurs, and brokers apply incremental deltas from the log instead of receiving full-state RPC fan-out. -->
<!--    Independent coverage describes resulting controller failover as near-instantaneous, typically under a -->
<!--    second. -->
<!-- 5. KIP-833 marked KRaft production-ready for new clusters starting with Apache Kafka 3.3 (released -->
<!--    October 3, 2022), after roughly three years of KIP-500 development. ZooKeeper support was later -->
<!--    deprecated and, in subsequent major releases, removed entirely from Apache Kafka. -->
<!-- 6. KAFKA-6879 is a real, publicly filed Apache Kafka bug: a ZooKeeper session-expiration event could -->
<!--    deadlock the controller's own initialization lock against the latch used to confirm all queued -->
<!--    controller events had been handled, leaving the controller silently unresponsive ("zombie") — brokers -->
<!--    continued fetching but the controller never issued further directives until manually restarted. A -->
<!--    related issue, KAFKA-8151, documents similar broker lockups following ZooKeeper outages. -->

# Kafka's Team Spent a Decade Tuning ZooKeeper. The Fix Was Deleting It.

**Date:** 2026-07-27
**Company:** Apache Kafka / Confluent
**Category:** messaging
**Post type:** contrarian
**Opening style:** challenge_assumption
**Slug:** kafka-kraft-zookeeper-removal
**Character count (LinkedIn):** ~2,521

---

## LinkedIn Post

For a decade, the fix for a slow Kafka controller failover was "give ZooKeeper more headroom." That was never going to work.

Kafka's controller — the node owning topic/partition/ISR metadata — depends on ZooKeeper for cluster state. When it dies, whichever broker wins the leader-election znode doesn't just start serving. It has to walk the entire ZooKeeper tree first: every topic, partition, replica assignment, and in-sync-replica set, loaded into memory before it can issue a single LeaderAndIsr request. That reload is O(total partitions), not O(ZooKeeper's own throughput). On some production clusters, that failover window stretched past 20 minutes. No amount of ZK tuning shrinks a linear scan of your own metadata.

There's a second cost hiding in the same design. ZooKeeper watches are one-shot: they fire once, then the client has to re-register. So every metadata change means the controller re-arms a watch and then fans out a full UpdateMetadataRequest to every broker — work that scales with partition count on every single update, not just on failover.

Kafka's own team eventually did the contrarian thing: ripped ZooKeeper out (KIP-500) and embedded a Raft-based metadata quorum inside Kafka itself. Controller nodes are Raft voters. Standby controllers aren't idle — they're followers, continuously replaying the metadata log, so they already hold the state before anyone calls an election. Failover became a Raft vote, not a data-loading job: under a second, typically. Broker updates went from full-state RPC fanout to tailing a log of deltas — O(N) collapsed to O(1) per change.

Why did it take ten years to admit this? Because ZooKeeper was the safe default — proven, boring, already embedded in HBase, Solr, Kafka itself. The instinct was always to tune the tool everyone trusted, not question whether a session-based external coordination service was ever the right shape for a system that needs sub-second decisions at 200,000 partitions.

The tuning had a real cost, too. KAFKA-6879 is a filed bug where a ZooKeeper session expiration deadlocked the controller's own internal lock against its own expiry-handling latch — leaving a "zombie" controller that kept the broker fetching but never issued another directive again, silently, until someone restarted it by hand.

Sometimes the slow thing isn't slow because it needs tuning. It's slow because your control plane's source of truth lives in somebody else's system.

#SystemDesign #ApacheKafka #ZooKeeper #DistributedSystems

---

## Twitter / X Version

1/ For a decade, the fix for a slow Kafka controller failover was "give ZooKeeper more headroom." That was never going to work.

2/ On controller death, the new controller must walk the entire ZooKeeper tree — every topic, partition, replica, ISR — into memory before issuing one LeaderAndIsr request. That's O(total partitions). On some production clusters, failover stretched past 20 minutes.

3/ Second hidden cost: ZK watches are one-shot. Every metadata change means re-arming a watch, then fanning out a full UpdateMetadataRequest to every broker. That fan-out work scales with partition count on every update, not just on failover.

4/ Kafka's own team did the contrarian thing: ripped ZooKeeper out (KIP-500), embedded a Raft metadata quorum inside Kafka. Standby controllers are Raft followers already replaying the log — failover became a vote, not a data-load. Under a second, typically.

5/ Broker updates went from full-state RPC fanout to tailing a log of deltas. O(N) collapsed to O(1) per change.

6/ The tuning-instinct cost was real too: KAFKA-6879, a filed bug where a ZK session expiry deadlocked the controller's own lock, leaving a "zombie" controller — broker still fetching, but never getting another directive until someone restarted it by hand.

7/ Sometimes the slow thing isn't slow because it needs tuning. It's slow because your control plane's source of truth lives in somebody else's system.

---

## Excalidraw Diagram

**File:** 2026-07-27-kafka-kraft-zookeeper-removal.excalidraw
**Type:** Contrarian side-by-side architecture — ZooKeeper-based controller (rose) vs KRaft self-managed quorum (teal), joined by a "KIP-500" arrow, with a mechanism-shift callout and a war-story callout beneath.
**Color scheme:** Rose for the ZooKeeper-based design (not "wrong," just the wrong shape at scale), teal for KRaft, slate for the neutral mechanism-shift callout, amber for the KAFKA-6879 war story. No blanket red/green — ZooKeeper was the right call in 2011; it stopped being the right call at 200,000 partitions.
**Screenshottable stat:** "ZooKeeper-based controller failover: 20+ minutes on large clusters. KRaft controller failover: under 1 second, typically — because standby controllers already hold the state before the vote."

### Layout

```
Title: "Kafka's Team Spent a Decade Tuning ZooKeeper. The Fix Was Deleting It."
Subtitle: "KIP-500 (2019) → KRaft marked production-ready in Kafka 3.3 (Oct 2022) — replacing an external, session-based coordination service with a Raft quorum embedded in Kafka itself"

[SIDE-BY-SIDE ARCHITECTURE]

Left box (rose)                                    Right box (teal)
ZOOKEEPER-BASED CONTROLLER (2011–2022)              KRAFT SELF-MANAGED QUORUM (KIP-500)
• Controller election via an ephemeral znode        • Controller nodes are Raft voters
• On failover: reload the ENTIRE metadata           • Standby controllers are Raft followers,
  tree from ZK — every topic, partition,              already replaying the metadata log —
  replica assignment, in-sync-replica set              no reload needed when a vote happens
• Watches are one-shot: re-arm, then fan            • Brokers tail a log of deltas instead of
  out a full UpdateMetadataRequest to                  receiving full-state RPC fan-out on
  every broker, on every single change                 every metadata change

FAILOVER: 20+ MINUTES on large clusters             FAILOVER: UNDER 1 SECOND, typically

                          --- KIP-500 --->

[CALLOUT — the mechanism shift, slate]
THE MECHANISM SHIFT
O(total partitions) full-state reload on every failover, plus O(N) RPC fan-out on every metadata change → O(1)
incremental log replay — because standby controllers already hold the state before the vote ever happens.

[WAR STORY — amber]
WHAT ZK TUNING COULDN'T FIX
KAFKA-6879: a ZooKeeper session expiration deadlocked the controller's own internal lock against its own
expiry-handling latch, leaving a "zombie" controller — brokers kept fetching, but none ever got another
directive again, silently, until someone restarted it by hand.

[REFLECTION — footnote]
Sometimes the slow thing isn't slow because it needs tuning. It's slow because your control plane's source
of truth lives in somebody else's system.
```
