<!-- sources -->
<!-- Primary: -->
<!--   Linear, "Scaling the Linear Sync Engine" (Tuomas Artman, June 29, 2023) -->
<!--   URL: https://linear.app/now/scaling-the-linear-sync-engine -->
<!-- Note: direct WebFetch of linear.app, bytemash.net, fujimon.com, news.ycombinator.com, hn.algolia.com, and -->
<!-- web.archive.org all returned HTTP 403 / were blocked under this session's egress policy (same recurring -->
<!-- failure mode documented in earlier posts in this repo, e.g. the 2026-07-28 Zuul post and 2026-07-26 Uber -->
<!-- post). raw.githubusercontent.com fetches succeeded. Facts below are cross-checked across multiple independent -->
<!-- WebSearch result excerpts that directly quote or closely paraphrase the primary linear.app post, corroborated -->
<!-- by: -->
<!--   wzhudev/reverse-linear-sync-engine — a reverse-engineering writeup of the sync engine's client internals, -->
<!--   explicitly endorsed by Linear's CTO — https://github.com/wzhudev/reverse-linear-sync-engine -->
<!--   (README fetched directly via raw.githubusercontent.com) -->
<!--   performance.dev, "How's Linear so fast? A technical breakdown" -->
<!--   https://performance.dev/how-is-linear-so-fast-a-technical-breakdown -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Linear's client persists a working copy of the workspace in IndexedDB and treats it, not the server, as -->
<!--    the source of truth the UI reads from; the server is a sync target the client stays caught up with. -->
<!-- 2. Mechanism: a single global, monotonically increasing "lastSyncId" counter, incremented once per accepted -->
<!--    mutation across the whole system. Each mutation produces a "delta packet" — a typed diff (Insertion, -->
<!--    Update, Archive, Delete, and other action types) tagged with that sync id — broadcast over WebSocket to -->
<!--    every connected client in the affected sync groups, including the client that originated the change. -->
<!-- 3. Transaction lifecycle: a client's own pending mutation is only cleared from its local outbox once the -->
<!--    matching sync id comes back through the same delta-packet broadcast channel as everyone else's — there is -->
<!--    exactly one code path for "apply a change," whether it's the client's own edit, a teammate's edit, or a -->
<!--    backlog of changes accumulated while offline. -->
<!-- 4. Reverse-engineering source explicitly frames this as a total order rather than a CRDT-style partial order, -->
<!--    and notes the sync id can jump by many numbers for one visible edit, because side-effect records (e.g. -->
<!--    activity/history entries) also consume ids from the same global counter. -->
<!-- 5. Bootstrap: a new client (or one too far behind) fetches a full snapshot via a bootstrap endpoint, persists -->
<!--    it to IndexedDB, then subscribes to the delta-packet stream from that snapshot's sync id forward — the -->
<!--    same shape as a database logical-replication subscriber doing an initial snapshot/COPY followed by -->
<!--    streaming WAL from an LSN. -->
<!-- 6. Scaling fix (the evolution): the two heaviest, unbounded tables — issues and comments — lazy-hydrate on -->
<!--    demand via partial indexes scoped to what a given view actually needs, while bounded workspace metadata -->
<!--    (labels, workflow states, projects) still bootstraps eagerly. Result, per corroborating technical -->
<!--    breakdowns of the architecture: startup cost tracks workspace structure, not workspace size — a -->
<!--    10,000-issue workspace boots in about the same time as a 100-issue one. -->
<!-- 7. Conflict handling is last-writer-wins at the field level with local pending transactions rebased in front -->
<!--    of newly arrived deltas, not CRDT merge — a deliberate simplicity tradeoff over full concurrent-edit -->
<!--    merging. -->
<!-- Mechanism-level framing of *why* a single global counter is sufficient (the question being answered is "did I -->
<!--   miss anything since my checkpoint," not "how do two concurrent writes commute") and the direct analogy to -->
<!--   Postgres logical replication's LSN + snapshot/COPY + streaming-WAL subscriber model is standard database -->
<!--   replication internals knowledge, used here to go one level deeper than either primary or secondary source, -->
<!--   per the skill's sourcing guidance. -->

# A Browser Tab, Kept in Sync Like a Postgres Replica

**Date:** 2026-07-29
**Company:** Linear
**Category:** real-time
**Post type:** narrative
**Opening style:** mid_scene
**Slug:** linear-sync-engine-global-sync-id
**Character count (LinkedIn):** ~2,811

---

## LinkedIn Post

Every field you edit in Linear writes to your browser's IndexedDB before a single byte reaches the server. That's not a caching trick bolted onto a normal web app — it's the entire architecture.

Most SPAs solve "real-time" the same way: optimistic UI over a REST or GraphQL cache, a WebSocket that fires on change, invalidate-and-refetch on receipt. Reasonable default, and what most teams should still reach for. But it has two holes Linear's founders couldn't live with. There's no ordering primitive tying a push to whatever else is in flight — a websocket message for issue #482 can land while a filtered list query on the same workspace is mid-request, leaving the cache holding two versions of reality with no rule for which wins. And it doesn't work offline, since every mutation needs a live round trip to "commit." Close the laptop mid-edit and the write doesn't exist yet.

Linear's answer, laid out in their 2023 "Scaling the Linear Sync Engine" post: treat the browser tab like a Postgres replica. Every mutation the server accepts increments one global, monotonically increasing counter — lastSyncId — and emits a delta packet: an ordered, typed diff (insert, update, archive, delete) stamped with that number. The packet broadcasts to every connected client, including whichever one caused it. One code path handles "apply a change locally": consume the next delta packet, bump your local lastSyncId to match. Your edit, a teammate's edit, and a week of offline backlog all move through that same pipe, replayed in order from wherever you last checked in.

That's the shape of logical replication: an initial snapshot, then ordered deltas from a checkpoint, tailed by however many readers subscribe. No CRDT merge logic needed — the real question was never "how do two concurrent edits combine," it was "did I miss anything since my last checkpoint," and one global counter answers that for free.

Not free, though. Even a private label rename bumps a counter the whole workspace shares, so a busy team's own side-effect data — history records, activity logs — inflates the stream every client stays caught up on. And bootstrapping years of issues naively would defeat the point, which is why issues and comments, the two unbounded tables, lazy-load per view instead of loading upfront. Startup cost tracks how a workspace is structured — labels, states, projects — not how big its history has grown. A 10,000-issue workspace opens about as fast as a 100-issue one.

Nobody CRDT'd their way out of merge conflicts here. They noticed the problem was never "reconcile concurrent edits" — it was "keep a replica caught up" — and reached for the log-tailing idea Postgres has used for decades, one browser tab at a time.

#SystemDesign #Linear #RealTimeSync #DistributedSystems

---

## Twitter / X Version

Linear writes every edit to IndexedDB before it ever reaches the server. Not a cache trick — that's the whole architecture.

Most real-time apps do optimistic UI + REST/GraphQL cache + "invalidate on websocket push." Two holes: no ordering between a push and an in-flight fetch, and no offline writes — every mutation needs a live round trip to "commit."

Linear treats the browser tab like a Postgres replica instead. Every accepted mutation bumps one global counter (lastSyncId) and emits an ordered delta packet, broadcast to every client — including the one that sent it. Apply the packet, bump your counter. Same code path whether it's your edit, a teammate's, or a week of backlog.

That's logical replication, reinvented client-side: snapshot + ordered delta stream from a checkpoint. No CRDT merge needed — the real question was never "how do two edits combine," it's "did I miss anything since my last checkpoint." A monotonic counter answers that for free.

Cost: even a private edit bumps a counter the whole workspace shares. And naive bootstrap would choke on years of history — so issues/comments lazy-load per view instead. Startup tracks workspace structure, not size: a 10k-issue workspace boots about as fast as a 100-issue one.

---

## Excalidraw Diagram

**File:** 2026-07-29-linear-sync-engine-global-sync-id.excalidraw
**Type:** Three-row sequence flow (narrative) — row 1 shows the naive cache-and-invalidate approach and where it breaks, row 2 shows Linear's ordered delta-packet mechanism as a request sequence, row 3 shows bootstrap-as-snapshot-plus-replay, unified by a mechanism callout and a scaling-fix callout underneath.
**Color scheme:** Amber for the naive cache-invalidate approach (a reasonable default, not a strawman — most teams should still use it), blue for Linear's delta-packet mechanism, violet for the bootstrap/replay path, slate for the unifying mechanism callout, emerald for the scaling-fix result. Deliberately not a single red/green pass — the naive approach isn't "wrong," it's mismatched to a narrower problem than the one Linear had.
**Screenshottable stat:** "A 10,000-issue workspace boots about as fast as a 100-issue one — startup cost tracks workspace structure, not workspace size."

### Layout

```
Title: "A Browser Tab, Kept in Sync Like a Postgres Replica"
Subtitle: "Linear's sync engine: global sync id as a client-side LSN, IndexedDB as the replica"

ROW 1: THE NAIVE FIX — CACHE + INVALIDATE ON WEBSOCKET PUSH

[Client edits an issue]  →  [Optimistic UI + REST/GraphQL round trip]  →  [WebSocket push → invalidate & refetch list]

[WHERE IT BREAKS]
No ordering primitive ties a push to what's already in flight — a push for issue #482 can land mid-request against
a stale list fetch. No local writes possible offline: every mutation needs a live round trip to "commit."

ROW 2: LINEAR'S SYNC ENGINE — ORDERED DELTA STREAM

[Client A edits a field (tracked locally)]  →  [Server: lastSyncId++, execute mutation, emit delta packet @ id N]  →  [Broadcast delta packet to ALL clients, incl. originator]
                                                                                      ↓                                    ↓
                                          [Client A: matches pending tx to id N → clears outbox → IndexedDB]   [Client B: applies delta, bumps local lastSyncId to N → IndexedDB]

ROW 3: BOOTSTRAP = SNAPSHOT + REPLAY (same shape as Postgres logical replication)

[New client, or offline a week]  →  [Fetch snapshot at known syncId X → hydrate IndexedDB]  →  [Subscribe to delta stream from X forward → replay in order until caught up]

[MECHANISM CALLOUT]
A sync id is a client-side LSN; IndexedDB is the replica. Total order (not CRDT partial order) is enough because the
only question is "did I receive every change since my checkpoint" — the same question a Postgres replica asks.

[SCALING FIX]
Bootstrap cost tracks workspace STRUCTURE (labels, states, projects — bounded), not workspace SIZE (issues, comments —
unbounded, lazy-hydrated per view via partial indexes). A 10,000-issue workspace boots about as fast as a 100-issue one.

Footer: Source: Linear, "Scaling the Linear Sync Engine" (Tuomas Artman, 2023); reverse-engineering docs endorsed by
Linear's CTO (wzhudev/reverse-linear-sync-engine).
```
