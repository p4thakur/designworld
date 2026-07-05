<!-- sources -->
<!-- Primary: AWS, "Summary of the Amazon S3 Service Disruption in the Northern Virginia (US-EAST-1) Region" (Feb 28, 2017) -->
<!-- URL: https://aws.amazon.com/message/41926/ -->
<!-- Note: direct fetch of aws.amazon.com/message/41926/ returned HTTP 403 under this session's egress policy; -->
<!-- facts and figures below are cross-checked across multiple independent search-result excerpts quoting the -->
<!-- primary AWS postmortem directly (exact phrasing on the index/placement subsystems and the safety-check delay -->
<!-- matched verbatim across sources), rather than a single full-text fetch. -->
<!-- Corroborating (cross-checked, consistent on figures below): -->
<!--   https://www.gremlin.com/blog/the-2017-amazon-s-3-outage -->
<!--   https://www.datacenterknowledge.com/outages/aws-outage-that-broke-the-internet-caused-by-mistyped-command -->
<!--   https://www.networkworld.com/article/960912/read-the-full-text-of-amazons-post-mortem-from-its-s3-cloud-brownout.html -->
<!--   https://www.npr.org/sections/thetwo-way/2017/03/03/518322734/amazon-and-the-150-million-typo -->
<!--   https://www.axios.com/2017/12/15/amazon-outage-cost-sp-500-companies-150m-1513300728 -->
<!--   https://www.theregister.com/2017/03/02/aws_s3_meltdown/ -->
<!--   https://www.csoonline.com/article/560421/aws-says-a-typo-caused-the-massive-s3-failure-this-week.html -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Feb 28, 2017, 9:37 AM PST: an authorized S3 team member, using an established playbook, executed a command -->
<!--    to remove a small number of servers supporting the S3 billing subsystem in US-EAST-1; one input parameter -->
<!--    was entered incorrectly, removing a much larger set of servers than intended -->
<!-- 2. Two subsystems went down as a result: the index subsystem (tracks metadata/location for every S3 object in -->
<!--    the region; required for all GET/LIST/PUT/DELETE requests) and the placement subsystem (allocates storage -->
<!--    for new objects) -->
<!-- 3. Neither subsystem had been fully restarted in US-EAST-1 (one of the largest regions) in several years; the -->
<!--    restart plus the safety checks needed to validate metadata integrity before serving traffic again "took -->
<!--    longer than expected" -->
<!-- 4. AWS's own Service Health Dashboard was itself hosted on assets served from S3 in the same affected region, -->
<!--    so it could not be updated for roughly the first two hours of the ~4-hour incident -->
<!-- 5. Total outage duration was approximately four hours (from 9:37 AM PST to just before 2 PM PST) -->
<!-- 6. Affected services/sites included Quora, Medium, Slack, Trello, Docker, Imgur, GitHub, Expedia, Coursera, and -->
<!-- 6. the SEC's EDGAR filings system, among many others relying on S3 in US-EAST-1 -->
<!-- 7. Cyence, a cyber-risk modeling firm, estimated S&P 500 companies alone lost about $150 million from the outage -->
<!-- 8. AWS's remediation: modified the capacity-removal tooling to remove server capacity more slowly, added a -->
<!--    safeguard preventing removal below a subsystem's minimum required capacity, and made the Service Health -->
<!--    Dashboard run across multiple AWS regions instead of depending on a single one -->

# AWS S3, February 28, 2017: The Playbook That Worked Until It Didn't

**Date:** 2026-07-05
**Company:** Amazon (AWS)
**Category:** storage
**Post type:** narrative
**Opening style:** mid_scene
**Slug:** aws-s3-2017-typo-outage
**Character count (LinkedIn):** ~2,246

---

## LinkedIn Post

9:37 AM Pacific, February 28, 2017. An Amazon engineer runs a command they've run before — a routine playbook, taking a small number of servers offline to debug the S3 billing system. One of the inputs is off. Instead of a handful of servers, a much larger set drops out of Amazon S3, US-EAST-1.

Two subsystems go down with them. The index subsystem, which tracks the metadata and location of every object in the region — required for every GET, LIST, PUT, and DELETE. And the placement subsystem, which allocates space for new objects. Without them, S3 in the busiest AWS region stops answering requests. Half the internet's "storage" quietly depends on a service most of its users have never heard of.

Recovery should have been routine — remove capacity, add it back. Except neither subsystem had been fully restarted in years, not at this scale. Restarting meant re-running the safety checks that validate the integrity of the metadata before serving traffic again. Nobody had timed how long that would take at US-EAST-1's actual size, because nobody had needed to find out.

While engineers worked the incident, customers went looking for AWS's own status page. It couldn't update. The dashboard's icons and assets were served from — S3, in the same region that had just gone dark. AWS was down, and the page that says AWS is down was down too.

Four hours later, S3 was fully restored. Quora, Medium, Slack, Trello, Docker, Imgur, GitHub, even the SEC's filing system had spent the afternoon degraded or dark. Cyence, which models cyber-risk losses, later put the hit to S&P 500 companies alone at $150 million — from one mistyped parameter.

AWS's fix wasn't a smarter engineer. It was slower tooling: the capacity-removal tool now removes servers gradually and refuses to take any subsystem below its minimum safe capacity. The status dashboard now runs across multiple regions, independent of any single one going dark.

No one broke a rule that day. The engineer followed the playbook. The playbook had worked for years. The failure mode that mattered wasn't in the code — it was in a system so reliable that no one had rehearsed what a full restart of its core subsystems would actually cost.

#SystemDesign #Storage #AWS #Engineering

---

## Twitter / X Version

1/ 9:37 AM Pacific, Feb 28, 2017. An AWS engineer runs a routine playbook command to debug S3's billing system — take a few servers offline. One input is off. A much larger chunk of Amazon S3 in US-EAST-1 goes down with them.

2/ The two subsystems that dropped: the index (metadata + location for every object — needed for every GET/LIST/PUT/DELETE) and placement (allocates space for new objects). Without them, S3 in AWS's busiest region just stops answering.

3/ Should've been a quick fix. Except neither subsystem had been fully restarted in years, at this scale. Restart meant re-running safety checks on the metadata first. Nobody knew how long that would actually take, because nobody had needed to find out.

4/ Meanwhile customers checked AWS's own status page for updates. It couldn't load — its assets were served from S3, in the same dead region. AWS was down, and the "AWS is down" page was down with it.

5/ Four hours later: fully restored. Quora, Medium, Slack, Trello, Docker, GitHub, even the SEC's filings system had spent the afternoon degraded. Cyence estimated the S&P 500 alone lost $150M — from one mistyped parameter.

6/ The fix: slower tooling, not a smarter engineer. Capacity now gets removed gradually, with a floor per subsystem. The status dashboard now runs across regions. No one broke a rule — the playbook had worked for years. The system was just more reliable than anyone had rehearsed for.

---

## Excalidraw Diagram

**File:** 2026-07-05-aws-s3-2017-typo-outage.excalidraw
**Type:** Sequence flow with a highlighted crash window (narrative)
**Color scheme:** Slate for the routine command (not a mistake yet), amber for the typo itself, crimson for the crash window (the one place red is earned — this is the actual failure), violet for the status-dashboard blind spot, teal for the fix. No red/green good/bad pairing beyond the single crimson box.
**Screenshottable stat:** "9:37 AM typo → ~4 hours down → status page itself went blind → $150M in S&P 500 losses"

### Layout

```
Title: "AWS S3, February 28, 2017: The Playbook That Worked Until It Didn't"
Subtitle: "9:37 AM PST typo → ~4 hours down → AWS's own status page couldn't load → ~$150M in S&P 500 losses (Cyence)"

[9:37 AM PST]          [THE TYPO]              [INDEX + PLACEMENT DOWN]           [BLIND SPOT]              [~4 HOURS LATER]
Engineer runs a        One input is wrong.     Metadata/location (index) and      AWS's own status          S3 fully restored.
playbook command       Far more servers than   new-storage allocation             dashboard is served        Capacity tool now
to debug S3's          intended come out       (placement) subsystems fail.       from S3 — in the           removes servers
billing system.        of US-EAST-1.           Neither fully restarted in         same dead region.          slower, with a
Removes a few                                  years — safety checks on           Can't update for           safety floor. Status
servers.                                        metadata integrity take            ~2 hours.                  dashboard now spans
                                                longer than anyone expected.                                   multiple regions.

Footnote: Quora, Medium, Slack, Trello, Docker, Imgur, GitHub, and the SEC's filings system all spent the
afternoon degraded or dark. Cyence estimated S&P 500 companies alone lost $150M — from one mistyped parameter.

Timeline: 9:37 AM playbook command -> typo removes too many servers -> index & placement subsystems down
          -> status dashboard blind for ~2 hrs -> S3 fully restored ~4 hrs later
```
