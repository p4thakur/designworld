<!-- sources -->
<!-- Primary: -->
<!--   LinkedIn Engineering blog, "Open Sourcing Venice: LinkedIn's Derived Data Platform" (Sept 2022) -->
<!--   https://engineering.linkedin.com/blog/2022/open-sourcing-venice--linkedin-s-derived-data-platform -->
<!--   LinkedIn Engineering blog, "Prototyping Venice: Derived Data Platform" -->
<!--   https://engineering.linkedin.com/distributed-systems/prototyping-venice-derived-data-platform -->
<!--   LinkedIn Engineering blog, "Venice Hybrid: Doing Lambda Better" (Dec 2017) -->
<!--   https://engineering.linkedin.com/blog/2017/12/venice-hybrid--doing-lambda-better -->
<!--   LinkedIn Engineering blog, "Venice Performance Optimization" (Apr 2018) -->
<!--   https://engineering.linkedin.com/blog/2018/04/venice-performance-optimization -->
<!--   LinkedIn Engineering blog, "Building Venice with Apache Helix" -->
<!--   https://engineering.linkedin.com/blog/2017/02/building-venice-with-apache-helix -->
<!--     — direct WebFetch of engineering.linkedin.com returned EGRESS_BLOCKED under this session's network -->
<!--     policy (same class of gateway-level denial noted on prior posts in this series). Facts below were -->
<!--     cross-checked across multiple independent web-search-result excerpts that directly quote LinkedIn's -->
<!--     own engineering blog posts, not written from memory. -->
<!-- Corroborating (independent secondary source, cross-referenced for consistency): -->
<!--   MarkTechPost, "LinkedIn Open-Sources 'Venice,' LinkedIn's Derived Data Platform that Powers more than -->
<!--   1800 Datasets" (Sept 2022) -->
<!--   https://www.marktechpost.com/2022/09/27/linkedin-open-sources-venice-linkedins-derived-data-platform-that-powers-more-than-1800-datasets/ -->
<!--   Database of Databases, "Venice" entry -->
<!--   https://dbdb.io/db/venice -->
<!-- Key verifiable details (cross-referenced across independent search excerpts that quote/summarize -->
<!-- LinkedIn's own engineering blog posts consistently): -->
<!-- 1. Venice is LinkedIn's "derived data" platform — serving data computed from another signal (relevance -->
<!--   scores, ML/recommendation output, event-stream aggregates), not source-of-truth data. -->
<!-- 2. Venice was built as a significant improvement over its predecessor, Voldemort Read-Only, a -->
<!--   batch-only key-value store: fine for daily snapshots, unable to serve anything fresher than the last -->
<!--   batch push. -->
<!-- 3. The classic Lambda-architecture alternative (a separate batch layer plus a separate speed/streaming -->
<!--   layer) forces the application to read from two databases, wait for whichever responds slower, stay up -->
<!--   only when both are up, and hand-roll the logic that reconciles the two answers. -->
<!-- 4. Venice instead funnels every write — whether it originates as a Hadoop batch job or a Samza streaming -->
<!--   job — through Apache Kafka first. Kafka's log is the single ingestion path for both; Venice's storage -->
<!--   nodes simply consume from Kafka and persist locally, with reconciliation handled as part of the -->
<!--   infrastructure rather than in each application. -->
<!-- 5. The "Venice Hybrid" design (per the Dec 2017 "Doing Lambda Better" post) layers continuous Kafka-based -->
<!--   updates on top of the batch push, so a dataset that would otherwise be "up to a day stale" can instead -->
<!--   be "fresh to the minute" — without any change on the application read path. -->
<!-- 6. As of the 2022 open-sourcing post, Venice ingests more than 25TB (un-replicated) daily and serves -->
<!--   over 100K QPS per data center, powering more than 1,800 datasets used by over 300 distinct applications -->
<!--   inside LinkedIn (numbers cross-confirmed independently by MarkTechPost's coverage of the same post). -->
<!-- 7. Venice has a pluggable storage-engine architecture: LinkedIn fully swapped the underlying engine from -->
<!--   BDB-JE to RocksDB without requiring any intervention from the applications built on top of Venice. -->
<!-- 8. Venice was open-sourced by LinkedIn in September 2022. -->
<!-- Publication: LinkedIn Engineering blog (engineering.linkedin.com), Venice series (2017-2022). -->

# LinkedIn Killed the Lambda Architecture by Deleting One of Its Two Databases

**Date:** 2026-08-25
**Company:** LinkedIn
**Category:** database
**Post type:** structured
**Opening style:** shared_pain_point
**Slug:** linkedin-venice-derived-data-lambda
**Character count (LinkedIn):** ~2490

---

## LinkedIn Post

Every team that runs a classic Lambda architecture hits the same wall. A batch layer computes the authoritative numbers overnight. A speed layer patches in whatever happened since. The application sits on top of both, waiting for whichever database answers slower, staying up only when both are up, and hand-rolling the logic that decides which system's answer wins.

LinkedIn hit that wall building "derived data" — data computed from something else, not the source of truth: relevance scores, recommendation output, aggregates rolled up from event streams. It started serving this out of Voldemort Read-Only, a batch-only key-value store. Good for daily snapshots, useless the moment a feature needed anything fresher than a day old.

The fix most teams reach for is bolting a streaming store next to the batch one and reconciling in application code. LinkedIn built the opposite: a single database, called Venice, with reconciliation done once, at write time, as part of the infrastructure — not re-implemented by every application that touches derived data.

The trick is the entry point. Every write to Venice — whether it originates as a Hadoop batch job or a Samza streaming job — gets funneled through Kafka first. Kafka's log becomes the one ingestion path for both worlds, so Venice's storage nodes just consume from Kafka and persist locally, with no idea whether the record in front of them came from a nightly job or a job running right now. Reconciliation isn't a runtime decision the app makes on every read. It's a property of the log.

That single design choice let LinkedIn add a hybrid mode later — batch push for the bulk of the data, continuous Kafka updates layered on top — so a dataset that used to be up to a day stale could be fresh to the minute, without touching the app layer that reads from it at all.

Venice now ingests more than 25TB a day and serves over 100K QPS per data center, across more than 1,800 datasets used by 300+ applications internally. Along the way, the team swapped Venice's entire storage engine from BDB-JE to RocksDB — with zero intervention required from any of those 300 applications, because the interface they depend on never changed.

Lambda architecture isn't wrong. It's just a tax collected at the wrong layer — paid by every application, on every read, forever. LinkedIn moved that tax into the log once, and every team downstream stopped paying it.

#SystemDesign #DistributedSystems #DataEngineering #Database

---

## Twitter / X Version

1/ LinkedIn's Lambda architecture had a database for batch and a database for streaming — and an application layer stuck waiting for whichever one answered slower.

2/ Their derived data (recommendations, relevance scores, rollups) started on Voldemort Read-Only: batch-only, up to a day stale by design.

3/ Instead of bolting a streaming store next to the batch one, LinkedIn built Venice — one database. Every write, batch or streaming, funnels through Kafka first. Reconciliation happens once, in the log — not on every app's every read.

4/ That let them add a hybrid mode later: batch push plus continuous Kafka updates, so datasets went from "stale up to a day" to "fresh to the minute" — with zero changes to the apps reading them.

5/ Today: 25TB+ ingested daily, 100K+ QPS per data center, 1,800+ datasets, 300+ applications. They even swapped the entire storage engine (BDB-JE → RocksDB) with no app-side changes required.

6/ Lambda architecture's real cost isn't the extra database. It's the tax every application pays, on every read, coordinating two sources of truth. LinkedIn moved that tax into the log — once.

---

## Excalidraw Diagram

**File:** 2026-08-25-linkedin-venice-derived-data-lambda.excalidraw
**Type:** Before/after comparison (two architecture snapshots side by side) converging into a single unified
flow band — matching the Structured Case Study type's recommended layout of showing the journey with
specific numbers at each stage.
**Color scheme:** Slate for neutral labels, indigo for the before-architecture (two databases, app-layer
coordination — not "bad," just more expensive), amber for the Kafka log as the convergence point, teal for
the after-architecture and the results band — a four-color set distinct from the red/indigo/amber/teal run
used two posts ago and the slate/gray/amber/teal/violet run used on the prior database-adjacent post.
**Screenshottable stat:** "Lambda architecture: 2 databases, app waits for the slower one. Venice: 1 database,
every write funneled through Kafka. Result: 25TB+/day, 100K+ QPS per DC, 1,800+ datasets, 300+ apps."

### Layout

```
Title: "LinkedIn Killed the Lambda Architecture by Deleting One of Its Two Databases"
Subtitle: "LinkedIn Engineering blog, Venice series (2017-2022) — how Venice replaced a batch store plus a
streaming store with one database and reconciliation at write time"
Stat callout (amber): "Lambda architecture: 2 databases, app waits for the slower one. Venice: 1 database,
every write funneled through Kafka. Result: 25TB+/day, 100K+ QPS per DC, 1,800+ datasets, 300+ apps."

[LEFT COLUMN — BEFORE, x 40-560]                     [RIGHT COLUMN — AFTER, x 640-1160]
"THE LAMBDA ARCHITECTURE TAX" [slate]                 "WHAT LINKEDIN BUILT: VENICE" [slate]
[indigo box]                                          [teal box]
"Batch layer (Voldemort Read-Only):                   "ONE database. Every write — Hadoop
up to a day stale. Speed layer patches                batch job or Samza streaming job —
in what's new. App reads BOTH, waits                  funnels through Kafka first. Storage
for the slower response, stays up only                nodes just consume the log.
when both are up, and hand-rolls which                Reconciliation is a property of the
answer wins." [indigo]                                log, not a per-read app decision." [teal]

        \\                                                  //
         \\                                                //
          v                                              v
[CONVERGENCE BAND, amber, full width]
"THE SINGLE ENTRY POINT — Kafka's log unifies both write paths. A hybrid mode layers continuous streaming
updates on top of the batch push: datasets go from stale-a-day to fresh-to-the-minute, with zero changes on
the application read path."
                              |
                              v
[RESULTS BAND, teal, full width]
"25TB+ ingested per day · 100K+ QPS per data center · 1,800+ datasets · 300+ applications. The storage
engine itself was swapped BDB-JE to RocksDB with zero app intervention — the interface those 300
applications depend on never changed."

[FOOTER, slate band, full width]
"Lambda architecture isn't wrong. It's a tax collected at the wrong layer — paid by every application, on
every read, forever. LinkedIn moved that tax into the log once, and every team downstream stopped paying it."
```
