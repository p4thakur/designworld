# Every Index Is a Write Tax

The query got faster. Write throughput dropped by 60%. Those two outcomes came from the same schema change — three indexes added to support a new analytics dashboard. The queries the dashboard ran were real, the indexes helped them, and the write path quietly collapsed under the load.

This is the index tradeoff that surfaces after deployment, not before.

---

## What engineers know about indexes

Indexes speed up reads. Add a B-tree index on a column and SELECT queries that filter or sort on it go from full table scans to targeted lookups. The tradeoff most engineers reach for is disk space — the index consumes storage proportional to the indexed data.

That framing is accurate. It's also incomplete. It describes the read benefit and the storage cost. It skips the write cost entirely.

---

## What actually happens on every write

When you execute `INSERT INTO events (user_id, event_type, created_at) VALUES (...)`, Postgres doesn't do one write. It writes the row to the heap, then updates every index on that table.

Each B-tree index is a separate data structure. An index on `(user_id)` is its own set of pages. An index on `(created_at)` is another. An index on `(event_type, user_id)` is another still. Each one must be traversed to find the correct insertion point, then updated.

That's N+1 write operations for a table with N indexes. A table with 5 indexes: every write is actually 6 operations.

The random I/O problem compounds this. Heap writes are largely sequential — new rows append near the end of the heap. B-tree index writes are random. The correct position in the tree depends on the value being indexed: a row with `user_id = 9847361` goes in a completely different B-tree position than `user_id = 3`. That randomness means the disk (or SSD page cache) gets hit in unpredictable locations on every write.

Random I/O is significantly more expensive than sequential I/O — on spinning disks by an order of magnitude, on SSDs by a meaningful fraction due to write amplification and page cache pressure.

At low write volume this is invisible. The I/O subsystem absorbs it. At high write volume — sustained 10,000 inserts per second — index maintenance starts competing with the write path for I/O bandwidth and buffer pool pages.

On a high-frequency event table doing roughly 15M rows per day (average ~175 writes/second, peak around 8,000/second), three indexes added for analytics queries dropped peak write throughput from 8,000 to 3,200 inserts per second. The queries ran faster. The writes got strangled.

### Composite and expression indexes

Simple indexes are the base case. Composite and expression indexes are more expensive.

A simple index on `(created_at)` requires Postgres to insert one value into one B-tree. A composite index on `(event_type, user_id, created_at)` requires Postgres to:
1. Extract all three column values from the new row
2. Construct the composite key in the defined sort order
3. Traverse the composite B-tree to the correct position
4. Write the new entry

An expression index like `lower(email)` requires Postgres to evaluate the expression on every write before it can even begin the B-tree traversal. Not on first insert. On every single insert, every update to the `email` column, every delete of a row containing that value.

This evaluation happens in the write path, not the read path. The query planner benefits from it on reads. The write path pays for it every time.

---

## How to detect it

Write throughput degradation from index overhead shows up in a few specific places.

**pg_stat_user_tables** — compare `n_tup_ins`, `n_tup_upd`, `n_tup_del` against your expected write rate. If the table is receiving writes at the application level but these counters grow slower than expected, something in the write path is the bottleneck.

**pg_stat_user_indexes** — this is the most actionable view. The `idx_scan` column shows how many times each index has been used for a query since the last stats reset. An index with `idx_scan = 0` over the past 90 days is a write tax with zero corresponding read benefit.

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan < 50
  AND schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
```

This query returns the largest low-usage indexes. These are the candidates to drop first.

**EXPLAIN (ANALYZE, BUFFERS) on your INSERT** — shows buffer hits and misses for the write path. High buffer misses on index pages signal index maintenance overhead under real load. Run this against a write-heavy workload, not an idle database.

**Application p99 write latency** — if your p99 write latency climbs while p50 stays flat, index maintenance under burst load is a common cause. B-tree rebalancing under write bursts isn't uniformly distributed — when a node splits, that write takes longer than average. At high percentiles, these splits become visible.

**Postgres 15+ pg_stat_io** — breaks down I/O by object type. You can see index write I/O separately from heap write I/O. If index writes are consuming a disproportionate share of write I/O, that's the signal.

---

## How to fix it

### Step 1: Drop unused indexes

Find them with the query above. An index with `idx_scan < 50` over a representative period (at minimum, since the last deploy) is a candidate. An index with `idx_scan = 0` over 90 days is almost certainly safe to drop.

Dropping an index is immediate and reversible. Postgres acquires a brief lock to drop the index entry from the catalog, but it doesn't block reads or writes during the drop itself. You can always recreate it.

If you're uncertain about a specific index, use `CREATE INDEX CONCURRENTLY` in reverse — drop with `DROP INDEX CONCURRENTLY` so even the brief catalog lock is avoided.

### Step 2: Replace broad indexes with partial indexes

If you have an index that serves a query with a highly selective filter, a partial index covers the same queries at a fraction of the write cost.

```sql
-- This indexes every row:
CREATE INDEX idx_jobs_status ON jobs(status);

-- This indexes only the rows the query actually touches:
-- (if 98% of jobs have status = 'completed', the partial index is 2% the size)
CREATE INDEX idx_jobs_status_pending ON jobs(status)
WHERE status IN ('pending', 'running');
```

The partial index maintains only the rows matching the WHERE clause. Every write to a completed row incurs zero index maintenance cost. Every write to a pending or running row still pays — but that's the minority of writes.

This is a meaningful optimization for status columns, soft-delete flags, or any column with extreme skew.

### Step 3: Separate write and read models for high-throughput tables

For tables under extreme write pressure, the most surgical fix is model separation: write to a lean table with minimal indexes, replicate or aggregate to a read-optimized table that carries the full index set.

This is the core idea behind CQRS, but it applies at the table level without requiring an architectural overhaul. A materialized view refreshed on a schedule, or a replica with additional indexes, gives the analytics queries what they need without taxing the write path.

The tradeoff: you're now maintaining two representations of the same data. The read table has eventual consistency. That's a real cost — worth it for extreme write loads, probably not worth it for moderate ones.

### Step 4: Batch writes

If the application is issuing individual inserts, switching to bulk inserts amortizes the per-row overhead:

```sql
-- Instead of this (N separate transactions, N separate index updates each):
INSERT INTO events VALUES ($1, $2, $3);
INSERT INTO events VALUES ($4, $5, $6);
-- ... repeated N times

-- This (one transaction, index updates batched internally):
INSERT INTO events VALUES
  ($1, $2, $3),
  ($4, $5, $6),
  ($7, $8, $9);
```

Bulk inserts allow Postgres to sort the incoming data by index key before writing, converting some random index writes to sequential ones. The benefit scales with batch size — 100-row batches are meaningfully cheaper per row than individual inserts.

---

## The tradeoff

Dropping indexes hurts queries. There's no path around this.

The question is whether each index is being used — and whether the write cost is worth the read benefit. The `pg_stat_user_indexes` data answers the first question. The second requires understanding the read pattern: an index that serves 10 queries per day on a table that takes 10,000 writes per second has an extremely unfavorable cost-benefit ratio.

For analytics queries on live transactional tables, the right answer is usually to move the analytics workload elsewhere — a read replica, a data warehouse, a Postgres database dedicated to reads with a different index configuration. That's more infrastructure to maintain. It's also honest about the tradeoff: you're not eliminating the cost, you're moving it to where it belongs.

Partial indexes can recover 80–90% of query benefit at a small fraction of write cost — but only when the query has a selective predicate. Not every index can be made partial. A query that scans the entire table can't benefit from a partial index by definition.

Covering indexes (using the `INCLUDE` clause in Postgres 11+) can sometimes replace multiple narrow indexes with one wider one. If three queries each need a different non-indexed column alongside the same indexed column, a single covering index might replace three separate indexes — cutting index maintenance by two-thirds for that query pattern.

None of these are free. They're just explicit about what the cost is instead of hiding it inside the write path.

---

## The thing to remember

Every index is a write tax. The query optimizer shows you the read benefit clearly — it's right there in EXPLAIN output. The write cost is invisible until write throughput is the bottleneck, by which point it's already a production problem.

Before adding an index to a write-heavy table, the question isn't "will this help the query?" — it's "what does the write path look like after?" Check `pg_stat_user_indexes` for unused indexes first. Drop those. Add the new one only when the write path can afford it.
