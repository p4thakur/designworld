# GitHub's mysql1: When the Margin Ran Out

> **Sources (primary):**
> - [Partitioning GitHub's relational databases to handle scale](https://github.blog/engineering/infrastructure/partitioning-githubs-relational-databases-scale/) — GitHub Engineering Blog, September 2021
> - [February service disruptions post-incident analysis](https://github.blog/2020-03-26-february-service-disruptions-post-incident-analysis/) — GitHub Engineering Blog, March 2020

---

## LinkedIn Post

On February 27, 2020, GitHub went down for the fourth time in nine days.

Not four different problems. Four different expressions of the same one: mysql1.

mysql1 was GitHub's main database cluster. It housed the tables that ran the whole platform: users, repositories, issues, pull requests. By 2019, it was processing 950,000 queries per second — 900,000 against replicas, 50,000 against the primary.

That ratio looked healthy. It wasn't.

In mid-February, a query meant to run against the replica pool was accidentally routed to the primary. Load spiked. ProxySQL — the connection pooler sitting in front of mysql1 — started dropping connections.

That's when the team found something quietly alarming. The file descriptor limit on ProxySQL nodes had been silently reduced from 1,073,741,824 to 65,536 by the process manager — a 16,000x drop — with no warning logged. The system simply accepted the lower cap and moved on.

mysql1 had no margin. Eight hours and 14 minutes of degraded service. Four outages in nine days.

GitHub had recognized the problem in 2019 and already started planning a split. The February incidents changed the timeline. But splitting a cluster that holds your most critical tables — without downtime, without losing a write — is not simple.

They built two parallel migration paths.

Vitess, a sharding layer originally built at YouTube, could move sets of tables with zero downtime via vertical sharding. But Vitess adoption at GitHub was still early in 2020. They didn't want a single migration path for tables that powered most of GitHub.com.

So they also built a custom write-cutover process: add a replica to mysql1, let it sync, stop replication, flip connections, cut it loose. They used this to move 130 of the busiest tables — repositories, issues, pull requests — in a single operation.

By 2021, per-host load on mysql1's successors dropped 50%. Total query volume grew to 1.2 million queries per second. The pressure was real; now it had somewhere to go.

The file descriptor bug wasn't something they wrote. The misconfigured query wasn't careless — it was one step in an active scaling project. The cluster had handled 950,000 queries a day for years without complaint.

It worked until the margin disappeared.

#SystemDesign #Databases #MySQL #SoftwareEngineering

---

**Character count: ~2,307** ✓ (limit: 3,000)

---

## Twitter / X Version

GitHub went down four times in nine days in February 2020. All four traced back to one cluster: mysql1. Here's the story. 🧵

1/ By 2019, mysql1 processed 950,000 queries/sec — every repo, issue, and PR. 900K hit replicas. 50K hit the primary. It looked fine.

2/ Then a single query got misrouted to the primary instead of the replica pool. Load spiked. ProxySQL (the connection pooler) collapsed.

3/ The hidden cause: file descriptor limits on ProxySQL had been silently capped at 65,536 by the process manager — down from 1,073,741,824. A 16,000x reduction. No warning. No log entry.

4/ Four outages. 8 hours 14 minutes total. GitHub had already started planning a split in 2019. February 2020 changed the urgency.

5/ They built two migration paths in parallel — couldn't trust Vitess alone at that stage. Vitess handled zero-downtime table moves. The custom write-cutover moved 130 tables at once: add replica → sync → stop replication → flip.

6/ By 2021: per-host load cut 50%. Total QPS grew to 1.2M. The pressure didn't disappear. It just got room.

7/ The cluster wasn't fragile by design. It ran 950K QPS for years. It became fragile the day it ran out of margin.

---

## Diagram

See: `github-mysql1-four-outages.excalidraw`

**Type:** Narrative timeline — three phases (2019 → Feb 2020 → 2021) with file descriptor annotation and migration paths below.
