---
date: 2026-10-25
company: PostgreSQL
topic: The xmin horizon - one idle-in-transaction session, replication slot or standby feedback pins dead-row cleanup for every table in the database, and autovacuum tuning cannot fix it.
category: database
post_type: contrarian
opening_style: challenge_assumption
slug: postgres-xmin-horizon-old-transaction-blocks-vacuum
---

## Sources

- PostgreSQL source, [src/backend/storage/ipc/procarray.c](https://github.com/postgres/postgres/blob/master/src/backend/storage/ipc/procarray.c) - primary: `ComputeXidHorizons()` and `ComputeXidHorizonsResult`. Each backend contributes `Min(xmin, xid)`; backends in `PROC_IN_VACUUM` or `PROC_IN_LOGICAL_DECODING` are skipped; `shared_oldest_nonremovable` considers all databases, `data_oldest_nonremovable` only `MyDatabaseId` (plus `PROC_AFFECTS_ALL_HORIZONS`, used for hot standby feedback, and recovery); `slot_xmin` is folded into the data and shared horizons; the doc comment says a standby is only protected "unless the standby uses a replication slot".
- PostgreSQL source, [src/backend/access/heap/vacuumlazy.c](https://github.com/postgres/postgres/blob/master/src/backend/access/heap/vacuumlazy.c) - primary: VACUUM works from `cutoffs.OldestXmin`; the verbose log line is "removable cutoff: %u, which was %d XIDs old when operation ended".
- PostgreSQL source, [postgresql.conf.sample](https://github.com/postgres/postgres/blob/master/src/backend/utils/misc/postgresql.conf.sample) - primary: `idle_in_transaction_session_timeout = 0`, `transaction_timeout = 0`, `idle_replication_slot_timeout = 0`, `max_slot_wal_keep_size = -1`, `hot_standby_feedback = off` are all the defaults (disabled / unlimited).

**Note on sourcing:** only GitHub-hosted sources were reachable (postgresql.org docs failed DNS). Nothing here is from the user-facing docs or a vendor blog; no incident numbers are cited. The mechanism is read straight from the horizon computation.

**Key primary-source detail:** the horizon is computed per database for user tables, so an idle session in database A does not hold back vacuum in database B, but it does hold back shared catalogs. The one exception is a standby with `hot_standby_feedback`: it carries `PROC_AFFECTS_ALL_HORIZONS` because "that can't be tied to a specific database".

---

## LinkedIn Post

When a Postgres table bloats despite autovacuum running constantly, the usual advice is to tune autovacuum. Lower the scale factor, raise the cost limit, add workers. That advice assumes vacuum is the bottleneck. Often it is not.

Vacuum can only remove a dead row if no snapshot could still see it. The cutoff is a single number, the oldest xmin in play. In procarray.c, ComputeXidHorizons walks every backend and takes the older of its xmin and its xid. The result is one horizon for all normal tables in that database, not one per table.

So a session that ran a SELECT in a transaction, then went idle without committing, pins the cutoff. Vacuum scans the table, finds the dead rows, and correctly leaves them. The verbose log even says it: "removable cutoff: ..., which was N XIDs old when operation ended". The work happens and nothing is reclaimed. Raising its priority does not help, because the rows are not eligible.

Three things move the horizon backwards, and only one of them is a session you can see in pg_stat_activity. An idle-in-transaction backend. A replication slot, whose slot_xmin is folded straight into the data horizon. And a standby with hot_standby_feedback, which the source flags as affecting all horizons because it "can't be tied to a specific database". A forgotten slot on a replica that was decommissioned months ago is the quiet one.

The scope is narrower than people fear. Backends in other databases are ignored for user tables, and vacuum backends themselves are skipped. But shared catalogs consider everyone.

Now the uncomfortable part. Check the defaults in postgresql.conf.sample: idle_in_transaction_session_timeout is 0, transaction_timeout is 0, idle_replication_slot_timeout is 0, max_slot_wal_keep_size is -1. Every guardrail that would bound the horizon ships disabled. The database trusts every client to commit eventually.

That is a defensible default. Killing sessions by surprise breaks applications. But it means the safety limit is a decision someone has to make, and until they do, a single connection from a notebook, a stuck job, or a dead replica sets the cleanup speed for the whole database.

Tuning autovacuum is the right answer to a slow cleaner. It is the wrong answer to a cleaner that is not allowed to clean.

#PostgreSQL #Databases #SystemDesign #Backend

---

## Twitter Version

Postgres table bloating while autovacuum runs nonstop? Tuning autovacuum may be the wrong fix.

Vacuum can only remove dead rows older than one cutoff: the oldest xmin of any backend. One horizon per database, not per table.

An idle-in-transaction session pins it. So does a replication slot (slot_xmin goes straight into the horizon), and a standby with hot_standby_feedback. Vacuum runs, logs "removable cutoff", reclaims nothing.

The defaults that would bound this are all off: idle_in_transaction_session_timeout=0, transaction_timeout=0, idle_replication_slot_timeout=0, max_slot_wal_keep_size=-1.

A cleaner that isn't allowed to clean doesn't need tuning.

---

## Diagram

See `2026-10-25-postgres-xmin-horizon-one-old-transaction-blocks-vacuum.excalidraw` (timeline of transactions with the pinned horizon line and the three things that hold it back).
