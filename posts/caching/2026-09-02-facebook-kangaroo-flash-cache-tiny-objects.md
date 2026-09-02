---
date: 2026-09-02
company: Facebook (Meta)
topic: Why two established flash-caching designs both fail on 100-byte objects, and the hybrid that fixed it
category: caching
post_type: structured
opening_style: shared_pain_point
slug: facebook-kangaroo-flash-cache-tiny-objects
---

## Sources

- USENIX OSDI '20: [The CacheLib Caching Engine: Design and Experiences at Scale](https://www.usenix.org/conference/osdi20/presentation/berg) (Berg et al.)
- ACM SOSP '21: [Kangaroo: Caching Billions of Tiny Objects on Flash](https://dl.acm.org/doi/10.1145/3477132.3483568) (Atikoglu, Berg, Chen, et al.)
- Meta Engineering: [CacheLib, Facebook's open source caching engine for web-scale services](https://engineering.fb.com/2021/09/02/open-source/cachelib/) (Sept 2, 2021)
- Meta Engineering: [Kangaroo: A new flash cache optimized for tiny objects](https://engineering.fb.com/2021/10/26/core-infra/kangaroo/) (Oct 26, 2021)
- GitHub: [facebook/CacheLib](https://github.com/facebook/CacheLib)
- Cross-verification: [Facebook's Kangaroo jumps over flash cache limitations — Blocks & Files](https://blocksandfiles.com/2021/10/29/facebooks-kangaroo-jumps-over-flash-cache-limitations/)

**Key primary-source detail (not in most summaries):** the specific failure mode of a pure set-associative flash cache on ~100-byte objects isn't just "some waste" — because flash reads/writes only happen in multi-KB pages, writing one tiny object direct-to-slot means writing roughly **40x more bytes than the object itself needs**. That number is the whole reason Kangaroo's two-tier design (KLog + KSet) exists instead of a single smarter cache.

**Note:** engineering.fb.com, usenix.org, arxiv.org, and dl.acm.org were unreachable from this research environment's network egress; the figures below are cross-verified across the independent secondary write-ups above (Blocks & Files, plus search-indexed excerpts of the primary papers), which quote the same numbers consistently.

---

## LinkedIn Post

Every flash cache built for tiny objects has to pick its poison: burn DRAM, or burn flash.

Facebook's caching layer, CacheLib, sits behind image caching, social graph lookups, and hundreds of other read paths. A lot of what it caches is small — user metadata, feature values, counters — often under 100 bytes each, and there are billions of them. Moving that data from DRAM to flash is the obvious cost play: SSD storage runs more than 10x cheaper per bit than DRAM. The catch is that flash doesn't do small writes. It reads and writes in pages of several kilobytes, no matter the size of the object going in.

That mismatch breaks both standard designs. A set-associative flash cache — the kind Facebook had already shipped for photo caching — writes each object directly into its slot. Simple, low DRAM overhead, but for a 100-byte object it ends up writing roughly 40x more bytes to flash than the object actually needs, just to fill out the page. A log-structured cache solves the write problem by batching objects sequentially onto flash, but it has to keep a DRAM index entry pointing at every single object sitting there. At billions of tiny objects, that index alone can cost more DRAM than moving to flash was supposed to save in the first place.

Facebook's fix, Kangaroo, doesn't pick a side. It stacks two caches. KLog is a small log-structured cache that absorbs new writes cheaply and quietly drops the objects nobody re-requests. KSet is a large set-associative cache that only the objects surviving KLog get promoted into. Flash only takes the expensive, page-aligned write once an object has proven it's worth keeping. DRAM only indexes the survivors — not everything that ever touched the cache.

Tested against real Facebook and Twitter production traces, Kangaroo matched the DRAM footprint of the best DRAM-optimized design and the flash-write footprint of the best write-optimized design, at the same time — something neither single-strategy design could do alone — while cutting cache misses 29% over the prior state of the art.

The right cache for 100-byte objects wasn't a better version of either existing design. It was refusing to commit to one until the object had earned it.

#SystemDesign #Caching #Facebook #FlashStorage

**Character count: ~2,230 / 3,000 ✓**
**First 140 chars (mobile hook):** "Every flash cache built for tiny objects has to pick its poison: burn DRAM, or burn flash." ✓

---

## Twitter / X Thread

1/ Every flash cache for tiny objects has to pick its poison: waste DRAM, or waste flash.

2/ Facebook's CacheLib caches billions of objects under ~100 bytes each — metadata, counters, feature values. Flash is 10x+ cheaper per bit than DRAM. But flash only writes in multi-KB pages, whatever size the object is.

3/ Set-associative flash caches (Facebook already used one for photos) write ~40x more bytes than a 100-byte object needs, just to fill the page. Log-structured caches fix that — but need a DRAM index entry for every object on flash. Billions of entries.

4/ Facebook's answer: Kangaroo. A small log cache (KLog) filters out one-hit objects cheaply. Only survivors get promoted to a big set-associative cache (KSet) — and only survivors get a DRAM index entry.

5/ Result, on real Facebook/Twitter production traces: DRAM usage of the best DRAM-optimized design, flash writes of the best write-optimized design, at the same time — plus 29% fewer misses than the prior best.

6/ The fix wasn't a smarter single cache. It was making an object prove itself before it gets the expensive treatment.

---

## Diagram

See: `2026-09-02-facebook-kangaroo-flash-cache-tiny-objects.excalidraw`

Type: Comparison matrix (two flawed designs) merging into a hybrid decision box (structured case study style)
Color scheme: Amber (set-associative — reasonable, but 40x write waste) / Blue (log-structured — reasonable, but DRAM-hungry index) → Green (Kangaroo hybrid)
Key screenshottable number: ~40x more bytes written to flash per 100-byte object under set-associative caching, and Kangaroo's 29% miss-rate improvement
