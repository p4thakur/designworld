<!-- sources -->
<!-- Primary: Bronson, N. et al. "TAO: Facebook's Distributed Data Store for the Social Graph." USENIX ATC 2013. -->
<!-- Paper PDF: https://www.usenix.org/system/files/conference/atc13/atc13-bronson.pdf -->
<!-- Supporting: https://engineering.fb.com/2013/06/25/core-infra/tao-the-power-of-the-graph/ -->
<!-- Key verifiable detail: inverse write happens BEFORE forward write (id2 shard first, then id1). On failure, "hanging associations" repaired by async job — deliberate choice to avoid 2PC overhead. -->

# Facebook TAO: The Cache That Understood What It Was Caching

**Date:** 2026-06-13
**Company:** Facebook
**Category:** caching
**Post type:** contrarian
**Opening style:** challenge_assumption
**Slug:** facebook-tao-graph-cache
**Character count (LinkedIn):** ~2,426

---

## LinkedIn Post

Everyone assumed Facebook just needed more Memcache. TAO was the argument that Memcache was solving the wrong problem.

By 2013, the Facebook social graph was handling over a billion read queries per second. They were already using Memcache heavily. The problem wasn't throughput — it was semantics.

Generic key-value caches are language-agnostic. They don't know that when you create "Alice follows Bob," you also need to record "Bob is followed by Alice." That logic lived in application code. Hundreds of Facebook teams inherited it, copied it, and got it slightly wrong — invalid cache entries, missing inverse edges, race conditions on write.

The underlying issue: Memcache didn't know anything about associations. It stored bytes. The correctness burden fell on every team that touched the social graph.

TAO replaced that with a typed API: assoc_add, assoc_get, assoc_count. When you wrote a forward association, TAO automatically wrote the inverse — not at the application layer, but at the cache layer. Inverse types were defined in a schema, not in code. No team had to remember.

There's a detail here that doesn't make the summaries. When TAO writes a bidirectional edge, it first writes the inverse (id2's shard), then writes the forward (id1's shard). If the second write fails, a forward association exists without its inverse — a "hanging association." TAO doesn't use two-phase commit to prevent this. Instead, an async reconciliation job finds and repairs them. Facebook deliberately chose eventual consistency between forward and inverse edges over the latency cost of 2PC.

The architecture: 2-tier caches. Leader tiers colocated with MySQL in each region. Follower tiers distributed globally. A follower miss routes to the leader — not to MySQL. The leader is both a cache and the read proxy for MySQL. Overall hit rate: 96.4%.

And assoc_count. When you want to know how many friends someone has, TAO doesn't deserialize the full edge list. It maintains a separate 8-way associative count cache per association type. Memcache can't do that — it stores blobs.

The conventional move would have been to scale Memcache and fix the application logic. TAO's argument was that any solution at the key-value layer forces correctness back into every application. You can't fix a semantic mismatch by adding more cache.

Sometimes the right abstraction is a new layer, not a bigger one.

#SystemDesign #DistributedSystems #Caching #Engineering

---

## Twitter Version

Everyone assumed Facebook just needed more Memcache.

TAO was the argument that Memcache was solving the wrong problem.

Here's the architecture that served >1B reads/second — and why it wasn't just a cache.

1/ By 2013, hundreds of Facebook teams shared Memcache clusters for social graph data. The problem wasn't scale. It was correctness.

Generic key-value caches don't know that "Alice follows Bob" requires "Bob is followed by Alice." That logic lived in app code. Hundreds of teams, hundreds of slightly different implementations, dozens of ways to get it wrong.

2/ Facebook's answer: TAO — The Associations and Objects. Typed API: assoc_add, assoc_get, assoc_count.

Inverse edges written automatically at the cache layer. Defined in schema, not code. No team had to remember. No team could forget.

3/ The write path detail that doesn't make summaries:

TAO writes the inverse edge first (id2's shard), then the forward edge (id1's shard). If step 2 fails, you get a "hanging" forward association with no inverse.

Facebook didn't use 2-phase commit to prevent this. They chose eventual consistency + an async repair job. Deliberate. Latency > strict atomicity.

4/ Architecture:
• Leaders: colocated with MySQL per region
• Followers: distributed globally
• A follower miss goes to the leader, not MySQL
• Overall hit rate: 96.4% across >1B reads/second

5/ assoc_count — TAO maintains a separate 8-way associative count cache per association type. Want to know how many friends someone has? No list deserialization. Just the count.

Memcache stores blobs. TAO knew what was in them.

6/ The conventional move: add more Memcache, fix application logic.

TAO's argument: any key-value solution forces correctness back into every app layer. The semantic mismatch doesn't go away with more cache.

Sometimes the right cache is one that understands your data model.

---

## Excalidraw Diagram

**File:** facebook-tao-graph-cache-2026-06-13.excalidraw
**Type:** Side-by-side architecture (contrarian post style)
**Color scheme:** Amber (#d4813a) for the Memcache approach — not red, it wasn't wrong, just insufficient. Teal (#2a8c6e) for TAO.

### Layout

```
┌─────────────────────────────────────┐  ┌───────────────────────────────────────┐
│  WITHOUT TAO: Scale Memcache        │  │  TAO: The Associations and Objects    │
│  (the "obvious" fix)                │  │  Typed cache API · Schema-driven      │
│                                     │  │                                       │
│  Team A App  Team B App  Team C App │  │           Application                 │
│  ✓ writes    ✗ forgot   ✗ race      │  │                 ↓                     │
│  inverse     inverse    condition   │  │         TAO Follower Tier             │
│       ↘         ↓         ↙        │  │   [distributed globally, miss→leader] │
│         Memcache Cluster            │  │         [inverse type in schema]      │
│     key-value only · no schema      │  │                 ↓                     │
│                                     │  │         TAO Leader Tier              │
│  ┌──────────────────────────────┐   │  │   [colocated with MySQL, writes inv] │
│  │ Correctness is a per-team    │   │  │         [assoc_count: 8-way cache]   │
│  │ problem. 100s of teams.      │   │  │                 ↓                     │
│  │ 100s of ways to get it wrong │   │  │              MySQL                    │
│  └──────────────────────────────┘   │  │                                       │
│                                     │  │  1B reads/sec | 96.4% hit rate        │
└─────────────────────────────────────┘  └───────────────────────────────────────┘

         The problem wasn't cache size. It was cache semantics.
     TAO moved the correctness guarantee from every team to the cache itself.
```

**Screenshottable numbers:** "1B reads/sec | 96.4% hit rate" in the stats bar.
**Unique callout:** "assoc_count: 8-way cache — no list deserialization to count edges"
