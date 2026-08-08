<!-- sources -->
<!-- Primary: -->
<!--   Uber Engineering Blog, "Ringpop: Building a scalable and fault-tolerant application layer" -->
<!--     https://www.uber.com/blog/ringpop-open-source-nodejs-library/ (also mirrored at eng.uber.com and -->
<!--     regional uber.com/*/blog paths) — title, existence, and framing corroborated via multiple independent -->
<!--     web-search-result excerpts; direct WebFetch of uber.com and eng.uber.com returned EGRESS_BLOCKED under -->
<!--     this session's network policy (same class of gateway-level denial noted on prior posts in this series). -->
<!--   uber-node/ringpop-common, "Architecture, Design, and Implementation" (fetched directly, GitHub) — -->
<!--     https://github.com/uber-node/ringpop-common/blob/master/docs/architecture_design.md -->
<!--   uber-node/ringpop-common, "Partitions" / split-brain healing doc (fetched directly, GitHub) — -->
<!--     https://github.com/uber-node/ringpop-common/blob/master/docs/partitions.md -->
<!--   uber/cadence, GitHub Issue #2471, "Migrate away from Ringpop use in cadence" (fetched directly) — -->
<!--     https://github.com/uber/cadence/issues/2471 -->
<!-- Corroborating: -->
<!--   Massive Technical Interview Tips, "Uber Ringpop" — https://massivetechinterview.blogspot.com/2015/10/uber-ringpop.html -->
<!--   Dilip Kumar, "Ringpop: A scalable and fault-tolerant application-layer sharding strategy" (Medium) — -->
<!--     https://dilipkumar.medium.com/ringpop-a-scalable-and-fault-tolerant-application-layer-sharding-strategy-7910ab39b9c5 -->
<!--   Archon, "How Uber Built Their Dispatch System" (uberblack monolith / in-memory trip state / geospatial matching) — -->
<!--     https://archon-eight.vercel.app/company-architecture/uber-dispatch -->
<!--   High Scalability, "Brief History of Scaling Uber" — https://highscalability.com/brief-history-of-scaling-uber/ -->
<!--   ringpop.readthedocs.io, "Architecture, Design, and Implementation" — https://ringpop.readthedocs.io/en/latest/architecture_design.html -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Ringpop = embeddable Node.js library used across Uber's dispatch services: a consistent hash ring for -->
<!--   application-layer sharding + a SWIM-variant gossip protocol for cluster membership, no external coordinator. -->
<!-- 2. Consistent hashing: FarmHash as the hash function, a red-black tree backing the ring (O(log n) lookup/ -->
<!--   insert/removal), a uniform number of replica points added per node for even load distribution. -->
<!-- 3. SWIM gossip: nodes ping each other at random (ping / ping-req), the "disseminator" piggybacks membership -->
<!--   changes onto ping traffic and tracks a propagation count per change, membership carries alive/suspect/ -->
<!--   faulty status plus an incarnation number (logical clock) per member. Ring + membership checksums detect -->
<!--   divergence between nodes. -->
<!-- 4. Request routing: "handle or forward" — a node hashes the key, and if it isn't the owner, forwards the -->
<!--   request over TChannel (Uber's RPC transport) to whoever is; TChannel is documented as supporting roughly -->
<!--   20,000-40,000 operations/sec. Clients don't need to know the sharding scheme. -->
<!-- 5. Split-brain: on a network partition, nodes on each side individually and correctly conclude the other -->
<!--   side's nodes are faulty. Ringpop's default behavior keeps "faulty" members in the membership list rather -->
<!--   than deleting them (distinguishing it from vanilla SWIM), enabling a documented two-phase "healing" -->
<!--   algorithm (compatibility check via reincarnation/version bumps, then merge) that reconciles the two -->
<!--   partitions' membership lists back into one ring once connectivity is restored. -->
<!-- 6. Cadence (Uber's own workflow orchestration engine, later donated as the basis for Temporal) reused Ringpop -->
<!--   for the same shard-ownership purpose. Per Cadence's own GitHub issue tracker, the team moved off Ringpop -->
<!--   because it was deprecated (no support/new features), showed high CPU usage at scale, and its TChannel -->
<!--   dependency conflicted with adding gRPC support. They evaluated Zookeeper/etcd/Consul (rejected: extra -->
<!--   external dependency, consistency-over-availability tradeoff) and a persistence-layer-based membership -->
<!--   scheme (rejected: doesn't scale), and chose Serf — a different, actively maintained gossip library — -->
<!--   specifically because it preserved the same sub-1-2-second failure detection Ringpop provided. -->
<!-- 7. Uber's original dispatch system began as a monolithic Python app ("uberblack", SQLAlchemy + Postgres); by -->
<!--   2014 deployments took hours and a single bug could take down the whole platform, driving the move to -->
<!--   sharded, in-memory, service-oriented dispatch (trip state machine: SEARCHING/MATCHED/ARRIVED/IN_PROGRESS/ -->
<!--   COMPLETED/CANCELLED) where sub-second geospatial matching ruled out a database round trip per update. -->
<!-- Note: no public source in this search gave an exact node count or exact production year for Uber's original -->
<!--   Ringpop-backed dispatch cluster; those specifics are not claimed below. Numbers used (TChannel throughput, -->
<!--   Cadence's sub-1-2s failure detection) are the ones directly documented in the sources above. -->

# Every Request to Uber's Dispatch Cluster Could Hit the Wrong Machine — On Purpose

**Date:** 2026-08-08
**Company:** Uber
**Category:** infrastructure
**Post type:** narrative
**Opening style:** mid_scene
**Slug:** uber-ringpop-swim-gossip-consistent-hashing
**Character count (LinkedIn):** ~2790

---

## LinkedIn Post

In 2014, a driver's location ping could land on any of hundreds of machines in Uber's dispatch cluster. No rule said which one — and that was fine, because the cluster wasn't built to route a request to the right machine. It was built to route it to any machine, and let that machine figure out where the request belonged.

Dispatch matches millions of driver pings against open ride requests in well under a second. That match state has to live in memory — a database round trip per ping is too slow at that volume. So the cluster shards itself: each node keeps a slice of drivers and trips in-process.

Sharding creates a routing problem. The obvious fix, driver_id % N, fails the moment N changes — add or remove one machine and modulo remaps almost every key at once, with no failure story either: a dead node's shard just disappears until a human notices. Put a shared datastore behind a load balancer instead, and every request pays a database round trip anyway — erasing the reason state moved into memory.

Uber built Ringpop to make the cluster own this itself. A consistent hash ring — FarmHash into a red-black tree, O(log n) lookups — means a node joining or leaving only remaps its own slice, not the whole ring. Membership is tracked by SWIM gossip: nodes ping each other at random, and every ping piggybacks the newest changes it knows, so news about any node spreads by infection in a few rounds — no coordinator, no ZooKeeper. Because a client can land on any node, every request goes through handle-or-forward: hash the key, check the local ring, and if you're not the owner, forward over TChannel to whoever is.

Nothing here is free. Full gossip means every node eventually hears every change — chatter that grows with cluster size, not a flat cost. A real network partition breaks SWIM's core assumption: nodes on each side correctly, individually decide the other side is faulty and delete them — so both halves can end up believing they alone own the whole ring. Split brain.

Ringpop's answer wasn't prevention — you can't tell "the other side died" from "the network broke" from inside the partition. It keeps faulty members in the list instead of deleting them, tagged with an incarnation number, so a healed network still has shared history on both sides to reconcile into one ring automatically.

Ringpop is retired now. Cadence, Uber's own workflow engine, reused it for the same shard-ownership job, hit rising CPU and an unmaintained dependency chain, and migrated to Serf — a different gossip library, chosen to keep the same sub-2-second failure detection while dropping Ringpop's baggage. The gossip idea wasn't wrong. The implementation just had a shelf life.

Sources in comments.

#SystemDesign #Uber #DistributedSystems #Sharding

---

## Twitter / X Version

1/ 2014: a driver's location ping could land on any of hundreds of machines in Uber's dispatch cluster. No rule said which one. That was on purpose — the cluster wasn't built to route to the right machine, it was built to route anywhere and let that machine sort it out.

2/ Dispatch matches millions of driver pings to open ride requests in well under a second. Match state has to live in memory — a DB round trip per ping is too slow at that volume. So the cluster shards itself: each node holds a slice of drivers/trips in-process.

3/ Obvious fix: driver_id % N. Fails the moment N changes — one node added or removed remaps almost every key at once, and a dead node's shard just vanishes until a human notices. A shared DB behind a load balancer dodges the reshuffle but brings back the round trip.

4/ Uber's answer: Ringpop. Consistent hash ring (FarmHash → red-black tree, O(log n)) so a node joining/leaving remaps only its own slice. SWIM gossip tracks membership — pings piggyback the latest changes, spreading by infection in a few rounds. No coordinator, no ZooKeeper.

5/ Any client can hit any node. Every request goes through handle-or-forward: hash the key, check the local ring, and if you're not the owner, forward over TChannel to whoever is.

6/ Cost: full gossip means every node eventually hears every change — chatter that grows with cluster size. A real network partition breaks SWIM's core assumption: both sides correctly, individually decide the other is faulty and delete it. Split brain.

7/ Fix isn't prevention, it's recovery: faulty members stay in the list instead of getting deleted, tagged with an incarnation number, so once the network heals, both sides still share enough history to merge back into one ring automatically.

8/ Ringpop's retired now. Cadence, Uber's own workflow engine, reused it, hit rising CPU and an unmaintained dependency chain, and moved to Serf — chosen to keep the same sub-2-second failure detection. The gossip idea wasn't wrong. The implementation had a shelf life.

---

## Excalidraw Diagram

**File:** 2026-08-08-uber-ringpop-swim-gossip-consistent-hashing.excalidraw
**Type:** Structural snapshot (consistent hash ring + handle-or-forward request sequence) paired with a before/after split-brain-to-healing panel.
**Color scheme:** Indigo for the ring's entry node and the healed/normal state, amber for the highlighted owner node and the "forward" arrow, emerald for the gossip/healing mechanism, rose reserved specifically for the faulty/partitioned state (earned here — that side really is broken until it heals), slate for neutral structure and labels. No blanket red=bad/green=good pass — the ring itself is drawn in neutral slate/indigo since routing to the "wrong" node first isn't a failure, it's the design.
**Screenshottable stat:** "TChannel: 20,000-40,000 ops/sec for the forward hop. Cadence's Ringpop replacement (Serf) was chosen to keep the same sub-1-2-second failure detection."

### Layout

```
Title: "Every Request to Uber's Dispatch Cluster Could Hit the Wrong Machine — On Purpose"
Subtitle: "2014-2015 — Ringpop: a consistent hash ring + SWIM gossip let Uber's dispatch cluster shard
driver/trip state with no coordinator"

[PANEL 1 — CONSISTENT HASH RING, left]
  8 nodes (N1-N8) arranged on a dashed ring. N3 (indigo) is the "entry" node a client happened to
  connect to. N6 (amber) is the actual owner of the hashed key.
  Arrow: "client -> N3 (any node)" into the entry node.
  Dashed amber arrow: N3 -> N6 labeled "forward over TChannel (20k-40k ops/sec)".
  Caption: "FarmHash + red-black tree ring, O(log n). A node joining/leaving remaps only its own slice.
  Client can hit ANY node — wrong node forwards, never rejects."

[PANEL 2 — SWIM GOSSIP, right of panel 1]
  4 boxes in a row: Node 1 (alive) -> Node 2 (alive) -> Node 3 (suspect, amber) -> Node 4 (faulty, rose),
  connected by emerald arrows labeled "ping -> ping-req -> piggyback membership update -> incarnation++".
  Caption: "Every ping piggybacks the newest changes it knows — news spreads by infection in a few
  gossip rounds. No ZooKeeper, no external coordinator. Cost: chatter grows with cluster size."
  Note: "Cadence (Uber's workflow engine) later hit rising CPU from this at scale."

[PANEL 3 — SPLIT BRAIN -> HEALING, bottom, full width]
  Left box (indigo): "Partition A: N1-N4 — sees N5-N8 as FAULTY, ring intact on this side"
  Right box (rose): "Partition B: N5-N8 — sees N1-N4 as FAULTY, ring intact on this side"
  Jagged line between them labeled "network cut"
  Emerald arrow down, labeled "network heals"
  Merged box (emerald): "One ring again — faulty members were kept in the list (not deleted), tagged
  with an incarnation number, so gossip reconciles both views automatically once the network stops
  lying to it."
  Right-side footnote: "The mechanism that causes split-brain (no node has a global view) is the same
  one that heals it. Ringpop is retired — Cadence reused it, hit rising CPU and an unmaintained
  TChannel dependency, and migrated to Serf specifically to keep the same sub-2-second failure
  detection while dropping Ringpop's baggage."
```
