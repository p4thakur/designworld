---
date: 2026-11-23
company: etcd/raft and CockroachDB (issue #92088, PR #104042)
topic: Raft PreVote (thesis §9.6) is meant to stop a rejoining node from disrupting a healthy leader. etcd added it in 3.4 (off by default) and turned it on by default in 3.5. In etcd/raft, a pre-vote is granted when `m.Term > r.Term`, which is always true because pre-candidates ask for term+1, and when the candidate's log is up to date. The only check that refuses a candidate while a leader is alive is `inLease`, and it is gated on CheckQuorum. A node that rejoins with a caught-up log can therefore win a pre-vote and take leadership. CockroachDB ran PreVote=true with CheckQuorum off, hit this as issue #92088 (Nov 2022), and fixed it with PR #104042 "base: enable Raft CheckQuorum by default" (merged June 28, 2023). etcd's own server always hard-codes CheckQuorum: true.
category: availability
post_type: structured
opening_style: shared_pain_point
slug: raft-prevote-needs-checkquorum-cockroachdb
---

## Sources

- etcd-io/raft main, [raft.go](https://raw.githubusercontent.com/etcd-io/raft/main/raft.go). Primary.
  - The `Config.PreVote` doc: "enables the Pre-Vote algorithm described in raft thesis section 9.6. This prevents disruption when a node that has been partitioned away rejoins the cluster."
  - The `Config.CheckQuorum` doc: "Leader steps down when quorum is not active for an electionTimeout."
  - `campaign()`: "PreVote RPCs are sent for the next term before we've incremented r.Term", `term = r.Term + 1`.
  - Vote grant in `Step`: `canVote := r.Vote == m.From || (r.Vote == None && r.lead == None) || (m.Type == MsgPreVote && m.Term > r.Term)` followed by `r.raftLog.isUpToDate(candLastID)`.
  - The lease guard: `inLease := r.checkQuorum && r.lead != None && r.electionElapsed < r.electionTimeout`, with the comment "If a server receives a RequestVote request within the minimum election timeout of hearing from a current leader, it does not update its term or grant its vote".
  - The lower-term comment: an isolated follower "soon starts an election ending up with a higher term than leader... this response with MsgAppResp of higher term would force leader to step down... This can be prevented with Pre-Vote phase."
- etcd [CHANGELOG-3.4](https://raw.githubusercontent.com/etcd-io/etcd/main/CHANGELOG/CHANGELOG-3.4.md). Primary. It adds `--pre-vote` (PR #9352, issue #9333, "disruptive rejoining servers") and says "a flaky (or rejoining) member may drop in and out, and start campaign. This member will end up with a higher term, and ignore all incoming messages with lower term." It also lists "`etcd --pre-vote=false` by default" and "v3.5 will enable `etcd --pre-vote=true` by default."
- etcd [CHANGELOG-3.5](https://raw.githubusercontent.com/etcd-io/etcd/main/CHANGELOG/CHANGELOG-3.5.md). Primary. "Turned on --pre-vote by default (PR #12770)."
- etcd [release-3.4 etcdserver/raft.go](https://raw.githubusercontent.com/etcd-io/etcd/release-3.4/etcdserver/raft.go) and [main server/etcdserver/bootstrap.go](https://raw.githubusercontent.com/etcd-io/etcd/main/server/etcdserver/bootstrap.go). Primary. Both have `CheckQuorum: true`, hard-coded, with `PreVote: cfg.PreVote`.
- CockroachDB master, [pkg/base/config.go](https://raw.githubusercontent.com/cockroachdb/cockroach/master/pkg/base/config.go). Primary. The comment on `defaultRaftEnableCheckQuorum` says: "In etcd/raft, this also has the effect of fully enabling PreVote, such that a follower will not grant a PreVote for a candidate if it has heard from an established leader in the past election timeout... (assuming they have an up-to-date log, which they do with a read-only workload)... this can allow an unreachable node to steal leadership away from the leaseholder, leading to range unavailability." The env var is `COCKROACH_RAFT_ENABLE_CHECKQUORUM`, default `true`.
- CockroachDB master, [pkg/kv/kvserver/store.go](https://raw.githubusercontent.com/cockroachdb/cockroach/master/pkg/kv/kvserver/store.go). Primary. `PreVote: true, CheckQuorum: storeCfg.RaftEnableCheckQuorum`.
- [cockroachdb/cockroach#92088](https://github.com/cockroachdb/cockroach/issues/92088), "kvserver: Raft prevote does not prevent election despite active leader". Erik Grinaker opened it on Nov 17, 2022, and it closed on June 28, 2023. A restarted node kept winning leadership because its log was caught up. "We can end up electing a raft leader that is not reachable from the leaseholder." This was read through WebFetch, so it is summarized and not quoted at length.
- [cockroachdb/cockroach#104042](https://github.com/cockroachdb/cockroach/pull/104042), "base: enable Raft CheckQuorum by default". Opened May 29, 2023, merged June 28, 2023. Read through WebFetch and summarized.
- [cockroachdb/cockroach#27772](https://github.com/cockroachdb/cockroach/issues/27772). This comes from a search excerpt only. It says CockroachDB had treated PreVote and CheckQuorum as mutually exclusive, because CheckQuorum did not fit well with quiesced replicas.
- Ongaro, *Consensus: Bridging Theory and Practice* (2014), §9.6. The section number is confirmed by the etcd/raft source comment. The thesis text itself was not reachable in this run, so no wording from it is quoted.
- Not used: blog.cloudflare.com (Cloudflare's Nov 2020 etcd partial-switch-failure post) was blocked in this session's network settings, so nothing from it appears in the post.

**Key primary-source detail:** in etcd/raft, the pre-vote grant clause `m.Term > r.Term` is always true for a pre-vote, because a pre-candidate always asks for `r.Term + 1`. Without CheckQuorum, the only remaining check is whether the candidate's log is up to date. A node that rejoins with a caught-up log, which is common on a read-only workload, wins the pre-vote and then the real election. The check that would refuse it, `inLease`, starts with `r.checkQuorum &&`.

Derived/interpretive (the author's reading of the code, not stated verbatim by a source): the 2×2 matrix in the diagram. The PreVote-off/CheckQuorum-on cell follows the lower-term comment, where a stale heartbeat gets a higher-term MsgAppResp and the leader steps down. "Name describes intent, guard describes behavior" is the author's framing.

---

## LinkedIn Post

Every Raft cluster has the same annoying failure. A node drops off the network, times out, and starts elections nobody answers. Each one bumps its term. When it reconnects, that higher term forces a healthy leader to step down. Writes stall while the cluster re-elects, and nothing was wrong to begin with.

The textbook fix is PreVote, from Ongaro's Raft thesis §9.6. Before raising its term, a node asks its peers whether they would vote for it at term+1. A partitioned node never gets a majority, so its term never moves. etcd shipped it in 3.4 (off by default) and turned it on by default in 3.5.

CockroachDB ran with PreVote on. In November 2022 they filed issue #92088: "Raft prevote does not prevent election despite active leader." A restarted node kept taking leadership.

The cause is a single condition in etcd/raft. A follower grants a pre-vote if the request is for a future term (m.Term > r.Term) and the candidate's log is up to date. A pre-vote always asks for term+1, so the first check always passes. A node that rejoins after a restart on a read-only range has a fully caught-up log, so it wins.

The check that says "I heard from a leader recently, go away" exists in the same function:

inLease := r.checkQuorum && r.lead != None && r.electionElapsed < r.electionTimeout

It starts with checkQuorum. With CheckQuorum off, a follower can only turn a pre-vote down when the candidate's log is behind. Under a partial partition, Cockroach could elect a Raft leader that the leaseholder couldn't reach, and the range went unavailable.

The fix was PR #104042, "enable Raft CheckQuorum by default," merged June 28, 2023. Leaders now step down if a quorum goes quiet for an election timeout, and followers refuse votes while they still hear from a leader. The cost is that a deliberate campaign can be delayed by up to one election timeout.

etcd's own server never hit this, because it hard-codes CheckQuorum: true. The gap only showed up for teams that embedded the library and turned on PreVote by itself.

A flag's name tells you what it's for. The if statement tells you what it does. Read the if statement.

#DistributedSystems #Raft #CockroachDB #etcd

---

## Twitter Version

Raft PreVote has a catch most people don't know about.

PreVote asks "would you vote for me at term+1?" before bumping the term. That stops partitioned nodes from disrupting the leader when they come back.

In etcd/raft, a pre-vote is granted if m.Term > r.Term and the log is up to date. A pre-vote always asks for term+1, so the first check always passes.

The "I still hear a leader" guard is inLease, and it starts with r.checkQuorum &&.

CockroachDB ran PreVote without CheckQuorum. Restarted nodes with caught-up logs stole leadership (#92088). The fix in June 2023 was to turn CheckQuorum on by default.

etcd's server hard-codes CheckQuorum: true. Embedders had to know to do it themselves.

---

## Diagram

See `2026-11-23-raft-prevote-needs-checkquorum-cockroachdb.excalidraw`. It's a structured comparison matrix: PreVote (off/on) × CheckQuorum (off/on), and each cell says what happens when a node with a caught-up log rejoins next to a healthy leader. Off/off: the term bump forces the leader to step down. PreVote only: the pre-vote is granted and leadership is stolen (CockroachDB #92088). CheckQuorum only: the vote is ignored, but the node's inflated term still comes back in a MsgAppResp and the leader steps down. Both: the pre-vote is ignored in the lease and the leader stays. The code line `inLease := r.checkQuorum && ...` sits under the grid as the screenshot detail. A timeline strip runs along the bottom: etcd 3.4 PreVote (off) → 3.5 default on → CRDB #92088 Nov 2022 → #104042 Jun 2023. Palette: indigo, amber and slate, with no red or green.
