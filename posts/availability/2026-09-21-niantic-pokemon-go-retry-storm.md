---
date: 2026-09-21
company: Niantic
topic: Niantic load-tested Pokémon GO's launch for 5x its most optimistic traffic estimate; real demand hit roughly 50x within 15 minutes of the Australia/New Zealand launch, and when overloaded backends slowed down instead of crashing outright, the mobile client's retry logic and Google's own load balancer retries synchronized into a thundering herd that spiked request volume to 20x the prior global peak and cut Google Cloud's load balancer capacity worldwide by roughly half — for every GCP customer sharing that infrastructure, not just Niantic
category: availability
post_type: narrative
opening_style: mid_scene_drop
slug: niantic-pokemon-go-retry-storm
---

## Sources

- Google SRE Workbook, Chapter 11: ["Managing Load"](https://sre.google/workbook/managing-load/) — primary source for the Pokémon GO case study: the 5x load-test vs. ~50x actual traffic, the cascading-failure mechanism across Datastore/backends/load-balancing layer, the GFE SSL-reconnection performance regression that cut GCLB's worldwide capacity by roughly 50%, the client retry storm spiking to 20x the previous global RPS peak, Traffic SRE's administrative rate-limiting response, and Niantic's later fix of introducing jitter and truncated exponential backoff to client retries.
- Google Cloud Blog: ["Bringing Pokémon GO to life on Google Cloud"](https://cloud.google.com/blog/products/containers-kubernetes/bringing-pokemon-go-to-life-on-google-cloud) — corroborates the launch traffic exceeding estimates by roughly 50x and describes Google engineers working directly with Niantic during the scaling response.
- Google Cloud Blog: ["How Pokémon GO scales to millions of requests"](https://cloud.google.com/blog/topics/developers-practitioners/how-pok%C3%A9mon-go-scales-millions-requests) — background on the game's later architecture (GKE, Cloud Spanner, Bigtable, Pub/Sub) used only for context, not for the incident's specific numbers.
- Press coverage (KitGuru, SDxCentral, ITPro/CloudPro) independently confirming the "50x expected traffic" figure and the CEO's statement that the global rollout was paused until server capacity caught up.

**Note on sourcing:** Direct fetch of sre.google and highscalability.com was blocked by this environment's network egress policy at write time. The facts above are drawn from search-indexed excerpts of the Google SRE Workbook chapter itself (quoted phrases like "thundering herd," "truncated exponential backoff," and the specific 20x/50% figures appear verbatim across the excerpts), cross-checked against Google's own engineering blog posts and multiple independent press accounts of the same launch.

**Key primary-source detail (not in most summaries):** Most retellings of this story stop at "Pokémon GO launched and the servers couldn't handle it." What the SRE Workbook actually documents is that Niantic's own overload became a capacity problem for Google Cloud customers who had never heard of Pokémon GO. The retry storm didn't just fill up Niantic's backends — it degraded the SSL-reconnection handling inside Google's shared Front End (GFE) layer so badly that GCLB's *worldwide* load-balancing capacity dropped by roughly 50%, because GFE capacity is a shared pool, not a per-customer allocation. A mobile game's launch day retry logic became a global infrastructure incident.

---

## LinkedIn Post

Fifteen minutes after Pokémon GO launched in Australia and New Zealand, the traffic numbers hitting Niantic's dashboards stopped matching any plan anyone had made.

Niantic had load-tested its stack for five times its most optimistic launch estimate. Real demand came in around fifty times that. Google's SRE team, running the infrastructure underneath Niantic's game, watched capacity planning become irrelevant in real time.

What happened next wasn't one system falling over. It was three systems, each behaving reasonably on its own, stacking into something none of them could survive.

Niantic's backends didn't crash cleanly — they slowed down. A slow backend looks different to a load balancer than a dead one: instead of failing fast, requests sitting in Google's front-end layer (GFE) started timing out. GFE, doing exactly what it's built to do, retried the GET requests itself. That's more load stacked on top of load that was already too much.

Meanwhile the Pokémon GO client had its own retry logic: one immediate retry, then constant backoff. Reasonable in isolation. But when an overloaded backend returns a wave of errors all at once, every client that just failed retries in roughly the same instant. That's a thundering herd, and this one spiked request volume to twenty times the previous global peak — not Niantic's normal peak, the peak from the outage already in progress.

That retry storm hit GFE's SSL-reconnection handling hard enough to degrade it worldwide. Google Cloud's global load-balancing capacity dropped by roughly half — for every customer sharing that infrastructure, not just Niantic.

The immediate fix wasn't code. Google's Traffic SRE team throttled how much Pokémon GO traffic the load balancers would even accept, buying enough room for both systems to stabilize. Niantic paused its global rollout and brought new countries online in waves while real capacity caught up.

The lasting fix was rewriting the client's retry strategy: jitter plus truncated exponential backoff, so the next backend hiccup would scatter retries across time instead of synchronizing them into another herd.

No single piece of this was actually broken. Datastore behaved like an overloaded database behaves. GFE behaved like a load balancer facing a slow backend instead of a dead one. The client behaved exactly like an app is supposed to when a request fails — it tried again. Line up three correct behaviors, and global capacity dropped by half.

#SystemDesign #SRE #DistributedSystems #Reliability

**Character count: 2,523 / 3,000 ✓**
**First ~140 chars (mobile hook):** "Fifteen minutes after Pokémon GO launched in Australia and New Zealand, the traffic numbers hitting Niantic's dashboards stopped matching an..." ✓

---

## Twitter / X Thread

1/ Fifteen minutes after Pokémon GO launched in Australia and New Zealand, traffic stopped matching any projection Niantic had made.

2/ Load-tested for 5x their best-case estimate. Real demand: roughly 50x. Three systems, each fine alone, were about to stack into a global outage.

3/ Niantic's backends didn't crash — they slowed down. Slow backends look like timeouts to Google's load balancer (GFE), which retried the GET requests itself. More load on top of too much load.

4/ The mobile client had its own retry logic: one immediate retry, then constant backoff. When a backend hiccup errors out a wave of requests at once, every client retries in the same instant. Thundering herd — spiking to 20x the prior peak.

5/ That retry storm hit GFE's SSL-reconnection handling hard enough to cut Google Cloud's global load-balancer capacity roughly in half. For every customer sharing that infrastructure. Not just Niantic.

6/ Immediate fix: Google's Traffic SRE team throttled how much Pokémon GO traffic the load balancers would even accept. Niantic paused the global rollout, went country by country.

7/ Lasting fix: replace the retry strategy with jitter + truncated exponential backoff, so the next hiccup scatters retries instead of synchronizing them.

8/ Nothing here was actually broken. An overloaded database, a load balancer, and a retrying client all did exactly what they're built to do. Stack three correct behaviors and watch capacity drop by half.

---

## Diagram

See: `2026-09-21-niantic-pokemon-go-retry-storm.excalidraw`

Type: Side-by-side sequence flow (narrative style) — left lane shows the normal request path (Client → GFE/Load Balancer → Niantic Backend → Datastore) under calm, ordinary conditions; right lane shows the same path during the incident, with a feedback loop arrow from the timed-out backend back through GFE's retries and the client's synchronized retries, highlighting exactly where the failure compounds. A numbers banner sits beneath both lanes.
Color scheme: slate blue-gray for the "normal flow" lane (nothing wrong with it, it's just an ordinary day), amber for the backend that's "slow, not down," and deep red-orange for the GFE box to mark where the shared, global resource actually degrades. Deliberately avoids the slate/indigo/mustard/plum palette used in the prior post and the orange/purple/teal/blue palette used two posts ago.
Key screenshottable numbers: load-tested for 5x, actual traffic ~50x, retry storm spikes to 20x the previous global peak, GCLB worldwide capacity cut by ~50%.
