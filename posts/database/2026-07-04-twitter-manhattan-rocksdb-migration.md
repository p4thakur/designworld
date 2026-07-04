<!-- sources -->
<!-- Primary: Twitter Engineering Blog, "Manhattan, our real-time, multi-tenant distributed database for Twitter scale" (2014) -->
<!-- URL: https://blog.x.com/engineering/en_us/a/2014/manhattan-our-real-time-multi-tenant-distributed-database-for-twitter-scale -->
<!-- Primary: Twitter Engineering Blog, "Adopting RocksDB within Manhattan" (2021, @gvteja) -->
<!-- URL: https://blog.x.com/engineering/en_us/topics/infrastructure/2021/adopting-rocksdb-within-manhattan -->
<!-- Primary: Twitter Engineering Blog, "Data transfer in Manhattan using RocksDB" (2022) -->
<!-- URL: https://blog.x.com/engineering/en_us/topics/infrastructure/2022/data-transfer-in-manhattan-using-rocksdb -->
<!-- Corroborating (cross-checked, consistent on figures below): -->
<!--   https://www.infoq.com/news/2014/05/twitters-manhattan/ -->
<!--   https://dirtysalt.github.io/html/manhattan.html (mirror of the 2014 post) -->
<!--   https://x.com/i/web/status/1387087571314831360 (Twitter Engineering: "The RocksDB migration, a three-year effort, is now complete") -->
<!-- Note: direct fetch of blog.x.com and its mirrors returned HTTP 403 under this session's egress policy; -->
<!-- facts and figures below are cross-checked across multiple independent search-result excerpts quoting the -->
<!-- three primary posts directly, rather than a single full-text fetch. -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Manhattan launched 2014 as Twitter's in-house distributed key-value store after Cassandra couldn't scale -->
<!--    to new machine sets at Twitter's growth rate; clusters handle tens of millions of queries per second -->
<!-- 2. Manhattan originally shipped with two storage engines: SSTable (in-house LSM, write-optimized) and -->
<!--    MhBtree (B-tree, read-optimized); most production workloads are read-heavy, so most clusters ran on MhBtree -->
<!-- 3. MhBtree was implemented as a MySQL storage plugin using the MySQL handler interface -- ~15k lines of C++ -->
<!--    plugin code, requiring deep MySQL/InnoDB internals knowledge to modify -->
<!-- 4. Because each storage engine used a different on-disk file format, cross-engine migration required generic -->
<!--    streaming (replaying data as individual write requests) instead of direct file transfer -- this behaved -->
<!--    like a sustained spike in write traffic and risked write-stalls on the receiving cluster -->
<!-- 5. Twitter adopted RocksDB (Facebook's open-source, LSM-based embedded storage engine) as Manhattan's unified -->
<!--    replacement; productionizing it took about a year, complete by mid-2018 -->
<!-- 6. Full migration (including Tweets, User Profiles, Direct Messages clusters) was a three-year effort, -->
<!--    2018-2021, covering trillions of keys and petabytes of storage -->
<!-- 7. Results: same or better latency than the engines it replaced, lower CPU utilization, ~50% lower disk -->
<!--    space per node; ~1/3 of the storage-engine codebase deleted, ~10% of the entire Manhattan codebase deleted -->

# Twitter's Manhattan: Retiring the Homegrown Storage Engines

**Date:** 2026-07-04
**Company:** Twitter (X)
**Category:** databases
**Post type:** structured
**Opening style:** the_decision
**Slug:** twitter-manhattan-rocksdb-migration
**Character count (LinkedIn):** ~2,105

---

## LinkedIn Post

Twitter's Manhattan database ran on two storage engines, both built in-house, both tuned to Twitter's exact workload. In 2018, the team started ripping both of them out — for something anyone could download off GitHub for free.

Manhattan launched in 2014 after Cassandra hit a wall at Twitter's scale. It shipped with two engines: SSTable, an in-house LSM engine built for writes, and MhBtree, a B-tree engine built for reads. Since most Manhattan traffic is read-heavy, MhBtree carried the majority of production clusters — Tweets, user profiles, direct messages.

Here's the detail that doesn't show up in the summaries: MhBtree wasn't a clean, purpose-built engine. It was implemented as a MySQL storage plugin, riding on MySQL's handler interface, wrapped in roughly 15,000 lines of C++. To change how Manhattan stored a byte on disk, an engineer needed to understand InnoDB internals, not just Manhattan. And because SSTable and MhBtree used different on-disk formats, migrating data between them meant replaying it as a stream of individual writes — which hit the receiving cluster like a sustained traffic spike.

Twitter didn't respond by building a third, better custom engine. They adopted RocksDB — the open-source LSM engine originally built at Facebook — as Manhattan's single storage engine for everything.

The migration ran three years, 2018 to 2021, moving trillions of keys and petabytes of data across clusters serving Tweets, profiles, and DMs. The result: same or better latency than the engines it replaced, lower CPU utilization, and roughly half the disk space per node. Twitter also deleted about a third of its storage-engine code and close to 10% of Manhattan's entire codebase.

The scaling problem at Twitter's size usually isn't "can an off-the-shelf system handle our load." It's "how many of our own engineers can safely touch the thing we built to handle it." Sometimes the fix for a homegrown system isn't a better homegrown system — it's admitting someone else's already has more people who understand it than yours does.

#SystemDesign #Databases #Twitter #Engineering

---

## Twitter / X Version

1/ Twitter's Manhattan database ran on two homegrown storage engines for years. In 2018, the team started tearing out both — for an open-source engine anyone could download for free.

2/ Manhattan replaced Cassandra in 2014. It shipped with SSTable (in-house LSM, for writes) and MhBtree (B-tree, for reads). Most production traffic — Tweets, profiles, DMs — ran on MhBtree.

3/ The part summaries skip: MhBtree was built as a MySQL storage plugin. ~15,000 lines of C++ wrapped around MySQL's handler interface. Touching it meant knowing InnoDB internals, not just Manhattan.

4/ Two engines, two on-disk formats. Migrating data between them meant replaying it as individual writes — which hit the receiving cluster like a sustained traffic spike.

5/ The fix wasn't a third custom engine. Twitter adopted RocksDB — Facebook's open-source engine — as Manhattan's one storage engine. Three-year migration: trillions of keys, petabytes of data.

6/ Result: same or better latency, lower CPU, ~50% less disk per node. Plus a third of the storage-engine code and ~10% of Manhattan's entire codebase — deleted. Sometimes the fix for homegrown isn't more homegrown.

---

## Excalidraw Diagram

**File:** 2026-07-04-twitter-manhattan-rocksdb-migration.excalidraw
**Type:** Horizontal migration timeline + results callout (structured case study)
**Color scheme:** Steel blue for the 2014-era homegrown engines (not "bad" — it was the right call for 2014), amber for the 2018 decision and migration, violet for the results callout. No red/green good/bad coding.
**Screenshottable stat:** "Same or better latency · ~50% less disk per node · 1/3 of the storage-engine code deleted"

### Layout

```
Title: "Twitter's Manhattan: Retiring the Homegrown Storage Engines"
Subtitle: "Two custom engines (one a 15k-line MySQL plugin) replaced by RocksDB · same/better latency · ~50% less disk · 3-year migration"

[2014 — Launch]                [The catch]                    [2018 — The call]              [2018-2021 — Migration]
Two in-house engines:          MhBtree is a MySQL storage      Instead of a third custom       Tweets, User profiles,
SSTable (LSM, write-           plugin -- ~15k lines of C++     engine, the team adopts          Direct Messages move
optimized) + MhBtree           wrapped around the MySQL        RocksDB, Facebook's open-        cluster by cluster.
(B-tree, read-optimized).      handler interface. Changing     source LSM engine, as            Trillions of keys.
Most production traffic        it means knowing InnoDB         Manhattan's one and only         Petabytes of data.
runs on MhBtree.               internals, not just Manhattan.  storage engine.                  Three years, start to finish.

Result: Same or better latency than the engines it replaced. Lower CPU utilization. ~50% less disk space per node.
Twitter deleted about a third of its storage-engine code and close to 10% of Manhattan's entire codebase.

Timeline: 2014 launches with two custom engines -> maintenance burden surfaces -> 2018 adopts RocksDB
          -> 2018-2021 three-year migration -> same/better latency at half the disk, with less code to maintain
```
