# LinkedIn Post — Roblox's 73-Hour Outage: The Bug Fix That Existed for Two Years
# Narrative | Hook: mid_scene | ~2,377 chars

---

On October 28, 2021, Roblox went dark. 50 million players. 18,000 servers. 170,000 containers. Nobody could explain why for three days.

The platform ran the HashiCorp stack: Consul for service discovery and traffic routing, Nomad for workload scheduling, Vault for secrets. The previous day at 14:00, they'd enabled Consul streaming — a new feature in Consul 1.10 designed to reduce CPU and bandwidth across large clusters. Twenty-four hours later, write latency on Consul's internal KV store climbed from its normal sub-300ms p50 to 2 seconds. And kept climbing.

The engineers assumed bad hardware. They replaced the Consul cluster. Nothing changed. They doubled the CPU from 64 to 128 cores per machine and added faster SSDs. Things got worse. More hardware meant more Raft followers, which meant more log writes, which meant more of what they hadn't yet found: BoltDB's freelist problem.

BoltDB stores Consul's Raft logs. The way BoltDB manages free disk pages — its "freelist" — is to track them in a flat array, then write the entire freelist to disk on every single log append. Under normal load, this overhead was invisible. Under Consul streaming's elevated write pressure, it became catastrophic. For every 16kB of actual data being appended, BoltDB was writing a 7.8MB freelist to disk. Write amplification of nearly 500x.

The fix had already been written. In 2019, the bbolt project — the community-maintained fork of BoltDB — replaced the array with a hashmap, turning freelist lookups from O(n) to O(1). The pathological write amplification disappeared. But Consul was still using BoltDB, not bbolt. The fix sat in a fork, unused, for two years while the conditions for triggering the bug quietly assembled themselves in Roblox's cluster.

After diagnosing it, recovery took another two days. The cache layer depended on Consul for routing topology and had to warm back up. 170,000 containers' worth of routing state isn't instant. Engineers brought players back in gradually, watching metrics, ready to pull back.

Nobody made the wrong call. The original BoltDB design made sense. The bbolt fix was reasonable. Enabling streaming was reasonable. The failure came from a fix that never crossed the gap between a fork and its upstream adopter.

The tradeoffs don't disappear. They just move.

#SystemDesign #Reliability #DistributedSystems #Engineering
