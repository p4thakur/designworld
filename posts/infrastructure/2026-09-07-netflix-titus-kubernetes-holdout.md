---
date: 2026-09-07
company: Netflix
topic: Titus — why Netflix built its own container platform instead of adopting Kubernetes in 2015, and why it partly reversed that call in 2026
category: infrastructure
post_type: contrarian
opening_style: challenge_assumption
slug: netflix-titus-kubernetes-holdout
---

## Sources

- Netflix Tech Blog: ["Titus, the Netflix container management platform, is now open source"](https://netflixtechblog.com/titus-the-netflix-container-management-platform-is-now-open-source-f868c9fb5436) (2018)
- Netflix Tech Blog: ["Distributed Resource Scheduling with Apache Mesos"](http://techblog.netflix.com/2016/07/distributed-resource-scheduling-with.html) (2016)
- ACM Queue: ["Titus: Introducing Containers to the Netflix Cloud"](https://queue.acm.org/detail.cfm?id=3158370)
- Netflix Tech Blog: ["How Netflix Simplified Batch Compute with Kueue"](https://netflixtechblog.com/how-netflix-simplified-batch-compute-with-kueue-87860682629c) (June 2026)
- InfoQ: ["Netflix Adopts Cloud-Native Job Queueing System Kueue to Replace an In-House Solution"](https://www.infoq.com/news/2026/08/netflix-kueue-kubernetes-batch/) (August 2026)

**Key primary-source detail (not in most summaries):** Netflix didn't pick Kueue because it's the popular Kubernetes-native batch tool — it picked it specifically because, unlike alternatives such as YuniKorn or Volcano, Kueue does not replace pod scheduling done by kube-scheduler. That let Netflix keep its existing Titus scheduling profiles intact instead of re-implementing years of scheduling logic. That's a compatibility-driven tool choice, not a trend-driven one, and it only shows up in the actual migration writeup, not in coverage of "Netflix adopts Kubernetes tool."

**Note on sourcing:** `netflixtechblog.com`, `cacm.acm.org`, and `www.infoq.com` were not reachable from this environment's network egress policy at write time. The facts above — Titus's 2015-2016 origin on Apache Mesos, the per-container IAM metadata-proxy design, the 2018 open-source scale numbers (millions of containers/week, 1,000+ workloads, 3 AWS regions), CMB's 2018 origin, and the 2026 Kueue migration details (the YuniKorn/Volcano comparison, the ~4-week production migration, "millions of batch workloads") — come from consistent, near-identical phrasing surfaced across independent search-indexed excerpts of those primary posts, cross-checked across multiple separate queries, rather than a single secondary summary.

---

## LinkedIn Post

In 2015, the accepted wisdom in infrastructure was simple: don't build your own container orchestrator, adopt whatever the ecosystem is converging on. Kubernetes and Docker Swarm were both racing to become that default.

Netflix looked at both and built Titus instead, on top of Apache Mesos.

The "obvious" platforms of that era were built for a specific kind of company: one starting fresh, writing new services from scratch, where every container could reasonably get the same broad permissions. Netflix wasn't that company. It had a decade of existing applications it needed to keep running unchanged, and giving thousands of containers identical AWS permissions was a security problem, not a convenience.

So Titus shipped with something the "obvious" choice didn't have: a metadata-service proxy running on every agent VM, handing each container only the specific IAM role its job declared — legacy apps kept running untouched, but with per-container identity instead of per-node identity. By the time Netflix open-sourced Titus in 2018, it was launching millions of containers a week across three AWS regions for 1,000+ workloads.

Building instead of adopting is usually the wrong call. Most homegrown platforms rot into the thing everyone warns you about. Titus didn't, because it solved a constraint — fine-grained identity for a decade of existing apps — that the "obvious" tools of 2015 hadn't been designed around at all.

Here's the twist nobody predicts when they tell this kind of story: holding out wasn't permanent. This year, Netflix quietly gutted CMB, the batch layer it built on top of Titus back in 2018, and replaced most of it with Kueue, an open-source, Kubernetes-native queueing system. The ecosystem had finally caught up and absorbed the features CMB once had to build alone.

Even here, Netflix didn't just grab the popular option. It picked Kueue specifically over alternatives like YuniKorn and Volcano because Kueue doesn't touch pod scheduling — it layers on top, so Netflix kept its existing Titus scheduling logic intact instead of ripping it out.

The contrarian call was never "never adopt the standard." It was knowing precisely which constraint made the standard wrong in 2015, and precisely when that constraint stopped mattering, ten years later.

#SystemDesign #Netflix #Kubernetes #Infrastructure

**Character count: ~2,348 / 3,000 ✓**
**First 140 chars (mobile hook):** "In 2015, the accepted wisdom in infrastructure was simple: don't build your own container orchestrator, adopt whatever the ecosystem" ✓

---

## Twitter / X Thread

1/ In 2015, everyone said the same thing about infrastructure: don't build your own orchestrator, ride the wave. Kubernetes and Docker Swarm were racing to become that default.

2/ Netflix looked at both and built Titus instead, on Apache Mesos. Not NIH pride — the "obvious" platforms assumed greenfield apps and coarse, node-level AWS permissions. Netflix had a decade of existing apps and needed per-container identity.

3/ Titus ran a metadata-proxy on every agent VM, handing each container only the IAM role its job declared. Legacy apps ran unchanged. By open-sourcing in 2018: millions of containers/week, 3 AWS regions, 1,000+ workloads.

4/ Most homegrown platforms rot. Titus didn't, because it solved a real constraint the industry-standard tools of 2015 weren't built around at all.

5/ The twist: this year Netflix gutted CMB, the batch layer built on Titus in 2018, and replaced most of it with Kueue — a Kubernetes-native queueing system. They picked Kueue specifically because, unlike YuniKorn or Volcano, it doesn't touch pod scheduling, so their existing Titus scheduling logic stayed intact.

6/ The contrarian move was never "reject the standard forever." It was knowing exactly which constraint made it wrong in 2015 — and exactly when that constraint stopped mattering.

---

## Diagram

See: `2026-09-07-netflix-titus-kubernetes-holdout.excalidraw`

Type: Side-by-side architecture comparison + twist banner (contrarian style)
Color scheme: Slate (the crowd's "obvious" path) vs. Violet (what Netflix built) vs. Amber (the 2026 reversal) — no red/green good-bad coding, and a different layout/palette from the previous post's 4-stage timeline
Key screenshottable number: millions of containers/week across 1,000+ workloads (2018), and Kueue chosen specifically because it doesn't replace pod scheduling
