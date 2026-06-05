# LinkedIn Post — Topic #1: Adding more indexes slowed down the writes
# Type A (Hidden Cost) | Hook: surprising_outcome | ~1,487 chars

---

The write throughput dropped by 60% after the schema change. The change added three indexes.

Indexes are framed as a query tool. The cost is usually storage — disk space, not performance. That framing misses half the picture.

Every INSERT, UPDATE, and DELETE maintains every index on that table. A table with 5 indexes: every write is 6 operations. The row itself, plus one B-tree update per index. That maintenance is random I/O — indexes live in their own pages, scattered across the heap.

At low write volume this disappears. At high write volume — 10,000 inserts per second — index maintenance starts competing with the write path itself.

On a high-frequency event table doing ~15M rows per day, three indexes added for a new analytics query dropped peak write throughput from 8,000 to 3,200 inserts per second. The queries ran faster. The writes got strangled.

Composite and expression indexes compound this. They require evaluation before the B-tree lookup. Sort the key, evaluate the expression, find the position, write. Every single time.

Every index is a write tax. The query optimizer sees the benefit. The write path pays every time.

Before adding an index to a write-heavy table: check pg_stat_user_indexes.idx_scan. Any index with zero scans in the last 90 days is a tax with no corresponding benefit. Drop it. Partial indexes recover most query speed at a fraction of the write cost.

The question isn't whether the index helps the query. It's what the write path looks like after.
