---
date: 2026-10-13
company: Apache Kafka (LinkedIn origin)
topic: Kafka refuses to keep its own cache: the log lives in the OS page cache and sendfile skips user space.
category: messaging
post_type: contrarian
opening_style: specific_number_doesnt_add_up
slug: kafka-pagecache-sendfile-no-inprocess-cache
---

## Sources

- Apache Kafka, [Design: Persistence, Efficiency](https://github.com/apache/kafka/blob/trunk/docs/design/design.md) - primary: 600MB/sec linear vs 100kB/sec random writes, page cache vs in-process cache (28-30GB on 32GB, 10GB cache = 10 min rebuild), BTree seek cost, four copies and two syscalls vs sendfile, "no read activity on the disks".
- ACM Queue, [The Pathologies of Big Data / "Sequential access can beat random memory access"](https://queue.acm.org/detail.cfm?id=1563874) - cited by the Kafka doc, not re-read here.

**Note on sourcing:** only the Kafka design doc in the Apache repo was reachable from this environment (company blogs were blocked). All numbers come from that doc; no figures from memory.

**Key primary-source detail:** sendfile is not used when SSL is enabled, because TLS runs in user space. The famous zero-copy path quietly disappears once you encrypt.

---

## LinkedIn Post

A disk that writes 600MB/sec and also 100kB/sec. Both numbers are in Kafka's design doc, for the same array. The difference is 6,000x, and it is the whole reason Kafka looks the way it does.

The 600MB/sec is linear writes. The 100kB/sec is random ones. Most messaging systems of the era kept a per-consumer queue plus a BTree for message metadata, which is the versatile, textbook choice. But the doc points out the catch: BTree operations are O(log N), and on disk that is not "basically constant". Seeks cost about 10 ms each, and a disk does one at a time.

So Kafka went the other way. A log is a file. Append at the end, read sequentially. No tree.

Then the less obvious move: no cache of its own either. Everyone's instinct is to keep hot data in process memory. The doc argues that is storing everything twice, because the OS already puts it in the page cache. And on the JVM, object overhead often doubles the data size, and GC gets slower as the heap grows.

So Kafka writes straight to the filesystem and lets the kernel's page cache do the caching. That gives up to 28-30GB of cache on a 32GB machine with no GC penalty. The doc also notes a 10GB in-process cache can take 10 minutes to rebuild after a restart. The page cache stays warm.

Serving reads follows the same logic. The normal file-to-socket path is four copies and two system calls. With sendfile, data goes from page cache to the NIC. On a cluster where consumers are mostly caught up, the doc says you will see no read activity on the disks at all.

One detail that rarely makes the summaries: sendfile is not used when SSL is enabled. TLS libraries work in user space, so the zero-copy path is gone the moment you encrypt.

The design isn't clever because it adds machinery. It's clever because it removes the cache, the tree, and the copies, and lets the operating system do jobs it already does well.

#Kafka #SystemDesign #DistributedSystems #BackendEngineering

---

## Twitter Version

Kafka's design doc has two numbers for the same disk array: 600MB/sec linear writes, 100kB/sec random writes. 6,000x apart.

So Kafka's log is just a file. Append, read sequentially. No BTree, because a BTree on disk means 10 ms seeks, one at a time.

Stranger decision: no cache of its own. An in-process cache stores data twice (the OS caches it anyway), and on the JVM object overhead can double it. Kafka leans on the page cache: up to 28-30GB on a 32GB box, still warm after a restart. A 10GB heap cache can take 10 minutes to rebuild.

Reads use sendfile: page cache straight to the NIC instead of four copies and two syscalls. Caught-up consumers cause no disk reads at all.

Catch: enable SSL and sendfile is off. TLS lives in user space.

---

## Diagram

See `2026-10-13-kafka-pagecache-sendfile-no-inprocess-cache.excalidraw` (side-by-side: the obvious path with four copies vs the sendfile path).
