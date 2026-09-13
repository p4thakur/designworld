---
date: 2026-09-13
company: AWS
topic: AWS spent two hours fixing internal DNS errors during the Dec 7, 2021 US-EAST-1 outage — then the outage kept going for five more hours, because DNS was a symptom of network congestion, not the cause, and that same congestion had also broken the status page's own failover
category: availability
post_type: narrative
opening_style: specific_number
slug: aws-2021-network-congestion-dashboard-blind
---

## Sources

- AWS: ["Summary of the AWS Service Event in the Northern Virginia (US-EAST-1) Region"](https://aws.amazon.com/message/12721/), published December 10, 2021 — AWS's own post-event summary, the primary source for the trigger time, root cause, and recovery timestamps below.
- CNBC: ["AWS explains outage and will make it easier to track future ones"](https://www.cnbc.com/2021/12/10/aws-explains-outage-and-will-make-it-easier-to-track-future-ones.html), December 10, 2021 — covers AWS's own admission that congestion broke the Service Health Dashboard's regional failover.
- The Stack: ["Why did AWS Support fail with US-EAST-1 again?"](https://www.thestack.technology/us-east-1-aws-support-aws-outage/) and ["AWS outage cause: It's always DNS, but sometimes it's..."](https://www.thestack.technology/aws-outage-cause-network/) — corroborate the Support Contact Center outage and the DNS misdiagnosis sequence.
- ThousandEyes: ["AWS Outage Analysis: December 7 & 10, 2021"](https://www.thousandeyes.com/blog/aws-outage-analysis-dec-7-2021) — independent network-level analysis corroborating the recovery timeline.

**Note on sourcing:** Direct fetch of aws.amazon.com, thestack.technology, and web.archive.org was blocked by this environment's network egress policy at write time. The facts and quotes below are drawn from search-indexed excerpts of AWS's own message/12721 page, cross-checked against CNBC's and The Stack's independent coverage of that same AWS statement, which agree on the same timestamps and wording.

**Key primary-source detail (not in most summaries):** AWS's Service Health Dashboard has a failover mechanism to a standby region for exactly this kind of event. It didn't fire during this outage, because reaching the standby region also required routing through the same congested internal network the outage was caused by. AWS confirmed this directly: the congestion "impaired our Service Health Dashboard tooling from appropriately failing over to our standby region." Most retellings just say "AWS couldn't update its status page" — the actual reason is that the tool's own redundancy design shared a single point of failure with the thing it was built to report on.

---

## LinkedIn Post

At 9:28 AM PST on December 7th, 2021, AWS's engineers finished fixing the internal DNS errors they'd spent two hours chasing. The US-EAST-1 outage had five more hours to go.

Here's the sequence. At 7:30 AM, an automated job scaling capacity on a service inside AWS's main network triggered unexpected behavior from a large number of clients on AWS's internal network. Those clients opened a surge of connections that overwhelmed the networking devices sitting between the internal network and the main AWS network — the exact devices AWS had deliberately multiplied for redundancy.

The first symptom engineers saw wasn't a saturated network. It was elevated internal DNS errors. So that's what they fixed — two hours of work, moving internal DNS traffic off the congested paths, resolution fully restored by 9:28 AM. AWS's oldest joke about itself is that the root cause is always DNS. This time it wasn't. DNS was a casualty of the congestion, not the cause of it, and the outage kept running underneath the fix.

What made the real problem hard to see was that the congestion was eating the tools meant to diagnose it. Real-time monitoring for AWS's own operations teams degraded right along with everything else.

The Service Health Dashboard has a failover to a standby region for exactly this scenario. It didn't fire, because reaching that standby region also meant routing through the same congested internal network. AWS said so afterward, plainly: the congestion "impaired our Service Health Dashboard tooling from appropriately failing over to our standby region." The page built to tell customers what was broken was broken by the same cause.

Filing a support ticket about it didn't work either. The Support Contact Center runs on the same internal network, so customers couldn't open new cases for hours.

From there it cascaded outward — Route 53 API changes blocked, EC2 control-plane errors, STS, Connect, API Gateway, DynamoDB endpoints — each one waiting on the same link to clear. Recovery came in stages through the afternoon: EC2 error rates improving by 1:15 PM, full resolution landing around 4:44 PM.

Nobody misconfigured anything. The redundancy was real: multiple isolated networking devices, a standby-region failover, a separate support path. The gap was that the tools for seeing and reporting a network problem shared one dependency with the network itself. No one was wrong about how to build resilience. They just hadn't built resilience for their own resilience tooling.

#AWS #SystemDesign #DistributedSystems #Availability

**Character count: ~2,560 / 3,000 ✓**
**First 140 chars (mobile hook):** "At 9:28 AM PST on December 7th, 2021, AWS's engineers finished fixing the internal DNS errors they'd spent two hours chasing. The US-EAST-1 " ✓

---

## Twitter / X Thread

1/ Dec 7, 2021: AWS spent 2 hours fixing DNS errors during the US-EAST-1 outage. Fixing DNS didn't end it. It had 5 more hours to run.

2/ Real trigger: 7:30 AM PST, an automated scaling job on AWS's main network caused a connection surge from internal clients that saturated the devices bridging the internal and main networks.

3/ DNS errors were a symptom of that congestion, not the cause. Engineers chased the symptom first — usually a safe bet at AWS. Not this time.

4/ Worse: the congestion degraded AWS's own monitoring, and broke the Service Health Dashboard's failover to its standby region — because that failover routed through the same congested link. The status page couldn't report the outage it was living through.

5/ Even the Support Contact Center went down with it. For hours, customers couldn't open a ticket to ask what was wrong, because ticketing ran on the same internal network too.

6/ Route 53, EC2, STS, Connect, API Gateway, DynamoDB endpoints — all cascaded from the same choke point. EC2 errors improved by 1:15 PM. Full recovery: ~4:44 PM, about 9 hours after it started.

7/ The redundancy AWS built was real. It just didn't cover the tools built to watch the redundancy work.

---

## Diagram

See: `2026-09-13-aws-2021-network-congestion-dashboard-blind.excalidraw`

Type: Sequence/timeline flow (narrative style) — a horizontal event timeline with a dashed dead-end branch showing the two hours spent on the DNS misdiagnosis, and a callout band above showing the monitoring and status-page blindness running the whole time.
Color scheme: violet for the "blind spot" band (the monitoring/dashboard/support failure — not "bad," just invisible), amber for the DNS dead-end branch (wasted effort, not an error), slate for the main timeline, teal banner for the close. No red/green good-bad pairing.
Key screenshottable number: a ~9-hour outage with 2 of those hours spent fixing a problem — DNS — that turned out not to be the problem.
