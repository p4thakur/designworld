---
date: 2026-11-16
company: Elasticsearch
topic: Search-idle shards - since 7.0, a shard with no search or get for 30 s stops background refreshes (only if index.refresh_interval was never set), so the next search parks behind a refresh of everything indexed meanwhile; writing refresh_interval "1s" explicitly, the same value as the default, turns the optimization off.
category: search
post_type: narrative
opening_style: mid_scene
slug: elasticsearch-search-idle-shards-explicit-refresh
---

## Sources

- Elasticsearch, [server/.../index/shard/IndexShard.java](https://github.com/elastic/elasticsearch/blob/main/server/src/main/java/org/elasticsearch/index/shard/IndexShard.java) - primary: `scheduledRefresh()` skips the refresh when `engine.allowSearchIdleOptimization() && isSearchIdle() && indexSettings.isExplicitRefresh() == false && active.get()`, logs `"scheduledRefresh: search-idle, skipping refresh"`, and calls `setRefreshPending(engine)`, which records the translog's last write location. `isSearchIdle()` = now - `lastSearcherAccess` >= `index.search.idle.after`. `ensureShardSearchActive()` calls `markSearcherAccessed()`, registers a refresh listener on the pending translog location, and forks `maybeRefresh("ensure-shard-search-active")` onto the REFRESH thread pool; the search's listener fires only after that refresh.
- Elasticsearch, [server/.../index/IndexSettings.java](https://github.com/elastic/elasticsearch/blob/main/server/src/main/java/org/elasticsearch/index/IndexSettings.java) - primary: `INDEX_SEARCH_IDLE_AFTER` = `index.search.idle.after`, default `TimeValue.timeValueSeconds(30)`, dynamic; `DEFAULT_REFRESH_INTERVAL` = 1 s (5 s stateless/serverless); `isExplicitRefresh()` is `INDEX_REFRESH_INTERVAL_SETTING.exists(settings)`, with the javadoc "Returns true iff the refresh setting exists or in other words is explicitly set."
- Elasticsearch docs, [index-modules.md](https://github.com/elastic/elasticsearch/blob/main/docs/reference/elasticsearch/index-settings/index-modules.md) - primary: `index.search.idle.after` "How long a shard can not receive a search or get request until it's considered search idle. (default is 30s)". `index.refresh_interval`: "To opt out of this behavior, set an explicit value for the refresh interval, even if it matches the default value."
- Elasticsearch 7.0 breaking changes, [migrate_7_0/indices.asciidoc](https://github.com/elastic/elasticsearch/blob/7.0/docs/reference/migration/migrate_7_0/indices.asciidoc) - primary: "Skipped background refresh on search idle shards ... Searches that access a search idle shard will be 'parked' until the next refresh happens." 7.0 release notes list it as "Skip shard refreshes if shard is `search idle`" (#27500). The 6.8 `IndexSettings.java` has no `search.idle` setting.

**Key primary-source detail:** the opt-out check is `INDEX_REFRESH_INTERVAL_SETTING.exists(settings)`. It asks whether the setting is *present*, not what its value is. So an index created with `"refresh_interval": "1s"` and an index with no refresh_interval at all both refresh every second on paper, but only the second one goes search-idle. The docs say it directly: set an explicit value "even if it matches the default value."

The opening scenario (4 ms vs several seconds, 2 a.m. load) is illustrative, not a reported incident. Derived (author's reasoning from the code, not a measured benchmark): because idleness is measured from the last searcher access against a 30 s threshold, a client that queries a shard every 20 s keeps it active forever, while a client that queries every 60 s finds it idle every single time and pays an on-demand refresh on each query. The size of that refresh is everything indexed since the last one.

---

## LinkedIn Post

The dashboard query takes 4 ms all afternoon. At 2 a.m. the nightly bulk load starts, and nobody's looking. At 7 a.m. the first person opens the page and the same query takes several seconds. Reload the page and it is fast again.

Elasticsearch did this on purpose.

Since 7.0, a shard that has seen no search or get request for 30 seconds (index.search.idle.after) becomes "search idle." On an idle shard, the 1-second background refresh just stops. IndexShard.scheduledRefresh() logs "search-idle, skipping refresh" and notes the translog position it would have refreshed up to.

The reasoning is sound. A refresh turns the in-memory indexing buffer into a new Lucene segment. Doing that every second while a bulk job runs and nobody reads makes lots of tiny segments that merges then have to clean up. If no one is searching, why pay for visibility nobody uses?

The bill shows up on the first read. ensureShardSearchActive() marks the shard active, adds a listener on that saved translog position, and kicks off a refresh on the refresh thread pool. The search waits for it. The 7.0 migration notes say searches get "parked." After five hours of bulk loading, that refresh is five hours of buffered writes, paid inside one person's request.

Then it gets odder. The skip only applies when isExplicitRefresh() is false, and that method is INDEX_REFRESH_INTERVAL_SETTING.exists(settings). It checks whether the setting is present, not what it says. Write "refresh_interval": "1s" into your template, the same value as the default, and the optimization is off. Two indices with identical settings on paper behave differently because one of them typed the default out.

The access pattern matters too. Idleness is measured from the last searcher access. An alert that runs every 20 seconds keeps its shards warm forever. One that runs every 60 seconds finds them idle every time and pays the refresh on every run.

No one was wrong here. Bulk loading got cheaper, which is what most clusters wanted. But "1s" now means two things depending on whether you wrote it down, and the cost moved from the indexer to whoever searches first.

#Elasticsearch #Search #SystemDesign #Performance

---

## Twitter Version

Query takes 4 ms all day. Overnight bulk load. First search at 7 a.m. takes seconds. Second one is fast.

Elasticsearch 7.0+: no search or get on a shard for 30 s = "search idle." Background refresh stops.

First search then waits for a refresh of everything buffered since.

The opt-out check is refresh_interval.exists(), not its value.

Write "1s" explicitly, same as the default, and the behavior's gone.

Alert every 20 s: always warm. Every 60 s: pays the refresh every time.

---

## Diagram

See `2026-11-16-elasticsearch-search-idle-shards-explicit-refresh.excalidraw` (sequence/timeline: two lanes on one time axis. Lane A, refresh_interval unset: refreshes tick every 1 s, stop at the 30 s idle mark, a bulk load piles up as a growing "pending" bar, the first search arrives and is parked behind one large refresh. Lane B, refresh_interval "1s" written explicitly: refreshes keep ticking and the search returns at once. A callout shows `INDEX_REFRESH_INTERVAL_SETTING.exists(settings)`.) Palette: teal + indigo + sand, no red/green.
