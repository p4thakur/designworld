---
date: 2026-09-08
company: Cloudflare
topic: Workers KV — built for dual-cloud redundancy in 2018, quietly simplified to a single provider in 2025, then taken down by that provider's outage
category: availability
post_type: confessional
opening_style: cold_fact
slug: cloudflare-workers-kv-gcp-outage-redundancy
---

## Sources

- Cloudflare Blog: ["Cloudflare service outage June 12, 2025"](https://blog.cloudflare.com/cloudflare-service-outage-june-12-2025/)
- Cloudflare Blog: ["Hardening Workers KV"](https://blog.cloudflare.com/workers-kv-restoring-reliability/)
- Cloudflare Blog: ["Redesigning Workers KV for increased availability and faster performance"](https://blog.cloudflare.com/rearchitecting-workers-kv-for-redundancy/)
- Cloudflare Blog: ["Building With Workers KV, a Fast Distributed Key-Value Store"](https://blog.cloudflare.com/building-with-workers-kv/) (2018)
- InfoQ: ["Cloudflare Rearchitects Workers KV Following GCP Outage, Achieves 40x Performance Gain"](https://www.infoq.com/news/2025/08/cloudflare-workers-kv/) (August 2025)

**Key primary-source detail (not in most summaries):** The dual-provider design wasn't dropped because of a security review or an incident — Cloudflare gave it up earlier in 2025 specifically to cut the operational complexity of running two cloud backends in lockstep as Workers KV scaled to hundreds of billions of key-value pairs. The single-provider setup that failed on June 12 was a deliberate simplification made months before the outage, not an oversight baked in from the start.

**Note on sourcing:** `blog.cloudflare.com` was not reachable from this environment's network egress policy at write time. The specific facts above — the 2018 dual-provider active-active design with raced reads, the 2025 simplification to GCP alone "to reduce operational complexity," the June 12, 2025 GCP IAM token-issuance failure, the 90.22% Workers KV request failure rate, the 2h28m outage duration, the cascading failures across Access/WARP/Gateway/Turnstile, the failover to R2, and the post-incident hybrid architecture (small objects to Cloudflare's own distributed database by size, median 288 bytes, larger objects to R2, p99 read latency ~200ms → under 5ms) — come from consistent, near-identical phrasing surfaced across independent search-indexed excerpts of those primary posts and independent third-party coverage (InfoQ, Byte-Sized Design), cross-checked across multiple separate queries, rather than a single secondary summary.

---

## LinkedIn Post

In 2018, Cloudflare built Workers KV so that no single cloud provider's outage could ever take it down. In 2025, a single cloud provider's outage took it down anyway.

The original design wrote every value to two separate third-party cloud storage backends at once and raced reads between them, taking whichever answered first. Real redundancy — an active-active system across two clouds, where a provider-wide failure meant slightly higher latency, not an outage.

As Workers KV grew to hundreds of billions of key-value pairs and millions of requests a second, running two providers in lockstep got expensive to operate. So earlier in 2025, Cloudflare quietly simplified down to one: Google Cloud. The redundancy KV was built around wasn't there anymore by the time it mattered.

On June 12, 2025, Google Cloud's IAM service stopped issuing auth tokens globally. Workers KV kept its own configuration data inside GCP — so when IAM went down, KV couldn't even read the config that told it what its own data was. 90.22% of requests started failing. KV quietly backs identity, config, and asset delivery across nearly the whole platform, so the damage didn't stay contained: Access failed 100% of identity logins, WARP dropped, Gateway and Turnstile went with it. Full recovery took 2 hours 28 minutes, engineers shedding non-critical load and failing traffic over to Cloudflare's own R2 storage partway through.

The fix wasn't restoring the second cloud provider. It was removing the dependency on having one at all — small objects (median size: 288 bytes) now route into Cloudflare's own distributed database, everything larger into R2, all served from infrastructure Cloudflare controls. p99 read latency dropped from around 200ms to under 5ms as a side effect, not the point.

The redundancy you design for a system's first ten million requests a day isn't the redundancy that survives its ten billionth. Every simplification made under load is a quiet bet about which failure you've decided to stop worrying about.

#Cloudflare #SystemDesign #Reliability #DistributedSystems

**Character count: ~2,079 / 3,000 ✓**
**First 140 chars (mobile hook):** "In 2018, Cloudflare built Workers KV so that no single cloud provider's outage could ever take it down. In 2025, a single cloud provider's" ✓

---

## Twitter / X Thread

1/ In 2018, Cloudflare built Workers KV so no single cloud provider's outage could ever take it down. In 2025, a single cloud provider's outage took it down anyway.

2/ Original design: write every value to two separate cloud storage backends at once, race the reads, take whichever answers first. Real active-active redundancy — a provider outage meant higher latency, not downtime.

3/ As KV grew to hundreds of billions of keys and millions of req/s, running two providers in lockstep got expensive. Earlier in 2025, Cloudflare quietly dropped to one: Google Cloud.

4/ June 12, 2025: Google Cloud's IAM stopped issuing auth tokens globally. KV's own config lived inside GCP — so KV couldn't even read what its own data was. 90.22% of requests failed. Access, WARP, Gateway, Turnstile all went down with it. 2h28m to full recovery.

5/ The fix wasn't adding the second cloud back. It was removing the dependency on having one at all: small objects (median 288 bytes) now live in Cloudflare's own DB, larger ones in R2. p99 latency dropped ~200ms → under 5ms as a side effect.

6/ The redundancy you design for ten million requests a day isn't automatically the redundancy that survives ten billion. Every simplification made under load is a bet about which failure you've stopped worrying about.

---

## Diagram

See: `2026-09-08-cloudflare-workers-kv-gcp-outage-redundancy.excalidraw`

Type: Timeline (confessional style, 4 stages + callout)
Color scheme: Teal (2018 dual-cloud design) → Amber (early-2025 simplification) → Crimson (the outage) → Indigo (own-infra fix) — no red/green good-bad pairing, different palette and layout from the last two infrastructure/storage posts
Key screenshottable number: 90.22% request failure rate, 2h28m outage, p99 latency 200ms → under 5ms
