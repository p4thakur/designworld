<!-- sources -->
<!-- Primary: -->
<!--   Nick Craver (Stack Overflow / Stack Exchange), "Stack Overflow: The Architecture - 2016 Edition" (Feb 17, 2016) -->
<!--   URL: https://nickcraver.com/blog/2016/02/17/stack-overflow-the-architecture-2016-edition/ -->
<!--   Nick Craver, "Stack Overflow: The Hardware - 2016 Edition" (Mar 29, 2016) -->
<!--   URL: https://nickcraver.com/blog/2016/03/29/stack-overflow-the-hardware-2016-edition/ -->
<!-- Note: direct fetch of nickcraver.com returned HTTP 403 under this session's egress policy (same class of -->
<!-- gateway-level denial hit on prior posts in this series, e.g. monzo.com, careersatdoordash.com). Craver's -->
<!-- blog is statically generated from his own public GitHub repo, and the raw markdown source files for both -->
<!-- posts above were fetched directly and successfully from that repo — effectively the primary source itself, -->
<!-- not a summary of it: -->
<!--   https://raw.githubusercontent.com/NickCraver/nickcraver.github.com/main/blog/_posts/2016-02-17-stack-overflow-the-architecture-2016-edition.markdown -->
<!--   https://raw.githubusercontent.com/NickCraver/nickcraver.github.com/main/blog/_posts/2016-03-29-stack-overflow-the-hardware-2016-edition.markdown -->
<!-- These were cross-checked against independent secondary coverage of the same posts: -->
<!--   DataCenterDynamics, "Stack Overflow: Still on prem, runs Q&A platform off just nine servers" -->
<!--   URL: https://www.datacenterdynamics.com/en/news/stack-overflow-still-on-prem-runs-qa-platform-off-just-nine-servers/ -->
<!--   High Scalability, "StackOverflow Update: 560M Pageviews a Month, 25 Servers, and It's All About Performance" -->
<!--   URL: https://highscalability.com/stackoverflow-update-560m-pageviews-a-month-25-servers-and-i/ -->
<!--   Techworld with Milan newsletter, "Stack Overflow Architecture" — https://newsletter.techworld-with-milan.com/p/stack-overflow-architecture -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Stack Overflow's production web tier ran on 9 IIS servers (11 total including 2 dev/meta boxes), each a -->
<!--    Dell R630: dual Xeon E5-2690v3 (12 cores, 2.6-3.5GHz), 64GB RAM, 2x 300GB Intel SSDs in RAID 1, dual -->
<!--    10Gbps NICs. -->
<!-- 2. SQL Server tier: 4 servers across 2 AlwaysOn Availability Group clusters. Stack Overflow cluster: dual -->
<!--    E5-2697v2 (12 core), 384GB RAM, 1x 4TB Intel P3608 NVMe + 24x 200GB Intel 710 SSDs. Stack Exchange -->
<!--    cluster: dual E5-2667v3 (8 core), 768GB RAM, 3x 2TB Intel P3700 NVMe + 24x 1.2TB 10K HDDs. -->
<!-- 3. Redis: 2 main servers (256GB RAM, ~90GB in use) plus 2 dedicated ML servers (384GB RAM, ~125GB in use), -->
<!--    handling roughly 160 billion ops/month at under 2% CPU per instance. Elasticsearch: 3-node clusters (one -->
<!--    per data center), all-SSD, 192GB RAM, dual 10Gbps. HAProxy: 4 load balancers (v1.5.15 on CentOS 7, 64GB+ -->
<!--    RAM for SSL negotiation). -->
<!-- 4. Traffic on February 9th, 2016 (a single day, cited directly in the primary post): 209.4 million HTTP -->
<!--    requests, 66.3 million page loads, 504.8 million SQL queries generated from those HTTP requests, 5.8 -->
<!--    billion Redis hits, 17.2 million Elasticsearch searches, 1.24TB of HTTP traffic sent. Average server-side -->
<!--    render time: 22.71ms for question pages, 11.80ms for the home page. SQL server CPU utilization sat at -->
<!--    5-10% almost always (per High Scalability's contemporaneous coverage of the same architecture). -->
<!-- 5. Architecture: a single multi-tenant application pool served the entire Q&A network (Stack Overflow plus -->
<!--    all Stack Exchange sites) from one shared codebase — not microservices. Craver's post states the whole -->
<!--    network could run off a single application pool on a single server if it had to (not a recommendation, -->
<!--    a statement about built-in headroom). Database access used the Dapper micro-ORM almost exclusively; the -->
<!--    primary post notes only 1 stored procedure existed in the entire database. All of the above ran on -->
<!--    on-premises hardware the company owned, not public cloud infrastructure. -->

# Stack Overflow Served 209 Million Requests in a Day Off Nine Servers. No Microservices. No Cloud.

**Date:** 2026-07-15
**Company:** Stack Overflow
**Category:** performance
**Post type:** contrarian
**Opening style:** challenge_assumption
**Slug:** stackoverflow-monolith-vertical-scaling
**Character count (LinkedIn):** ~2,265

---

## LinkedIn Post

For a decade, the standard advice for internet-scale traffic has been the same: break the monolith into microservices, move to the cloud, scale out horizontally as load grows. On February 9th, 2016, Stack Overflow's engineers published exactly what their infrastructure looked like — and it broke every rule in that playbook.

Nine web servers. One monolithic application, one app pool. On-premise hardware, not cloud. That day alone, the site absorbed 209.4 million HTTP requests, 66.3 million page loads, and 504.8 million SQL queries generated from those requests, plus 5.8 billion Redis hits and 17.2 million Elasticsearch searches. Question pages rendered server-side in 22.71 milliseconds on average.

Here's why the obvious fix — split it up, scale it out — wasn't obvious to them: their SQL servers were running at 5-10% CPU, almost always. Their Redis instances handled roughly 160 billion operations a month at under 2% CPU each. There was no server gasping for capacity. Horizontal scaling and microservices solve a real problem — a single machine maxed out, a team blocked on someone else's deploy — and that problem hadn't shown up yet. Building a distributed system to solve a bottleneck that doesn't exist just adds network hops, serialization, and failure modes you didn't have before.

So instead of scaling out, they specced up. Dell R630s for the web tier — dual 12-core Xeons, 64GB RAM. SQL boxes built for their exact workload, one cluster running 384GB RAM over NVMe, another running 768GB. Four HAProxy boxes doing SSL termination. The whole Q&A network could, in a pinch, run off a single application pool on a single server — not a recommendation, just a fact about how much headroom was actually built in.

Microservices and cloud autoscaling are the default because they solve the problems most growing companies actually have — team autonomy, isolated deploys, unpredictable bursty load. Stack Overflow didn't have those problems. It had a predictable Q&A workload and engineers who measured where the ceiling actually was before they built anything to raise it. The industry's default architecture isn't wrong. It's just routinely applied to bottlenecks nobody bothered to check for.

#SystemDesign #Monolith #Scalability #StackOverflow

---

## Twitter / X Version

1/ The standard playbook for internet-scale traffic: break the monolith, go microservices, move to the cloud, scale out horizontally. On Feb 9, 2016, Stack Overflow's public architecture numbers broke every part of that playbook.

2/ Nine web servers. One monolith, one app pool, on-prem hardware. That single day: 209.4M HTTP requests, 66.3M page loads, 504.8M SQL queries, 5.8B Redis hits, 17.2M Elasticsearch searches. Question pages rendered server-side in 22.71ms average.

3/ Why they didn't split it up: SQL server CPU sat at 5-10%, almost always. Redis ran ~160 billion ops/month at under 2% CPU per instance. Nothing was actually maxed out. Horizontal scaling solves a capacity problem — theirs didn't exist yet.

4/ Instead of scaling out, they specced up: Dell R630 web servers (dual 12-core Xeons, 64GB RAM), SQL boxes with 384-768GB RAM over NVMe, 4 HAProxy boxes for SSL termination. The whole Q&A network could run off one app pool on one server if it had to.

5/ Microservices and cloud autoscaling are the default because they solve real problems — team autonomy, isolated deploys, bursty load. Stack Overflow didn't have those problems. It had predictable traffic and engineers who measured the ceiling before building anything to raise it.

---

## Excalidraw Diagram

**File:** 2026-07-15-stackoverflow-monolith-vertical-scaling.excalidraw
**Type:** Side-by-side architecture comparison (contrarian) — the industry-default playbook against what Stack Overflow actually ran, plus a full-width stats bar and a capacity-headroom callout as the screenshottable centerpiece.
**Color scheme:** Cyan for the default playbook (not a villain — the right call for most companies), burnt orange for what Stack Overflow actually built, fuchsia for the traffic-stats bar (the twist), stone/neutral for the closing reflection. No red/green good/bad pairing — this is a "different problem shape, different answer" story, not a "cloud bad" story.
**Screenshottable stat:** "Feb 9, 2016, nine web servers: 209.4M HTTP requests · 66.3M page loads · 504.8M SQL queries · 5.8B Redis hits · 17.2M Elasticsearch searches — with SQL CPU at 5-10% and Redis under 2% CPU the whole time."

### Layout

```
Title: "Stack Overflow Served 209 Million Requests in a Day Off Nine Servers. No Microservices. No Cloud."
Subtitle: "Feb 9, 2016 — the industry-default scaling playbook, versus the one Stack Overflow actually ran"

[THE DEFAULT PLAYBOOK — cyan]                      [WHAT STACK OVERFLOW ACTUALLY BUILT — orange]
Break the monolith into                              One monolith, one app pool, running the
microservices. Move to the                           entire Q&A network. On-premises hardware,
cloud. Scale out horizontally                        individually specced per job — SQL boxes
as traffic grows. Add nodes                          with NVMe and 384-768GB RAM, web tier at
when a server nears its ceiling.                     64GB RAM and 12 cores each.

[TRAFFIC — ONE DAY, NINE WEB SERVERS — fuchsia, full width]
Feb 9, 2016: 209.4M HTTP requests · 66.3M page loads · 504.8M SQL queries · 5.8B Redis hits · 17.2M Elasticsearch searches
Question pages rendered server-side in 22.71ms average.

[THE CAPACITY THAT WAS NEVER USED — orange]
SQL servers: 5-10% CPU, almost always. Redis: ~160 billion ops/month, under 2% CPU per instance. The bottleneck
horizontal scaling and microservices exist to solve never actually showed up at Stack Overflow's traffic level.

[REFLECTION — stone, footnote]
Microservices and cloud autoscaling solve real problems — team autonomy, isolated deploys, bursty load. Stack
Overflow didn't have those problems. It had predictable traffic and engineers who measured the ceiling first.
```
