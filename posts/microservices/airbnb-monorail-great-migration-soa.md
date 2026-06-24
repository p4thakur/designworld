---
date: 2026-06-24
company: Airbnb
category: microservices
post_type: confessional
opening_style: cold_fact
slug: airbnb-monorail-great-migration-soa
---

**Sources (verified primary):**
- QCon SF 2018, "The Great Migration: from Monolith to Service-Oriented" by Jessica Tai — https://qconsf.com/sf2018/presentation/airbnbs-great-migration-monolith-service-oriented
- InfoQ coverage: https://www.infoq.com/news/2019/02/airbnb-monolith-migration-soa/

---

## LinkedIn Post

Airbnb's engineers were losing 15 hours a week. Not to meetings. To waiting for their own code to ship.

When Airbnb had 200 engineers in 2015, their Ruby on Rails monolith — Monorail — was excellent. A new engineer could push a change to production in minutes. The codebase was readable. Deploys were reliable.

Then the company grew to 1,000 engineers.

With teams committing constantly, Monorail deploys became a shared bottleneck. A single rollback froze everyone. A flaky test blocked the entire org. The 15 hours per week wasn't an outlier — it was the average cost of a monolith that had outgrown its team.

The migration that followed was careful and, in hindsight, unusually low-level.

Instead of building new APIs and redirecting traffic, Airbnb intercepted at the Active Record layer — the ORM inside Monorail itself. Existing Ruby code didn't need to know any service existed. When a model touched home data through ActiveRecord, the interceptor caught it and routed it to a new homes data service. Shadow testing started at 1% of requests, compared responses against Monorail, fixed discrepancies, then scaled incrementally to 100%. Writes went to a shadow database simultaneously, validated before any data store was cut over.

The process took years. Over 250 services were onboarded using an IDL framework built on Apache Thrift, which auto-generated boilerplate and gave every new service templated monitoring dashboards by default. Over 1,000 endpoints migrated.

The results: deploys dropped from hours to minutes. Search results became 3x faster. Home description pages became 10x faster.

But here's the honest part. Monorail wasn't a design mistake. It was the right architecture for a 200-engineer company. The engineers who built it made sensible decisions.

A monolith scales with your product. It doesn't always scale with your engineering org in the same way. Those are different axes. Figuring out which constraint is actually biting you — the system or the team structure — is usually the harder problem.

#SystemDesign #Microservices #SoftwareEngineering #EngineeringLeadership

---

**Character count: ~2,108** ✓ (limit: 3,000)

---

## Twitter / X Version

Airbnb's engineers were losing 15 hours/week waiting for their own code to ship. Not to meetings. To Monorail. 🧵

1/ In 2015: Monorail (Ruby on Rails monolith), 200 engineers, deploys in minutes. The right call for where they were.

2/ By 2019: 1,000 engineers. Any rollback froze everyone. Any flaky test blocked the entire org. 15 hrs/week blocked — per engineer — on average.

3/ The migration was unusually low-level. They didn't build new APIs and redirect traffic. They intercepted at the Active Record (ORM) layer inside Monorail. Existing code had no idea any service existed.

4/ 1% of home data requests went to the new service. Responses compared against Monorail. Discrepancies fixed. Traffic scaled to 100%. Writes validated against a shadow database before any data store was cut over.

5/ Years later: 250+ services. 1,000+ endpoints. Deploys: minutes again. Search 3× faster. Home pages 10× faster.

6/ But Monorail wasn't a mistake. The engineers who built it made sensible decisions.

A monolith scales with your product. It doesn't always scale with your org the same way. Those are different axes — and figuring out which one is biting you is usually the harder problem.

---

## Diagram

See: `airbnb-monorail-great-migration-diagram.excalidraw`

**Type:** 5-phase horizontal timeline — Monorail birth (2015, indigo), growing pains (2017, light indigo), tipping point (2019, amber ⚠️), migration technique (2021, purple), results (2023, teal). Bottom banner shows key numbers screenshottable at LinkedIn preview size.
