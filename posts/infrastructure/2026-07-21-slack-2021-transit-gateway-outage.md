<!-- sources -->
<!-- Primary: Slack Engineering, "Slack's Outage on January 4th 2021," slack.engineering, Feb 2021. -->
<!--   URL: https://slack.engineering/slacks-outage-on-january-4th-2021/ -->
<!-- Secondary analysis: "Slack's Jan 2021 outage: a tale of saturation," Surfing Complexity, Feb 8 2021. -->
<!--   URL: https://surfingcomplexity.blog/2021/02/08/slacks-jan-2021-outage-a-tale-of-saturation/ -->
<!-- Secondary: The Register, "Slack fingers AWS auto-scaling failure in January outage postmortem," Feb 2 2021. -->
<!--   URL: https://www.theregister.com/2021/02/02/slack_outage_aws_autoscaling/ -->
<!-- Secondary: TechTarget, "Massive Slack outage caused by AWS gateway failure." -->
<!--   URL: https://www.techtarget.com/searchunifiedcommunications/news/252495267/Massive-Slack-outage-caused-by-AWS-gateway-failure -->
<!-- Note: direct WebFetch of slack.engineering and surfingcomplexity.blog returned HTTP 403 under this -->
<!--   session's egress policy (the same session-wide WebFetch outage noted in the 2026-07-18 Etsy post). -->
<!--   Facts below are cross-checked across multiple independent WebSearch result excerpts that quote or -->
<!--   closely paraphrase the primary Slack engineering post, corroborated by two independent secondary -->
<!--   writeups (The Register, TechTarget) that each independently repeat the 1,200-server figure, the -->
<!--   7:01-7:15am PST provisioning window, and the CPU/thread-utilization autoscaling signal conflict. -->
<!-- Key verifiable details (via search excerpts of the primary post and corroborating secondary sources): -->
<!-- 1. At 6:57am PST, Slack's message-send success rate was ~99%, against a normal baseline above 99.999% -->
<!--    -- roughly a thousand-fold jump in the failure rate. -->
<!-- 2. Root cause: one of Slack's AWS Transit Gateways (the hub routing traffic between Slack's VPCs) did -->
<!--    not scale its forwarding capacity fast enough for a traffic spike, causing packet loss between -->
<!--    backend servers. The spike was driven by Slack's unusual annual pattern: quiet holiday traffic, -->
<!--    then everyone reconnecting the same morning with cold local caches, so first-connection clients -->
<!--    pulled a full resync instead of a small incremental delta. -->
<!-- 3. Slack's web tier autoscaled on two signals: CPU utilization and Apache worker-thread utilization. -->
<!--    Network packet loss made request threads spend more time blocked waiting on the network stack -->
<!--    (retransmits), which lowered measured CPU utilization even as the service was saturated -- so the -->
<!--    autoscaler initially read the incident as spare capacity and scaled the web tier DOWN, before the -->
<!--    thread-utilization signal caught up and triggered a sharp scale-up. -->
<!-- 4. Between 7:01am and 7:15am PST, Slack attempted to add 1,200 servers to the web tier at once. That -->
<!--    provisioning burst pushed provision-service into two resource bottlenecks -- primarily a Linux -->
<!--    open-file-descriptor limit, secondarily an AWS API quota. -->
<!-- 5. Slack's own dashboarding/alerting tooling also became unavailable during the incident, complicating -->
<!--    the response. Around 8:15am PST, provision-service recovered and healthy instances began entering -->
<!--    service. -->
<!-- 6. Fix: Slack's postmortem states AWS increased the capacity of the cross-boundary network traffic -->
<!--    systems involved and moved Slack from a shared Transit Gateway to a dedicated one. -->
<!-- 7. NOT independently verified with hard numbers via this session's search: exact per-attachment -->
<!--    Transit Gateway bandwidth/Gbps limits in effect at the time, and a minute-precise total outage -->
<!--    duration (secondary sources describe "nearly five hours" end-to-end with roughly 90 minutes of the -->
<!--    service being fully unusable; that range is reported as-is, not asserted to the minute). -->
<!-- Mechanism-level explanation of *why* CPU utilization inverts as a load signal under network I/O wait, -->
<!-- and why a hub-and-spoke gateway concentrates load that direct peering would have spread out, is -->
<!-- standard distributed-systems/networking internals knowledge, used here to go one level deeper than the -->
<!-- blog posts themselves, per the skill's sourcing guidance. -->

# Slack's January 4th 2021 Outage: When the Autoscaler Read the Wrong Number

**Date:** 2026-07-21
**Company:** Slack
**Category:** infrastructure
**Post type:** narrative
**Opening style:** mid_scene
**Slug:** slack-2021-transit-gateway-outage
**Character count (LinkedIn):** ~2,500

---

## LinkedIn Post

6:57am PST, January 4th, 2021. Slack's message-send success rate reads 99%. That sounds fine — until you know Slack's normal baseline is above 99.999%. That's roughly a thousand-fold jump in failures, and the incident is just getting started.

Two quiet holiday weeks had just ended. Everyone logged back in within the same few hours, with cold local caches, so instead of pulling small deltas, every client pulled a full resync. Cross-VPC traffic through Slack's AWS Transit Gateway — the hub that routes packets between all of Slack's VPCs — spiked far past a normal Monday, faster than the gateway's own control plane could provision more forwarding capacity for that attachment. Packets queued, then dropped.

Packet loss meant TCP retransmits, and retransmits meant application threads sitting blocked on the network stack, waiting to hear back — not computing, just waiting. Slack's web tier autoscaled partly on CPU utilization. CPU utilization measures how busy the processor is, not how busy the service is, and those are the same thing only when compute is what's actually saturated. Here it wasn't. The worse the network got, the more idle the fleet looked to the one number partly driving scaling decisions.

So the autoscaler did the opposite of what the incident needed: it read low CPU as spare capacity and scaled the web tier down, in the middle of the degradation.

Within minutes, the fleet's other signal — Apache worker-thread utilization — caught up and overcorrected hard. Between 7:01 and 7:15am PST, Slack tried to add 1,200 servers at once. And the rescue broke too: provisioning that many instances in that tight a window ran provision-service straight into a Linux open-file-descriptor limit nobody had sized for a burst that size, because ordinary autoscaling events are smaller and slower. Slack was effectively unusable for roughly ninety minutes.

No single decision here was wrong on its own terms. Autoscaling on CPU is standard practice. A hub-and-spoke gateway is how you avoid an N² mesh of VPC peering connections. Each piece did exactly what it was built to do. They just hadn't been tested against each other, under a traffic shape that only happens once a year, at a rate none of them had absorbed together before.

Afterward, AWS moved Slack off a shared Transit Gateway onto a dedicated one and grew its cross-boundary capacity. The bottleneck didn't disappear. It stopped being shared with anyone else's bad Monday.

#SystemDesign #AWS #SRE #DistributedSystems

---

## Twitter / X Version

6:57am PST, Jan 4 2021: Slack's message success rate reads 99%. Normal is >99.999%. That's a ~1000x jump in failures — and it's the beginning, not the peak.

Everyone came back from holiday at once, cold caches, full resyncs instead of deltas. Traffic through Slack's AWS Transit Gateway spiked faster than the gateway could provision forwarding capacity. Packets queued, then dropped.

Packet loss → TCP retransmits → threads blocked waiting on the network, not the CPU. Slack's autoscaler partly watched CPU utilization. Under network wait, CPU looks idle even when the service is drowning. The autoscaler read that as spare capacity and scaled the web tier DOWN, mid-incident.

Minutes later the other signal — Apache thread utilization — caught up and overcorrected: 1,200 servers requested in a 15-minute window. The rescue broke too — provisioning hit a Linux open-file-descriptor limit nobody had tested at that burst size.

~90 minutes fully down. Nothing here was individually wrong — CPU-based autoscaling and hub-and-spoke gateways are both standard. They just hadn't been tested against each other, at that shape of traffic, at the same time.

Fix: AWS moved Slack to a dedicated Transit Gateway instead of a shared one. The bottleneck didn't disappear. It stopped being shared.

---

## Excalidraw Diagram

**File:** 2026-07-21-slack-2021-transit-gateway-outage.excalidraw
**Type:** Causal sequence, two rows (narrative style) — row one is the cascade from cold-cache traffic spike to a mid-incident downscale, row two is the overcorrection, the second failure inside the rescue mechanism, the recovery, and the fix. A wide indigo box spells out the mechanism match (why CPU utilization inverted as a signal), and a footer names what didn't disappear.
**Color scheme:** Slate for the calm starting state, amber for the warning stage, red for the two actual mistakes (the downscale and the file-descriptor exhaustion), teal for recovery, green for the fix. No single villain box — every piece (CPU autoscaling, the hub gateway) was standard practice that simply hadn't been tested against the others at this traffic shape.
**Screenshottable stat:** "99% success rate at 6:57am PST (normal: >99.999%) · 1,200 servers requested in 15 minutes · ~90 min fully down"

### Layout

```
Title: "Slack's January 4th 2021 Outage: When the Autoscaler Read the Wrong Number"
Subtitle: "99% success rate at 6:57am PST (normal: >99.999%) · 1,200 servers requested in 15 min · ~90 min fully down"

ROW 1 — THE CASCADE: HOW A COLD-CACHE MORNING BECAME A NETWORK OUTAGE
[THE RECONNECT STORM]      →   [THE SATURATION]           →   [THE WRONG SIGNAL]         →   [THE DOWNSCALE]
Two quiet holiday weeks        Traffic outruns how fast        Packet loss → TCP               Before 7:00am PST, the
end at once. Cold client       the Transit Gateway's           retransmits → threads           autoscaler reads low CPU
caches mean full resyncs,      control plane can provision     blocked waiting on the           as spare capacity and
not deltas. Cross-VPC          more forwarding capacity        network, not computing.          scales the web tier DOWN
traffic through Slack's        for the attachment. Packets     CPU utilization reads low        — removing capacity in
shared AWS Transit Gateway     queue, then drop, between        right when the service is        the middle of the
spikes past a normal Monday.   backend servers.                 most saturated.                  degradation.

ROW 2 — THE OVERCORRECTION, THE SECOND FAILURE, AND THE FIX
[THE OVERCORRECTION]       →   [THE SECOND FAILURE]       →   [THE RECOVERY]             →   [THE FIX]
Apache worker-thread            Provisioning 1,200               ~90 minutes fully                Afterward, AWS moves
utilization — the other         instances in a 15-minute         unusable, roughly 7:00-           Slack off a shared
autoscaling signal — catches    window drives provision-         8:30am PST. Around                Transit Gateway onto a
up and spikes. 7:01-7:15am      service into a Linux open-       8:15am PST provision-             dedicated one, and
PST: Slack tries to add         file-descriptor limit            service recovers and              grows cross-boundary
1,200 servers at once.          nobody had sized for a           healthy instances start           capacity for that
                                 burst that size.                 entering service.                 attachment.

[THE MECHANISM MATCH]
CPU utilization is a fine proxy for load only when compute is what's actually saturated. Here the bottleneck was network
bandwidth through a shared hub — so the worse the network got, the more idle the fleet looked to the one signal partly
driving scaling decisions. Autoscaling didn't fail by being slow. It failed by measuring the wrong resource, then
overcorrecting straight into a second, un-load-tested limit inside its own rescue mechanism.

Footer: No single piece was wrong on its own terms — CPU-based autoscaling and a hub-and-spoke gateway are both standard
practice. They just hadn't been tested against each other, at that shape of traffic, at the same time. The bottleneck
didn't disappear afterward. It stopped being shared with anyone else's bad Monday.
```
