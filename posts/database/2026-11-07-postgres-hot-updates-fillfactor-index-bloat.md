---
date: 2026-11-07
company: PostgreSQL
topic: HOT (heap-only tuple) updates - an UPDATE that touches no indexed column and fits on the same page skips index maintenance and is cleaned by single-page pruning; one indexed column or a full page turns it into a cold update. fillfactor reserves the room.
category: database
post_type: structured
opening_style: shared_pain_point
slug: postgres-hot-updates-fillfactor-index-bloat
---

## Sources

- GitHub, postgres/postgres [src/backend/access/heap/README.HOT](https://github.com/postgres/postgres/blob/master/src/backend/access/heap/README.HOT) - primary: "Without HOT, every version of a row in an update chain has its own index entries"; "indexed column" includes any column referenced in an index definition, even only in a partial-index predicate; HOT chain restricted to a single page; pruning needs a cleanup lock; root line pointer becomes a redirect.
- GitHub, postgres/postgres [doc/src/sgml/storage.sgml](https://github.com/postgres/postgres/blob/master/doc/src/sgml/storage.sgml) (docs section "Heap-Only Tuples") - primary: two conditions (no indexed column modified, BRIN excepted; free space on the old row's page); intermediate versions removed during normal operation including SELECTs, no vacuum needed.
- GitHub, postgres/postgres [doc/src/sgml/ref/create_table.sgml](https://github.com/postgres/postgres/blob/master/doc/src/sgml/ref/create_table.sgml) - primary: fillfactor is 10-100, default 100; smaller values reserve page space for updates and make HOT more likely; "in heavily updated tables smaller fillfactors are appropriate."

**Key primary-source detail:** a column used only in a partial-index WHERE predicate still counts as "indexed" and disables HOT.

Note: the opening scenario is generic, no company incident is claimed.

---

## LinkedIn Post

Every heavily updated Postgres table pays the same hidden tax, and most teams never see the bill.

MVCC means an UPDATE writes a new row version. The README in the Postgres source says what that normally costs: "Without HOT, every version of a row in an update chain has its own index entries, even if all indexed columns are the same." Change a counter on a row with five indexes and you write five index entries that all point at the same logical row, and later someone has to vacuum them out.

Heap-only tuples (HOT) were built to skip that. Two conditions, both from the docs. First, the update modifies no column referenced by the table's indexes (BRIN excepted). Second, the new version fits on the same page as the old one.

When both hold, the new tuple gets no index entries at all. The index keeps pointing at the original line pointer, and the page follows a chain forward. Because the chain lives in a single page, there are no extra page fetches.

The cleanup is the better half. Intermediate versions are removed "during normal operation, including SELECTs," by pruning a single page, with no table-wide vacuum. The original line pointer becomes a redirect, so the index never needs to change.

Now the traps.

"Indexed column" is broader than it sounds. The README says it means any column referenced in an index definition, including columns only tested in a partial-index predicate. An index on (user_id) WHERE status = 'active' means every update to status is a cold update.

And the second condition is about space. The default fillfactor is 100: pages are packed full, so on a busy table there is often no room for the new version. The docs are direct: for tables that are never updated, full packing is best, but "in heavily updated tables smaller fillfactors are appropriate." The range is 10 to 100. Setting it to 70 trades 30% more heap for room to update in place.

The decision is a tradeoff, not a rule: drop an index you barely use, or move a hot counter into its own narrow table, and the indexes stop being part of the write path. Heap size for write speed is a good trade only if you measured which updates are actually going HOT.

#PostgreSQL #Databases #SystemDesign #BackendEngineering

---

## Twitter Version

Every heavily updated Postgres table pays a tax most teams never see.

MVCC: an UPDATE writes a new row version. Without HOT, "every version of a row in an update chain has its own index entries." Five indexes, five new entries per update.

HOT skips it when (1) no indexed column changes and (2) the new version fits on the same page. No index entries, and the dead versions get pruned from that one page, no vacuum needed.

Traps: a column used only in a partial-index WHERE counts as indexed. And fillfactor defaults to 100, so pages are often too full to qualify.

Fillfactor 70 = 30% more heap for room to update in place. Measure how many updates go HOT first.

---

## Diagram

See `2026-11-07-postgres-hot-updates-fillfactor-index-bloat.excalidraw` (comparison matrix: HOT update vs cold update, with the two conditions).
