---
date: 2026-11-05
company: Memcached
topic: Slab allocator - pages were assigned to a size class forever, so a shift in object sizes left memory stranded in the wrong class; slab rebalancing and the automover were added to undo that.
category: caching
post_type: confessional
opening_style: cold_fact
slug: memcached-slab-pages-never-moved-calcification
---

## Sources

- GitHub wiki, [memcached UserInternals](https://github.com/memcached/memcached/wiki/UserInternals) - primary: 1 MB pages, "Once a page is assigned to a class, it is never moved", per-class LRU, class 1 = 80-byte chunks / 13,107 per page, class 2 = 104 bytes / 10,082.
- GitHub wiki, [Release notes 1.4.11](https://github.com/memcached/memcached/wiki/ReleaseNotes1411) - primary: introduces slab page reassignment (beta), 100-byte chunks cannot serve 200-byte requests, moving a page evicts every item in the 1 MB page, automove "slow and conservative".
- GitHub wiki, [Release notes 1.5.0](https://github.com/memcached/memcached/wiki/ReleaseNotes150) - primary: "Automated slab rebalancing. Avoiding slab stagnation as objects change size over time."; segmented LRU HOT/WARM/COLD.
- GitHub, [doc/protocol.txt](https://raw.githubusercontent.com/memcached/memcached/master/doc/protocol.txt) - primary: `slabs automove` modes 0/1/2; mode 1 returns pages to a global pool when a class has more than 2 pages of free chunks; mode 2 moves a page on every eviction.

**Note on sourcing:** the opening scene is an illustrative composite, not a report of a specific company incident. The word "calcification" does not appear in the official docs; it is community shorthand and the post avoids attributing it to the project.

**Key primary-source detail:** moving a slab page is not free - every item in that 1 MB page is evicted.

---

## LinkedIn Post

An early memcached page in the project wiki states a rule in one blunt sentence: "Once a page is assigned to a class, it is never moved."

That sentence explains a class of cache problems that looked like bad luck.

Here is the design. Memcached carves memory into 1 MB pages. Each page is assigned to a slab class and cut into fixed-size chunks. Class 1 uses 80-byte chunks, 13,107 per page. Class 2 uses 104-byte chunks, 10,082 per page. Every class has its own LRU. When a class runs out of free chunks and there are no free pages left, it evicts from its own tail, no matter how cold the neighboring classes are.

It was a good trade. No per-item malloc, no fragmentation, O(1) allocation. For a workload with stable object sizes, it is close to ideal.

Then the workload changes. A feature ships and the typical value grows from 100 bytes to 200. The cache has been up for weeks and every page already belongs to the 100-byte class. In the project's own words from the 1.4.11 release notes: memcached "could not use the 100 byte chunks to satisfy the 200 byte requests." The new items fight over whatever little memory the 200-byte class owns, evict each other constantly, and the hit rate drops while total memory shows as full and healthy.

Nobody did anything wrong. The first design optimized for the steady state, and the steady state moved.

The fix took years and had a cost. 1.4.11 added slab page reassignment, marked beta, with an automover described as "slow and conservative." Moving a page is not free: every item in that 1 MB page is evicted. Version 1.5.0 listed automated rebalancing to avoid "slab stagnation as objects change size over time," and added a segmented HOT/WARM/COLD LRU. In the protocol docs, automove mode 1 returns pages to a global pool when a class holds more than 2 pages of free chunks. Mode 2 moves a page on every eviction.

The honest reflection: an allocator that never gives memory back is simple. Simple is only correct while the data stays the same shape.

#Memcached #Caching #SystemDesign #BackendEngineering

---

## Twitter Version

Early memcached docs had one blunt line: "Once a page is assigned to a class, it is never moved."

Memory is split into 1 MB pages, each cut into fixed chunks (80 B x 13,107 in class 1; 104 B x 10,082 in class 2). Each class has its own LRU and evicts only from itself.

Great while object sizes are stable. Then values grow from 100 B to 200 B and every page already belongs to the 100 B class. Cache is full, hit rate drops.

The fix (1.4.11 reassign, 1.5.0 auto-rebalancing) costs something: moving a page evicts every item in that 1 MB.

Simple allocators are correct only while the data keeps its shape.

---

## Diagram

See `2026-11-05-memcached-slab-pages-never-moved-calcification.excalidraw` (timeline: stable sizes, shift, stranded pages, rebalancer).
