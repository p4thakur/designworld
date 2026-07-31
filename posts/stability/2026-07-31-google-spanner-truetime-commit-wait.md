<!-- sources -->
<!-- Primary: -->
<!--   J.C. Corbett et al., "Spanner: Google's Globally-Distributed Database" (OSDI 2012) -->
<!--   URL: https://research.google/pubs/spanner-googles-globally-distributed-database/ -->
<!--   (paper mirrors: usenix.org/system/files/conference/osdi12/osdi12-final-16.pdf, -->
<!--   static.googleusercontent.com/media/research.google.com/en//archive/spanner-osdi2012.pdf) -->
<!-- Note: direct fetch of usenix.org and the googleusercontent paper mirror returned HTTP 403 under this -->
<!-- session's egress policy (same class of gateway-level denial hit on prior posts in this series). Facts -->
<!-- below were cross-checked across multiple independent web-search-result excerpts that quote or closely -->
<!-- paraphrase the primary OSDI paper directly, plus corroborating secondary technical writeups: -->
<!--   Kevin Sookocheff, "TrueTime" — https://sookocheff.com/post/time/truetime/ -->
<!--   Google Cloud Docs, "Spanner: TrueTime and external consistency" — -->
<!--     https://docs.cloud.google.com/spanner/docs/true-time-external-consistency -->
<!--   CockroachDB, "Living without atomic clocks" — https://www.cockroachlabs.com/blog/living-without-atomic-clocks/ -->
<!--   Wikipedia, "Marzullo's algorithm" — https://en.wikipedia.org/wiki/Marzullo's_algorithm -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. TrueTime API returns an interval TTinterval = [earliest, latest] guaranteed to bound true absolute -->
<!--    time within epsilon (ε), rather than a single timestamp. TT.now(), TT.after(t), TT.before(t) are the -->
<!--    exposed operations. -->
<!-- 2. ε is small (single-digit ms) and follows a sawtooth: the daemon polls time masters every 30 seconds, -->
<!--    assuming a worst-case local drift rate of ~200 microseconds/second, contributing up to ~6ms drift plus -->
<!--    ~1ms communication delay to the masters — so ε swings roughly between 1ms (just after a sync) and 7ms -->
<!--    (just before the next). -->
<!-- 3. Time masters combine GPS receivers and atomic clocks per datacenter; the majority are GPS-based with a -->
<!--    minority of pure-atomic-clock "Armageddon masters" as a fallback if GPS fails or is spoofed/jammed. -->
<!--    Marzullo's algorithm combines multiple noisy/untrusted time references into the tightest interval the -->
<!--    largest subset of sources still agrees on, discarding outliers. -->
<!-- 4. External consistency guarantee: if a transaction T2 starts (in real/wall-clock time) after transaction -->
<!--    T1 commits, T2's commit timestamp is guaranteed greater than T1's — globally, even if T1 and T2 never -->
<!--    exchanged a message or touched the same row/shard. Logical clocks (Lamport, vector clocks) only order -->
<!--    events connected by a causal chain of messages; they cannot make this guarantee for causally unrelated -->
<!--    transactions, which is the general case in a globally-distributed database. -->
<!-- 5. Commit-wait: before making a transaction's writes externally visible, the coordinator waits until -->
<!--    TT.now().earliest is provably past the transaction's chosen commit timestamp s. Because ε is bounded to -->
<!--    single-digit ms, this wait is short in practice (on the order of a few ms) and runs in parallel with -->
<!--    other transaction-commit work rather than blocking serially. -->
<!-- 6. CockroachDB explicitly rejected the atomic-clock/GPS dependency and built Hybrid Logical Clocks (HLC) -->
<!--    instead — a software combination of physical clock reads and a logical counter — trading Spanner's -->
<!--    tight real-time bound for the ability to run on commodity hardware without owning datacenters, at the -->
<!--    cost of more transaction restarts under clock skew. -->

# Google Made Clock Uncertainty a Number Small Enough to Wait Out

**Date:** 2026-07-31
**Company:** Google (Spanner)
**Category:** stability
**Post type:** contrarian
**Opening style:** challenge_assumption
**Slug:** google-spanner-truetime-commit-wait
**Character count (LinkedIn):** ~2617

---

## LinkedIn Post

Every distributed-systems text repeats the same warning: never trust wall-clock time across machines. Clocks drift, NTP jitters by tens or hundreds of milliseconds over a WAN. The standard fix is to throw the clock away — Lamport clocks, vector clocks, counters that only capture "happened-before" for events that actually exchange a message.

That's the wall Spanner hit. It needed one global commit-timestamp order across every shard in every datacenter: if T2 starts after T1 commits — even sharing no row, no server, no message — T2's timestamp must still land after T1's. Logical clocks can't give you that; they only order events that communicate. Two transactions with zero causal link are invisible to a Lamport clock, and that's exactly the case Spanner had to get right, everywhere, always.

Plain NTP can't either — not because the idea is wrong, but because its error bound is too loose to act on. If you don't know your uncertainty, you can't safely wait it out; you'd have to guess.

So Google did the opposite of "don't trust clocks": they made the clock trustworthy enough to trust completely. TrueTime doesn't return a timestamp — it returns an interval, [earliest, latest], guaranteed to contain true time. GPS receivers and atomic clocks sit in every datacenter as time masters; each server polls several and combines readings with Marzullo's algorithm, discarding outliers and keeping the tightest interval every source still agrees on. Between polls (every 30s), local drift widens that interval in a sawtooth — ~1ms right after a sync, up to 7ms before the next.

The move: when Spanner commits at timestamp s, it doesn't publish yet. It waits until TT.now().earliest is provably past s — "commit-wait," a few milliseconds, since epsilon is capped at single digits. That short, deliberate pause turns "probably ordered" into "provably ordered," for transactions that never knew the other existed.

The cost doesn't go away: GPS antennas and atomic clocks in every datacenter, a second "Armageddon master" tier against GPS spoofing, and a latency floor on every commit no network tuning removes — bounded by epsilon, not round-trip time. It's also why nobody outside Google adopts TrueTime directly: CockroachDB built Hybrid Logical Clocks instead, trading tighter guarantees for commodity hardware and more retries under drift.

"Avoid physical time" isn't wrong — it's the cheap way out. Spanner bet the hard problem, priced honestly in racks of atomic clocks, was still cheaper than living without a global order.

#SystemDesign #DistributedSystems #GoogleSpanner #Databases

---

## Twitter / X Version

1/ Every distributed systems text says the same thing: never trust wall-clock time. Google built Spanner, a globally consistent database, by trusting it more than anyone ever had.

2/ Spanner needed one global commit order across every datacenter: if T2 starts after T1 commits — even with zero shared rows or messages between them — T2's timestamp has to land after T1's. Lamport/vector clocks can't do this. They only order events that actually communicate.

3/ Plain NTP can't do it either. Not because the idea is wrong — because its error bound (tens to hundreds of ms over a WAN) is too loose to act on. You can't safely wait out uncertainty you can't bound.

4/ So Spanner's TrueTime doesn't return a timestamp. It returns an interval [earliest, latest] guaranteed to contain the true time. GPS + atomic clocks sit in every datacenter as time masters; servers poll several and merge readings with Marzullo's algorithm, tossing outliers.

5/ Between 30s polls, drift widens that interval in a sawtooth: ~1ms right after sync, up to 7ms before the next. When committing at timestamp s, Spanner just waits until TT.now().earliest is provably past s — "commit-wait," a few ms — before publishing the result.

6/ That deliberate wait is the whole trick: it turns "probably ordered" into "provably ordered," even for transactions that never knew about each other.

7/ Cost: GPS antennas + atomic clocks in every DC, a spoofing-resistant "Armageddon master" tier, and a latency floor on every commit no network tuning removes. It's also why CockroachDB built Hybrid Logical Clocks instead — commodity hardware, weaker real-time guarantees, more retries under drift.

8/ "Avoid physical time" isn't wrong. It's just the cheap way out. Spanner bet that the hard problem, priced honestly in racks of atomic clocks, was cheaper than living without a global order.

---

## Excalidraw Diagram

**File:** 2026-07-31-google-spanner-truetime-commit-wait.excalidraw
**Type:** Contrarian side-by-side callouts + a sawtooth line graph — the single spatial mechanism (ε growing and resetting between time-master polls) sits at the top, with "the default" (logical clocks / NTP) and "the move" (TrueTime + commit-wait) as two matched callout boxes below it.
**Color scheme:** Teal for the sawtooth line itself (the measured, trustworthy signal). Amber for "the default" callout and the commit-wait highlight box — not because the default was foolish, but to mark it as the well-worn, lower-investment path. Indigo for "the move" callout — the higher-investment, deliberate choice. Slate for the footnote. No red/green: the default wasn't broken, it just wouldn't clear the bar Spanner needed.
**Screenshottable stat:** "ε swings between 1ms (right after a GPS/atomic-clock sync) and 7ms (right before the next one, 30 seconds later) — and Spanner's commit-wait just waits out that number instead of pretending it's zero."

### Layout

```
Title: "Google Made Clock Uncertainty a Number Small Enough to Wait Out"
Subtitle: "OSDI 2012 — how Spanner's TrueTime turns a bounded clock interval into a global commit order"

[LINE GRAPH — ε (ms) over time, teal sawtooth]
  Axis label: "ε (clock uncertainty, ms) between GPS + atomic-clock time-master syncs"
  Line rises from 1ms to 7ms across each 30s poll interval, then drops instantly back to ~1ms at
  the next sync — three cycles shown. Labeled "1ms" at the troughs, "7ms (right before resync)" at
  the peaks. Small note under the graph: "Each drop = a time-master poll, every 30s. Drift between
  polls (~200μs/s) rebuilds the sawtooth."
  Dashed amber callout box overlaid near a peak: "commit-wait: hold the result until TT.now()
  .earliest > s" — visually anchoring the wait to the uncertainty it's waiting out.

[CALLOUT — amber — THE DEFAULT]
Lamport/vector clocks order events that exchange a message — nothing else. Plain NTP's error bound
is tens to hundreds of ms over a WAN, too loose to act on. Neither can order two transactions that
share no row, no server, no message — exactly the case Spanner had to get right, everywhere, always.

[CALLOUT — indigo — THE MOVE]
TrueTime returns [earliest, latest], not a point. GPS + atomic clocks in every datacenter feed it;
Marzullo's algorithm merges readings and discards liars. ε stays single-digit ms, so commit-wait
(holding the result until TT.now().earliest > s) costs a few ms instead of the hundreds NTP would
require.

[FOOTNOTE — slate]
The uncertainty never fully disappears — it's just made small and known. That's also the bill: GPS
antennas and atomic clocks in every datacenter, an "Armageddon master" tier of pure atomic clocks
against GPS spoofing, and a latency floor on every commit that no network tuning removes. It's why
CockroachDB built Hybrid Logical Clocks instead — commodity hardware, weaker real-time guarantees,
more retries.
```
