---
date: 2026-09-04
company: LinkedIn
topic: Brooklin's partition assignment — how a system built to consolidate two brittle streaming pipelines grew its own cascading-rebalance problem
category: messaging
post_type: confessional
opening_style: cold_fact
slug: linkedin-brooklin-partition-rebalancing
---

## Sources

- LinkedIn Engineering Blog: ["Open sourcing Brooklin: Near real-time data streaming at scale"](https://engineering.linkedin.com/blog/2019/brooklin-open-source) (2019)
- LinkedIn Engineering Blog: ["Load-balanced Brooklin Mirror Maker: Replicating large-scale Kafka clusters at LinkedIn"](https://engineering.linkedin.com/blog/2022/load-balanced-brooklin-mirror-maker--replicating-large-scale-kaf) (2022)
- LinkedIn Engineering Blog: ["Streaming Data Pipelines with Brooklin"](https://engineering.linkedin.com/blog/2017/10/streaming-data-pipelines-with-brooklin) (2017)
- GitHub: [linkedin/brooklin Wiki — Kafka MirrorMaker Connector](https://github.com/linkedin/brooklin/wiki/Kafka-MirrorMaker-Connector)

**Key primary-source detail (not in most summaries):** The Brooklin MirrorMaker connector's flow-control thresholds are exact and asymmetric — it auto-pauses a partition once more than 5,000 messages are in flight unacknowledged, and only resumes once that backlog drops back under 1,000. That gap-on-purpose (pause at 5,000, resume at 1,000, not the same number) is a hysteresis band meant to stop a task from flapping pause/resume on every message. It's a small, specific engineering choice that only shows up in the connector's own wiki page, not in any summary of Brooklin.

**Note on sourcing:** `engineering.linkedin.com` was not reachable from this environment's network egress policy at write time. The rebalancing-cascade description and the "count partitions, not load" root cause come from consistent, near-identical phrasing surfaced across independent search-indexed excerpts of the 2022 LinkedIn Engineering post (cross-checked across two separate queries), rather than a single secondary summary. The flow-control threshold numbers (5,000 / 1,000) were verified directly against the reachable `github.com/linkedin/brooklin` wiki page, not inferred from search snippets.

---

## LinkedIn Post

LinkedIn's Brooklin moves more than seven trillion messages a day across Kafka clusters. For years, the thing deciding how to split that work across worker tasks was simple: count the partitions each task holds, keep the counts even.

Brooklin itself was already a fix. LinkedIn used to run two separate systems for moving data around — Databus for change capture out of Espresso and Oracle, and Kafka MirrorMaker for replicating clusters across data centers. Starting in 2016, Brooklin replaced both with one general-purpose streaming service any team could plug into, complete with real guardrails: its MirrorMaker connector caps how far a task can get ahead of itself, auto-pausing a partition once more than 5,000 messages are in flight unacknowledged, and only resuming once that backlog drops back under 1,000.

The one thing the guardrails didn't cover was which task got which partition in the first place. Partition count isn't partition load — some topics run hot, some sit nearly idle — and the original assignment strategy only knew how to count. At LinkedIn's scale, that gap became a failure mode with its own momentum: uneven load meant some tasks fell behind, delivery latency spiked, a monitor built to watch for exactly that spike fired a rebalance, and if the destination cluster was already under strain, that rebalance could trigger another one behind it. A system built to smooth over cluster trouble was, under the wrong conditions, amplifying it.

The fix wasn't more capacity. It was teaching the assignment strategy to look at actual per-partition throughput, estimate how many tasks the real traffic needed, keep hot partitions off the same task, and hold assignments sticky so one local hiccup didn't cascade into a full reshuffle.

Brooklin's first job was consolidating two brittle systems into one. Its second job, years later, was admitting that consolidation had just moved the brittleness down a level — from "which system moves this data" to "which task inside Brooklin gets the busy partition." The scaling problem doesn't disappear. It changes address.

#SystemDesign #LinkedIn #Kafka #DistributedSystems

**Character count: ~2,148 / 3,000 ✓**
**First 140 chars (mobile hook):** "LinkedIn's Brooklin moves more than seven trillion messages a day across Kafka clusters. For years, the thing deciding how to split th" ✓

---

## Twitter / X Thread

1/ LinkedIn's Brooklin moves 7+ trillion messages a day across Kafka clusters. For years it split that work across tasks by counting partitions. Not by how busy they were.

2/ Brooklin already replaced two brittle systems — Databus (change capture) and Kafka MirrorMaker (cross-cluster replication) — with one streaming service, starting in 2016. Its MirrorMaker connector auto-pauses a partition at 5,000 unacked messages in flight, resumes under 1,000.

3/ What it didn't get right at first: partition count ≠ partition load. Some topics run hot, some sit idle. The original strategy balanced the numbers, not the traffic.

4/ At scale that became a feedback loop: uneven load → latency spike → monitor fires a rebalance → if the destination cluster is already struggling, that rebalance triggers another one. The system built to fix cluster trouble was amplifying it.

5/ The real fix: assign partitions by measured throughput, not count. Estimate tasks needed from real metrics, keep hot partitions apart, hold assignments sticky so local hiccups don't cascade.

6/ Brooklin's first job was consolidating two systems into one. Its second job was realizing that just moved the brittleness one layer down.

---

## Diagram

See: `2026-09-04-linkedin-brooklin-partition-rebalancing.excalidraw`

Type: Timeline (confessional style, 4 stages)
Color scheme: Slate (the old, fragmented world) → Teal (Brooklin's original fix) → Amber (the cascade it grew) → Green (the 2022 load-aware fix) — no red/green good-bad coding
Key screenshottable number: 7+ trillion messages/day, and the 5,000-in / 1,000-out flow-control hysteresis band
