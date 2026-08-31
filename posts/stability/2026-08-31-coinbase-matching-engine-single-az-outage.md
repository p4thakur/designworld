---
date: 2026-08-31
company: Coinbase
topic: Matching engine quorum loss during the May 7, 2026 AWS thermal outage
category: stability
post_type: confessional
opening_style: the_decision
slug: coinbase-matching-engine-single-az-outage
---

## Sources

- Coinbase Blog: [A postmortem of our May 7, 2026 outage](https://www.coinbase.com/blog/a-postmortem-of-our-may-7-2026-outage)
- InfoQ: [Coinbase Postmortem Reveals How a Localized AWS Failure Triggered a Multi-Hour Trading Outage](https://www.infoq.com/news/2026/06/coinbase-aws-failure-postmortem/)
- The Pragmatic Engineer: [Reliability fail: No automated zone failover for Coinbase's global trading service](https://blog.pragmaticengineer.com/coinbase-fail/)
- Crypto Economy: [Coinbase Details Eight-Hour Service Breakdown in Postmortem of May 7 Outage](https://crypto-economy.com/coinbase-may-7-outage-postmortem/)
- CryptoTimes: [Coinbase Publishes Post-Mortem on May 7 Service Outage](https://www.cryptotimes.io/2026/06/02/coinbase-publishes-post-mortem-on-may-7-service-outage/)

**Key primary-source detail (not in summaries):** The 3-of-5 Raft quorum design itself was never the flaw the postmortem targets. All five matching-engine nodes were deliberately placed inside a single AWS Cluster Placement Group in one data hall — a conscious trade against cross-zone network hops, which a matching engine settling trades in microseconds can't absorb. Recovery required shipping an emergency code change mid-incident just to remove a hardcoded startup assumption that all five nodes had to be DNS-resolvable before the cluster would even come up outside that placement group.

---

## LinkedIn Post

Coinbase's trading matching engine runs as a 5-node Raft cluster. All five nodes sit in the same AWS building. That's not an oversight — it's a decision engineers made on purpose.

A Raft cluster votes on every write. Put voting members across availability zones and you add a network hop between them. For a matching engine settling trades in microseconds, that hop is the difference between a fast exchange and a slow one. So Coinbase kept all five nodes in one data hall inside a single AWS Cluster Placement Group. Fast, and for years, fine.

On May 7, 2026, at 7:20 PM ET, multiple chiller units failed at once in that data hall, inside AWS us-east-1's use1-az4. The thermal shutdown that followed took the building's EC2 instances and EBS volumes offline. By 7:48 PM, nearly all trading on Coinbase had stopped. At 9:29 PM, AWS terminated the instances in Coinbase's placement group outright — three of five matching-engine nodes gone, quorum lost.

Getting it back wasn't a restart. Engineers shipped an emergency code change mid-incident to remove a startup assumption that all five nodes had to be resolvable, stood up a new node group outside the dead placement group, and rebuilt a 3-of-5 quorum by hand. Cancel-only trading came back at 2:25 AM. Full trading resumed at 3:49 AM — over eight hours after the chillers failed.

A second, unrelated fault made it worse: a defect in AWS's managed Kafka control plane stopped two clusters from re-electing partition leaders, stalling the fee and quoting services downstream. Coinbase reassigned partitions by hand at 3 AM to get moving again.

The postmortem doesn't dress this up as bad luck. The 3-of-5 quorum design was sound. The five-nodes-one-building placement was a deliberate trade of resilience for latency, and it worked for years until the one room it depended on got too hot. Coinbase is now building a warm cross-zone standby for the matching engine and running failover drills on a schedule, instead of discovering how failover works during the incident itself.

Every latency optimization is a bet against a specific kind of failure. Most days you collect on it. Some days the room gets hot.

#SystemDesign #DistributedSystems #SRE #Coinbase

**Character count: ~2,220 / 3,000 ✓**
**First 140 chars (mobile hook):** "Coinbase's trading matching engine runs as a 5-node Raft cluster. All five nodes sit in the same AWS building. That's not an oversight" ✓

---

## Twitter / X Thread

1/ Coinbase's matching engine: 5 Raft nodes, all in the same AWS building. On purpose — cross-zone hops kill latency for a system settling trades in microseconds.

2/ May 7, 2026, 7:20 PM ET: chiller units fail in that data hall. Thermal shutdown takes the building's EC2 and EBS offline. By 7:48 PM, trading is down.

3/ 9:29 PM: AWS terminates the instances outright. 3 of 5 matching-engine nodes gone. Quorum lost.

4/ Fix wasn't a restart. Emergency code change mid-incident, new node group stood up outside the dead placement group, quorum rebuilt by hand. Full trading back at 3:49 AM.

5/ A second bug — AWS's managed Kafka stuck re-electing partition leaders — knocked out fee and quote services too. Manual partition reassignment at 3 AM.

6/ The trade-off wasn't wrong. It just met a failure mode nobody had drilled for. Now: warm cross-zone standby for the matching engine, and failover drills on a schedule.

---

## Diagram

See: `2026-08-31-coinbase-matching-engine-single-az-outage.excalidraw`

Type: Incident timeline (confessional style)
Color scheme: Blue (deliberate design) → Red (cascading failure) → Green (recovery/remediation)
Key screenshottable number: 5 nodes, 1 building, 8+ hours down
