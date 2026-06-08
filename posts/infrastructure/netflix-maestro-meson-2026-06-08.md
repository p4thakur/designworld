---
date: 2026-06-08
company: Netflix
topic: Meson to Maestro — workflow orchestration at scale
category: infrastructure
post_type: confessional
opening_style: cold_fact
slug: netflix-maestro-meson-single-leader
---

## Sources

- Netflix TechBlog: [Maestro: Data/ML Workflow Orchestrator at Netflix](https://netflixtechblog.com/maestro-netflixs-workflow-orchestrator-ee13a06f9c78)
- Netflix TechBlog: [100X Faster: How We Supercharged Netflix Maestro's Workflow Engine](https://netflixtechblog.com/100x-faster-how-we-supercharged-netflix-maestros-workflow-engine-028e9637f041)
- Netflix TechBlog: [Meson: Workflow Orchestration for Netflix Recommendations (2016)](https://netflixtechblog.com/meson-workflow-orchestration-for-netflix-recommendations-fc932625c1d9)
- GitHub: [Netflix/maestro](https://github.com/Netflix/maestro)

**Key primary-source detail (not in summaries):** The midnight UTC spike was not a traffic surge or a bug. It was caused by engineers copy-pasting the example cron expression from Netflix's own scheduling documentation, which used midnight as the default trigger time. Most of those workflows had no business requirement to start at 00:00 UTC — they just inherited the example.

---

## LinkedIn Post

Meson ran Netflix's data pipelines for years. 70,000 workflows. 500,000 jobs a day. It worked.

Then the midnight problem started.

Every night around midnight UTC, the system would groan under load. Engineers got paged. Meson's architecture was a single-leader model — one primary node coordinating all scheduling and execution across the platform. For years, that was fine. Netflix scaled it vertically, upgrading to more powerful machines without drama. Then they reached the ceiling of what AWS instance types could offer. There was nowhere left to climb.

So they built Maestro. Launched in 2022, it's horizontally scalable, event-driven, and distributed across hundreds of nodes. Today it handles over 2 million jobs on peak days — roughly four times what Meson ever could. The migration worked.

But here's the detail that stayed with me after reading the engineering blog.

The midnight spike wasn't a surge in streaming demand. It wasn't a runaway batch job or a misconfigured retry loop. It was the example cron expression in Netflix's own scheduling documentation. The default trigger time was midnight UTC. Engineers read the docs, copied the expression, and moved on. Thousands of workflows — many with zero business reason to start at exactly 00:00 UTC — ended up hitting the scheduler at the same minute every night. Meson had accidentally built itself a thundering herd.

Nobody was wrong. The docs were accurate. Users did what engineers always do: copy the example and ship.

The original Meson designers built something that served Netflix for nearly a decade. That's not a cautionary tale — that's a success. The system buckled only because so many teams trusted it with their most important pipelines.

Sometimes the bottleneck isn't the architecture. It's the documentation default that got copy-pasted 10,000 times.

#SystemDesign #Netflix #DataEngineering #WorkflowOrchestration

**Character count: ~1,874 / 3,000 ✓**
**First 140 chars (mobile hook):** "Meson ran Netflix's data pipelines for years. 70,000 workflows. 500,000 jobs a day. It worked. Then the midnight problem" ✓

---

## Twitter / X Thread

1/ Netflix ran 500,000 workflow jobs a day on Meson. Then it started choking every night at midnight. The culprit? A cron example in their own docs. 🧵

2/ Meson was a single-leader orchestrator. One node. 70,000 workflows. For years: no drama. Then Netflix hit the ceiling of the largest AWS instance available. Nowhere left to scale vertically.

3/ Thousands of workflows fired at midnight UTC — not because midnight mattered to the business, but because engineers copy-pasted the example from Netflix's scheduling documentation. The default was midnight.

4/ The docs were correct. The users were reasonable. The system did exactly what it was told. It just got told the same thing by thousands of teams.

5/ Netflix built Maestro in 2022. Horizontally scalable. Event-driven. Hundreds of nodes. Now handles 2M+ jobs on peak days. The migration worked.

6/ The Meson team built something that lasted nearly a decade and scaled to 70K workflows. That's not a failure. The architecture buckled only because adoption outgrew a single documentation default. The ceiling was the success.

---

## Diagram

See: `netflix-maestro-meson-2026-06-08.excalidraw`

Type: Timeline (confessional style)
Color scheme: Blue (growth era) → Red (ceiling) → Green (Maestro)
Key screenshottable number: 500K → 2M+ jobs/day
