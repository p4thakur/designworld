---
date: 2026-06-23
slug: slack-message-ordering-persist-broadcast
category: messaging
post_type: narrative
opening_style: mid_scene_drop
company: Slack
---

## Sources

- Slack Engineering Blog: "Real-time Messaging," slack.engineering/real-time-messaging/ (2023)

---

## LinkedIn Post

You hit Enter. Slack shows your message instantly. But for a moment, that message only exists in RAM.

That was the original design. And it was elegant, right up until it wasn't.

Slack's real-time messaging layer is built around Channel Servers: stateful, in-memory processes each mapped to a subset of channels via consistent hashing. At peak, a single host serves around 16 million channels. A message arrives at the Channel Server, fans out to Gateway Servers worldwide, and exits through WebSocket connections to connected clients — all in under 500ms, globally.

The early design was broadcast-first: the Channel Server sent the message to connected clients and confirmed it to the sender, then wrote to storage. It felt fast because it was fast. The sender got immediate feedback. The latency was real.

The problem was also real. If the Channel Server crashed between the broadcast and the persist, the message was gone. Not delayed. Not in a retry queue. Gone. To the sender, it looked sent. To everyone offline during that window — including the sender after refreshing — it never happened.

The fix was persist-first: write to storage before broadcasting. The Channel Server only forwards to Gateway Servers after the database acknowledges the write. Durability guaranteed. Real-time delivery preserved.

That solved the loss problem. It created a different one.

Channel Servers are still stateful. Still single-owner per channel — one CS per channel. When a CS goes down, Slack's coordination layer (CHARMs: Consistent Hash Ring Managers) spins up a replacement in under 20 seconds. Those 20 seconds matter. Users see elevated latency. The channel is technically up. It doesn't feel like it.

And then there's ordering. With persist-first and concurrent writers, two near-simultaneous messages can hit storage in a different order than they arrived at the CS. Slack resolves final sequence at the Channel Server after persist — making the CS both a routing layer and a sequencing authority. Those responsibilities don't always want to live in the same place.

Slack handles billions of messages a day. The architecture works. But "sent," "durable," and "ordered" are three separate guarantees, and none of them collapsed into a single clean solution. The tradeoffs didn't disappear. They moved.

#SystemDesign #DistributedSystems #Engineering #Slack

---

**Character count: ~2,350**

---

## Twitter / X Version

You hit Enter. Slack confirms your message instantly.

But for a moment, that message only exists in RAM.

That was the original design. Here's the mess it created. 🧵

---

Slack's messaging runs on Channel Servers (CS): stateful, in-memory, each mapped to a set of channels via consistent hashing.

Peak: ~16 million channels per host.
Global delivery: under 500ms.

---

Original flow: broadcast-first.

CS broadcasts to all connected clients → confirms to sender → THEN writes to storage.

Fast. Clean feedback. Also: a crash window.

If the CS died between broadcast and persist, the message vanished. Looked sent. Was gone.

---

The fix: persist-first.

Write to DB. Get the ack. Then broadcast to Gateway Servers → WebSocket clients.

Durability guaranteed. Real-time delivery preserved.

---

But stateful systems don't let you off clean.

Each CS is single-owner per channel. When one crashes, CHARMs (Consistent Hash Ring Managers) spins up a replacement in <20 seconds.

Those 20 seconds: elevated latency. Channel is up. Doesn't feel like it.

---

Then there's ordering.

Persist-first with concurrent writers means two near-simultaneous messages can hit storage in a different order than they arrived.

Slack resolves final sequence at the CS level — making the Channel Server both a router and a sequencing authority.

---

"Sent." "Durable." "Ordered."

Three separate guarantees. Each shift moved the problem somewhere else.

The tradeoffs didn't disappear. They moved.

---

## Diagram

See: `slack-message-ordering-persist-broadcast.excalidraw`

Type: Side-by-side sequence flow (broadcast-first vs persist-first)
Style: Amber/warm for the original crash window, blue/teal for the persist-first current design
