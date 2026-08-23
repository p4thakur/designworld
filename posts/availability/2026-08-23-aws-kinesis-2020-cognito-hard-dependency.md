<!-- sources -->
<!-- Primary: -->
<!--   AWS, "Summary of the Amazon Kinesis Event in the Northern Virginia (US-EAST-1) Region" (Nov 25, 2020) -->
<!--   — https://aws.amazon.com/message/11201/ — AWS's own post-incident summary. Direct WebFetch of -->
<!--   aws.amazon.com returned EGRESS_BLOCKED under this session's network policy (as did every other domain -->
<!--   tried directly: byu-se.github.io, notes.nicolevanderhoeven.com, news.ycombinator.com), so the facts below -->
<!--   were verified across multiple independent web-search-result excerpts that directly quote or closely -->
<!--   paraphrase the AWS summary's own language, not written from memory. -->
<!-- Corroborating (independent secondary sources, cross-referenced for consistency): -->
<!--   Jack Shirazi, "What Reliability Engineers can learn from Amazon's November 2020 Kinesis Outage," Medium -->
<!--   — https://jackshirazi.medium.com/what-reliability-engineers-can-learn-from-amazons-november-2020-kinesis-outage-32edbb34d475 -->
<!--   Arpio, "Outage Tales: The Thanksgiving Kinesis Outage of 2020" — https://arpio.io/outage-tales-17-hour-aws-kinesis-outage/ -->
<!--   GeekWire, "Amazon details cause of AWS outage that hobbled thousands of online sites and services" -->
<!--   — https://www.geekwire.com/2020/amazon-details-cause-aws-cloud-outage-hobbled-thousands-online-sites-services/ -->
<!-- Key verifiable details: -->
<!-- 1. The trigger was a relatively small capacity addition to the Kinesis front-end server fleet in us-east-1, -->
<!--   begun at 2:44 AM PST and completed by 3:47 AM PST on Nov 25, 2020. -->
<!-- 2. Kinesis front-end servers maintain a full-mesh: each opens one OS thread per peer server to build an -->
<!--   in-memory shard-map cache. Adding servers increased the thread count required per server past the -->
<!--   operating system's configured thread limit, causing cache-building to fail on affected servers. -->
<!-- 3. Customer-visible impact (elevated error rates/latency) began around 6:36 AM PST; by 7:30 AM PST the -->
<!--   disruption had spread to CloudWatch, Cognito, EventBridge, IoT Core, and other services whose internal -->
<!--   pipelines write to Kinesis for buffering/telemetry, not services that call Kinesis directly by design. -->
<!-- 4. Cognito was not architecturally supposed to depend on Kinesis to operate — it used Kinesis only for -->
<!--   best-effort usage/add-on reporting. AWS's own summary described this as an "unrealized hard dependency": -->
<!--   the reporting call sat synchronously in Cognito's request path, so a stalled write to Kinesis stalled -->
<!--   the login request behind it. -->
<!-- 5. CloudWatch's own pipeline is downstream of Kinesis, so CloudWatch degraded alongside the services it -->
<!--   would normally be used to diagnose. Updates to the public AWS Service Health Dashboard also failed at -->
<!--   first because that update path ran through Cognito; a manual backup process existed but was slow because -->
<!--   support staff were not well-practiced with it. -->
<!-- 6. Recovery was gated by cold-cache rebuild time: each front-end server needed up to about an hour to -->
<!--   rebuild its membership/shard-map cache from scratch, and restarting too many servers simultaneously risked -->
<!--   overwhelming the metadata store again — so AWS restored capacity gradually, throttled, over the course of -->
<!--   roughly 17 hours total before full recovery. -->
<!-- 7. AWS's post-incident response included cellularizing the Kinesis front-end fleet to limit blast radius from -->
<!--   a single capacity change, and auditing other services for similar unrealized hard dependencies on Kinesis. -->
<!-- Publication: AWS Post-Event Summaries, aws.amazon.com/message/11201/, published shortly after Nov 25, 2020. -->

# The "Best-Effort" Call That Took Down AWS Authentication for 17 Hours

**Date:** 2026-08-23
**Company:** AWS
**Category:** availability
**Post type:** confessional
**Opening style:** the_decision
**Slug:** aws-kinesis-2020-cognito-hard-dependency
**Character count (LinkedIn):** 2464

---

## LinkedIn Post

Amazon Cognito's write to Kinesis was labeled best-effort. It shipped usage data — nothing that should ever sit between a user and a successful login. AWS's own post-incident summary later admitted otherwise: it had become a hard dependency nobody had realized existed.

On November 25, 2020, someone on the Kinesis team added a modest amount of capacity to the service's front-end fleet in us-east-1, starting at 2:44 AM PST and finishing about an hour later. Kinesis's front-end servers hold a full-mesh membership: every server opens one OS thread per peer to build its shard-map cache. More servers in the fleet means more threads per server. The new capacity pushed several servers past the operating system's thread limit, and cache construction started failing.

By 6:36 AM, error rates were climbing. By 7:30 AM, the failure had spread well past Kinesis itself — CloudWatch, Cognito, EventBridge, IoT Core, all degraded. Not because they call Kinesis directly in any obvious way, but because their internal pipelines write to it for buffering and telemetry.

That's where Cognito's "best-effort" label stopped meaning anything. The reporting call sat in the request path, synchronously. When Kinesis stalled, so did the write — and so did the login behind it. Nobody had marked it critical, so nobody had built it to fail safely.

The irony compounded: CloudWatch is itself downstream of Kinesis, so the tool engineers would normally use to diagnose the outage was part of the outage. Updates to AWS's own status page ran through Cognito too — the same service that was down — and the manual fallback process existed but hadn't been rehearsed recently enough for anyone to move fast with it.

Fixing the thread bug was fast. Recovering wasn't — each front-end server needs up to an hour to rebuild its membership cache from cold, and restarting too many at once would have overloaded the metadata store all over again. They brought the fleet back node by node. Full recovery took roughly 17 hours.

Afterward, AWS said it would break the front-end fleet into smaller, isolated cells, and go looking for every other "best-effort" call across their services quietly sitting on a critical path.

"Best-effort" is a label a team puts on a call. It isn't a property the runtime enforces. The dependency graph doesn't know what you called something — only what happens when it doesn't come back in time.

#SystemDesign #AWS #DistributedSystems #SRE

---

## Twitter / X Version

1/ Amazon Cognito's write to Kinesis was labeled best-effort — just usage logging, nothing that should block a login. AWS's own post-incident summary called it something else: an unrealized hard dependency.

2/ Nov 25, 2020: a small capacity add to Kinesis's front-end fleet in us-east-1 pushed several servers past the OS thread limit (each server holds one thread per peer in a full mesh). Cache building started failing.

3/ The blast radius: CloudWatch, Cognito, EventBridge, IoT Core — not because they call Kinesis obviously, but because their internal pipelines write to it. Cognito's synchronous reporting call sat in the login path. When it stalled, so did auth.

4/ CloudWatch is downstream of Kinesis too, so the tool you'd use to diagnose the outage was part of the outage. The status page update process ran through Cognito. The manual fallback existed — nobody had used it recently enough to move fast.

5/ Recovery: each front-end node needs up to an hour to rebuild its membership cache cold, and restarting too many at once would've overloaded the metadata store again. Brought back node by node. ~17 hours total.

6/ "Best-effort" is a label a team puts on a call. The dependency graph doesn't know what you called it — only what breaks when it doesn't return in time.

---

## Excalidraw Diagram

**File:** 2026-08-23-aws-kinesis-2020-cognito-hard-dependency.excalidraw
**Type:** Horizontal timeline with a hidden-dependency callout and a reflection footer — matching the
confessional post type's recommended layout (evolution over hours, focused on the human/labeling cause
rather than pure architecture boxes).
**Color scheme:** Blue for the routine timeline stages (this wasn't a malicious or careless act — a capacity
add is a normal Tuesday), amber for the "best-effort" callout (a label, not a failure, until it wasn't), red
reserved only for the actual blast-radius band, and violet for the reflection footer — a fresh palette versus
the slate/amber/red/teal set used on the prior post, and deliberately not a straight red=bad/green=good story.
**Screenshottable stat:** "One 63-minute capacity add. 17 hours to fully recover."

### Layout

```
Title: "The 'Best-Effort' Call That Took Down AWS Authentication for 17 Hours"
Subtitle: "AWS's own Nov 25, 2020 post-incident summary — how a label, not a bug, decided the blast radius"
Stat callout (blue): "One 63-minute capacity add to a front-end fleet. 17 hours to fully recover."

[Horizontal timeline, 4 stages, blue nodes connected left to right]
2:44–3:47 AM PST        6:36 AM PST              7:30 AM PST                 ~17 HRS LATER
Capacity added to   →   Thread limit exceeded, →  Cascade: CloudWatch,   →   Full recovery — fleet
Kinesis front-end        cache-build fails,        Cognito, EventBridge,      restored node by node,
fleet, us-east-1          error rates climb          IoT Core all degraded     cold-cache rebuild throttled

[CALLOUT BAND, amber, full width]
"Cognito's write to Kinesis was labeled best-effort usage reporting — but it ran synchronously in the login
path. AWS's own summary called it an 'unrealized hard dependency.' Nobody marked it critical, so nobody
built it to fail safely."

        v (center arrow)

[BLAST RADIUS BAND, red, full width]
"CloudWatch — the tool used to diagnose outages — is itself downstream of Kinesis. The AWS status page
update process also ran through Cognito. The manual fallback existed; nobody had rehearsed it enough to
move fast."

        v (center arrow)

[FOOTER, violet band, full width]
"THE REFLECTION — 'Best-effort' is a label a team puts on a call. It isn't a property the runtime enforces.
The dependency graph doesn't know what you called something — only what happens when it doesn't come back
in time."
```
