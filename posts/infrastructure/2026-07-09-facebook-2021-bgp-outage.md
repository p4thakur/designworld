<!-- sources -->
<!-- Primary: -->
<!--   Meta Engineering, "More details about the October 4 outage" (Santosh Janardhan, VP of Infrastructure) -->
<!--   URL: https://engineering.fb.com/2021/10/05/networking-traffic/outage-details/ -->
<!--   Meta Engineering, "Update about the October 4th outage" -->
<!--   URL: https://engineering.fb.com/2021/10/04/networking-traffic/outage/ -->
<!-- Note: direct fetch of engineering.fb.com and en.wikipedia.org returned HTTP 403 under this session's egress -->
<!-- policy (bot protection). Facts below were cross-checked across multiple independent search-result excerpts -->
<!-- that quote the primary Meta engineering blog post directly, plus corroborating reporting, including: -->
<!--   https://en.wikipedia.org/wiki/2021_Facebook_outage -->
<!--   https://www.theregister.com/2021/10/06/facebook_outage_explained_in_detail/ -->
<!--   https://www.kentik.com/blog/facebooks-historic-outage-explained/ -->
<!--   https://www.engadget.com/facebook-outage-explainer-193155776.html -->
<!--   https://fortune.com/2021/10/04/facebook-outage-cost-revenue-instagram-whatsapp-not-working-stock/ -->
<!--   https://www.forbes.com/sites/abrambrown/2021/10/05/facebook-outage-lost-revenue/ -->
<!--   https://news.ycombinator.com/item?id=28750894 (discussion thread quoting NYT reporting on badge readers) -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Oct 4, 2021, ~15:39 UTC: a routine maintenance command intended to assess spare backbone capacity instead -->
<!--    withdrew all backbone network connections; a bug in the audit tool meant to catch this didn't stop it -->
<!-- 2. Facebook's authoritative DNS servers disable their own BGP route advertisements if they can't reach the -->
<!--    data center network (a self-health-check design). With the backbone gone, every DNS server declared -->
<!--    itself unhealthy and withdrew its own routes, making DNS unreachable even though servers were fine -->
<!-- 3. Facebook, Instagram, WhatsApp, Messenger, and Oculus were all globally unavailable as a result -->
<!-- 4. Per the primary post, the total loss of DNS also broke many of the internal tools engineers would -->
<!--    normally use to investigate and resolve an outage like this -->
<!-- 5. Per NYT reporting (via an employee quoted by Sheera Frenkel), electronic badge readers on data center -->
<!--    doors ran on the same internal network and failed, delaying physical access for on-site engineers -->
<!-- 6. BGP routes were restored ~21:50 UTC, DNS became available ~22:05 UTC, service was generally restored for -->
<!--    users by ~22:50-23:00 UTC — roughly six to seven hours of global outage -->
<!-- 7. Estimated ~3.5 billion people affected across the app family; revenue-loss estimates range roughly -->
<!--    $60-100 million for the day (Fortune ~$100M, Forbes ~$65M at ~$13M/hour); Meta stock closed down ~4.9% -->

# Facebook Built a Safety Check That Made Its Own Outage Total

**Date:** 2026-07-09
**Company:** Facebook (Meta)
**Category:** infrastructure
**Post type:** narrative
**Opening style:** mid_scene
**Slug:** facebook-2021-bgp-outage
**Character count (LinkedIn):** ~2,489

---

## LinkedIn Post

At 15:39 UTC on October 4, 2021, an engineer at Facebook ran a routine command to check spare capacity on the global backbone network. Ordinary maintenance, protected by an audit tool built for exactly this class of mistake.

The audit tool had a bug. It let the command through. Instead of measuring capacity, the command withdrew every route connecting Facebook's backbone to the internet — instantly, everywhere.

Here's what turned a bad command into a six-hour blackout. Facebook's DNS servers had a safety mechanism: if a server couldn't reach the data center network, it assumed something was wrong and pulled its own BGP advertisements — stopped announcing it existed. Sane design, in isolation. When the backbone vanished, every DNS server correctly diagnosed itself as unhealthy and pulled its own address off the map. Facebook, Instagram, WhatsApp, Messenger, and Oculus didn't go down because servers crashed. They went down because the internet lost the address book, and the address book had been told, correctly, by its own logic, to unlist itself.

Then it got worse. The engineers fixing this found that the tools they'd normally use to diagnose a network outage also depended on that same internal DNS. Their own recovery infrastructure was a casualty of the outage it was supposed to fix.

Worse again: the badge readers on the data center doors ran on the same backbone. Engineers who showed up to work on the hardware directly couldn't get through the doors, and needed physical tools to force their way into server rooms their own credentials could no longer open.

BGP routes came back around 21:50 UTC, DNS around 22:05, full service near 23:00 — six to seven hours, roughly 3.5 billion people affected across the app family, and somewhere between $60-100 million in lost revenue for the day.

Nobody made an obviously bad call. The audit tool existed because someone had already thought about this failure mode. The DNS self-withdrawal existed because someone had thought about network partitions. The badge system was centralized because that was simpler and more secure. Each safeguard was reasonable alone. Stacked together, they turned one bug into a scenario where the people who could fix the internet couldn't get through their own front door.

The tradeoffs don't disappear when you add a safety mechanism. They just move — usually into the one scenario nobody modeled: everything failing at once.

#SystemDesign #BGP #DNS #Infrastructure #Outages

---

## Twitter / X Version

1/ Oct 4, 2021, 15:39 UTC: an engineer runs a routine command to check spare capacity on Facebook's backbone network. Normal maintenance. An audit tool exists specifically to catch a mistake like this.

2/ The audit tool had a bug. It let the command through. Instead of measuring capacity, the command withdrew every backbone route to the internet — everywhere, at once.

3/ Here's the twist: Facebook's DNS servers were built to withdraw their own BGP routes if they couldn't reach the data center network — a safety check. When the backbone disappeared, every DNS server correctly declared itself unhealthy and unlisted itself.

4/ Facebook, Instagram, WhatsApp, Messenger, Oculus — all down. Not because servers crashed. Because the internet's address book had, correctly, taken itself off the map.

5/ Then the recovery tools turned out to depend on that same internal DNS. And the badge readers on the data center doors ran on the same backbone — engineers needed physical tools to force their way into the server rooms.

6/ BGP back ~21:50 UTC. DNS ~22:05. Full service ~23:00. ~6-7 hours down, ~3.5B people affected, an estimated $60-100M in lost revenue.

7/ No single bad decision. Every safeguard made sense alone. Stacked together, they locked the fixers out of the thing they needed to fix — including the front door.

8/ Safety mechanisms don't remove tradeoffs. They relocate them — usually into the one scenario nobody modeled.

---

## Excalidraw Diagram

**File:** 2026-07-09-facebook-2021-bgp-outage.excalidraw
**Type:** Cascading-failure sequence flow (narrative) — five stages stacked top to bottom, each one triggering the next, showing where the failure actually happens (the DNS self-withdrawal box) rather than a generic architecture snapshot.
**Color scheme:** Slate for the routine trigger (a normal, reasonable action), amber for the audit-tool bug (the one earned "something's wrong" color), crimson for the moment the backbone is actually gone (the pivotal failure — used once, not paired with a green "good" box anywhere), indigo for the DNS self-withdrawal design (a deliberate, sane-in-isolation safety mechanism, not villainized), violet and teal for the two knock-on failures (tooling, physical access) to keep them visually distinct from the root cause. No red/green good/bad pairing.
**Screenshottable stat:** "1 bug in 1 audit tool → BGP down ~21:50 UTC, DNS ~22:05 UTC, full service ~23:00 UTC · ~6-7 hrs · ~3.5B people affected · ~$60-100M lost that day"

### Layout

```
Title: "Facebook Built a Safety Check That Made Its Own Outage Total"
Subtitle: "Oct 4, 2021, 15:39 UTC → ~6-7 hrs down → ~3.5B people affected → ~$60-100M lost"

[15:39 UTC — THE TRIGGER]
Routine command to check spare
backbone capacity. Ordinary
maintenance work.
        |
        v
[THE BUG]
Audit tool meant to catch this
class of mistake has a bug.
It lets the command through.
        |
        v
[THE FAILURE — screenshottable]
Every backbone route to the
internet withdrawn, globally,
at once.
        |
        v
[THE IRONY — DNS SELF-WITHDRAWAL]
DNS servers can't reach the data center network → they correctly diagnose themselves as
unhealthy → they withdraw their own BGP advertisements. The address book unlists itself.
Facebook, Instagram, WhatsApp, Messenger, Oculus: all unreachable. No server crashed.
        |
        +--------------------------------+
        v                                v
[KNOCK-ON: TOOLING]              [KNOCK-ON: PHYSICAL ACCESS]
Internal tools used to           Badge readers on datacenter
diagnose/fix outages also        doors run on the same
depend on the same internal      backbone. Engineers need
DNS — the fix tools are down     physical tools to force
too.                              their way into server rooms.

[RECOVERY TIMELINE]
15:39 command run → ~21:50 UTC BGP restored → ~22:05 UTC DNS restored → ~23:00 UTC full service

Footnote: No one made an obviously bad call — every safeguard was reasonable alone.
Stacked together, they locked the fixers out of the thing they needed to fix.
```
