<!-- sources -->
<!-- Primary: -->
<!--   Verbitski, Gupta, Saha, et al., "Amazon Aurora: Design Considerations for High Throughput Cloud-Native Relational -->
<!--   Databases," SIGMOD '17, pp. 1041-1052 — https://www.amazon.science/publications/amazon-aurora-design-considerations-for-high-throughput-cloud-native-relational-databases -->
<!--   (PDF mirror: https://www.cs.purdue.edu/homes/bb/cs542-23Fall/readings/impl/sigmod-17-amazon-aurora-design.pdf) -->
<!--   Werner Vogels / All Things Distributed, "Weekend Reading: Amazon Aurora: Design Considerations..." (May 2017) — -->
<!--     https://www.allthingsdistributed.com/2017/05/amazon-aurora-design-considerations.html -->
<!--   AWS, "Amazon Aurora FAQs" (crash recovery time) — https://aws.amazon.com/rds/aurora/faqs/ -->
<!-- Corroborating: -->
<!--   Adrian Colyer, "the morning paper" summary — -->
<!--     https://blog.acolyer.org/2019/03/25/amazon-aurora-design-considerations-for-high-throughput-cloud-native-relational-databases/ -->
<!--   Murat Demirbas, "Amazon Aurora: Design Considerations... + On Avoiding Distributed Consensus" — -->
<!--     https://muratbuffalo.blogspot.com/2022/03/amazon-aurora-design-considerations-and.html -->
<!--   Hacker News thread quoting the Aurora crash-recovery FAQ — https://news.ycombinator.com/item?id=13073718 -->
<!-- Note: direct WebFetch of allthingsdistributed.com, blog.acolyer.org, muratbuffalo.blogspot.com, and aws.amazon.com -->
<!-- all returned HTTP 403 under this session's egress policy (same class of gateway-level denial hit on prior posts in -->
<!-- this series). Facts below were cross-checked across multiple independent web-search-result excerpts that quote or -->
<!-- closely paraphrase the primary sources directly, including the exact benchmark figures from the SIGMOD paper. -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. SIGMOD '17 benchmark (30-min Sysbench run): stock MySQL on mirrored EBS completed 780,000 transactions at an -->
<!--   average of 7.4 disk I/Os per transaction. Aurora completed 27,378,000 transactions in the same window at 0.95 -->
<!--   I/Os per transaction on the database node -- a 7.7x reduction in per-transaction network I/O despite Aurora -->
<!--   physically writing to 6 storage replicas per log record (vs. MySQL mirroring to 1 standby). -->
<!-- 2. Traditional MySQL commit path amplification: redo log (InnoDB WAL), binlog (archived for point-in-time restore), -->
<!--   double-write buffer (torn-page protection), the modified data page itself, and metadata/frm files -- multiple -->
<!--   distinct writes per logical change, each doubled again under synchronous AZ-to-AZ EBS mirroring (e.g. RDS Multi-AZ). -->
<!-- 3. Aurora's storage engine ships ONLY redo log records across the network to a purpose-built distributed storage -->
<!--   fleet -- 6 copies of each protection group, 2 per Availability Zone across 3 AZs. Materialization of log records -->
<!--   into data pages, checkpointing, garbage collection, and backup/restore all happen inside the storage layer, off -->
<!--   the write-commit critical path. -->
<!-- 4. Quorum model: writes are durable once 4-of-6 storage nodes acknowledge (write quorum); reads are guaranteed to -->
<!--   observe the latest write once 3-of-6 are consulted (read quorum). Because 4+3 > 6, any write quorum and any read -->
<!--   quorum must share at least one node, guaranteeing read-your-writes without a distributed consensus (e.g. Paxos) -->
<!--   round-trip on the hot path -- the paper frames this explicitly as avoiding distributed consensus for ordinary I/O. -->
<!-- 5. Crash recovery: because the storage layer continuously applies/coalesces the redo log in the background (parallel, -->
<!--   distributed, asynchronous) regardless of whether the database engine has crashed, Aurora restarts and becomes -->
<!--   available in well under a minute, vs. traditional single-threaded redo-log replay from the last checkpoint -->
<!--   (typically ~5 minutes between checkpoints) in MySQL/Postgres-style engines. -->

# Aurora's Contrarian Bet: Stop Replicating the Database. Replicate the Log.

**Date:** 2026-08-04
**Company:** Amazon Web Services (Aurora team)
**Category:** database
**Post type:** contrarian
**Opening style:** specific_number
**Slug:** aws-aurora-log-is-the-database
**Character count (LinkedIn):** ~2760

---

## LinkedIn Post

In a 30-minute benchmark AWS published themselves: stock MySQL on mirrored storage did 780,000 transactions, at 7.4 disk I/Os each. Aurora did 27,378,000 transactions in the same window — while writing to six storage nodes on every commit. More copies, fewer I/Os, 35x the throughput. That's the whole redesign in one benchmark.

The obvious way to survive a zone failure is synchronous mirroring — replicate the whole database to a standby before you ack the commit. It's literally what RDS Multi-AZ does, and it's what every "add a hot standby" tutorial teaches.

Here's why it doesn't scale. A single MySQL commit isn't one write — it's the redo log, the binlog, the double-write buffer (guarding against torn pages), the data page itself, and metadata. Five writes for one logical change, which is where that 7.4-I/O average comes from. Mirror that synchronously and all five round-trip to a remote box before your commit returns. Add a replica for read scaling and you've chained another synchronous hop onto every write. Cost scales with how much you write, not how many replicas you have.

Aurora's team asked which of those five writes is actually the source of truth. It's the redo log — every data page can be rebuilt by replaying log records against a base version. So the engine stopped shipping pages, binlogs, and double-write buffers over the network. It ships only redo log records, to 6 storage nodes across 3 AZs. A write is durable once 4 of 6 ack it; a read is current once you gather 3 of 6. 4+3 > 6, so those sets always overlap by at least one node — a read can't miss the latest commit, and checking that is a local vote against version numbers the nodes already hold, not a consensus round-trip.

Turning log into pages — materialization, checkpointing, backup — moves entirely into the storage layer, off the commit path. That's also why Aurora recovers from a crash in under a minute: it doesn't replay the log from the last checkpoint itself, single-threaded, the way MySQL does. The storage layer has already been applying it continuously in the background, crash or no crash.

We default to full-object mirroring because it's conceptually simple — copy the whole thing, every replica is interchangeable. Fine at two replicas. Stops being fine once every replica pays the full write-amplification tax, forever.

The real cost: this only pays off if you already operate a purpose-built quorum storage fleet under every database you run. Ship "just the log" without owning that fleet and you've traded a boring standby for a harder distributed-storage problem, minus the engineering AWS amortizes across everyone else's databases.

Sources in comments.

#SystemDesign #DistributedSystems #AWS #DatabaseEngineering

---

## Twitter / X Version

1/ AWS's own benchmark: MySQL on mirrored storage did 780K transactions in 30 min, 7.4 disk I/Os each. Aurora did 27.4M transactions in the same window — while writing to 6 storage nodes on every commit. More copies, fewer I/Os, 35x the throughput.

2/ The obvious durability move is synchronous mirroring: replicate the whole DB to a standby before you ack the commit. It's what RDS Multi-AZ does. It's what every "add a hot standby" tutorial teaches. It doesn't scale, and here's the mechanism why.

3/ A MySQL commit isn't one write. It's the redo log, the binlog, the double-write buffer, the data page, and metadata — 5 writes for one change. Mirror that synchronously and all 5 round-trip to a remote box before your commit returns. More replicas = more chained hops.

4/ Aurora asked which of those 5 writes is actually the truth. The redo log — pages are just replayed log records. So the engine ships only the log, to 6 storage nodes across 3 AZs. Write durable at 4-of-6 ack. Read current at 3-of-6. 4+3>6 means those sets always overlap.

5/ No consensus round-trip needed to check that overlap — just a local vote against version numbers the storage nodes already hold. Materializing pages, checkpointing, backup all move off the commit path into the storage layer. Crash recovery: under a minute, not MySQL's ~5-minute single-threaded replay.

6/ We default to full-object mirroring because it's simple — copy the whole thing, every replica is interchangeable. Fine at 2 replicas. The catch with Aurora's move: it only pays off if you already run a quorum storage fleet under every DB you own. Otherwise you just built a harder problem.

---

## Excalidraw Diagram

**File:** 2026-08-04-aws-aurora-log-is-the-database.excalidraw
**Type:** Side-by-side architecture comparison (traditional synchronous mirroring vs. Aurora's log-only quorum storage), with the write/read quorum overlap shown structurally.
**Color scheme:** Slate for the traditional MySQL/EBS-mirror side — not "wrong," just an older, well-understood trade. Amber for Aurora's storage fleet, since it's the unconventional choice, not a "correct/green" one — the diagram avoids red=bad/green=good since neither side is a mistake, just a different point on the same trade-off curve.
**Screenshottable stat:** "MySQL: 780,000 tx / 7.4 I/Os each. Aurora: 27,378,000 tx / 6 storage writes each. 7.7x fewer I/Os per transaction."

### Layout

```
Title: "Aurora's Contrarian Bet: Stop Replicating the Database. Replicate the Log."
Subtitle: "SIGMOD '17 benchmark — how shipping only redo log records cut per-transaction network I/O 7.7x versus mirroring the whole write path"

[LEFT PANEL — slate, "TRADITIONAL: SYNCHRONOUS MIRROR (e.g. RDS Multi-AZ)"]
  Box "Primary (AZ1)" with 5 stacked mini-labels inside: "redo log", "binlog", "double-write buffer", "data page", "metadata"
  Arrow (slate, labeled "all 5, synchronous, over network") pointing to
  Box "Standby (AZ2)" — same 5 stacked labels
  Caption under panel: "780,000 tx / 30 min — 7.4 I/Os per transaction"

[RIGHT PANEL — amber, "AURORA: LOG-ONLY QUORUM STORAGE"]
  Small box "DB Engine" with single label "redo log record only"
  6 arrows (amber, labeled "1 write type") fanning out to 6 small storage-node rectangles, grouped visually into
  3 pairs labeled "AZ1", "AZ2", "AZ3" (2 nodes per AZ)
  4 of the 6 storage nodes highlighted (amber fill) with caption "4-of-6 = write quorum (durable)"
  A different overlapping set of 3 nodes outlined (amber outline only) with caption "3-of-6 = read quorum (current)"
  Small note pointing at the one node common to both sets: "4+3 > 6 — quorums always overlap by ≥1 node"
  Caption under panel: "27,378,000 tx / 30 min — 0.95 I/Os per transaction on the DB node"

[FOOTNOTE — slate]
Because the write quorum and read quorum always share a node, a read can never miss the latest committed write —
no consensus round-trip required, just a version check against numbers the storage nodes already hold.
Crash recovery: Aurora restarts in under a minute because the storage layer applies the log continuously in the
background; traditional engines replay single-threaded from the last checkpoint, typically ~5 minutes of log.
```
