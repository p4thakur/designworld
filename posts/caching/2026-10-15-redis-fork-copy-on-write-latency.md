---
date: 2026-10-15
company: Redis
topic: Redis persistence by fork(): page-table copy cost, Xen fork times, and transparent huge pages turning copy-on-write into a memory spike.
category: caching
post_type: confessional
opening_style: shared_pain_point
slug: redis-fork-copy-on-write-page-table-latency
---

## Sources

- Redis, [Diagnosing latency issues](https://github.com/redis/redis-doc/blob/master/docs/management/optimization/latency.md) - primary: 24 GB page table math, fork-time table per platform, transparent huge pages, appendfsync everysec behavior.
- Redis, [Persistence](https://github.com/redis/redis-doc/blob/master/docs/management/persistence.md) - primary: RDB forks a child so the parent never does disk I/O; fork can stop serving clients "for some milliseconds or even for one second".

**Note on sourcing:** only GitHub-hosted docs were reachable from this environment (Notion's and other company blogs failed DNS), so the post is built from the Redis docs. Every number below is from those two pages.

**Key primary-source detail:** the doc measures fork cost per GB and shows an old EC2 Xen instance at 239.3 ms/GB versus about 9-13 ms/GB on physical hardware.

---

## LinkedIn Post

Every Redis team eventually meets the same ghost: p99 looks fine, then once in a while the whole instance freezes for a beat, and nothing in the slowlog explains it.

Often the culprit is the feature that makes Redis safe. To write an RDB snapshot or rewrite the AOF, Redis calls fork(). The child does all the disk work, which is elegant: the parent never touches the disk. The docs say as much.

The catch is that fork() itself runs in the main thread. Redis' latency docs walk through the arithmetic. Linux splits memory into 4 kB pages, and every process carries a page table with an 8-byte pointer per page. A 24 GB instance needs 24 GB / 4 kB x 8 = 48 MB of page table, and fork has to allocate and copy all of it while clients wait.

How long that takes depends on where you run. The docs list fork times from a real BGSAVE: 6.9 GB forked in 62 ms on a physical Xeon (9 ms/GB) and 6.0 GB in 77 ms on VMware. On old EC2 Xen instances, 6.1 GB took 1,460 ms, about 239 ms per GB. On a Linode Xen VM, 0.9 GB took 382 ms. The docs call it a one-to-two orders of magnitude hit and just tell EC2 users to move to modern HVM instances.

Then there is the second half of the bill. After fork, parent and child share pages copy-on-write. With transparent huge pages on, a few event loop runs can touch a few thousand huge pages and trigger copy-on-write of almost the whole process memory. Big latency and big memory usage, together. The fix is one line: echo never into the THP setting.

None of this makes fork a bad idea. It was a smart way to get a consistent snapshot of a single-threaded in-memory store without locks. But the design quietly ties your tail latency to the kernel, the hypervisor and the page size, three things nobody puts on the Redis dashboard.

The cheapest persistence is the one whose cost you can actually see.

#Redis #SystemDesign #Linux #Performance

---

## Twitter Version

Redis p99 fine, then a random freeze that the slowlog can't explain? Check fork().

RDB snapshots and AOF rewrites fork a child. Elegant: the parent never does disk I/O. But fork runs in the main thread and copies the page table: 24 GB / 4 kB x 8 B = 48 MB, while clients wait.

Redis' own docs list fork times: 6.9 GB in 62 ms on bare metal (9 ms/GB). Old EC2 Xen: 6.1 GB in 1,460 ms (239 ms/GB).

And with transparent huge pages on, copy-on-write can duplicate almost all memory after the fork.

Smart design, but your tail latency now depends on the hypervisor and page size.

---

## Diagram

See `2026-10-15-redis-fork-copy-on-write-latency.excalidraw` (bar chart of fork ms/GB per platform plus the 48 MB page table callout).
