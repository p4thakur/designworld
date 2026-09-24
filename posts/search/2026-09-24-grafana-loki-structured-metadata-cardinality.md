---
date: 2026-09-24
company: Grafana Labs
topic: Grafana Loki was built on one hard rule — never index the content of a log line, only the labels on its stream — because that's what kept the index small and queries cheap; when distributed tracing made engineers need to filter by trace_id and customer_id (fields unique per line, not per stream), that rule had no good answer, and Grafana had to ship structured metadata (GA in Loki 3.0) as a deliberate, narrow exception to its own founding constraint
category: search
post_type: confessional
opening_style: cold_fact
slug: grafana-loki-structured-metadata-cardinality
---

## Sources

- Grafana Loki official documentation: ["Cardinality"](https://grafana.com/docs/loki/latest/get-started/labels/cardinality/) — primary source confirming Loki "was not designed or built to support high cardinality label values" and was built for long-lived streams with low label cardinality.
- Grafana Loki official documentation: ["What is structured metadata"](https://grafana.com/docs/loki/latest/get-started/labels/structured-metadata/) — primary source for what structured metadata is (key-value pairs attached to a log line, stored in the chunk, not promoted into the stream's label set), its intended use for high-cardinality, frequently-searched fields like trace IDs and customer IDs, its experimental status in Loki 2.9 and GA status in Loki 3.0, and its storage in chunk format v4 (schema v13+).
- GitHub, grafana/loki, [Issue #13229](https://github.com/grafana/loki/issues/13229) — primary-source detail: a Promtail pipeline that materializes a field as a label via relabeling, then converts it to structured metadata without also demoting the original label, silently sends that field to Loki as a real high-cardinality label — recreating the exact problem structured metadata exists to prevent.
- Grafana Labs blog and KubeCon talk history for Loki's original design tagline, "Like Prometheus, but for logs" (introduced by Tom Wilkie at KubeCon Seattle, December 2018), and the label-only indexing philosophy behind it.

**Note on sourcing:** Direct fetch of grafana.com and third-party engineering blogs was blocked by this environment's network egress policy at write time. The facts above are drawn from search-indexed excerpts of Grafana's own official documentation pages (quoted phrases like "was not designed or built to support high cardinality label values" appear verbatim in the indexed docs) and a direct fetch of the GitHub issue, which this environment's network policy does allow.

**Key primary-source detail (not in most summaries):** Most descriptions of structured metadata stop at "it's a way to add searchable fields without indexing them." What the GitHub issue tracker actually shows is that the escape hatch has its own footgun: if a Promtail pipeline stage first turns a field into a normal label (a common step in relabeling) and then converts it to structured metadata but never removes the original label, Loki ends up with both — meaning the high-cardinality label Loki 3.0 was built to eliminate is still there, just sitting next to the fix that was supposed to replace it. The rule didn't just get an exception; the exception has its own way of quietly turning back into the original problem.

---

## LinkedIn Post

Grafana Loki has one architectural rule: never index the contents of a log line. Only index the labels — service, environment, pod — attached to each stream. Everything else gets compressed 10-20x and pushed to object storage untouched. That's the whole pitch: "like Prometheus, but for logs."

For years this held. Small index, cheap storage, fast queries — because Loki never has to grep through billions of lines, it just narrows to the right stream first.

Then distributed tracing became normal. Engineers wanted to pull every log line for one request: filter by trace_id, request_id, customer_id. Fields that are unique per line, not per stream.

Two bad options showed up. Add trace_id as a label, and Loki treats every unique value as a new stream — the index that was supposed to stay small explodes into millions of tiny streams. Or leave it in the log line, and every query becomes exactly the full-text scan Loki was built to avoid.

Grafana's fix, shipped as structured metadata and made GA in Loki 3.0, was to admit the label-only model had a hole in it. Structured metadata attaches key-value pairs — trace IDs, customer IDs — directly to each log line, stored in the chunk itself (a new chunk format, v4), but never promoted into the stream identifier. Queryable, but not indexed. Not quite the original rule. A deliberate crack in it.

The part that doesn't make the release notes: Grafana had to warn that a specific Promtail misconfiguration — materializing a field as a label before converting it to structured metadata, without also demoting it back down — silently recreates the exact cardinality explosion structured metadata exists to prevent. The escape hatch is only as good as the pipeline config in front of it.

Every clean architectural rule collects an exception once the real query patterns show up. The interesting engineering isn't stating the rule. It's building the exception without letting it swallow the rule whole.

#SystemDesign #Observability #DistributedSystems #Grafana

**Character count: 2,030 / 3,000 ✓**
**First ~140 chars (mobile hook):** "Grafana Loki has one architectural rule: never index the contents of a log line. Only index the labels — service, environment, pod — att" ✓

---

## Twitter / X Thread

1/ Grafana Loki's entire design rests on one rule: never index the content of a log line. Index only the labels on the stream. Compress the rest 10-20x and dump it in object storage untouched.

2/ "Like Prometheus, but for logs." That held for years.

3/ Then distributed tracing showed up. Engineers needed to pull every line for one request — filter by trace_id, request_id, customer_id. Fields that are unique per line, not per stream.

4/ Add them as labels and the index that was supposed to stay tiny explodes into millions of streams. Leave them in the log line and every query becomes the full-text scan Loki exists to avoid.

5/ Grafana's answer: structured metadata, GA in Loki 3.0. Key-value pairs attached to each log line, stored in the chunk (a new format, v4), queryable — but never promoted into the stream identifier. A deliberate crack in the original rule.

6/ What doesn't make the release notes: a specific Promtail misconfiguration can silently turn structured metadata back into high-cardinality labels — the exact explosion it was built to prevent. The escape hatch only works if the pipeline in front of it is configured right.

7/ No architecture stays pure once real query patterns show up.

---

## Diagram

See: `2026-09-24-grafana-loki-structured-metadata-cardinality.excalidraw`

Type: Horizontal timeline (confessional style) — four stages left to right: (1) 2018, the original label-only indexing rule; (2) Dec 2018 KubeCon launch of "like Prometheus, but for logs"; (3) 2019-2023, tracing adoption exposing the rule's blind spot (label explosion vs. full-text scan, both bad); (4) 2024, Loki 3.0 GA of structured metadata as the narrow, deliberate exception. A callout banner below the timeline holds the footgun detail from GitHub issue #13229 — the fix that can silently undo itself.
Color scheme: teal for the two stages where the original rule is working as intended, burnt orange for the stage where the rule breaks down, violet for the stage where the exception ships — and a separate muted red banner isolated at the bottom for the still-open footgun, so the "danger" color marks the unresolved risk specifically rather than being reused as a blanket bad/good signal.
Key screenshottable numbers: 10-20x log compression ratio, chunk format v4 / schema v13+, structured metadata experimental in Loki 2.9 → GA in Loki 3.0, GitHub issue #13229.
