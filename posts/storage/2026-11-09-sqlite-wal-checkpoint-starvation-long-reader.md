---
date: 2026-11-09
company: SQLite
topic: Autocheckpoint (1000 pages) is passive; a long-lived read transaction pins its snapshot, caps backfill at the reader's mark, and prevents the WAL from restarting, so the WAL grows unbounded.
category: storage
post_type: contrarian
opening_style: challenge_assumption
slug: sqlite-wal-checkpoint-starvation-long-reader
---

## Sources

- GitHub, sqlite/sqlite [src/wal.c](https://github.com/sqlite/sqlite/blob/master/src/wal.c) - primary: reader algorithm (mxFrame snapshot), aReadMark / WAL_NREADER, mxSafeFrame computation in walCheckpoint ("will never overwrite a database page that a concurrent reader might be using"), walRestartLog (exclusive lock on read marks 1..N-1, WAL only resets if no reader uses them).
- GitHub, sqlite/sqlite [src/sqlite.h.in](https://github.com/sqlite/sqlite/blob/master/src/sqlite.h.in) - primary: sqlite3_wal_autocheckpoint docs (default 1000 pages, checkpoints are PASSIVE), PASSIVE mode semantics (busy-handler never invoked, may leave checkpoint unfinished).
- GitHub, sqlite/sqlite [src/main.c](https://github.com/sqlite/sqlite/blob/master/src/main.c) - primary: sqlite3WalDefaultHook triggers checkpoint when nFrame >= configured threshold.
- GitHub, sqlite/sqlite [doc/wal-lock.md](https://github.com/sqlite/sqlite/blob/master/doc/wal-lock.md) - primary: checkpointer lock order (read marks taken exclusively).

**Key primary-source detail:** WAL reset (walRestartLog) takes an exclusive lock on read marks 1..N-1; a single reader on any of them makes it busy, so new frames append instead of overwriting the start of the log.

Note: www.sqlite.org was unreachable from the session network; all facts come from the source mirror on GitHub. No company incident is claimed.

---

## LinkedIn Post

Everyone knows SQLite checkpoints its WAL every 1000 pages. Fewer know that number is a request, not a ceiling.

The default is real. In sqlite.h.in: "Every new database connection defaults to having the auto-checkpoint enabled with a threshold of 1000 ... pages." After each commit, a hook checks the WAL size and, past the threshold, calls a checkpoint. It is natural to read that as "the WAL stays around 1000 pages."

It does not, and the reason is in two details.

First, the docs say it plainly: "Checkpoints initiated by this mechanism are PASSIVE." And a passive checkpoint "never invokes the busy-handler" and "might leave the checkpoint unfinished if there are concurrent readers or writers." It does what it can and leaves.

Second, what limits it is a reader. In wal.c, every read transaction records the last valid frame (mxFrame) and reads a consistent snapshot from there. The checkpointer computes mxSafeFrame: for each read mark in use, if a reader sits at an earlier frame, the checkpoint caps itself there. The source comment is blunt: it "will never overwrite a database page that a concurrent reader might be using."

Now the part that actually grows the file. The WAL only restarts from the beginning when walRestartLog finds every reader on read mark 0, meaning nobody needs old frames. It tries an exclusive lock on read marks 1 to N-1. If a reader holds one, the lock is busy, the WAL is not reset, and new frames are appended at the end.

So one connection that opens a read transaction and never finishes it, say a cursor left open, a forgotten BEGIN, or a slow export, pins its snapshot. Writers keep committing. Each commit triggers a passive checkpoint that can only go up to that reader's mark. The WAL grows past 1000 pages and keeps growing until the reader is gone. Reads also pay for it: the wal-index has to be searched across a longer log.

The fix is not a bigger threshold or a more aggressive mode. FULL and RESTART modes block waiting on that same reader. The fix is to find the long transaction. Keep read transactions short, and treat WAL file size as a metric: a WAL far above 1000 pages usually points to a reader, not a checkpoint setting.

Autocheckpoint is polite. It checkpoints what it can without getting in anyone's way. The cost of being polite is that the slowest reader sets the pace for everyone else.

#SQLite #Databases #SystemDesign #BackendEngineering

---

## Twitter Version

SQLite checkpoints its WAL every 1000 pages by default. That is a request, not a cap.

Autocheckpoint is PASSIVE: no busy-handler, and it "might leave the checkpoint unfinished if there are concurrent readers."

In wal.c the checkpointer computes mxSafeFrame from every active reader's mark and never overwrites a page a reader might use.

The WAL restarts from frame 0 only when all readers are on read mark 0. One read transaction left open means no reset. Writers keep appending.

Result: a WAL far past 1000 pages, with slower reads. FULL/RESTART modes just block on the same reader.

Fix: find the long transaction, not the threshold.

---

## Diagram

See `2026-11-09-sqlite-wal-checkpoint-starvation-long-reader.excalidraw` (scaling curve: WAL size over time, healthy sawtooth vs pinned by a long reader).
