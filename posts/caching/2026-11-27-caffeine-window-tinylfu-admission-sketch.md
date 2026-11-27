---
date: 2026-11-27
company: Caffeine (Java cache, successor to Guava's cache)
topic: Guava's CacheBuilder evicts by LRU inside independent segments, each capped at about maximumSize / concurrencyLevel (default 4), so it can evict before it's full. Caffeine, built by the authors of Guava's cache and ConcurrentLinkedHashMap, uses Window TinyLFU. A small LRU admission window (1% of capacity at the start) evicts into a segmented-LRU main space (99%, 80% of it protected), but only when TinyLFU judges the candidate more frequent than main's victim. Frequency comes from a 4-bit count-min sketch: 8 bytes per entry, four counters packed into one 64-byte block (one L1 line), and every counter halved after 10 × maximumSize increments. A hill climber resizes the window from sampled hit rates. Simulator sample report over 43.7M requests: optimal 48.09%, W-TinyLFU 45.25%, LIRS 38.14%, ARC 29.60%, LRU 20.24%. HashDoS guard: a losing candidate at frequency ≥ 6 is admitted when (random & 127) == 0.
category: caching
post_type: structured
opening_style: the_decision
slug: caffeine-window-tinylfu-admission-sketch
---

## Sources

- ben-manes/caffeine wiki, [Efficiency](https://github.com/ben-manes/caffeine/wiki/Efficiency) (raw: `raw.githubusercontent.com/wiki/ben-manes/caffeine/Efficiency.md`). Primary.
  - "in typical workloads LRU is not optimal and may have a poor hit rate in cases like full scans."
  - "W-TinyLfu uses a small admission LRU that evicts to a large Segmented LRU if accepted by the TinyLfu admission policy... The size of the window vs main space is adaptively determined using a hill climbing optimization."
  - "This implementation uses a 4-bit CountMinSketch, growing at 8 bytes per cache entry to be accurate. Unlike ARC and LIRS, this policy does not retain evicted keys."
  - ARC "requires that the cache size is doubled in order to retain evicted keys. It is also patented". LIRS "only achieves its maximum efficiency when the cache size is tripled".
- ben-manes/caffeine wiki, [Design](https://github.com/ben-manes/caffeine/wiki/Design). Primary. The eviction-policy section ("TinyLfu estimates the frequency of the window's victim and the main's victim, choosing to retain the entry with the highest historic usage"), Adaptivity (the hill climber), Fastpath ("When the cache is below 50% of its maximum capacity... The frequency sketch is not initialized"), HashDoS protection ("randomly admitting ~1% of the rejected candidates that have a moderate frequency"), and the lossy read buffer.
- ben-manes/caffeine wiki, [Simulator](https://github.com/ben-manes/caffeine/wiki/Simulator), "Sample Report". Primary. 43,704,979 requests: opt.Clairvoyant 48.09%, sketch.WindowTinyLfu 45.25%, irr.Lirs 38.14%, adaptive.Arc 29.60%, linked.Lru 20.24%. The page doesn't say which trace produced the report.
- ben-manes/caffeine master, [FrequencySketch.java](https://github.com/ben-manes/caffeine/blob/master/caffeine/src/main/java/com/github/benmanes/caffeine/cache/FrequencySketch.java). Primary. "The maximum frequency of an element is limited to 15 (4-bits) and an aging process periodically halves the popularity of all elements." "an item's counters are constrained to a 64-byte block, which is the size of an L1 cache line... the typical cost is only one memory access." `sampleSize = 10L * maximum`, then `reset()` when `++size == sampleSize`. The table is `new long[ceilingPowerOfTwo(maximum)]`, which is where the 8 bytes per entry comes from.
- ben-manes/caffeine master, [BoundedLocalCache.java](https://github.com/ben-manes/caffeine/blob/master/caffeine/src/main/java/com/github/benmanes/caffeine/cache/BoundedLocalCache.java). Primary. `PERCENT_MAIN = 0.99d` ("The initial percent of the maximum weighted capacity dedicated to the main space"), `PERCENT_MAIN_PROTECTED = 0.80d` and `ADMIT_HASHDOS_THRESHOLD = 6`. In `admit()`, when `candidateFreq > victimFreq` the candidate is admitted. Otherwise, when `candidateFreq >= ADMIT_HASHDOS_THRESHOLD`, it returns `(random & 127) == 0`.
- ben-manes/caffeine master, [WindowClimber.java](https://github.com/ben-manes/caffeine/blob/master/caffeine/src/main/java/com/github/benmanes/caffeine/cache/WindowClimber.java). Primary. "W-TinyLFU divides capacity between an admission window, which favors recency, and a main region, where TinyLFU filters new arrivals by frequency. The best split depends on the workload, so the climber adjusts it using the cache's hit statistics."
- ben-manes/caffeine [README](https://github.com/ben-manes/caffeine/blob/master/README.md). Primary. "The improvements draw on our experience designing Guava's cache and ConcurrentLinkedHashMap." Wiki [Guava](https://github.com/ben-manes/caffeine/wiki/Guava): "Guava will evict prior to reaching the maximum size using the LRU algorithm. Caffeine will evict once the threshold has been crossed using the Window TinyLFU algorithm."
- google/guava master, [CacheBuilder.java](https://github.com/google/guava/blob/master/guava/src/com/google/common/cache/CacheBuilder.java). Primary. In the `maximumSize` Javadoc: "the cache **may evict an entry before this limit is exceeded**... each resulting segment inside the cache *independently* limits its own size to approximately `maximumSize / concurrencyLevel`." `DEFAULT_CONCURRENCY_LEVEL = 4`.
- Not used: the TinyLFU paper (arXiv 1512.00727) and highscalability.com were blocked by this session's network settings. Every number above comes from Caffeine's or Guava's own wiki pages and source.

**Key primary-source detail:** the frequency sketch gives up the textbook count-min layout to fit the hardware. A key's four counters are forced into one 64-byte block, an L1 cache line, picked by the high bits of the hash. The source comment says uniform placement "may cause the pipeline to need to wait for four memory loads", while the block layout's "typical cost is only one memory access." A second detail: the HashDoS guard in code is `(random & 127) == 0` for candidates at frequency ≥ 6, which is 1/128 ≈ 0.8%. The Design wiki rounds that to "~1%".

Derived/interpretive (the author's reading, not stated verbatim by a source): "more than double" (45.25 / 20.24 ≈ 2.24×) and "within 3 points of optimal" (48.09 − 45.25 = 2.84) are arithmetic on the sample report. "LRU didn't survive as the eviction policy" is the author's framing: Caffeine still uses LRU, but as the admission window and inside the segmented main space, not as the whole decision. The closing line about "how often" is the author's summary.

---

## LinkedIn Post

The people who built Guava's cache wrote a new one, and LRU didn't survive as the eviction policy.

Guava evicts by LRU, inside segments. Its own Javadoc warns that with concurrencyLevel above 1, each segment "independently limits its own size to approximately maximumSize / concurrencyLevel", so the cache can evict before it's full. The default level is 4.

Caffeine's README says it draws on "our experience designing Guava's cache and ConcurrentLinkedHashMap." In its eviction policy, recency is no longer the whole decision.

Window TinyLFU splits the cache in two. New entries land in a small LRU window, 1% of capacity at the start. The main space, the other 99%, is a segmented LRU with 80% of it protected. When the window overflows, its victim has to earn a place in main. TinyLFU compares the candidate's estimated frequency against main's victim, and the one with the lower count is evicted.

The estimate comes from a 4-bit count-min sketch: four counters per key, a cap of 15, and the minimum wins. It costs 8 bytes per cache entry. Two details explain how it stays cheap.

All four counters for a key sit inside one 64-byte block, the size of an L1 cache line. The source comments say the textbook layout spreads counters across memory and can stall on four loads. The block layout usually costs one.

The sketch also forgets. After 10 × maximumSize increments, every counter is halved. A key that was popular last hour doesn't keep its place forever.

The 1% window doesn't stay at 1%. A hill climber samples the hit rate and moves capacity between the window and main. A recency-heavy workload grows the window and a frequency-heavy one shrinks it.

The simulator docs include a sample report for a 43.7M-request trace:
Bélády's optimal 48.09%
W-TinyLFU 45.25%
LIRS 38.14%
ARC 29.60%
LRU 20.24%

That's more than double LRU's hit rate, and within 3 points of optimal. Unlike ARC and LIRS, it doesn't keep ghost entries for evicted keys.

A frequency gate has its own attack. Collide your keys with the victim's hash, inflate its count, and every newcomer gets rejected. Caffeine's admit() handles this with randomness: a candidate at frequency 6 or above that loses still gets in when (random & 127) == 0, about 1 in 128.

LRU asks one question: when was this last used? Most of the hit-rate gap comes from also asking how often, and that answer fits in 4 bits.

#Caching #Java #SystemDesign #Performance

---

## Twitter Version

Guava's cache evicts by LRU, and the same authors went on to write Caffeine. It puts a frequency gate in front of the main cache.

New keys enter a 1% LRU window. To move into the other 99%, a key has to beat main's victim on estimated frequency.

That frequency comes from a 4-bit count-min sketch: 8 bytes per entry, all four counters in one 64-byte cache line, and every counter halved after 10 × maxSize increments so old popularity fades.

The simulator's sample report, over 43.7M requests:
optimal 48.09%
W-TinyLFU 45.25%
ARC 29.60%
LRU 20.24%

A frequency gate can be attacked with hash collisions, so a losing candidate at frequency ≥ 6 still gets in 1 time in 128.

---

## Diagram

See `2026-11-27-caffeine-window-tinylfu-admission-sketch.excalidraw`. It's a structured before/after with a results bar chart. The before panel, in slate, shows Guava's four independent LRU segments with "each caps at ~maximumSize / 4". The after panel is a left-to-right pipeline: a coffee-brown "Window LRU 1%" box, then an amber "TinyLFU gate (4-bit sketch, 8 B/entry)" box, then a teal "Main SLRU 99%, protected 80% / probation 20%" box. Under the pipeline, a dashed navy strip covers the hill climber and the 64-byte-block / halve-every-10×max sketch details. Below that is a horizontal bar chart of the simulator sample report (48.09 / 45.25 / 38.14 / 29.60 / 20.24) and an amber footer on the 1-in-128 HashDoS admission. Palette: coffee, amber, teal, navy and slate, with no red or green.
