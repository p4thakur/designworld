<!-- sources -->
<!-- Primary: -->
<!--   Uber Engineering Blog, "Why Uber Engineering Switched from Postgres to MySQL" (July 26, 2016) -->
<!--   URL: https://www.uber.com/en-US/blog/postgres-to-mysql-migration/ -->
<!--   Uber Engineering Blog, "Designing Schemaless, Uber Engineering's Scalable Datastore Using MySQL" (2016) -->
<!--   URL: https://www.uber.com/blog/schemaless-part-one-mysql-datastore/ -->
<!-- Note: direct fetch of uber.com, eng.uber.com, news.ycombinator.com, and use-the-index-luke.com all returned -->
<!-- HTTP 403 under this session's egress policy (same class of gateway-level denial hit on prior posts in this -->
<!-- series). Facts below were cross-checked across multiple independent search-result excerpts that quote or -->
<!-- closely paraphrase the primary Uber post directly, plus corroborating secondary coverage: -->
<!--   LWN.net, "Why Uber dropped PostgreSQL" — https://lwn.net/Articles/696085/ -->
<!--   InfoQ, "Uber Engineering Switches from Postgres to MySQL" — https://www.infoq.com/news/2016/08/Uber-Engineering-Postgres-MySQL -->
<!--   Hacker News discussion (2021 repost of the 2016 post) — https://news.ycombinator.com/item?id=26283348 -->
<!--   Use The Index, Luke!, "On Uber's Choice of Databases" (technical rebuttal quoting the original post) — -->
<!--     https://use-the-index-luke.com/blog/2016-07-29/on-ubers-choice-of-databases -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Published July 26, 2016 — exactly ten years before this post's date. -->
<!-- 2. Write amplification: Postgres secondary indexes point directly at a row's physical location (heap -->
<!--    tuple), so updating any column requires rewriting every index on that row, even ones on columns that -->
<!--    didn't change. MySQL/InnoDB secondary indexes point at the primary key instead — one extra lookup hop — -->
<!--    so a row move only requires updating the clustered primary index. -->
<!-- 3. Vacuum/compaction: reclaiming space from updated or deleted rows in Postgres requires the autovacuum -->
<!--    process to run a full table scan to find dead tuples, because there is no compact list of which rows -->
<!--    are garbage. MySQL/InnoDB keeps eligible-for-cleanup rows directly available via the rollback segment. -->
<!-- 4. Replica MVCC: Postgres replicas apply the same physical WAL writes as the master and can block or cancel -->
<!--    long-running read queries on the replica when replay conflicts with them. -->
<!-- 5. The Postgres 9.2 corruption incident: during a routine version upgrade, a bug in Postgres 9.2 caused data -->
<!--    corruption affecting a small number of rows per database (some entries not correctly marked inactive). -->
<!--    Because Postgres ships physical, page-level WAL replication, the corruption replayed onto every standby -->
<!--    along with legitimate writes. Uber traced the bug and found the newly promoted master was clean but the -->
<!--    existing replicas were not; the fix was resyncing every replica from a fresh snapshot of the master, a -->
<!--    manual, laborious process. MySQL's logical-statement-level replication means an equivalent bug could not -->
<!--    corrupt a B-tree the same way, since rebalancing operations aren't replicated as raw physical page writes. -->
<!-- 6. Schemaless: in early 2014, Uber had already run out of usable space/headroom on its Postgres-backed trip -->
<!--    tables and built Schemaless, an append-only, horizontally sharded key-value datastore layered on plain -->
<!--    MySQL (InnoDB). It has been Uber's datastore for core trip data in production since October 2014. -->

# Postgres's Indexes Point at a Disk Address. That One Design Choice Cost Uber a Two-Year Migration.

**Date:** 2026-07-26
**Company:** Uber
**Category:** databases
**Post type:** confessional
**Opening style:** number_mismatch
**Slug:** uber-postgres-to-mysql-migration
**Character count (LinkedIn):** ~2,106

---

## LinkedIn Post

Postgres indexes point straight at a row's physical location on disk. MySQL's InnoDB indexes point at the primary key instead — one extra hop. That single architectural difference is most of the reason Uber ripped Postgres out, ten years ago this week.

In Uber's early days, Postgres was the obvious pick: mature, well understood, and the team already knew it. It worked fine when the fleet was small.

Then trip volume compounded, and the design started working against them. Because Postgres indexes reference a row's physical offset directly, updating one column meant rewriting every index on that row, not just the one that changed. Write amplification scaled with index count, not with what actually changed. Autovacuum made it worse: reclaiming space from dead rows requires scanning the whole table, because Postgres keeps no compact list of "what's garbage," the way MySQL's rollback segment does.

Replication carried a subtler risk. Postgres ships its write-ahead log at the physical page level. During a routine version upgrade, a bug in Postgres 9.2 corrupted a handful of index pages — and because replication is physical, that corruption replayed onto every standby right along with everything else. The newly promoted master turned out clean; the replicas weren't. The fix was resyncing every replica from a fresh snapshot, by hand. A logical-replication bug stays contained to the rows it got wrong. A physical one can take out a whole B-tree.

By early 2014, Uber had already run out of room on its Postgres trip tables and built Schemaless — an append-only, horizontally sharded datastore running on plain MySQL, live in production by October of that year. It wasn't really a rewrite. It was an admission that the row-store abstraction their trip pipeline was built on wasn't going to survive the write volume, no matter how much hardware sat behind it.

Postgres wasn't the wrong database in 2011. It was the wrong database for what Uber became by 2015. Most "we regret our database" stories are growth stories wearing a technology costume.

#SystemDesign #Databases #PostgreSQL #MySQL

---

## Twitter / X Version

1/ Postgres indexes point at a row's physical disk location. MySQL's InnoDB indexes point at the primary key instead — one extra hop. That's most of why Uber ripped Postgres out, exactly ten years ago this week.

2/ Every column update rewrote every index on the row, not just the one that changed — write amplification tied to index count, not to what actually changed. Autovacuum needed a full table scan just to find garbage rows to reclaim.

3/ Then a Postgres 9.2 bug corrupted index pages during a routine upgrade. Because Postgres replicates physically, that corruption replayed onto every standby. The newly promoted master was clean. The replicas weren't. They resynced every one from a fresh snapshot, by hand.

4/ By early 2014 they'd already outgrown Postgres on the trip tables and built Schemaless — an append-only, sharded store on plain MySQL, live in prod by October 2014.

5/ Postgres wasn't wrong in 2011. It was wrong for what Uber became by 2015.

---

## Excalidraw Diagram

**File:** 2026-07-26-uber-postgres-to-mysql-migration.excalidraw
**Type:** Confessional timeline — four stages (early days working fine → write-amplification bind → the 9.2 corruption incident → the Schemaless admission) with the actual architectural cause called out separately from the timeline boxes.
**Color scheme:** Teal for "worked fine at small scale" (the routine, unremarkable early state), amber for the write-amplification/vacuum bind, rose for the physical-replication corruption incident, indigo for Schemaless as the resolution. No blanket red/green — Postgres wasn't a bad database, it was a mismatched one for this specific write pattern at this specific scale.
**Screenshottable stat:** "Postgres: index → physical row offset (any column update rewrites every index). MySQL/InnoDB: index → primary key (one extra hop, only the clustered index moves). A Postgres 9.2 bug during a routine upgrade corrupted index pages on a few rows per database — and because replication is physical, it replayed onto every standby anyway."

### Layout

```
Title: "Postgres's Indexes Point at a Disk Address. That One Design Choice Cost Uber a Two-Year Migration."
Subtitle: "July 26, 2016 (ten years to this post) — why Uber Engineering moved its core trip data off Postgres and onto MySQL"

[TIMELINE — horizontal, four stages]

Stage 1 (teal)               Stage 2 (amber)                Stage 3 (rose)                   Stage 4 (indigo)
Early days                    As trips scaled up              During a routine upgrade         Early 2014 → Oct 2014
POSTGRES WORKS FINE            WRITE AMPLIFICATION BINDS       9.2 BUG CORRUPTS REPLICAS         SCHEMALESS GOES LIVE
Mature, well understood,       Indexes point at a row's        A Postgres 9.2 bug corrupted      Ran out of room on Postgres
team already knew it.          physical offset — one column    a handful of index pages on       trip tables. Built an
Fine at small fleet size.      update rewrites every index     upgrade. Physical replication     append-only, sharded
                                on the row. Autovacuum needs    replayed the corruption onto      datastore on plain MySQL —
                                a full table scan to find       every standby. New master was     live in production by
                                garbage rows to reclaim.        clean; replicas weren't.          October 2014.

[CALLOUT — the actual architectural cause, set apart from the timeline]
THE ONE-HOP DIFFERENCE
Postgres secondary indexes point straight at a row's physical location on disk — fast to read, expensive to
write, because every index on a row must be rewritten on any update. MySQL/InnoDB secondary indexes point at
the primary key instead. One extra lookup hop at read time buys back most of that write cost, and means a
row's physical move only touches the clustered primary index.

[WHAT CHANGED — indigo]
Resynced every corrupted replica from a fresh master snapshot by hand. Built Schemaless: cells are pure
INSERT-only JSON blobs, keyed by UUID plus an auto-incrementing added_id, running on ordinary MySQL/InnoDB —
no in-place updates, no index rewrite storm, no full-table vacuum scans.

[REFLECTION — teal, footnote]
Postgres wasn't the wrong database in 2011. It was the wrong database for what Uber became by 2015. Most
"we regret our database" stories are growth stories wearing a technology costume.
```
