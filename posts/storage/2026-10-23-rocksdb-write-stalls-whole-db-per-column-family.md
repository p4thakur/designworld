---
date: 2026-10-23
company: RocksDB
topic: Write stalls - three triggers evaluated per column family, one penalty applied to the whole database.
category: storage
post_type: confessional
opening_style: cold_fact
slug: rocksdb-write-stalls-whole-db-per-column-family
---

## Sources

- RocksDB wiki, [Write Stalls](https://github.com/facebook/rocksdb/wiki/Write-Stalls) - primary: the three stall causes (immutable memtables, level-0 file count, pending compaction bytes), slowdown vs stop, `delayed_write_rate`, the per-column-family triggers with DB-wide stall, `no_slowdown`.
- RocksDB wiki, [Leveled Compaction](https://github.com/facebook/rocksdb/wiki/Leveled-Compaction) - primary: L0 files overlap so all are picked for L0->L1; leveled write amplification "often larger than 10".
- RocksDB wiki, [RocksDB Tuning Guide](https://github.com/facebook/rocksdb/wiki/RocksDB-Tuning-Guide) - primary: example trigger settings.

**Note on sourcing:** only GitHub-hosted docs were reachable from this environment, so the wiki is the sole source. The log lines and trigger values quoted are the wiki's own examples, not defaults.

**Key primary-source detail:** the wiki says the slowdown/stop triggers and pending-compaction limits are per column family, but the stall applies to the whole DB. One busy column family throttles all of them.

---

## LinkedIn Post

A RocksDB write can sleep for about 1ms before it is even attempted, and the database is doing it on purpose.

That is a write stall, and it is a confession built into the engine: the storage layer admits it cannot always absorb what you send it.

The reason is the shape of an LSM tree. Writes land in a memtable, get flushed to level-0 files, and background compaction then merges those into deeper levels. L0 files overlap, so compaction normally has to pick up all of them at once. The wiki notes leveled write amplification is often larger than 10, so every byte you write can mean ten or more bytes of compaction work later.

If writes outrun that work, the wiki says the database would balloon in space amplification and read amplification. So RocksDB applies backpressure instead, from three signals: too many immutable memtables waiting to flush, too many level-0 files, too many estimated pending compaction bytes.

Each signal has two stages. Past the soft limit, writes are slowed to `delayed_write_rate`, each one sleeping around 1ms. Past the hard limit, writes stop and the calling thread can block indefinitely.

Here is the part that bites. The triggers are per column family. The stall is not. If one column family falls behind on compaction, the whole DB is stalled, including the column families that were perfectly healthy.

The wiki does not say why, so this is my reading: column families share one write path, so the engine protects the whole DB. From the outside it looks like an unrelated table getting slow for no reason.

The honest options are all workarounds. Add compaction threads. Enlarge the memtable to cut write amplification. Mark non-critical writes low priority. Or set `no_slowdown` so the stall returns `Status::Incomplete()` instead of blocking, which at least turns a mystery latency spike into an error you can handle.

Backpressure is not a bug in an LSM tree. It is the bill for deferring work, arriving all at once.

#RocksDB #SystemDesign #Storage #Backend

---

## Twitter Version

A RocksDB write can sleep ~1ms before it even runs. On purpose.

LSM trees defer work. Writes hit a memtable, flush to L0, compaction merges later. Leveled write amp is often >10.

When compaction falls behind, RocksDB pushes back on three signals: pending memtables, L0 file count, pending compaction bytes. Soft limit = slow. Hard limit = stop.

The catch: triggers are per column family. The stall is DB-wide. One lagging CF slows all of them.

Escape hatch: `no_slowdown` returns Incomplete() instead of blocking.

---

## Diagram

See `2026-10-23-rocksdb-write-stalls-whole-db-per-column-family.excalidraw` (three-signal timeline from healthy to slowdown to stop, with the per-CF trigger / whole-DB stall callout).
