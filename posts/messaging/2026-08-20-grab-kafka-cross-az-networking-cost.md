<!-- sources -->
<!-- Primary (attempted direct fetch — blocked by this session's network egress policy for -->
<!--   engineering.grab.com; facts below reconstructed from multiple independent secondary sources -->
<!--   that quote and corroborate the primary post's specific figures and mechanism): -->
<!--   Grab Engineering Blog, "Zero traffic cost for Kafka consumers" -->
<!--     https://engineering.grab.com/zero-traffic-cost -->
<!-- Corroborating (independently confirm the same numbers and mechanism from the primary post): -->
<!--   Noise (engineering-blog aggregator mirror of the Grab post), "Zero traffic cost for Kafka consumers" -->
<!--     https://noise.getoto.net/2023/07/07/zero-traffic-cost-for-kafka-consumers/ -->
<!--   AWS Big Data Blog, "Reduce network traffic costs of your Amazon MSK consumers with rack awareness" -->
<!--     https://aws.amazon.com/blogs/big-data/reduce-network-traffic-costs-of-your-amazon-msk-consumers-with-rack-awareness/ -->
<!--   2 Minute Streaming, "KIP-392: Fetch From Follower" -->
<!--     https://blog.2minutestreaming.com/p/kafka-kip-392-follower-fetching -->
<!--   Grab Engineering Blog, "Plumbing At Scale" (Coban platform scale figures: 300B+ events/week, -->
<!--   terabytes of ingress/hour, across every Grab vertical) -->
<!--     https://engineering.grab.com/plumbing-at-scale -->
<!-- Key verifiable details: -->
<!-- 1. Grab's Coban team runs Kafka at 300+ billion events a week, terabytes of ingress per hour, across -->
<!--   every Grab vertical (GrabFood, GrabPay, mobility, etc). -->
<!-- 2. Kafka's default consumer fetch behavior routes a consumer to whichever broker holds the partition -->
<!--   leader, with no awareness of which availability zone the consumer itself is running in. -->
<!-- 3. With replicas spread across 3 AZs (standard practice for durability), a consumer's own AZ holds the -->
<!--   leader only ~1/3 of the time by chance — meaning roughly 2 out of 3 fetch requests cross an AZ -->
<!--   boundary. AWS bills for inter-AZ data transfer. -->
<!-- 4. At Grab's scale, this inter-AZ consumer fetch traffic represented roughly 50% of the total Kafka -->
<!--   platform cost. -->
<!-- 5. Grab's brokers already had broker.rack configured via an Ansible role that read the AZ ID from EC2 -->
<!--   instance metadata at deploy time (originally just for replica placement across AZs). -->
<!-- 6. The fix extended that: consumers advertise their own AZ via client.rack, and brokers run a -->
<!--   replica.selector.class (Kafka's KIP-392 "Fetch From Follower" mechanism) that redirects a consumer's -->
<!--   fetch request to an in-AZ follower replica when one exists, instead of always the leader. -->
<!-- 7. Tradeoff: a follower replica can lag the leader by a small amount, so a rack-aware consumer reads a -->
<!--   slightly older copy of the log; the saving only applies in AZs that actually hold a replica for that -->
<!--   partition. -->
<!-- 8. Aligning consumer fetch traffic to the same AZ is reported to cut Kafka cluster network cost by up to -->
<!--   50% — hence the post's title, "zero traffic cost." -->

# Grab's Kafka Consumers Were Crossing an Availability Zone Boundary Two Out of Three Times. Nobody Had Done Anything Wrong.

**Date:** 2026-08-20
**Company:** Grab
**Category:** messaging
**Post type:** narrative
**Opening style:** mid_scene
**Slug:** grab-kafka-cross-az-networking-cost
**Character count (LinkedIn):** 2374

---

## LinkedIn Post

A Kafka consumer sitting in one availability zone sends a fetch request. The partition leader it needs lives in a different zone. The bytes cross the AZ boundary — and on AWS, someone pays for every gigabyte that crosses it.

Grab's Coban team runs Kafka at a scale where this stops being a rounding error: over 300 billion events a week, terabytes of ingress every hour, across every vertical from GrabFood to GrabPay. Kafka's default behavior has never cared about zones. A consumer asks for a partition and gets routed to whichever broker holds the leader replica, wherever that broker happens to sit.

With replicas spread across three AZs for durability — standard practice, nobody would design it any other way — that default routing means a consumer's own AZ holds the leader only about a third of the time. Do the math and roughly two out of three fetch requests cross a zone boundary. At Coban's throughput, that inter-AZ fetch traffic wasn't a line item buried in the bill. It was close to half of the entire Kafka platform's cost.

Nobody had misconfigured anything. Spreading replicas across zones is exactly what you're supposed to do to survive an AZ going down. The cost was a side effect of doing the right thing for durability — the kind of bill that doesn't show up until someone actually goes looking for where the money is going.

The fix didn't touch durability at all. Grab's brokers already tagged themselves with their own AZ — an Ansible role read it straight from EC2 instance metadata at deploy time, originally just to spread replicas evenly. They extended the same idea to consumers: advertise your own AZ too, and let brokers run a replica selector that redirects a fetch to an in-AZ follower when one exists, instead of always the leader. It's Kafka's KIP-392 fetch-from-follower path, repurposed as a cost control.

It isn't free. A follower can lag its leader by a few milliseconds, so a rack-aware consumer is reading a slightly older copy of the log, and the saving only shows up in AZs that actually hold a replica. But the traffic that had been running up roughly half the Kafka bill collapsed once fetches stopped crossing zones by default.

The boundary Kafka was built to survive turned out to be the boundary that was quietly the most expensive one to cross.

Sources in comments.

#SystemDesign #Kafka #Grab #DistributedSystems

---

## Twitter / X Version

1/ A Kafka consumer in one AWS zone sends a fetch request. The partition leader lives in a different zone. The bytes cross the AZ boundary — and AWS bills for every GB that crosses it.

2/ Grab's Kafka platform (Coban) moves 300+ billion events a week. Kafka's default consumer routing has never cared about zones — you get sent to whichever broker holds the leader, wherever it sits.

3/ Replicas spread across 3 AZs for durability (the right call). But that means a consumer's own AZ holds the leader only ~1/3 of the time. Two of three fetch requests cross a zone. At Coban's scale, that was close to half the entire Kafka bill.

4/ Nobody did anything wrong. Durability caused the cost — not a misconfiguration.

5/ The fix: brokers already tagged their own AZ via EC2 metadata. Extend that to consumers (client.rack), and use KIP-392 fetch-from-follower so brokers redirect fetches to an in-AZ replica when one exists, instead of always the leader.

6/ Tradeoff: a follower can lag the leader by a few ms, so you're reading a slightly older copy of the log. Only helps in AZs that actually hold a replica.

7/ The zone boundary Kafka was built to survive turned out to be the boundary quietly costing the most to cross.

---

## Excalidraw Diagram

**File:** 2026-08-20-grab-kafka-cross-az-networking-cost.excalidraw
**Type:** Sequence flow, before/after side by side — two request paths (default routing vs. rack-aware routing) showing exactly where the AZ boundary gets crossed, plus a footer stating the cost tradeoff.
**Color scheme:** Amber for the "before" path — not painted as a mistake, since spreading replicas across AZs was the right durability call. Crimson isolates just the arrow that crosses the AZ boundary, so the one costly hop is visually distinct from the boxes around it. Indigo for the "after" path, marking the fix as a different tool for a different job rather than a correction of an error. Teal footer, separate from both paths, so the tradeoff statement reads as commentary rather than a third pipeline stage.
**Screenshottable stat:** "~2 out of 3 Kafka fetch requests crossed an AZ boundary by default. That inter-AZ traffic was ~50% of Grab's Kafka platform cost."

### Layout

```
Title: "Grab's Kafka Consumers Were Crossing an Availability Zone Boundary Two Out of Three Times."

[BEFORE — DEFAULT ROUTING, top row, left to right]
  Box 1 (amber): "CONSUMER — AZ-A. Just wants the next batch of messages from its partition."
  --arrow (crimson, labeled "crosses AZ boundary → billed per GB")-->
  Box 2 (amber): "BROKER — AZ-C (partition leader). Replicas spread across 3 AZs for durability. Consumer's
    own AZ holds the leader only ~1 in 3 times, by chance."

[AFTER — RACK-AWARE ROUTING (KIP-392), bottom row, left to right]
  Box 3 (indigo): "CONSUMER — AZ-A. Now advertises its own AZ via client.rack."
  --arrow (indigo, short, labeled "same AZ → no inter-AZ charge")-->
  Box 4 (indigo): "BROKER — AZ-A (in-AZ follower replica). Broker's replica selector redirects the fetch here
    instead of the leader in AZ-C, when a same-AZ replica exists."

[FOOTER, teal band, full width]
  "~2 out of 3 fetch requests crossed an AZ boundary by default — roughly 50% of Grab's Kafka platform cost.
  Fix costs nothing in durability: writes still go to the leader; only consumer reads redirect. Tradeoff: a
  follower can lag its leader by a few ms, so rack-aware consumers read a slightly older copy of the log."
```
