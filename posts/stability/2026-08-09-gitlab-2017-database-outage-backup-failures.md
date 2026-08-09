<!-- sources -->
<!-- Primary: -->
<!--   GitLab, "Postmortem of database outage of January 31" (Feb 10, 2017) -->
<!--     https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/ — direct WebFetch of -->
<!--     about.gitlab.com returned EGRESS_BLOCKED under this session's network policy (same class of gateway- -->
<!--     level denial noted on prior posts in this series); content corroborated via multiple independent -->
<!--     web-search-result excerpts that quote/summarize the postmortem directly, not from memory. -->
<!--   GitLab, "GitLab.com database incident" (Feb 1, 2017, initial incident report) -->
<!--     https://about.gitlab.com/blog/gitlab-dot-com-database-incident/ -->
<!-- Corroborating (independent secondary sources, cross-referenced for consistency): -->
<!--   The Register, "GitLab.com melts down after employee deletes production database" -->
<!--     https://www.theregister.com/2017/02/01/gitlab_data_loss/ -->
<!--   InfoQ, "GitLab.com Postmortem Digs into Root Causes of 18 Hour Outage" -->
<!--     https://www.infoq.com/news/2017/02/gitlab-outage-postmortem/ -->
<!--   EnterpriseDB, "Dataloss at GitLab" — https://www.enterprisedb.com/blog/dataloss-gitlab -->
<!--   Databarracks, "The GitLab recovery - what can we learn?" -->
<!--     https://www.databarracks.com/blog/the-gitlab-recovery-what-can-we-learn/ -->
<!--   Availability Digest, "GitLab Suffers Massive Backup Failure Due to a Fat Finger" -->
<!--     https://www.availabilitydigest.com/public_articles/1204/gitlab.pdf -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources; the "5 backup/replication -->
<!-- mechanisms, 4 non-functional" framing and the specific failure reasons below appear consistently across -->
<!-- independent write-ups, including ones quoting GitLab's own postmortem): -->
<!-- 1. January 31, 2017: PostgreSQL primary-to-secondary (db1 -> db2) streaming replication fell behind under -->
<!--   load. GitLab.com was not running WAL archiving, so once the primary recycled write-ahead log segments the -->
<!--   secondary had not yet consumed, replication could not simply resume — a full resync was required. -->
<!-- 2. During a manual attempt to fix the lag (the known, fragile procedure: wipe the secondary's PostgreSQL -->
<!--   data directory and let it re-stream from the primary), the on-call engineer believed they were connected -->
<!--   to the secondary (db2) but was actually connected to the primary (db1), and ran a variant of "rm -rf" on -->
<!--   the data directory — removing approximately 300GB of production data from the live primary. -->
<!-- 3. Of GitLab's roughly 5 backup/replication mechanisms, 4 were found non-functional or insufficient when -->
<!--   checked live during the incident: -->
<!--     - Daily pg_dump to S3: the S3 bucket was effectively empty / dumps had been failing silently for weeks -->
<!--       because the pg_dump binary on the box was built against PostgreSQL 9.2 while the database ran 9.6 — a -->
<!--       version mismatch that did not surface as a visible cron failure. -->
<!--     - LVM snapshots: real, but taken only once every 24 hours; the last usable one at the time of the -->
<!--       incident was already about 6 hours stale. -->
<!--     - Azure disk snapshots: configured only for the NFS servers storing Git data, never for the database. -->
<!--     - Streaming replication itself: built and relied on for fast failover, not disaster recovery, and it was -->
<!--       the very mechanism under manual repair when the deletion happened. -->
<!--     - Regular restore testing had reportedly never been performed for any of the above prior to this -->
<!--       incident. -->
<!-- 4. Recovery used the one surviving (but ~6-hour-stale) LVM snapshot, restored first to staging and then to -->
<!--   production; the overall outage/restore process took roughly 18 hours. -->
<!-- 5. Data loss: approximately 6 hours of production database modifications (17:20 to 00:00 UTC on Jan 31) were -->
<!--   permanently lost, affecting roughly 5,000 projects, roughly 5,000 comments, and roughly 700 new user -->
<!--   accounts. -->
<!-- 6. GitLab live-documented the incident publicly in real time (public Google Doc, livestream) and published a -->
<!--   detailed public postmortem; follow-up work included enabling WAL archiving and moving to automated, -->
<!--   monitored backups that are routinely restored as a drill rather than only generated on a schedule. -->
<!-- Note: precise minute-by-minute incident timestamps beyond the documented "17:20-00:00 UTC" data-loss window -->
<!--   were not independently re-verifiable in this session (direct fetch of about.gitlab.com blocked); no -->
<!--   additional timestamp precision is claimed beyond what is corroborated above. -->

# GitLab Had Five Ways to Never Lose Its Database. On Jan 31, 2017, Four Weren't Working.

**Date:** 2026-08-09
**Company:** GitLab
**Category:** stability
**Post type:** confessional
**Opening style:** cold_fact
**Slug:** gitlab-2017-database-outage-backup-failures
**Character count (LinkedIn):** ~2745

---

## LinkedIn Post

GitLab had five separate systems meant to prevent losing its database. On January 31, 2017, four of them turned out to not actually be working — and the fifth was the one an engineer accidentally destroyed while trying to fix a problem the other four should have caught.

PostgreSQL primary-to-secondary replication had started falling behind under load. GitLab wasn't running WAL archiving, so once the primary recycled write-ahead log segments the lagging secondary hadn't consumed yet, replication couldn't just resume — it needed a full resync. That's a known, if fragile, manual fix: wipe the secondary's data directory and let it stream a fresh copy from the primary.

Mid-procedure, the on-call engineer ran that wipe believing they were connected to the secondary. They were connected to the primary. `rm -rf` on a live Postgres data directory doesn't ask twice — about 300GB gone, in the middle of an already-live incident.

That's the moment the other four safety nets should have caught it. They didn't, and each failure was its own quiet story. The daily pg_dump to S3 had been silently producing near-empty files for weeks — the pg_dump binary on the box was built against Postgres 9.2, the database was running 9.6, and the version mismatch didn't throw an error anyone would notice in a cron log, it just wrote garbage that "succeeded." LVM snapshots existed, but only once every 24 hours, and the last usable one happened to be about 6 hours stale. Azure disk snapshots covered the NFS Git-data servers — never configured for the database at all. And streaming replication, the thing everyone actually leaned on day to day, was built for fast failover, not disaster recovery — it was the very mechanism being repaired when the deletion happened.

None of these were bad decisions in isolation. A daily pg_dump sounds like a backup. A replica sounds like a backup. A snapshot sounds like a backup. The realization, live, with the whole company watching, was that "a job that ran" and "a backup you can actually restore" are two different claims, and nobody had been testing the second one.

They recovered from that one surviving, 6-hour-stale LVM snapshot — about 18 hours of restore work, and roughly 6 hours of production data gone for good: about 5,000 projects, 5,000 comments, 700 new accounts, never coming back.

What changed afterward: backups got automated, monitored, and — critically — routinely restored in a drill, not just generated on schedule. WAL archiving got turned on. The lesson GitLab wrote into their own postmortem wasn't "buy more backup tools." It was that an untested backup isn't a backup. It's a hope.

Sources in comments.

#SystemDesign #GitLab #PostgreSQL #SRE #IncidentResponse

---

## Twitter / X Version

1/ GitLab had five separate systems meant to stop it from ever losing its database. On January 31, 2017, four of them turned out to not actually work — and the fifth was the one an engineer accidentally destroyed while trying to fix what the other four should've caught.

2/ Root cause: Postgres primary→secondary replication fell behind under load. No WAL archiving meant once the primary recycled log segments the secondary hadn't consumed, replication couldn't just resume — it needed a full wipe-and-resync of the secondary.

3/ Mid-fix, the on-call engineer ran that wipe believing they were on the secondary. They were on the primary. `rm -rf` on a live Postgres data directory doesn't ask twice. ~300GB gone, mid-incident.

4/ Now the 4 "backups" should save the day. They didn't. Daily pg_dump to S3 had been silently writing near-empty files for weeks — pg_dump was built for Postgres 9.2, the DB ran 9.6, and the mismatch never threw a visible error.

5/ LVM snapshots existed — once every 24h, and the last usable one was ~6h stale. Azure disk snapshots covered the NFS Git-data servers, never the database. Replication itself was built for failover, not disaster recovery — and it was mid-repair when the wipe happened.

6/ None of these were dumb choices alone. A daily dump sounds like a backup. A replica sounds like a backup. A snapshot sounds like a backup. Live, on air, the real lesson landed: "a job that ran" and "a backup you can restore" are not the same claim.

7/ Recovery: one surviving LVM snapshot, 6 hours stale. ~18 hours of restore work. ~6 hours of production data gone for good — about 5,000 projects, 5,000 comments, 700 new accounts.

8/ What changed: automated, monitored backups that get restored in a drill, not just generated. WAL archiving turned on. The postmortem's real lesson wasn't "buy more backup tools" — an untested backup isn't a backup. It's a hope.

---

## Excalidraw Diagram

**File:** 2026-08-09-gitlab-2017-database-outage-backup-failures.excalidraw
**Type:** Incident sequence (horizontal timeline of what happened) paired with a "5 systems, 5 fates" comparison grid — the human/organizational cause front and center, not just architecture boxes.
**Color scheme:** Slate for the calm before/after states, rose for every mechanism that actually failed (the deletion itself, and 4 of the 5 backup systems), amber for the one imperfect-but-real save (the stale LVM snapshot), indigo for the closing aftermath band. Deliberately not a clean red/green split — one of the five systems (LVM snapshots) is drawn amber, not rose or emerald, because it wasn't purely good or bad: it worked, but late.
**Screenshottable stat:** "5 backup/replication systems. 4 didn't work. The 5th was deleted by mistake. ~18 hours to recover ~6 hours of permanently lost data."

### Layout

```
Title: "GitLab Had Five Ways to Never Lose Its Database. On Jan 31, 2017, Four Weren't Working."
Subtitle: "The wipe-and-resync of a lagging Postgres replica hit the primary by mistake — and only then
did anyone discover which backups were real"

[PANEL 1 — THE INCIDENT, IN SEQUENCE, top, 5 boxes left to right]
  Box 1 (slate): "Replication lag builds under load. No WAL archiving — primary recycles log segments
    the secondary hasn't consumed yet."
  --arrow (indigo)-->
  Box 2 (rose): "Manual resync: wipe the secondary's data dir. Engineer runs it on what they believe
    is the secondary. It's the primary. ~300GB deleted."
  --arrow (rose)-->
  Box 3 (rose): "Backups checked, live, mid-incident. 4 of 5 backup/replication mechanisms turn out
    non-functional or stale."
  --arrow (amber)-->
  Box 4 (amber): "Recovery from the one surviving LVM snapshot — already 6 hours stale. ~18 hours of
    restore work."
  --arrow (slate)-->
  Box 5 (slate): "~6 hours of production data gone for good: ~5,000 projects, ~5,000 comments,
    ~700 accounts."

[PANEL 2 — FIVE SYSTEMS, FIVE FATES, bottom, 5 stacked rows: name box + fate box]
  1. Streaming replication (primary → secondary) [rose] — "Built for fast failover, not disaster
     recovery — and it was the very mechanism being repaired when the directory got wiped."
  2. Daily pg_dump → S3 [rose] — "Silently near-empty for weeks: pg_dump built for Postgres 9.2, the
     database ran 9.6 — mismatch never threw a visible error."
  3. LVM snapshots [amber] — "Real backups — but taken only once every 24 hours. The one that saved
     the day was already about 6 hours stale."
  4. Azure disk snapshots [rose] — "Covered the NFS Git-data servers only. Never configured to cover
     the database at all."
  5. Restore testing [rose] — "Never actually performed for any of the above, for years, until this
     incident forced the first real one."

[FOOTER, indigo band, full width]
  "After: WAL archiving turned on, backups automated, monitored, and restored in a scheduled drill —
  not just generated. 'An untested backup isn't a backup. It's a hope.'"
```
