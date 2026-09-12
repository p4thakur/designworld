---
date: 2026-09-12
company: Foursquare
topic: Foursquare sharded its MongoDB check-in database into 200 perfectly equal partitions by user ID — and an eleven-hour outage still followed, because equal key-space isn't equal load
category: database
post_type: confessional
opening_style: cold_fact
slug: foursquare-mongodb-2010-outage
---

## Sources

- Foursquare Engineering Blog: "So, that was a bummer." (October 5, 2010) — the original outage post-mortem, referenced and quoted across all contemporaneous coverage below. Direct fetch of the original foursquare.com/blog URL and its Wayback Machine archive was blocked by this environment's network egress policy at write time.
- TechCrunch: ["Foursquare Explains Yesterday's 11 Hour Outage: An Overloading Of Database Shards"](https://techcrunch.com/2010/10/05/foursquare-downtime), October 5, 2010
- InfoQ: ["4square mongodb outage"](https://www.infoq.com/news/2010/10/4square_mongodb_outage/), October 2010 — summarizes the 10gen (MongoDB) engineering post-mortem
- MongoDB user mailing list: ["Foursquare outage post mortem"](https://groups.google.com/g/mongodb-user/c/UoqU8ofp134) — 10gen CTO Eliot Horowitz's technical walkthrough of the failure, posted for the community
- High Scalability: ["Troubles with Sharding — What can we learn from the Foursquare Incident?"](https://highscalability.com/troubles-with-sharding-what-can-we-learn-from-the-foursquare/)
- ReadWrite: ["Foursquare Offers Very Technical Explanation for Yesterday's Very Long Downtime"](https://readwrite.com/2010/10/05/foursquare_offers_very_technical_explanation_for_y)

**Key primary-source detail (not in most summaries):** Foursquare's sharding was not naive — they split their check-in data into 200 chunks, evenly sized by user ID, which is the textbook MongoDB sharding move. The failure wasn't uneven partitioning of data; it was uneven partitioning of *load*. Because check-in frequency varies wildly by user, an evenly-sized key range does not produce an evenly-sized working set. Compounding it, check-in documents are only ~300 bytes while MongoDB allocated storage in 4KB pages at the time — so as documents moved (grew, reallocated), the vacated pages weren't reclaimed, silently inflating disk footprint through fragmentation that monitoring wasn't tracking. That combination — correct-looking partitioning plus invisible fragmentation — is the mechanism most retellings compress into "MongoDB ran out of memory."

**Note on sourcing:** Direct fetch of techcrunch.com, infoq.com, groups.google.com, highscalability.com, readwrite.com, and web.archive.org was blocked by this environment's network egress policy at write time. The specific numbers above — 66GB RAM per shard, shard0 reaching ~67GB against ~50GB on shard1, the 200-chunk user-ID partitioning, the ~300-byte check-in / 4KB-page fragmentation mechanism, the failed mid-outage attempt to add a third shard, the four-hour offline compaction, and the slow EBS volumes of the era — are drawn from search-indexed excerpts and quotes of the primary sources above, cross-checked across TechCrunch, InfoQ, the MongoDB mailing-list post-mortem, and High Scalability's independent write-up, all of which agree on the same figures.

---

## LinkedIn Post

On October 4th, 2010, Foursquare's check-ins went dark for eleven hours. The cause wasn't sloppy capacity planning. It was worse — they'd planned it by the book, and the book was wrong.

Foursquare sharded its MongoDB check-in database across two boxes, split by user ID into 200 evenly sized chunks — straight out of the sharding playbook. Each shard ran on a machine with 66GB of RAM, sized to hold its half of the dataset comfortably.

For months, it worked exactly as designed. Then it didn't.

200 equal partitions of user IDs is not the same as 200 equal partitions of load. Some users check in a dozen times a day; most barely touch the app. By early October, one shard's actual working set had quietly pulled ahead of the other's — invisible to monitoring that watched disk usage, not RAM pressure from a slowly bloating index.

There was a second, smaller mechanism working against them. Check-ins are tiny, about 300 bytes. MongoDB allocates storage in 4KB pages. Every time a document moved, the old page stayed reserved, mostly empty. Not a leak — just fragmentation, compounding quietly until one shard's live-plus-fragmented footprint crossed 67GB against 66GB of RAM.

Once the working set stopped fitting in memory, every read started paging to disk. Disk is slow. Queries backed up. The backlog forced more paging. The system didn't degrade gracefully — it fell off a cliff.

Mid-outage, the team added a third shard and started migrating chunks off the hot one. It didn't help. The real problem was fragmentation on disk, and MongoDB at the time could only compact a shard offline. Four hours of compaction — slower still because of how slow EBS was back then — closed out the eleven hours.

Nobody undersized the hardware. Nobody miscounted the shards. The partitioning was even by every number they were watching. It just wasn't the number that mattered.

#SystemDesign #MongoDB #DistributedSystems #Databases

**Character count: ~1,929 / 3,000 ✓**
**First 140 chars (mobile hook):** "On October 4th, 2010, Foursquare's check-ins went dark for eleven hours. The cause wasn't sloppy capacity planning. It was worse — they'd pl" ✓

---

## Twitter / X Thread

1/ On Oct 4, 2010, Foursquare went dark for 11 hours. Not because they under-provisioned. Because "even" wasn't even.

2/ Check-ins were sharded across 2 MongoDB boxes, split into 200 equal chunks by user ID. Textbook. Each shard: 66GB RAM.

3/ 200 equal partitions of user IDs ≠ 200 equal partitions of load. Some users check in nonstop, most barely do. The shards drifted apart in actual heat, not in size.

4/ Check-ins are ~300 bytes. MongoDB allocates in 4KB pages. Every time a doc moved, the old page stayed reserved, mostly empty. Silent fragmentation — until one shard's real footprint hit 67GB against 66GB of RAM.

5/ Working set stopped fitting in RAM → disk paging → slow queries → backlog → more paging → collapse.

6/ They added a 3rd shard mid-outage and migrated chunks off the hot one. Didn't help — the real problem was disk fragmentation, and MongoDB could only compact offline. 4 hours of compaction (slow EBS didn't help) closed out the 11 hours.

7/ The partitions were perfectly even. Just not on the axis that mattered.

---

## Diagram

See: `2026-09-12-foursquare-mongodb-2010-outage.excalidraw`

Type: Bar/spike visualization (confessional style) — two shard bars against a dashed 66GB RAM ceiling line, with a callout at the exact crossing point where the working set exceeds RAM and disk paging begins.
Color scheme: amber/orange for the shard that crossed the ceiling (the one that mattered, not simply "bad"), slate gray for the shard that stayed under it (not "good" — just quieter users), blue banner for the closing reflection. No red/green good-bad pairing.
Key screenshottable number: 67GB of working set against a 66GB RAM ceiling, split across "200 evenly-sized" chunks — the gap between even partitioning and even load.
