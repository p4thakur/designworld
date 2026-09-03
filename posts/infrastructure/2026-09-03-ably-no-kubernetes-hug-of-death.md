---
date: 2026-09-03
company: Ably
topic: A real-time messaging platform running thousands of machines across 10 AWS regions skipped Kubernetes entirely — and the post explaining that decision took its own website down
category: infrastructure
post_type: contrarian
opening_style: challenge_assumption
slug: ably-no-kubernetes-hug-of-death
---

## Sources

- Ably Engineering Blog — "No, we don't use Kubernetes" by Maik Zumstrull (ably.com/blog/no-we-dont-use-kubernetes), originally published July 2021
- [The Register — "Ably blog claims company doesn't need Kubernetes to scale, surge in traffic takes down entire website"](https://www.theregister.com/2021/07/22/ably_doesnt_need_kubernetes/) (July 22, 2021)
- [InfoQ — coverage of the Ably Kubernetes post](https://www.infoq.com/news/2021/07/ably-kubernetes)
- [Hacker News discussion — "We don't use Kubernetes"](https://news.ycombinator.com/item?id=27893482) (July 2021)

**Key primary-source detail (not in most summaries):** The irony wasn't a side comment — it's independently documented across three separate contemporaneous sources (The Register, InfoQ, and the Hacker News thread itself) that Ably's own site and blog started returning 500 errors from the traffic the "No, we don't use Kubernetes" post generated on Hacker News. The infrastructure built to run real-time pub/sub at global scale held up fine. The blog explaining that infrastructure did not.

**Note on sourcing:** Direct access to ably.com was not reachable from this environment's network egress policy at write time. The architecture specifics below (ASG-to-container-set mapping, the custom AMI boot service, the per-instance container watchdog, the "at least 10 regions" / "always at least many thousands" of machines figures, and the direct quote "doing mostly the same things, but in a more complicated way") are consistently attributed to Maik Zumstrull's original Ably post across the independent contemporaneous coverage cited above, rather than resting on a single secondary summary.

---

## LinkedIn Post

In July 2021, if your engineering blog didn't mention Kubernetes, people assumed you hadn't scaled yet.

Ably was running real-time pub/sub infrastructure across at least 10 AWS regions, with, in their own words, "always at least many thousands" of machines running at any moment. That's exactly the scale where Kubernetes stops being optional in most engineers' minds. So when Ably engineer Maik Zumstrull published a post titled "No, we don't use Kubernetes," it read like a confession.

It wasn't. Ably's argument was that adopting Kubernetes at their scale would mean, in Zumstrull's words, "doing mostly the same things, but in a more complicated way." What they run instead has no control plane at all. Every EC2 instance maps 1:1 to an AWS Auto Scaling Group, and the set of containers it runs is fixed for its life, decided entirely by which ASG launched it. A small custom boot service, baked directly into the AMI, reads that identity on startup, pulls the matching container images, and starts them. A lightweight per-instance watchdog respawns any container that dies, and if an image goes stale, it kills the instance outright and lets the ASG quietly replace it. To replicate their real footprint in Kubernetes, they'd have needed at least 10 separate clusters, one per region, each one more control plane to patch, upgrade, and debug.

That's the part people skip when they reach for Kubernetes by default: it doesn't remove the work of running distributed infrastructure, it relocates it into a scheduler and a control plane, and somebody still owns that at 3am. For a genuinely homogeneous workload, the same stateless services replicated globally, that's generality you're paying for and never spending.

Here's the detail that makes the story: the post arguing Ably didn't need complex infrastructure went viral on Hacker News, and the traffic spike knocked Ably's own website offline with 500 errors. The system engineered for real-time messaging at global scale had no trouble that day. The blog explaining that system did.

Ably got the hard infrastructure problem right by refusing the default. They got the easy one, hosting a blog post, wrong by treating it as obviously solved. Boring, well-matched infrastructure and "we'll figure out hosting later" are two different bets. Only one of them was actually derisked.

#SystemDesign #Infrastructure #Kubernetes #AWS

**Character count: ~2,388 / 3,000 ✓**
**First 140 chars (mobile hook):** "In July 2021, if your engineering blog didn't mention Kubernetes, people assumed you hadn't scaled yet." ✓

---

## Twitter / X Thread

1/ In July 2021, an Ably engineer published a post titled "No, we don't use Kubernetes." At their scale (10+ AWS regions, thousands of machines), that reads like a confession. It wasn't.

2/ Their case: adopting K8s would mean "doing mostly the same things, but in a more complicated way." Instead — every EC2 instance maps 1:1 to an Auto Scaling Group. Its container set is fixed for life, decided by which ASG launched it.

3/ A custom boot service baked into the AMI reads that identity on startup and pulls the right containers. A per-instance watchdog respawns dead ones, and kills + replaces the instance if an image goes stale. No control plane. No scheduler.

4/ To match their real footprint in Kubernetes, they'd have needed 10+ separate clusters, one per region. K8s doesn't remove the work of running distributed infra — it moves it into a control plane someone still owns at 3am.

5/ The twist: the post arguing they didn't need complex infrastructure went viral on Hacker News and took Ably's own website down — 500 errors. Their real-time messaging system didn't blink. Their blog did.

6/ They solved the hard infrastructure problem by refusing the default. The easy problem, hosting a blog, they assumed was already solved. Two different bets. Only one was actually derisked.

---

## Diagram
See: `ably-no-kubernetes-hug-of-death.excalidraw`
Type: Side-by-side architecture comparison ("obvious" Kubernetes-per-region approach vs. what Ably actually runs), with an irony callout below
Color scheme: violet for the "obvious" Kubernetes path, teal for Ably's actual ASG-based approach, amber for the callout — no red/green good-bad coding
Key screenshottable number: 10+ AWS regions, thousands of machines, 0 Kubernetes clusters — and the post about it took the site down with 500 errors
