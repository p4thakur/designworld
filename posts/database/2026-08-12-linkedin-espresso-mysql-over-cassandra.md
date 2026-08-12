<!-- sources -->
<!-- Primary: -->
<!--   LinkedIn Engineering, "Introducing Espresso - LinkedIn's hot new distributed document store" (2011 launch post) -->
<!--     https://engineering.linkedin.com/espresso/introducing-espresso-linkedins-hot-new-distributed-document-store -->
<!--     — direct WebFetch of engineering.linkedin.com returned EGRESS_BLOCKED under this session's network policy -->
<!--     (same class of gateway-level denial noted on prior posts in this series, e.g. the Fastly and Netflix posts). -->
<!--     Content corroborated via multiple independent web-search-result excerpts that quote/paraphrase the post -->
<!--     directly, not from memory. -->
<!--   L. Qiao, K. Surlaker, et al., "On Brewing Fresh Espresso: LinkedIn's Distributed Data Serving Platform," -->
<!--     ACM SIGMOD 2013 — https://dl.acm.org/doi/pdf/10.1145/2463676.2465298 (existence/abstract corroborated -->
<!--     via search; direct dl.acm.org fetch not attempted after repeated EGRESS_BLOCKED pattern on this domain -->
<!--     class this session). -->
<!--   LinkedIn Engineering, "Espresso Onboarding Experiences: InMail" -->
<!--     https://engineering.linkedin.com/espresso-migration-inmail/espresso-onboarding-experiences-inmail -->
<!--   LinkedIn Engineering, "Migrating to Espresso" (Oracle -> Espresso migration retrospective) -->
<!--     https://engineering.linkedin.com/blog/2017/08/migrating-from-oracle-to-espresso -->
<!--   LinkedIn Engineering, "Solving Espresso's scalability and performance challenges to support our member base" (2023) -->
<!--     https://engineering.linkedin.com/blog/2023/solving-espresso-s-scalability-and-performance-challenges-to-sup -->
<!-- Corroborating (independent secondary sources, cross-referenced for consistency): -->
<!--   Database of Databases, "Espresso" — https://dbdb.io/db/espresso (fetch blocked; used via search excerpts) -->
<!--   Zohaib Saeed, "Inside LinkedIn Espresso: Building a Scalable Document-Relational Database" (Medium, 2026) -->
<!--     https://medium.com/@zohaibsaeed/inside-linkedin-espresso-building-a-scalable-document-relational-database-aeefdd71e0ac -->
<!--   Agustin Ignacio Rossi, "Why LinkedIn Built Its Own NoSQL Database: The Rise of Espresso" (Medium) -->
<!--     https://medium.com/@agustin.ignacio.rossi/why-linkedin-built-its-own-nosql-database-the-rise-of-espresso-cf3d685800ee -->
<!--   Apache Helix project docs, "Use cases at LinkedIn" — https://helix.apache.org/UseCases.html -->
<!-- Note: precise internal throughput/latency figures beyond what's corroborated below (InMail's ~300ms average -->
<!--   failover latency at 1024 partitions, the 2023 post's "75% latency reduction" from the HTTP/2 migration) were -->
<!--   not independently re-verifiable via direct primary-source fetch in this session (engineering.linkedin.com -->
<!--   blocked); no additional precision is claimed beyond what is corroborated across the search-result excerpts -->
<!--   above. -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Circa 2011, LinkedIn ran Oracle (RDBMS, strong consistency, expensive to shard) and Voldemort (key-value -->
<!--   store, horizontally scalable, no secondary indexes, no ordered change-capture stream) for different data. -->
<!--   Neither fit primary data needing both consistency and scale with a source-of-truth change stream. -->
<!-- 2. LinkedIn built Espresso rather than adopting a multi-master NoSQL model (e.g. Cassandra, which LinkedIn -->
<!--   already ran elsewhere): Espresso assigns exactly one master per partition, all writes for that partition -->
<!--   go through it, and replicas apply changes in the same order — "timeline consistency," giving deterministic -->
<!--   read-your-own-writes without full cross-cluster ACID coordination. -->
<!-- 3. Espresso's storage layer runs on MySQL with the InnoDB engine rather than a purpose-built storage engine, -->
<!--   because InnoDB already handles disk I/O, buffer pools, and crash recovery; its buffer pool is held outside -->
<!--   the JVM heap, which helped avoid GC-pause issues affecting LinkedIn's other large in-memory Java services. -->
<!-- 4. Architecture: a routing/partitioning layer on top of MySQL, transactionally consistent local secondary -->
<!--   indexes (Lucene-backed for text use cases like InMail, with Lucene segments stored as MySQL rows), Apache -->
<!--   Helix for cluster management (partition assignment, mastership transitions), and Databus (later succeeded -->
<!--   by Kafka in this role) as the change-data-capture pipeline streaming ordered changes downstream. -->
<!-- 5. Espresso reached production in June 2012. By January 2015 it had over a dozen production clusters. By 2017 -->
<!--   it had grown to close to 100 clusters storing roughly 420TB of source-of-truth data, powering approximately -->
<!--   30 LinkedIn applications including Member Profile, InMail, Company Pages, and the Unified Social Content -->
<!--   Platform. -->
<!-- 6. The InMail migration off Oracle split a monolithic Oracle dump into 1,024 partitions using Espresso's -->
<!--   partitioning hash function; documented average failover latency at that partition count was around 300ms. -->
<!-- 7. By 2023, at LinkedIn's 950M+ member scale, the router-to-storage-node connection model itself became the -->
<!--   bottleneck (millions of concurrent TCP connections between routers and storage nodes), which LinkedIn -->
<!--   addressed by migrating that layer to HTTP/2, reducing latency by 75% per LinkedIn's own published account -->
<!--   (after first observing a 45% throughput regression in an initial Netty-based HTTP/2 implementation that had -->
<!--   to be corrected). -->

# LinkedIn Rejected Multi-Master NoSQL. They Built a Database on Top of MySQL Instead.

**Date:** 2026-08-12
**Company:** LinkedIn
**Category:** database
**Post type:** contrarian
**Opening style:** challenge_assumption
**Slug:** linkedin-espresso-mysql-over-cassandra
**Character count (LinkedIn):** ~2530

---

## LinkedIn Post

In 2011, the industry consensus among backend engineers was blunt: relational databases don't scale, so you migrate to NoSQL and move on. LinkedIn looked at that consensus and built a new database anyway — on top of MySQL.

The problem was concrete. LinkedIn ran Oracle for data needing strong consistency and Voldemort, a key-value store, for data needing horizontal scale. Neither covered everything. Oracle didn't shard cheaply. Voldemort had no secondary indexes and no ordered change stream for downstream systems. Cassandra, which LinkedIn already ran elsewhere, gave horizontal scale — but as multi-master, any replica accepts writes and conflicts resolve later. Fine for some workloads. Bad when a member needs their own InMail or profile edit to show up immediately, which multi-master doesn't guarantee.

So instead of the trendy multi-master model, LinkedIn built Espresso: one master per partition, every write goes through it, every replica applies writes in the same order. That's "timeline consistency" — deterministic read-your-own-writes, without full cross-cluster ACID coordination.

The contrarian part: they didn't write a new storage engine. Espresso runs on MySQL's InnoDB, because InnoDB already handles disk I/O, buffer pools, and crash recovery about as well as anything available — and its buffer pool sits outside the JVM heap, sidestepping the GC-pause problem plaguing LinkedIn's other in-memory Java services. Add a routing/partitioning layer, Lucene-backed secondary indexes stored as ordinary MySQL rows, Apache Helix for cluster management, and Databus to stream ordered changes downstream. Callers see JSON over HTTP; MySQL quietly does the disk work.

Espresso hit production in June 2012. By 2015: a dozen-plus clusters. By 2017: close to 100 clusters, ~420TB of source-of-truth data, roughly 30 applications on it, including Member Profile and InMail.

We default to reaching for a new database because reusing MySQL feels like not building anything new. LinkedIn's bet was that the hard, valuable engineering was never the storage engine — it was the consistency model and partitioning logic above it.

The tradeoff didn't disappear, it moved. By 2023, at 950M+ members, the router-to-storage connection model became the bottleneck — millions of concurrent TCP connections — forcing a migration to HTTP/2 that cut latency 75%. The boring foundation bought LinkedIn a decade. Not forever.

Sources in comments.

#SystemDesign #LinkedInEngineering #Databases #DistributedSystems

---

## Twitter / X Version

1/ 2011: the industry consensus was "relational databases don't scale, go NoSQL." LinkedIn's answer was to build a new database anyway — on top of MySQL.

2/ They had Oracle (consistent, didn't shard cheaply) and Voldemort (scaled, but no secondary indexes, no ordered change stream). Cassandra could've filled the gap — except its multi-master model means conflicts resolve later, no guaranteed read-your-own-writes.

3/ That's a bad trade when a member needs their own InMail or profile edit to show up instantly. So LinkedIn skipped the trendy multi-master route.

4/ They built Espresso: one master per partition, every write goes through it, replicas apply writes in the same order. "Timeline consistency" — deterministic read-your-own-writes, without full cluster-wide ACID.

5/ The contrarian move: no new storage engine. Espresso sits on MySQL's InnoDB — it already does disk I/O, buffer pools, crash recovery well, and its buffer pool lives outside the JVM heap, dodging the GC-pause problem hitting LinkedIn's other Java services.

6/ Wrap it in routing, Lucene-backed secondary indexes stored as MySQL rows, Apache Helix for cluster management, Databus for ordered change streams. Callers get JSON over HTTP. MySQL does the real work underneath.

7/ Production: June 2012. By 2015: a dozen-plus clusters. By 2017: ~100 clusters, ~420TB of source-of-truth data, ~30 apps including Member Profile and InMail.

8/ We reach for a new database because reusing MySQL feels like not building anything. LinkedIn bet the hard part was never the storage engine — it was the consistency model on top.

9/ The tradeoff moved, not vanished. By 2023, at 950M+ members, router-to-storage connections became the bottleneck — millions of concurrent TCP connections — forcing a migration to HTTP/2 that cut latency 75%.

10/ The boring foundation bought LinkedIn a decade. Not forever.

---

## Excalidraw Diagram

**File:** 2026-08-12-linkedin-espresso-mysql-over-cassandra.excalidraw
**Type:** Side-by-side architecture comparison (obvious multi-master path vs. what LinkedIn built) paired with a 4-point growth strip from 2012 to 2023.
**Color scheme:** Violet for the multi-master path — not framed as wrong, just a different, legitimate tradeoff. Teal for Espresso's design. Amber for the growth strip, since it's neither "win" nor "loss," just scale accumulating. Slate for the closing footer. No color in this post was reused from the Fastly (slate/amber/rose/teal), Uber (indigo/amber/emerald/rose), or Netflix (rose/indigo/slate) posts.
**Screenshottable stat:** "2012: production launch. 2017: ~100 clusters, ~420TB of source-of-truth data. 2023: 950M+ members force a router-to-storage HTTP/2 migration that cuts latency 75%."

### Layout

```
Title: "LinkedIn Rejected Multi-Master NoSQL. They Built a Database on Top of MySQL Instead."
Subtitle: "2011: Espresso traded Cassandra's multi-master model for one master per partition on plain MySQL/InnoDB"

[LEFT PANEL — violet, "THE OBVIOUS PATH: MULTI-MASTER NoSQL", 3 stacked boxes]
  Box 1: "Cassandra-style multi-master: any of a partition's replicas can accept a write for the same key."
  --arrow down (violet)-->
  Box 2: "Conflicts between concurrent writes get resolved later, after the fact. Fast, near-infinite
    horizontal scale."
  --arrow down (violet)-->
  Box 3 (caption): "No guaranteed read-your-own-writes. Bad when a member needs their own InMail or
    profile edit to show up immediately."

[RIGHT PANEL — teal, "WHAT LINKEDIN BUILT: ESPRESSO ON MYSQL", 3 stacked boxes, mirrors left panel]
  Box 1: "Espresso: exactly one master per partition. Every write for that partition goes through it,
    in order."
  --arrow down (teal)-->
  Box 2: "Storage underneath is plain MySQL InnoDB — disk I/O, buffer pools, crash recovery already
    solved. Buffer pool lives outside the JVM heap, dodging Java GC pauses."
  --arrow down (teal)-->
  Box 3 (caption): "Timeline consistency: deterministic order, read-your-own-writes — without full
    cross-cluster ACID coordination."

[GROWTH STRIP — amber, "GROWTH: THE BORING FOUNDATION SCALES, THEN STRAINS", 4 boxes left to right]
  1. "June 2012 — Espresso goes to production, replacing parts of Oracle and Voldemort."
  2. "2015 — Over a dozen production clusters running on Espresso."
  3. "2017 — ~100 clusters, ~420TB of source-of-truth data, ~30 apps incl. Member Profile & InMail."
  4. "2023 — 950M+ members. Router-storage connections become the new bottleneck; HTTP/2 migration
     cuts latency 75%."

[FOOTER, slate band, full width]
  "Sometimes the right architecture isn't a new database. It's a strict, deterministic consistency
  layer wrapped around the boring storage engine you already trust — until connection scaling becomes
  the next boring problem to solve."
```
