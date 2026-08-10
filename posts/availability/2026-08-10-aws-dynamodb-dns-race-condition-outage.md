<!-- sources -->
<!-- Primary: -->
<!--   AWS, "Summary of the Amazon DynamoDB Service Disruption in the Northern Virginia (US-EAST-1) Region" -->
<!--     (official post-event summary, published ~Oct 23-24, 2025) — direct WebFetch of aws.amazon.com returned -->
<!--     EGRESS_BLOCKED under this session's network policy (same class of gateway-level denial noted on prior -->
<!--     posts in this series, e.g. the GitLab 2017 post). Content corroborated via multiple independent -->
<!--     web-search-result excerpts from outlets that read and directly quote/summarize the official postmortem, -->
<!--     not from memory. -->
<!-- Corroborating (independent secondary sources, cross-referenced for consistency): -->
<!--   The Register, "A single DNS race condition brought AWS to its knees" (Oct 23, 2025) -->
<!--     https://www.theregister.com/2025/10/23/amazon_outage_postmortem/ -->
<!--   Constellation Research, "AWS delivers outage post mortem: When automation bites back" -->
<!--     https://www.constellationr.com/blog-news/insights/aws-delivers-outage-post-mortem-when-automation-bites-back -->
<!--   ThousandEyes, "AWS Outage Analysis: October 20, 2025" -->
<!--     https://www.thousandeyes.com/blog/aws-outage-analysis-october-20-2025 -->
<!--   Computerworld, "The AWS outage post-mortem is more revealing in what it doesn't say" -->
<!--     https://www.computerworld.com/article/4082890/the-aws-outage-post-mortem-is-more-revealing-in-what-it-doesnt-say.html -->
<!--   InfoQ, "AWS DynamoDB Outage Postmortem" (Nov 2025) — https://www.infoq.com/news/2025/11/aws-dynamodb-outage-postmortem -->
<!--   Gremlin, "Reliability lessons from the 2025 AWS DynamoDB outage" -->
<!--     https://www.gremlin.com/blog/reliability-lessons-from-the-2025-aws-dynamodb-outage -->
<!-- Key verifiable details (cross-referenced across independent write-ups that quote/summarize AWS's own -->
<!-- postmortem consistently): -->
<!-- 1. Oct 19-20, 2025, us-east-1: a latent race condition in the internal automation that manages DNS for -->
<!--   DynamoDB's regional endpoints. A "DNS Planner" continuously computes desired IP-record plans; redundant -->
<!--   "DNS Enactor" processes apply those plans to Route 53 and clean up stale ones. -->
<!-- 2. One DNS Enactor experienced unusual delay applying an older plan while the Planner kept producing newer -->
<!--   plans and a second, healthy Enactor applied them on schedule. When the delayed Enactor resumed, its -->
<!--   stale-plan check fired against outdated state and triggered cleanup that removed all IP records for -->
<!--   dynamodb.us-east-1.amazonaws.com, leaving an empty record the automation did not repair. -->
<!-- 3. This made every DynamoDB request in us-east-1 fail to resolve, including from AWS's own internal -->
<!--   services. EC2's Droplet Workflow Manager (DWFM), which leases/tracks the physical hosts ("droplets") in -->
<!--   the region and depends on DynamoDB to persist that lease state, began failing its lease checks broadly; -->
<!--   leases expired and healthy hosts were marked unavailable for new EC2 launches. -->
<!-- 4. DNS itself was restored roughly 3 hours in. EC2 recovery took roughly 12 additional hours: once DynamoDB -->
<!--   was reachable, DWFM tried to re-establish leases across the full regional fleet at once; timed-out -->
<!--   requests were requeued rather than dropped, and arrival rate outpaced processing rate — a state AWS's own -->
<!--   engineers described as "congestive collapse." Recovery required manually throttling incoming requests and -->
<!--   selectively restarting DWFM hosts; most leases were restored by approximately 5:28am ET. -->
<!-- 5. Total outage window commonly reported as ~15 hours, with 70-plus AWS services and reportedly 1,000-plus -->
<!--   downstream internet services/companies affected, including Snapchat, Fortnite, Roblox, Ring, Duolingo, -->
<!--   Signal, and others; exact "reports" counts vary by source/metric (figures from roughly 6.5 million to -->
<!--   17 million Downdetector-style reports appear across write-ups) and are not claimed here beyond "millions." -->
<!-- 6. Fixes described in AWS's own postmortem per corroborating sources: DNS Planner/Enactor automation disabled -->
<!--   worldwide pending a fix for the race condition plus new safeguards against applying an invalid/empty plan; -->
<!--   a new "velocity control" limiting how much capacity a Network Load Balancer can pull from rotation at once -->
<!--   on health-check failure; new EC2/DWFM scale tests specifically exercising the full-fleet recovery path, and -->
<!--   throttling that rate-limits incoming work by queue depth. -->
<!-- Note: precise sub-minute incident timestamps beyond the commonly corroborated "~11:48pm PT start / ~3hr DNS -->
<!--   fix / ~5:28am ET lease restoration / ~15hr total" figures were not independently re-verifiable in this -->
<!--   session (direct fetch of aws.amazon.com blocked); no additional timestamp precision is claimed beyond what -->
<!--   is corroborated above. -->

# AWS Ran Two Robots to Keep DynamoDB's DNS Safe. One Was Late, and the Other Let It Erase the Address.

**Date:** 2026-08-10
**Company:** AWS
**Category:** availability
**Post type:** narrative
**Opening style:** in_medias_res
**Slug:** aws-dynamodb-dns-race-condition-outage
**Character count (LinkedIn):** ~3479

---

## LinkedIn Post

Two processes were built to make DynamoDB's DNS safer. On October 19, 2025, they raced each other — and the loser won by accident, wiping every IP address for dynamodb.us-east-1.amazonaws.com and touching off a 15-hour outage that took down Snapchat, Fortnite, Roblox, Ring, Duolingo, and Signal along with it.

Here's the setup: a DNS Planner continuously computes the correct set of IP records for DynamoDB's regional endpoint. DNS Enactors — plural, deliberately redundant — apply those plans to Route 53 and clean up anything stale. Redundancy is the obvious answer to "what if one process hangs": run more than one, so a slow writer can't stall the system. It works because updates normally land in well under a second, so a newer plan supersedes an older one before staleness is ever a real question.

On the 19th, one Enactor got unusually slow applying an older plan while a second, healthy Enactor kept applying newer ones on schedule. There was no shared lock between them, no single writer, no version check that was atomic with the write — just two independent processes racing to be the last one to touch the same record. When the slow Enactor finally resumed, it checked whether its plan was stale against a view of the world that had already moved on, and its cleanup logic fired — not a narrow, validated removal of one old entry, but a wipe of the record. dynamodb.us-east-1.amazonaws.com went from several healthy IPs to zero. Not slow. Not degraded. Empty.

Here's the part that turned a DNS bug into a 15-hour outage: EC2's own control plane turns out to be one of DynamoDB's biggest customers. EC2's Droplet Workflow Manager tracks a lease on every physical host in us-east-1, and it stores that lease state in DynamoDB, checking in continuously. When DynamoDB's name stopped resolving, DWFM's lease checks started failing en masse — not because any server broke, but because the bookkeeping that tracked which servers were available had disappeared. Leases expired, and healthy machines got marked unavailable for new EC2 launches.

DNS itself was fixed in about three hours. EC2 took twelve more. Once DynamoDB was reachable again, DWFM tried to re-establish leases across the entire us-east-1 fleet at once — a full-fleet thundering herd. Requests that didn't complete before timing out got requeued instead of dropped, so the backlog grew faster than DWFM could drain it. AWS's own engineers called the resulting state "congestive collapse": arrival rate permanently ahead of processing rate. Recovery meant throttling incoming requests and selectively restarting DWFM hosts by hand until the backlog broke, with most leases restored around 5:28am ET.

The fix wasn't "add more redundancy." It was closer to the opposite: AWS turned the DNS Planner and Enactor automation off worldwide until they could close the actual race with real compare-and-swap protection — a plan can no longer overwrite or delete state without proving it's still current. For the Network Load Balancer, a new "velocity control" now caps how much capacity can be pulled from rotation in one health-check failure. For EC2, new scale tests specifically exercise the full-fleet recovery path that had never actually been load-tested at that scale before.

Redundant writers without a single source of truth aren't more available. They're a race with better uptime — until the day the timing lines up.

Sources in comments.

#SystemDesign #AWS #DynamoDB #DistributedSystems #SRE

---

## Twitter / X Version

1/ AWS ran two redundant processes to keep DynamoDB's DNS safe. On Oct 19, 2025, they raced each other — and the loser won by accident, wiping every IP for dynamodb.us-east-1.amazonaws.com. 15 hours down. Snapchat, Fortnite, Roblox, Duolingo, Signal, all caught in it.

2/ Setup: a DNS Planner computes IP plans for DynamoDB's regional endpoint. DNS Enactors — plural, redundant on purpose — apply them to Route 53. Normally updates land in under a second, so a newer plan beats an older one before staleness is ever a real question.

3/ On the 19th, one Enactor stalled applying an old plan. A second, healthy one kept applying new plans on schedule. No shared lock. No single writer. No version check atomic with the write — just two independent processes racing to touch the same record last.

4/ The stalled Enactor resumed, checked staleness against a view of the world that had already moved on, and fired its cleanup logic — not a narrow removal of one old entry, but a wipe. dynamodb.us-east-1.amazonaws.com went from healthy IPs to zero. Not slow. Empty.

5/ Why it became a 15-hour outage instead of a 3-hour one: EC2's own control plane is a huge DynamoDB customer. Droplet Workflow Manager leases every physical host in us-east-1 and stores that lease state in DynamoDB, checking in constantly.

6/ DNS died → DWFM's lease checks failed en masse → leases expired → healthy machines got marked unavailable for new EC2 launches. Nothing physically broke. The bookkeeping just vanished.

7/ DNS was fixed in ~3 hours. EC2 took 12 more. DWFM tried to re-lease the entire fleet at once — a full thundering herd. Timed-out requests got requeued instead of dropped, so the backlog grew faster than it could drain. AWS called it "congestive collapse."

8/ Recovery meant throttling requests and manually restarting DWFM hosts until the backlog broke — leases mostly restored ~5:28am ET.

9/ The fix wasn't more redundancy — it was less, temporarily. AWS turned the Planner/Enactor automation off worldwide until they could add real compare-and-swap protection so no plan can overwrite state without proving it's current.

10/ Redundant writers without one source of truth aren't more available. They're a race with better uptime — until the day the timing lines up.

---

## Excalidraw Diagram

**File:** 2026-08-10-aws-dynamodb-dns-race-condition-outage.excalidraw
**Type:** Two-panel — a 5-box horizontal sequence of the DNS race itself, paired with a 5-row cascade panel showing how one DNS bug turned into a 15-hour, multi-service outage.
**Color scheme:** Slate for the calm start/end states, rose for every step where the race condition or its cascade is actively destructive, amber for the imperfect-but-working recovery steps (manual DNS fix, NLB capacity protection). Not a clean two-color split — the point is that redundancy (drawn as the "safe" default) is exactly what removes the safety net once ordering breaks.
**Screenshottable stat:** "2 redundant DNS processes, 0 IPs left after they raced. 3 hours to fix DNS. 12 more hours for EC2 to recover. ~15 hours, 1,000+ services down."

### Layout

```
Title: "AWS Ran Two Robots to Keep DynamoDB's DNS Safe. One Was Late, and the Other Let It Erase the Address."
Subtitle: "A race condition between two DNS automation processes emptied dynamodb.us-east-1.amazonaws.com —
and EC2 turned out to be one of DynamoDB's biggest customers"

[PANEL 1 — THE RACE, IN SEQUENCE, top, 5 boxes left to right]
  Box 1 (slate): "Oct 19, ~11:48pm PT. DNS Planner keeps computing fresh IP plans for DynamoDB's regional
    endpoint. Enactors normally apply each one in under a second."
  --arrow (indigo)-->
  Box 2 (rose): "One DNS Enactor stalls applying an older plan. A second, healthy Enactor keeps applying
    newer plans on schedule. No shared lock between them."
  --arrow (rose)-->
  Box 3 (rose): "Stalled Enactor resumes, checks staleness against outdated state, fires cleanup — wiping
    the DNS record instead of removing one narrow, validated old entry."
  --arrow (rose)-->
  Box 4 (rose): "dynamodb.us-east-1.amazonaws.com resolves to zero IPs. Every client, including AWS's own
    control plane, gets an empty answer, not a timeout."
  --arrow (amber)-->
  Box 5 (amber): "AWS disables DNS automation, manually restores records. DNS itself is fixed roughly
    3 hours after it started."

[PANEL 2 — THE CASCADE: ONE RACE, FIVE FAILURES DOWNSTREAM, bottom, 5 stacked rows: name box + fate box]
  1. EC2 Droplet Workflow Manager (DWFM) [rose] — "Leases every physical host in us-east-1 — and stores
     that lease state in DynamoDB. When DNS died, so did every lease check-in."
  2. Droplet leases [rose] — "Leases expire when checks fail. Healthy physical servers get marked
     unavailable for new EC2 launches — the machines were fine, the bookkeeping wasn't."
  3. Recovery attempt: congestive collapse [rose] — "DynamoDB comes back; DWFM tries to re-lease the whole
     fleet at once. Timed-out requests get requeued, not dropped — arrival rate outpaces drain rate."
  4. Network Load Balancer health checks [amber] — "Failing health checks pull capacity out of rotation
     faster than it can be validated back in, compounding the backlog elsewhere in the stack."
  5. Manual throttling [slate] — "Engineers throttle incoming requests and selectively restart DWFM hosts
     to drain the queue. Leases mostly restored ~5:28am ET — 12 hours after DNS itself was fixed."

[FOOTER, indigo band, full width]
  "Total: ~15 hours, 70+ AWS services, 1,000+ downstream services — Snapchat, Fortnite, Roblox, Ring,
  Duolingo, Signal among them. Fix: DNS automation off worldwide until the race has real compare-and-swap
  protection. 'Redundant writers without a single source of truth aren't safer. They're a race with
  better uptime.'"
```
