---
date: 2026-10-22
company: Redis
topic: How Redis expires keys without ever scanning them - 20 random samples, a 25% repeat rule, and DELs synthesized by the master.
category: caching
post_type: structured
opening_style: the_decision
slug: redis-key-expiry-sampling-25-percent-rule
---

## Sources

- Redis docs, [EXPIRE command and Appendix: Redis expires](https://github.com/redis/redis-doc/blob/master/commands/expire.md) - primary: passive vs active expiry, the 10x/second loop (test 20 random keys with an expire, delete expired ones, repeat if more than 25% were expired), the bound on expired-but-resident keys (writes per second divided by 4), replicas waiting for a master-synthesized `DEL`, the pre-2.1.3 semantics where modifying a volatile key removed it.

**Note on sourcing:** only GitHub-hosted docs were reachable from this environment, so the Redis docs are the single source. The 1M-keys example below is arithmetic on the documented rule, an illustration and not a benchmark.

**Key primary-source detail:** the docs state the bound outright: the expired keys still holding memory are at most max write operations per second divided by 4. Expiry is a statistical guarantee, not an exact one.

---

## LinkedIn Post

Redis made an unusual call about deleting expired keys: don't look for them.

Scanning every key with a TTL, on a timer, is the obvious design. It also means the cost of expiry grows with the size of the keyspace, on a single-threaded server that cannot afford a pause.

So Redis expires keys two ways. The passive way is lazy: a key is deleted when a client touches it and finds it timed out. That is free, but it is not enough, because some expired keys are never read again and would hold memory forever.

The active way is a trivial probabilistic loop. Ten times per second: test 20 random keys from the set that have an expire, delete the expired ones, and if more than 25% were expired, start again.

The docs spell out the assumption. The sample is taken to be representative of the whole keyspace, and Redis keeps going until the likely share of expired keys drops under 25%.

That loop is the whole design, and it has a neat property. The cost is proportional to the amount of garbage, not the amount of data. A keyspace that is mostly healthy costs one cheap round of 20 samples. A keyspace where a big batch just expired keeps looping until it is clean.

The guarantee is also stated plainly: the expired keys still occupying memory are at most the maximum write operations per second divided by 4. At 100,000 writes a second that is a ceiling of 25,000 stale keys (my arithmetic on their formula). Bounded, but not zero.

One more decision keeps replication honest. Replicas do not expire keys on their own. When a key expires, the master synthesizes a DEL into the AOF and sends it to every replica, so expiry is centralized and cannot drift. A replica still carries the full TTL state, so if it is promoted it can start expiring independently.

That centralization has a history. Before Redis 2.1.3, modifying a key that had a TTL removed the key entirely, a semantic the docs say was needed because of limits in the replication layer, since fixed.

The lesson is about what you refuse to guarantee. Redis never promised that expired means gone. It promised that stale memory stays bounded, and in return expiry costs almost nothing.

An exact guarantee you cannot afford is worth less than a bound you can.

#Redis #SystemDesign #Caching #Backend

---

## Twitter Version

Redis never scans for expired keys.

Instead, 10x per second:
1. Sample 20 random keys that have a TTL
2. Delete the expired ones
3. If >25% were expired, repeat

Cost scales with garbage, not data size.

The docs bound the damage: stale keys in memory <= max writes/sec / 4.

Replicas don't expire keys themselves. The master synthesizes a DEL to AOF and replicas, so expiry can't drift.

Not exact. Bounded. That was the trade.

---

## Diagram

See `2026-10-22-redis-key-expiry-sampling-25-percent-rule.excalidraw` (the 20-sample loop with the 25% repeat branch, and the master-to-replica DEL).
