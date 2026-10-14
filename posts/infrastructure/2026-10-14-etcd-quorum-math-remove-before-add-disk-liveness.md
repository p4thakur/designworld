---
date: 2026-10-14
company: etcd
topic: etcd quorum arithmetic: even-sized clusters, remove-before-add, and disk latency as leader liveness.
category: infrastructure
post_type: structured
opening_style: cold_fact
slug: etcd-quorum-math-remove-before-add-disk-liveness
---

## Sources

- etcd, [FAQ (v3.5)](https://github.com/etcd-io/website/blob/main/content/en/docs/v3.5/faq.md) - primary: failure tolerance table, odd member count, max cluster size of about seven, remove-before-add reasoning, strict-reconfig-check, disk latency and leader loss.
- etcd, [Tuning (v3.5)](https://github.com/etcd-io/website/blob/main/content/en/docs/v3.5/tuning.md) - 100ms heartbeat, 1000ms election timeout, fsync stalls cause missed heartbeats.
- etcd, [Hardware recommendations (v3.5)](https://github.com/etcd-io/website/blob/main/content/en/docs/v3.5/op-guide/hardware.md) - 50 / 500 sequential IOPS, concurrent IOPS can be 10x sequential.

**Note on sourcing:** only GitHub-hosted docs were reachable from this environment; all numbers come from the etcd docs above, none from memory.

**Key primary-source detail:** strict-reconfig-check exists because adding a broken member to a 3-node cluster with one failure leaves 2 up, 2 down, and needs 3 votes to fix it.

---

## LinkedIn Post

A 4-node etcd cluster survives exactly as many failures as a 3-node one: one. The fourth machine adds cost, replication traffic and a new way to lose the cluster, and buys nothing.

That table sits in etcd's FAQ, and it explains most of the rules that look like pedantry in the docs. Quorum is (n/2)+1. With 3 members the majority is 2. With 4 it becomes 3. Same tolerance, more things that can break. The FAQ's list runs 5 members tolerating 2 failures, 7 tolerating 3, 9 tolerating 4, and still advises against going past seven because every write must replicate to more machines.

The sharper consequence is about replacing a dead node. Intuition says add the new member, then remove the dead one. etcd's FAQ says the opposite: remove first. Take a 3-member cluster with one member down. Quorum is 2, two are alive, life goes on. Add a fourth and quorum jumps to 3. If the new node is misconfigured and never joins, the cluster has two up and two down, needs three votes, and cannot even vote to undo the mistake. Permanent quorum loss. Remove first and quorum stays at 2 throughout, so a botched replacement can still be removed by the survivors. etcd also rejects membership changes that would cost quorum (strict-reconfig-check), and the docs warn that disabling it can end in "disk geometry corruption".

Then the part that surprises people running on shared cloud disks. etcd treats disk latency as part of leader liveness. The FAQ's example: the leader takes a minute to fsync a raft log write while the election timeout is one second. It still answers network messages and sends heartbeats, but it cannot commit anything, so it is effectively down. The defaults are a 100ms heartbeat and a 1000ms election timeout, so a noisy neighbor causing fsync stalls triggers elections. The docs ask for about 50 sequential IOPS at minimum, 500 for busy clusters, and warn that providers often publish concurrent IOPS that can be 10x the sequential figure.

None of this is a bug. A consensus system has to define "alive" as "can durably commit," not "can answer a ping." Everything else follows from taking quorum arithmetic literally.

Treat etcd's odd-number and remove-first rules as math, not folklore. The math is what keeps a bad Tuesday from becoming a rebuild from backup.

#etcd #Kubernetes #DistributedSystems #SystemDesign

---

## Twitter Version

A 4-node etcd cluster tolerates the same single failure as a 3-node one. Quorum is (n/2)+1: 2 of 3, but 3 of 4. The extra node is pure risk.

Same math explains the rule that surprises people: replace a dead member by removing it first, then adding. Add first on a 3-node cluster with one down and quorum jumps to 3. If the new node never joins, the cluster can't even vote to undo it.

Stranger: etcd counts disk latency as leader liveness. A leader that answers heartbeats but needs a minute to fsync is effectively down. Defaults: 100ms heartbeat, 1000ms election timeout. Shared cloud disks can trigger elections.

Define alive as "can durably commit", not "answers a ping".

---

## Diagram

See `2026-10-14-etcd-quorum-math-remove-before-add-disk-liveness.excalidraw` (comparison matrix of cluster size vs quorum vs failures tolerated, plus the add-first trap).
