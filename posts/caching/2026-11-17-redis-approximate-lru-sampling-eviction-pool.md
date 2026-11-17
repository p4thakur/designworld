---
date: 2026-11-17
company: Redis
topic: Redis "allkeys-lru" is not LRU - it keeps 24 bits of last-access time per object (1-second resolution), samples maxmemory-samples=5 random keys per eviction into a 16-entry candidate pool, and evicts the oldest; it skips even that 24-bit write on reads while a fork child exists to avoid copy-on-write. True LRU's linked list would cost two pointers per key and writes on every read.
category: caching
post_type: contrarian
opening_style: challenge_assumption
slug: redis-approximate-lru-sampling-eviction-pool
---

## Sources

- Redis, [src/evict.c](https://github.com/redis/redis/blob/unstable/src/evict.c) - primary: `#define EVPOOL_SIZE 16`; comment "Redis uses an approximation of the LRU algorithm that runs in constant memory. Every time there is a key to expire, we sample N keys (with N very small, usually in around 5) to populate a pool of best keys to evict"; "we don't remove keys from the pool when they are deleted so the pool may contain keys that no longer exist." `estimateObjectIdleTime()` returns `(lruclock - o->lru) * LRU_CLOCK_RESOLUTION` and handles wrap-around. LFU section: "We have 24 total bits of space in each object ... since we re-use the LRU field", split as 16 bits last-access time in minutes + 8-bit `LOG_C` logarithmic counter; `LFULogIncr()` increments with probability `1.0/(baseval*lfu_log_factor+1)`, saturating at 255.
- Redis, [src/object.h](https://github.com/redis/redis/blob/unstable/src/object.h) and [7.2 src/server.h](https://github.com/redis/redis/blob/7.2/src/server.h) - primary: `#define LRU_BITS 24`, `LRU_CLOCK_MAX ((1<<LRU_BITS)-1)`, `LRU_CLOCK_RESOLUTION 1000 /* LRU clock resolution in ms */`. 7.2 `struct redisObject { unsigned type:4; unsigned encoding:4; unsigned lru:LRU_BITS; int refcount; void *ptr; }`.
- Redis 7.2, [src/db.c](https://github.com/redis/redis/blob/7.2/src/db.c) `lookupKey()` - primary: "Update the access time for the ageing algorithm. Don't do it if we have a saving child, as this will trigger a copy on write madness." guarded by `if (!hasActiveChildProcess() && !(flags & LOOKUP_NOTOUCH))`.
- Redis, [redis.conf](https://github.com/redis/redis/blob/unstable/redis.conf) and [src/config.c](https://github.com/redis/redis/blob/unstable/src/config.c) - primary: "LRU, LFU and minimal TTL algorithms are not precise algorithms but approximated algorithms (in order to save memory)"; "The default of 5 produces good enough results. 10 Approximates very closely true LRU but costs more CPU. 3 is faster but not very accurate. The maximum value that can be set is 64." `createIntConfig("maxmemory-samples", ..., 1, 64, ..., 5, ...)`.
- Redis docs, [Key eviction](https://github.com/redis/docs/blob/main/content/develop/reference/eviction/index.md) - primary: "The reason Redis does not use a true LRU implementation is because it costs more memory"; "From Redis 3.0 onwards, the algorithm also tracks a pool of good candidates for eviction"; with 10 samples "the approximation is very close to the theoretical performance"; "using a power law access pattern, the difference between true LRU and Redis approximation were minimal or non-existent." LFU from 4.0 uses a Morris counter that saturates around one million requests and decays every minute by default.

**Key primary-source detail:** `lookupKey()` refuses to update even the 24-bit access stamp while a BGSAVE/AOF-rewrite child exists, with the comment "this will trigger a copy on write madness." Writing 3 bytes into an object on a read dirties the whole 4 KB page that holds it, and after fork() every dirtied page gets physically copied. If one tiny stamp on reads is already too expensive during a snapshot, a doubly linked list that rewrites the node plus its two neighbours plus the head on every GET is a non-starter.

Derived (author's arithmetic, not a Redis-published number): a true LRU list needs prev/next pointers, 2 x 8 = 16 bytes per key on 64-bit. The 7.2 `redisObject` header is itself 16 bytes (32 bits of type/encoding/lru + 4-byte refcount + 8-byte pointer), so exact LRU would double the per-object header; at 100M keys that is ~1.6 GB of pointers. 2^24 seconds = 16,777,216 s, about 194 days, which is why `estimateObjectIdleTime()` has a wrap-around branch. Nothing in the post is a reported incident.

---

## LinkedIn Post

Set maxmemory-policy to allkeys-lru and you'd assume Redis evicts the least recently used key.

It doesn't. And it was right not to.

Real LRU is a doubly linked list. Every read unlinks the key and moves it to the head. That's two pointers per key, 16 bytes on a 64-bit box. A Redis 7.2 object header is 16 bytes total. Exact LRU would double the header of every key you store, and turn every GET into writes across three or four nodes scattered around the heap.

So Redis keeps 24 bits instead. The lru field in each object is a last-access stamp at 1-second resolution (LRU_CLOCK_RESOLUTION 1000). It wraps every 2^24 seconds, about 194 days, and the idle-time function has a branch for that.

When memory is full, evict.c samples maxmemory-samples keys at random. Default 5, max 64. Since Redis 3.0 the samples feed a 16-entry pool of the oldest candidates seen so far, so good candidates carry over between evictions. Redis evicts the worst one in the pool. The pool doesn't even remove keys that were deleted meanwhile. It just skips them.

The Redis docs say the reason plainly: true LRU "costs more memory." Their test shows 10 samples landing very close to theoretical LRU, and under power-law access the gap was "minimal or non-existent."

The best evidence is in db.c. On a read, lookupKey() updates the 24-bit stamp, unless a BGSAVE or AOF rewrite child is running. Then it skips it, because writing to the object would "trigger a copy on write madness." After fork(), touching 3 bytes copies a 4 KB page. If one tiny stamp is too expensive during a snapshot, a linked list that relinks nodes on every read never had a chance.

Redis 4.0's LFU mode reuses the same 24 bits: 16 bits of minutes plus an 8-bit probabilistic counter that saturates near a million hits. No extra bytes.

We treat "approximate" as a compromise. Here it's the design. Exact LRU is accurate about something that matters less, recency rank among cold keys, and pays for it in memory and writes on every key. If the hit rate looks off, raise maxmemory-samples to 10 and measure. Don't reach for exactness.

#Redis #Caching #SystemDesign #DistributedSystems

---

## Twitter Version

allkeys-lru in Redis isn't LRU.

True LRU = linked list. 2 pointers/key = 16 bytes. The whole Redis 7.2 object header is 16 bytes.

Redis keeps a 24-bit last-access stamp, samples 5 random keys, keeps a 16-entry pool of the oldest, evicts the worst.

It even skips updating that stamp on reads during BGSAVE. Source comment: "copy on write madness."

Want closer to LRU? maxmemory-samples 10. Not a linked list.

---

## Diagram

See `2026-11-17-redis-approximate-lru-sampling-eviction-pool.excalidraw` (side-by-side architecture, contrarian layout. Left, "What you'd build": a doubly linked list of keys with prev/next pointers, labeled "+16 B per key, 3-4 writes on every GET". Right, "What Redis built": an object header with the 24-bit lru field highlighted, an arrow from "sample 5 random keys" into a 16-slot eviction pool sorted by idle time, and "evict worst". A bottom callout quotes the db.c line "copy on write madness" with "BGSAVE child alive: skip stamp update". Palette: charcoal + amber + slate blue, no red/green.)
