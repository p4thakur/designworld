<!-- sources -->
<!-- Primary: -->
<!--   Twitter Engineering Blog, "Caching with Twemcache" (2012) -->
<!--   https://blog.x.com/engineering/en_us/a/2012/caching-with-twemcache -->
<!--   Twitter Engineering Blog, "The Infrastructure Behind Twitter: Scale" (2017) -->
<!--   https://blog.x.com/engineering/en_us/topics/infrastructure/2017/the-infrastructure-behind-twitter-scale -->
<!--   GitHub, twitter/pelikan — project repo and wiki -->
<!--   https://github.com/twitter/pelikan -->
<!--   https://github.com/twitter/pelikan/wiki/FAQs  (fetched directly — not blocked) -->
<!--   Pelikan.io blog, "Why Pelikan" (2019) -->
<!--   https://pelikan.io/2019/why-pelikan.html -->
<!--   Yang, Yue, Rashmi, et al., "A large-scale analysis of hundreds of in-memory cache clusters at -->
<!--   Twitter," OSDI 2020 (USENIX) -->
<!--   https://www.usenix.org/system/files/osdi20-yang.pdf -->
<!--   Yang, Yue, et al., "Segcache: a memory-efficient and scalable in-memory key-value cache for small -->
<!--   objects," NSDI 2021 (USENIX, NSDI Community Award) -->
<!--   https://www.usenix.org/conference/nsdi21/presentation/yang-juncheng -->
<!--   Pelikan.io blog, "Segcache: a memory-efficient, scalable cache for small objects with TTL" (2021) -->
<!--   https://pelikan.io/2021/segcache.html -->
<!--     — direct WebFetch of blog.x.com, pelikan.io, danluu.com, and news.ycombinator.com returned -->
<!--     EGRESS_BLOCKED under this session's network policy (same class of gateway-level denial noted on -->
<!--     prior posts in this series). The GitHub-hosted Pelikan wiki FAQ was fetched directly and is not -->
<!--     blocked. Every other fact below was cross-checked across multiple independent web-search-result -->
<!--     excerpts that directly quote or closely paraphrase the primary sources above, not written from -->
<!--     memory. -->
<!-- Corroborating (independent secondary sources, cross-referenced for consistency): -->
<!--   ACM Transactions on Storage, "A Large-scale Analysis of Hundreds of In-memory Key-value Cache -->
<!--   Clusters at Twitter" (journal version of the OSDI'20 paper) -->
<!--   https://dl.acm.org/doi/fullHtml/10.1145/3468521 -->
<!--   Aleksey Charapko, reading-group notes on the OSDI'20 Twemcache paper -->
<!--   https://charap.co/reading-group-a-large-scale-analysis-of-hundreds-of-in-memory-cache-clusters-at-twitter/ -->
<!-- Key verifiable details (cross-referenced across independent search excerpts that quote/summarize -->
<!-- the primary sources consistently): -->
<!-- 1. Twemcache (Twitter's own fork of Memcached, open-sourced 2012) ran hundreds of dedicated cache -->
<!--   servers holding 20TB+ of data for 30+ internal services, collectively serving close to 2 trillion -->
<!--   queries on an average day (23M+ QPS) as of the 2012 announcement post. -->
<!-- 2. By the mid-2010s Twitter also ran Nighthawk, a separate sharded-Redis caching service, which -->
<!--   independent secondary sources describe scaling to roughly 3,000+ Redis nodes, 10TB+ of data, and -->
<!--   10M+ QPS. -->
<!-- 3. Running Twemcache and Redis/Nighthawk as two independent stacks meant duplicated operational and -->
<!--   reliability work; Twitter's own Pelikan project materials describe the motivation as being "stuck -->
<!--   maintaining two independent software stacks" with gaps in functionality and reliability between them. -->
<!-- 4. Pelikan (Twitter's unified, modular cache framework, publicly released) separates data-plane and -->
<!--   control-plane functionality onto different threads and has "no locks anywhere" in the server -->
<!--   (direct quote from the twitter/pelikan GitHub wiki FAQ) — it can be composed into a Memcached- -->
<!--   compatible server, a Redis-compatible server, or a custom variant from the same codebase. -->
<!-- 5. In the OSDI 2020 paper, Twitter's cache/research team analyzed production traces from hundreds of -->
<!--   its own live Twemcache clusters and found that for a large share of real workloads, the choice of -->
<!--   eviction algorithm (LRU, LFU, ARC, etc. — the primary focus of decades of academic cache research) -->
<!--   had limited impact on miss ratio, because TTL-based expiration was already removing most objects -->
<!--   before eviction pressure ever applied. -->
<!-- 6. That finding directly motivated Segcache (NSDI 2021, awarded the NSDI Community Award), which -->
<!--   treats TTL as a first-class organizing principle: objects with similar creation/expiration times are -->
<!--   grouped into shared, fixed-size segments instead of being tracked with full per-object metadata, -->
<!--   enabling bulk (segment-level) expiration and eviction. -->
<!-- 7. Segcache stores about 5 bytes of metadata per object — roughly a 91% reduction versus Memcached's -->
<!--   per-object overhead — and cuts total memory footprint by up to 60% for small-object, TTL-heavy -->
<!--   workloads, while holding throughput comparable to Twitter's existing production cache and improving -->
<!--   write scalability. -->
<!-- Publication: Twitter/X Engineering Blog (2012, 2017), twitter/pelikan GitHub project (ongoing), -->
<!-- Pelikan.io project blog (2019, 2021), USENIX OSDI 2020 and NSDI 2021 conference papers. -->

# Twitter's Cache Handled 2 Trillion Queries a Day. It Was Still Solving the Wrong Problem.

**Date:** 2026-08-27
**Company:** Twitter (X)
**Category:** caching
**Post type:** confessional
**Opening style:** specific_number
**Slug:** twitter-segcache-ttl-eviction-rethink
**Character count (LinkedIn):** ~2020

---

## LinkedIn Post

Twitter's cache layer was already answering nearly 2 trillion queries a day back in 2012, on hundreds of dedicated Twemcache servers holding over 20TB of data for more than 30 internal services. Twemcache — Twitter's own fork of Memcached — was the fix for whatever stock Memcached couldn't handle at that volume, and it ran like that for most of a decade.

But Twemcache for reads and a separate Redis fleet (Nighthawk, eventually 3,000+ nodes) for anything needing structure meant maintaining two independent systems — two sets of bugs, two operational playbooks, two paths to the same class of failure. The fix for that was Pelikan: one modular framework, no locks anywhere in the server, data-plane and control-plane on separate threads, that could be composed into a Memcached-compatible server, a Redis-compatible server, or something else entirely.

That would have been a fine place to stop. Instead, the cache team did something almost nobody does: they pulled production traces from hundreds of their own live clusters and actually looked at what was evicting objects, and why. Cache eviction research runs three decades deep — LRU, LFU, ARC, and everything after. Twitter's own data said most of it barely applied to them. Objects were expiring via TTL long before eviction pressure ever touched them. The thing the industry had spent thirty years optimizing wasn't the thing determining their hit rate.

So they stopped treating TTL as an afterthought bolted onto a generic key-value store and built Segcache around it instead — grouping objects by creation and expiration time into shared segments rather than tracking metadata per key. Five bytes of metadata per object instead of Memcached's usual load: a 91% cut. Up to 60% less memory on small-object, TTL-heavy workloads, at comparable throughput.

Nobody had gotten Memcached "wrong." The industry had just spent decades answering a question their production traffic wasn't really asking.

#SystemDesign #Caching #DistributedSystems #Twitter

---

## Twitter / X Version

1/ Twitter's cache layer was handling ~2 trillion queries a day back in 2012. Hundreds of Twemcache servers, 20TB+ in memory, 30+ services depending on it. Twemcache — their own Memcached fork — ran like that for most of a decade.

2/ But Twemcache for reads plus a separate Redis fleet (Nighthawk, 3,000+ nodes eventually) meant two systems, two bug classes, two playbooks. The fix: Pelikan — one modular, lock-free framework that could become either.

3/ Then the cache team did something rare: pulled traces from hundreds of their own live clusters and checked what was actually evicting objects. Thirty years of eviction research — LRU, LFU, ARC — and it barely mattered. TTL was expiring objects before eviction pressure ever kicked in.

4/ So they rebuilt around that fact instead of ignoring it. Segcache groups objects by creation/expiration time into shared segments instead of per-key metadata. Result: 5 bytes of metadata per object (a 91% cut vs. Memcached) and up to 60% less memory on TTL-heavy, small-object workloads.

5/ Nobody got Memcached "wrong." The field had just spent decades optimizing an answer to a question Twitter's actual traffic wasn't asking.

---

## Excalidraw Diagram

**File:** 2026-08-27-twitter-segcache-ttl-eviction-rethink.excalidraw
**Type:** Four-stage horizontal timeline (2012 → 2016 → 2020 → 2021) with a highlighted "turning point" stage
and a closing reflection band — matching the Confessional post type's recommended layout of showing how the
system evolved over years, with the human/realization moment called out rather than just architecture boxes.
**Color scheme:** Blue for the 2012 origin, slate for the 2016 unification, rose for the 2020 realization
(the uncomfortable finding gets the "warning" color, not because anyone was wrong, but because it upended
assumptions), green for the 2021 result — a blue/slate/rose/green set distinct from the amber/indigo/teal/
violet run used on the prior (storage) post and the run used on the post before that.
**Screenshottable stat:** "OSDI'20: analyzed hundreds of live production clusters. Eviction algorithm choice
barely mattered — TTL was already expiring objects first. Segcache (NSDI'21): 5 bytes of metadata/object,
a 91% cut vs Memcached, up to 60% less memory on TTL-heavy workloads."

### Layout

```
Title: "Twitter's Cache Handled 2 Trillion Queries a Day. It Was Still Solving the Wrong Problem."

[STAGE 1 — 2012, blue]      [STAGE 2 — 2016, slate]      [STAGE 3 — 2020, rose]           [STAGE 4 — 2021, green]
"TWEMCACHE IS BORN           "PELIKAN UNIFIES THEM         "THE UNCOMFORTABLE TRUTH          "SEGCACHE SHIPS
Twitter forks Memcached.     Twemcache (reads) + Redis/     Cache team analyzes traces        Objects grouped by
Hundreds of servers,         Nighthawk (structure) =       from hundreds of its own live      creation/expiration
20TB+ data, 30+ services,    two stacks, two bug           clusters. Eviction algorithm       into shared segments.
~2 trillion queries/day."    classes. Fix: one modular,     choice barely matters — TTL        5 bytes metadata/
                             lock-free framework."          expires objects first."            object. NSDI
                                                                                                Community Award."

[STAT CALLOUT BAND, orange, full width]
"THE NUMBERS: 5 bytes of metadata per object — a 91% cut vs. Memcached. Up to 60% less memory on small-
object, TTL-heavy workloads. Comparable throughput to Twitter's existing production cache."

[FOOTER, indigo band, full width]
"Nobody had gotten Memcached 'wrong.' The industry had just spent three decades answering a question
Twitter's actual production traffic wasn't really asking."
```
