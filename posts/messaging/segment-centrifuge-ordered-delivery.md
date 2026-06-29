<!-- source: Segment Engineering Blog — "Centrifuge: a reliable system for delivering billions of events per day" (2018) -->
<!-- category: messaging | post_type: contrarian | opening_style: challenge_assumption -->
<!-- date: 2026-06-29 -->

# Segment's Centrifuge: Why 170B Events/Month Broke Kafka Fan-Out

**Sources (verified primary):**
- Segment Engineering Blog: "Centrifuge: a reliable system for delivering billions of events per day" (2018)
- Segment Engineering Blog: "Rebuilding our infrastructure" (2017)

**Detail only in the primary source:** The ordering problem was the deeper constraint — deduplication at the consumer side was explored and rejected not just because of unbounded state, but because out-of-order retries produced logically impossible states in destination systems (e.g., "subscription cancelled" before "subscription created"). This ordering requirement, not just duplicate volume, is what drove the Centrifuge architecture.

---

## LinkedIn Post

~2,450 characters · contrarian · challenge_assumption opener

---

Everyone says Kafka solves fan-out at scale. Segment processed 170 billion events a month through Kafka. It almost broke them.

Segment collects events from your app and delivers them to 200+ destinations — Salesforce, Mixpanel, Intercom, Amplitude. The customer doesn't see the plumbing. The plumbing is the hard part.

The obvious architecture is obvious for a reason. Publish events to Kafka. Spin up a worker per destination. Workers consume and deliver. Scale horizontally as volume grows. Kafka handles backpressure. Done.

Except it wasn't. Kafka guarantees at-least-once delivery, which means workers will sometimes process the same event twice — after a crash, a rebalance, a network timeout. That's usually acceptable. For Segment it was catastrophic.

Their destinations aren't idempotent. A "purchase completed" event delivered twice to Salesforce doubles the revenue number. Twice to Mixpanel corrupts the funnel. Twice to Intercom creates duplicate users in your marketing automation. At 170 billion events a month, retry storms weren't edge cases.

The obvious fix: build deduplication at the consumer. Track event IDs in Redis. Reject what you've seen before.

Here's what broke that plan. Retries at Segment's scale could arrive hours or days later. Dedup state per destination per user became unbounded — billions of IDs with no safe expiry window. Worse: events could arrive out of order. A "subscription cancelled" delivered before "subscription created" left users in an impossible state in the destination system. Broken billing. Support tickets. All from a retry in the wrong sequence.

So they built Centrifuge. Kafka topics partitioned by destination and user ID. Events for the same user, same destination, always land on the same partition, in order. A coordination layer tracks the last confirmed offset — not a list of IDs, just a position. Retries replay from that point. The result: ordered, exactly-once delivery across 200+ destinations, without unbounded state.

The contrarian insight: most teams optimize event pipelines for throughput. More partitions, more parallelism. Segment optimized for correctness first. Once they had ordered, reliable delivery, they could parallelize safely — because the race conditions that forced circuit breakers and retry limits no longer existed.

The real cost of at-least-once delivery isn't the duplicates. It's every workaround you build to survive them.

#SystemDesign #Kafka #DataEngineering #SoftwareArchitecture

---

## Twitter Thread

Everyone said Kafka solves fan-out at scale.

Segment ran 170 billion events/month through Kafka. It almost broke them.

Why they had to rebuild the whole thing 🧵

---

Segment delivers events to 200+ destinations: Salesforce, Mixpanel, Intercom. The obvious move: Kafka → workers per destination → deliver.

Kafka is at-least-once. Their destinations aren't idempotent.

A purchase event delivered twice to Salesforce = doubled revenue. Twice to Mixpanel = corrupted funnel.

---

"Just deduplicate at the consumer."

At 170B events/month, retries arrive hours or days later. You can't expire event IDs. Dedup state per destination per user = unbounded, forever.

But the real problem: ordering.

---

A "subscription cancelled" arriving before "subscription created" doesn't just duplicate. It leaves the user in an impossible state in the destination system.

Broken billing. Support tickets. All from a retry in the wrong sequence.

Dedup alone can't fix ordering.

---

Centrifuge:

• Kafka partitioned by dest + user ID
• Same user → same destination → always same partition, in order
• Coordination layer tracks confirmed offset (not IDs — just a position)
• Retries replay from that offset

Ordered, exactly-once. No unbounded state.

---

The takeaway: most teams optimize for throughput. More workers, more partitions.

Segment optimized for correctness first.

Once they had that, parallelism was safe. The race conditions that forced circuit breakers and retry limits? Gone.

The real cost of at-least-once isn't duplicates. It's the workarounds.

---

## Diagram

See: `segment-centrifuge-ordered-delivery.excalidraw`

**Layout:** Side-by-side architecture comparison (contrarian post type)
- **Left — Obvious Approach:** Kafka → Worker Pool → 200+ destinations, with at-least-once delivery causing DUPLICATE corruption
- **Right — Centrifuge:** Kafka (partitioned by dest+user) → Coordination Layer (confirmed offsets) → 200+ destinations, producing ORDERED + EXACTLY-ONCE delivery
- **Colors:** Red for problem path, green for Centrifuge path. Yellow destination boxes stay neutral — they aren't the problem.
- **Key numbers embedded:** 170B events/month · 200+ destinations · retries arrive hours or days late
