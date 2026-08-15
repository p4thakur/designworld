<!-- sources -->
<!-- Primary: -->
<!--   Alexandra Noonan, "Goodbye Microservices: From 100s of problem children to 1 superstar," Segment -->
<!--   Engineering Blog — https://segment.com/blog/goodbye-microservices/ (also republished by Twilio after -->
<!--   the Segment acquisition: https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices). -->
<!--   Originally published 2018. Related talk by the same author: "To Microservices and Back Again." -->
<!--     — direct WebFetch of segment.com, www.twilio.com, web.archive.org, news.ycombinator.com, daily.dev, and -->
<!--     lukas.pustina.de all returned EGRESS_BLOCKED under this session's network policy (same class of -->
<!--     gateway-level denial noted on prior posts in this series). Facts below were cross-checked across -->
<!--     multiple independent web-search-result excerpts that directly quote or closely paraphrase the primary -->
<!--     Segment blog post, not written from memory. -->
<!-- Corroborating (independent secondary sources, cross-referenced for consistency): -->
<!--   Changelog.com, "Segment says goodbye microservices" — https://changelog.com/news/segment-says-goodbye-microservices-nnwW -->
<!--   Lukas Pustina, notes on "Goodbye Microservices: From 100s of problem children to 1 superstar" -->
<!--     https://lukas.pustina.de/notes/2018-07-17/goodbye-microservices:-from-100s-of-problem-children-to-1-superstar/ -->
<!--   Hacker News discussion thread on the original post — https://news.ycombinator.com/item?id=17499137 -->
<!--   InfoQ, "To Microservices and Back Again - Why Segment Went Back to a Monolith" (coverage of Alexandra -->
<!--     Noonan's related conference talk) — https://www.infoq.com/news/2020/04/microservices-back-again/ -->
<!--   daily.dev summary of the Segment blog post — https://daily.dev/posts/goodbye-microservices-uk1z3n0yv -->
<!-- Key verifiable details (cross-referenced across independent write-ups and discussion threads that quote/ -->
<!-- summarize Segment's own engineering blog post consistently): -->
<!-- 1. Segment's core product forwards each customer's analytics events to whichever third-party destinations -->
<!--   that customer has connected (Google Analytics, Mixpanel, and 140+ others). Originally, each destination -->
<!--   was its own microservice with its own queue, specifically for fault isolation: if one destination's API -->
<!--   stalled or went down, only that destination's queue backed up, and no other destination was affected. -->
<!-- 2. As the number of supported destinations grew past 100+, operational overhead scaled roughly linearly -->
<!--   with destination count — every new destination meant a new service, a new queue, and a new thing that -->
<!--   could page the on-call engineer, including for load spikes on small, low-traffic destinations. -->
<!-- 3. At its worst, 3 full-time engineers were spending most of their time just keeping the microservices -->
<!--   architecture alive rather than building new features. -->
<!-- 4. The fix: Centrifuge, a single router/aggregator that replaced every individual per-destination queue and -->
<!--   fed events into one monolithic service handling all 140+ destinations, with a shared worker pool that -->
<!--   absorbs load spikes across all destinations instead of a single narrow queue taking the full spike. -->
<!-- 5. Centrifuge took a full year and two of Segment's most senior engineers to build and get into production. -->
<!-- 6. To keep the resulting monolith testable at that scale, Segment built Traffic Recorder (built on top of -->
<!--   the yakbak library): it records each destination's real HTTP request/response once, then replays the -->
<!--   recorded response on every subsequent test run instead of hitting the live destination endpoint. After -->
<!--   integrating Traffic Recorder, running the full test suite across all 140+ destinations took milliseconds. -->
<!-- 7. The trade-off was deliberate and explicitly acknowledged in the post: fault isolation became harder — a -->
<!--   bug introduced in the code path for one destination can now crash the shared service for every other -->
<!--   destination too, the direct opposite of the original microservices design's guarantee. -->
<!-- 8. A few months after Centrifuge and the monolith were finished, two engineers were able to build an -->
<!--   entirely new destination delivery system in a matter of months — a project the old, per-destination -->
<!--   microservices architecture had made effectively impractical to attempt. -->
<!-- Author: Alexandra Noonan, Software Engineer, Segment. -->

# Segment Deleted 140 Microservices and Called It Progress

**Date:** 2026-08-15
**Company:** Segment (Twilio)
**Category:** microservices
**Post type:** confessional
**Opening style:** specific_number
**Slug:** segment-goodbye-microservices-monolith
**Character count (LinkedIn):** ~2290

---

## LinkedIn Post

Segment ran more than 140 microservices. Three of their best engineers spent most of their time just keeping the system alive.

It didn't start that way, and the original design wasn't wrong. Segment's product forwards every customer event to whatever analytics tools that customer has connected — Google Analytics, Mixpanel, dozens of others. Early on, each destination got its own service and its own queue. The logic was sound: if one destination's API stalled or went down, only that destination's queue backed up. Everyone else kept moving. Fault isolation, one service at a time.

The problem showed up as destinations kept multiplying. Every new integration meant a new service, a new queue, a new deploy pipeline, one more thing that could page someone at 2am. Operational overhead scaled 1:1 with the thing they were proudest of — how many destinations they supported. Small, low-traffic destinations paged on-call for load spikes just as often as the biggest ones. By 140+, three full-time engineers were spending most of their time on upkeep, not features.

The realization: isolating failures per destination was solving the right problem at the wrong scale. So they built Centrifuge — a single router that replaced every individual queue and fed all 140+ destinations into one monolithic service with a shared worker pool, absorbing spikes instead of paging one narrow queue at a time. It took a full year and their two most senior engineers to get it into production. To make a monolith testable at that size, they also built Traffic Recorder: it records each destination's real HTTP response once, then replays it locally on every later test run instead of hitting live APIs. The full 140+ destination suite dropped to milliseconds.

They gave something up on purpose: one buggy destination can now crash the service for everyone else, not just itself. A few months after Centrifuge shipped, two engineers built an entirely new delivery system in a matter of months — work the old architecture had made effectively unworkable.

Sometimes the right fix isn't optimizing the system you have. It's admitting the isolation you built is costing more than the failures it was meant to prevent.

Sources in comments.

#SystemDesign #Microservices #Segment #SoftwareArchitecture

---

## Twitter / X Version

1/ Segment ran more than 140 microservices. Three of their best engineers spent most of their time just keeping the system alive, not shipping features.

2/ It wasn't a bad design at first. Segment forwards customer events to whatever analytics tools a customer connects — GA, Mixpanel, dozens more. Each destination got its own service + queue: one API stalls, only its queue backs up. Clean fault isolation.

3/ The problem was growth. Every new destination = new service, new queue, new deploy, new pager. Ops overhead scaled 1:1 with the thing they were proudest of. Small, low-traffic destinations paged on-call as often as the big ones.

4/ The fix: Centrifuge. One router replaces every individual queue and feeds all 140+ destinations into a single monolith with a shared worker pool — spikes get absorbed by pooled capacity instead of paging one narrow queue.

5/ Cost: a full year, and their two most senior engineers, to get Centrifuge into production.

6/ To make a monolith testable at that scale, they built Traffic Recorder — records each destination's real HTTP response once, replays it on every later test run. Full 140+ destination suite: milliseconds.

7/ The trade they accepted on purpose: one buggy destination can now crash the service for every other destination too. That fault isolation is gone.

8/ A few months after Centrifuge shipped, two engineers built a brand-new delivery system in a matter of months — a project the old architecture had made effectively unworkable.

9/ Sometimes the right fix isn't optimizing the system you have. It's admitting the isolation you built is costing more than the failures it was meant to prevent.

---

## Excalidraw Diagram

**File:** 2026-08-15-segment-goodbye-microservices-monolith.excalidraw
**Type:** Horizontal timeline — five stages from the original fault-isolation design through the breaking point to the monolith rebuild, plus a footer callout on the trade-off Segment accepted deliberately.
**Color scheme:** Slate for the original microservices design (stage 1) — not "wrong," just a decision that made sense at the time. Amber for the growth tax (stage 2). Rose for the breaking point (stage 3), the most human-cost stage of the story. Violet for the rebuild, Centrifuge (stage 4). Teal for the testing win, Traffic Recorder (stage 5). Indigo for the footer's honest trade-off callout — deliberately not red/green, since the point of the post is that both architectures were reasonable trades, not a "bad old system, good new system" story.
**Screenshottable stat:** "140+ services, 3 engineers just keeping it alive → 1 monolith, full 140-destination test suite in milliseconds."

### Layout

```
Title: "Segment Deleted 140 Microservices and Called It Progress"
Subtitle: "Segment engineering blog — a fault-isolation architecture that became three engineers' full-time
job, and the monolith that replaced it"
Stat callout (rose): "140+ services, 3 engineers just keeping it alive → 1 monolith, full 140-destination
test suite in milliseconds"

[TIMELINE, 5 boxes left to right, connected by arrows]

STAGE 1 — FAULT ISOLATION [slate]
  "Segment forwards events to 140+ analytics tools (GA, Mixpanel, etc). Each destination gets its own
  service + queue. One stalls — only that queue backs up."
--arrow-->
STAGE 2 — THE GROWTH TAX [amber]
  "Every new destination = new service, new queue, new deploy, new pager. Ops overhead grows 1:1 with the
  thing they were proudest of: coverage."
--arrow-->
STAGE 3 — THE BREAKING POINT [rose]
  "140+ services running. 3 full-time engineers spend most of their time just keeping it alive. Small
  destinations page on-call as often as the biggest ones."
--arrow-->
STAGE 4 — THE REBUILD [violet]
  "Centrifuge: one router replaces every queue, feeds all destinations into one monolith with a shared
  worker pool. 1 year. Their 2 most senior engineers."
--arrow-->
STAGE 5 — TESTABLE AGAIN [teal]
  "Traffic Recorder records each destination's real HTTP response once, then replays it on every test.
  Full 140+ destination suite: milliseconds."

[FOOTER, indigo band, full width]
  "THE TRADE THEY ACCEPTED, ON PURPOSE — One buggy destination can now crash the service for every other
  destination too — the fault isolation they gave up, deliberately, to get here. A few months after
  Centrifuge shipped, two engineers built an entirely new delivery system in a matter of months — work the
  old, per-destination architecture had made effectively unworkable."
```
