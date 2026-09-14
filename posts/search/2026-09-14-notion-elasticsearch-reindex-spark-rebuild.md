---
date: 2026-09-14
company: Notion
topic: Notion's quarterly Elasticsearch reindex took over two weeks on a custom ECS pipeline riddled with OOMs and coordination failures, plus a separate catchup pipeline that silently dropped edits it couldn't reconcile — replacing the custom coordination layer with a Spark-native pipeline and Elasticsearch's own snapshot format cut full reindex time to under two days
category: search
post_type: structured
opening_style: shared_pain_point
slug: notion-elasticsearch-reindex-spark-rebuild
---

## Sources

- Notion Engineering Blog: ["Rebuilding Notion's lexical search reindexer"](https://www.notion.com/blog/rebuilding-notions-lexical-search-reindexer), published August 10, 2026 — the primary source for the pipeline architecture, timings, and the dropped-block detail below.
- ZenML LLMOps Database: ["Notion: Rebuilding a Production Search Reindexing Pipeline at Scale"](https://www.zenml.io/llmops-database/rebuilding-a-production-search-reindexing-pipeline-at-scale) — independent summary corroborating the ECS OOM/coordination failures, the Spark+Airflow replacement, and the S3 snapshot mechanism.
- Notion Engineering Blog: ["Two years of vector search at Notion: 10x scale, 1/10th cost"](https://www.notion.com/blog/two-years-of-vector-search-at-notion) — companion post on Notion's separate vector-search infrastructure, referenced for context on Notion's broader search stack.

**Note on sourcing:** Direct fetch of notion.com and zenml.io was blocked by this environment's network egress policy at write time. The facts and quotes below are drawn from search-indexed excerpts of Notion's own blog post, cross-checked against the independent ZenML summary of the same post, which agree on the same architecture, numbers, and root-cause details.

**Key primary-source detail (not in most summaries):** The old ECS-based pipeline didn't just run slowly — it lost data silently. Edits that didn't cleanly match during the post-build catchup reconciliation were dropped as "unmatched" blocks, with no alert and no record, until someone noticed content missing from search results later. Most retellings of "we migrated our reindexing to Spark" stop at the speed numbers. The actual failure mode being fixed was a silent correctness bug, not just a slow job.

---

## LinkedIn Post

Every Elasticsearch team eventually hits the same wall: a full reindex stops being routine maintenance and starts being an event people schedule around. At Notion, that event happened once a quarter, and it took more than two weeks.

The old pipeline ran on a custom system built on ECS. Building a fresh index from scratch ate most of those two weeks, with engineers babysitting the job through OOM crashes and worker-coordination failures. Then came a second problem: everything users edited during those two weeks of building still had to be caught up separately. A dedicated ECS "catchup" pipeline replayed the backlog of Kafka changes after the fact — with the same OOM and coordination issues, adding two more days before the index was actually current. Worse, some edits never made it at all: the old pipeline silently dropped "unmatched" blocks it couldn't reconcile, and nobody found out until later.

The root cause wasn't Elasticsearch. It was that Notion had built its own distributed-coordination layer on top of ECS to redo something two mature systems already solved. Apache Spark already manages memory and worker coordination across a cluster. Elasticsearch already has a native snapshot format meant to be restored, not rebuilt document-by-document.

So the fix wasn't a bigger ECS cluster. It was giving up the custom coordination code entirely. Notion rebuilt the pipeline as a Spark-native job orchestrated by Airflow. Reindexing now produces a self-contained snapshot in S3 that Elasticsearch restores directly, in hours instead of weeks. Because a snapshot is just files, atomic deploys and rollback are close to free — point back at the old snapshot in one step if something's wrong. The separate catchup pipeline is gone too: Elasticsearch's own primitives now absorb changes continuously instead of reconciling a multi-day backlog after the fact.

The results: full reindex time down from 2+ weeks to under 2 days. Catchup time down from 2 days to under 1 hour. Manual engineering effort per reindex down from weeks to under 2 hours, with zero on-call pages. And a side effect nobody was optimizing for: adding a new searchable field used to be a monthlong project. Now it's a Scala transformation, a validation job, and the next nightly run — done in days, not a quarter.

The lesson isn't "use Spark." It's that a lot of infrastructure pain isn't the underlying system fighting you. It's custom glue code re-solving problems the system underneath already solved, worse.

#SystemDesign #SearchEngineering #Elasticsearch #DistributedSystems

**Character count: ~2,566 / 3,000 ✓**
**First 140 chars (mobile hook):** "Every Elasticsearch team eventually hits the same wall: a full reindex stops being routine maintenance and starts being an event people sche" ✓

---

## Twitter / X Thread

1/ Notion used to rebuild its search index once a quarter. The rebuild alone took more than two weeks.

2/ The old pipeline ran on custom ECS code: OOMs, worker-coordination failures, constant babysitting. A separate "catchup" pipeline then had to replay two more days of edits made during the build — with the same OOM problems.

3/ Some edits didn't even survive: the old pipeline silently dropped blocks it couldn't reconcile. Nobody found out until later.

4/ The fix wasn't more ECS capacity. It was realizing Spark already solves distributed coordination, and Elasticsearch already has a snapshot format meant to be restored, not rebuilt document-by-document.

5/ New pipeline: Spark-native job on Airflow → self-contained snapshot in S3 → Elasticsearch restores it directly. Full reindex: 2+ weeks → under 2 days. Catchup: 2 days → under 1 hour.

6/ Manual engineering time per reindex: weeks → under 2 hours, zero on-call pages. Bonus: adding a new searchable field went from a monthlong project to a Scala transform + validation job picked up by the next nightly run.

7/ Most infra pain isn't the underlying system fighting you. It's custom glue code re-solving what the system underneath already solved.

---

## Diagram

See: `2026-09-14-notion-elasticsearch-reindex-spark-rebuild.excalidraw`

Type: Before/after comparison (structured case study style) — two stacked panels showing the old ECS pipeline vs. the new Spark+Airflow+snapshot pipeline, with a callout band for the silent-data-loss detail and a footer with the four headline numbers.
Color scheme: slate/gray for "before" (not bad — just built before Spark's coordination model was the obvious default), teal for "after," amber for the callout (a caught bug, not a failure). No red/green good-bad pairing.
Key screenshottable number: full reindex time dropped from 2+ weeks to under 2 days, and catchup from 2 days to under 1 hour.
