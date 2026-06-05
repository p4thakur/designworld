# Twitter/X Thread — Topic #1: Index Write Cost

---

**1/**
Write throughput dropped 60% after a schema change.
The change added three indexes.

---

**2/**
Every INSERT on a table maintains every index.

5 indexes = 6 write operations.
Not sequential — random I/O.
B-tree position depends on the value, not the write order.

---

**3/**
High-frequency event table. ~15M rows/day.
3 indexes added for analytics queries.

8,000 → 3,200 inserts/second.

Queries got faster.
Writes got strangled.

---

**4/**
Every index is a write tax.

The query optimizer sees the benefit.
The write path pays every time.

---

**5/**
How to find the ones not pulling their weight:

pg_stat_user_indexes.idx_scan = 0 over 90 days → drop it.

Partial indexes get 80% of query speed at 10% of write cost.

The question isn't "does this help the query."
It's "what does the write path look like after."
