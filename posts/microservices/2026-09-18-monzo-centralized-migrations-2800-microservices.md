---
date: 2026-09-18
company: Monzo
topic: Monzo stopped letting individual service-owning teams decide when their microservice takes a platform-wide migration, and instead centralized migrations across its 2,800+ microservice fleet under one platform team, because per-team autonomy was quietly the reason migrations never finished
category: microservices
post_type: structured
opening_style: the_decision
slug: monzo-centralized-migrations-2800-microservices
---

## Sources

- Monzo Engineering Blog: ["How we run migrations across 2,800 microservices"](https://monzo.com/blog/how-we-run-migrations-across-2800-microservices) — primary source (2024) for the current fleet size, the shift to a centrally-driven migration model, the 80/20 automation principle, and the use of Monzo's own config service for gradual roll-forward/rollback of migrations.
- QCon London 2020: ["Modern Banking in 1500 Microservices"](https://www.infoq.com/presentations/monzo-microservices/) by Matt Heath and Suhail Patel — primary talk corroborating the ~1,500-service count in 2020 and Monzo's Go/monorepo standardization.
- Monzo Engineering Blog: ["Humans who can RPC: Securing staff access to 2,000 microservices"](https://monzo.com/blog/2022/05/26/humans-who-can-rpc-securing-staff-access-to-microservices) — corroborates the ~2,000-service count in 2022 and describes the config service as a Cassandra-backed, request-response system used elsewhere in Monzo's platform.
- The Register: ["How does Monzo keep 1,600 microservices spinning?"](https://www.theregister.com/2020/03/09/monzo_microservices/) — independent 2020 corroboration of the service count and the Go-monorepo approach.

**Note on sourcing:** Direct fetch of monzo.com, theregister.com, and infoq.com was blocked by this environment's network egress policy at write time. The facts above are drawn from search-indexed excerpts of Monzo's own engineering blog posts and the QCon talk, cross-checked against the independent Register write-up, which agree on the same service-count trajectory (1,500 in 2020, ~2,000 in 2022, 2,800+ by 2024) and the same centralized-migration mechanism.

**Key primary-source detail (not in most summaries):** Most retellings of Monzo's microservices story stop at "they run thousands of services." The detail that doesn't show up in a generic summary is what changed operationally as the count kept climbing: Monzo's platform team didn't try to get faster at asking each of 2,800 teams for permission — they removed the ask. Migrations are now driven end-to-end by a dedicated team applying an 80/20 automation rule (codemod the common shape, hand-hold the real outliers), and rolled out gradually through Monzo's own config service — the same production Cassandra-backed system already serving live traffic — so a migration can be pushed to a slice of services and rolled back in seconds, without waiting on any other team's calendar.

---

## LinkedIn Post

Monzo looked at 2,800 independently-owned microservices and made an unusual call: stop letting individual teams decide when their service takes a platform migration.

Every microservices team learns the same rule early: you build it, you own it, you decide when it changes. Monzo lived by that as its platform grew from roughly 1,500 services in 2020 to over 2,800 by 2024. Somewhere in that growth, platform-wide migrations — a library bump, a new tracing standard, a security patch — stopped finishing. Not because any team refused. They just never got around to it.

The root cause was math, not attitude. A migration that needs a "yes" from 2,800 separate owners doesn't die from a "no" — it dies because the odds of all 2,800 acting in the same quarter round to zero. The last few percent always turns into an open-ended tail: reasonable teams, real other priorities, nobody actually blocking it, nobody finishing it either. Ownership, the exact thing that let 2,800 services scale day to day, was the same thing stalling maintenance of the platform underneath them.

So Monzo's platform team took the decision away from service owners for this category of work. A dedicated migrations team now drives changes centrally across the whole fleet instead of filing 2,800 tickets and waiting. They lean hard on an 80/20 rule: codemod the shape that covers most services automatically against their Go monorepo, and hand-hold only the genuine outliers by hand. Rollouts move gradually through Monzo's own config service — the same Cassandra-backed system already serving production traffic — so a migration ships to a slice of services, gets watched, and rolls back in seconds if it misbehaves, without a single other team being asked first.

The tradeoff: less team autonomy over platform-level change, in exchange for migrations that actually finish. It runs against the usual microservices advice, and that's exactly why it works. Autonomy is the right default for building the product. It's the wrong one for maintaining the ground it stands on.

#SystemDesign #Microservices #PlatformEngineering #SoftwareArchitecture

**Character count: ~2,131 / 3,000 ✓**
**First ~170 chars (mobile hook):** "Monzo looked at 2,800 independently-owned microservices and made an unusual call: stop letting individual teams decide when their service takes a platform migration." ✓

---

## Twitter / X Thread

1/ Monzo runs 2,800+ microservices today, up from about 1,500 in 2020. Standard microservices doctrine says each team owns its service and decides when it changes. Monzo followed that rule until platform-wide migrations quietly stopped finishing.

2/ Not because anyone refused. A migration needing a "yes" from 2,800 separate teams doesn't fail from a "no" — it fails from math. The odds all 2,800 act in the same quarter round to zero. The last few percent becomes a permanent tail.

3/ Monzo's fix: take the decision away from service owners. A dedicated platform team now drives migrations centrally across the whole fleet, applying an 80/20 rule — codemod the common shape against their Go monorepo, hand-hold only the real outliers.

4/ Rollouts move gradually through Monzo's own config service, the same Cassandra-backed system already running in production — ship to a slice of services, watch it, roll back in seconds, no other team's sign-off required.

5/ Less autonomy over platform-level change, more migrations that actually finish. It's the opposite of the usual microservices advice — autonomy is right for building the product, wrong for maintaining what it runs on.

---

## Diagram

See: `2026-09-18-monzo-centralized-migrations-2800-microservices.excalidraw`

Type: Migration timeline (structured case study style) — three horizontal stages (2020 / 2022 / 2024) showing the service count climbing alongside the same team-owned migration model, connected by arrows, with a bottom banner calling out the trajectory and the fix.
Color scheme: amber for the 2020 starting state, purple for the 2022 state where the model starts to strain, teal for the 2024 fix — avoiding a red/bad-green/good pairing since the original ownership model wasn't wrong, it just stopped scaling for one specific job.
Key screenshottable number: 1,500 -> 2,000 -> 2,800+ microservices (2020-2024), with the mechanism (80/20 codemods + config-service gradual rollout) called out in the final stage.
