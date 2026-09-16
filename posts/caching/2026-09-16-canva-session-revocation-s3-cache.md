---
date: 2026-09-16
company: Canva
topic: Canva kept its session-revocation list entirely in memory on every API gateway pod, refreshed from MySQL — the right call when they had a dozen pods, but a self-inflicted database stampede once every deploy meant hundreds of pods each pulling a million-plus records from MySQL at once; the fix moved the durable copy to S3 as pre-sorted 16-byte binary chunks gateways binary-search instead of query
category: caching
post_type: confessional
opening_style: cold_fact
slug: canva-session-revocation-s3-cache
---

## Sources

- Canva Engineering Blog: ["Session revocations at scale"](https://www.canva.dev/blog/engineering/session-revocations-at-scale/) by Llew Vallis, published July 22, 2026 — the primary source for the architecture, the 30-minute/16-byte binary chunk design, and the author's own explanation of why the original in-memory design was the right call.
- InfoQ: ["Canva Shares S3 Based Architecture for Session Revocation across Hundreds of Millions of Sessions"](https://www.infoq.com/news/2026/08/canva-session-revocation-scale/), August 2026 — independent summary corroborating the numbers and the deploy-stampede root cause, including the detail that post-migration database load scales with revocation write throughput and site traffic rather than gateway pod count.
- daily.dev syndication: ["Session revocations at scale"](https://daily.dev/posts/session-revocations-at-scale-freptfjr1) — secondary corroboration of the same figures.

**Note on sourcing:** Direct fetch of canva.dev and infoq.com was blocked by this environment's network egress policy at write time. The facts and quotes below are drawn from search-indexed excerpts of Canva's own engineering blog post, cross-checked against two independent summaries of the same post, which agree on the same architecture, numbers, and root-cause details.

**Key primary-source detail (not in most summaries):** The in-memory design wasn't a mistake the team later regretted — it was a deliberate tradeoff the author defended directly when asked why gateways don't just query the database on every check: querying per-refresh would increase database load and tie gateway availability to the database's, at exactly the moment (a deploy, a spike) that coupling hurts most. Most retellings of "we moved our cache to S3" imply the in-memory approach was the mistake. It wasn't — the mistake was reloading it from a relational database on every pod boot, at pod counts nobody designed for originally.

---

## LinkedIn Post

Canva has roughly 100 million active sessions live at any moment. Checking whether any one of them has been revoked — a logout, a stolen token, an admin kicking someone out — has to happen on every request, without hitting a database each time. So Canva kept the entire revocation set in memory, on every API gateway pod, refreshed from MySQL.

That design made sense. When someone asked why not just query the database directly on every check, an engineer on the team explained it plainly: frequent lookups would push more load onto MySQL on every token refresh, and it would tie gateway availability to the database's — exactly when a deploy or a traffic spike is the moment you can least afford that coupling. In memory, revocation checks stayed fast and kept working even through a bad minute for the database.

What stopped working was the loading, not the caching. As Canva added gateway capacity, every deploy became hundreds of pods, each independently pulling the full revocation set — over a million records apiece — from MySQL within seconds of each other. Deploys turned into a self-inflicted stampede on their own database. The instinctive fix was more MySQL read replicas, which treats the symptom: it doesn't shrink a full reload, it just buys headroom to survive one.

The actual fix left the in-memory idea alone and replaced what it loaded from. Revocations now live in S3, not MySQL: a rolling 12-hour window sliced into 30-minute chunks, each one a flat, pre-sorted array of 16-byte binary records — a principal ID and a timestamp — that a gateway can binary-search straight off disk. A pod restart now means fetching a handful of small, static S3 objects instead of running a query that returns a million-row result set.

The gateway cache's memory footprint dropped 87.5%. MySQL read replicas went from a scaling variable to two, kept only for redundancy — and database load now scales with revocation write throughput and site traffic, not with how many gateway pods happen to be restarting. The revocation worker processes over 2,000 events a second with room to spare.

Nobody misdesigned the original cache. It was the right call when Canva had a dozen gateway pods. What changed was the pod count, and the fix wasn't rethinking whether to cache in memory — it was noticing that "load everything from MySQL on boot" was never built to survive that kind of fan-out.

#SystemDesign #Caching #DistributedSystems #BackendEngineering

**Character count: 2,454 / 3,000 ✓**
**First 140 chars (mobile hook):** "Canva has roughly 100 million active sessions live at any moment. Checking whether any one of them has been revoked — a logout, a stolen tok" ✓

---

## Twitter / X Thread

1/ Canva runs about 100 million active sessions at once. Checking if any single one has been revoked has to happen on every request — without hitting a database each time.

2/ Their fix: keep the full revocation set in memory on every API gateway pod, refreshed from MySQL. Fast, and it kept working even during a rough minute for the database.

3/ An engineer on the team defended that choice directly: querying the DB on every refresh would add load and tie gateway uptime to the database's — right when a deploy or spike is the worst time for that coupling.

4/ The cache was never the problem. The reload was. Every deploy meant hundreds of gateway pods each pulling a million-plus revocation rows from MySQL within seconds of each other — a self-inflicted stampede on every release.

5/ The instinct is "add more read replicas." That doesn't shrink the reload. It just buys headroom to survive one.

6/ What actually fixed it: move the durable copy to S3. A rolling 12-hour window sliced into 30-minute chunks, each a sorted array of 16-byte binary records a gateway can binary-search straight off disk. No more full-table pulls from MySQL on boot.

7/ Result: cache memory down 87.5%. MySQL read replicas down to 2, redundancy only. DB load now scales with write throughput and traffic, not pod count. Revocation worker handling 2,000+ events/sec with headroom.

8/ The original in-memory design wasn't wrong. It just never accounted for what "load everything on boot" costs once you have hundreds of pods instead of a dozen.

---

## Diagram

See: `2026-09-16-canva-session-revocation-s3-cache.excalidraw`

Type: Spike/load visualization (confessional style) — two jagged load-over-time line charts side by side, "before" showing a cluster of near-simultaneous spikes (hundreds of gateway pods hammering MySQL during one deploy) and "after" showing a flat, low line (gateways binary-searching static S3 chunks instead), plus a callout box with the primary-source quote about why the in-memory design was deliberate, and a footer with the headline numbers.
Color scheme: burnt orange for the "before" spike (a real cost, not a moral failing — the design was right until pod count grew), deep violet for the "after" line (distinct from the teal used in the last two posts' diagrams), slate-blue callout box. No red/green good-bad pairing.
Key screenshottable number: cache memory footprint down 87.5%, MySQL read replicas down to 2 (redundancy only), revocation worker at 2,000+ events/sec.
