<!-- sources -->
<!-- Primary: Nishtala, Rajesh, et al. "Scaling Memcache at Facebook." NSDI 2013. -->
<!-- Paper: https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala -->
<!-- Key verifiable detail (primary source only): Leases solve TWO problems — thundering herds AND stale sets. The token is revocable on delete, so a stale fill attempt is rejected. Most summaries only describe thundering herd. Also: UDP (not TCP) for GET requests, explicit in Section 3.1. -->

# Facebook Memcache: The Three Things That Kill Your Database at Scale

**Date:** 2026-06-18
**Company:** Facebook
**Category:** caching
**Post type:** structured
**Opening style:** shared_pain_point
**Slug:** facebook-memcache-nsdi-scaling
**Character count (LinkedIn):** ~2,110

---

## LinkedIn Post

Caches don't fail by missing data. They fail when hundreds of servers miss the same key at the same millisecond. Facebook documented exactly how this happens — and built three systems to stop it.

Facebook's 2013 NSDI paper ("Scaling Memcache at Facebook") describes three failure modes that emerge at scale, none of which appear in standard caching tutorials. At the time of publishing, they were running more than 800 servers in a single Memcache cluster, with multiple clusters across data centers.

**The thundering herd.** A key expires. All servers waiting on it miss simultaneously and query MySQL in parallel. The database tips over.

Facebook fixed this with leases. The first server to miss a key receives a token. Every other server waiting for the same key is told to wait and retry after 10 milliseconds. MySQL handles exactly one fill request. The token can be revoked — if a delete operation arrives while the fill is in progress, the token is invalidated and the stale value can't be written back. One mechanism solving two separate problems: thundering herds and stale sets. Most secondhand summaries only mention one.

**Incast congestion.** A single web request reads hundreds of cache keys in parallel. All the responses arrive at the same moment. The server's incoming network buffer saturates. This isn't a cache problem — it's a network problem caused by the cache being too fast.

Facebook's fix was a sliding window on each client, capping the number of outstanding requests at any given time. No extra hardware. Just a queue.

**Failure cascade.** A Memcache server dies. Its keys go cold and fall through to MySQL. One server's worth of traffic, hitting the database all at once.

Facebook built "gutter pools" — a small set of servers representing less than 1% of total capacity, kept idle as a failover tier. When a server fails, the affected keyspace automatically reroutes to the gutter. The database never sees the burst.

One detail that only appears in the paper: Facebook uses UDP, not TCP, for GET requests. The paper states this explicitly — UDP has no handshake overhead, and a dropped packet is simply treated as a cache miss. At the scale they operated, the latency difference is real.

Three failure modes. Three targeted fixes. None of them make the cache faster. They make the database survivable.

#SystemDesign #DistributedSystems #Caching #Engineering

---

## Twitter / X Version

Caches don't kill databases by missing data. They do it when hundreds of servers miss the same key simultaneously.

Facebook's NSDI 2013 paper documents exactly how — and the three systems they built to prevent it.

🧵

1/ THE THUNDERING HERD

A key expires. Every server waiting on it misses at once. All query MySQL simultaneously. The DB spikes.

Fix: leases. First server to miss gets a token. Others wait 10ms and retry. MySQL handles 1 fill, not hundreds.

The token is revocable. If a delete arrives before the fill completes, the stale value can't be written back. One mechanism solving two problems: thundering herds + stale sets.

2/ INCAST CONGESTION

A single web request reads hundreds of cache keys in parallel. All responses arrive at once. The server's NIC saturates.

This isn't the cache being slow. It's the cache being too fast.

Fix: sliding window per client. Cap outstanding requests. No new hardware.

3/ FAILURE CASCADE

A Memcache server dies. Its keys fall to MySQL cold. One server's worth of traffic hitting the database all at once.

Fix: gutter pools. Less than 1% spare capacity, idle and waiting. Keyspace auto-reroutes on server death. Database never sees the burst.

4/ The detail that only appears in the paper:

Facebook uses UDP — not TCP — for GET requests. No handshake overhead. A dropped packet is a cache miss. At scale, this matters.

None of these fixes make the cache faster. They make the database survivable.

---

## Excalidraw Diagram

**File:** 2026-06-18-facebook-memcache-nsdi-scaling.excalidraw
**Type:** Three-row problem → fix → impact grid (structured case study style)
**Color scheme:** Warm amber (#d4813a / #2a1808) for problems. Teal (#2a8c6e / #081e18) for fixes. Soft green (#6acc8a) for impact. Dark canvas (#0d0d1a).
**Screenshottable stat:** ">800 servers per cluster · gutter pools <1% · leases: 10ms retry"

### Layout

```
Title: "Facebook Memcache: 3 Protection Mechanisms (NSDI 2013)"
Stats: ">800 servers per cluster  ·  UDP GETs  ·  leases  ·  gutter pools <1%"

              PROBLEM              →        FIX           →    IMPACT
┌─────────────────────────────┐   ┌─────────────────────┐   ┌──────────────────┐
│ THUNDERING HERD             │ → │ LEASES              │ → │ MySQL: 1 fill    │
│ Key expires                 │   │ 1st miss → token    │   │ not hundreds     │
│ → 100s of servers miss      │   │ Others wait 10ms    │   │ Spike eliminated │
│ → all query MySQL           │   │ Token revocable     │   │                  │
│ → DB spikes                 │   │ → also solves stale │   │                  │
└─────────────────────────────┘   └─────────────────────┘   └──────────────────┘
┌─────────────────────────────┐   ┌─────────────────────┐   ┌──────────────────┐
│ INCAST CONGESTION           │ → │ SLIDING WINDOW      │ → │ NIC never        │
│ 1 request → 100s of keys    │   │ Cap outstanding     │   │ saturated        │
│ → all responses at once     │   │ requests per client │   │ No extra hw      │
│ → server NIC overwhelmed    │   │ Not hardware.       │   │                  │
│ (too fast, not too slow)    │   │ Just a queue.       │   │                  │
└─────────────────────────────┘   └─────────────────────┘   └──────────────────┘
┌─────────────────────────────┐   ┌─────────────────────┐   ┌──────────────────┐
│ FAILURE CASCADE             │ → │ GUTTER POOL         │ → │ DB never sees    │
│ Memcache server dies        │   │ <1% idle capacity   │   │ server failures  │
│ → keys go cold              │   │ Failed keyspace     │   │ Transparent      │
│ → all hit MySQL directly    │   │ auto-reroutes here  │   │ failover         │
│ → DB burst                  │   │ MySQL unaffected    │   │                  │
└─────────────────────────────┘   └─────────────────────┘   └──────────────────┘

Footer: "UDP for GETs (not TCP): no handshake overhead · dropped packet = cache miss · at scale, latency difference is measurable"
```
