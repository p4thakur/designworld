---
date: 2026-10-17
company: Prometheus (CNCF)
topic: Why Prometheus scrapes instead of receiving pushes - the up metric and staleness markers fall out of the pull model, and the Pushgateway loses both.
category: observability
post_type: contrarian
opening_style: challenge_assumption
slug: prometheus-pull-model-up-metric-staleness
---

## Sources

- GitHub, [prometheus/docs - FAQ](https://github.com/prometheus/docs/blob/main/docs/introduction/faq.md) - primary: "Why do you pull rather than push?", "slightly better ... not a major point", Pushgateway only where you must push.
- GitHub, [prometheus/docs - When to use the Pushgateway](https://github.com/prometheus/docs/blob/main/docs/practices/pushing.md) - primary: SPOF/bottleneck, loses `up`, "never forgets series", only valid use case is service-level batch jobs.
- GitHub, [prometheus/docs - Jobs and instances](https://github.com/prometheus/docs/blob/main/docs/concepts/jobs_instances.md) - primary: `up` is stored per scrape, 1 healthy / 0 scrape failed.
- GitHub, [prometheus/prometheus - querying/basics.md, Staleness](https://github.com/prometheus/prometheus/blob/main/docs/querying/basics.md) - primary: 5 minute default lookback, series marked stale when a target is removed, exporters with their own timestamps linger.

**Key primary-source detail:** the maintainers themselves call pull "slightly better" and "not a major point" in the FAQ. The real argument is in the Pushgateway page: the lifecycle of the cache is separate from the lifecycle of the process, so dead instances keep serving their last value.

---

## LinkedIn Post

"Pull versus push" is usually argued as a networking question: firewalls, NAT, who opens the connection. That's the wrong axis.

Prometheus's own FAQ is surprisingly modest about it. Pulling is "slightly better than pushing," and "should not be considered a major point when considering a monitoring system." If the argument were about convenience, that would be the end of it.

The real argument is about who gets to declare a process dead.

With push, silence is ambiguous. A service that stopped sending metrics might be down, partitioned, idle, or just rate-limited on the way out. The monitoring system has to guess from an absence, which means a timeout and a threshold someone tuned.

With pull, the monitoring system initiates every conversation, so a failed conversation is itself data. On every scrape Prometheus stores an `up` sample for that target: 1 if it was reachable, 0 if the scrape failed. Dead is a recorded value, not an inference. The FAQ lists it as an advantage: "you can more easily and reliably tell if a target is down."

Then there's the opposite failure. Prometheus's Pushgateway page lists what you give up by pushing: you lose the `up` metric, the gateway becomes a single point of failure and a bottleneck, and it "never forgets series pushed to it." Rename or remove an instance and its last metrics stay exposed forever until someone calls the delete API.

The docs name the cause precisely: the lifecycle of the Pushgateway as a cache is fundamentally separate from the lifecycle of the processes that push to it. Under pull, the opposite holds. When a target is removed, its series are marked stale soon after, and queries stop returning them. Only exporters that attach their own timestamps get the other behavior, where values linger for the 5 minute default lookback.

So the recommended use of the Pushgateway is narrow: the outcome of a service-level batch job, deliberately without an instance label, because nothing about it should be tied to a machine's lifecycle.

Push feels simpler because the sender decides. That's exactly the problem. The party that can't observe the failure is the one reporting it.

#Prometheus #Observability #SystemDesign #SRE

---

## Twitter Version

"Pull vs push" isn't a firewall question.

Prometheus's FAQ calls pull "slightly better" and "not a major point." The real reason is who gets to say a process is dead.

Push: silence is ambiguous. Down? Partitioned? Idle? You guess from an absence.

Pull: every scrape stores `up` = 1 or 0. Dead is a value.

The Pushgateway page lists the cost of pushing: no `up`, a SPOF, and it "never forgets series." Remove an instance and its last metrics stay exposed until someone deletes them by hand.

Under pull, removed targets go stale on their own.

The one reporting a failure shouldn't be the one who can't see it.

---

## Diagram

See `2026-10-17-prometheus-pull-model-up-metric-staleness.excalidraw` (side-by-side: push via Pushgateway vs pull via scrape; who owns the failure signal).
