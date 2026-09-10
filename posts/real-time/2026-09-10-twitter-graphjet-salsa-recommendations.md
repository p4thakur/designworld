---
date: 2026-09-10
company: Twitter
topic: GraphJet — Twitter's real-time recommendation engine that holds the entire live interaction graph in memory on one server, and ranks it with a 1990s web-search algorithm instead of PageRank
category: real-time
post_type: structured
opening_style: the_decision
slug: twitter-graphjet-salsa-recommendations
---

## Sources

- Sharma, Jiang, Bommannavar, Larson, Lin: ["GraphJet: Real-Time Content Recommendations at Twitter"](https://www.vldb.org/pvldb/vol9/p1281-sharma.pdf), Proceedings of the VLDB Endowment, Vol. 9, No. 13, 2016
- ACM Digital Library listing: ["GraphJet: real-time content recommendations at twitter"](https://dl.acm.org/doi/10.14778/3007263.3007267)
- GitHub: [twitter/GraphJet](https://github.com/twitter/GraphJet) — official open-source release and README

**Key primary-source detail (not in most summaries):** The ranking algorithm isn't PageRank or a generic "collaborative filtering" black box — it's personalized SALSA (Stochastic Approach for Link-Structure Analysis), an algorithm originally built for hub-authority analysis in 1990s web search. The paper is explicit about why it fits better than PageRank here: PageRank does a single-direction random walk, which on a bipartite user-tweet graph lets a small number of viral hubs dominate every result. SALSA instead alternates direction — a step from user to tweet, then a step back from tweet to user, repeated — which matches the actual shape of a bipartite interaction graph instead of a one-way web-link graph.

**Note on sourcing:** `vldb.org`, `dl.acm.org`, `semanticscholar.org`, `medium.com`, and `readkong.com` were not reachable from this environment's network egress policy at write time. The specific numbers and design details above — 1,000,000 edges/second ingestion, 500 recommendations/second served, several million edge reads/second, the single-JVM in-memory design over a sliding time window of temporally-partitioned segments, the four-generation lineage (Cassovary → RealGraph → MagicRecs → GraphJet), and the personalized-SALSA forward-backward random walk vs. PageRank's one-way walk — come directly from the paper's abstract and body as reproduced verbatim in the official GraphJet GitHub README, cross-checked against multiple independent secondary summaries that quote the same paper.

---

## LinkedIn Post

Twitter looked at real-time recommendations and made an unusual call: skip the distributed graph database. Run the whole thing on one machine.

By the early 2010s, Twitter's "who to follow" recommendations ran on Cassovary — an in-memory graph library built for a graph that barely moves. It loaded a full snapshot of the follow graph, computed rankings, and served that same snapshot until the next batch run. Fine for follows. Follows change slowly.

Content recommendations are a different problem wearing the same name. A tweet that's trending right now is often stale in a few hours. By the time an overnight batch job finishes ranking yesterday's interactions, the graph it ranked doesn't exist anymore.

So Twitter's engineers built GraphJet, described in a 2016 VLDB paper. Each server holds the entire recent interaction graph — every favorite, retweet, and reply between users and tweets — resident in memory, organized into segments covering a sliding window of the last few hours. No database round-trip, no distributed store. One JVM process holding the live graph and answering queries directly against it.

One GraphJet server ingests up to 1,000,000 edges per second while simultaneously serving up to 500 recommendation queries per second — each query reading millions of edges off that same in-memory graph.

The ranking algorithm is the counterintuitive part. Instead of PageRank, the default choice for "rank things in a graph," Twitter used personalized SALSA — an algorithm from 1990s web search built for hub-authority analysis, not social graphs. PageRank does a one-directional random walk. SALSA alternates: user to tweet, then tweet back to user, repeat. That back-and-forth matches a bipartite interaction graph far better than a one-way walk, which tends to let a handful of viral hubs dominate every result.

GraphJet was the fourth generation of Twitter's recommendation stack, after Cassovary, RealGraph, and MagicRecs — not because each version failed, but because each one solved a version of the problem the last one didn't have.

The lesson isn't "in-memory beats distributed." It's that real-time and slow-moving are different problems that happen to share the word "graph." Twitter solved slow-moving with a batch snapshot, and solved real-time by shrinking the working set until it fit on one box.

Sometimes the scalable version of a problem is smaller, not bigger.

#SystemDesign #Twitter #DistributedSystems #RealTimeSystems

**Character count: ~2,466 / 3,000 ✓**
**First 140 chars (mobile hook):** "Twitter looked at real-time recommendations and made an unusual call: skip the distributed graph database. Run the whole thing on one machin" ✓

---

## Twitter / X Thread

1/ Twitter's recommendation engine doesn't run PageRank. It runs an algorithm from 1990s web search built for hub-authority analysis, not social graphs.

2/ The algorithm is SALSA. PageRank does a one-way random walk. SALSA alternates — user to tweet, tweet back to user, repeat. That two-way walk fits a bipartite interaction graph far better than a one-directional web-link graph.

3/ The system that runs it, GraphJet, is the more unusual part: one JVM server holds the entire recent interaction graph in memory. No distributed store, no database round-trip.

4/ Each server ingests up to 1,000,000 edges/sec while serving up to 500 recommendations/sec off that same in-memory graph — each query reading millions of edges.

5/ Why one machine? Because "real-time" and "slow-moving" are different problems. Twitter's follow graph (Cassovary) barely changes — a nightly batch snapshot works fine. But a viral tweet is stale in hours.

6/ By the time a distributed pipeline finishes ranking last night's interactions, the graph it ranked doesn't exist anymore.

7/ So instead of scaling the database, Twitter's engineers shrank the working set until one server could hold the whole live graph and answer instantly.

8/ Sometimes the scalable fix isn't bigger. It's smaller.

---

## Diagram

See: `2026-09-10-twitter-graphjet-salsa-recommendations.excalidraw`

Type: Migration timeline (structured case study style, 4 generations left to right, last stage enlarged and emphasized as the production system)
Color scheme: Gray (Cassovary, legacy offline) → Orange (RealGraph) → Amber (MagicRecs, prototype) → Teal (GraphJet, live production) — no red/green good-bad pairing; each earlier stage wasn't wrong, just built for a different problem
Key screenshottable number: 1,000,000 edges/sec ingested and 500 recommendations/sec served, per server, plus the SALSA-vs-PageRank walk-direction contrast
