<!-- sources -->
<!-- Primary: -->
<!--   Slack Engineering blog, "Scaling Slack's Job Queue" -->
<!--   https://slack.engineering/scaling-slacks-job-queue/ -->
<!--     — direct WebFetch of slack.engineering and its Medium mirror both returned EGRESS_BLOCKED under -->
<!--     this session's network policy (same class of gateway-level denial noted on the prior Honeycomb post -->
<!--     in this series). Facts below were cross-checked across multiple independent web-search-result -->
<!--     excerpts that directly quote or closely paraphrase Slack's own engineering blog post, not written -->
<!--     from memory. -->
<!-- Corroborating (independent secondary sources, cross-referenced for consistency): -->
<!--   Medium mirror (Several People Are Coding), "Scaling Slack's Job Queue" -->
<!--   https://medium.com/several-people-are-coding/scaling-slacks-job-queue-687222e9d100 -->
<!--   Hello Interview, "How Slack Put Kafka in Front of Its Redis Job Queue" -->
<!--   https://www.hellointerview.com/learn/system-design/in-the-wild/slack-job-queue -->
<!--   Quastor, "How Slack Processes 33,000 Jobs per Second" -->
<!--   https://blog.quastor.org/p/slack-processes-33000-jobs-per-second -->
<!--   zahere.com / Adaptive Engineer newsletter, "Why Slack Redesigned Their Job Queue" -->
<!--   https://zahere.com/why-slack-redesigned-their-job-queue -->
<!--   https://newsletter.adaptiveengineer.com/p/why-slack-redesigned-their-job-queue -->
<!--   GOTO Blog mirror listing of the original slack.engineering post -->
<!--   https://blog.gotocon.com/2017/12/20/slack-engineering-scaling-slacks-job-queue-several-people-are-coding/ -->
<!--   Suman Karumuri (Slack engineer), LinkedIn post linking to the Kafka-at-Slack writeup -->
<!--   https://www.linkedin.com/posts/mansu_a-good-summary-of-the-work-we-did-on-kafka-activity-7069426641571086336-9AGV -->
<!-- Key verifiable details (cross-referenced across independent search excerpts that quote/summarize -->
<!-- Slack's own engineering blog post consistently): -->
<!-- 1. Slack's original job queue was Redis-only: app servers enqueued jobs (link unfurls, notifications, -->
<!--   security checks) directly into Redis hosts chosen by job type/arguments; workers polled Redis and -->
<!--   dequeued; a handler did ID-based dedup, discarding a request if an identical job ID was already queued. -->
<!-- 2. In 2016, a slowdown in the database layer cascaded into slower job execution. Workers drained the -->
<!--   queue slower than app servers filled it, and Redis climbed to its configured maximum memory limit. -->
<!-- 3. The counterintuitive failure: once Redis had no free memory, Slack could not enqueue new jobs (expected) -->
<!--   AND could not dequeue existing ones either, because removing a job from Redis requires moving it into a -->
<!--   processing list first, which itself needs a sliver of free memory. With zero memory free, dequeue -->
<!--   stalled too — the queue was locked in both directions and needed manual intervention to recover. -->
<!-- 4. Every Slack feature riding on the job queue (notifications, unfurls, security checks) went down with it. -->
<!-- 5. At peak, Slack was processing up to 1.4 billion jobs a day, roughly 33,000 jobs per second. -->
<!-- 6. The fix was not replacing Redis — it was putting Kafka in front of it as a durable buffer, while -->
<!--   leaving the existing application enqueue/dequeue interfaces in place. -->
<!-- 7. Kafkagate: a new stateless Go service exposing a single HTTP POST interface (topic, partition, -->
<!--   content) that relays the request into Kafka using the Sarama Go driver. -->
<!-- 8. JQRelay: a stateless service that relays jobs from a Kafka topic back into Redis, with exactly one -->
<!--   relay process assigned per topic and self-healing reassignment if that process fails. -->
<!-- 9. Kafkagate acknowledges a write once the partition leader has it, not once it has replicated to other -->
<!--   replicas — minimizing enqueue latency at the cost of a small window where a leader failure before -->
<!--   replication could lose the job. -->
<!-- Publication: Slack Engineering blog (slack.engineering), "Scaling Slack's Job Queue," originally -->
<!-- published December 2017, corroborated by independent technical summaries and a Slack engineer's own -->
<!-- link-share of the underlying Kafka work. -->

# Slack's Job Queue Could Take Jobs In. In 2016, It Also Stopped Letting Them Out.

**Date:** 2026-08-28
**Company:** Slack
**Category:** messaging
**Post type:** narrative
**Opening style:** mid_scene
**Slug:** slack-kafkagate-redis-job-queue
**Character count (LinkedIn):** ~2424

---

## LinkedIn Post

Slack's job queue locked up in 2016. Not because it couldn't accept new jobs — because it couldn't get rid of old ones either.

The original design was simple. App servers enqueued jobs straight into Redis — unfurling a link, sending a notification, running a security check, each became a job, routed to a Redis host by job type. Workers polled Redis and dequeued. A bit of ID-based dedup kept duplicates out. Redis held the whole backlog, bookkeeping included. It had held it fine for years.

Then a slowdown in the database layer rippled sideways into job execution. Workers drained the queue slower than app servers filled it, and Redis climbed toward its configured memory ceiling.

Everyone expects what happens next: Redis fills up, enqueue fails. What's easy to miss is the second failure hiding right behind it. Dequeuing a job from Redis isn't free either — it has to move that job into a processing list before it can delete it from the backlog, and that move needs a sliver of memory too. With zero memory free, dequeue stalled right alongside enqueue. The queue wasn't backed up. It was sealed shut in both directions, and every feature riding on it — notifications, unfurls, security checks — went down with it until someone intervened by hand.

The fix wasn't replacing Redis. It was refusing to let Redis be the only place a job could survive. Slack put Kafka in front of it as a durable buffer. Kafkagate, a small stateless Go service, exposes one HTTP POST endpoint — topic, partition, payload — and relays straight into Kafka over the Sarama client. JQRelay drains Kafka back into Redis, one relay process per topic, self-healing if that process dies. Redis kept doing what it was good at, dispatching jobs to workers. It just stopped being the only copy.

That fix carries its own trade. Kafkagate acknowledges a job once the partition leader has it, not once it's replicated — faster, with a small window where a leader failure before replication loses a job. At 33,000 jobs a second, Slack wasn't choosing between risk and no risk. Just which risk, and how much of it, for how much speed.

No part of the original design was wrong. Redis-only was fine at 2013's traffic, and fine again the moment before the outage. What broke wasn't a component. It was an assumption baked into the interface — that dequeuing would always find the memory it needed.

#SystemDesign #DistributedSystems #Messaging #Kafka

---

## Twitter / X Version

1/ Slack's job queue locked up in 2016. Not because it couldn't take new jobs in. Because it couldn't get rid of old ones either.

2/ The setup: app servers enqueued jobs — link unfurls, notifications, security checks — straight into Redis. Workers polled and drained it. Worked fine for years.

3/ A database slowdown rippled into job execution. Workers fell behind. Redis climbed toward its memory ceiling — then hit it.

4/ Everyone expects enqueue to fail there. What's missed: dequeue needs a sliver of free memory too, to move a job into a processing list before deleting it. Zero memory free = dequeue stalls too. Sealed shut, both directions.

5/ Every feature riding on that queue — notifications, unfurls, security checks — went down with it. Recovery took manual intervention, not just waiting out the database.

6/ Fix wasn't replacing Redis. It was refusing to let Redis be the only copy. Kafka went in front as a durable buffer. Kafkagate (Go, one HTTP POST endpoint) relays into Kafka; JQRelay drains it back into Redis, one process per topic, self-healing.

7/ Even the fix has a trade: Kafkagate acks on leader-write, not full replication. Faster, with a small loss window if that leader dies first. At 33K jobs/sec, that's not risk vs. no risk. Just which risk.

---

## Excalidraw Diagram

**File:** 2026-08-28-slack-kafkagate-redis-job-queue.excalidraw
**Type:** Sequence flow shown twice (before/after), with the failure point isolated as its own highlighted
row in between — matching the Narrative post type's recommended layout of tracing how a request moves
through the system and calling out exactly where it breaks.
**Color scheme:** Slate for the original Redis-only flow (not "wrong," just the design that fit 2013's
traffic), rose for the 2016 lockup row, cyan for the Kafka-buffered flow that replaced it, amber for the
closing tradeoff band — a four-color set distinct from the amber/indigo/teal/violet run on the prior storage
post and the blue/orange/green/gray run on the prior database post.
**Screenshottable stat:** "Redis at 0 free memory: enqueue fails (expected) AND dequeue fails (the surprise —
moving a job to the processing list needs memory too). 1.4B jobs/day, 33,000/sec at peak. Fix: Kafka in
front of Redis, not instead of it."

### Layout

```
Title: "Slack's Job Queue Could Take Jobs In. In 2016, It Also Stopped Letting Them Out."

Section label: "BEFORE 2016 — REDIS IS THE ONLY COPY OF THE QUEUE" (slate)

[APP SERVERS, x 60-410, slate]      ->      [REDIS — BACKLOG + DISPATCH, x 440-790, slate]      ->      [WORKER POOL, x 820-1170, slate]
"Unfurl a link, send a                      "One store holds the whole backlog                          "Workers poll Redis, dequeue
notification, run a security                and the dispatch bookkeeping.                               a job, execute it. Simple
check — each becomes a job.                 ID-based dedup keeps duplicates                             loop — as long as dequeue
App servers enqueue it straight             out. Worked fine for years."                                always finds the memory
into Redis, picked by job type."                                                                        it needs."

Section label: "2016 — THE DOUBLE LOCKUP" (rose)

[ENQUEUE FAILS (expected), x 60-580, rose]                          [DEQUEUE ALSO FAILS (the surprise), x 620-1140, rose]
"A slowdown in the database layer ripples                            "Removing a job isn't free either — Redis must move it
into job execution. Workers fall behind.                             into a processing list before deleting it from the
Redis climbs to its configured memory                                backlog. That move needs memory too. At zero free,
ceiling — new jobs can't get in."                                    dequeue stalls right alongside enqueue."

[RESULT BAND, rose, full width]
"The queue is sealed shut in both directions. Notifications, link unfurls, and security checks all go down
with it — recovery needs manual intervention, not just waiting out the database slowdown."

Section label: "AFTER — KAFKA AS A DURABLE BUFFER, NOT A REDIS REPLACEMENT" (cyan)

[KAFKAGATE, x 60-410, cyan]                 ->      [KAFKA — DURABLE BUFFER, x 440-790, cyan]           ->      [JQRELAY -> REDIS -> WORKERS, x 820-1170, cyan]
"Stateless Go service. One HTTP                     "Jobs land here first now, not                              "One relay process per Kafka
POST endpoint — topic, partition,                   Redis. A slow drain no longer                               topic, self-healing if it dies,
payload — relayed into Kafka over                   means a full backlog with                                   drains jobs back into Redis
the Sarama client."                                 nowhere to go."                                             for workers to dequeue as
                                                                                                                  before."

[FOOTER, amber band, full width]
"THE TRADEOFF THE FIX DIDN'T ERASE: Kafkagate acknowledges a job once the partition leader has it — not once
it's replicated. Faster relay, with a small window where a leader failure before replication loses the job.
At 33,000 jobs a second, Slack wasn't choosing between risk and no risk. Just which risk, and how much of
it, for how much speed."
```
