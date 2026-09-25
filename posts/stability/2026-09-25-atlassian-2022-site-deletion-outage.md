---
date: 2026-09-25
company: Atlassian
topic: An internal script built to safely soft-delete a retired app was run with the wrong list of IDs and in the wrong delete mode, permanently erasing 883 live customer Cloud sites in 23 minutes; the same multi-tenant architecture that made the mistake possible — every customer's rows sharing one database and one backup — is also why restoring those sites took 13 days instead of hours, since there was no way to recover a single tenant without reloading a whole shared backup and pulling that tenant's rows out by hand
category: stability
post_type: narrative
opening_style: mid_scene
slug: atlassian-2022-site-deletion-outage
---

## Sources

- Atlassian Engineering blog, ["Post-Incident Review on the Atlassian April 2022 outage"](https://www.atlassian.com/blog/atlassian-engineering/post-incident-review-april-2022-outage) — Atlassian's own primary post-incident review: confirms the script provided both a "mark for deletion" (soft, recoverable) capability used in normal operations and a "permanently delete" capability meant only for compliance-driven hard deletes; confirms the team supplied the IDs of entire Cloud sites instead of the IDs of the specific apps meant to be deleted; confirms restoration ran from April 8 through April 18, with no customer losing more than five minutes of data.
- The Register, ["Atlassian comes clean on data-deleting script behind outage"](https://www.theregister.com/2022/04/14/atlassian_ongoing_outage/) — corroborates that the maintenance script was tied to retiring the Insight asset-management app, that ~400 customers had data improperly deleted (of 775 customers/883 sites affected overall), and that the deleting API accepted both site and app identifiers without validating which type the caller had actually supplied.
- Arpit Bhayani, ["An Engineering Deep-Dive into Atlassian's April 2022 Outage"](https://arpitbhayani.me/videos/atlassian-outage-2022-engineering-deep-dive) — primary-source-adjacent technical breakdown of the restore mechanism: because customer data is intermingled in a shared multi-tenant database, restoring one org requires loading the entire backup into a database and then extracting that org's rows specifically, rather than any form of per-tenant restore; also explains the up-to-five-minute data loss window as the gap between the deletion and the last change-data-capture / write-ahead-log-based incremental backup checkpoint.
- Atlassian Engineering blog, ["April 2022 outage update"](https://www.atlassian.com/blog/atlassian-engineering/april-2022-outage-update) — Atlassian's own timeline update confirming the deletion window (07:38–08:01 UTC on April 5, 2022) and staged customer restoration through mid-April.

**Note on sourcing:** direct fetches of atlassian.com, jhall.io, dev.to, and newsletter.pragmaticengineer.com were blocked by this environment's network egress policy at write time. The facts above are drawn from search-indexed excerpts of Atlassian's own official blog posts (the quoted "mark for deletion" / "permanently delete" language appears verbatim in indexed excerpts of Atlassian's post-incident review) plus independent technical write-ups (The Register, Arpit Bhayani's deep-dive) that cite and corroborate the same primary review.

**Key primary-source detail (not in most summaries):** most retellings of this outage stop at "wrong script, wrong IDs." What the deeper technical breakdowns show is that the two failures were the same failure at two different layers. At the API layer, one endpoint accepted both app_id and site_id and a caller-supplied delete mode with no cross-check between them — so a list mismatch became a silent, catastrophic action instead of a rejected request. At the storage layer, that same "don't distinguish, just trust the input" simplicity shows up again as the reason recovery was so slow: the database itself doesn't distinguish one tenant's rows from another's at the backup level, so undoing damage to one customer meant reloading everyone's data and filtering by hand. The bug and the slow recovery share a root cause — a system built around trusting big, coarse operations, not questioning small, precise ones.

---

## LinkedIn Post

At 07:38 UTC on April 5th, 2022, an Atlassian script finished a maintenance task it had run safely many times before: retiring an old app called Insight, one of a batch of standalone products being folded into core Jira Service Management. Twenty-three minutes later, 883 full Jira and Confluence Cloud sites were gone. Not disabled. Deleted.

The script's actual job was narrow: take a list of app_id values and mark them for deletion — a soft, reversible flag, the kind you run all the time without fear, because nothing is actually gone yet. But the same underlying API also accepted a permanently-delete mode, built for a different, rarer case: compliance-driven hard deletes that have to be irreversible by design. On April 5th, someone handed the script the ID list for the sites the apps lived on, not the apps themselves — and ran it in the mode meant for permanent removal. The API took the input at face value. It had no way to know a site_id had wandered into a call built for app_id, because it was never built to ask.

775 paying customers lost access instantly. For roughly 400 of them, the data wasn't just locked — it was actually gone from the live system.

Here's the part that made this a 13-day outage instead of a 3-hour one: Atlassian's Cloud runs multi-tenant, meaning one customer's rows sit in the same database, and the same backup, as hundreds of others. There's no button for "restore this one org." Recovering a single deleted site meant reloading an entire multi-terabyte backup into a live database, then pulling out just that customer's rows by hand — and doing it again, and again, for each of the roughly 400 affected orgs, one at a time, off a single recovery pipeline that was never built to run at that scale in parallel.

The same architecture that makes multi-tenant SaaS cheap to run — pool everyone into shared infrastructure — is exactly what makes a single customer's disaster recovery expensive when it finally has to happen alone. Most customers got their last five minutes of writes back too, thanks to incremental write-ahead-log backups closing that final gap. But the site itself came back on whatever day its turn came up in the queue.

Atlassian's fix afterward wasn't just "check the ID type." It was building real per-tenant disaster recovery and pushing soft-deletes as the only kind of delete almost anywhere in the system. The bug was one bad list. The two-week outage was an architecture that had never needed to answer "restore exactly one" — until the day it had to answer that 400 times at once.

#SystemDesign #SRE #Atlassian #DisasterRecovery

**Character count: 2,618 / 3,000 ✓**
**First ~140 chars (mobile hook):** "At 07:38 UTC on April 5th, 2022, an Atlassian script finished a maintenance task it had run safely many times before: retiring an old" ✓

---

## Twitter / X Thread

1/ April 5th, 2022, 07:38 UTC. An Atlassian maintenance script finishes running — routine task, retiring an old app called Insight. Twenty-three minutes later, 883 full customer Cloud sites are gone. Not disabled. Deleted.

2/ The script's real job: take a list of app_id, soft-flag them for deletion. Reversible, safe, run it a hundred times without worry. But the same API also had a "permanently delete" mode, built for rare compliance-driven hard deletes.

3/ Someone handed it the site_id list instead of app_id — and ran it in permanent mode. The API trusted the input. Nothing checked whether the ID type matched the call.

4/ 775 customers locked out instantly. ~400 orgs' data actually erased, not just inaccessible.

5/ Here's why it took 13 days, not hours: Cloud is multi-tenant. Every customer's rows sit in the same database, and the same backup, as hundreds of others.

6/ No "restore this one org" button exists. Recovery meant reloading a full backup into a live database, then pulling one customer's rows out by hand — repeat ~400 times, one at a time, off a single pipeline.

7/ Most customers got their last 5 minutes of writes back, thanks to incremental WAL-based backups closing that gap. But the site itself came back whenever its turn hit the queue.

8/ The thing that makes multi-tenant SaaS cheap — pooling everyone onto shared infrastructure — is exactly what makes one customer's disaster recovery brutally slow the day it has to happen alone, for hundreds of customers at once.

---

## Diagram

See: `2026-09-25-atlassian-2022-site-deletion-outage.excalidraw`

Type: Sequence flow (narrative style) — three linked boxes left to right showing the request path and where it broke: (1) the script's intended job (app_id list, soft mark-for-delete), (2) what actually ran (site_id list, permanent-delete mode, no type check), (3) the immediate blast radius in raw numbers (883 sites, 775 customers, 23 minutes). A full-width banner underneath breaks out the separate mechanism that turned the incident into a 13-day outage — shared multi-tenant backups requiring a full reload-and-extract per customer — followed by a footer line with the final recovery date and the write-ahead-log detail behind the "under 5 minutes of data loss" claim.
Color scheme: teal/green for the script's safe, intended path (nothing wrong with that design in isolation), orange for the point where the wrong input met the wrong mode, red reserved specifically for the concrete blast-radius numbers (not a blanket bad-system color), and violet for the restore-mechanism explanation — since the backup design that made recovery slow was a deliberate, defensible cost tradeoff, not a mistake like the deletion itself.
Key screenshottable numbers: 23 minutes (07:38–08:01 UTC), 883 sites, 775 customers, ~400 orgs with data actually erased, 13 days to full restoration (April 5–18, 2022), under 5 minutes of lost writes for most.
