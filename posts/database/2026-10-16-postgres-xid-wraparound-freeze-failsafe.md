---
date: 2026-10-16
company: PostgreSQL
topic: Transaction ID wraparound: a 32-bit counter, freezing, and the safeguards that stop the database before data goes invisible.
category: database
post_type: narrative
opening_style: mid_scene
slug: postgres-xid-wraparound-freeze-failsafe
---

## Sources

- PostgreSQL docs, [Routine Vacuuming: Preventing Transaction ID Wraparound Failures](https://github.com/postgres/postgres/blob/master/doc/src/sgml/maintenance.sgml) - primary: 32-bit XIDs, modulo-2^32 comparison, FrozenTransactionId, 100M warning, 3M hard stop, recovery steps.
- PostgreSQL docs, [Server configuration (config.sgml)](https://github.com/postgres/postgres/blob/master/doc/src/sgml/config.sgml) - autovacuum_freeze_max_age default of 200M and why it is low (pg_xact cleanup), vacuum_failsafe_age default of 1.6B and what it skips.

**Note on sourcing:** only GitHub-hosted sources were reachable from this environment; every number is from the docs above, none from memory.

**Key primary-source detail:** the 3-million-transaction safety margin exists specifically so an admin can enter single-user mode and TRUNCATE or DROP tables instead of vacuuming them. VACUUM FULL and VACUUM FREEZE are both the wrong fix during recovery.

---

## LinkedIn Post

The error message says the database is not accepting commands. The data is fine. Every row is still on disk. Postgres just stopped writing on purpose, with 3 million transactions to spare before it would have started hiding your data from you.

That is transaction ID wraparound, and the Postgres docs describe it bluntly: "catastrophic data loss. (Actually the data is still there, but that's cold comfort if you cannot get at it.)"

The design is old and sound. Every row version carries the 32-bit ID of the transaction that created it. Visibility is a comparison: is that ID in my past or my future? IDs are compared modulo 2^32, so the space is a circle. For any ID, two billion are older and two billion are newer. A row created at XID 100 looks like history for two billion transactions. At transaction two billion and one it looks like the future, and the row vanishes from every query.

The fix is freezing. VACUUM marks old rows with a flag meaning "inserted so long ago it is visible to everyone, forever," and the circle stops mattering for them. Before 9.4 this overwrote xmin with a special FrozenTransactionId. Newer versions set a flag bit and keep the original xmin around for forensics.

So the real question is how many tripwires sit between a busy table and the cliff. The docs and config reference give four. At 200 million transactions of age, autovacuum_freeze_max_age forces a vacuum even if autovacuum is switched off. The default is deliberately low because vacuum also lets Postgres delete old pg_xact files. At 1.6 billion, vacuum_failsafe_age fires: cost-based delay is dropped, index vacuuming is skipped, and the ring buffer is disabled so vacuum can use all of shared_buffers. At 100 million left, warnings start. At 3 million left, new XID assignment is refused and only read-only transactions can start.

The recovery steps are where people hurt themselves. Do not run VACUUM FULL, which needs an XID. Do not run VACUUM FREEZE, which does more than the minimum. Look first for what is holding the horizon back: forgotten prepared transactions, long-running open transactions, and stale replication slots pinned by replicas that no longer exist.

Older advice said to stop the postmaster and vacuum in single-user mode. The docs now say avoid it, since it disables the safeguards. The 3M margin exists for one case: dropping or truncating tables you would rather not vacuum.

None of this is a bug being worked around. A 32-bit counter was a bet that someone would always be vacuuming. The safeguards are what happens when that bet loses.

#PostgreSQL #Databases #DistributedSystems #SystemDesign

---

## Twitter Version

Postgres will deliberately stop accepting writes with 3 million transactions to spare. The data is fine. The alternative is worse.

XIDs are 32-bit and compared modulo 2^32: two billion older, two billion newer. A row at XID 100 looks like history, until transaction two billion and one, when it looks like the future and disappears from every query.

VACUUM prevents this by freezing old rows. The tripwires: 200M age forces autovacuum even if it's off. 1.6B triggers failsafe mode, skipping index vacuum. 100M left: warnings. 3M left: read-only.

Recovery trap: VACUUM FULL needs an XID, VACUUM FREEZE does extra work. Find the stale replication slot or open transaction pinning the horizon instead.

---

## Diagram

See `2026-10-16-postgres-xid-wraparound-freeze-failsafe.excalidraw` (age ruler from 0 to ~2.1B XIDs marking the four tripwires).
