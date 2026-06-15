# Roblox's 73-Hour Outage: The Bug Fix That Sat Unused for Two Years

**Sources (primary):**
- https://blog.roblox.com/2022/01/roblox-return-to-service-10-28-10-31-2021/ (Roblox Engineering Blog — "Return to Service 10/28–10/31 2021", January 2022)
- https://github.com/etcd-io/bbolt (bbolt project — commit history showing hashmap freelist fix, 2019)
- https://pkg.go.dev/go.etcd.io/bbolt (bbolt documentation)

---

On October 28, 2021, Roblox went dark. 50 million daily active users. 18,000 servers. 170,000 containers. The platform stayed offline for 73 hours, and for most of that time, the engineers working the incident didn't know why.

The postmortem, published in January 2022, is unusually candid. It identifies two root causes that had been sitting dormant in the system independently, waiting for conditions that would finally bring them into contact. Neither was a bad decision. Both made complete sense in isolation.

---

## The stack that ran everything

Roblox operated at a scale that required serious infrastructure coordination. 18,000 machines running 170,000 containers don't organize themselves.

For that coordination, Roblox ran the HashiCorp stack: Consul for service discovery and traffic routing, Nomad for container orchestration and workload scheduling, Vault for secrets management. These three systems formed the nervous system of the platform — every service relied on Consul to find other services, and the routing layer used it to direct traffic.

This was a reasonable, battle-tested choice. The HashiCorp tools are widely used at scale. Consul in particular is well-understood and production-hardened.

---

## A reasonable upgrade

Consul 1.10 shipped a new feature: streaming. The idea was straightforward. In a large Consul cluster, keeping all agents up to date on service state changes requires broadcasting updates across the cluster. Traditional polling consumed substantial CPU and network bandwidth. Consul streaming was designed to replace that polling with a more efficient push model.

On October 27th at 14:00, Roblox enabled streaming on a backend service responsible for traffic routing. It was a deliberate choice — the feature was intended to reduce resource consumption, and Roblox's cluster was large enough that the savings would be meaningful.

Twenty-four hours later, everything stopped.

---

## The cascading failure

The failure didn't announce itself cleanly. Write latency on Consul's internal key-value store — normally sub-300ms at p50 — started climbing. It hit 2 seconds. Then kept climbing. Services that depended on Consul for routing topology couldn't get updates reliably. Traffic routing degraded. The platform went down.

The engineering team's first instinct was hardware. In a cluster the size of Roblox's, individual machine failures aren't unusual, and a faulty Consul server could explain elevated write latency on that node. They replaced the Consul cluster hardware.

Nothing changed.

They escalated. More hardware — specifically, doubling the CPU cores per machine from 64 to 128, and replacing the storage with faster SSDs. This was a reasonable move: if the problem was write throughput, more CPU and faster disk should help.

Things got worse.

This is the detail that took time to understand. More hardware, in this specific failure mode, made things worse because it meant more Raft followers. More followers meant more log replication writes. More log replication writes meant more of the thing they hadn't found yet.

---

## BoltDB's freelist problem

Consul uses BoltDB as the persistence layer for its Raft logs. BoltDB doesn't store Consul's current service registry state — it stores the rolling log of operations being applied via Raft, which is how Consul maintains consistency across its cluster members.

BoltDB manages disk space using a structure called a freelist. The freelist tracks which pages on disk are currently free and available for reuse. When old log entries are deleted, the pages they occupied are added to the freelist. When new data needs to be written, BoltDB consults the freelist to find available pages.

The implementation stores the freelist as a flat array. Every time BoltDB appends a log entry, it also rewrites the entire freelist to disk.

Under normal operating conditions, this is overhead you'd never notice. The freelist grows slowly, rewrite time is fast, and the raw data being appended is small. At Roblox's Consul write load — amplified by the new streaming feature — it became catastrophic.

For every 16kB of actual log data being appended, BoltDB was writing a 7.8MB freelist to disk.

That's approximately 500x write amplification per log entry. The Consul cluster wasn't struggling because of bad hardware or insufficient CPU. It was choking on its own bookkeeping. And adding more hardware added more write pressure, which made the bookkeeping worse.

---

## The fix that never arrived

The BoltDB freelist problem was not unknown.

In 2019, the bbolt project — the community-maintained fork of BoltDB, hosted under the etcd-io GitHub organization — replaced the freelist's flat array with a hashmap. A flat array means O(n) scan time for freelist operations, where n grows as the database accumulates free pages. A hashmap means O(1) lookup time, independent of the freelist size. The pathological write amplification that would later take down Roblox disappeared in bbolt in 2019.

But bbolt is a different library. Consul's dependency was BoltDB, not bbolt. The fix existed in a fork that Consul had not adopted. For two years, the corrected implementation sat in a different repository while Roblox's cluster was slowly assembling the conditions — streaming feature, high write load, large cluster — that would finally trigger the bug at full scale.

---

## Recovery

Diagnosing the root cause was most of the battle, but it wasn't the end.

Once the team understood that BoltDB's freelist behavior was the underlying issue, they could begin recovery. But "rebuild Consul" isn't a fast operation when your entire platform's routing topology depends on it, and neither is what comes after.

Roblox's cache layer used Consul for service topology — knowing where backends were, how to route traffic to them. When Consul went down, that knowledge became stale. Warming it back up meant re-establishing routing state for 170,000 containers' worth of services. That's not instant.

The team brought the platform back cautiously: Consul rebuilt first, then cache systems gradually restored, then players let in slowly, with monitoring in place to catch any signs of instability and pull back if needed. At 05:00 on October 31st — 61 hours after the outage began — they had a healthy Consul cluster and a recovering cache layer. Full service restoration followed.

73 hours total.

---

## What the design says

The two root causes — Consul streaming's elevated write pressure, and BoltDB's freelist write amplification — were independent problems. Neither was caused by the other. But together, they produced an outage that neither would have caused alone.

Enabling streaming was a reasonable choice. The BoltDB freelist design made sense at normal write loads. The bbolt fix was made and documented. Consul's dependency on the unfixed library was not an active decision — it was a non-decision, the kind of thing that doesn't surface until it matters.

The failure came from a fix that never crossed the gap between a fork and its upstream adopter. Not negligence. Not a bad architecture. Just the ordinary friction of open-source ecosystems, visible only in retrospect, at the exact moment conditions aligned to make it consequential.

Nobody was wrong. The tradeoffs were just collecting interest.
