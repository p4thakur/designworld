---
date: 2026-11-21
company: PostgreSQL (fsyncgate, 2018)
topic: Postgres treated a failed fsync() as retryable, so it raised ERROR, aborted the checkpoint and tried again. On Linux a failed writeback leaves the page non-dirty ("lost async page write", buffer not uptodate, PG_error set, never re-dirtied). The second fsync() therefore returned 0, the checkpoint completed, and the redo point moved past the WAL that held the only good copy. In Linux 4.13–4.16 there was a second problem: errseq_t marked an existing error as "seen" at open(), so the checkpointer's later-opened fd never saw it at all. That was fixed in 4.17 by b4678df184b3. Postgres's fix (9ccdd7f66, shipped 2019-02-14 in 11.2 and back to 9.4.21) sends every data-file fsync failure through data_sync_elevel(), which returns PANIC, and then recovers from WAL. The old behavior can be restored with data_sync_retry=on.
category: storage
post_type: contrarian
opening_style: challenge_assumption
slug: postgres-fsyncgate-panic-not-retry
---

## Sources

- PostgreSQL REL_11_2, [doc/src/sgml/release-11.sgml](https://raw.githubusercontent.com/postgres/postgres/REL_11_2/doc/src/sgml/release-11.sgml). Primary. The 11.2 release (date 2019-02-14) has the entry "By default, panic instead of retrying after fsync() failure, to avoid possible data corruption (Craig Ringer, Thomas Munro)". The text reads: "Some popular operating systems discard kernel data buffers when unable to write them out, reporting this as fsync() failure. If we reissue the fsync() request it will succeed, but in fact the data has been lost ... By raising a panic condition instead, we can replay from WAL, which may contain the only remaining copy of the data ... While this is surely ugly and inefficient, there are few alternatives". The commit header shows master 9ccdd7f66 (2018-11-19) and backports to REL_11 through REL9_4. The same note appears in REL_10_7, REL9_6_12 and REL9_4_21 (grepped).
- PostgreSQL REL_11_2, [src/backend/storage/file/fd.c](https://raw.githubusercontent.com/postgres/postgres/REL_11_2/src/backend/storage/file/fd.c). Primary. `data_sync_elevel(int elevel) { return data_sync_retry ? elevel : PANIC; }`. The comment above it says: "Data may have been written to the operating system and removed from our buffer pool already, and if we are running on an operating system that forgets dirty data on write-back failure, there may be only one copy of the data remaining: in the WAL. A later attempt to fsync again might falsely report success. Therefore we must not allow any further checkpoints to be attempted."
- PostgreSQL REL_11_2, guc.c and [config.sgml](https://raw.githubusercontent.com/postgres/postgres/REL_11_2/doc/src/sgml/config.sgml). Primary. `data_sync_retry` is PGC_POSTMASTER and defaults to false. The docs say: "the second attempt may be reported as successful, when in fact the data has been lost."
- PostgreSQL REL_11_1, [src/backend/storage/smgr/md.c](https://raw.githubusercontent.com/postgres/postgres/REL_11_1/src/backend/storage/smgr/md.c). Primary, the pre-fix behavior. `mdsync()` does `ereport(ERROR, ... "could not fsync file ...")`, so the checkpoint fails and is retried later.
- Linux v4.16 [fs/buffer.c](https://raw.githubusercontent.com/torvalds/linux/v4.16/fs/buffer.c). Primary. On a failed write, `end_buffer_async_write()` calls `buffer_io_error(bh, ", lost async page write"); mark_buffer_write_io_error(bh); clear_buffer_uptodate(bh); SetPageError(page);`. The page is not re-dirtied.
- Linux [v4.13 lib/errseq.c](https://raw.githubusercontent.com/torvalds/linux/v4.13/lib/errseq.c) (errseq_t introduced: a 32-bit value holding an errno, a SEEN flag and a counter), [v4.16](https://raw.githubusercontent.com/torvalds/linux/v4.16/lib/errseq.c) (`errseq_sample()` sets ERRSEQ_SEEN on any existing error at sample time) and [v4.17](https://raw.githubusercontent.com/torvalds/linux/v4.17/lib/errseq.c) ("If nobody has seen this error yet, then we can be the first."). Primary.
- Matthew Wilcox, ["[PATCH] Always report a writeback error once"](https://lkml.iu.edu/hypermail/linux/kernel/1804.2/07389.html), LKML 2018-04-23, with v2 on 2018-04-24 and review by Andres Freund. Commit b4678df184b3 fixes 5660e13d2fd6, was tagged for stable, and went into 4.14.y. These details come from search-result excerpts.
- pgsql-hackers thread ["PostgreSQL's handling of fsync() errors is unsafe and risks data loss at least on XFS"](https://www.postgresql.org/message-id/CAMsr%2BYHh%2B5Oq4xziwwoEfhoTZgr07vdGG%2Bhu%3D1adXx59aTeaoQ%40mail.gmail.com) (Craig Ringer, March–April 2018). Ringer's stack was "xfs over lvm2 over multipath over a SAN", and the thin-provisioned SAN ran out of space while "Linux *thought* there was plenty of space". On 2018-03-29 he wrote "TL;DR: Pg should PANIC on fsync() EIO return". postgresql.org was blocked in this run, so these quotes come from search-result excerpts.
- Rebello et al., ["Can Applications Recover from fsync Failures?"](https://www.usenix.org/conference/atc20/presentation/rebello), USENIX ATC 2020. It studies ext4, XFS and Btrfs plus PostgreSQL, LMDB, LevelDB, SQLite and Redis, and concludes that none of their failure-handling strategies is sufficient. This is background and was not used in the post.

**Key primary-source detail:** the retry wasn't merely useless, it was the step that confirmed the loss. After the first failure the kernel has no dirty page left to write, so the second fsync() succeeds. A successful fsync() is what lets the checkpoint finish and the redo pointer move past the WAL holding the last good copy. Separately, between 4.13 and 4.16, `errseq_sample()` at open() silently marked an existing error as seen. Postgres's checkpointer opens files after the backends that wrote them have closed theirs, so its fd could miss the error completely.

Derived/interpretive (the author's reading, not stated verbatim by a source): "the redo point moves past the WAL that held the only good copy" is the standard consequence of a completed checkpoint, since WAL before the redo point becomes recyclable. The fd.c comment's "only one copy of the data remaining: in the WAL" supports it. The closing generalization about retries is the author's.

---

## LinkedIn Post

Every engineer knows what to do when an I/O call fails: log it and retry. PostgreSQL did exactly that with fsync() for about 20 years. In 2018 it learned that the retry was where the data got lost.

Craig Ringer hit it first, on a stack he described as XFS on LVM on multipath on a thin-provisioned SAN. The SAN ran out of real space. Linux thought the volume had plenty.

Here's the sequence. A backend write()s an 8 KB page, and Postgres evicts it from shared_buffers. Now the only copies are in the kernel page cache and in the WAL.

The kernel starts writeback, which clears the page's dirty bit, and the write fails. fs/buffer.c logs "lost async page write", marks the buffer not-uptodate and sets PG_error. It does not re-dirty the page. The kernel no longer has any dirty page to write.

The checkpointer calls fsync(), which returns EIO once. Postgres did the reasonable thing: raise ERROR, abort the checkpoint, try again next time.

On the next checkpoint, fsync() returns 0, because there's nothing dirty left to fail on. The checkpoint completes, the redo pointer moves past the WAL that held the only good copy, and the write is gone with nothing logged.

There was a second trap. The checkpointer often opens a file after the backend that wrote it has closed it. In Linux 4.13–4.16, errseq_t marked an existing error as "seen" at open(), so a descriptor opened after the failure never saw it. Commit b4678df184b3 in 4.17 fixed that.

But no kernel patch fixes the main problem: once writeback fails, the page cache no longer has your data.

So Postgres stopped retrying. Thomas Munro's commit 9ccdd7f66 shipped in 11.2 in February 2019 and was backported to 9.4.21. It sends every data-file fsync failure through data_sync_elevel(), which returns PANIC. The server crashes on purpose, then crash recovery replays WAL and rewrites the pages from the one copy that survived.

The release note calls this "surely ugly and inefficient." It is also correct. data_sync_retry=on brings back the old behavior, and the docs warn that the retry "may be reported as successful".

We retry by default because we assume a failed call leaves the state as it was. fsync breaks that assumption. The first failure changes the state the retry runs against.

If a failure has already destroyed what you meant to retry, retrying only gets you a false success. Crashing and rebuilding from your own log is the only safe option.

#PostgreSQL #Linux #Databases #Storage

---

## Twitter Version

fsync() failed. The textbook move is to retry. For 20 years PostgreSQL did, and the retry is what lost the data.

On Linux, failed writeback doesn't keep the page dirty. The kernel logs "lost async page write" and moves on. fsync #1 returns EIO. fsync #2 has nothing left to write, so it returns 0.

That 0 let the checkpoint finish and moved the redo point past the WAL holding the last good copy. The loss was silent.

On 4.13–4.16 it was worse: a file opened after the error never saw it at all.

The fix in 11.2 (2019): any data-file fsync failure means PANIC, then replay WAL. "Surely ugly and inefficient." It's also the only correct answer.

---

## Diagram

See `2026-11-21-postgres-fsyncgate-panic-not-retry.excalidraw`. It's a contrarian side-by-side. A shared top band shows write() → evicted from shared_buffers → writeback fails, "lost async page write", page not re-dirtied. The left column (amber) is the obvious path: fsync #1 EIO → ERROR, retry; fsync #2 returns 0; redo point moves past the WAL, so the loss is silent. The right column (navy) is the contrarian path: fsync #1 EIO → data_sync_elevel() → PANIC; crash recovery; WAL replay rewrites the pages. A dashed footer covers the 4.13–4.16 errseq "seen at open()" gap fixed by b4678df184b3. Palette: navy, amber and grey, with no red or green.
