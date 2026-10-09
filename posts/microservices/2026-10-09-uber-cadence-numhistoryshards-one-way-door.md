---
date: 2026-10-09
company: Uber (Cadence)
topic: Cadence fixes numHistoryShards at cluster provisioning time; the shard count is the hard ceiling on how many hosts the cluster can ever use.
category: microservices
post_type: structured
opening_style: shared_pain_point
slug: uber-cadence-numhistoryshards-one-way-door
---

## Sources

- GitHub, [cadence-workflow/cadence docs/persistence.md](https://github.com/cadence-workflow/cadence/blob/master/docs/persistence.md) - primary: "Note on numHistoryShards" (picked at provisioning, cannot be changed, cluster of 1 to N hosts), the `historyShardID = hash(workflowID) % numHistoryShards` formula, the DB-level sharding rules, the multi-row-transaction requirement for persistence.
- GitHub, [cadence-workflow/cadence README](https://github.com/cadence-workflow/cadence) - primary: open source since 2017, services (frontend, matching, history, worker), Cassandra/MySQL/PostgreSQL backends.

**Note on sourcing:** both docs were read directly from the repo. The Uber engineering blog was not reachable from this environment, so no claim here relies on it. No benchmark or customer-scale numbers are used; the only numbers are the ones in the docs (1024 in the sample config, 1 to N hosts).

**Key primary-source detail:** the same doc that sets the cap also shows the sample value, 1024, with the comment "this limits the scalability of single cadence cluster". The cap is documented as a config comment, not hidden.

---

## LinkedIn Post

Every distributed system has one setting that feels like a detail on day one and turns into a wall on day 700.

In Cadence, the workflow engine Uber open-sourced in 2017, that setting is numHistoryShards. The persistence docs describe it in one short paragraph, and it reads like a contract.

Cadence gives every workflow a home. historyShardID = hash(workflowID) % numHistoryShards. A history shard is owned by exactly one history host at a time, and that owner is the only process that mutates the state of the workflows inside it. No distributed locks across hosts, no conflicting writers. The whole consistency story is "one owner per shard."

That is also why the persistence layer asks for so little. Any database works if it supports multi-row transactions on a single shard or partition. Cassandra, MySQL, PostgreSQL, even DynamoDB-style stores qualify. Cadence never needs a transaction across shards, because a workflow never lives in two.

Now the cost. The docs say the shard count is "picked at cluster provisioning time and cannot be changed after that." Their own framing: with N shards, the cluster can be anywhere from 1 to N hosts. Past N, adding hosts does nothing. The sample config shows 1024, with a comment that this value "limits the scalability of single cadence cluster". Dynamic shard splitting is listed as a possible future feature, not a current one.

So the decision is asymmetric. Too few shards and you hit the ceiling and have to stand up a new cluster. Too many and you pay for it in per-shard overhead from day one, while most of those shards sit idle.

The same hash then fans out below. With multiple SQL databases, dbShardID = historyShardID % numDBShards, so history shards pack onto databases by modulo. Workflow history shards by hash(treeID), task lists by domainID + tasklistName, and visibility by domainID, which is why advanced visibility is required in that mode.

The lesson is not "avoid sharding". It is that a fixed shard count is a capacity plan written in YAML. The doc tells you the ceiling honestly, in the config comment, before you deploy.

Pick it like you'll never get to change it. In Cadence, you won't.

#SystemDesign #DistributedSystems #Sharding #WorkflowEngine

---

## Twitter Version

Every distributed system has one setting that feels like a detail on day one and a wall on day 700.

In Uber's Cadence it's numHistoryShards.

historyShardID = hash(workflowID) % numHistoryShards. One history host owns each shard and is the only writer for its workflows. No cross-host locks. That's the whole consistency model.

The docs: the count is picked at provisioning and "cannot be changed after that." N shards means a cluster of 1 to N hosts. Past N, new hosts do nothing.

Sample config: 1024, with a comment saying it "limits the scalability of single cadence cluster."

A fixed shard count is a capacity plan written in YAML. Pick it like you'll never get to change it.

---

## Diagram

See `2026-10-09-uber-cadence-numhistoryshards-one-way-door.excalidraw` (architecture snapshot: workflowID hashed to fixed shards, shards owned by hosts, ceiling at N hosts).
