---
date: 2026-06-21
slug: twitch-irc-go-gc-pauses
category: real-time
post_type: contrarian
opening_style: challenge_assumption
company: Twitch
---

## Sources

- Rhys Hiltner, "Go's march to low-latency GC," Twitch Engineering Blog, July 2016: https://blog.twitch.tv/en/2016/07/05/gos-march-to-low-latency-gc-a6fa96f06eb7/
- "Twitch Engineering: An Introduction and Overview," Twitch Engineering Blog, December 2015: https://blog.twitch.tv/en/2015/12/18/twitch-engineering-an-introduction-and-overview-a23917b71a25/

---

## LinkedIn Post

IRC was declared dead in 2013. Twitch built the world's largest IRC system that same year. The protocol wasn't the problem.

Twitch's chat went live in Go in late 2013, replacing a Python backend. Go's goroutines start at roughly 4KB of stack versus megabytes for OS threads, multiplexed across a small thread pool. At 500,000 concurrent users per physical host — reached without special tuning on pre-release Go 1.2 — the concurrency math works decisively in Go's favor. One production process ran with 1.5 million active goroutines.

But Go was young. And its garbage collector showed it.

GC pauses froze Twitch's chat servers for tens of seconds while the collector ran stop-the-world cycles. In a system where users notice 200ms of lag, a 2-second pause looks like an outage. A 10-second pause is indistinguishable from one.

Their workaround: pre-allocate aggressively, minimize heap churn, manually trigger GC at controlled off-peak moments to avoid surprise pauses during events. It worked well enough to ship. But it was borrowed time.

In 2016, Twitch published "Go's march to low-latency GC" — not a victory lap, but a detailed public accounting of what the GC was doing to their latency and what mitigations they'd tried. It named the failure modes precisely.

The improvements that followed: Go 1.5 cut pause time from 2 seconds to 200ms. Go 1.6 cut it another 10x. Go 1.7 made their manual workarounds unnecessary entirely.

The obvious move was to abandon Go or paper over the problem internally. Twitch did neither. They made the failure mode specific, made it public, and let the Go team see exactly what a real-time production workload at genuine scale looks like under GC pressure.

IRC still serves Twitch's chat today. Go's GC is now sub-millisecond. The protocol everyone called dead was exactly right for the scale they needed. The language everyone called production-ready had a two-second freeze baked in. Consensus doesn't survive production.

#SystemDesign #RealTimeSystems #Go #Engineering

---

**Character count: ~2,041**

---

## Twitter / X Version

Twitch's chat runs on IRC — a protocol from 1988.

At peak: 500,000 concurrent users per server. 1.5 million goroutines per process.

IRC wasn't the problem. Go's garbage collector was. 🧵

---

In 2013, Twitch rewrote chat in Go, replacing Python.

Go goroutines: ~4KB each. OS threads: megabytes each.

At 500K concurrent connections per host, the math is decisive. Go was the right call.

---

But Go 1.2's GC ran stop-the-world pauses.

At Twitch's scale, they lasted tens of seconds.

In a real-time chat system, 10 seconds of freeze is a chat outage. Their workaround: manually trigger GC at off-peak moments. Pre-allocate everything.

---

In 2016, Twitch published "Go's march to low-latency GC."

Not a workaround post. A precise, public diagnosis.

Go 1.5: 2s → 200ms
Go 1.6: another 10x
Go 1.7: manual tuning made unnecessary

---

The obvious move was switching languages.

Twitch stayed, documented, and pushed.

IRC still runs their chat. Go's GC is now sub-millisecond.

The protocol everyone called dead was exactly right. The language everyone called ready had a 2-second freeze in it.

---

## Diagram

See: `twitch-irc-go-gc-pauses.excalidraw.json`

Type: GC pause reduction timeline (improvement curve across Go versions)
Key numbers: ~30s (Go 1.2) → ~2s (Go 1.4) → 200ms (Go 1.5, 10x) → ~20ms (Go 1.6, 10x) → <1ms (Go 1.7)
Colors: Warm amber (#f97316) for high-pause versions transitioning to cool teal (#0ea5e9) for low-pause versions
Stats callout: 500,000 concurrent users/server | 1.5M goroutines/process
