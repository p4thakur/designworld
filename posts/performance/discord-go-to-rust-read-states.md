# Discord's Read States Service: Why They Rewrote Go in Rust

**Date:** 2026-06-25
**Slug:** `discord-go-to-rust-read-states`
**Category:** performance
**Post Type:** contrarian
**Opening Style:** challenge_assumption

**Sources:**
- Discord Engineering Blog: "Why Discord is switching from Go to Rust" — Jesse Howarth, Feb 2020
  https://discord.com/blog/why-discord-is-switching-from-go-to-rust

---

## LinkedIn Post

Go is fast enough for any high-performance service. That's what most engineers believe. Discord stress-tested that assumption.

Discord's Read States service is one of the most frequently accessed systems in their infrastructure. It tracks which messages every user has read, across every channel, in every server. Every message sent, every channel opened — a lookup or write. At peak, the service processes 30,000 operations per second on a single machine.

And every ~2 minutes, latency spiked to over 10 seconds at p99. Not the database. Not the network. Go's garbage collector.

Go's GC works by scanning live heap objects to find what's safe to free. Read States kept a large in-memory cache — millions of live objects the GC had to inspect on every collection cycle. The more cache hits, the more live objects. The more live objects, the longer the pause. At 30K ops/sec, those pauses became production incidents.

The obvious fixes didn't hold. Tuning GOGC changed the spike frequency without reducing the spike itself. Reducing cache size moved the bottleneck downstream to the database. The problem wasn't configuration. It was the runtime model.

Discord's engineers made an unusual call: rewrite the service in Rust.

Not because Rust benchmarks faster. Because Rust has no garbage collector. Memory lifetimes are determined at compile time through ownership rules — nothing to collect at runtime, no pauses, no spikes.

After the rewrite: p99 dropped from 10ms+ with periodic multi-second spikes to under 1ms. Same hardware. Same workload. Just no GC.

The takeaway isn't "switch everything to Rust." It's narrower: if your service holds large live in-memory state and has strict tail latency requirements, the garbage collector isn't a tuning problem. It's a runtime model problem. Rust solves it by moving memory reasoning from runtime to compile time.

That tradeoff has a real cost. Rust is harder to write. But for Read States, it was the right cost to pay.

#SystemDesign #Rust #Performance #Discord #EngineeringBlog

---

## Twitter Version

Discord's Read States service: 30K ops/sec. Tracks read state for every user, every channel.

Every ~2 minutes: p99 latency spike to 10+ seconds. Not the DB. Not the network.

Go's GC was scanning millions of live cache objects on every cycle. Tune GOGC? The frequency changes, the spike stays. Reduce cache? Bottleneck shifts to the database.

The fix: rewrite in Rust.

Not for benchmark wins. Because Rust has no GC. Memory lifetimes are compile-time rules — no runtime scans, no pauses.

Result: p99 went from 10ms+ (with multi-second spikes) to under 1ms. Same hardware.

If your service holds large live state with strict tail latency requirements, the GC isn't a tuning problem. It's a runtime model problem.

---

## Diagram

See `discord-go-to-rust-read-states.excalidraw` in this directory.

**Layout:** Side-by-side comparison — Go (left, red) vs Rust (right, green).
- Left: Hot cache → GC scan cycle every ~2min → p99 spike to 10s+
- Right: Ownership-tracked cache → no GC → p99 under 1ms
- Footer: "Same hardware · 30,000 ops/sec · Only the runtime changed"

**Key screenshottable number:** p99: 10s+ spikes → <1ms
