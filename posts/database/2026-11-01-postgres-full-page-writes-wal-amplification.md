---
date: 2026-11-01
company: PostgreSQL
topic: full_page_writes - the first modification of each page after a checkpoint logs the entire 8kB page to WAL, so checkpoint frequency trades recovery time against WAL volume.
category: database
post_type: confessional
opening_style: shared_pain_point
slug: postgres-full-page-writes-wal-amplification
---

## Sources

- GitHub, [postgres/postgres - doc/src/sgml/config.sgml](https://github.com/postgres/postgres/blob/master/doc/src/sgml/config.sgml) - primary: full_page_writes, wal_compression (off by default; zstd/lz4/pglz), checkpoint_timeout (default 5min).
- GitHub, [postgres/postgres - doc/src/sgml/wal.sgml](https://github.com/postgres/postgres/blob/master/doc/src/sgml/wal.sgml) - primary: torn writes across 512-byte sectors, ZFS example, BBU caveat, and the checkpoint-interval vs WAL-volume trade-off.

**Key primary-source detail:** wal.sgml itself states that a smaller checkpoint interval increases WAL volume, "partially negating the goal of using a smaller interval"; and that BBU controllers do not prevent partial page writes unless they guarantee full 8kB writes.

**Note on sourcing:** only GitHub-hosted docs were reachable from this environment. No measured WAL-amplification numbers are cited; the "thousand pages = thousand 8kB images" line is arithmetic on the documented behavior.

---

## LinkedIn Post

Postgres writes your 8kB page to the WAL again after every checkpoint, even if you only changed one row. That is not a bug. It is the price of a crash that can tear a page in half.

The reason is in the docs. Postgres pages are 8kB, but disks often write in 512-byte sectors. If the OS crashes mid-write, some sectors are new and some are old. The page on disk is a mix. The row-level change records in WAL cannot repair that, because they describe a change to a page that no longer exists in a known state.

So when full_page_writes is on, the default, Postgres logs the entire page the first time it is modified after a checkpoint. Replay always starts at a checkpoint, so one full image per page per checkpoint is enough to restore it.

That design is correct. It is also why a database doing small updates can produce far more WAL than the changes themselves would suggest. Touch a thousand different pages right after a checkpoint and you log a thousand 8kB images, whatever the row sizes were.

The tuning advice then pulls in two directions. Shorter checkpoint_timeout (default 5 minutes) means faster crash recovery. But the wal.sgml docs say it directly: a smaller checkpoint interval increases WAL volume, partially negating the goal and causing more disk I/O. Every checkpoint resets the "first touch" clock for every page.

Two real exits exist. wal_compression, off by default, compresses those page images with zstd, lz4 or pglz, and the docs say it does so without raising corruption risk, at the cost of CPU on write and replay. Or turn full_page_writes off, which the docs say is safe only where the filesystem prevents partial writes, ZFS being their example. They compare the risk to turning off fsync.

It is tempting to read the default as the conservative choice nobody questioned. I read it differently. It is a decision to pay a steady, visible cost in WAL volume so that a rare, invisible failure never corrupts data silently.

Most of us only meet it when replication lag or archive storage gets expensive. By then the question is not whether the setting is wrong. It is whether the failure it prevents can happen on your hardware.

#PostgreSQL #WAL #Databases #SystemDesign

---

## Twitter Version

Postgres logs a full 8kB page to WAL the first time it touches that page after each checkpoint. Even for a one-row update.

Why: disks write 512-byte sectors, pages are 8kB. A crash mid-write leaves a torn page that row-level WAL records can't repair. So the whole image goes in first.

The side effect: a shorter checkpoint_timeout (default 5min) speeds recovery but resets the "first touch" for every page, so WAL volume goes up. The docs say so themselves.

Exits: wal_compression (off by default) or full_page_writes=off if your filesystem prevents partial writes. The docs compare that risk to turning off fsync.

The default isn't timid. It buys protection against a failure you will never see, with a cost you see daily.

---

## Diagram

See `2026-11-01-postgres-full-page-writes-wal-amplification.excalidraw` (timeline across two checkpoints: first touch per page logs 8kB, later touches log small records).
