<!-- sources -->
<!-- Primary: -->
<!--   Netflix TechBlog, "A Closer Look at the Christmas Eve Outage" -->
<!--   https://netflixtechblog.com/a-closer-look-at-the-christmas-eve-outage-d7b409a529ee -->
<!--   Netflix TechBlog, "Active-Active for Multi-Regional Resiliency" (Ruslan Meshenberg, Naresh Gopalani, -->
<!--   Luke Kosewski) -->
<!--   http://techblog.netflix.com/2013/12/active-active-for-multi-regional.html -->
<!--   Netflix TechBlog, "Chaos Engineering Upgraded" (introduces Chaos Kong) -->
<!--   http://techblog.netflix.com/2015/09/chaos-engineering-upgraded.html -->
<!--     — direct WebFetch of netflixtechblog.com and techblog.netflix.com both returned EGRESS_BLOCKED under -->
<!--     this session's network policy (same class of gateway-level denial noted on the prior Slack and -->
<!--     Honeycomb posts in this series). Facts below were cross-checked across multiple independent -->
<!--     web-search-result excerpts that directly quote or closely paraphrase Netflix's own engineering blog -->
<!--     posts and a Netflix engineer's own conference talk, not written from memory. -->
<!-- Corroborating (independent secondary sources, cross-referenced for consistency): -->
<!--   Amjith Ramanujam (Netflix traffic/resilience engineer), "How Netflix does failovers in 7 minutes flat," -->
<!--   PyCon 2018 talk, summarized by Opensource.com -->
<!--   https://opensource.com/article/18/4/how-netflix-does-failovers-7-minutes-flat -->
<!--   https://us.pycon.org/2018/schedule/presentation/95/ -->
<!--   GitHub mirror of an independent postmortem writeup of the Dec 24 2012 incident -->
<!--   https://github.com/Operations-Incident-Board/Postmortem-Report-Reviews/blob/master/2016-03-14-gabinante-netflix-streaming-2012-12-24.md -->
<!--   GeekWire, "Netflix nightmare explained: Amazon apologizes for outage" -->
<!--   https://www.geekwire.com/2013/netflix-nightmare-amazon-explains-christmas-eve-outage-issues-apology/ -->
<!--   iTnews, "Netflix flicks to active-active operations" -->
<!--   https://www.itnews.com.au/news/netflix-flicks-to-active-active-operations-364302 -->
<!-- Key verifiable details (cross-referenced across independent search excerpts that quote/summarize -->
<!-- Netflix's own engineering blog posts and talks consistently): -->
<!-- 1. On December 24, 2012, at 12:24pm Pacific, an AWS engineer ran a maintenance process against -->
<!--   production Elastic Load Balancer state data by mistake, wiping state from a handful of Netflix's -->
<!--   hundreds of ELBs in AWS's US-EAST-1 region. -->
<!-- 2. AWS did not fully diagnose the cause for hours; the incident was not resolved until roughly 5:40am -->
<!--   the next morning — about seventeen hours after the first failures — leaving Netflix streaming broken -->
<!--   for large parts of Christmas Eve across the US, Canada, and Latin America. -->
<!-- 3. At the time, Netflix's entire service ran out of a single AWS region, so there was no healthy region -->
<!--   to shift traffic to. -->
<!-- 4. Netflix's response, detailed in "Active-Active for Multi-Regional Resiliency" (2013), was to run the -->
<!--   full service simultaneously live in more than one AWS region (eventually three: US-EAST-1, US-WEST-2, -->
<!--   EU-WEST-1) rather than keep a passive standby region, so any single region could absorb the others' -->
<!--   traffic without a cold start. -->
<!-- 5. To validate that failover path continuously, Netflix built Chaos Kong: a chaos-engineering tool that -->
<!--   deliberately takes an entire AWS region out of service in production, on a regular cadence, with real -->
<!--   customer traffic being rerouted live. -->
<!-- 6. Per the PyCon 2018 talk, a fully manual regional failover used to take roughly 45 minutes, with about -->
<!--   35 of those minutes spent simply waiting for the healthy region to scale up capacity. -->
<!-- 7. By 2018, Netflix's automated failover system completed a full regional evacuation in about 7 minutes, -->
<!--   using pre-scaled "shadow clusters" already running (but not serving) in the healthy region so there is -->
<!--   no scale-up wait, and DNS changes reroute users away from the failed region. -->
<!-- 8. Netflix tracks failure using a business metric built for this purpose — Stream Starts Per Second (SPS), -->
<!--   i.e. whether customers can actually start playback — rather than relying on infrastructure metrics alone. -->
<!-- 9. The failover orchestration software itself is written in Python and maintained by a small team -->
<!--   (reported as three engineers), notable because the great majority of Netflix's stack runs on the JVM. -->
<!-- Publication: Netflix Technology Blog (netflixtechblog.com / techblog.netflix.com), "A Closer Look at the -->
<!-- Christmas Eve Outage" (2012/2013) and "Active-Active for Multi-Regional Resiliency" (December 2013), -->
<!-- corroborated by a Netflix engineer's own 2018 PyCon talk on the resulting failover system. -->

# Netflix Broke on Christmas Eve 2012. So It Built a Machine to Break Itself on Purpose.

**Date:** 2026-08-29
**Company:** Netflix
**Category:** availability
**Post type:** structured
**Opening style:** cold_fact
**Slug:** netflix-active-active-region-failover
**Character count (LinkedIn):** ~2130

---

## LinkedIn Post

At 12:24 PM on December 24, 2012, an AWS engineer ran a maintenance process against the wrong production data and wiped the state out of a handful of Elastic Load Balancers. Netflix streaming broke for Christmas Eve across the US, Canada, and Latin America. AWS didn't fully understand the cause for hours. The fix didn't land until 5:40 AM the next morning — seventeen hours after the first drop.

Netflix ran everything out of one AWS region: US-EAST-1. When that region had a bad day, there was nowhere else for traffic to go.

The obvious fix is "add a backup region." Netflix's actual fix was harder: run the full service, live, in more than one region simultaneously — Active-Active — so every region already carries real production traffic and can absorb the others' load without a cold start.

But a failover path nobody has exercised recently is a hypothesis, not a plan. So Netflix built Chaos Kong: a tool that kills an entire AWS region, on purpose, in production, on a regular cadence, with real customers watching in real time. If it ever surfaces a gap, that's a bug found on Netflix's schedule, not on the next AWS outage's.

The results are specific. A manual regional failover used to take about 45 minutes, and 35 of those minutes were just waiting for the healthy region to scale up. Automated failover today takes 7 minutes flat, because the healthy region already runs "shadow clusters" pre-scaled and idle — no scale-up wait to eat. Failure gets caught not by an infra dashboard first, but by a business metric built for exactly this: Stream Starts Per Second, tracking whether people can actually press play. The orchestration code behind all of it runs in Python, at a company built almost entirely on Java, maintained by a team of three engineers.

None of the original 2012 design was incompetent. Single-region, multi-AZ was the right call for the traffic and the era. What it was missing wasn't more infrastructure. It was a habit of finding out, before Christmas Eve does it for you, whether the emergency path actually works.

#SystemDesign #DistributedSystems #Availability #ChaosEngineering

---

## Twitter / X Version

1/ At 12:24 PM on December 24, 2012, an AWS engineer wiped state data off a handful of production load balancers. Netflix broke for Christmas Eve. AWS didn't fix it until 5:40 AM the next day — 17 hours later.

2/ The real problem: Netflix ran its entire service out of one AWS region. One bad region, one bad Netflix.

3/ The obvious fix: add a backup region. What Netflix actually built was harder — Active-Active, running full production traffic live in multiple regions at once, so any one can absorb the others' load without warming up first.

4/ But an untested failover path is a hypothesis. So Netflix built Chaos Kong — a tool that kills an entire AWS region on purpose, in production, on a schedule, with real customers on it.

5/ The payoff is measurable: manual failover used to take ~45 minutes, 35 of them just waiting for scale-up. Automated failover today: 7 minutes flat, because the healthy region already runs pre-scaled "shadow clusters."

6/ Failure gets caught by a business metric — Stream Starts Per Second — not just infra dashboards. And the failover orchestration runs in Python, at a company built on Java, maintained by three engineers.

7/ 2012's design wasn't wrong for its time. It just hadn't been tested against the thing that eventually happened. Netflix's fix was making that test routine, not rare.

---

## Excalidraw Diagram

**File:** 2026-08-29-netflix-active-active-region-failover.excalidraw
**Type:** Horizontal migration timeline — four linked stages left to right (outage → decision → validation →
result), matching the Structured Case Study's recommended before/after/timeline layout, closed out by a
stats band and a principle band.
**Color scheme:** Red for the 2012 outage, blue for the Active-Active decision, purple for Chaos Kong's
ongoing validation, green for the measured result — a four-color set distinct from the slate/rose/cyan/amber
run on the prior messaging post and the amber/indigo/teal/violet run on the prior storage post.
**Screenshottable stat:** "Manual failover: ~45 min (35 min just waiting to scale up). Automated failover
today: 7 minutes flat — via pre-scaled shadow clusters, detected by Stream Starts Per Second, orchestrated
in Python at a company built on Java."

### Layout

```
Title: "Netflix Broke on Christmas Eve 2012. So It Built a Machine to Break Itself on Purpose."

[DEC 24, 2012 — ONE REGION, x 40-320, red]      ->      [THE FIX: ACTIVE-ACTIVE, x 355-635, blue]      ->      [THE PROOF: CHAOS KONG, x 670-950, purple]      ->      [THE RESULT, x 985-1265, green]
"An AWS engineer wipes                                  "Not a cold backup region.                             "An untested failover path                              "Manual failover: ~45 min,
state data off a handful                                Every region runs live                                 is a hypothesis. Netflix                               35 of them waiting for
of ELBs at 12:24 PM.                                    production traffic at once,                            built a tool that kills an                              scale-up. Automated
Netflix breaks for                                      so any region can absorb                                entire AWS region on                                   failover now: 7 minutes
Christmas Eve. Fix doesn't                              the others' load without a                              purpose, in production, on                             flat, via pre-scaled
land until 5:40 AM — 17                                 cold start."                                           a schedule — with real                                  'shadow clusters' in the
hours later. Everything ran                                                                                     customers on it."                                       healthy region."
in one AWS region:
US-EAST-1."

[DETECTION + OWNERSHIP BAND, full width, slate]
"Failure is caught by a business metric built for this — Stream Starts Per Second, whether people can
actually press play — not an infra dashboard first. The failover orchestration itself runs in Python, at a
company built almost entirely on Java, maintained by a team of three engineers."

[PRINCIPLE BAND, full width, amber]
"2012's single-region design wasn't incompetent — it fit the traffic and the era. What it lacked wasn't more
infrastructure. It was the habit of finding out, before Christmas Eve does it for you, whether the emergency
path actually works."
```
