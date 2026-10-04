---
date: 2026-10-04
company: Reddit
topic: Reddit's Pi Day 2023 outage (314 minutes) — a Kubernetes 1.23 to 1.24 upgrade removed the node-role.kubernetes.io/master label that selected Calico BGP route reflectors, so nodes lost all pod routes; the route reflector config was undocumented and uncommitted, and with no Kubernetes downgrade path, recovery meant an etcd restore.
category: infrastructure
post_type: confessional
opening_style: cold_fact
slug: reddit-pi-day-calico-route-reflector-outage
---

## Sources

- Reddit Engineering (r/RedditEng), [You Broke Reddit: The Pi-Day Outage](https://www.reddit.com/r/RedditEng/comments/11xx5o0/you_broke_reddit_the_piday_outage/) — primary source (not directly fetchable from this environment).
- [postmortem.io summary](https://postmortem.io/incidents/reddit--2023-03-21--pi-day-outage/), [Overmind](https://overmind.tech/blog/reddit-pi-day-outage), [Committed Nowhere (behindscale)](https://www.behindscale.com/articles/reddit-piday-outage) — secondary write-ups used via search excerpts.

**Note on sourcing:** reddit.com and the secondary sites were blocked by this environment's egress policy, so facts come from search-indexed excerpts of the postmortem and write-ups. Only facts repeated across several excerpts are used; no figure beyond 314 minutes, ~19:00 UTC, ~2 minutes is stated.

**Key primary-source detail:** the route reflector config is Calico-specific data pulled and pushed via calicoctl, not Kubernetes YAML, so it existed only in the live cluster and in the memory of departed engineers.

---

## LinkedIn Post

Reddit went down for 314 minutes on Pi Day 2023. The change that did it removed one word from a label.

Around 19:00 UTC, an engineer started a Kubernetes upgrade from 1.23 to 1.24. The cluster had just been the subject of a postmortem for an earlier upgrade that went badly, so people were being careful. About two minutes in, the site stopped.

Here is the mechanism. Reddit ran Calico with BGP route reflectors, which are the nodes that tell every other node how to reach every pod. Those reflectors were selected by a label: node-role.kubernetes.io/master. Kubernetes 1.24 replaced that label with node-role.kubernetes.io/control-plane.

When the first control plane node upgraded, the selector matched nothing. No route reflectors. Calico dropped the routes to that node, which was expected, and then dropped the routes to all the nodes, which was not. Pods were running fine and could not reach each other.

The setup made sense once. Calico's route reflector config isn't plain Kubernetes YAML. It had to be pulled out with Calico's own CLI, edited by hand, and pushed back. Per the postmortem, it lived in the running cluster and in the memory of people who had since moved on. It was committed nowhere.

The fix everyone reaches for is rollback. Kubernetes has no supported downgrade, so rollback meant restoring the cluster from an etcd backup, using a runbook written years earlier for different software and never tried in production. It took hours to decide to do it, and the real cause was only found after the restore.

Nobody here was careless. The people who built the route reflectors solved a real problem in the only way Calico offered, and then left. The knowledge walked out the door while the config stayed.

The upgrade didn't fail because Kubernetes changed a label. It failed because the system's most critical dependency had no author left.

#Kubernetes #SRE #Postmortem #Infrastructure

**Character count: 1913 / 3,000**

---

## Twitter / X Thread

1/ Reddit was down 314 minutes on Pi Day 2023. The trigger: one word removed from a Kubernetes node label.

2/ K8s 1.24 renamed node-role.kubernetes.io/master to .../control-plane. Reddit's Calico route reflectors were selected by the old label. After the first control-plane node upgraded, the selector matched nothing and every node lost its pod routes.

3/ The route reflector config wasn't plain K8s YAML. It lived in Calico's own data, hand-edited via CLI. Committed nowhere. Known only to people who'd left.

4/ Rollback? Kubernetes has no supported downgrade. It meant an etcd restore from an old, untried runbook. The real cause surfaced only after.

5/ Nobody was careless. The knowledge walked out the door while the config stayed.
