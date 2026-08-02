<!-- sources -->
<!-- Primary: -->
<!--   DoorDash Engineering Blog, "Building a transparent high-performance proxy cache for DoorDash services" -->
<!--   URL: https://careersatdoordash.com/blog/high-performance-proxy-cache-for-doordash-services/ -->
<!--   DoorDash Engineering Blog, "How DoorDash Standardized and Improved Microservices Caching" -->
<!--   URL: https://careersatdoordash.com/blog/how-doordash-standardized-and-improved-microservices-caching/ -->
<!-- Note: direct fetch of careersatdoordash.com and infoq.com returned HTTP 403 under this session's egress -->
<!-- policy (same class of gateway-level denial hit on prior posts in this series, e.g. confluent.io / -->
<!-- cwiki.apache.org on the Kafka KRaft post). Facts below were cross-checked across multiple independent -->
<!-- search-result excerpts that quote or closely paraphrase the DoorDash engineering post directly, plus a -->
<!-- corroborating secondary source: -->
<!--   InfoQ, "DoorDash Uses Envoy and Valkey for a 1.5M RPS Proxy Cache with 99.99999% Availability" (July 2026) — -->
<!--     https://www.infoq.com/news/2026/07/doordash-entity-cache-proxy/ -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Before Entity Cache, DoorDash microservices each maintained independent caching: a request-scoped -->
<!--    HashMap, a Caffeine in-JVM cache, or ad hoc Redis (Lettuce) clients per team — standardized later into a -->
<!--    shared library, but still one cache instance per process, invisible to every other pod. -->
<!-- 2. DoorDash built Entity Cache: a transparent proxy caching layer inside its Envoy-based service mesh, -->
<!--    backed by Valkey, that intercepts HTTP/gRPC requests before they reach upstream services. Onboarding is -->
<!--    done via service mesh configuration — client and upstream service code do not change. -->
<!-- 3. Entity Cache uses a lock-free single-flight mechanism so concurrent cache misses for the same entity -->
<!--    coalesce into one upstream call instead of each caller firing its own redundant request — described as -->
<!--    part of its outage-protection behavior. -->
<!-- 4. It also uses the XFetch algorithm for probabilistic early refresh, recomputing hot entries slightly -->
<!--    before expiry (scaled to recompute cost) to avoid many callers hitting an expired entry at the same -->
<!--    moment, plus custom buffer pools to cut memory allocation overhead. -->
<!-- 5. Cache freshness is handled via Kafka-based event-driven invalidation: upstream services emit change -->
<!--    events on writes; instead of pushing deletes to every cache node, Entity Cache records the entity's -->
<!--    update timestamp and compares it against the cached response's timestamp on each request, refetching if -->
<!--    stale. This avoids cross-pod delete coordination and stays correct even if events arrive out of order. -->
<!-- 6. Reported numbers: over 1.5 million requests per second, 100+ endpoints across 50 services, over 90% -->
<!--    cache hit rate on many endpoints, 99.99999% availability, 50-60% reduction in allocation rates, roughly -->
<!--    a 5x increase in per-pod throughput, and P99 latency spikes reduced by up to 80%. -->

# DoorDash's Caches Kept Missing at the Same Moment. The Fix Wasn't a Bigger Cache.

**Date:** 2026-08-02
**Company:** DoorDash
**Category:** caching
**Post type:** narrative
**Opening style:** mid_scene
**Slug:** doordash-entity-cache-request-coalescing
**Character count (LinkedIn):** ~2,675

---

## LinkedIn Post

A hundred pods, one service, and a cache entry that all of them happened to load within the same second. When that entry's TTL ran out, every pod discovered it was gone in the same breath — and every one of them independently called the same upstream service to refetch it. Multiply that across every hot entity in DoorDash's mesh, and an ordinary cache miss turns into a synchronized stampede aimed at whatever service is already having a bad day.

Each microservice at DoorDash kept its own cache — Caffeine in the JVM, a request-scoped HashMap, sometimes a hand-rolled Redis client. Reasonable first move: it cuts the repeat calls one process makes to itself. But it can't see any other pod's cache. Every process runs its own TTL clock, so a popular entity's expiry lands on hundreds of pods in nearly the same window, and each one treats it as a brand-new miss. The cache lived inside each service's own skin — no vantage point onto what every other caller was asking for at that same instant.

DoorDash's fix: pull caching out of the application entirely, into the mesh — a proxy layer built on Envoy, backed by Valkey, sitting in front of every service call. That relocation is the real mechanism, not a technology swap. Every caller's request now physically passes through the same shared layer before reaching the upstream, so that layer can see every concurrent request for the same entity and hold back all but one — a single-flight lock lets one request fetch fresh data while the rest simply wait on that answer. An app-embedded cache structurally can't do this; it only ever sees its own process's requests.

Two more mechanisms ride on that vantage point: XFetch probabilistic early refresh, recomputing hot entries slightly before they expire — proportional to recompute cost — so refreshes spread out instead of firing in sync. And Kafka-based invalidation that records an entity's update timestamp instead of pushing deletes to every cache node, so staleness becomes a timestamp comparison, correct even out of order, no cross-pod coordination required.

The system now runs past 1.5M requests per second across 100+ endpoints and 50 services, north of 90% hit rate on the busiest ones, with roughly a 5x jump in per-pod throughput and P99 latency spikes cut by up to 80%. None of that came from a faster cache. It came from giving the cache a vantage point no single service ever had.

The tradeoff didn't disappear, it moved: correctness now depends on every write path actually publishing its Kafka event. Forget one, and the mesh has no way to know the data underneath it changed.

#SystemDesign #Caching #Microservices #DistributedSystems

---

## Twitter / X Version

1/ A hundred pods at DoorDash once watched the same cache entry expire within the same second — and all hundred independently called the same upstream service to refetch it. That's not a bug. That's what per-service caching does by default.

2/ Each microservice kept its own cache: Caffeine, a request-scoped HashMap, sometimes a hand-rolled Redis client. Fine for cutting a process's own repeat calls. But no process can see any other pod's cache — every TTL clock runs alone.

3/ So a popular entity expires on hundreds of pods in nearly the same window, and every single one treats it as a fresh miss. Thundering herd, aimed straight at whatever upstream service is already struggling.

4/ DoorDash's fix: move caching out of the app entirely, into the mesh. A proxy layer on Envoy, backed by Valkey, sitting in front of every service call. Not a technology swap — a relocation.

5/ Because every caller's request now passes through the same shared layer, that layer can see every concurrent request for the same entity and hold back all but one: a single-flight lock. One fetch, everyone else waits on the answer. An app-embedded cache can never do that — it only sees itself.

6/ Add XFetch (probabilistic early refresh, spreads out expiry) and Kafka-based invalidation (timestamp comparison instead of distributed deletes, correct even out of order). Result: 1.5M+ req/sec, 90%+ hit rate, ~5x per-pod throughput, P99 spikes cut up to 80%.

7/ The tradeoff didn't vanish. It moved: correctness now depends on every write path publishing its Kafka event. Miss one, and the mesh has no idea the data underneath changed.

---

## Excalidraw Diagram

**File:** 2026-08-02-doordash-entity-cache-request-coalescing.excalidraw
**Type:** Narrative sequence flow — before/after side by side, showing where the stampede happens (before) and where it's stopped (after), with a mechanism callout and a numbers callout beneath.
**Color scheme:** Amber for the "before" per-service caching flow (not wrong, just the wrong vantage point), teal for the "after" mesh-level Entity Cache flow, slate for the mechanism callout, indigo for the numbers callout. No red/green — the per-service cache genuinely worked for what it was built to do.
**Screenshottable stat:** "1.5M+ requests/second, 100+ endpoints, 50 services, 90%+ hit rate, 99.99999% availability — from moving the cache's vantage point, not from a faster cache."

### Layout

```
Title: "DoorDash's Caches Kept Missing at the Same Moment. The Fix Wasn't a Bigger Cache."
Subtitle: "Entity Cache — a transparent proxy cache built on Envoy + Valkey inside DoorDash's service mesh"

[BEFORE — amber]                                    [AFTER — teal]
CACHE INSIDE EACH SERVICE                            CACHE INSIDE THE MESH (ENTITY CACHE)

Step 1: Service A's Caffeine cache misses            Step 1: Every caller's request passes through
  (TTL just expired)                                   the same Envoy + Valkey proxy layer first

        |                                                      |
        v                                                      v

Step 2: 100 other pods hit the SAME TTL              Step 2: First miss takes a single-flight lock —
  window — all miss the same entity                    every other concurrent request for that
  within the same breath                                entity WAITS on that one in-flight call

        |                                                      |
        v                                                      v

Step 3: ALL of them independently call               Step 3: ONE call reaches the upstream. Response
  Upstream Service X at once —                          fans out to every waiter. XFetch refreshes
  thundering herd hits an already-                       hot keys early so expiry never syncs up
  struggling service                                      across pods again

[CALLOUT — the vantage point shift, slate]
THE MECHANISM SHIFT
An app-embedded cache only ever sees its own process's requests — it has no way to know a hundred other
pods just missed the exact same entity. A cache living in the mesh sees every caller's request pass through
the same layer, so it can hold back duplicates and let one fetch answer for all of them.

[CALLOUT — the numbers, indigo]
WHAT THE VANTAGE POINT BOUGHT
1.5M+ requests/sec across 100+ endpoints, 50 services. 90%+ hit rate on the busiest endpoints. ~5x per-pod
throughput. P99 latency spikes cut up to 80%. Kafka timestamp-comparison invalidation — no cross-pod delete
coordination, correct even out of order.

[REFLECTION — footnote]
No one was wrong. Per-service caching does cut a process's own repeat calls — it just can't see what every
other pod is asking for at the same instant. The tradeoff didn't disappear when DoorDash moved caching into
the mesh. It moved to whoever forgets to publish a Kafka event.
```
