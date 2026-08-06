<!-- sources -->
<!-- Primary: -->
<!--   Adrian Cockcroft, "Netflix Heads into the Clouds," USENIX ;login: — -->
<!--     https://www.usenix.org/system/files/login/articles/cockcroft_0.pdf -->
<!--   Yury Izrailevsky, "Completing the Netflix Cloud Migration," Netflix Tech Blog (Feb 2016) — -->
<!--     https://netflixtechblog.com/completing-the-netflix-cloud-migration-29e0b3ddfd11 -->
<!--   NBC News, contemporaneous coverage of the Aug 2008 Netflix DVD-shipping outage — -->
<!--     https://www.nbcnews.com/id/wbna23795233 and https://www.nbcnews.com/id/wbna23811973 -->
<!--   Netflix/Hystrix GitHub Wiki, "How it Works" — https://github.com/Netflix/Hystrix/wiki -->
<!-- Corroborating: -->
<!--   ByteByteGo, "A Brief History of Scaling Netflix" — https://blog.bytebytego.com/p/a-brief-history-of-scaling-netflix -->
<!--   InfoWorld, "Big movies, big data: Netflix embraces NoSQL in the cloud" — -->
<!--     https://www.infoworld.com/article/2171162/big-movies-big-data-netflix-embraces-nosql-in-the-cloud.html -->
<!--   Sujeet Jaiswal, "Netflix: From Monolith to Microservices — A 7-Year Architecture Evolution" — -->
<!--     https://sujeet.pro/articles/netflix-microservices-evolution -->
<!--   Medium / S.C.A.L.E, "Talking microservices with the man who made Netflix's cloud famous" (Cockcroft interview) — -->
<!--     https://medium.com/s-c-a-l-e/talking-microservices-with-the-man-who-made-netflix-s-cloud-famous-1032689afed3 -->
<!--   Silicon.co.uk, "Netflix Completes Eight Year Cloud Migration And Shuts Last Data Centre" — -->
<!--     https://www.silicon.co.uk/cloud/cloud-management/netflix-completes-cloud-migration-data-centre-185843 -->
<!-- Note: direct WebFetch of netflixtechblog.com, usenix.org, infoworld.com, medium.com, and sujeet.pro all returned -->
<!-- HTTP 403 under this session's egress policy (same class of gateway-level denial hit on prior posts in this series). -->
<!-- Facts below were cross-checked across multiple independent web-search-result excerpts that quote or closely -->
<!-- paraphrase the primary sources directly, including the Aug 2008 outage details and the Hystrix mechanism. -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Aug 11, 2008: monitors flagged a corruption event in Netflix's central Oracle database. DVD shipping — then -->
<!--   the core business (~$1.36B in revenue) — went down for 3 days across all 55 Los Gatos-area shipping centers. -->
<!-- 2. Adrian Cockcroft (Netflix cloud architect): "we had a single data center, which meant we had a single point of -->
<!--   failure." Netflix rejected adding redundancy to the existing datacenter architecture and chose to rebuild -->
<!--   cloud-native rather than lift-and-shift. -->
<!-- 3. Migration was incremental, monolith and new services run in parallel for years: first production service moved -->
<!--   to AWS in 2009; the streaming API and hundreds of services followed through 2010-2012; billing, the last piece, -->
<!--   moved to AWS in Jan 2016, at which point Netflix shut down the last data center bits behind its streaming service -->
<!--   (~7.5 years after the outage). -->
<!-- 4. Cassandra replaced Oracle for scale-out services: denormalized, query-shaped tables (no joins, no cross-domain -->
<!--   foreign keys) instead of one normalized schema — a corruption or bug touching one service's data cannot reach -->
<!--   another service's keyspace. -->
<!-- 5. Hystrix (Netflix OSS, per its own wiki/README): a latency and fault-tolerance library that isolates each -->
<!--   outbound dependency call in its own thread pool (the bulkhead pattern) and trips a circuit breaker on rising -->
<!--   error/latency stats, so calls fail fast instead of queuing — a stalled dependency can only exhaust its own pool, -->
<!--   not the caller's. -->
<!-- 6. The 2012-era Java resilience stack (Hystrix, Eureka, Ribbon, Zuul 1) itself went into maintenance mode around -->
<!--   2018-2020 as Netflix moved fault tolerance out of the application runtime and into an Envoy-based sidecar mesh. -->

# Netflix Looked at a 3-Day Outage and Deleted the Idea of Having One Datacenter

**Date:** 2026-08-06
**Company:** Netflix
**Category:** microservices
**Post type:** structured
**Opening style:** the_decision
**Slug:** netflix-2008-outage-microservices-migration
**Character count (LinkedIn):** ~2604

---

## LinkedIn Post

Netflix looked at a three-day outage and made an unusual call: don't harden the datacenter. Delete the idea of having just one.

On August 11, 2008, monitors caught a corruption event in Netflix's central Oracle database. DVD shipping — still the whole business, about $1.36B in revenue — went dark for three days across all 55 shipping centers. One schema, one datacenter. When it broke, everything wired to it broke with it.

The obvious fix is redundancy: mirror the database, add a hot standby, buy a bigger box. Netflix's engineers rejected it. A standby in the same datacenter still shares the same schema across DVD shipping, billing, and browsing — joined and foreign-keyed together for convenience. Double the hardware and the blast radius of one corruption event is still 100% of the company. Vertical scaling doesn't shrink that radius, it just delays hitting the ceiling.

So the real problem wasn't capacity. It was that everything shared fate. The fix had to be structural: give every feature its own service, its own datastore, and a runtime that can't let one slow dependency drag the rest down with it.

That's two mechanisms, not one, doing the same job at different layers. Cassandra replaced Oracle because it denormalizes data around each query instead of normalizing it into one shared schema — no cross-domain joins means no single write can corrupt two domains at once, and each service got its own keyspace, so a bug in recommendations literally cannot touch billing's rows. Hystrix gave every outbound call its own thread pool, a bulkhead: a stalled dependency exhausts only its own pool and trips a circuit breaker, failing fast instead of queuing requests that starve the caller.

Database and thread pool, same shape of fix: shrink the blast radius down to one box, whichever kind of box is failing.

It took over seven years, monolith and microservices running in parallel the whole time — first AWS service in 2009, hundreds of services and the streaming API by 2012, billing (the last piece) off the last data center in January 2016. None of it was free: eventual consistency instead of transactions, write amplification from denormalizing the same fact into multiple tables, years of double operational load running two architectures at once. Even the fix aged — by 2018 Hystrix's own per-dependency thread pools became the next bottleneck, and Netflix moved resilience out of the app runtime entirely, into an Envoy sidecar mesh.

The datacenter wasn't the failure. Being one single thing was.

Sources in comments.

#SystemDesign #Netflix #Microservices #CloudMigration

---

## Twitter / X Version

1/ Aug 11, 2008: Netflix's monitors catch a corruption event in its one Oracle database. DVD shipping — the whole business, ~$1.36B in revenue — goes dark for 3 days across all 55 shipping centers. One schema, one datacenter, one point of failure.

2/ Obvious fix: redundancy. Mirror the DB, add a hot standby, buy a bigger box. Netflix rejected it — a standby in the same datacenter still shares the same schema across DVD shipping, billing, browsing. One corruption event still takes out 100% of the company either way.

3/ The real problem wasn't capacity, it was shared fate. So Netflix rebuilt around a different shape: every feature gets its own service, its own datastore, and a runtime that can't let one slow dependency drag the rest down.

4/ Cassandra replaced Oracle because it denormalizes around each query instead of normalizing around one schema — no cross-domain joins, so no single write touches two domains. Each service got its own keyspace. A bug in recommendations can't touch billing's rows.

5/ Hystrix gave every outbound call its own thread pool — a bulkhead. A stalled dependency exhausts only its own pool and trips the breaker, failing fast instead of stacking up requests that starve the caller. Database and thread pool, same fix, two layers.

6/ Took 7+ years, monolith and microservices running in parallel the whole time. First AWS service: 2009. Billing, the last piece: off the last data center, Jan 2016. Even the fix aged — by 2018 Hystrix's own thread-pool model became the bottleneck, replaced by an Envoy sidecar mesh.

---

## Excalidraw Diagram

**File:** 2026-08-06-netflix-2008-outage-microservices-migration.excalidraw
**Type:** Migration timeline (horizontal flow, 2008 → 2020) paired with a structural before/after "blast radius" comparison.
**Color scheme:** Rose/red for the monolith side — earned here, not decorative, since it's the side that actually failed catastrophically. Indigo for the microservices side, representing the new (not "correct") shape. Slate for neutral timeline/history text.
**Screenshottable stat:** "Aug 11, 2008: 1 corrupted database = 3 days, 55 shipping centers, ~$1.36B business down. One circuit breaker trips instead."

### Layout

```
Title: "Netflix Looked at a 3-Day Outage and Deleted the Idea of Having One Datacenter"
Subtitle: "Aug 2008 - Jan 2016 — how one corrupted Oracle database pushed Netflix off a single datacenter and onto hundreds of independently-failing microservices"

[TIMELINE — slate, 5 points]
  Aug 2008 -> 2009 -> 2010-2012 -> Jan 2016 -> 2018-2020
  Narrative under each stage:
    "Aug 2008 — Oracle corruption event. DVD shipping dark for 3 days, all 55 shipping centers idle."
    "2009 — First production service moves to AWS. Incremental migration begins, monolith kept running."
    "2010-2012 — Streaming API and hundreds of services move off the monolith. Eureka + Hystrix built in-house."
    "Jan 2016 — Billing, the last piece, moves to AWS. Last data center bits shut down. ~7.5 years after the outage."
    "2018-2020 — Hystrix's own thread-pool model becomes the bottleneck; resilience moves into an Envoy sidecar mesh."

[LEFT PANEL — rose, "MONOLITH (pre-2008)"]
  Box "Single Oracle DB" containing stacked labels: "DVD shipping", "billing", "browsing" — joined by lines showing
  shared schema / cross-domain foreign keys
  Caption: "1 corruption event = 100% of company down. 3 days. All 55 shipping centers."

[RIGHT PANEL — indigo, "MICROSERVICES (post-2012)"]
  4 small service boxes: "Shipping Svc", "Billing Svc", "Browse Svc", "Reco Svc" — each with its own small
  "Cassandra keyspace" label, no lines connecting their data stores to each other
  One box ("Reco Svc") shown mid-failure (red outline, "circuit open") with a "Hystrix bulkhead" label on the
  arrow feeding it, that arrow shown cut off / thread pool full
  Caption: "1 service fails. Bulkhead caps the blast radius at its own thread pool — the other three don't notice."

[FOOTNOTE — slate]
No shared schema means no single corruption event can cross domains. No shared thread pool means one slow
dependency can't starve the others. Different mechanism, same shape of fix: shrink the blast radius to one box.
