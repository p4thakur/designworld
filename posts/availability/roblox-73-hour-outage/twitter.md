# Twitter/X Thread — Roblox's 73-Hour Outage

---

**1/**
Roblox lost 73 hours to a bug fix that had existed since 2019.

50M users. 18,000 servers. 170,000 containers. All offline.

Here's what happened.

---

**2/**
Roblox ran the HashiCorp stack: Consul (service discovery + traffic routing), Nomad (scheduling), Vault (secrets).

Oct 27 at 14:00, they enabled Consul streaming — a Consul 1.10 feature to cut CPU and bandwidth usage on large clusters.

24 hours later: KV write latency jumped from <300ms to 2 seconds. Outage begins.

---

**3/**
Engineers assumed bad hardware. They replaced the Consul cluster.

No change.

Doubled CPU cores from 64 to 128. Added faster SSDs.

Things got WORSE.

More hardware = more Raft followers = more log writes = more of the bug they hadn't found yet.

---

**4/**
The bug: BoltDB's freelist.

BoltDB tracks free disk pages in a flat array. Every log append also rewrites the entire array to disk.

16kB of real data → 7.8MB freelist write, every single time.

~500× write amplification. The Consul cluster was choking on its own bookkeeping.

---

**5/**
The fix had existed since 2019.

bbolt (BoltDB's community fork) replaced the array with a hashmap. O(n) → O(1). Write amplification: gone.

But Consul was using BoltDB, not bbolt.

The fix sat in a fork, unused, for two years — while Roblox's cluster slowly assembled the conditions to trigger the bug.

---

**6/**
Recovery took another two days after diagnosis.

The cache layer depended on Consul for routing topology. Warming 170,000 containers' worth of state isn't instant.

Engineers let players in gradually, watching metrics, ready to pull back.

73 hours. The tradeoffs don't disappear. They just move.
