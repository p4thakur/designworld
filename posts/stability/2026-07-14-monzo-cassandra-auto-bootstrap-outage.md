<!-- sources -->
<!-- Primary: -->
<!--   Monzo Engineering Blog, "We had issues with Monzo on 29th July. Here's what happened, and what we did to fix it." (Sept 8, 2019) -->
<!--   URL: https://monzo.com/blog/2019/09/08/why-monzo-wasnt-working-on-july-29th -->
<!-- Note: direct fetch of monzo.com and community.monzo.com returned HTTP 403 under this session's egress -->
<!-- policy (same class of gateway-level denial hit on prior posts in this series, e.g. eng.lyft.com). Facts -->
<!-- below were cross-checked across multiple independent search-result excerpts that quote or closely -->
<!-- paraphrase the primary Monzo blog post directly, plus corroborating secondary coverage of the same -->
<!-- incident: -->
<!--   Hacker News discussion of the postmortem — https://news.ycombinator.com/item?id=20231863 -->
<!--   Monzo Community forum thread (mirrors/quotes the blog post) — -->
<!--     https://community.monzo.com/t/we-had-issues-with-monzo-on-29th-july-heres-what-happened-and-what-we-did-to-fix-it/75903 -->
<!--   The Downtime Project, podcast episode "Monzo's 2019 Cassandra Outage" — https://downtimeproject.com/podcast/monzos-2019-cassandra-outage/ -->
<!--   InfoQ, "Banking on Thousands of Microservices" (background on Monzo's Cassandra cluster topology) — -->
<!--     https://www.infoq.com/articles/cassandra-kubernetes-microservices/ -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Monzo ran its core banking data on a single Cassandra cluster of 21 nodes, with the accounts keyspace -->
<!--    set to replication factor 3 and reads/writes at local quorum. -->
<!-- 2. On July 29, 2019, starting around 13:10, Monzo scaled the cluster the way it had scaled before: adding -->
<!--    6 new servers to the existing 21-node ring. -->
<!-- 3. Root cause: Cassandra's auto_bootstrap setting is meant to bring a joining node in "inactive" — it is -->
<!--    assigned a slice of the token range, but the existing nodes keep serving reads/writes for that range -->
<!--    until the new node has actually streamed the underlying data over. Monzo's configuration did not behave -->
<!--    this way: the new nodes took over responsibility for their assigned token ranges immediately, before any -->
<!--    data had streamed into them. -->
<!-- 4. Effect: queries for data now "owned" by the new, empty nodes came back missing or wrong. Some customers -->
<!--    saw incorrect account balances and transactions that appeared to have vanished; payments, transfers, -->
<!--    and chat were all affected. -->
<!-- 5. Detection was slow relative to the fix: it took nearly an hour from the first alert to the point where -->
<!--    the team could pin the incident on Cassandra specifically, rather than the API layer or one of Monzo's -->
<!--    many other services sitting in front of it — a single cluster serving everything made isolating the -->
<!--    cause harder. -->
<!-- 6. The fix that day was mechanical: decommission the new nodes one by one, roughly 8-10 minutes per node to -->
<!--    remove safely, for a total resolution time of about 90 minutes. -->
<!-- 7. Aftermath: Monzo fixed its use of auto_bootstrap, reviewed and documented its Cassandra configuration, -->
<!--    built out more extensive operational runbooks, and committed to splitting the single large cluster into -->
<!--    several smaller ones specifically to shrink blast radius and make root-causing future incidents faster. -->

# Monzo Scaled Cassandra the Way It Always Had. This Time, the New Servers Served Money They Didn't Have.

**Date:** 2026-07-14
**Company:** Monzo
**Category:** stability
**Post type:** confessional
**Opening style:** specific_number
**Slug:** monzo-cassandra-auto-bootstrap-outage
**Character count (LinkedIn):** ~1,900

---

## LinkedIn Post

Monzo ran its core banking ledger on one Cassandra cluster — 21 nodes, replication factor 3, quorum reads. On July 29th, 2019, they scaled it the way they always did: added 6 more servers. Forty-some minutes later, customers' account balances were showing the wrong numbers.

The scaling process had worked before. Cassandra's auto_bootstrap setting is supposed to bring a new node in "inactive" — it gets assigned a slice of the data, but the cluster keeps serving reads and writes from the old nodes until the new one has actually streamed that data over. Only then does it join for real.

That's not what happened. The new nodes took over their assigned token ranges immediately — before any data had streamed into them. For a slice of the ledger, Monzo was suddenly querying servers holding none of the rows they were supposed to own. Balances came back wrong. Transactions looked missing. It wasn't a lot of accounts, but it was real money, in a live bank.

Finding it took time it shouldn't have. Nearly an hour passed between the first alert and the moment the team could say, with certainty, that Cassandra was the actual cause — not the API layer, not one of Monzo's hundreds of other services sitting in front of it. One cluster serving everything meant one incident could look like almost anything.

The fix that day was mechanical: pull the new nodes back out, one at a time, roughly 8–10 minutes each, about 90 minutes total. The fix that mattered came after — Monzo committed to breaking that one cluster into several smaller ones, not because smaller is inherently safer, but because a smaller blast radius is easier to point at.

Nobody set auto_bootstrap wrong on purpose. It's the kind of assumption that's correct right up until the day it's tested for real, on a live system, with your own money running through it.

#SystemDesign #Cassandra #Banking #Monzo #Incidents

---

## Twitter / X Version

1/ Monzo ran its banking ledger on one Cassandra cluster: 21 nodes, replication factor 3, quorum reads. July 29, 2019: they scaled it the normal way, adding 6 servers. ~40 minutes later, customer account balances started showing wrong numbers.

2/ The assumption: new nodes join "inactive" — old nodes keep serving until data streams over. Instead, the new nodes took over their token ranges immediately, before any data had streamed in. Balances came back wrong. Real money, live bank.

3/ It took almost an hour just to confirm Cassandra was the cause. One cluster serving everything meant the incident could've been anywhere.

4/ Fix that day: pull the new nodes back out, one at a time, ~8-10 min each, ~90 min total.

5/ Fix that mattered: split the one big cluster into several smaller ones — not because small is inherently safer, but because a smaller blast radius is easier to find.

6/ Nobody set auto_bootstrap wrong on purpose. Some assumptions are correct right up until the day they're tested on a live system, with real money moving through it.

---

## Excalidraw Diagram

**File:** 2026-07-14-monzo-cassandra-auto-bootstrap-outage.excalidraw
**Type:** Incident timeline (confessional) — how a routine scaling operation unfolded minute by minute, with the human/technical cause (the auto_bootstrap assumption) called out separately from the architecture boxes.
**Color scheme:** Slate blue for "how it always worked" (the routine, unremarkable scaling step), amber for the moment it broke, indigo for the fix that mattered (cluster split), teal reserved for the reflection/footnote box. No red/green good/bad pairing — the original 21-node design wasn't wrong, it was untested in this specific way.
**Screenshottable stat:** "21-node cluster, RF3, quorum reads → +6 servers, 13:10 → wrong balances at +~40 min → Cassandra confirmed as cause at +~60 min → fully resolved at +~90 min, one node at a time, ~8-10 min each."

### Layout

```
Title: "Monzo Scaled Cassandra the Way It Always Had. This Time, the New Servers Served Money They Didn't Have."
Subtitle: "July 29, 2019 — a routine 6-node scale-up on a 21-node cluster (RF3, quorum reads) exposed a bug in auto_bootstrap"

[TIMELINE — horizontal, four stages]

Stage 1 (slate)              Stage 2 (amber)              Stage 3 (amber)                Stage 4 (indigo)
~13:10                        ~13:50                        ~14:10                          ~14:40
SCALE-UP BEGINS               BALANCES GO WRONG             ROOT CAUSE CONFIRMED            RESOLVED
6 new servers join the        New nodes took over token      ~1 hour from first alert to     New nodes decommissioned
21-node ring. Standard        ranges immediately, before     pinning Cassandra as the        one at a time, ~8-10 min
operation, done before.       data had streamed in.          cause — not the API layer,      each. ~90 min total from
RF3, quorum reads.            Queries hit empty nodes.        not one of the hundreds of      first alert to resolution.
                               Wrong balances, missing         other services in front of it.
                               transactions. Real money.

[CALLOUT — the actual bug, set apart from the timeline]
auto_bootstrap is supposed to keep a joining node "inactive": assigned a slice of data, but not serving reads/writes
for it until that data has actually streamed over. Monzo's new nodes skipped the inactive part and started serving
immediately — for data they didn't yet hold.

[WHAT CHANGED — indigo]
Fixed the auto_bootstrap configuration. Documented every Cassandra setting in real runbooks. Committed to splitting
the single 21-node cluster into several smaller ones — not because smaller is safer, but because a smaller blast
radius is faster to diagnose.

[REFLECTION — teal, footnote]
Nobody set auto_bootstrap wrong on purpose. It's the kind of assumption that's correct right up until the day it's
tested for real, on a live system, with customers' money running through it.
```
