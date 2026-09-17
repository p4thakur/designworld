---
date: 2026-09-17
company: Pinterest
topic: Pinterest runs Kafka across 3,000+ brokers, where a broker dying is a weekly (sometimes daily) event — for years a human hand-wrote the partition reassignment file at 3am; in 2017 they automated it with DoctorKafka, then found that automated leader-balancing modeled as a max-flow graph problem could hit near-perfect balance while proposing far more partition moves than necessary, requiring a "shared residue" mechanism to stop it over-working the problem
category: messaging
post_type: narrative
opening_style: mid_scene
slug: pinterest-doctorkafka-broker-autohealing
---

## Sources

- Pinterest Engineering Blog (Medium): ["Open sourcing DoctorKafka: Kafka cluster healing and workload balancing"](https://medium.com/pinterest-engineering/open-sourcing-doctorkafka-kafka-cluster-healing-and-workload-balancing-e51ad25b6b17) — primary source for the manual reassignment process, the 2017 open-sourcing, and the "broker failures every week, sometimes multiple times a day" framing.
- Pinterest Engineering Blog (Medium): ["Using graph algorithms to optimize Kafka operations, Part 1"](https://medium.com/pinterest-engineering/using-graph-algorithms-to-optimize-kafka-operations-part-1-abbabd606a25) and [Part 2](https://medium.com/@Pinterest_Engineering/using-graph-algorithms-to-optimize-kafka-operations-part-2-c970d9c08c7d) — primary source for the max-flow leader-balancing approach, the finding that a naive flow solution over-proposes reassignments relative to the theoretical minimum, and the "shared residue" fix.
- Pinterest Engineering Blog, also syndicated via [Confluent](https://www.confluent.io/blog/running-kafka-at-scale-at-pinterest/): "How Pinterest Runs Kafka at Scale" — primary source for the scale numbers: 3,000+ brokers, 50+ clusters, 3 AWS regions (us-east-1, us-east-2, eu-west-1), peak throughput (~40M+ inbound msgs/sec), and daily volume (800B+ messages, 1.2PB+).
- [pinterest/DoctorK on GitHub](https://github.com/pinterest/DoctorK) — corroborates DoctorKafka's stated purpose (auto-healing and workload balancing) and confirms it as an open-source Pinterest project.

**Note on sourcing:** Direct fetch of medium.com, confluent.io, and other blog domains was blocked by this environment's network egress policy at write time. The facts below are drawn from search-indexed excerpts of Pinterest's own engineering blog posts, cross-checked across the DoctorKafka post, the two-part graph-algorithms post, and the Kafka-at-scale post — all three agree on the same broker counts, failure cadence, and balancing approach.

**Key primary-source detail (not in most summaries):** Most retellings of "we automated Kafka broker healing" stop at "they built a bot that fixes dead brokers." What the graph-algorithms posts show is that automation didn't close the story — Pinterest's own max-flow approach to leader balancing had a real flaw: it could always reach near-perfect balance on a topic, but by proposing far more partition reassignments than the imbalance actually justified, because plain max-flow has no notion of "already close enough." They had to add a "shared residue" mechanism to the flow graph specifically to cap unnecessary moves. Balanced and efficient turned out to be two different problems.

---

## LinkedIn Post

It's 3 a.m., and a Kafka broker just died somewhere inside Pinterest's fleet of more than 3,000 of them, spread across 50+ clusters in three AWS regions. At this scale — over 40 million messages a second at peak, more than 800 billion messages and 1.2 petabytes moved a day — that isn't rare. A broker dies most weeks. Some weeks it happens more than once a day.

For years, what happened next was a human. An on-call engineer got paged, logged in, worked out which broker died and which partitions it owned, hand-wrote a partition reassignment JSON file, and ran the Kafka CLI to move those replicas onto healthy nodes. Get the file wrong under pressure and you could just as easily unbalance a healthy broker as fix a dead one.

That process was fine when Pinterest ran a few hundred brokers. It stopped being fine somewhere past a thousand. Multiple failures a day meant multiple 3 a.m. pages, and every manual reassignment was one more chance to make a bad night worse.

So in 2017 Pinterest built DoctorKafka: a service that watches broker health continuously, detects a dead or overloaded one, and generates and executes the reassignment itself, no human required unless something looks genuinely unusual. The load-balancing decision that used to live in someone's head at 3 a.m. moved into code, and Pinterest open-sourced it.

Automating the reassignment didn't finish the problem, it relocated it. Leader balancing wasn't just "spread the load evenly" — every reassignment costs real network and disk I/O on a live cluster, so how you get to balanced matters. Pinterest modeled it as a max-flow graph problem and found that a naive flow solution could reach near-perfect balance on a topic, but got there by proposing far more partition moves than the imbalance actually required. Balanced didn't mean efficient. They had to add a "shared residue" mechanism to the flow graph just to stop the algorithm from doing more work than the problem justified.

No one was wrong at any point here. Manual reassignment was the right call at a few hundred brokers. Hand-rolled automation was the right call once it wasn't. And even DoctorKafka's own balancing math needed a second pass once "does it balance" stopped being the right question and "does it balance efficiently" became the one that mattered.

#Kafka #SystemDesign #DistributedSystems #Pinterest

**Character count: 2,356 / 3,000 ✓**
**First 140 chars (mobile hook):** "It's 3 a.m., and a Kafka broker just died somewhere inside Pinterest's fleet of more than 3,000 of them, spread across 50+ clusters in three" ✓

---

## Twitter / X Thread

1/ It's 3 a.m. at Pinterest, and a Kafka broker just died — one of more than 3,000, across 50+ clusters. At this scale (40M+ msgs/sec peak, 800B+ msgs/day) that's not rare. It happens most weeks, some weeks more than once a day.

2/ For years, the fix was a human: get paged, find the dead broker, work out which partitions it owned, hand-write a partition reassignment JSON, run the CLI. Get it wrong at 3am and you could unbalance a healthy broker too.

3/ Fine at a few hundred brokers. Not fine past a thousand — multiple failures a day means multiple 3am pages, and every manual fix is a chance to make it worse.

4/ So in 2017 Pinterest built DoctorKafka: it watches broker health, detects failures, and generates + executes the reassignment itself. No human unless something looks genuinely unusual.

5/ But automating it didn't remove the hard part, it moved it. Balancing leaders as a max-flow graph got near-perfect balance — while proposing way more partition moves than the imbalance actually needed. Balanced ≠ efficient.

6/ They had to add a "shared residue" mechanism to the flow graph just to stop the algorithm from over-working the problem.

7/ Manual ops was right at a few hundred brokers. Automation was right after that. And the automation itself needed a second pass once "does it balance" stopped being the real question.

---

## Diagram

See: `2026-09-17-pinterest-doctorkafka-broker-autohealing.excalidraw`

Type: Sequence flow, before/after side by side (narrative style) — two vertical columns of four steps each showing the same 3am broker-death event moving through the manual process (left) versus the DoctorKafka-automated process (right), with a wide callout box beneath both columns holding the primary-source "twist" (naive max-flow reaches balance but over-proposes reassignments; fixed with a shared-residue mechanism), and a footer with the scale numbers.
Color scheme: neutral slate gray for the "before" column (the manual process wasn't wrong, just outgrown — deliberately not red, since nobody made a mistake), teal for the "after" column (distinct from the orange/blue/green used in recent posts' diagrams), violet for the twist callout. No red/green good-bad pairing.
Key screenshottable number: 3,000+ brokers, weekly-to-daily broker failures, and the "shared residue" fix for over-reassignment in the max-flow balancer.
