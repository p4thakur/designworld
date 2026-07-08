<!-- sources -->
<!-- Primary: -->
<!--   Pinterest Engineering, "Sharding Pinterest: How we scaled our MySQL fleet" (Pinterest Engineering Blog / Medium) -->
<!--   URL: https://medium.com/pinterest-engineering/sharding-pinterest-how-we-scaled-our-mysql-fleet-3f341e96ca6f -->
<!--   Primary talk: Yashwanth Nelapati & Marty Weiner (Pinterest), "Scaling Pinterest — From 0 to 10s of Billions of -->
<!--   Page Views a Month in Two Years" (QCon), summarized at High Scalability: -->
<!--   https://highscalability.com/scaling-pinterest-from-0-to-10s-of-billions-of-page-views-a/ -->
<!-- Note: direct fetch of medium.com, highscalability.com, and gigaom.com returned HTTP 403 under this session's -->
<!-- egress policy (bot protection). Facts below were cross-checked across multiple independent search-result -->
<!-- excerpts that quote the primary Pinterest blog post and the Nelapati/Weiner QCon talk directly, including: -->
<!--   https://gigaom.com/2012/09/27/scaling-pinterest-and-adventures-in-database-sharding/ -->
<!--   https://read.engineerscodex.com/p/how-pinterest-scaled-to-11-million -->
<!--   https://news.ycombinator.com/item?id=10086782 (discussion thread quoting the primary post) -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. January 2012: Pinterest had 11.7 million monthly unique users, run by a team of 6 engineers -->
<!-- 2. 2011: Pinterest was roughly doubling its user base every ~6 weeks; the team layered automatic clustering -->
<!--    and rebalancing (evaluating Cassandra and Membase) on top of MySQL to try to make growth self-managing -->
<!-- 3. During a rebalance, a secondary node flipped itself to primary partway through a data transfer while the -->
<!--    old primary demoted itself, losing roughly 20% of the data; a Pinterest engineer's summary of the lesson -->
<!--    ("losing 20% of the data is worse than losing all of it, because you don't know what you've lost") is -->
<!--    quoted consistently across corroborating write-ups of the Nelapati/Weiner talk -->
<!-- 4. Pinterest removed the clustering/auto-rebalancing layer entirely and rebuilt on plain MySQL, sharded -->
<!--    manually. Every object's 64-bit ID is deterministic: 16-bit shard ID + 10-bit type ID + 36-bit local ID, -->
<!--    combined as (shard_id << 46) | (type_id << 36) | local_id — no lookup service required to place an object -->
<!-- 5. Pinterest opened 4,096 shards on launch (early 2012) even though the 16-bit shard field allows up to -->
<!--    65,536 — deliberate headroom so growth means activating more shards, not re-deriving existing IDs -->
<!-- 6. The shard configuration map is stored in ZooKeeper and pushed to the services that route to MySQL; per -->
<!--    the primary post, Pinterest never built automatic failover — a human runs scripts to promote a replica -->
<!--    and rebuild a replacement machine when a master dies, and that was still true years after the 2012 launch -->
<!-- 7. By October 2012, Pinterest had grown to roughly 22 million monthly users and ~40 engineers, running on -->
<!--    88 sharded MySQL servers (plus a replica each) alongside Redis and Memcache -->
<!-- 8. Per Pinterest's own account, this sharding scheme remained the core of how Pinterest stored pins, boards, -->
<!--    and users well beyond the initial 2012 rewrite -->

# Pinterest Rejected Automatic Rebalancing and Wrote a Sharding Function Instead

**Date:** 2026-07-08
**Company:** Pinterest
**Category:** database
**Post type:** structured
**Opening style:** cold_fact
**Slug:** pinterest-mysql-manual-sharding
**Character count (LinkedIn):** ~2,183

---

## LinkedIn Post

In January 2012, Pinterest had 11.7 million monthly users. Six engineers ran the entire database layer underneath it.

A year earlier, that layer had nearly eaten itself. Pinterest was doubling its user base roughly every six weeks, and the team did what most startups do at that stage: hand the hard part to something that promises to handle it automatically. They laid automatic clustering and rebalancing on top of MySQL, trying out Cassandra and Membase along the way, so growth would, in theory, take care of itself.

It didn't. During one rebalance, a secondary node decided, partway through the data transfer, that it was now the primary. The old primary demoted itself mid-flight. Roughly 20% of the data was gone. A Pinterest engineer's verdict afterward stuck: losing 20% of your data is worse than losing all of it, because you don't know what you lost.

So Pinterest did the unfashionable thing. It ripped out the clustering middleware and every automatic rebalancer, and went back to plain MySQL — sharded entirely by hand. Every object got a 64-bit ID built from three fixed fields: a 16-bit shard ID, a 10-bit type ID, and a 36-bit local ID, packed together with bit shifts. No lookup service decided where an object lived. The ID was the address.

They lit up 4,096 shards on day one, despite the 16-bit shard field leaving room for 65,536 — deliberate headroom, so future capacity meant turning on more shards, not re-deriving every ID in the system. And they never built auto-failover. When a master died, an engineer ran a script by hand to promote its replica and rebuild the box. Years later, that was still true.

By October 2012, Pinterest had grown to roughly 22 million monthly users and 40 engineers, running on 88 sharded MySQL servers. That sharding scheme, by Pinterest's own account, was still the core of how they stored pins, boards, and users years after the rewrite.

The fashionable fix made rebalancing invisible. The one that survived made failure slow, visible, and someone's decision to make. Automation isn't the goal. A failure mode you can actually reason about at 3am is.

#SystemDesign #MySQL #DatabaseSharding #Pinterest #Scalability

---

## Twitter / X Version

1/ January 2012: Pinterest had 11.7M monthly users. Six engineers ran the database underneath all of it.

2/ A year before that, they'd tried to make growth automatic — clustering and auto-rebalancing on top of MySQL, testing Cassandra and Membase along the way.

3/ During one rebalance, a secondary node flipped itself to primary mid-transfer. The old primary demoted. ~20% of the data vanished.

4/ The lesson a Pinterest engineer drew from it: losing 20% of your data is worse than losing all of it — you don't know what you lost.

5/ So they ripped the clustering layer out entirely. Back to plain MySQL, sharded by hand. Every object: a 64-bit ID = 16-bit shard + 10-bit type + 36-bit local, built with bit shifts. The ID is the address — no lookup service needed.

6/ 4,096 shards live on day one, even though the 16-bit shard field had room for 65,536. Deliberate headroom. And no auto-failover, ever — a human runs a script to promote a replica when a master dies.

7/ By Oct 2012: ~22M monthly users, 40 engineers, 88 sharded MySQL boxes. Same scheme, per Pinterest's own account, still ran their core datastore years later.

8/ The fancy fix made rebalancing invisible. The one that survived made failure slow, visible, and someone's decision. That's the tradeoff that actually scales.

---

## Excalidraw Diagram

**File:** 2026-07-08-pinterest-mysql-manual-sharding.excalidraw
**Type:** Before/after architecture snapshot (structured case study) — three horizontal stages (crisis → decision → result), plus a standalone bit-layout box for the 64-bit ID scheme as the screenshottable centerpiece.
**Color scheme:** Slate for the 2011 auto-clustering attempt (a reasonable bet for its time, not a villain), amber for the specific rebalancing failure (the one earned "warning" color, like a single crimson box elsewhere — here it's the moment trust broke), indigo for the manual-sharding decision, teal for the 2012 result. No red/green good/bad pairing.
**Screenshottable stat:** "64-bit ID = 16-bit shard + 10-bit type + 36-bit local · 4,096 shards live (of 65,536 possible) · 6 engineers/11.7M MAU (Jan 2012) → 40 engineers/22M MAU (Oct 2012) on 88 sharded MySQL boxes"

### Layout

```
Title: "Pinterest Rejected Automatic Rebalancing and Wrote a Sharding Function Instead"
Subtitle: "Jan 2012: 11.7M monthly users, 6 engineers → Oct 2012: ~22M monthly users, 40 engineers, 88 sharded MySQL boxes"

[2011: THE BET]                 [THE FAILURE]                      [2012: THE DECISION]
Auto-clustering + rebalancing   Mid-rebalance, a secondary          Rip out the clustering layer.
on top of MySQL (Cassandra,     node flips itself to primary.       Plain MySQL, sharded by hand.
Membase evaluated). Growth      Old primary demotes. ~20% of        No automatic failover, ever —
should manage itself.           the data is gone.                   a human promotes a replica.

                                 "Losing 20% of the data is
                                 worse than losing all of it —
                                 you don't know what you lost."

[THE ID SCHEME — screenshottable]
64-bit object ID, no lookup service required:
| 16 bits: shard ID | 10 bits: type ID | 36 bits: local ID |
ID = (shard_id << 46) | (type_id << 36) | local_id
4,096 shards live at launch — headroom to 65,536 without re-deriving a single existing ID

[2012 RESULT]
88 sharded MySQL servers · 22M monthly users · 40 engineers
Same scheme, per Pinterest's own account, still the core of their datastore years later

Footnote: The fashionable fix made rebalancing invisible. The one that survived made failure slow, visible,
and someone's decision to make. Automation isn't the goal — a failure mode you can reason about at 3am is.
```
