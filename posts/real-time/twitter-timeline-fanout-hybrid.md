# Twitter's Hybrid Timeline: How One Lady Gaga Tweet Broke the Write Path

**Date:** 2026-06-14
**Slug:** twitter-timeline-fanout-hybrid
**Category:** real-time systems
**Post Type:** structured case study
**Opening Style:** specific_number_that_doesnt_add_up

---

## Sources

- Raffi Krikorian, "Timelines at Scale" — QCon London 2012 (InfoQ)
- Twitter Engineering Blog: "New Tweets per second record, and how!" (2013)
- Raffi Krikorian, "Decomposing Twitter: Adventures in Service-Oriented Architecture" — OSCON 2013

---

## LinkedIn Post

A Lady Gaga tweet used to break Twitter's delivery SLA. Here's how they fixed it.

When Twitter built its home timeline, the model was clean. You tweet → Twitter writes your tweet to every follower's Redis sorted set. Each home timeline cache holds your last 800 tweets from people you follow.

The problem: Lady Gaga had 31 million followers in 2012. One tweet meant 31 million async Redis writes queued through a single Fanout service. During a celebrity spike, timelines lagged by several minutes.

The obvious fix: make the Fanout service faster. They tried. The problem wasn't throughput — it was structural. Any push model breaks when a single graph node has 100× the edges of the median.

So Twitter built a split write path.

Regular users (under ~250K followers) still get the push model. You tweet → Fanout writes directly into each follower's Redis timeline. Sub-5-second delivery.

High-follower accounts — what Twitter internally calls "twitterati" — get a completely different path. Their tweets aren't pushed at write time at all. Instead, when you load your timeline, the Timeline Service merges two sources: your pre-computed Redis feed and a real-time fetch of recent twitterati tweets.

Your home timeline is assembled from data written at two different times, via two different strategies, stitched together the moment you hit refresh.

The trade-off nobody talks about: this made reads heavier. Every timeline load now requires a merge. Twitter offset this with aggressive caching of twitterati tweets — but the read path is fundamentally more expensive than pure push.

The lesson isn't "push bad, pull good." It's that uniform architecture breaks under non-uniform graphs. When your node degree distribution spans four orders of magnitude, one write path isn't enough.

#SystemDesign #DistributedSystems #RealTimeSystems #Engineering

**Character count: ~1,840**

---

## Twitter/X Thread

**1/** A Lady Gaga tweet used to lag your Twitter feed by minutes.

The fix changed how every single timeline load works — even today.

**2/** Twitter's original model was pure push (fanout-on-write).

You tweet → your tweet gets written to every follower's Redis sorted set. Each cache holds your last 800 tweets.

At 31M followers per tweet, the queue chokes.

**3/** The fix wasn't "make the Fanout service faster." They tried that.

The problem was structural: any uniform push model breaks when one graph node has 100× the edges of the median.

**4/** Twitter's solution: split the write path at ~250K followers.

Regular users → push model. Tweet → Fanout writes directly into Redis timelines. Sub-5-second delivery.

High-follower "twitterati" → no push at write time.

**5/** Instead, when you load your timeline, the Timeline Service merges two sources:

— Your pre-computed Redis feed (regular accounts you follow)
— Real-time fetch of recent twitterati tweets

Stitched together every time you hit refresh.

**6/** Trade-off nobody mentions: this made reads more expensive.

Every timeline load now requires a merge operation. Twitter offset this with aggressive twitterati caching — but the read path is fundamentally heavier than pure push.

**7/** Uniform architecture breaks under non-uniform graphs.

When your node degree distribution spans 4 orders of magnitude, one write path isn't enough.

---

## Diagram

See: `twitter-timeline-fanout-hybrid.excalidraw.json`

**Type:** Before/After Side-by-Side
**Style:** Structured case study — migration comparison
**Key numbers:** 31M followers, ~250K threshold, 800 tweets cached per user, < 5s SLA
**Color scheme:** Blue for before (not bad, just limited at scale), Green/orange for after
