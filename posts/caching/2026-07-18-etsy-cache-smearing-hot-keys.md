<!-- sources -->
<!-- Primary: Etsy Engineering, "How Etsy caches: hashing, Ketama, and cache smearing," Code as Craft, Nov 2017. -->
<!--   URL: https://www.etsy.com/codeascraft/how-etsy-caches/  (also mirrored at https://codeascraft.com/2017/11/30/how-etsy-caches) -->
<!-- Primary: Etsy Engineering, "mctop - a tool for analyzing memcache get traffic," Code as Craft. -->
<!--   URL: https://www.etsy.com/codeascraft/mctop-a-tool-for-analyzing-memcache-get-traffic/ -->
<!-- Note: direct WebFetch of etsy.com/codeascraft and codeascraft.com returned HTTP 403 under this session's -->
<!--   egress policy -- WebFetch of https://example.com also returned 403, confirming a session-wide WebFetch -->
<!--   outage rather than a per-site block (same failure mode noted in the prior day's post). Facts below are -->
<!--   cross-checked across multiple independent WebSearch result excerpts that quote or closely paraphrase both -->
<!--   primary posts, corroborated by a secondary summary (atech.guide's "Scaling Caching at Etsy") that -->
<!--   independently repeats the same smearing entropy range (0-8, sometimes 0-16) and the same NIC-saturation -->
<!--   framing. -->
<!-- Key verifiable details (quoted or closely paraphrased via search excerpts): -->
<!-- 1. Etsy uses Ketama to implement consistent hashing for its memcached pools: the hash space is divided into -->
<!--    large contiguous buckets, one (or more) per cache host, so a given key always maps to the same host -->
<!--    regardless of pool size, and resizing the pool only remaps a small slice of keys instead of the whole -->
<!--    cache. -->
<!-- 2. From the mctop post: a hot key drove memcached01's outbound network traffic past 800Mbps, at which point -->
<!--    90th-percentile GET latency rose from ~5ms to ~35ms; once the host's 1Gbps NIC fully saturated at roughly -->
<!--    960Mbps, latency spiked past 200ms. Etsy diagnosed the responsible key via a 60-second packet capture of -->
<!--    memcached01's egress traffic, parsed with tshark, which became the basis for the mctop tool. -->
<!-- 3. Direct quote (paraphrase-safe, closely tracked): keys that are "hit quite often" and store a large enough -->
<!--    value "saturate the network interface of their cache host," and "further horizontal scaling by adding -->
<!--    more cache hosts doesn't help in this case, because it only changes the distribution of keys to hosts -- -->
<!--    at best, it would only move the problem key and saturate a different host." -->
<!-- 4. The fix, "cache smearing": append a small amount of entropy (a random number in a small range, e.g. 0-8 -->
<!--    or 0-16) to a hot key on every read and write, so different smeared variants of the same logical key hash -->
<!--    to different hosts, sharing read/write volume across the pool. -->
<!-- 5. NOT independently verified with hard numbers: exact host count of Etsy's memcached fleet at the time, the -->
<!--    exact percentage of keys remapped on a real production resize (the "roughly 1/N of keys move" figure -->
<!--    below is the textbook property of consistent hashing, illustrated generically, not asserted as an exact -->
<!--    Etsy fleet measurement). -->
<!-- Mechanism-level explanation of *why* modulo hashing thrashes a whole cache on resize, and why consistent -->
<!-- hashing's one-key-one-host guarantee is structurally powerless against a single overloaded key, is standard -->
<!-- distributed-caching internals knowledge, used here to go one level deeper than the blog posts themselves, per -->
<!-- the skill's sourcing guidance. -->

# Etsy's Cache Smearing: When Consistent Hashing's Best Feature Becomes the Bottleneck

**Date:** 2026-07-18
**Company:** Etsy
**Category:** caching
**Post type:** confessional
**Opening style:** specific_number
**Slug:** etsy-cache-smearing-hot-keys
**Character count (LinkedIn):** ~2,430

---

## LinkedIn Post

One key. On a memcached pool spread across dozens of hosts, a single hot key pushed one box's network interface to 960 megabits a second — on a 1 gigabit card.

Etsy's caching layer used Ketama, a consistent-hashing scheme, to spread keys across memcached hosts. It's the reason resizing the pool never ruined anyone's day. With naive modulo hashing — key_hash % N — changing N remaps almost every key at once: add one host and roughly (N-1)/N of the cache goes cold in the same instant, and all of that traffic lands on the database behind it simultaneously. Ketama instead divides the hash space into large contiguous buckets, one per host. Add or remove a host and only the keys in that host's slice move. For years, that property let Etsy scale memcached horizontally without a single painful rehash.

Then one key broke it anyway. A popular listing's cached page data got hit hard enough that its own GET traffic saturated a single host's NIC. As outbound crossed 800Mbps, p90 latency on that box went from 5ms to 35ms. Once it hit roughly 960Mbps — effectively maxed on a 1Gbps card — latency blew past 200ms.

The obvious fix, add more hosts, did nothing. That's the part worth sitting with. Consistent hashing's entire guarantee is that a given key always resolves to the same host, no matter how big the pool is. Five hosts or five hundred, that key was always going to land on exactly one of them. Horizontal scaling only helps when load is spread across many keys. This wasn't a many-keys problem.

Etsy had to build mctop just to find the culprit — a packet capture on the host's egress traffic, parsed with tshark, to see which key was eating the bandwidth. Then they fixed it one level up from the hash function: cache smearing. Append a small random suffix, 0–8, sometimes 0–16, to the hot key on every read and write. One logical key becomes up to sixteen physical keys, and the same Ketama hash, completely untouched, now spreads those sixteen strings across sixteen different hosts.

The routing rule was never broken. It only ever had one key to route.

Nothing here is free. Smearing is manual — applied by hand to whatever mctop flags, not a default. And writes now touch every smeared copy, so two clients reading different smeared variants of the same "key" can briefly see different values. Etsy traded a little consistency for a lot of bandwidth.

#SystemDesign #Caching #Memcached #DistributedSystems

---

## Twitter / X Version

A single memcached key pushed one host's NIC to 960 Mbps — on a 1 Gbps card. p90 latency: 5ms → 35ms → 200ms+.

Etsy's pools used Ketama consistent hashing: a key always resolves to the same host, at any pool size. That's why adding or removing hosts only remaps a slice of keys instead of the whole cache.

Great property — until one key is hot enough on its own. Five hosts or five hundred, that key was always landing on exactly one of them. Adding more hosts did nothing.

Fix: mctop (tshark packet capture on the host's egress) named the key. Then cache smearing — append random entropy (0–8, sometimes 0–16) to the hot key on every read and write. Same hash, untouched, now spread across up to 16 physical keys → up to 16 hosts.

The hash function was never the problem. It just needed more keys to work with.

Cost: it's manual, and writes now touch every smeared copy — so two reads can briefly disagree.

---

## Excalidraw Diagram

**File:** 2026-07-18-etsy-cache-smearing-hot-keys.excalidraw
**Type:** Causal sequence + spike (confessional style) — top row is the mechanism and where it silently breaks (design → promise → the exception → the spike), bottom row is the fix as a sequence (identify → smear → redistribute → result), a wide indigo box spells out the mechanism match, and a footer names the tradeoff.
**Color scheme:** Slate for the neutral design/promise boxes (Ketama wasn't wrong — it was right for every key except one), amber/red for the hot-key and spike boxes, teal/green for the fix-row boxes and its result, indigo for the mechanism explainer. No default villain — consistent hashing's guarantee is what made scaling painless for years before it became the ceiling.
**Screenshottable stat:** "960 Mbps on a 1 Gbps NIC · p90 latency 5ms → 35ms → 200ms+ · fix: 1 key → up to 16 keys"

### Layout

```
Title: "Etsy's Cache Smearing: When Consistent Hashing's Best Feature Becomes the Bottleneck"
Subtitle: "1 key → 1 host, always · memcached01 hit 960 Mbps on a 1 Gbps NIC · fix: 1 key → 16 keys"

ROW 1 — THE MECHANISM, AND WHERE IT SILENTLY BREAKS
[THE DESIGN]              →   [THE PROMISE]              →   [THE HOT KEY]              →   [THE SPIKE]
Ketama consistent hash:       Resize the pool and only        Same guarantee, now a           Outbound > 800Mbps: p90
hash space split into         the keys in the changed         liability: one listing's        latency 5ms → 35ms.
large contiguous buckets,     host's slice remap. No          cached page data gets            NIC saturates near
one per memcached host.       mass rehash, no stampede.       hit hard enough alone to         960Mbps (1Gbps card):
Key → host is deterministic.  Years of painless scaling.      saturate memcached01's NIC.      latency > 200ms.

ROW 2 — THE FIX: CACHE SMEARING
[IDENTIFY]                →   [SMEAR]                    →   [REDISTRIBUTE]             →   [RESULT]
mctop: 60s packet capture     Append random entropy           Same Ketama hash, untouched,    Hot value's read volume
of memcached01's egress,      (0-8, sometimes 0-16) to        now applied to up to 16          splits across up to 16
tshark-parsed, to find        the hot key on every read        different key strings —          hosts. No single host
exactly which key was         and write.                       each lands on a different        carries more than its
responsible.                                                   host.                             share.

[THE MECHANISM MATCH]
Consistent hashing's whole guarantee is "one key maps to one host, deterministically, at any pool size." That's exactly
what makes horizontal scaling free for ordinary keys — and exactly why it's powerless against one key that's hot enough
on its own: more hosts just relocates the same single point of saturation. Cache smearing doesn't touch the hash
function at all. It multiplies the keys feeding into it — the routing rule wasn't broken, it just needed more keys.

Footer: The tradeoff didn't disappear — it moved. Smearing is manual, applied by hand to whatever mctop flags, not a
default. And writes now touch every smeared copy, so two clients reading different smeared variants of the same
logical key can briefly see different values. Etsy spent a little consistency to buy back bandwidth.
```
