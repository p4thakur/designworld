---
date: 2026-10-19
company: Elasticsearch
topic: Deep pagination with from/size, the 10,000 hit window, and why search_after plus a point in time replaced it.
category: search
post_type: confessional
opening_style: number_that_doesnt_add_up
slug: elasticsearch-deep-pagination-search-after-pit
---

## Sources

- Elastic, [Paginate search results](https://github.com/elastic/elasticsearch/blob/main/docs/reference/elasticsearch/rest-apis/paginate-search-results.md) - primary: every shard loads the hits of all previous pages, 10,000 default limit, search_after, PIT, `_shard_doc` tiebreaker, tie-break warning across replicas.
- Elastic, [Index modules](https://github.com/elastic/elasticsearch/blob/main/docs/reference/elasticsearch/index-settings/index-modules.md) - primary: `index.max_result_window` defaults to 10000 and exists to cap heap use proportional to `from + size`.

**Note on sourcing:** only GitHub-hosted docs were reachable from this environment, so every number below comes from those two pages. The 5-shard example is arithmetic on the documented behavior, not a measured benchmark.

**Key primary-source detail:** the docs warn that Lucene internal doc IDs are the tiebreaker and "can be completely different across replicas of the same data", so even plain from/size paging can order equal-sorted documents inconsistently between pages. A PIT adds an implicit `_shard_doc` tiebreaker that is unique and constant within the PIT.

---

## LinkedIn Post

The number is 10,000, and it is not a round number someone picked for fun. It is the cap on from + size in Elasticsearch, and it exists because page 1,000 does not cost what page 1 costs.

Paging with from and size feels free. Skip 20, take 10. Every ecommerce search box and admin table starts there, and it works for years.

Then someone scrolls deep. The docs spell out why this hurts: a search usually spans multiple shards, and each shard must load its requested hits plus the hits for every previous page into memory. There is no cheap skip. Ask for hits 9,990 to 10,000 on an index with 5 shards and each shard builds a sorted list of 10,000 entries so the coordinating node can merge 50,000 candidates to keep 10. That is arithmetic on the documented behavior, but it is why the setting, index.max_result_window, defaults to 10000 and is described as a limit on heap memory.

The honest part: raising that limit is the first thing most teams do. It makes the error go away, and it makes the cost bigger. The docs say exactly this: degraded performance or node failures. The setting was a seatbelt and we treated it as a speed limit sign.

The replacement is search_after. Instead of "skip N", you send the sort values of the last hit you saw, and each shard only has to find what comes after that point. The page cost stops growing with depth.

It brings its own trap. Between requests a refresh can change the index, so pages shift. The fix is a point in time: open a PIT, search against it, and the view stays frozen. PIT searches add a hidden tiebreaker called _shard_doc, unique per document and constant within the PIT. Without a tiebreaker, the docs say your paged results could miss or duplicate hits.

One more detail that rarely makes it into tutorials: with from/size, ties are broken by Lucene's internal doc IDs, and the docs warn these can differ across replicas of the same data. Two identical requests can order equal documents differently if they hit different copies.

Offset pagination was never wrong. It was an interface that hid a cost, and the cost showed up at the worst page.

#Elasticsearch #SystemDesign #Search #Backend

---

## Twitter Version

Elasticsearch caps from + size at 10,000. Not arbitrary.

Each shard has to load the hits for every previous page. 5 shards, hits 9,990-10,000: each builds 10,000 entries, the coordinator merges 50,000 to return 10.

Raising max_result_window just makes the cost bigger.

Fix: search_after with the last hit's sort values, plus a PIT so a refresh can't shift pages. PIT adds a unique _shard_doc tiebreaker.

Bonus from the docs: with plain from/size, ties use Lucene doc IDs that can differ across replicas.

---

## Diagram

See `2026-10-19-elasticsearch-deep-pagination-search-after-pit.excalidraw` (candidates merged per page: from/size grows with depth, search_after stays flat, with the 10,000 cap marked).
