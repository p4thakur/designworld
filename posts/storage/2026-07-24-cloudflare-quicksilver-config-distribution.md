<!-- sources -->
<!-- Primary: Cloudflare Blog, "Introducing Quicksilver: Configuration Distribution at Internet Scale," -->
<!--   blog.cloudflare.com, published 2020-03. -->
<!--   URL: https://blog.cloudflare.com/introducing-quicksilver-configuration-distribution-at-internet-scale/ -->
<!-- Primary: Cloudflare Blog, "Moving Quicksilver into production," blog.cloudflare.com. -->
<!--   URL: https://blog.cloudflare.com/moving-quicksilver-into-production/ -->
<!-- Primary: Cloudflare Blog, "PIPEFAIL: How a missing shell option slowed Cloudflare down," -->
<!--   blog.cloudflare.com, published 2022-04-05 (incident of 2021-12-16). -->
<!--   URL: https://blog.cloudflare.com/pipefail-how-a-missing-shell-option-slowed-cloudflare-down/ -->
<!-- Primary: Cloudflare Blog, "Quicksilver v2: evolution of a globally distributed key-value store" -->
<!--   (Part 1 and Part 2), blog.cloudflare.com, published 2025-07. -->
<!--   URLs: https://blog.cloudflare.com/quicksilver-v2-evolution-of-a-globally-distributed-key-value-store-part-1/ -->
<!--         https://blog.cloudflare.com/quicksilver-v2-evolution-of-a-globally-distributed-key-value-store-part-2-of-2/ -->
<!-- Secondary corroboration: InfoQ, "How Cloudflare Migrated Quicksilver to Multi-Level Caching While Serving -->
<!--   Billions of Requests" (infoq.com/news/2025/08/cloudflare-key-value-store/); Hacker News discussion of the -->
<!--   PIPEFAIL post (news.ycombinator.com/item?id=30918689); LMDB reference documentation (lmdb.tech/doc/, -->
<!--   en.wikipedia.org/wiki/Lightning_Memory-Mapped_Database) used only to confirm the generic mechanism -->
<!--   (single-writer/multi-reader MVCC, copy-on-write, memory-mapped reads) Cloudflare's posts describe using. -->
<!-- Note: direct WebFetch of blog.cloudflare.com returned HTTP 403 under this session's egress policy (same -->
<!--   recurring failure mode documented in earlier posts in this repo, e.g. the 2026-07-18 Etsy post and -->
<!--   2026-07-22 Spotify post). Facts below are cross-checked across multiple independent WebSearch result -->
<!--   excerpts that directly quote or closely paraphrase the primary blog.cloudflare.com posts, corroborated by -->
<!--   the InfoQ secondary summary and the Hacker News thread discussing the primary PIPEFAIL post, all repeating -->
<!--   the same specific numbers without contradiction. -->
<!-- Key verifiable details (quoted or closely paraphrased via search excerpts): -->
<!-- 1. Kyoto Tycoon: many components ran on a single physical root server; became a growing risk over the years, -->
<!--   including one incident where the root node disappeared due to faulty hardware. Fine at a small number of -->
<!--   locations; ran into operational problems at hundreds of locations; not secure by default. Removing it -->
<!--   entirely (50+ producer teams migrated one at a time, across time zones) took about four years. -->
<!-- 2. Quicksilver v1 (2020): LMDB per node — memory-mapped B+tree, single-writer/multi-reader MVCC, -->
<!--   copy-on-write pages, read transactions that never block and are never blocked, read-only mmap for -->
<!--   corruption immunity, a batch-write mode combining many updates into one disk commit. Root → intermediate -->
<!--   → leaf replication tree; asynchronous because different parts of the world replicate at different speeds. -->
<!--   Each transaction log entry carries a hash of the previous entry plus a combined hash, and is fsynced to -->
<!--   disk on replication from management nodes. A new DNS record or security rule reaches 90% of servers on the -->
<!--   network within seconds. -->
<!-- 3. Scale (2025 v2 posts): 5 billion+ key-value pairs, 1.6TB combined size, serves 3 billion+ keys/second -->
<!--   worldwide, 90% of requests under 1ms, 99.9% under 7ms. -->
<!-- 4. v2 (2025): every server previously held a full copy of the dataset; data centers range from hundreds of -->
<!--   servers down to a single rack, so the full-copy model made dataset size a floor for the smallest possible -->
<!--   edge deployment. Introduced two new roles — replica (stores the full dataset) and proxy (a persistent, -->
<!--   self-evicting cache) — with a hard low-disk-space threshold that temporarily stops adding new keys to the -->
<!--   proxy cache rather than risking disk overflow. -->
<!-- 5. War story (PIPEFAIL, incident of 2021-12-16, published 2022-04-05): between 20:10 and 20:40 UTC, web -->
<!--   requests were delayed up to five seconds. A Kubernetes cron job piped the output of dos-make-addr-conf -->
<!--   into dosctl (which writes the Quicksilver key template_vars) without the shell option `pipefail`; when the -->
<!--   first command failed, its non-zero exit code was silently discarded by the pipeline, and empty output was -->
<!--   written into template_vars regardless. dosd — the peer-to-peer DDoS-detection daemon running on every -->
<!--   Cloudflare server, which depends on Quicksilver for fast configuration access — failed against the bad -->
<!--   config, and Front Line's in-memory cache had to be flushed, stalling requests while it rebuilt. -->
<!-- Mechanism-level explanation of *why* single-writer/copy-on-write MVCC lets reads run lock-free off a memory -->
<!--   map with zero allocation, and why a hash-chained log lets any node self-verify replication integrity -->
<!--   without a central authority, is standard distributed-systems/storage-engine internals knowledge, used here -->
<!--   to go one level deeper than the blog posts, per the skill's sourcing guidance. -->

# Quicksilver: Cloudflare's Config Store Where Fast Replication Cuts Both Ways

**Date:** 2026-07-24
**Company:** Cloudflare
**Category:** storage
**Post type:** structured
**Opening style:** cold_fact
**Slug:** cloudflare-quicksilver-config-distribution
**Character count (LinkedIn):** ~2,651

---

## LinkedIn Post

For years, one physical server sat at the root of every configuration change reaching Cloudflare's global edge. Then faulty hardware made it disappear.

That server ran Kyoto Tycoon, an open-source KV store pushing DNS records, WAF rules, and routing config to every data center. Fine across a handful of locations. Past a few hundred, replication turned into an operational headache, the root was a literal single point of failure, and Kyoto Tycoon wasn't secure by default — a bad set of assumptions once you're the root of trust for your network's live config.

The obvious fix — add root replicas, harden the root — skips the real problem. A global config change has a specific shape: writes are rare and tiny (a DNS record, a rule), but reads sit on the hot path of every HTTP request, at hundreds of thousands of machines that can never block on a lock. A sturdier root is still one root.

Quicksilver pushed the read path down to the metal instead. Every server keeps its own LMDB — a memory-mapped B+tree with single-writer, multi-reader MVCC and copy-on-write pages. Reads never block, never get blocked, never malloc: a lookup is a pointer dereference into memory the kernel already mapped. Writes flow one way — root, to intermediate nodes, to leaf servers — as a hash-chained log, each entry hashing the one before it, fsynced to disk, so any node detects a gap or corruption without asking a central authority. That's why a DNS change reaches 90% of the fleet in seconds, and reads hold p90 under 1ms across 5 billion-plus keys.

It cost them the assumption that every server can hold the whole dataset. Past 1.6TB, a single-rack colo in a small city needed the same full copy as a hub with hundreds of machines — disk, not CPU, became the ceiling. Cloudflare's 2025 rewrite split the role: replica nodes keep the full set, proxy nodes keep a self-evicting cache, with a hard cutoff that stops ingesting new keys before a small box fills its disk.

The same fan-out that makes Quicksilver fast also makes it dangerous. On Dec 16, 2021, a cron job piped one shell command into another without `pipefail` — a failed step's exit code got silently swallowed, and an empty config doc got written into a key the fleet-wide DDoS-detection daemon depends on. It replicated everywhere in the same few seconds a real change would, and every server's peer-to-peer defense mesh choked on it at once. Requests queued behind it up to 5 seconds, for 30 minutes.

Fast, global replication and a fast, global blast radius are the same mechanism, pointed at different outcomes.

#SystemDesign #Cloudflare #DistributedSystems #Infrastructure

---

## Twitter / X Version

One physical server was the root of every config change reaching Cloudflare's edge. Then faulty hardware made it disappear.

That was Kyoto Tycoon — fine for a handful of locations, an operational and security liability past a few hundred.

Quicksilver's fix: push reads to the metal. Every server runs LMDB — a memory-mapped B+tree, single writer, readers that never block and never malloc. Writes flow root → intermediate → leaf as a hash-chained, fsynced log. A DNS change hits 90% of the fleet in seconds; reads hold p90 under 1ms across 5B+ keys.

Cost: every server needed the full dataset, so a 1-rack colo carried the same 1.6TB as a hub. 2025's fix split replica (full copy) from proxy (self-evicting cache), with a hard cutoff before a small box fills its disk.

Dec 16, 2021: a script piped two commands without `pipefail`. A failed step's exit code vanished, and empty config replicated everywhere in seconds — same mechanism, wrong payload. The fleet-wide DDoS daemon choked on it. Requests stalled up to 5s, for 30 minutes.

---

## Excalidraw Diagram

**File:** 2026-07-24-cloudflare-quicksilver-config-distribution.excalidraw
**Type:** Migration timeline (structured case study style) — three horizontal stages (Kyoto Tycoon → Quicksilver v1 → Quicksilver v2) with specific numbers at each stage, a mechanism-match explainer band underneath, and an incident callout showing the same mechanism causing a real outage.
**Color scheme:** Slate for the neutral opening stage (Kyoto Tycoon wasn't a bad choice, just aged out of its scale). Blue for Quicksilver v1. Purple for Quicksilver v2. Teal for the mechanism-match explainer. Amber (caution, not "wrong") for the incident callout — the incident wasn't a design flaw in Quicksilver, it was the same fan-out property working exactly as designed on bad input.
**Screenshottable stat:** "1 root server (pre-2020) → 5B+ keys / 1.6TB replicated fleet-wide in seconds, p90 <1ms reads → Dec 16, 2021: one bad write, 30 minutes, up to 5s of added latency"

### Layout

```
Title: "Quicksilver: Cloudflare's Config Store Where Fast Replication Cuts Both Ways"
Subtitle: "One root server → LMDB on every box, hash-chained replication tree → replica/proxy split as the dataset outgrew small colos"

ROW 1 — THE TIMELINE

[KYOTO TYCOON (pre-2020)]      ->      [QUICKSILVER v1 (2020)]      ->      [QUICKSILVER v2 (2025)]
Open-source KV store. One                Every server: its own LMDB —          Full copy no longer fits every
physical server as root of the           mmap'd B+tree, single-writer          colo. Split into replica (full
replication tree for the whole           MVCC. Root -> intermediate ->         dataset) and proxy (self-
network. Fine under a handful            leaf, hash-chained log,               evicting cache) roles. Hard
of locations; an operational             fsynced. Full copy on every           cutoff stops ingest before a
and security liability past a            single box.                          small box fills its disk.
few hundred. Root node once
disappeared to faulty hardware.

[THE MECHANISM MATCH]
Reads sit on every request's hot path across hundreds of thousands of servers that can never block on a lock —
LMDB's single-writer, copy-on-write MVCC lets reads run lock-free straight off a memory map, no malloc, no copy.
Writes are rare and tiny, so they flow one-way down a tree as a hash-chained, fsynced log: each entry hashes the
one before it, so any node can detect corruption or a gap without asking a central authority. That's why a DNS
change reaches 90% of the fleet in seconds, with p90 reads under 1ms across 5B+ keys and 1.6TB of data.

[WHAT BROKE — DEC 16, 2021, 20:10-20:40 UTC]
A cron job piped dos-make-addr-conf into dosctl without `set -o pipefail`. The first command failed; its exit
code was silently swallowed by the pipe, and empty output got written as the value of a Quicksilver key the
fleet-wide DDoS-detection daemon (dosd) depends on. The same instant, global fan-out that makes Quicksilver fast
pushed that empty config everywhere within seconds. dosd choked fleet-wide; requests queued up to 5 seconds for
30 minutes.

Footer: Fast, global replication and a fast, global blast radius are the same mechanism, pointed at different
outcomes.
```
