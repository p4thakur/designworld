<!-- sources -->
<!-- Primary: "Cloudflare outage on November 18, 2025" — Cloudflare Blog (official post-mortem) -->
<!-- URL: https://blog.cloudflare.com/18-november-2025-outage/ -->
<!-- Corroborating technical analyses (cross-checked, consistent on all figures below): -->
<!--   https://hackaday.com/2025/11/20/how-one-uncaught-rust-exception-took-out-cloudflare/ -->
<!--   https://www.gremlin.com/blog/reliability-lessons-from-the-2025-cloudflare-outage -->
<!--   https://newrelic.com/blog/observability/what-the-cloudflare-outage-teaches-us-about-system-limits-and-latent-bugs -->
<!-- Key verifiable details (cross-referenced across primary + technical analyses): -->
<!-- 1. 11:05 UTC: gradual ClickHouse cluster permission rollout causes feature-file query to return duplicate schema rows -->
<!-- 2. Bot Management feature file: ~60 features under normal conditions -> 200+ once the query hit an updated cluster node -->
<!-- 3. Feature file regenerated every 5 minutes; only part of the cluster had the new permissions, so each cycle was a coin flip between a good and a bad file -->
<!-- 4. FL2 (new Rust proxy): `Result::unwrap()` on the oversized-file check panics the fl2_worker_thread -> 5xx -->
<!-- 5. FL (old proxy): no crash, but silently scored all traffic with a bot score of 0 -->
<!-- 6. Cloudflare's externally-hosted status page went down independently at nearly the same time, causing an initial (wrong) DDoS hypothesis -->
<!-- 7. Timeline: 11:20 first customer errors -> 13:37 rollback of feature file begins -> 14:24 bad file propagation stopped -> 14:30 core traffic restored -> 17:06 fully normal -->

# Cloudflare's November 2025 Outage: The Failure That Looked Like a DDoS Attack

**Date:** 2026-07-01
**Company:** Cloudflare
**Category:** availability
**Post type:** narrative
**Opening style:** mid_scene_drop
**Slug:** cloudflare-nov-2025-bot-management-outage
**Character count (LinkedIn):** ~2,351

---

## LinkedIn Post

At 11:20 UTC on November 18, 2025, Cloudflare's core proxy started throwing 5xx errors. Then it recovered. Then it broke again. Every few minutes, a huge slice of the internet flickered between working and down.

Here's the system behind that flicker.

Cloudflare's Bot Management runs a machine learning model that scores every request for how likely it is to be a bot. The model reads a "feature file" — a config listing the traits it checks — regenerated every 5 minutes by a query against a ClickHouse cluster.

That morning, Cloudflare was rolling out tighter permission grants on the cluster, one piece at a time. Once the change landed on part of the cluster, the query stopped returning just the feature table — it started returning the underlying schema metadata too, duplicating rows. A file that normally listed about 60 features suddenly listed over 200.

The proxy pre-allocates memory for that file and hard-caps it. Past the limit, the code does `.unwrap()` on a `Result` it assumed could never fail. On Cloudflare's newer proxy engine, FL2, that panic crashed the worker thread — instant 5xx for anyone routed through it. On the older engine, FL, nothing crashed. It just quietly scored every single request as zero — not a bot — and moved on.

Because only part of the ClickHouse cluster had the new permissions, and the file rebuilt every 5 minutes, each cycle was a coin flip: good file or bad file, propagated globally within seconds either way. That's why it looked like flapping instead of a clean outage — engineers would see traffic recover and think they'd fixed it.

Then, by pure coincidence, Cloudflare's own status page — hosted outside its network — went down at almost the same moment for an unrelated reason. For a while, the incident team seriously suspected a DDoS attack on two fronts at once.

Core traffic was stable again by 14:30 UTC, full recovery by 17:06.

No one shipped reckless code that day. The permissions rollout was routine. The file-size limit existed on purpose. The bug lived in the gap between three separate, individually reasonable decisions — a database migration, a hardcoded safety limit, and an error path nobody expected to hit.

The scariest outages aren't caused by the change that looked risky. They're caused by the one three systems away from what actually breaks.

#SystemDesign #Engineering #SRE #Cloudflare

---

## Twitter / X Version

1/ Nov 18, 2025: Cloudflare's proxy starts throwing 5xx errors. Then recovers. Then breaks again. Every few minutes, a huge chunk of the internet flickered between up and down.

Here's why it flickered instead of just failing.

2/ Cloudflare's Bot Management scores every request with an ML model. The model reads a "feature file" rebuilt every 5 min by a ClickHouse query.

That morning, a permissions rollout on the cluster made the query return duplicate schema rows. ~60 features became 200+.

3/ The proxy hard-caps the feature file size and pre-allocates memory for it. Past the cap, the code calls `.unwrap()` on a Result it assumed could never be an Err.

New proxy engine (FL2): panic, crash, 5xx.
Old engine (FL): no crash — just silently scored every request as "not a bot."

4/ Only part of the ClickHouse cluster had the new permissions. The file rebuilt every 5 min. So each cycle was a coin flip — good file or bad file, pushed globally in seconds either way.

That's why it looked like flapping, not a clean outage.

5/ Bonus chaos: Cloudflare's own status page (hosted outside its network) went down at almost the same moment, for an unrelated reason. The incident team briefly suspected a two-front DDoS attack.

6/ Stable by 14:30 UTC. Fully resolved 17:06.

No single decision here was reckless — a routine permissions change, a safety limit, an error path nobody expected to hit. The outage lived in the gap between three separately reasonable choices.

---

## Excalidraw Diagram

**File:** 2026-07-01-cloudflare-nov-2025-bot-management-outage.excalidraw
**Type:** Sequence flow with failure branch (narrative)
**Color scheme:** Blue (ClickHouse), purple (query), amber (feature file — the swelling artifact), red (FL2 crash path), yellow (FL silent-failure path), teal (flapping mechanism), violet (status-page coincidence). Light canvas.
**Screenshottable stat:** "60 → 200+ features · rebuilt every 5 min · 11:20 → 14:30 → 17:06 UTC"

### Layout

```
Title: "Cloudflare, Nov 18 2025: The Outage That Flickered Instead of Failing"
Subtitle: "60 → 200+ features · file rebuilt every 5 min · 11:20 → 14:30 → 17:06 UTC"

[ClickHouse cluster]  ->  [Feature-file query]  ->  [Bot Mgmt feature file]
 11:05 rolling             reruns every 5 min          ~60 -> 200+ rows
 permission update          returns dup rows            (past hardcoded cap)
                                                          /              \
                                                         v                v
                                          [FL2 proxy: .unwrap()      [FL proxy: no crash —
                                           panics -> 5xx]             bot score = 0 for all]

[Only part of cluster updated + 5-min rebuild = coin flip every        [Coincidence: status page
 cycle -> flapping between good/bad file, 11:20-14:30 UTC]              (external) also down ->
                                                                         briefly suspected DDoS]

Timeline: 11:05 permission change -> 11:20 first errors -> 13:37 rollback begins
          -> 14:30 fixed globally -> 17:06 fully normal
```
