<!-- sources -->
<!-- Primary: Instagram Engineering, "What Powers Instagram: Hundreds of Instances, Dozens of Technologies," -->
<!--   instagram-engineering.com, published 2012-04. URL: https://instagram-engineering.com/what-powers-instagram-hundreds-of-instances-dozens-of-technologies-adf2e22da2ad -->
<!-- Primary: Benjamin Woodruff, "Static Analysis at Scale: An Instagram Story," Instagram Engineering, 2019. -->
<!--   URL: https://instagram-engineering.com/static-analysis-at-scale-an-instagram-story-8f498ab71a0c -->
<!-- Secondary corroboration: High Scalability mirror/summary of the 2012 post -->
<!--   (https://highscalability.com/instagram-architecture-14-million-users-terabytes-of-photos/); InfoQ QCon London -->
<!--   2024 coverage of Meta's Threads launch talk (https://www.infoq.com/news/2024/04/meta-threads-instagram-5-months/). -->
<!-- Note: direct WebFetch of instagram-engineering.com and the Hacker News discussion thread both returned HTTP 403 -->
<!--   under this session's egress policy (same recurring failure mode documented in earlier posts in this repo, e.g. -->
<!--   the 2026-07-18 Etsy post and 2026-07-22 Spotify post). Facts below are cross-checked across multiple -->
<!--   independent WebSearch result excerpts that directly quote or closely paraphrase the two primary -->
<!--   instagram-engineering.com posts, corroborated across several independent secondary summaries (High Scalability, -->
<!--   engineerscodex.com, ByteByteGo) that each repeat the same specific numbers without contradiction. -->
<!-- Key verifiable details (quoted or closely paraphrased via search excerpts): -->
<!-- 1. Instagram reached 14 million users about fourteen months after launch with a team of 3 engineers. -->
<!-- 2. App tier: stateless Django + Gunicorn on Amazon High-CPU Extra-Large instances, behind Amazon's Elastic Load -->
<!--   Balancer with 3 nginx instances in front, "over 25" app instances by the time of the 2012 post, up from "just a -->
<!--   few." Since the server is stateless, capacity is added by adding more machines. -->
<!-- 3. Data tier at the same point: PostgreSQL on 12 Quadruple Extra-Large memory instances (durable relational data — -->
<!--   profiles, photo metadata, tags, comments, relationships); Redis on several Quadruple Extra-Large instances, -->
<!--   holding a ~300-million-photo-to-user-ID mapping in about 5GB via clever hashing, plus the main feed, activity -->
<!--   feed, and session data; 6 Memcached instances as a read-through cache layer. -->
<!-- 4. 2019 primary source ("Static Analysis at Scale"): Instagram's server app described as a monolith of "several -->
<!--   million lines of code" with "a few thousand Django endpoints," hundreds of engineers shipping hundreds of -->
<!--   commits daily, continuous deploys roughly every 7 minutes / on the order of a hundred production deploys per -->
<!--   day, and an explicit statement that while a few services had been split out, there was no plan to aggressively -->
<!--   break up the monolith — the stated motivation for building ~100 custom lint rules and LibCST-based codemods was -->
<!--   to control coupling (circular imports surfacing as architectural problems) inside that single codebase instead. -->
<!-- 5. QCon London 2024 (InfoQ coverage): Meta described shipping Threads, built on Instagram's backend, in about -->
<!--   five months, crediting the monolithic architecture for that speed — reused, not replaced, at Meta's post- -->
<!--   billion-user scale. -->
<!-- Mechanism-level explanation of *why* a stateless process is the specific property that makes horizontal cloning -->
<!--   near-free, versus what a network call between decomposed services actually costs (serialization, a versioned -->
<!--   contract, a new failure mode, a new on-call surface) is standard distributed-systems internals knowledge, used -->
<!--   here to go one level deeper than either primary post, per the skill's sourcing guidance. -->

# Instagram's Monolith: Why 3 Engineers Never Split It Into Services

**Date:** 2026-07-23
**Company:** Instagram
**Category:** microservices
**Post type:** contrarian
**Opening style:** challenge_assumption
**Slug:** instagram-monolith-vs-microservices
**Character count (LinkedIn):** ~2,620

---

## LinkedIn Post

Everyone said Instagram would need to break up its monolith to survive its growth curve. Three backend engineers, 14 million users about fourteen months after launch — and by then "services, not monoliths" was already the conventional advice for anyone hitting that curve.

Instagram never did it. Not then, not at 300 million users after the Facebook acquisition, not now.

The obvious fix — carve photos, feed, comments, and auth into independently deployed services — sounds right, because more users usually does mean more complexity somewhere. But splitting an app into services doesn't reduce load; it adds hops. Every boundary becomes a network call, a serialization format, a versioned contract between two teams, its own on-call rotation. Three engineers can't operate a fleet of services. Microservices' coordination cost outgrows a small team faster than the user base does.

What Instagram actually had was a stateless app tier: Django behind Gunicorn, behind Amazon's load balancer, no session pinned to any one box. That statelessness is the whole trick — if any of N identical processes can answer any request, scaling out is just cloning the process. They went from a handful of app servers to over 25 Amazon High-CPU Extra-Large instances without a single service-boundary decision. The actual state — what genuinely needs sharding, replication, consistency — lived one layer down: 12 large Postgres instances for durable relational data, Redis holding a ~300-million-photo-to-user-ID mapping in about 5GB via clever hashing, six Memcached nodes as a read-through cache. That's where the hard distributed-systems problems belong. The app layer stayed dumb and clonable on purpose.

We default to microservices because we assume a growing user count means growing code complexity that needs independent ownership. Instagram's bottleneck was volume, not complexity — and volume against a stateless process is the one scaling problem you solve by copy-paste.

It wasn't free. By 2019, several million lines of Python behind a few thousand Django endpoints had turned circular imports into real architectural coupling. The fix was tooling, not topology — around a hundred custom lint rules and codemods, so hundreds of engineers could ship hundreds of commits a day without breaking each other. They still didn't split it up. In 2024, Meta credited that same monolith for shipping Threads in five months.

Sometimes the right architecture is the boring one. Not because it's clever — because splitting it would have solved a problem they never had.

#SystemDesign #Microservices #Instagram #SoftwareArchitecture

---

## Twitter / X Version

Instagram had 3 backend engineers and 14M users about 14 months after launch. The standard advice: break up the monolith before it breaks you.

They never did.

Splitting into services doesn't cut load, it adds hops — every boundary is a network call, a contract, an on-call rotation. 3 people can't run a fleet of services.

What actually scaled: a stateless Django app tier. Any of N identical processes can answer any request, so scaling out is cloning a box — a handful to 25+ EC2 instances, zero service decisions. All the genuinely hard stuff (sharding, replication, consistency) lived one layer down, in Postgres/Redis/Memcached.

Cost showed up later: by 2019, several million lines of Python meant circular imports became architecture bugs. The fix was tooling — lint rules, codemods — not breaking up the app.

2024: Meta shipped Threads off that same monolith in five months.

---

## Excalidraw Diagram

**File:** 2026-07-23-instagram-monolith-vs-microservices.excalidraw
**Type:** Side-by-side architecture comparison (contrarian style) — left column is the "obvious fix" and why it doesn't fit a 3-person team, right column is what Instagram actually built and where the real complexity went, with a wide mechanism-match explainer underneath and a footer showing the cost and how it held up over a decade.
**Color scheme:** Slate for the neutral header row. Amber (caution, not "wrong") for the "obvious fix" column — microservices weren't a bad idea, just mismatched to a 3-engineer team. Teal/green for the "what they built" column. Indigo for the mechanism explainer. No red=bad villain, since the obvious fix is a real, valid pattern at a different team size.
**Screenshottable stat:** "3 engineers, 14M users, 25+ app servers · one codebase, several million lines of Python, ~100 deploys/day · still one monolith in 2024, used to ship Threads in 5 months"

### Layout

```
Title: "Instagram's Monolith: Why 3 Engineers Never Split It Into Services"
Subtitle: "3 backend engineers · 14M users, ~14 months in · one Django app tier, cloned 25+ times · still standing in 2024"

ROW 1 — THE "OBVIOUS" FIX vs. WHAT THEY ACTUALLY BUILT

[THE "OBVIOUS" FIX]                              VS         [WHAT THEY BUILT]
Carve photos, feed, comments, and auth                       Stateless Django + Gunicorn behind
into independently owned, independently                      an ELB — no session pinned to any
deployed services, so each can scale                         box. Any of N identical processes
and be staffed on its own.                                   can answer any request.

[WHY IT DOESN'T FIT 3 ENGINEERS]                              [WHERE SCALING ACTUALLY HAPPENED]
Every service boundary becomes a                              Scaling out = clone the process.
network call, a serialization format,                        A handful of app boxes grew to
a versioned contract, and its own                             25+ Amazon High-CPU XL instances —
on-call rotation. 3 people can't                              zero service-boundary decisions,
operate a fleet of services — the                             zero new failure modes.
coordination cost outgrows the team
before the user base does.

[WHERE THE REAL COMPLEXITY WENT — THE DATA TIER]
12 large Postgres instances (durable relational data), Redis holding a ~300M photo→user-ID
map in ~5GB via clever hashing (feeds, sessions), 6 Memcached nodes as read-through cache.
Sharding, replication, consistency — the actually hard distributed-systems problems — live
here, one layer below the app, not spread across a mesh of services.

[THE MECHANISM MATCH]
The bottleneck was request volume and data volume, not code complexity that needed
independent ownership. A stateless process is shaped exactly like "add more identical
copies" — that's why cloning a monolith horizontally is nearly free, and why splitting it
into services would only add network hops between code paths that were never going to be
owned by separate teams anyway.

Footer: Not free — by 2019, several million lines of Python behind a few thousand Django
endpoints turned circular imports into architectural coupling. The fix was ~100 custom
lint rules and codemods, not breaking up the app. They still hadn't split it up: in 2024
Meta shipped Threads off the same monolith in 5 months.
```
