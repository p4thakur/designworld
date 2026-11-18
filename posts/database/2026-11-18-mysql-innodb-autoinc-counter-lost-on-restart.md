---
date: 2026-11-18
company: MySQL (InnoDB)
topic: Through 5.7, InnoDB kept the AUTO_INCREMENT counter only in memory and rebuilt it on first table open after restart with SELECT MAX(col)+1, so deleting the highest rows and restarting reissued their IDs. Bug #199 (filed 2003) was fixed by WL#6204 in 8.0 (2016) by logging each new counter value to redo (MLOG_TABLE_DYNAMIC_META) and writing it to mysql.innodb_dynamic_metadata at checkpoint.
category: databases
post_type: confessional
opening_style: cold_fact
slug: mysql-innodb-autoinc-counter-lost-on-restart
---

## Sources

- MySQL 5.7, [storage/innobase/handler/ha_innodb.cc](https://github.com/mysql/mysql-server/blob/5.7/storage/innobase/handler/ha_innodb.cc) - primary: `innobase_initialize_autoinc()` "Set the autoinc column max value. This should only be called once from ha_innobase::open()", with the comment `/* Execute SELECT MAX(col_name) FROM TABLE; */` before `row_search_max_autoinc()`, then `innobase_next_autoinc(read_auto_inc, 1, 1, 0, col_max_value)`. In `open()`: "we only init the autoinc counter once, the first time the table is loaded", guarded by `if (dict_table_autoinc_read(m_prebuilt->table) == 0)`.
- MySQL 5.7, [storage/innobase/dict/dict0dict.cc](https://github.com/mysql/mysql-server/blob/5.7/storage/innobase/dict/dict0dict.cc) - primary: `dict_table_autoinc_store()` / `dict_table_autoinc_restore()` keep the counter in `dict_sys->autoinc_map` when a table is evicted from the dictionary cache, so eviction does not reset it; only a restart does.
- MySQL 8.0, [storage/innobase/include/dict0mem.h](https://github.com/mysql/mysql-server/blob/8.0/storage/innobase/include/dict0mem.h) - primary: `autoinc` ("Autoinc counter value to give to the next inserted row") vs `autoinc_persisted` ("Autoinc counter value that has been persisted in redo logs or DDTableBuffer"); `PM_TABLE_AUTO_INC = 2`; `AutoIncPersister` writes "1 byte for dynamic metadata type and 11 bytes for the max possible size of counter."
- MySQL 8.0, [storage/innobase/dict/dict0dict.cc](https://github.com/mysql/mysql-server/blob/8.0/storage/innobase/dict/dict0dict.cc) - primary: `dict_table_autoinc_log()` writes the counter to redo via `persister->write_log()` with "No need to flush due to performance reason"; `dict_persist_to_dd_table_buffer()` "write dirty persistent data of table to mysql.innodb_dynamic_metadata", called by checkpoint. Redo type `MLOG_TABLE_DYNAMIC_META = 62` in [mtr0types.h](https://github.com/mysql/mysql-server/blob/8.0/storage/innobase/include/mtr0types.h).
- MySQL 8.0, [mysql-test/suite/innodb/t/autoinc_persist.test](https://github.com/mysql/mysql-server/blob/8.0/mysql-test/suite/innodb/t/autoinc_persist.test) - primary: "Scenario 2: Delete some values, to test the counters should not be the one which is the largest in current table"; "Scenario 4: Update some values, to test the counters should be updated to the bigger value, but not smaller value"; "Scenario 10: Rollback would not rollback the counter."
- [Bug #199 "Innodb autoincrement stats los on restart"](https://bugs.mysql.com/bug.php?id=199) and [WL#6204 "InnoDB persistent max value for autoinc columns"](https://dev.mysql.com/worklog/task/?id=6204) - filed 2003; developer comment (Sept 2016) says fixed by WL#6204 in 8.0. Confirmed via search-result snippets and lefred's "bye bye bug 199"; bugs.mysql.com/dev.mysql.com were not directly reachable from this run.

**Key primary-source detail:** the 5.7 counter was not lost on dictionary-cache eviction (it was parked in `autoinc_map`), only on restart, and the recovery was literally commented as `SELECT MAX(col_name) FROM TABLE;`. In 8.0 there are two counters, `autoinc` (handed out) and `autoinc_persisted` (already logged), because the value is handed out before the redo record is written.

Derived/interpretive (author's reading, not MySQL-published): "13 years" is 2003 to 2016. The "orders 1..110, purge 101..110" example is illustrative, matching autoinc_persist.test Scenario 2. The claim that persistence rode on 8.0's new data dictionary is inferred from `mysql.innodb_dynamic_metadata` being an 8.0 DD table. Nothing here is a specific company incident.

---

## LinkedIn Post

MySQL Bug #199 was filed in 2003: InnoDB forgets its AUTO_INCREMENT counter on restart. The fix landed in 2016.

For a long stretch of those 13 years, not fixing it looked like the right call.

Here is what InnoDB did through 5.7. The counter lived only in memory, in dict_table_t::autoinc. Nothing wrote it to disk. The first time a table was opened after startup, ha_innobase::open() saw a zero counter and called innobase_initialize_autoinc(). The source comment says exactly what happens next: "Execute SELECT MAX(col_name) FROM TABLE;" The next ID became MAX + 1.

That's cheap and almost always right. Reading the rightmost entry of an index is one descent of the B-tree. No extra write on every insert, no new metadata to keep crash-safe. The 5.7 code even stashed the counter in a side map when a table got evicted from the dictionary cache, so only a real restart lost it.

The catch is deletes at the top. Insert orders 1 to 110, purge 101 to 110 into an archive, restart. MAX is now 100, so the next order is 101 again. The ID that your archive, your cache, your outbound events and your support tickets already knew now names a different row. The database never breaks a constraint. It just quietly reissues a name.

The fix was WL#6204 in 8.0, and its size explains the wait. Each new counter value now goes into the redo log as an MLOG_TABLE_DYNAMIC_META record. A second field, autoinc_persisted, tracks what has already been logged. At checkpoint, dirty tables get written to a new system table, mysql.innodb_dynamic_metadata, through DDTableBuffer. Startup reads that table and replays the redo on top. 8.0 also bumps the counter when an UPDATE sets the column above it, which 5.7 never did.

So "remember one integer" meant a new redo record type, a new system table and a hook into checkpointing. It landed with 8.0's rebuilt data dictionary, which is where that new table lives.

Nobody was careless here. SELECT MAX was a reasonable answer for a world where IDs stayed inside one database. The ground moved: IDs went out into caches, queues and other people's systems. A number that can be recomputed is only safe if nobody outside remembers the old one.

#MySQL #Databases #SystemDesign #InnoDB

---

## Twitter Version

MySQL Bug #199, filed 2003: InnoDB forgets AUTO_INCREMENT on restart.

Through 5.7 the counter lived in RAM. On first open after restart, InnoDB ran (source comment) "SELECT MAX(col_name) FROM TABLE;" and used MAX+1.

Delete ids 101-110, restart, and 101 gets handed out again. Your cache and your event log still think 101 is the old row.

8.0 fixed it in 2016: counter goes to redo, then to mysql.innodb_dynamic_metadata at checkpoint.

Recomputable is only safe if nobody outside remembers.

---

## Diagram

See `2026-11-18-mysql-innodb-autoinc-counter-lost-on-restart.excalidraw` (confessional timeline: 2003 Bug #199 filed -> <=5.7 "counter in RAM, SELECT MAX(id)+1 on first open" -> 2016/8.0 WL#6204 redo log + innodb_dynamic_metadata. Below, a dashed sand panel walks the reuse sequence "INSERT 1..110 -> purge 101..110 -> restart -> MAX = 100 -> next INSERT = 101 (again)" with the ha_innodb.cc source comment quoted. Palette: plum + teal + sand, no red/green.)
