<!-- sources -->
<!-- Primary: -->
<!--   Discord Blog (2017-07-06), "How Discord Scaled Elixir to 5,000,000 Concurrent Users" — Stanislav Vishnevskiy -->
<!--   URL: https://discord.com/blog/how-discord-scaled-elixir-to-5-000-000-concurrent-users -->
<!--   GitHub: discord/manifold (README) — https://github.com/discord/manifold -->
<!--   GitHub: discord/ex_hash_ring (README) — https://github.com/discord/ex_hash_ring -->
<!-- Note: direct fetch of discord.com/blog, its Medium mirror, elixir-lang.org, and several third-party mirrors -->
<!-- returned HTTP 403 under this session's egress policy (bot protection). The GitHub READMEs for -->
<!-- discord/manifold and discord/ex_hash_ring — Discord's own open-sourced libraries built to fix the exact -->
<!-- problems described in the blog post — were fetched directly and quote the blog's own numbers verbatim -->
<!-- ("send calls cost about 70 µs/op", "packets/sec drop by half immediately"). Those figures, plus the -->
<!-- ~100,000 PIDs / ~12µs ring-lookup / ~30s reconnect-storm cost / /r/Overwatch 30,000-user guild figures, were -->
<!-- cross-checked across independent search-result excerpts quoting the primary Discord blog post directly. -->
<!-- Corroborating (cross-checked, consistent on figures below): -->
<!--   https://elixir-lang.org/blog/2020/10/08/real-time-communication-at-scale-with-elixir-at-discord/ -->
<!--   https://elixirforum.com/t/how-discord-scaled-elixir-to-5-000-000-concurrent-users/6788 -->
<!--   https://news.ycombinator.com/item?id=19238221 -->
<!--   https://sudonull.com/post/68063-How-Discord-Scaled-Elixir-to-5-Million-Concurrent-Users -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Discord's real-time chat layer runs one GenServer process per Discord server ("guild") and one per user -->
<!--    session, communicating across the cluster via Erlang's location-transparent send/2 -->
<!-- 2. By 2017, some guilds — e.g. the /r/Overwatch community's Discord — had grown to up to 30,000 concurrently -->
<!--    connected users in a single guild process -->
<!-- 3. Distributed Erlang forms a fully connected mesh by default; sending a message to a remote PID looks -->
<!--    identical in code to sending to a local one, but each remote send/2 call cost roughly 70 microseconds -->
<!-- 4. Some busy guild GenServers had on the order of 100,000 session PIDs attached, spread across many nodes; -->
<!--    looping send/2 once per PID caused those processes to fall behind their own message queues -->
<!-- 5. Discord's fix, open-sourced as "Manifold": group target PIDs by which remote node they live on, then send -->
<!--    one batched message per node to a local Manifold.Partitioner process, which fans the message out locally -->
<!--    — bounding network sends to "one per node" instead of "one per session" -->
<!-- 6. Per Discord's own post-deploy numbers: packets/sec dropped by half immediately, and guild processes that -->
<!--    had been lagging caught back up with their queues -->
<!-- 7. Separately, Discord used a consistent-hashing ring to find which node owns a given guild/session; a single -->
<!--    lookup cost about 12 microseconds, but a crash-triggered mass reconnect storm made the aggregate cost of -->
<!--    re-running that lookup for every reconnecting session add up to roughly 30 seconds of pure overhead -->
<!-- 8. Discord's fix: rewrite the ring from a C-backed implementation into pure Elixir, then have one process own -->
<!--    the canonical ring and continuously copy it into ETS (Erlang's concurrent in-memory table) so every other -->
<!--    process could read it directly instead of queuing behind a single owner process; open-sourced as -->
<!--    "ex_hash_ring" -->

# Discord vs. Distributed Erlang's Free Lunch

**Date:** 2026-07-07
**Company:** Discord
**Category:** real-time
**Post type:** contrarian
**Opening style:** challenge_assumption
**Slug:** discord-elixir-manifold-distribution
**Character count (LinkedIn):** ~2,474

---

## LinkedIn Post

Distributed Erlang's biggest selling point is that sending a message to a process on another machine looks exactly like sending one on your own. At 5 million concurrent users, Discord found out "looks the same" and "costs the same" are not the same claim.

Discord built its chat layer on Elixir specifically for this reason: one lightweight GenServer per Discord server, one per user session, and the ability to message any process by PID whether it lives in this node or three machines away. The network stays invisible in the code.

By 2017, some servers — like the r/Overwatch community's Discord — had grown to 30,000 people connected at once, all talking to a single guild process. Every message posted there fanned out to every connected session: one send/2 call per PID, in a loop. Erlang made each of those calls look identical, local or remote.

They weren't identical. Each remote send/2 cost roughly 70 microseconds. Some of these guild processes had around 100,000 session PIDs attached, scattered across dozens of nodes. Loop through all of them, 70 microseconds at a time, and the guild's mailbox starts falling behind its own message queue.

The fix wasn't fewer users or more nodes. Discord built Manifold: instead of one send/2 per PID, it groups the target PIDs by which remote node they live on, then ships one batched message per node to a local partitioner process that fans it out from there. The sender now pays for "one call per node," not "one call per session." Their own numbers after deploy: packets/sec dropped by half, immediately, and the guilds that had been falling behind caught back up.

The same pattern showed up again in their consistent-hashing ring, used to find which node owns a given guild. One lookup: about 12 microseconds, nothing to worry about. But when a crash triggered a mass reconnect, redoing that lookup for every reconnecting session added up to roughly 30 seconds of pure lookup cost, stacked on top of everything else already failing at once. The fix: rewrite the ring in pure Elixir, have one process own it, and continuously copy it into ETS so every other process reads it directly instead of queuing behind a single owner.

Location transparency is a real, useful abstraction. What Discord's fixes have in common is that neither one broke it. They just stopped paying its cost by accident, once per PID, and started paying it on purpose, once per node.

#SystemDesign #Elixir #Erlang #Discord #DistributedSystems

---

## Twitter / X Version

1/ Distributed Erlang's whole pitch: sending to a process on another machine looks exactly like sending to one on yours. Discord hit 5M concurrent users and found out "looks the same" isn't "costs the same."

2/ Discord runs one GenServer per Discord server (guild), one per session. By 2017 some guilds — like r/Overwatch's — had 30,000 people connected at once. Every message fanned out via one send/2 call per PID, in a loop.

3/ Erlang makes local and remote send/2 look identical. They aren't. Each remote call cost ~70µs. Some guild processes had ~100K session PIDs spread across dozens of nodes. Loop through that and the mailbox falls behind.

4/ Fix: Manifold. Instead of one send/2 per PID, group the PIDs by remote node, send one batched message per node to a local partitioner that fans out from there. Cost drops from "per session" to "per node."

5/ Result, per Discord's own numbers: packets/sec dropped by half immediately after deploy. The guilds that were falling behind caught up.

6/ Same story, second act: their consistent-hash ring (finds which node owns a guild) cost ~12µs per lookup — fine, until a crash caused a mass reconnect and re-running that lookup for every session added ~30s of pure overhead on top of an already-bad outage.

7/ Fix: rewrite the ring in pure Elixir, have one process own it, continuously copy it into ETS so every process reads it directly instead of queuing behind a single owner.

8/ Location transparency didn't get removed either time. Discord just stopped paying its cost by accident, per call, and started paying it on purpose, per node.

---

## Excalidraw Diagram

**File:** 2026-07-07-discord-elixir-manifold-distribution.excalidraw
**Type:** Side-by-side architecture (contrarian) — "the assumption" vs "at scale" vs "what they built," plus a second, smaller row showing the same fix pattern recurring in the consistent-hash ring.
**Color scheme:** Slate for the original design assumption (not wrong, just incomplete), amber for the cost that assumption hid at scale, teal for the fix. Same three-color logic repeats in both rows, reinforcing that it's one pattern, not two separate incidents.
**Screenshottable stat:** "100K PIDs/guild · 70µs per remote send/2 · Manifold: packets/sec -50% overnight · ring lookup 12µs → reconnect storm ~30s → fixed via ETS"

### Layout

```
Title: "Discord vs. Distributed Erlang's Free Lunch"
Subtitle: "5M concurrent users · up to 30K in one guild (r/Overwatch) · ~100K session PIDs per busy guild process"

[THE ASSUMPTION]                [AT SCALE (2017)]                    [MANIFOLD]
Distributed Erlang: sending     Guild GenServer loops send/2         Group target PIDs by remote node.
to a remote PID looks exactly   over ~100K session PIDs across       Send one batched message per node
like a local send/2. Location   dozens of nodes. Each remote         to a local Manifold.Partitioner,
transparency by design — the    call: ~70µs. Mailbox falls           which fans out from there.
network is hidden from the      behind its own message queue.
code.                                                                Result: packets/sec drop by half,
                                                                      immediately.

Row 2 label: "The same fix, twice: the consistent-hash ring that finds which node owns a guild"

[Ring lookup: ~12µs each.       [Re-running that lookup for         [Fix: ring rewritten in pure
Fine — until a crash forces     every reconnecting session:         Elixir, copied continuously into
a mass reconnect storm.]        ~30s of pure lookup cost, on        ETS — no single owner process to
                                 top of the outage.]                 queue behind.]

Footnote: Location transparency didn't get removed either time. Discord just stopped paying its cost by
accident, once per PID, and started paying it on purpose, once per node.
```
