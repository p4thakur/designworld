---
date: 2026-10-11
company: Figma
topic: LiveGraph 100x - replacing a mutation-based query cache fed by one replication stream with sharded caches that are only invalidated and re-queried.
category: real-time systems
post_type: contrarian
opening_style: challenge_assumption
slug: figma-livegraph-invalidate-dont-mutate
---

## Sources

- Figma Blog, [Keeping it 100(x) with real-time data at scale](https://www.figma.com/blog/livegraph-real-time-data-at-scale/) - primary: original single-server mutation-based cache, 3x users / 5x page views, multi-TB tables, cache sharded by query hash, invalidator, ordering no longer significant.
- Figma Blog, [LiveGraph: real-time data fetching at Figma](https://www.figma.com/blog/livegraph-real-time-data-fetching-at-figma/) - primary: original LiveGraph design.
- Better Stack newsletter, [Figma's 100x approach](https://newsletter.betterstack.com/p/figmas-100x-approach-to-scaling-its) - secondary corroboration (invalidator sharded like the DB).

**Note on sourcing:** direct fetches of figma.com were blocked by this environment's egress policy. Facts come from search-indexed excerpts of the Figma posts plus secondary corroboration. Figures not seen in excerpts were left out.

**Key primary-source detail:** Because re-querying always returns the newest result, update ordering stops mattering, which is exactly what allowed the single ordered replication stream to be split up.

---

## LinkedIn Post

Everyone assumes the fast way to keep a live query fresh is to patch the cached result the moment a row changes. Figma's LiveGraph did exactly that. Then it became the thing blocking their growth.

The first version was one server with an in-memory query cache, tailing the replication stream of a single Postgres instance. The cache was mutation-based: each row change was applied directly to the cached results. Elegant, and fast for a long time.

Then users tripled and page views grew 5x, all on one Postgres with tables several terabytes in size. Figma sharded the database. LiveGraph now had to follow.

The obvious move was to shard the cache by hashing the query. That ran into two problems. The database has no idea which cache shard holds a query that cares about a given row. And one change, such as moving a file between folders, can affect results on two shards.

Patching results across shards, in the right order, from one ordered stream, is the hard version of the problem.

So Figma stopped patching. They added an invalidator that only marks affected cache shards as invalid. The next LiveGraph instance that needs the data re-queries the database.

That sounds wasteful, and the team checked before betting on it. Their measurements showed most updates invalidate only a few queries, so the fan-out stays small.

The detail that makes it work: a re-query always returns the newest result. So the order in which invalidations arrive stops mattering. And once ordering stopped mattering, the single replication stream, the thing everything depended on, could be broken up and sharded like the database.

A mutation-based cache has to be right about every change, in order. An invalidation-based cache only has to be right about what is stale, and the database does the rest.

We default to the clever incremental update because it looks cheaper. Sometimes the cheaper system is the one that throws work away and asks again.

#SystemDesign #Caching #Postgres #DistributedSystems

---

## Twitter Version

Conventional wisdom: keep a live query fresh by patching the cached result on every row change.

Figma's LiveGraph did that. One server, one in-memory cache, one Postgres replication stream.

Then users tripled, page views grew 5x, and the database got sharded.

Sharding the cache by query hash broke it. The DB can't tell which cache shard cares about a row, and moving one file between folders can touch two shards.

The fix: stop patching. An invalidator marks shards stale; the next reader re-queries Postgres.

Re-queries always return the newest result, so ordering stopped mattering. That let them split the one ordered stream.

Sometimes throwing work away and asking again is the scalable design.
