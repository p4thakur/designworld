<!-- sources -->
<!-- Primary: -->
<!--   Muralidhar et al., "f4: Facebook's Warm BLOB Storage System" (OSDI 2014) -->
<!--   URL: https://www.usenix.org/system/files/conference/osdi14/osdi14-paper-muralidhar.pdf -->
<!--   USENIX session page: https://www.usenix.org/conference/osdi14/technical-sessions/presentation/muralidhar -->
<!-- Note: direct fetch of usenix.org, cs.princeton.edu, snia.org, and several paper-review blogs all returned -->
<!-- HTTP 403 under this session's egress policy (same class of gateway-level denial hit on prior posts in this -->
<!-- series). Facts below were cross-checked across multiple independent web-search-result excerpts that quote -->
<!-- or closely paraphrase the primary OSDI paper directly, plus corroborating secondary coverage: -->
<!--   Adrian Colyer, "f4: Facebook's warm BLOB storage system" (The Morning Paper) — -->
<!--     https://blog.acolyer.org/2014/12/16/f4-facebooks-warm-blob-storage-system/ -->
<!--   umbrant, "Paper review: Facebook f4" — https://www.umbrant.com/2014/10/29/paper-review-facebook-f4/ -->
<!--   Massive Technical Interviews Tips summary — -->
<!--     https://massivetechinterview.blogspot.com/2015/10/f4-facebooks-warm-blob-storage-system.html -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Published at OSDI 2014. f4 stored over 65PB of logical BLOBs at time of publication. -->
<!-- 2. Haystack's replication factor: triple geographic replication x 1.2 RAID-6 overhead = 3.6x effective. -->
<!-- 3. Access-rate drop-off: request rate for week-old BLOBs was an order of magnitude lower than for -->
<!--    less-than-a-day-old content, for 8 of 9 examined BLOB types. -->
<!-- 4. Migration trigger metric: 99th-percentile IOPS/TB per BLOB type. Synthetic benchmarks showed f4's 4TB -->
<!--    drives could handle ~80 IOPS with acceptable latency; migration to f4 made sense once a type's -->
<!--    IOPS/TB fell below 20. -->
<!-- 5. Migration timeline: photos migrated to f4 after three months; other BLOB types after one month. -->
<!--    Profile photos do not exhibit the drop-off and are never moved to f4. -->
<!-- 6. f4 mechanism: Reed-Solomon(10,4) erasure coding within a single datacenter (10 data blocks + 4 parity -->
<!--    blocks laid out across different racks), giving 1.4x local overhead (14/10) while tolerating disk, -->
<!--    host, and rack failure. A geo-replicated copy in a second datacenter brings this to 2.8x; XOR coding -->
<!--    across the two datacenters' encoded copies reduces the effective factor further to 2.1x, while still -->
<!--    tolerating the loss of an entire datacenter. -->

# Facebook Measured 99th-Percentile IOPS Per Terabyte. That Number Cut Their Storage Bill by Nearly Half.

**Date:** 2026-07-30
**Company:** Facebook
**Category:** storage
**Post type:** confessional
**Opening style:** cold_fact
**Slug:** facebook-f4-warm-blob-storage-erasure-coding
**Character count (LinkedIn):** ~2,508

---

## LinkedIn Post

By 2014, Facebook was storing over 65 petabytes of photos and video in Haystack, its purpose-built BLOB store. Every byte — the one uploaded ten seconds ago and the one uploaded four years ago — was replicated 3.6 times.

Haystack earned that redundancy honestly. Built in 2008, it solved a real problem: a plain filesystem needed several disk seeks just to find a photo's metadata before reading a byte of it. Haystack kept the whole offset index in memory and appended data straight to a log file — one seek, not several — then replicated that file three times across two datacenters, plus RAID-6, for 3.6x total. It fit the access pattern Facebook had in 2008: almost every stored photo had just been uploaded.

By 2014 that pattern had quietly stopped being true. For eight of nine measured BLOB types, week-old content got an order of magnitude fewer reads than content uploaded that same day. Every cooling photo still sat on hardware provisioned for peak demand, still replicated 3.6 times — because in Haystack's design, durability and throughput were the same number. An old photo couldn't get less redundancy without also getting less durability.

So they measured the real thing: 99th-percentile IOPS per terabyte, per BLOB type, over time. A 4TB drive could safely serve about 80 IOPS. Once a type's trailing IOPS/TB dropped under 20 — a quarter of the disk's real capacity — the extra copies weren't buying availability anymore. They were buying headroom nobody would spend.

That's what f4 sells back. Instead of full copies, it erasure-codes each stripe with Reed-Solomon(10,4) — 10 data blocks plus 4 parity, spread across racks — tolerating the same disk, host, and rack failures Haystack did, for 1.4x overhead instead of 3x. Mirror the encoded copy into a second datacenter and you're at 2.8x. XOR the two datacenters' encoded copies against each other and it drops to 2.1x, still surviving a full datacenter loss. A router tracks IOPS/TB per volume and migrates it once it crosses the line: three months for photos, one month for the other eight types. Profile photos never move — people look at those forever.

Nothing about Haystack was a mistake in 2008. One replication factor was just answering two different questions — durability and throughput — for six years after the corpus's shape had already changed underneath it. At 65 petabytes, 3.6x down to 2.1x is on the order of 100 petabytes of disk that no longer needed to spin.

#SystemDesign #DistributedSystems #Storage #Facebook

---

## Twitter / X Version

1/ By 2014 Facebook was storing 65+ petabytes in Haystack, its BLOB store. Every byte — one second old or four years old — got replicated 3.6x. Nobody was checking whether the old stuff still needed that.

2/ Haystack (2008) solved a real problem: normal filesystems needed multiple disk seeks to find a photo's metadata. Haystack kept the index in RAM and appended data to a log — one seek — then replicated 3x across two datacenters + RAID-6. Built for content that just got uploaded.

3/ By 2014 that stopped being true. For 8 of 9 BLOB types, week-old content got an order of magnitude fewer reads than day-old content. Every cooling photo still sat at full 3.6x replication, because durability and throughput were the same number in Haystack's design.

4/ So they measured it: 99th-percentile IOPS/TB per type. A 4TB drive safely handles ~80 IOPS. Once a type dropped under 20 IOPS/TB, the extra replicas were pure unused headroom.

5/ f4: Reed-Solomon(10,4) erasure coding → 1.4x local overhead instead of 3x, same fault tolerance. Geo-mirror → 2.8x. XOR across datacenters → 2.1x, still survives a full DC loss. A router migrates volumes once IOPS/TB crosses the line — 3 months for photos, 1 month for everything else. Profile photos never move.

6/ Haystack wasn't wrong in 2008. One replication number was just answering two different questions — durability and throughput — six years after the corpus stopped looking like it did on day one.

---

## Excalidraw Diagram

**File:** 2026-07-30-facebook-f4-warm-storage-erasure-coding.excalidraw
**Type:** Confessional bar chart / spike visualization — four content-type bars showing IOPS/TB demand crossing (or not crossing) the migration threshold, with a callout pair below explaining the mismatch and the fix.
**Color scheme:** Slate for content that legitimately stays in Haystack (day-old baseline, and the profile-photo exception), teal for content that migrates to f4, amber for the threshold line and the mismatch callout, indigo for the "what changed" callout. No red/green — Haystack wasn't broken, it just kept answering a question the corpus had stopped asking.
**Screenshottable stat:** "A 4TB drive safely serves ~80 IOPS. Once a BLOB type's 99th-percentile IOPS/TB drops under 20, migrate it to f4. Photos cross that line at 3 months. Profile photos never cross it — people look at those forever."

### Layout

```
Title: "Facebook Measured 99th-Percentile IOPS Per Terabyte. That Number Cut Their Storage Bill by Nearly Half."
Subtitle: "OSDI 2014 — how a trailing IOPS/TB signal turned into f4, Facebook's warm BLOB storage system"

[BAR CHART — IOPS/TB needed, by content age/type]

  Bar A (slate, tall)      Bar B (teal, short)         Bar C (teal, short)          Bar D (slate, tall)
  DAY 1 — ANY TYPE          OTHER 8 TYPES — 1 MONTH      PHOTOS — 3 MONTHS             PROFILE PHOTOS — 3mo+
  Peak reads right          Request rate already an      Same drop-off, just           No drop-off — people
  after upload.              order of magnitude down.     slower. Crosses the           look at these forever.
  Stays in Haystack.          → migrates to f4              line later. → f4              Never migrates.

  [dashed threshold line across the B/C gap, labeled:
   "20 IOPS/TB = f4 migration trigger · a 4TB drive safely handles ~80 IOPS/TB"]

[CALLOUT — amber — THE MISMATCH]
Haystack replicated every object 3.6x — three full geographic copies x 1.2 for RAID-6 — no matter whether it
was read a thousand times a day or once a year. Durability and throughput were the same number: an old photo
couldn't get less redundancy without also getting less durability.

[CALLOUT — indigo — WHAT CHANGED]
f4 decouples them. Reed-Solomon(10,4) erasure-codes each stripe — 10 data blocks, 4 parity blocks, spread
across racks — for 1.4x local overhead instead of 3x, same failure tolerance. A geo-mirrored copy in a second
datacenter brings it to 2.8x; XOR-coding the two datacenters' encoded copies against each other cuts it to
2.1x, still surviving a full datacenter loss. A router tracks trailing IOPS/TB per volume and migrates it
once it crosses the line.

[REFLECTION — slate, footnote]
Haystack wasn't a bad design — it was tuned for the exact shape of the corpus in 2008, when almost every
stored photo had just been uploaded. The problem was quieter: one replication number was being asked to
answer two different questions for six years after the corpus's shape had already changed underneath it.
```
