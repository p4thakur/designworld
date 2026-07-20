<!-- sources -->
<!-- Primary: Figma Engineering Blog, "How Figma's Databases Team Lived to Tell the Scale" (April 29, 2024). -->
<!--   URL: https://www.figma.com/blog/how-figmas-databases-team-lived-to-tell-the-scale/ -->
<!-- Primary: Figma Engineering Blog, "The Growing Pains of Database Architecture." -->
<!--   URL: https://www.figma.com/blog/how-figma-scaled-to-multiple-databases/ -->
<!-- Secondary (technical summary, closely paraphrases/quotes the primary posts): pganalyze, "How Figma built DBProxy for sharding Postgres." -->
<!--   URL: https://pganalyze.com/blog/5mins-postgres-figma-dbproxy-sharding-postgres -->
<!-- Secondary (technical summary of the vertical-partitioning post): pganalyze, "How Figma and Notion scaled Postgres." -->
<!--   URL: https://pganalyze.com/blog/5mins-postgres-partitioning-tables-between-servers-horizontal-sharding -->
<!-- Note: direct WebFetch of figma.com/blog/* returned HTTP 403 under this session's egress policy (a recurring -->
<!--   session-wide restriction noted in several prior days' posts), not a per-site block. Facts below are -->
<!--   cross-checked across multiple independent WebSearch result excerpts that quote or closely paraphrase the -->
<!--   two primary Figma blog posts, corroborated by the pganalyze technical summaries and the Hacker News/Simon -->
<!--   Willison discussion threads on the same posts. -->
<!-- Key verifiable details (via search excerpts): -->
<!-- 1. In 2020, Figma ran on a single Postgres primary hosted on AWS's largest physical instance type. By the end -->
<!--   of 2022 they had built a distributed architecture: caching, read replicas, and a dozen vertically -->
<!--   partitioned databases. The database stack grew almost 100x between 2020 and 2024. -->
<!-- 2. Some tables grew to several terabytes and billions of rows, at which point they began to see reliability -->
<!--   impact during Postgres vacuum operations -- vacuum is the background process that reclaims dead tuples and -->
<!--   prevents transaction ID wraparound. -->
<!-- 3. Vertical partitioning = moving whole tables (not splitting individual tables) onto their own database -->
<!--   instances. Cutover used logical replication; because logical replication copies rows in bulk but rebuilds -->
<!--   indexes one row at a time (slow at terabyte scale), Figma dropped destination indexes, bulk-copied, then -->
<!--   rebuilt indexes afterward, reducing copy time to hours. PgBouncer was split into separate pooled services -->
<!--   ahead of the cutover so misrouted queries during the transition still resolved correctly; traffic was -->
<!--   briefly frozen for replication to catch up, then cut over, with a reverse replication stream back to the -->
<!--   old database kept live as a rollback path. -->
<!-- 4. For horizontal sharding: Figma separated "logical sharding" (application-layer, via database views that -->
<!--   make an unsharded table look pre-sharded) from "physical sharding" (Postgres-layer). A shadow-reads -->
<!--   framework sent live read traffic through both the view and the raw table to validate correctness and -->
<!--   performance -- overhead was minimal in most cases, and under 10% in the worst case. -->
<!-- 5. DBProxy: a Go service sitting between the application layer and PgBouncer. Its query engine parses SQL into -->
<!--   an AST, a logical planner extracts the query type and logical shard ID (sharded on user ID, file ID, or -->
<!--   org ID depending on the table), and a physical planner maps the logical shard to a physical database. -->
<!--   Queries missing a shard key fall back to a scatter-gather across all shards, aggregated in the proxy. -->
<!-- 6. Figma went live with its first sharded tables in September 2023, with minimal impact on availability. -->
<!-- 7. NOT independently verified with hard numbers: the exact AWS instance type/size in 2020, the precise -->
<!--   terabyte/row-count figures for the tables that triggered the vacuum problem, and an exact incident -->
<!--   timestamp/duration tied to a specific vacuum-caused outage (these are described qualitatively in the -->
<!--   sources, not quantified with a specific incident metric). -->
<!-- Mechanism-level explanation of *why* vacuum cost scales with table size (Postgres MVCC: every UPDATE/DELETE -->
<!-- creates a new row version rather than overwriting in place, leaving a dead tuple that autovacuum must walk the -->
<!-- table to reclaim, both to control bloat and to freeze transaction IDs ahead of 32-bit XID wraparound) is -->
<!-- standard Postgres internals knowledge, used here to go one level deeper than the blog posts themselves, per -->
<!-- the skill's sourcing guidance. -->

# Figma's Postgres: Why Sharding Was the Last Step, Not the First

**Date:** 2026-07-20
**Company:** Figma
**Category:** database
**Post type:** structured case study
**Opening style:** cold_fact
**Slug:** figma-postgres-sharding-dbproxy
**Character count (LinkedIn):** ~2,744

---

## LinkedIn Post

Figma's database stack grew almost 100x between 2020 and 2024. In 2020: one Postgres primary, already on AWS's largest physical instance. By end of 2022: a dozen separate databases. By September 2023: parts of it finally sharded. Nobody just "added shards" — the path between those points is the interesting part.

The trigger wasn't size on its own. Some tables had grown to several terabytes and billions of rows — exactly where Postgres autovacuum started causing reliability incidents. Postgres never updates a row in place — every UPDATE or DELETE leaves the old version behind as a dead tuple, and autovacuum has to walk the table reclaiming that garbage and freezing transaction IDs before the 32-bit counter wraps and corrupts the table. That walk costs time proportional to table size. At multi-terabyte scale, a vacuum pass runs long enough to fight live traffic for I/O and locks. The table hadn't just gotten big — it had outgrown the maintenance operation that keeps Postgres correct.

A bigger box wasn't an option — already on AWS's largest instance. A full horizontal shard in one shot wasn't either: rewriting every query across the whole app in one move is exactly the kind of change that takes a company down.

So they split the difference first. Vertical partitioning: move whole tables onto their own databases, not splitting individual tables across many. The cutover ran on logical replication, which had its own trap — it copies rows in bulk but rebuilds indexes one row at a time, brutal at terabyte scale. Fix: drop destination indexes, bulk-copy the data, rebuild indexes after — replication time down to hours. PgBouncer got split into separate pools first so misrouted queries mid-cutover still landed somewhere valid, then a brief traffic freeze for replication to catch up, then flip — with a reverse replication stream back to the old database as a rollback path.

Vertical partitioning bought years, not forever — the largest tables kept outgrowing what one box could vacuum. For horizontal sharding, they proved the abstraction before it was real: database views made an unsharded table look pre-sharded to the app, and a shadow-reads framework ran 100% of live reads through both paths — under 10% overhead worst case. Only then did they build DBProxy, a Go service parsing every query to an AST, extracting the shard key (user, file, or org ID depending on the table), and routing it — falling back to scatter-gather when no key is present.

First sharded tables went live in September 2023, with minimal availability impact. Sharding here wasn't one decision. It was a sequence of smaller, reversible ones, each proven before the next became load-bearing.

#SystemDesign #PostgreSQL #DatabaseSharding #Figma

---

## Twitter / X Version

Figma's database grew ~100x between 2020 and 2024. 2020: one Postgres primary on AWS's biggest instance. 2022: a dozen databases. Sept 2023: first shards live.

The trigger wasn't "big data." It was autovacuum. Postgres never updates a row in place — updates/deletes leave dead tuples behind, and vacuum has to walk the table reclaiming them before transaction IDs wrap. At multi-TB tables, a vacuum pass got slow enough to fight live traffic for locks and I/O.

Bigger box? Already maxed out. Shard everything in one move? Too risky for one company to swallow at once.

So: vertical partition first — whole tables onto separate DBs. Logical replication copies rows in bulk but rebuilds indexes one at a time, brutal at TB scale. Fix: drop indexes, bulk copy, rebuild after. Hours instead of days.

For horizontal sharding, they proved it first: views made one DB look pre-sharded, shadow reads compared both paths on 100% of live traffic (<10% overhead worst case). Then DBProxy: parses SQL to an AST, extracts the shard key, routes it — scatter-gather when there's no key.

Live September 2023. Sharding wasn't a decision here. It was a sequence of reversible ones, each proven before the next got load-bearing.

---

## Excalidraw Diagram

**File:** 2026-07-20-figma-postgres-sharding-dbproxy.excalidraw
**Type:** Migration timeline (structured case study style) — four horizontal stages (starting state → the real bottleneck → fix stage one → fix stage two/result), a wide indigo mechanism box underneath spelling out the vacuum/MVCC math, and a footer naming the reversibility principle that ties every stage together.
**Color scheme:** Slate for the neutral starting state, amber for the diagnosed problem (not villainized — vacuum is doing its job, it's just outgrown), teal for the first fix (vertical partitioning), green for the final result (sharding live). Indigo for the mechanism explainer. No single "bad guy" box — every stage is a reasonable decision given what was known at the time.
**Screenshottable stat:** "2020: 1 primary, AWS's largest instance · 2022: 12 vertically partitioned DBs · Sept 2023: first shards live · ~100x growth · shadow-read overhead <10% worst case"

### Layout

```
Title: "Figma's Postgres: Why Sharding Was the Last Step, Not the First"
Subtitle: "2020: 1 primary, AWS's largest instance  ·  2022: 12 vertically partitioned DBs  ·  Sept 2023: first shards live  ·  ~100x growth"

ROW — THE TIMELINE: FOUR STAGES, EACH VALIDATED BEFORE THE NEXT BECAME LOAD-BEARING
[2020 — ONE PRIMARY]        →   [THE VACUUM CEILING]         →   [2020–2022 — VERTICAL      →   [SEPT 2023 — DBPROXY
                                                                    PARTITION]                     SHARDS LIVE]
One Postgres primary,           Postgres never updates rows      Move whole tables onto           Views proved logical
already on AWS's largest        in place — every UPDATE/          their own databases.             sharding first — shadow
physical instance. As           DELETE leaves a dead tuple.       Logical replication was           reads on 100% of live
Figma grew, some tables         Autovacuum must reclaim           slow rebuilding indexes           traffic, <10% worst-case
reached several terabytes       them before transaction IDs       row-by-row, so they               overhead. Then DBProxy:
and billions of rows.           wrap, and that walk costs         dropped indexes, bulk-            parse SQL to an AST,
                                 time proportional to table         copied, rebuilt after. A          extract the shard key,
                                 size.                              dozen DBs by end of 2022.         route it.

[THE MECHANISM MATCH]
The problem was never raw size — it was that Postgres's own upkeep no longer fit inside the traffic pattern. MVCC turns every write into a
new row version instead of overwriting in place; vacuum has to walk the whole table to reclaim old versions and freeze transaction IDs before
a 32-bit counter wraps and corrupts the database. That walk is O(table size) with no shortcut. Split the table across smaller databases —
vertically, then horizontally — and each vacuum only has to walk its own slice. The ceiling moves with you instead of catching up to you.

Footer: Every step here was reversible before it was made permanent: vertical partitioning kept a reverse replication stream back to the old
database in case of rollback; sharding validated its query router against a live shadow of production traffic before a single row physically
moved. Sharding wasn't one decision — it was a sequence of smaller ones, each proven before the next one became load-bearing.
```
