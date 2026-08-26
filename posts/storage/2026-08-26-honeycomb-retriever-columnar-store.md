<!-- sources -->
<!-- Primary: -->
<!--   Honeycomb blog, "Why We Built Our Own Distributed Column Store" (Sam Stokes) -->
<!--   https://www.honeycomb.io/resources/why-we-built-our-own-distributed-column-store -->
<!--   Honeycomb blog, "Why Observability Requires a Distributed Column Store" -->
<!--   https://www.honeycomb.io/blog/why-observability-requires-distributed-column-store -->
<!--   Honeycomb blog, "Virtualizing Our Storage Engine" -->
<!--   https://www.honeycomb.io/blog/virtualizing-storage-engine -->
<!--   Honeycomb blog, "From 'Secondary Storage' To Just 'Storage': A Tale of Lambdas, LZ4, and Garbage -->
<!--   Collection" -->
<!--   https://www.honeycomb.io/blog/secondary-storage-to-just-storage -->
<!--   Honeycomb blog, "Announcing Secondary Storage and the Fast Query Window" -->
<!--   https://www.honeycomb.io/blog/announcing-secondary-storage-and-the-fast-query-window -->
<!--   Honeycomb blog, "Solving a Murder Mystery: The Columnar Datastore Bug" -->
<!--   https://www.honeycomb.io/blog/solving-murder-mystery-columnar-datastore -->
<!--   Strange Loop 2017 talk, "Why We Built Our Own Distributed Column Store" -->
<!--   https://www.thestrangeloop.com/2017/why-we-built-our-own-distributed-column-store.html -->
<!--     — direct WebFetch of www.honeycomb.io returned EGRESS_BLOCKED under this session's network policy -->
<!--     (same class of gateway-level denial noted on prior posts in this series). Facts below were -->
<!--     cross-checked across multiple independent web-search-result excerpts that directly quote or closely -->
<!--     paraphrase Honeycomb's own engineering blog posts, not written from memory. -->
<!-- Corroborating (independent secondary sources, cross-referenced for consistency): -->
<!--   Paul Osman, "Solving a Murder Mystery" (personal blog, first-hand account by the engineer who led the -->
<!--   investigation) -->
<!--   https://paulosman.me/2022/11/29/solving-a-murder-mystery/ -->
<!--   InfoQ, "Jessica Kerr on Observability and Honeycomb's Use of AWS Lambda for Retriever" -->
<!--   https://www.infoq.com/podcasts/aws-lambda-custom-database-retriever/ -->
<!-- Key verifiable details (cross-referenced across independent search excerpts that quote/summarize -->
<!-- Honeycomb's own engineering blog posts consistently): -->
<!-- 1. Retriever is Honeycomb's custom-built, distributed, schemaless datastore that stores and queries every -->
<!--   customer event the product observes — modeled on Facebook's internal "Scuba" system/paper. -->
<!-- 2. Honeycomb needed properties (multi-tenancy, cost-to-serve, arbitrary high-cardinality slicing of raw -->
<!--   events on demand) that off-the-shelf databases of the time were not shaped for — general-purpose or -->
<!--   metrics-oriented stores assume pre-aggregation, not per-field ad hoc queries over raw events. -->
<!-- 3. Unlike Scuba, which lives in memory, Retriever stores events on disk, using a column-oriented layout: -->
<!--   when a node consumes an event off a Kafka partition, it writes the event's fields to separate files per -->
<!--   column (one file per attribute), not one row-oriented record. -->
<!-- 4. Two redundant Retriever nodes independently consume the same Kafka partition and persist to their own -->
<!--   fast local NVMe disks — there is no shared/network storage (no EBS, no S3) in the hot ingest/query path; -->
<!--   durability comes from the redundancy between the two nodes, not from the storage layer itself. -->
<!-- 5. Years later, keeping all customer data on primary NVMe indefinitely became a cost problem. Honeycomb -->
<!--   introduced "Secondary Storage": colder data is compressed and shipped to S3, letting customers retain -->
<!--   more history for less money, at the cost of query-time performance — rehydrated on demand via AWS -->
<!--   Lambda. -->
<!-- 6. A follow-up post ("From 'Secondary Storage' To Just 'Storage'") describes finding that the *network* -->
<!--   wasn't the bottleneck for Lambda-based reads against S3 — gzip decompression and per-query garbage- -->
<!--   collection overhead (allocation/cleanup cost proportional to query size) were. The fix: switch -->
<!--   compression from gzip to LZ4 with a compression-friendly file layout (~3x faster file reads), and adopt -->
<!--   a more C-like manual memory-management model — finding the exact point a heap-allocated structure -->
<!--   expires and reusing it, rather than leaving it to the garbage collector. -->
<!-- 7. In May 2022, an engineer (Paul Osman) led an investigation into a bug latent in the columnar datastore -->
<!--   for more than two years, causing minor data loss and crashed queries — documented in "Solving a Murder -->
<!--   Mystery." -->
<!-- Publication: Honeycomb engineering blog (honeycomb.io/blog, honeycomb.io/resources), Retriever/storage -->
<!-- engine series (2017-2023), corroborated by a first-hand Honeycomb engineer's personal blog post. -->

# Everyone Says Never Build Your Own Database. Honeycomb's Product Runs on One.

**Date:** 2026-08-26
**Company:** Honeycomb
**Category:** storage
**Post type:** contrarian
**Opening style:** challenge_assumption
**Slug:** honeycomb-retriever-columnar-store
**Character count (LinkedIn):** ~2505

---

## LinkedIn Post

Everyone tells startups never to build their own database. Honeycomb built one anyway — and it's not a side project. It's the thing that stores and queries every event the product exists to observe.

The obvious path in 2016 was to bolt the UI onto something that already existed — Cassandra, InfluxDB, any off-the-shelf time-series store. All of them assume a query shape observability doesn't have: pre-aggregated metrics, not raw high-cardinality events sliced by any arbitrary field on demand. Retrofitting that meant paying for flexibility Honeycomb didn't need, and not getting the flexibility it did.

So they built Retriever, modeled on Facebook's internal Scuba — but changed the constraint that mattered most for a startup's bank account. Scuba lived in memory. Retriever lives on disk. Each event gets consumed off a Kafka partition and written to separate files per column, one file per attribute, not one file per row — so a query touching five fields never reads the other ninety-five.

Then came the second rejection. The standard cloud pattern is to decouple compute from storage — shared network storage, EBS or S3, for durability. Honeycomb didn't. Two redundant Retriever nodes each persist an independent copy straight from Kafka onto their own local NVMe disks. No shared storage in the hot path. Durability comes from redundancy, not the storage layer.

That decision didn't age the way anyone would guess. It wasn't the query engine that needed rework later — it was the disks. Local NVMe is fast and expensive; keeping years of every customer's raw events on it forever doesn't scale into a business. So Honeycomb built a second, slower tier: compress cold data, ship it to S3, rehydrate it through Lambda when a query actually needs it.

Even that got rejected once it shipped. "Just use S3" turned out to be slow for reasons that had nothing to do with the network — gzip decompression and garbage collection were eating the CPU time, proportional to the size of every query. So they swapped gzip for LZ4 with a compression-friendly file layout, about 3x faster reads, and rewrote the hot path to manually track when heap-allocated structures expired instead of letting the garbage collector guess.

The contrarian move was never "local disks beat S3" or "custom beats Cassandra." It's that Honeycomb kept re-earning both decisions every time the constraint changed, instead of treating either one as settled for good.

#SystemDesign #DistributedSystems #Databases #Observability

---

## Twitter / X Version

1/ "Never build your own database" is close to gospel in engineering circles. Honeycomb built one anyway — it's not a side project, it's the thing every customer event runs through.

2/ 2016's obvious move: bolt the UI onto Cassandra or InfluxDB. Wrong shape — those assume pre-aggregated metrics, not raw events sliced by any field, on demand.

3/ So they built Retriever, modeled on Facebook's Scuba — but put it on disk instead of memory. One file per column, not per row. A 5-field query never touches the other 95.

4/ Then they rejected cloud-native storage too. No S3, no EBS in the hot path — two redundant nodes, each writing straight from Kafka onto their own local NVMe disks. Durability = redundancy, not shared storage.

5/ Years later, the disks got expensive, not the query engine. Fix: compress cold data, ship it to S3, rehydrate via Lambda when a query needs it.

6/ Even that got rejected once it felt slow. Gzip decompression and garbage collection were the real tax, not the network — so they swapped gzip for LZ4 (~3x faster reads) and hand-managed memory instead.

7/ The lesson isn't "local disks beat S3." It's that Honeycomb never treated a storage decision as settled for good — they kept re-earning it as the constraints changed.

---

## Excalidraw Diagram

**File:** 2026-08-26-honeycomb-retriever-columnar-store.excalidraw
**Type:** Side-by-side architecture comparison across two stacked decisions (database choice, then storage
layer choice), with a footer band showing the reversal/evolution — matching the Contrarian post type's
recommended layout of showing the "obvious" approach vs. what they actually built.
**Color scheme:** Amber for the "obvious path" boxes (not "wrong," just the default), indigo for what
Honeycomb actually built, teal for the cost/reversal band, violet for the closing judgment — a four-color
set distinct from the indigo/amber/teal run used on the prior database post and the slate/red/indigo/amber/
teal run used on the prior messaging post.
**Screenshottable stat:** "Retriever: 1 file per COLUMN, not per row. 2 redundant nodes, local NVMe only, no
S3/EBS in the hot path. Years later: gzip → LZ4 cut file reads ~3x — the network was never the bottleneck."

### Layout

```
Title: "Everyone Says Never Build Your Own Database. Honeycomb's Product Runs on One."

Section label: "DECISION 1 — THE DATABASE"

[LEFT — OBVIOUS PATH, x 40-560, amber]                [RIGHT — WHAT HONEYCOMB BUILT, x 640-1160, indigo]
"Bolt the UI onto an existing                          "Retriever — modeled on Facebook's
time-series store (Cassandra,                          Scuba. Events on DISK, not memory.
InfluxDB). Built for pre-aggregated                    One file per COLUMN, not per row —
metrics — wrong shape for slicing                      a query touching 5 fields never
raw, high-cardinality events by                        reads the other 95."
any field, on demand."

Section label: "DECISION 2 — THE STORAGE LAYER"

[LEFT — OBVIOUS PATH, amber]                           [RIGHT — WHAT HONEYCOMB BUILT, indigo]
"Decouple compute from storage —                       "Local NVMe disks only. Two
shared network storage (EBS/S3),                       redundant Retriever nodes each
the standard cloud-native pattern                      persist an independent copy
for durability."                                       straight off Kafka. Durability =
                                                        redundancy, not the storage layer."

[REVERSAL BAND, teal, full width]
"THE REVERSAL THAT PROVES THE POINT: years later, keeping every customer's raw events on NVMe forever got
expensive — so Honeycomb added 'Secondary Storage': compress cold data, ship it to S3, rehydrate through
Lambda on query. But once that felt slow, they didn't just accept whatever speed S3 gave them — gzip →
LZ4 cut file reads ~3x, and the read path was rewritten to manually reclaim memory instead of leaning on
garbage collection, because GC and decompression — not the network — turned out to be the real tax."

[FOOTER, violet band, full width]
"The contrarian move was never 'local disks beat S3' or 'custom beats Cassandra.' It's that Honeycomb kept
re-earning both decisions every time the constraint changed, instead of treating either one as settled for
good."
```
