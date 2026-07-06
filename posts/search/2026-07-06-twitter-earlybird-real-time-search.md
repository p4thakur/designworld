<!-- sources -->
<!-- Primary: -->
<!--   Twitter Engineering Blog (2010), "Twitter's New Search Architecture" -->
<!--   URL: https://blog.twitter.com/engineering/en_us/a/2010/twitters-new-search-architecture -->
<!--   Twitter Engineering Blog (2011), "The Engineering Behind Twitter's New Search Experience" -->
<!--   URL: https://blog.twitter.com/engineering/en_us/a/2011/the-engineering-behind-twitter-s-new-search-experience -->
<!--   Twitter Engineering Blog (2020), "Reducing search indexing latency to one second" -->
<!--   URL: https://blog.twitter.com/engineering/en_us/topics/infrastructure/2020/reducing-search-indexing-latency-to-one-second -->
<!--   Busch, M. et al., "Earlybird: Real-Time Search at Twitter," IEEE ICDE 2012 -->
<!--   URL: https://ieeexplore.ieee.org/document/6228205 (also https://dl.acm.org/doi/10.1109/ICDE.2012.149) -->
<!-- Note: direct fetch of blog.twitter.com/blog.x.com and notes.stephenholiday.com returned HTTP 403 under this -->
<!-- session's egress policy; facts and figures below are cross-checked across multiple independent search-result -->
<!-- excerpts quoting the primary Twitter engineering posts and the Busch et al. paper directly (the 2 billion -->
<!-- queries/day figure, the 17,000 QPS per 16M-tweet segment figure, and the unrolled-linked-list-to-skip-list -->
<!-- migration matched verbatim across independent summaries), rather than a single full-text fetch. -->
<!-- Corroborating (cross-checked, consistent on figures below): -->
<!--   https://blog.reachsumit.com/posts/2020/07/twitter-search-redesign/ -->
<!--   https://notes.stephenholiday.com/Earlybird.pdf -->
<!--   https://techcrunch.com/2008/07/15/confirmed-twitter-acquires-summize-search-engine/ -->
<!--   https://www.usv.com/writing/2008/07/twitter-acquires-summize/ -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. July 2008: Twitter acquired Summize, a real-time tweet-search startup running Ruby on Rails with a -->
<!--    MySQL backend; Summize built its inverted index on top of MySQL's B-tree indexes -->
<!-- 2. By ~2010, tweet volume had grown into the hundreds of millions per day; the MySQL-based index could not -->
<!--    keep up with simultaneous high-rate writes and reads, so Twitter rebuilt search around an inverted index -->
<!--    rather than a relational database -->
<!-- 3. Twitter chose Apache Lucene as a base, then rewrote Lucene's core in-memory posting-list data structures -->
<!--    to support real-time (in-place) updates, since stock Lucene assumed periodic batch reindexing, not -->
<!--    millisecond-fresh content; the result shipped as "Earlybird" -->
<!-- 4. Per the 2012 Busch et al. paper: Earlybird ingested roughly 6,000 tweets/second on average (~500 million -->
<!--    tweets/day) and served over 2 billion queries/day at ~50ms average query latency; a single 16-million- -->
<!--    tweet index segment achieved ~17,000 QPS at sub-100ms p95 latency, and a fully loaded server holding -->
<!--    144 million tweets sustained ~5,000 QPS -->
<!-- 5. Earlybird's posting lists were implemented as unrolled linked lists (cache-friendly, low pointer overhead) -->
<!--    but only correct if incoming tweets arrive in strictly increasing ID order, since the structure can't -->
<!--    cheaply insert into the middle of the list -->
<!-- 6. Twitter's document IDs encoded a timestamp at microsecond granularity (27 bits) plus a 4-bit same- -->
<!--    microsecond counter (room for 16 tweets); tweets beyond that count landed in the next segment slightly -->
<!--    out of strict order -->
<!-- 7. By 2019, that ordering assumption had become a bottleneck: new tweets could take up to ~15 seconds to -->
<!--    become searchable, on a system originally built to make Twitter search "real-time" -->
<!-- 8. Twitter's fix (shipped ~2019-2020) replaced unrolled linked lists with skip lists, which support O(log n) -->
<!--    lookups/insertions at arbitrary positions and adapt more easily to concurrency; this cut indexing latency -->
<!--    by more than 90% (absolute), down to about one second -->

# Twitter's Earlybird: The Real-Time Fix That Got Old

**Date:** 2026-07-06
**Company:** Twitter (X)
**Category:** search
**Post type:** confessional
**Opening style:** specific_number
**Slug:** twitter-earlybird-real-time-search
**Character count (LinkedIn):** ~2,328

---

## LinkedIn Post

Twitter's search index answers more than two billion queries a day. In 2019 — a decade after Twitter first solved "real-time" search — a new tweet could still take up to 15 seconds to become searchable.

Back in 2008, Twitter bought a small startup called Summize just to have real-time search at all. Summize's engine ran on Rails and MySQL, with B-tree indexes doing double duty as an inverted index. It worked, because Twitter was still small enough that a relational database could handle constant writes and constant reads at roughly the same time.

That stopped being true within about two years. By 2010, ingestion had grown into the hundreds of millions of tweets a day, and a system built for transactions wasn't built to be rewritten thousands of times a second while also serving search queries. Twitter didn't patch MySQL — they replaced the model, building an inverted index around Apache Lucene. But even Lucene wasn't ready: it assumed indexes get rebuilt periodically, not that content becomes searchable within milliseconds of being posted. So Twitter rewrote Lucene's internal posting lists to update in place. It shipped as "Earlybird," and it worked well enough to still be running Twitter search a decade later — ~500 million tweets a day, 17,000 queries per second on a single 16-million-tweet segment.

Earlybird's posting lists were unrolled linked lists — fast, cache-friendly, and correct only if every tweet arrives in strict order. Document IDs encoded a timestamp down to the microsecond, with 4 bits left as a same-microsecond counter: room for 16 tweets before the next one had to jump segments and land slightly out of order. That assumption held for years. By 2019, it was costing 15 seconds of indexing latency on a system named for being early.

The fix wasn't smarter indexing. It was swapping unrolled linked lists for skip lists — a structure that tolerates insertion anywhere, not just the end — cutting indexing latency by more than 90%, down to about a second.

Nobody misdesigned Earlybird in 2010. It beat MySQL badly, on the numbers that mattered at the time. It just turned out that "real-time" isn't a fixed target. The system Twitter built to escape one era's staleness spent the next decade quietly becoming the source of the next one.

#SystemDesign #Search #Twitter #Engineering

---

## Twitter / X Version

1/ Twitter's search answers 2 billion+ queries a day. In 2019, a new tweet could still take up to 15 seconds to become searchable. A decade earlier, Twitter had already "solved" real-time search once.

2/ 2008: Twitter buys Summize for real-time tweet search. Rails + MySQL, B-tree indexes moonlighting as an inverted index. Fine, until tweet volume hit hundreds of millions a day and a transactional DB doing nonstop rewrites-plus-reads gave out.

3/ 2010: Twitter rebuilds on Lucene. But stock Lucene wasn't built for millisecond-fresh content either, so they rewrote its posting lists to update in place. Shipped as "Earlybird." Ran Twitter search for a decade — ~500M tweets/day, 17K QPS per segment.

4/ The catch: Earlybird's posting lists were unrolled linked lists — fast, but only correct if tweets arrive in strict order. Document IDs packed a microsecond timestamp + a 4-bit counter — room for 16 tweets before the next one landed slightly out of order.

5/ By 2019 that assumption was costing 15 seconds of indexing latency. Fix: swap unrolled linked lists for skip lists, which allow insertion anywhere. Indexing latency dropped 90%+, to about a second.

6/ Earlybird wasn't a mistake in 2010 — it crushed MySQL. Turns out "real-time" isn't a fixed target. The fix for one era's staleness spent the next decade becoming the next one's bottleneck.

---

## Excalidraw Diagram

**File:** 2026-07-06-twitter-earlybird-real-time-search.excalidraw
**Type:** Timeline showing system evolution over years, focused on the human/technical cause rather than pure architecture boxes (confessional)
**Color scheme:** Slate for the 2008 MySQL era (adequate for its time, not "bad"), indigo for the 2010 Earlybird rebuild, amber for the ordering assumption quietly aging into a bottleneck, teal for the 2020 skip-list fix. No red/green good/bad pairing — this isn't a failure story, it's a system outgrowing itself.
**Screenshottable stat:** "2008: MySQL search → 2010: Earlybird (500M tweets/day, 17K QPS/segment) → 2019: 15s indexing lag → 2020: skip lists cut it to ~1s"

### Layout

```
Title: "Twitter's Earlybird: The Real-Time Fix That Got Old"
Subtitle: "2B+ queries/day · 2019: tweets took up to 15s to become searchable · 2020: skip lists cut that to ~1s"

[2008]                    [2010]                       [2012 — AT SCALE]              [2019]                      [2020]
Twitter buys              MySQL can't keep up.          Earlybird in production:       The ordering               Unrolled linked
Summize for real-         Twitter rebuilds search       ~500M tweets/day ingested,     assumption cracks:         lists replaced
time tweet search.        on Lucene, rewriting its      2B+ queries/day, ~50ms avg     new tweets take up         with skip lists —
Rails + MySQL,             posting lists to update       latency. 17K QPS on a          to 15s to become           insertion works
B-tree index doing        in place instead of           16M-tweet segment.             searchable. Named          anywhere, not just
double duty as            periodic rebuilds.            Doc IDs: 27-bit microsecond    for being early, now       the end. Indexing
inverted index.           Ships as "Earlybird."          timestamp + 4-bit counter      running behind.           latency: -90%+,
                                                          (16 tweets/µs before order                               down to ~1s.
                                                          slips).

Footnote: Nobody misdesigned Earlybird in 2010 — it beat MySQL badly on the numbers that mattered then. The
system built to escape one era's staleness spent the next decade quietly becoming the source of the next one.

Timeline: 2008 MySQL search -> 2010 Earlybird rebuild on Lucene -> 2012 running at scale (500M tweets/day)
          -> 2019 15s indexing lag exposed -> 2020 skip lists cut latency to ~1s
```
