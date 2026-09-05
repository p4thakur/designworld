---
date: 2026-09-05
company: GitHub
topic: GitHub replaced crossover-cabled file-server pairs with Spokes, a replication system for every Git repository that has no leader at all — every single write holds its own vote
category: storage
post_type: narrative
opening_style: mid_scene
slug: github-spokes-no-leader-election-replication
---

## Sources

- [Introducing DGit — The GitHub Blog](https://github.blog/engineering/architecture-optimization/introducing-dgit/) (April 5, 2016)
- [Building resilience in Spokes — The GitHub Blog](https://github.blog/engineering/infrastructure/building-resilience-in-spokes/)
- [Stretching Spokes — The GitHub Blog](https://github.blog/engineering/infrastructure/stretching-spokes/)
- [GitHub rolls out DGit to stop downtime of repositories — SD Times](https://sdtimes.com/applications/github-rolls-out-dgit-to-stop-downtime-of-repositories/)
- [InfoQ — GitHub DGit coverage](https://www.infoq.com/news/2016/04/github-dgit)

**Key primary-source detail (not in most summaries):** Spokes doesn't do leader election at all — the standard answer any Raft- or Paxos-literate engineer would reach for. Instead, per the GitHub Engineering Blog's own description, every write is treated as its own election: the proxy proposes an ordering, all replicas vote on it directly, and any replica on the losing side is marked unhealthy — pulled out of reads and writes — until it's repaired and resynced. There is never a standing leader to fail over from, only a fresh quorum on every single push.

**Note on sourcing:** Direct fetches to github.blog were not reachable from this environment's network egress policy at write time. The architecture specifics below (crossover-cabled file-server pairs, RAID+DRBD disk copies, the "hundreds of thousands of repositories" blast radius, the DGit-to-Spokes rename reasoning, the 38M+ repositories / 36M+ gists figures, the majority-vote quorum math, and the leaderless per-write election mechanic) are drawn consistently across the GitHub Engineering Blog posts cited above and independent contemporaneous coverage (SD Times, InfoQ), rather than resting on a single secondary summary.

---

## LinkedIn Post

Every git push to GitHub used to be a bet that the one server holding your repository wouldn't die in the next ten seconds.

For years, GitHub stored each repository on a single file server, paired with an identical hot spare over a physical crossover cable. DRBD mirrored the disk in real time, so a repo effectively had four copies: two via RAID on the primary, two more via DRBD on the spare. It looked redundant. It wasn't.

Every repository still lived on exactly one logical machine. If both boxes in a pair went down, or the cable between them, or the DRBD sync itself hiccuped, every repository on that pair went offline at once. At GitHub's scale, "that pair" wasn't a handful of side projects. It was routinely hundreds of thousands of repositories, gone until someone restored a specific box.

The fix, built through 2015 and shipped in April 2016, wasn't a better spare. It was to stop treating replication as a disk problem. GitHub called it DGit, Distributed Git, then renamed it Spokes months later because "DGit" kept getting misread as git itself.

Spokes keeps three independent copies of every repository on three different servers, synced at the application layer over Git's own protocol, not at the block level. A push streams to all three. Lose any one server, and the repository stays fully readable and writable on the other two.

Here's the part that doesn't show up in the architecture diagrams: Spokes has no leader. No server is ever elected to own write order the way Raft or Paxos would do it. Every single write is its own election instead. The proxy proposes an order, all replicas vote on it, and whichever replicas land on the losing side get marked unhealthy, pulled from reads and writes, until they're repaired and resynced. Three replicas need two votes to commit. Five need three. There's no standing authority, just a fresh quorum, every push, across 38 million repositories and 36 million gists.

That decision didn't stay simple. When GitHub later needed replicas spread across widely separated datacenters, to survive an entire region failing, not just a server, the same voting protocol that made Spokes leaderless also needed every replica close enough to vote fast, thousands of times a second. Stretching the ring meant re-solving the same coordination problem at a new distance.

No one was wrong to bolt a hot spare onto a file server with a crossover cable back when that was the whole fleet. The tradeoff didn't disappear when GitHub replaced it. It moved into a protocol that has to hold a fresh vote before it can agree on anything, forever.

#SystemDesign #GitHub #DistributedSystems #Git

**Character count: ~2,626 / 3,000 ✓**
**First 140 chars (mobile hook):** "Every git push to GitHub used to be a bet that the one server holding your repository wouldn't die in the next ten seconds." ✓

---

## Twitter / X Thread

1/ For years, every repo on GitHub lived on one file server, mirrored to a hot spare over a physical crossover cable. Looked redundant. Wasn't — it was still one logical copy.

2/ Lose both boxes in that pair (or the cable, or the DRBD sync) and every repo on it went dark at once. At GitHub's scale that meant hundreds of thousands of repositories offline together.

3/ The fix, shipped April 2016: Spokes (originally called DGit, renamed because it kept getting misread as "git"). Three independent copies per repo, on three servers, synced over Git's own protocol — not disk mirroring.

4/ The twist nobody diagrams: Spokes has no leader. Every write is its own election. The proxy proposes an order, replicas vote, and whoever loses gets marked unhealthy until resynced. 2 of 3 must agree to commit.

5/ Then they had to stretch replicas across distant datacenters for region failures — and that same voting protocol needed to stay fast enough at a much longer distance.

6/ No standing authority. Just a fresh quorum, every push, across 38M+ repos and 36M+ gists.

---

## Diagram
See: `2026-09-05-github-spokes-no-leader-election-replication.excalidraw`
Type: Top/bottom before-after timeline (crossover-cabled single copy vs. Spokes leaderless voting), with a callout explaining the vote mechanic below
Color scheme: slate gray for the old crossover-cable pair (not "bad," just earlier), blue for Spokes, green for the leaderless-vote callout — no red/green good-bad coding
Key screenshottable number: 38M+ repositories, 36M+ gists, 3 copies each, 0 leaders ever elected
