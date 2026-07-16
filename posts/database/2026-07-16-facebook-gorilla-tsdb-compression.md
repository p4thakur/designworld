<!-- sources -->
<!-- Primary: Pelkonen et al., "Gorilla: A Fast, Scalable, In-Memory Time Series Database" (Facebook, VLDB 2015) -->
<!--   URL: https://www.vldb.org/pvldb/vol8/p1816-teller.pdf -->
<!--   Note: direct fetch of the VLDB PDF and of blog.acolyer.org / charap.co / joe.schafer.dev returned HTTP 403 -->
<!--   under this session's egress policy. Facts below were cross-checked across multiple independent search-result -->
<!--   excerpts that quote the primary paper directly, plus Facebook's own follow-up engineering post on Beringei: -->
<!--   https://engineering.fb.com/2017/02/03/core-infra/beringei-a-high-performance-time-series-storage-engine/ -->
<!--   https://dl.acm.org/doi/10.14778/2824032.2824078 (VLDB proceedings entry, abstract + citation) -->
<!--   https://github.com/facebookarchive/beringei (open-source release, archived 2018) -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Gorilla retains the most recent 26 hours of every time series fully in memory, as a write-through cache -->
<!--    sitting in front of HBase, which held the durable long-term history. -->
<!-- 2. Raw data point = 16 bytes (8-byte timestamp + 8-byte double value). Gorilla's compression brings the -->
<!--    average down to 1.37 bytes/point -- roughly a 12x reduction. -->
<!-- 3. Timestamp compression is delta-of-delta encoding: compute D = second-order delta of consecutive timestamps; -->
<!--    D=0 -> single '0' bit; D in [-63,64] -> '10' + 7 bits; D in [-255,256] -> '110' + 9 bits; -->
<!--    D in [-2047,2048] -> '1110' + 12 bits; else -> '1111' + 32-bit value. -->
<!-- 4. Value compression is XOR-based: XOR the current double against the previous one. XOR=0 -> single '0' bit; -->
<!--    otherwise '1' + either reuse of the prior leading/trailing-zero window (control bit 0) or a fresh window -->
<!--    encoded as 5 bits leading-zero-count + 6 bits meaningful-block-length + the meaningful bits (control bit 1). -->
<!-- 5. Compared to querying the HBase-backed system, Gorilla achieved ~73x lower query latency and ~14x higher -->
<!--    query throughput. ODS (Facebook's monitoring query service) served ~450 queries/sec before Gorilla; -->
<!--    Gorilla scaled to 5,000+ steady-state queries/sec, with peaks reported around 40,000 queries/sec. -->
<!-- 6. Failure/durability tradeoff: Gorilla is memory-only and replays a write-ahead log after a crash, but during -->
<!--    a prolonged, cluster-wide outage where WAL replay can't keep pace, it does not block ingestion to catch up -->
<!--    -- it keeps only the most recent ~1 minute of data and drops the rest, favoring availability/freshness over -->
<!--    completeness. -->
<!-- 7. Facebook open-sourced the design as Beringei in 2017 (facebookarchive/beringei); the standalone repo was -->
<!--    archived in 2018, with its ideas absorbed back into Facebook's broader ODS/Scuba monitoring stack. -->

# Facebook Compressed Monitoring Data to 1.37 Bytes a Point — and Cut Query Latency 73x

**Date:** 2026-07-16
**Company:** Facebook
**Category:** databases
**Post type:** structured
**Opening style:** cold_fact
**Slug:** facebook-gorilla-tsdb-compression
**Character count (LinkedIn):** ~2,540

---

## LinkedIn Post

By 2015, Facebook's monitoring system was collecting hundreds of billions of time series points a day — CPU load, error rates, cache hit ratios, one line per metric per host, forever. All of it lived in HBase. And the query that mattered most — an on-call engineer, mid-incident, pulling up the last hour across a few thousand related series — was also the slowest one the system served.

The instinct is to throw more HBase at it: more read replicas, bigger regions, a fatter block cache. That doesn't fix this, because the query during an incident isn't "read one row." It's a wide scan across the freshest, least-settled data for thousands of series at once, at the exact moment everyone else runs the same query. That's a fan-out of reads against the part of an LSM-tree-backed store that's least compacted: recent writes still sitting across memtables and fresh SSTables. Scaling the cluster scales the wrong axis — the problem was never total volume, it was serving the newest slice under concurrent load.

So Facebook built Gorilla: a pure in-memory time series store, sharded per host, holding only the most recent 26 hours, as a write-through cache in front of HBase. The hard part wasn't the architecture — it was making 26 hours of every metric on the fleet fit in RAM at all.

Two compressions, both exploiting one fact: consecutive points in a metric barely change. Timestamps arrive on a fixed interval, so instead of storing each one, Gorilla stores the delta of the delta — for a steady 60-second cadence, that's 0, over and over, encoded as a single bit. When it drifts, a variable-width prefix (10 + 7 bits, 110 + 9 bits, and up) picks the smallest bucket that fits. Values get XOR'd against the previous reading: for a gauge like CPU% that moves slowly, the mantissa and exponent barely shift, so the XOR result is almost all zero bits, clustered at the front and back. Gorilla stores only the meaningful middle bits, plus one control bit saying whether to reuse the previous point's leading/trailing-zero window.

Raw, a point is 16 bytes. Compressed, it averages 1.37 — about a 12x reduction. Not a clever architecture. An entire day of monitoring data, fleet-wide, made small enough for memory.

Queries against Gorilla ran roughly 73x lower latency and 14x higher throughput than the same query against HBase. ODS launched serving about 450 queries/second; Gorilla grew to over 5,000 steady-state, with peaks past 40,000.

Being memory-only has a cost. On a single host crash, Gorilla replays a write-ahead log. But during a prolonged, cluster-wide outage where replay can't keep pace, it doesn't block ingestion to catch up — it keeps the most recent minute of data and drops the rest. Facebook decided a monitoring system that goes slow during an outage is worse than one that loses some history and stays fast, because the one moment you can't afford a lagging dashboard is the one you built it for.

Facebook open-sourced the design as Beringei in 2017; the standalone project was archived a year later, its ideas folded back into the broader ODS/Scuba stack. The mechanism outlived the repo, because the shape of the problem — a fixed-interval, slowly-drifting signal, read as a recent range — is the shape of nearly every metric anyone monitors.

#SystemDesign #TimeSeriesDatabase #Facebook #Monitoring #DistributedSystems

---

## Twitter / X Version

1/ By 2015, Facebook's monitoring store held hundreds of billions of time series points a day in HBase. The slowest query it served was also the one an on-call engineer ran mid-incident: the last hour, across thousands of series, right now.

2/ More HBase doesn't fix that. That query is a wide scan over the freshest, least-compacted data — memtables and fresh SSTables — at the exact moment everyone else hits the same shard. Scaling the cluster scales the wrong axis.

3/ So they built Gorilla: in-memory only, 26 hours retained, a write-through cache in front of HBase. The hard part wasn't the architecture — it was fitting 26 hours of every metric on the fleet into RAM.

4/ Timestamps: store the delta of the delta. On a steady 60s interval, that's 0, encoded in a single bit. Values: XOR against the previous reading — for a slow-moving gauge, the result is almost all zero bits, so only the meaningful middle bits get stored.

5/ 16 raw bytes per point → 1.37 bytes average. ~12x reduction. Not a clever architecture — just an entire day of fleet-wide monitoring data made small enough for memory.

6/ Result: ~73x lower query latency, ~14x higher throughput than HBase. ODS launched at ~450 qps; Gorilla scaled past 5,000 steady-state, peaks over 40,000.

7/ The tradeoff: memory-only means a crash replays from a write-ahead log. In a prolonged outage where replay can't keep up, Gorilla doesn't block ingestion — it keeps the last minute and drops the rest. A monitoring system that goes slow during an outage defeats its own purpose.

8/ Facebook open-sourced this as Beringei in 2017, archived it in 2018. The standalone project didn't survive. The mechanism did — almost every metric anyone monitors has this exact shape: fixed interval, slow drift, read as a recent range.

---

## Excalidraw Diagram

**File:** 2026-07-16-facebook-gorilla-tsdb-compression.excalidraw
**Type:** Structural/bit-layout snapshot (structured case study) — three horizontal stages (problem → mechanism → result), plus a standalone bit-encoding box for delta-of-delta + XOR compression as the screenshottable centerpiece. This mechanism is genuinely spatial (bit widths, zero-run positions), so the diagram earns its place per the skill's own rule.
**Color scheme:** Slate for the pre-Gorilla HBase setup (a reasonable design, just mismatched to this one query shape — not a villain), amber for the specific access-pattern mismatch that made scaling HBase pointless, indigo for the Gorilla in-memory mechanism, teal for the measured result. No red/green good/bad pairing.
**Screenshottable stat:** "16 bytes raw → 1.37 bytes compressed (~12x) · 73x lower query latency · 14x higher throughput · 26-hour in-memory window"

### Layout

```
Title: "Facebook Compressed Monitoring Data to 1.37 Bytes a Point — and Cut Query Latency 73x"
Subtitle: "Hundreds of billions of points/day, all in HBase → Gorilla: in-memory, 26-hour write-through cache"

[BEFORE: ODS ON HBASE]           [THE MISMATCH]                      [GORILLA: THE FIX]
Hundreds of billions of          An incident query scans the         In-memory only, sharded per
points/day. Durable, but         freshest, least-compacted           host, holds the most recent
every dashboard query hits       data across thousands of             26 hours as a write-through
HBase directly.                 series at once — exactly            cache in front of HBase.
                                 when everyone else queries too.

                                 More HBase = more of the same
                                 fan-out. Scaling the cluster
                                 scales the wrong axis.

[THE COMPRESSION MECHANISM — screenshottable]
Timestamps (delta-of-delta):  D=0 → '0'  |  D∈[-63,64] → '10'+7 bits  |  D∈[-255,256] → '110'+9 bits  |  else → wider prefix
Values (XOR vs previous):     XOR=0 → '0'  |  else → '1' + reused zero-window OR fresh 5-bit/6-bit window + meaningful bits
16 bytes raw → 1.37 bytes avg (~12x). Same trick both times: consecutive points barely change.

[RESULT]
~73x lower query latency · ~14x higher throughput vs HBase
ODS: ~450 qps at launch → Gorilla: 5,000+ steady-state qps, peaks past 40,000
Prolonged outage: WAL replay can't keep up → Gorilla keeps the last ~1 minute, drops the rest, stays fast

Footnote: The architecture wasn't the trick. Making a full day of every metric on the fleet fit in RAM was —
and the compression that did it just mirrors the shape of the signal: fixed interval, barely changing, read as a recent range.
```
