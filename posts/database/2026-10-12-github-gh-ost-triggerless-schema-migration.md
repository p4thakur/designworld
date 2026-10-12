---
date: 2026-10-12
company: GitHub
topic: gh-ost replaces trigger-based online schema migration with a binlog-reading ghost table and a two-connection atomic cut-over.
category: database
post_type: narrative
opening_style: mid_scene
slug: github-gh-ost-triggerless-schema-migration
---

## Sources

- GitHub, [gh-ost doc: why triggerless](https://github.com/github/gh-ost/blob/master/doc/why-triggerless.md) - primary: trigger concurrency/locking, interpreted stored routines, can't pause triggers, replica testing limits.
- GitHub, [gh-ost doc: cut-over](https://github.com/github/gh-ost/blob/master/doc/cut-over.md) - primary: non-atomic two-step swap, two-connection lock + sentry table, failure rolls back.
- GitHub, [gh-ost doc: triggerless design](https://github.com/github/gh-ost/blob/master/doc/triggerless-design.md) - primary: binlog replica, alternating row copy and binlog backlog, checksum validation on replicas.

**Note on sourcing:** the GitHub engineering blog was unreachable from this environment; all facts come from the three docs in the gh-ost repo, read directly. No numbers beyond those docs are used.

**Key primary-source detail:** MySQL won't let a connection swap tables it holds under lock, so gh-ost needs two connections and a sentry table to make the final RENAME atomic and abortable.

---

## LinkedIn Post

Changing a column on a busy MySQL table sounds like a solved problem. The standard tools had been solving it for years, and GitHub still wrote its own.

The established approach creates a ghost copy of the table, copies rows over in chunks, and installs triggers on the original so every write is mirrored into the copy. It works. It also has a property that only shows up under load: the triggers run inside the same transactions as your production writes.

GitHub's docs list what that costs. Triggers compete for locks, like the auto_increment value on the ghost table, with no coordination between them. MySQL stored routines are interpreted, never compiled, so every write pays for that. The docs report near or complete lock downs in production.

The worse problem is control. Existing tools can pause the row copy, but not the triggers. Cancel the triggers and you lose information, so the data ends up wrong. On a busy server, the migration can't be told to back off.

Testing was no better. Triggers only fire on a replica under statement-based replication, and even then they don't reproduce the master's load.

gh-ost removes the triggers entirely. It pretends to be a MySQL replica, reads the binary log, and turns row changes into apply tasks for the ghost table. Row copy and binlog events sit in two queues, and gh-ost alternates between them so the server sees writes from a single connection. Because it is just a log reader, it can run against a replica, and pausing is trivial: stop reading.

That left the last step. Swapping the tables atomically is the one thing MySQL makes awkward. A two-step rename leaves a window where the table does not exist and queries fail. And a connection can't swap tables it holds under lock.

So gh-ost uses two connections. One holds the lock while the other issues the RENAME, and a sentry table blocks that rename until everything is confirmed in order. If anything times out, it falls back to the original table and tries again.

The tradeoff didn't disappear. It moved from the write path into a very careful final second.

#SystemDesign #MySQL #Databases #GitHub

---

## Twitter Version

Changing a column on a huge MySQL table: the standard tools copy rows to a ghost table and use triggers to mirror writes.

GitHub's docs list the problem. Triggers run inside production transactions, compete for locks, and are interpreted, never compiled. You can pause the row copy, but not the triggers. Cancel them and data goes wrong.

So gh-ost has no triggers. It poses as a replica, reads the binlog, and applies changes to the ghost table itself. Pausing means stop reading.

The last step is the hard one. A two-step rename leaves a moment with no table. So it uses two connections and a sentry table to make the swap atomic, and if anything times out, it rolls back.

The cost moved from every write to one careful second.

---

## Diagram

See `2026-10-12-github-gh-ost-triggerless-schema-migration.excalidraw` (side-by-side: trigger path inside the write transaction vs binlog path outside it).
