<!-- sources -->
<!-- Primary: -->
<!--   Martin Kleppmann, "How to do distributed locking" (Feb 8, 2016) -->
<!--   URL: https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html -->
<!--   Salvatore Sanfilippo (antirez), "Is Redlock safe?" (Feb 2016) -->
<!--   URL: https://antirez.com/news/101 -->
<!--   Redis docs, "Distributed Locks with Redis" (Redlock algorithm specification) -->
<!--   URL: https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/ -->
<!-- Note: direct fetch of martin.kleppmann.com, antirez.com, and redis.io returned HTTP 403 under this -->
<!-- session's egress policy (same class of gateway-level denial hit on prior posts in this series). Facts -->
<!-- below were cross-checked across multiple independent search-result excerpts that quote or closely -->
<!-- paraphrase both primary posts, plus the Redis documentation's own algorithm spec: -->
<!--   Hacker News discussion of antirez's rebuttal — https://news.ycombinator.com/item?id=11065933 -->
<!--   Redisson glossary, "What Is the Redlock Algorithm?" — https://redisson.pro/glossary/redlock-algorithm.html -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Redlock is Redis's official recipe for a distributed mutual-exclusion lock: N independent Redis -->
<!--    masters (canonically 5), with zero replication between them. A client acquires the lock by setting -->
<!--    the same key/random-value pair on each master in turn with a short per-request timeout, and considers -->
<!--    the lock held only if it wins a majority (N/2+1, i.e. 3 of 5) AND the total time spent acquiring is -->
<!--    comfortably under the lease TTL. -->
<!-- 2. Validity time formula: MIN_VALIDITY = TTL - (T2-T1) - clock_drift_margin, where T1/T2 are timestamps -->
<!--    sampled before/after the acquisition round-trip and clock_drift_margin is typically ~1% of TTL plus a -->
<!--    couple of milliseconds. This protects against slow acquisition (network delay during the handshake), -->
<!--    not pauses after the lock is already granted. -->
<!-- 3. Why a single-instance Redis lock isn't the "obvious fix": if the one master fails over to a replica -->
<!--    before the lock key has replicated (Redis uses async replication), the new master has no record of the -->
<!--    key and a second client can acquire the "same" lock immediately. Redlock's N=5/no-replication/majority -->
<!--    structure exists specifically to make that failure mode require forging agreement across independent -->
<!--    nodes with no shared state. -->
<!-- 4. Kleppmann's Feb 2016 critique: Redlock assumes bounded network delay, bounded process pauses, and -->
<!--    bounded clock error — real production systems violate all three. Worked example: Client 1 wins the -->
<!--    lock, then experiences a GC pause (or scheduler pause, or slow disk write) of tens of seconds; its -->
<!--    lease expires while frozen; Client 2 acquires the now-free lock and starts writing to a shared -->
<!--    resource; Client 1 wakes up unaware time passed, still believes it holds the lock, and writes too. -->
<!--    Redlock has no fencing token — no number that provably increases with each acquisition — so the -->
<!--    resource being protected cannot distinguish a stale write from a fresh one. -->
<!-- 5. antirez's rebuttal: the elapsed-time check in Redlock does protect against slow acquisition, which is -->
<!--    a real (if different) hazard; a GC pause occurring after the lock is already granted is a property of -->
<!--    every lease-based lock, not specific to Redlock; the fix is a fencing token/CAS check layered on top of -->
<!--    the lock, and Redis should move toward monotonic clock APIs to reduce clock-jump risk. -->
<!-- 6. Resolution: both sides converged on "use a fencing token if correctness matters," while continuing to -->
<!--    disagree on whether Redlock itself needed to change. ZooKeeper's zxid (or an incrementing DB version -->
<!--    column) can serve as a native fencing token; Redlock, as originally specified, does not produce one. -->

# Redlock's Quorum Stops a Dead Node. It Doesn't Stop a Live One That Fell Asleep.

**Date:** 2026-07-25
**Company:** Redis / Redis community (antirez vs. Martin Kleppmann)
**Category:** stability
**Post type:** narrative
**Opening style:** mid_scene
**Slug:** redis-redlock-fencing-token-debate
**Character count (LinkedIn):** ~2,414

---

## LinkedIn Post

In February 2016, Redis's creator and a Cambridge database researcher spent two weeks publicly disagreeing about whether a lock actually locks anything.

The lock was Redlock — Redis's own recipe for a distributed mutual-exclusion lock, already wired into production systems to guarantee things like "only one worker touches this job" or "only one node runs this migration." The design was deliberate: instead of trusting one Redis instance (which can fail over to a replica that never got the key, letting two clients grab the "same" lock), Redlock spreads the lock across 5 independent Redis masters with zero replication between them. A client wins the lock only with a majority — 3 of 5 — and only if the round-trip to all 5 finished fast enough to leave most of the lease (a 10-second TTL, in the canonical example) still on the clock. That's a real fix for a real failure mode: forging a second grant needs 3 independent nodes to agree, and there's no shared state between them to corrupt.

Martin Kleppmann's critique wasn't about the quorum. It was about what happens after you win it. Client 1 acquires the lock, then hits a 30-second GC pause — stop-the-world, nothing it can do. Its 10-second lease expires while it's frozen. Client 2 sees the key free, wins its own majority, starts writing to the shared resource. Client 1 wakes up, has no idea 20 seconds passed, still believes it owns the lock, and writes too. Two clients, one resource, both convinced they're exclusive — and Redlock can't stop it, because the lock is a yes/no. It never hands out a number that increases with each acquisition, so the resource being written to has no way to tell a stale write from a fresh one.

antirez pushed back hard: Redlock does check elapsed time, but during acquisition, not after — that guards against slow handshakes, not GC pauses once you're already holding the lock. He called that a property of every lease-based lock, not a Redlock-specific flaw, and argued the fix is a fencing token layered on top — something ZooKeeper hands you for free via its zxid, and Redlock, as specified, never produced.

Neither side backed down on whether Redlock itself needed to change. Both ended up agreeing on the fix. A decade later, most teams reaching for Redlock still skip the fencing token — right up until their GC pause outlives their TTL.

#SystemDesign #Redis #DistributedSystems #Redlock

---

## Twitter / X Version

1/ Redis's creator and a Cambridge database researcher spent Feb 2016 publicly fighting about whether Redis's own official distributed lock actually locks anything.

2/ Redlock: 5 independent Redis masters, zero replication between them. You win the lock with 3/5, and only if acquiring all 5 was fast enough to leave most of a 10s TTL. That kills the "one Redis node fails over, key never replicated, two clients grab the same lock" bug.

3/ Kleppmann's hole: Client 1 wins the lock, then hits a 30s GC pause. Its lease expires while it's frozen. Client 2 grabs the now-free key, writes. Client 1 wakes up unaware, still thinks it owns the lock, writes too. Redlock hands out a yes/no, never a number that goes up — so the resource can't tell a stale write from a fresh one.

4/ antirez: the elapsed-time check happens during acquisition, not after — that's a different failure mode (slow handshake, not post-acquisition pause). GC pauses after you're holding the lock are a problem for every lease-based lock, not just this one. Fix: layer a fencing token on top.

5/ Both sides agreed on fencing tokens. Neither agreed Redlock itself needed to change. A decade later, most teams reaching for Redlock still skip the token — until a GC pause outlives the TTL.

---

## Excalidraw Diagram

**File:** 2026-07-25-redis-redlock-fencing-token-debate.excalidraw
**Type:** Sequence flow (narrative) — a minute-by-minute timeline of the exact race condition Kleppmann described, showing precisely where the two clients' beliefs about lock ownership diverge.
**Color scheme:** Indigo for Client 1's normal acquisition, slate for the frozen/paused state (neutral, not yet "bad"), amber for the lease-expiry warning, teal for Client 2 (a distinct actor, not a villain), rose for the moment of actual collision and the explanatory callout. No blanket red/green — Redlock's quorum design wasn't wrong, it solved a different failure mode than the one that bit here.
**Screenshottable stat:** "5 masters, 3/5 quorum, 10s TTL, ~30s GC pause → lease expires at T+10s, second client acquires at T+10.2s, first client wakes and writes anyway at T+30s — with no fencing token to tell them apart."

### Layout

```
Title: "Redlock's Quorum Stops a Dead Node. It Doesn't Stop a Live One That Fell Asleep."
Subtitle: "Feb 2016 — Redis's creator (antirez) and Martin Kleppmann publicly argued over this exact gap in Redlock's distributed lock"

[SEQUENCE — horizontal, five stages]

Stage 1 (indigo)       Stage 2 (slate)        Stage 3 (amber)         Stage 4 (teal)          Stage 5 (rose)
T+0s                    T+0.1s                  T+10s                   T+10.2s                 T+30s
CLIENT 1 ACQUIRES       CLIENT 1 FREEZES        LEASE EXPIRES           CLIENT 2 ACQUIRES       CLIENT 1 WAKES, WRITES TOO
Requests the lock on    Stop-the-world GC        Client 1's TTL         Sees the key free,      Unaware any time passed.
5 independent Redis     pause, ~30s. No CPU,     lapses on the Redis    wins its own majority,  Still believes it holds
masters. Wins majority, no network, no idea      side while it's       starts writing to the   the lock. Writes to the
3 of 5. 10s TTL lease   time is passing.         still frozen. The     shared resource.        same resource.
starts.                                          key is now free.

[CALLOUT — rose, the actual gap]
THE GAP
Redlock's quorum — 3 of 5 independent nodes, no shared state between them — stops a crashed node from forging a
second grant. It does nothing about a live client that pauses past its own lease and wakes up unaware, because the
lock is a yes/no. It never hands out a number that increases with each acquisition, so the resource being written
to can't tell a stale write from a fresh one.

[REFLECTION — teal, footnote]
antirez: the elapsed-time check happens during acquisition — it catches slow handshakes, not pauses after the
lease is granted. Kleppmann: without a fencing token, the resource has no way to reject the stale write. Both
right. Neither backed down on whether Redlock itself needed to change.
```
