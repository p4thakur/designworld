<!-- sources -->
<!-- Primary: -->
<!--   Heroku, "Routing and Web Performance on Heroku: a FAQ" — https://blog.heroku.com/routing_and_web_performance_on_heroku_a_faq -->
<!--   Heroku, "Updated Network Routing for Improved Performance" — https://blog.heroku.com/routing_performance_update (mirror: https://www.heroku.com/blog/routing_performance_update/) -->
<!--   Heroku, "Addressing Bamboo Routing Performance" — https://blog.heroku.com/bamboo_routing_performance -->
<!--   Genius Engineering (Rap Genius), "Heroku's Ugly Secret" (Feb 2013) — https://genius.engineering/herokus-ugly-secret/ -->
<!-- Corroborating: -->
<!--   TechCrunch, "Heroku Admits To Performance Degradation Over The Past 3 Years After Criticism From Rap Genius" — -->
<!--     https://techcrunch.com/2013/02/14/heroku-admits-to-performance-degradation-over-the-past-3-years-after-criticism-from-rap-genius/ -->
<!--   Railsware Blog, "Heroku Queuing Time: Problem and Solution" — https://railsware.com/blog/heroku-queuing-time-part1-problem/ -->
<!--   Artsy Engineering, "The Impact of Heroku's Routing Mesh and Random Routing" — -->
<!--     https://artsy.github.io/blog/2013/02/17/impact-of-heroku-routing-mesh-and-random-routing/ -->
<!--   Heroku Dev Center, "HTTP Routing" — https://devcenter.heroku.com/articles/http-routing -->
<!--   Heroku Blog, "Router 2.0 and HTTP/2 Now Generally Available" / "Tips & Tricks for Migrating to Router 2.0" — -->
<!--     https://www.heroku.com/blog/router-2dot0-http2-now-generally-available/ , https://www.heroku.com/blog/tips-tricks-router-2dot0-migration/ -->
<!-- Note: direct WebFetch of blog.heroku.com, genius.engineering, railsware.com, artsy.github.io, and judoscale.com all -->
<!-- returned HTTP 403 under this session's egress policy (same class of gateway-level denial hit on prior posts in this -->
<!-- series). Facts below were cross-checked across multiple independent web-search-result excerpts that quote or closely -->
<!-- paraphrase the primary sources directly, including the direct Oren Teich apology quote and the mechanism description -->
<!-- from Heroku's own routing-performance-update post. -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Heroku's original ("Bamboo"-era) routing mesh was small enough that its per-router view of dyno busy/idle state -->
<!--   was close to the whole fleet's actual state, so requests were routed to genuinely idle dynos — what Heroku -->
<!--   marketed as "intelligent routing." -->
<!-- 2. As traffic grew starting around mid-2010, Heroku added more router nodes to the mesh. Each router makes its -->
<!--   dispatch decision independently, based only on the requests it personally has seen — there is no shared/global -->
<!--   queue-state registry across router nodes. Heroku's own routing-performance-update post describes this directly: -->
<!--   a slow request on one router's view leaves other routers, unaware, still dispatching to that same dyno. -->
<!-- 3. This shift was undocumented and unreported in the platform's metrics for roughly three years, until James -->
<!--   Somers/Rap Genius published "Heroku's Ugly Secret" (Feb 2013), which calculated the queueing cost precisely and -->
<!--   went viral on Hacker News. -->
<!-- 4. Heroku's GM Oren Teich publicly admitted the degradation; TechCrunch quotes his apology verbatim: "We failed to -->
<!--   explain how our product works. We failed to help our customers scale. We failed our community at large." -->
<!-- 5. The practical bite: Heroku's default web dynos ran single-threaded Unicorn (concurrency = 1 request at a time), -->
<!--   so a request routed behind an in-flight slow request queues for the remainder of that request's duration -->
<!--   regardless of other dynos sitting idle. -->
<!-- 6. Heroku's remediation was primarily application-layer: documentation pushed customers toward concurrent web -->
<!--   servers (Unicorn with multiple workers, later Puma with threads) so a single dyno could serve more than one -->
<!--   request at a time, reducing the cost of a bad routing pick. The router's shared-nothing, no-global-state design -->
<!--   was not replaced. -->
<!-- 7. Router 2.0 (later Heroku router generation) added persistent keep-alive connections between routers and dynos -->
<!--   (removing per-request TCP handshake overhead) and, for large dyno pools, an availability-zone-aware bias in -->
<!--   dyno selection — but did not introduce cross-router shared queue-depth state. -->

# Heroku Sold "Intelligent Routing" for Three Years After It Quietly Became Random

**Date:** 2026-08-03
**Company:** Heroku
**Category:** performance
**Post type:** confessional
**Opening style:** cold_fact
**Slug:** heroku-random-routing-shared-nothing
**Character count (LinkedIn):** ~2670

---

## LinkedIn Post

In 2007, Heroku's routing mesh did something specific: it tracked which of your dynos were busy and sent each new request to one that was actually free. That's what "intelligent routing" meant, and it's part of what people paid for.

By 2010, it quietly stopped being true. Nobody documented the change. Nobody updated the metrics. For three years, customers paid for idle-aware routing and got something close to random chance — until Rap Genius's "Heroku's Ugly Secret" went viral in February 2013.

Here's the mechanism, because "it got random" undersells what happened. Heroku's router tier scales horizontally — add nodes as traffic grows, each one decides independently, zero coordination with the others. That's not a bug; it's what lets the router tier scale without a shared-state bottleneck. At three routers, each one's local view of "who's busy" was close enough to the whole fleet's truth that routing looked intelligent. At hundreds of routers, that stops holding: Router 12 and Router 47 have never exchanged a message about dyno B's queue. Both check their own local state, both see it as idle, both dispatch in the same instant. Dyno A and dyno C, actually idle, get nothing. Do that across hundreds of independent routers and the aggregate outcome converges to statistically random placement — no matter how "smart" any single router's local logic is.

The obvious fix — one global registry of dyno busy-state every router checks first — is exactly what shared-nothing routing was built to avoid. It means a synchronized read (and write) in front of every HTTP request, fleet-wide: either a single coordination point that becomes the new bottleneck, or a gossip layer that's stale by the time you read it, reintroducing the same collision under load.

It mattered because Heroku's dynos ran single-threaded Unicorn workers, one request at a time. Land behind a 15-second request and your 100ms request takes 15.1 seconds — while a dyno two racks over sits empty.

Heroku's GM Oren Teich, in the apology: "We failed to explain how our product works. We failed to help our customers scale. We failed our community at large."

The fix that shipped wasn't a smarter router. It was pushing concurrency down a layer — telling customers to run Puma or multi-worker Unicorn so one slow request couldn't monopolize a whole dyno's queue. Router 2.0, years later, added keep-alive connections and availability-zone-aware bias. The routers still don't share queue depth with each other. The trade made in 2010 — stateless horizontal scalability over global routing accuracy — is still the trade today.

#SystemDesign #DistributedSystems #Heroku #BackendEngineering

---

## Twitter / X Version

1/ In 2007, Heroku's router mesh tracked which of your dynos were busy and sent new requests to the ones that were free. That's "intelligent routing" — part of what people paid for. By 2010 it quietly stopped being true, and nobody said so for three years.

2/ The router tier scales horizontally: add nodes as traffic grows, each one decides independently, zero coordination. That's exactly what lets it scale without a shared-state bottleneck. At three routers, each one's local view was close enough to the whole fleet's truth.

3/ At hundreds of routers, that breaks. Router 12 and Router 47 have never talked. Both see the same dyno as idle right now. Both dispatch in the same instant. Two other dynos sit empty. Do that across hundreds of routers and the outcome converges to statistically random.

4/ The obvious fix — one shared registry every router checks before dispatching — is exactly what shared-nothing was built to avoid. It's a synchronized read+write in front of every request, fleet-wide: one new bottleneck, or a gossip layer that's stale exactly when it matters.

5/ It mattered because Heroku's dynos ran single-threaded Unicorn: one request at a time. Land behind a 15s request and your 100ms request takes 15.1s, while a dyno two racks over sits idle. Rap Genius's Feb 2013 post made this impossible to ignore.

6/ Heroku's GM Oren Teich: "We failed to explain how our product works. We failed to help our customers scale. We failed our community at large." The fix that shipped wasn't a smarter router — it was telling customers to run concurrent workers so one slow request couldn't own a dyno's whole queue. The routers still don't share state today.

---

## Excalidraw Diagram

**File:** 2026-08-03-heroku-random-routing-shared-nothing.excalidraw
**Type:** Confessional timeline (small mesh → quiet drift → public admission → partial fix) paired with a structural snapshot of the actual collision mechanism — two independent routers converging on the same dyno while two truly idle dynos sit untouched.
**Color scheme:** Slate/teal for the timeline itself (a measured, factual record — nothing dramatic, just what happened and when). Rose/red only on the one dyno that actually collides, and only there — marking the specific failure, not the whole system, since the shared-nothing design itself wasn't wrong, it just crossed a threshold. Teal for the two routers, showing they're doing exactly what they were built to do.
**Screenshottable stat:** "Router 12 and Router 47 have never exchanged a message about Dyno B's queue. Both see it as idle. Both dispatch in the same instant — while Dyno A and Dyno C sit empty."

### Layout

```
Title: "Heroku Sold 'Intelligent Routing' for Three Years After It Quietly Became Random"
Subtitle: "Feb 2013 — how a shared-nothing router mesh that scaled perfectly well also drifted into statistically random dispatch"

[TIMELINE — horizontal slate line, 4 teal dots]
  2007-2009: "Few routers. Each one's local view of dyno state ≈ the whole fleet's truth. Routing is genuinely idle-aware."
  2010: "Router fleet grows with traffic. No shared queue-state added between nodes. Routing quietly drifts toward random."
  Feb 2013: "Rap Genius's 'Heroku's Ugly Secret' goes viral. GM Oren Teich admits it publicly."
  Router 2.0 (later): "Keep-alive connections + AZ-aware bias cut overhead. Routers still don't share queue depth."

[STRUCTURAL SNAPSHOT — "THE COLLISION, MADE VISUAL"]
  Two teal ellipses labeled "Router 12" and "Router 47" sit above three dyno rectangles.
  Dyno A (slate, idle) — untouched.
  Dyno B (rose outline) — both routers' arrows land here at once. Label: "mid 15s request."
  Dyno C (slate, idle) — untouched.
  Caption beneath: "Router 12 and Router 47 have never exchanged a message about Dyno B's queue. Each
  independently sees it as idle right now, so both dispatch in the same instant. Dyno A and Dyno C, actually
  idle, get nothing. With enough independent routers deciding this way, the aggregate outcome converges to
  statistically random placement — no matter how 'intelligent' any single router's local logic is."

[FOOTNOTE — slate]
Heroku's dynos ran single-threaded Unicorn: one request at a time. A request that lands behind a 15-second
request takes 15.1 seconds to finish, even with an idle dyno two racks over. Oren Teich, Heroku GM, Feb 2013:
"We failed to explain how our product works. We failed to help our customers scale. We failed our community
at large."
```
