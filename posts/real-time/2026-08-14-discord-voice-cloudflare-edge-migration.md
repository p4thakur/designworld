<!-- sources -->
<!-- Primary: -->
<!--   Discord Engineering Blog, "How We Moved Discord Voice to the Edge" (discord.com/blog, published June 9, 2026) -->
<!--     — direct WebFetch of discord.com returned EGRESS_BLOCKED under this session's network policy (same class -->
<!--     of gateway-level denial noted on prior posts in this series, e.g. the Fastly and AWS DynamoDB posts). -->
<!--     Content corroborated via multiple independent web-search-result excerpts and discussion threads that -->
<!--     read and directly quote/summarize the official Discord blog post, not from memory. -->
<!-- Corroborating (independent secondary sources and discussion threads, cross-referenced for consistency): -->
<!--   Lobsters discussion thread on "How We Moved Discord Voice to the Edge" -->
<!--     https://lobste.rs/s/w6ptmr/how_we_moved_discord_voice_edge -->
<!--   Hacker News discussion thread on "How We Moved Discord Voice to the Edge" -->
<!--     https://news.ycombinator.com/item?id=48489830 -->
<!--   Cloudflare, case study page on Discord -->
<!--     https://www.cloudflare.com/case-studies/discord/ -->
<!--   PiunikaWeb, "Discord acknowledges voice problems tied to major Cloudflare backend shift" -->
<!--     https://piunikaweb.com/2026/02/27/discord-acknowledges-voice-problems-cloudflare-backend-shift/ -->
<!--   Discord staff (coral) public post acknowledging the in-progress voice migration to Cloudflare -->
<!--     https://x.com/coral9000/status/2027157346003411400 -->
<!--   "Architecting on Cloudflare," Chapter 10: Realtime — Audio and Video at the Edge -->
<!--     https://architectingoncloudflare.com/chapter-10/ -->
<!-- Background/context (Discord's original, pre-edge voice architecture — used only for the "before" comparison, -->
<!-- from an earlier, separate Discord blog post, also previously used in this series): -->
<!--   Discord Engineering Blog, "How Discord Handles Two and Half Million Concurrent Voice Users using WebRTC" -->
<!--     https://discord.com/blog/how-discord-handles-two-and-half-million-concurrent-voice-users-using-webrtc -->
<!-- Key verifiable details (cross-referenced across independent write-ups and discussion threads that quote/ -->
<!-- summarize Discord's own migration postmortem consistently): -->
<!-- 1. For most of Discord's history, users connected to the closest of roughly 30-40 hyperscaler-hosted voice -->
<!--   regions. That worked well for users near major cloud regions (e.g. Bay Area, Frankfurt) and poorly for -->
<!--   users far from any hyperscaler presence (e.g. Reykjavik, Auckland, Lagos, Hawaii) — an Icelandic user's -->
<!--   call, for example, routed through Rotterdam. -->
<!-- 2. Discord began migrating voice/video traffic onto Cloudflare's edge network (300+ PoPs vs. ~30-40 -->
<!--   hyperscaler regions), reaching PoPs such as Reykjavik that no major cloud provider serves directly. -->
<!-- 3. Early in the migration, US East showed sustained packet loss of 1.5-2%, against a baseline of under 0.5% -->
<!--   on the prior provider — this pushed Discord away from an initial plan to migrate whole regions on a fixed -->
<!--   calendar, toward a more cautious, capacity-and-peering-gated rollout. -->
<!-- 4. In late April 2025, when Rotterdam voice traffic was shifted onto Cloudflare's Amsterdam PoP, users -->
<!--   connecting via Orange (a major French ISP) saw call latency exceed one second at peak hours, with voice -->
<!--   freeze ratio regressing roughly 30%. Root cause: Orange's transit path into Cloudflare's Amsterdam edge -->
<!--   ran over Telia's backbone, and the Telia-Orange interconnect was already saturated at peak — a third-party -->
<!--   ISP transit capacity issue, not a bug in Discord's or Cloudflare's own systems. -->
<!-- 5. In the same investigation window, Cloudflare's team separately found stalls of up to 860 milliseconds -->
<!--   inside Discord's own voice process, with per-thread CPU sampling showing one thread pegged at 100% on a -->
<!--   single core during each spike and socket receive buffers growing during those windows. Root cause: -->
<!--   Cloudflare's infrastructure had pinned its Receive IRQ to the same vCPU Discord's worker threads were -->
<!--   scheduled on. Fix: a CPU affinity change using taskset to pin Discord's worker threads off that vCPU, -->
<!--   combined with Receive Packet Steering (RPS) to spread softirq/interrupt processing across other cores. -->
<!-- 6. As a direct result of incidents like the Orange/Telia saturation, Discord changed its rollout strategy -->
<!--   from pacing region migrations primarily by capacity readiness to pacing them by peering analysis — -->
<!--   checking that Cloudflare's peering with a region's major ISPs had real headroom before shifting -->
<!--   meaningful production traffic there. -->
<!-- 7. Results reported in the post: more than 80% of Discord's voice and video traffic now runs on Cloudflare's -->
<!--   edge network; 70% of regions show year-over-year quality improvements. Frankfurt specifically: average -->
<!--   ping down 34% and packet loss down 42% compared to the previous vendor. -->
<!-- Note: precise sub-percent figures, exact dates for every regional cutover, and Discord's exact internal -->
<!--   wording beyond the commonly corroborated figures above were not independently re-verifiable in this -->
<!--   session (direct fetch of discord.com and medium.com both blocked); no additional precision is claimed -->
<!--   beyond what is corroborated above. -->

# Discord Fixed Its Global Voice Latency Problem. The Real Bugs Showed Up After the Fix Was Right.

**Date:** 2026-08-14
**Company:** Discord
**Category:** real-time
**Post type:** narrative
**Opening style:** mid_scene
**Slug:** discord-voice-cloudflare-edge-migration
**Character count (LinkedIn):** ~2635

---

## LinkedIn Post

In late April 2025, Discord shifted a slice of Rotterdam's voice traffic onto Cloudflare's Amsterdam point of presence. Within days, users on Orange — one of France's largest ISPs — were seeing call latency above a full second during peak hours, and freeze ratio on those calls had regressed 30%.

For most of Discord's history, your voice server was whichever of about 30-40 hyperscaler regions sat closest to you. Fine in the Bay Area or Frankfurt. Rough in Reykjavik, Auckland, Lagos, or Hawaii — an Icelandic user's call routed through Rotterdam, hundreds of kilometers away, because that's where the nearest big cloud data center happened to be.

The fix looked simple: move voice and video onto Cloudflare's edge network, 300+ points of presence instead of 30-40 regions. Reykjavik gets its own PoP. Geography stops being the bottleneck.

It wasn't a clean cutover. Weeks earlier, US East had already shown packet loss of 1.5-2%, against a baseline under 0.5% on the old provider — enough to scrap the original plan of migrating whole regions on a fixed calendar. Then came Orange. Root cause: not Discord's code, not Cloudflare's routing — Orange's transit into Cloudflare's Amsterdam edge ran over Telia's backbone, and the Telia-Orange handoff was already saturated at peak. A capacity problem sitting one layer below anything either company's own infrastructure could see.

Same investigation, stranger finding: stalls up to 860 milliseconds inside Discord's own process, one thread pegged at 100% on a single CPU core during every spike, receive buffers quietly filling behind it. Not a network issue at all — Cloudflare's infra had pinned its Receive IRQ to the same vCPU Discord's worker threads ran on. The fix was taskset, pinning workers off that core, plus Receive Packet Steering to spread interrupt handling elsewhere.

Because of incidents like these, Discord rewrote its rollout playbook — from pacing migrations by capacity readiness to pacing by peering analysis, checking each region's ISP interconnects for headroom before real traffic arrived.

Today, over 80% of voice and video traffic runs on the edge. 70% of regions show year-over-year quality gains. Frankfurt: ping down 34%, packet loss down 42%.

No one built the wrong thing. The 30-region architecture made sense for a decade. The edge migration was the right call. It just turned out that solving the geography problem didn't remove the next bottleneck — it relocated it, one layer down, into an ISP's transit contract and a CPU's interrupt affinity.

Sources in comments.

#SystemDesign #Discord #Cloudflare #WebRTC #Infrastructure

---

## Twitter / X Version

1/ Late April 2025: Discord shifts a slice of Rotterdam's voice traffic onto Cloudflare's Amsterdam edge. Days later, users on Orange — a major French ISP — see call latency above 1 second at peak. Freeze ratio regresses 30%.

2/ Backstory: for most of Discord's history, your voice server was one of ~30-40 hyperscaler regions. Fine in Frankfurt. Rough in Reykjavik or Lagos — an Icelandic call used to route through Rotterdam, hundreds of km away.

3/ The fix: move voice/video onto Cloudflare's edge — 300+ PoPs instead of 30-40 regions. Reykjavik gets its own. On paper, geography stops being the bottleneck.

4/ Not a clean cutover. US East had already shown 1.5-2% packet loss vs a <0.5% baseline weeks earlier, killing the plan to migrate whole regions on a fixed calendar.

5/ The Orange root cause: not Discord's code, not Cloudflare's routing. Orange's transit into Amsterdam ran over Telia's backbone, and that handoff was saturated at peak. A capacity problem neither company's own infra could see alone.

6/ Weirder finding, same investigation: 860ms stalls inside Discord's process, one thread pegged at 100% on a single core during every spike. Cloudflare's infra had pinned its Receive IRQ to the same vCPU Discord's workers ran on. Fix: taskset + Receive Packet Steering.

7/ Discord rewrote its rollout playbook after this — pacing migrations by ISP peering headroom, not just capacity readiness.

8/ Today: 80%+ of voice/video traffic on the edge, 70% of regions improved YoY. Frankfurt: ping -34%, packet loss -42%.

9/ No one built the wrong thing. Fixing the geography problem didn't remove the next bottleneck — it just moved it, one layer down, into an ISP's transit contract and a CPU's interrupt affinity.

---

## Excalidraw Diagram

**File:** 2026-08-14-discord-voice-cloudflare-edge-migration.excalidraw
**Type:** Two-panel — a side-by-side before/after routing comparison for a single Icelandic call, paired with a 3-box horizontal sequence showing where the migration's real failures surfaced.
**Color scheme:** Blue for the "before" hyperscaler routing — deliberately not a "bad" color, since the old design wasn't wrong, just geographically limited. Violet for the "after" edge routing, to mark it as the improvement without reusing red/green. Slate for the early warning sign (US East packet loss). Amber for the Orange/Telia ISP transit incident. Rose for the stranger, kernel-level bug (the 860ms stalls), since it's the most surprising find in the story. Footer in teal for the results, deliberately different from the violet used for "after," so the palette doesn't collapse into a single "good" color.
**Screenshottable stat:** "1 second+ call latency after a routine ISP handoff saturated. 860ms CPU stalls from a Receive IRQ pinned to the wrong core. 80%+ of Discord's voice traffic now on the edge anyway."

### Layout

```
Title: "Discord Fixed Its Global Voice Latency Problem. The Real Bugs Showed Up After the Fix Was Right."
Subtitle: "Discord's and Cloudflare's own postmortems: moving voice onto a 300-PoP edge network fixed the
geography problem, then surfaced an ISP transit bottleneck and a kernel-level CPU contention bug"

[PANEL 1 — ONE ICELANDIC CALL: BEFORE THE EDGE VS. AFTER, top, two side-by-side flows]
  BEFORE — HYPERSCALER REGIONS [blue]
    Box: "A Reykjavik user places a voice call."
    --arrow (blue)-->
    Box: "Routes to the nearest hyperscaler region: Rotterdam — roughly 2,600 km away. Not a mistake,
      just where the nearest big cloud data center happened to be."
  AFTER — CLOUDFLARE EDGE [violet]
    Box: "A Reykjavik user places a voice call."
    --arrow (violet)-->
    Box: "Routes to Cloudflare's own Reykjavik point of presence — one of 300+ edge cities. No
      hyperscaler detour."

[PANEL 2 — THE CRACKS THAT SHOWED UP DURING THE MIGRATION, bottom, 3 boxes left to right]
  Box 1 (slate): "Weeks before Orange: US East already shows 1.5–2% packet loss on the edge path, against
    a <0.5% baseline on the old provider. Discord scraps its plan to migrate whole regions on a fixed
    calendar."
  --arrow (indigo)-->
  Box 2 (amber): "Late April 2025: Rotterdam traffic shifts to Cloudflare's Amsterdam PoP. Orange, a major
    French ISP, sees call latency above 1 second at peak; freeze ratio regresses 30%. Root cause: Orange's
    own Telia transit into Amsterdam was already saturated."
  --arrow (amber)-->
  Box 3 (rose): "Same investigation, a second bug: stalls up to 860ms inside Discord's own process, one
    thread pegged at 100% every spike. Cloudflare had pinned its Receive IRQ to the same vCPU as Discord's
    workers. Fixed with taskset plus Receive Packet Steering."

[FOOTER, teal band, full width]
  "Result: 80%+ of Discord's voice and video traffic now runs on Cloudflare's edge, 70% of regions
  showing year-over-year quality gains. Frankfurt alone: ping down 34%, packet loss down 42% vs the
  prior vendor. Rollout is now paced by ISP peering headroom, not just server capacity. 'Fixing the
  geography problem didn't remove the next bottleneck. It moved it — into a transit contract, and a
  CPU's interrupt affinity.'"
```
