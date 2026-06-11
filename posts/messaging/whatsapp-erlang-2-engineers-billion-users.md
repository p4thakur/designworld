---
date: 2026-06-11
slug: whatsapp-erlang-2-engineers-billion-users
category: messaging
post_type: narrative
opening_style: mid_scene_drop
company: WhatsApp
---

## Sources

- Rick Reed, "Scaling to Millions of Simultaneous Connections," Erlang Factory SF 2014
- WhatsApp Engineering Blog: "1 million is so 2011" (archived, Jan 2012)
- Facebook acquisition press release, February 19, 2014
- Wired: "WhatsApp: The Inside Story" (2014)

---

## LinkedIn Post

In 2011, Jan Koum was writing WhatsApp's server in a language most engineers had never heard of: Erlang.

Not Java. Not C++. Not Go — which barely existed. Erlang: a language built in the 1980s for telephone switches, running on a virtual machine called BEAM, with a concurrency model centered on millions of lightweight processes instead of OS threads.

His engineers raised the obvious objections. Small ecosystem. Hard to hire for. Primitive tooling. Jan's answer, in essence: the hard problem is concurrent connections, and Erlang was built for concurrent connections.

That turned out to be the right frame.

Erlang's BEAM spawns processes that start at around 300 bytes of memory each. An OS thread — even a stack-minimized one — costs roughly 8 KB. At 2 million concurrent connections, that gap becomes 600 MB versus 16 GB on a single server. The math doesn't just affect performance. It decides how many servers you need and what your hardware bill looks like at scale.

WhatsApp's team didn't stop there. They ran FreeBSD — not Linux — because FreeBSD's network stack fit their connection patterns better. They tuned the kernel's file descriptor limits into the millions. They modified the BEAM VM itself when they hit ceilings the standard runtime couldn't clear.

By February 2014, when Facebook acquired WhatsApp for $19 billion, the backend was handling 450 million monthly active users and 54 billion messages per day. The engineering team: 32 people.

That ratio is still hard to look at. Most companies at that scale had backend teams measured in hundreds. WhatsApp had 32 — not through heroics, but because Erlang let each server carry a connection load that required far fewer of them.

The real decision wasn't "use Erlang." It was: identify the irreducible constraint — concurrent connections per server — and choose the runtime designed from the ground up for exactly that constraint. Everything else follows from there.

#SystemDesign #Engineering #DistributedSystems #Erlang

---

**Character count: ~2,021**

---

## Twitter / X Version

WhatsApp had 450 million users when Facebook acquired them for $19B.

Their backend engineering team: 32 people.

This isn't a hustle story. It's an Erlang story. 🧵

---

Erlang was built in the 1980s for telecom switches. Massive concurrency, fault tolerance, predictable latency.

Most engineers had never used it. Jan Koum chose it anyway.

His frame: the hard problem is concurrent connections. Erlang was designed for concurrent connections.

---

BEAM — Erlang's VM — spawns processes at ~300 bytes each.

An OS thread costs ~8 KB minimum.

At 2M concurrent connections:
• OS threads → 16 GB RAM per server
• Erlang processes → 600 MB RAM per server

That gap decides your server count and your infrastructure bill.

---

WhatsApp didn't just use Erlang. They went deep.

• Ran FreeBSD (not Linux) — better network stack for their patterns
• Tuned kernel file descriptor limits to millions
• Modified the BEAM VM itself when they hit ceilings

---

By acquisition: 54 billion messages/day. 450M MAU. 32 engineers.

The difference wasn't heroics. It was choosing a runtime designed around the one constraint that actually mattered.

---

## Diagram

See: `whatsapp-erlang-2-engineers-billion-users.excalidraw`

Type: Before/after comparison (OS threads vs BEAM processes) + scaling timeline
Style: Warm orange for OS threads, cool teal for Erlang BEAM — colors show contrast, not judgment
