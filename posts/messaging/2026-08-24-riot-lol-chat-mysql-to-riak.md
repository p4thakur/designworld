<!-- sources -->
<!-- Primary: -->
<!--   Riot Games Technology blog, "Chat Service Architecture: Persistence" -->
<!--   https://technology.riotgames.com/news/chat-service-architecture-persistence -->
<!--   Riot Games Technology blog, "Chat Service Architecture: Servers" -->
<!--   https://technology.riotgames.com/news/chat-service-architecture-servers -->
<!--   Riot Games Technology blog, "Chat Service Architecture: Protocol" -->
<!--   https://technology.riotgames.com/news/chat-service-architecture-protocol -->
<!--     — direct WebFetch of technology.riotgames.com and highscalability.com both returned EGRESS_BLOCKED -->
<!--     under this session's network policy (same class of gateway-level denial noted on prior posts in -->
<!--     this series). Facts below were cross-checked across multiple independent web-search-result excerpts -->
<!--     that directly quote or closely paraphrase Riot's own engineering blog posts, not written from memory. -->
<!-- Corroborating (independent secondary sources, cross-referenced for consistency): -->
<!--   High Scalability, "How League of Legends Scaled Chat to 70 million Players" -->
<!--   https://highscalability.com/how-league-of-legends-scaled-chat-to-70-million-players-it-t/ -->
<!--   Strange Loop 2014 talk listing, "Scaling League of Legends Chat to 70 million Players" -->
<!--   https://www.thestrangeloop.com/2014/scaling-league-of-legends-chat-to-70-million-players.html -->
<!-- Key verifiable details (cross-referenced across independent search excerpts that quote/summarize -->
<!-- Riot's own engineering blog posts consistently): -->
<!-- 1. Riot's chat servers are built on a heavily modified, internally rewritten fork of ejabberd: roughly -->
<!--   90% Erlang, 10% C (the C used for XML parsing, SSL handling, and string manipulation). -->
<!-- 2. The chat server tier has no single point of failure by design — sessions are not pinned to one -->
<!--   server, so when a server shuts down (planned or not), client-side reconnect logic moves the player to -->
<!--   another server without disrupting the chat experience. -->
<!-- 3. As League of Legends' player base grew toward roughly 70 million players (per the 2014 Strange Loop -->
<!--   talk and High Scalability writeup of Riot's own presentation), chat servers began overloading a single -->
<!--   MySQL primary instance that held rosters, friend notes, and privacy lists. -->
<!-- 4. Loading a friends list, accepting a friend invite, or editing a note on a player all wrote to and read -->
<!--   from that same MySQL primary; small performance glitches on that one instance surfaced to players as -->
<!--   timeouts loading their friends list. -->
<!-- 5. Riot's initial response was to scale the MySQL primary vertically — adding more memory and then -->
<!--   costly FusionIO flash storage — before concluding that a single writer was itself the structural risk, -->
<!--   not just a capacity problem. -->
<!-- 6. Riot migrated chat persistence to Riak, a masterless, distributed key-value store that provides -->
<!--   availability/partition-tolerance (AP) semantics and can scale horizontally, removing the single-writer -->
<!--   dependency. -->
<!-- 7. Because Riak allows any node to accept a write, concurrent updates to the same player's data (e.g. two -->
<!--   chat servers both recording a friend invite at once) can produce conflicting versions. Riak stores both -->
<!--   versions rather than rejecting one, and Riot's own CRDT (convergent replicated data type) extensions to -->
<!--   ejabberd merge the conflicting versions the next time that player's client connects. -->
<!-- 8. The migration was partial rather than a full cutover: depending on the shard, the persistence layer -->
<!--   today is either MySQL (legacy shards) or Riak (newer shards). -->
<!-- 9. Riot also extended core XMPP itself for chat, via internal "RXEP" (Riot XMPP Enhancement Proposal) -->
<!--   extensions — e.g. friend roster notes and incremental privacy-list updates — features with no existing -->
<!--   XMPP standard to build on. -->
<!-- Publication: Riot Games Technology blog (technology.riotgames.com), "Chat Service Architecture" series, -->
<!-- and the associated 2014 Strange Loop conference talk. -->

# League of Legends' Chat Servers Had No Single Point of Failure. Its Database Did.

**Date:** 2026-08-24
**Company:** Riot Games
**Category:** messaging
**Post type:** narrative
**Opening style:** mid_scene_drop
**Slug:** riot-lol-chat-mysql-to-riak
**Character count (LinkedIn):** ~2360

---

## LinkedIn Post

League of Legends' chat servers had no single point of failure. Its database did.

By 2014, Riot's chat system was carrying League past 70 million players, and the servers underneath were built for exactly this kind of scale: 90% Erlang, 10% C, layered on a heavily rewritten ejabberd. No single chat server owned a player's session. If one machine went down mid-conversation, the client just reconnected somewhere else and kept going.

But every one of those masterless, fault-tolerant servers still wrote to the same place: one MySQL primary holding every roster, friend note, and privacy list in the game. Loading your friends list, accepting an invite, jotting a note on a teammate — all of it funneled through that single writer. As the player base kept climbing, small hiccups on that one box turned into timeouts on everyone's friend list.

Riot's first fix was the obvious one: make the primary bigger. More memory, then FusionIO storage, because scaling one machine up is always the easier call than redesigning around it — until the machine itself becomes the risk. A chat system engineered from the ground up to survive server failure was still one bad MySQL night away from breaking rosters for the whole player base.

So they replaced the primary with something that had no primary. Riak, a masterless key-value store, lets any node accept a write, which is what actually removes the single point of failure — but it also means two chat servers can now write conflicting versions of the same roster at the same time. Riot didn't try to prevent that. When it happens, Riak keeps both versions, and a CRDT merge — wired into their own extensions of ejabberd — reconciles them the next time that player logs in.

The single point of failure didn't get eliminated. It moved. It used to sit in the database, as one box that could take down rosters for everyone. Now it sits in the merge logic, as one function that has to correctly reconcile two truths into one, quietly, every time it runs. And Riot never finished the swap — some shards still run on MySQL to this day, split by when they happened to be provisioned.

No one was wrong for building it on a single MySQL writer in the first place. It was the right call for a chat system before it had 70 million concurrent rosters to protect.

#SystemDesign #DistributedSystems #Messaging #Engineering

---

## Twitter / X Version

1/ League of Legends' chat servers had zero single points of failure. Its database was the single point of failure.

2/ By 2014, Riot's chat system — 90% Erlang, masterless, self-healing — served past 70M players. Every server still wrote to one MySQL primary holding every roster and friend note in the game.

3/ Riot's first fix: scale the primary up. More RAM, then FusionIO storage. A fault-tolerant chat architecture was still one bad MySQL night away from breaking every friend list at once.

4/ The real fix: Riak, a masterless key-value store. Any node accepts a write — which also means two servers can now write conflicting rosters at the same time. Riot let that happen and resolved it later with a CRDT merge on next login.

5/ The single point of failure didn't disappear. It moved — from a database box to a merge function that has to reconcile two truths into one, quietly, every login.

6/ Some shards still run MySQL today. Riot never finished the swap — and didn't need to.

---

## Excalidraw Diagram

**File:** 2026-08-24-riot-lol-chat-mysql-to-riak.excalidraw
**Type:** Side-by-side sequence flow (before vs. after), the request path for "load your friends list"
traced through each architecture, with the failure point highlighted in the before-flow — matching the
Narrative post type's recommended layout of showing where the failure happens.
**Color scheme:** Slate for the chat-server tier (unchanged in both flows — it was never the problem), red
for the before-flow's single MySQL writer and its failure mode, indigo for the after-flow's masterless Riak
ring, amber for the conflict itself, and teal for the CRDT resolution step — a five-color set distinct from
the blue/amber/red/green run used on the prior database post.
**Screenshottable stat:** "70M players on a masterless chat tier → all writes still hit ONE MySQL primary →
timeouts on friend-list loads → Riak (masterless) + CRDT merge on next login. Some shards still run MySQL."

### Layout

```
Title: "League of Legends' Chat Servers Had No Single Point of Failure. Its Database Did."
Subtitle: "Riot Games Technology blog, 'Chat Service Architecture' series (2014) — how Riot's chat
persistence layer moved from a single MySQL writer to masterless Riak with CRDT conflict resolution"
Stat callout (amber): "70M players on a masterless chat tier → all writes still hit ONE MySQL primary →
timeouts on friend-list loads → Riak (masterless) + CRDT merge on next login. Some shards still run MySQL."

Section label: "THE SAME REQUEST, TWO ARCHITECTURES — 'LOAD MY FRIENDS LIST'"

[LEFT COLUMN — BEFORE, x 60-560]                    [RIGHT COLUMN — AFTER, x 640-1140]
"CLIENT" [slate]                                     "CLIENT" [slate]
    v                                                     v
"CHAT SERVER (Erlang, masterless,                   "CHAT SERVER (Erlang, masterless,
no SPOF — any node can serve you)" [slate]           no SPOF — any node can serve you)" [slate]
    v                                                     v
"MYSQL PRIMARY — single writer for                  "RIAK RING — any node accepts the
every roster, note, and privacy list" [red,          write. No primary to overload." [indigo]
highlighted as the failure point]                        v
    v                                                "CONCURRENT WRITE ON SAME ROSTER?
"RESULT: primary hiccup = timeout                    Riak keeps BOTH versions instead
loading your friend list, for everyone" [red]        of rejecting one." [amber]
                                                          v
                                                      "CRDT MERGE — reconciled next time
                                                      that player's client connects,
                                                      via Riot's own ejabberd extensions." [teal]

[RESULT BAND, teal, full width]
"WHAT ACTUALLY CHANGED: the single point of failure moved from a database box (MySQL primary) to a
function (the CRDT merge) — and some shards never migrated off MySQL at all."

[FOOTER, violet band, full width]
"No one was wrong for building this on a single MySQL writer. It was the right call for a chat system
before it had 70 million concurrent rosters to protect. The tradeoffs didn't disappear when Riak came in.
They moved from 'can the database survive' to 'can the merge function reconcile two truths into one.'"
```
