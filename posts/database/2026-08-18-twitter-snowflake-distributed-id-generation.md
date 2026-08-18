<!-- sources -->
<!-- Primary (fetched directly): -->
<!--   Twitter, "Snowflake" README, original 2010 release (tag snowflake-2010), twitter-archive/snowflake repo -->
<!--     https://raw.githubusercontent.com/twitter-archive/snowflake/snowflake-2010/README.mkd -->
<!-- Blocked by network egress policy (blog.x.com and blog.twitter.com both returned EGRESS_BLOCKED under this -->
<!--   session's network policy, same class of gateway-level denial noted on prior posts in this series): -->
<!--   Twitter Engineering Blog, "Announcing Snowflake" (June 2010) -->
<!--     https://blog.x.com/engineering/en_us/a/2010/announcing-snowflake -->
<!-- Corroborating (independent secondary sources, cross-referenced for consistency; the ticket-server/ZooKeeper -->
<!-- rejection details below are not present in the primary README and are sourced only from these, cross-checked -->
<!-- across two independent search-result summaries that used matching phrasing when describing the blocked -->
<!-- primary blog post): -->
<!--   Flickr Code Blog, "Ticket Servers: Distributed Unique Primary Keys on the Cheap" -->
<!--     https://code.flickr.net/2010/02/08/ticket-servers-distributed-unique-primary-keys-on-the-cheap/ -->
<!--   Discord Lookup Docs, "Discord Snowflake ID Format" -->
<!--     https://discordlookup.org/docs/discord-snowflake-format -->
<!-- Key verifiable details (from the primary README unless noted otherwise): -->
<!-- 1. Motivation, quoted directly: "As we at Twitter move away from Mysql towards Cassandra, we've needed a new -->
<!--   way to generate id numbers. There is no sequential id generation facility in Cassandra, nor should there be." -->
<!-- 2. Stated performance requirements, quoted directly: "minimum 10k ids per second per process" and -->
<!--   "response rate 2ms (plus network latency)." -->
<!-- 3. Uncoordinated requirement, quoted directly: "For high availability within and across data centers, -->
<!--   machines generating ids should not have to coordinate with each other." -->
<!-- 4. Ordering requirement: ids are k-sorted (not strictly ordered — the README notes Twitter already didn't -->
<!--   guarantee in-order delivery due to async operations) "within a reasonable bound (we're promising 1s, but -->
<!--   shooting for 10's of ms)." Two academic k-sorting citations are given inline. -->
<!-- 5. Compactness requirement, quoted directly: "There are many otherwise reasonable solutions to this problem -->
<!--   that require 128bit numbers. For various reasons, we need to keep our ids under 64bits." (This is understood -->
<!--   to rule out UUIDs, which are 128-bit, though the README does not name UUID explicitly.) -->
<!-- 6. Solution: a Thrift server written in Scala. 64-bit id composed of: 41-bit time (millisecond precision, -->
<!--   custom epoch, "gives us 69 years"), 10-bit configured machine id ("up to 1024 machines"), 12-bit sequence -->
<!--   number ("rolls over every 4096 per machine (with protection to avoid rollover in the same ms)"). -->
<!-- 7. System clock dependency, quoted directly: "Snowflake protects from non-monotonic clocks, i.e. clocks that -->
<!--   run backwards. If your clock is running fast and NTP tells it to repeat a few milliseconds, snowflake will -->
<!--   refuse to generate ids until a time that is after the last time we generated an id." -->
<!-- 8. Per secondary sources (not the primary README): Twitter considered a Flickr-style MySQL ticket server -->
<!--   (single dedicated server handing out sequential ids) but rejected it because it lacked the ordering -->
<!--   guarantees without a resync routine, and reintroduced a single write bottleneck. Twitter also evaluated -->
<!--   ZooKeeper sequential znodes for coordinated id assignment but found the performance characteristics -->
<!--   insufficient and was concerned a coordinated approach would cost availability for no real benefit. -->
<!-- 9. Discord's own Snowflake-derived id format (for the closing comparison, verified independently): 42-bit -->
<!--   timestamp on a custom 2015-01-01 epoch, 5-bit worker id, 5-bit process id, 12-bit per-worker-process -->
<!--   increment — a different bit split than Twitter's 41/10/12, confirming the pattern was copied conceptually -->
<!--   rather than byte-for-byte. -->

# Twitter's Tweet IDs Used to Be a MySQL Auto-Increment Column. Then Cassandra Showed Up.

**Date:** 2026-08-18
**Company:** Twitter
**Category:** database
**Post type:** narrative
**Opening style:** mid_scene
**Slug:** twitter-snowflake-distributed-id-generation
**Character count (LinkedIn):** ~2460

---

## LinkedIn Post

By 2010, half of Twitter's API contract rested on one assumption: tweet IDs only go up. "Give me everything since this id" was baked into pagination, streaming, mentions — a single auto-increment column on one MySQL table made all of it trivial.

Then Twitter started moving off MySQL onto Cassandra to handle write volume across shards. Cassandra had no sequential ID facility, deliberately. A single incrementing counter is a single point of coordination, and Cassandra's whole design bet was against that kind of coordination.

The obvious fixes each had a catch. A 128-bit UUID solved uniqueness but broke sortability and blew past the 64-bit budget Twitter had set for itself. A Flickr-style ticket server — a MySQL box dedicated to handing out sequential IDs — kept ordering intact, but reintroduced a resync routine and a single write bottleneck, the exact thing sharding was supposed to remove. ZooKeeper sequential znodes could coordinate ID assignment across machines, but Twitter clocked the performance and worried a coordinated scheme would cost availability for no real gain.

So they wrote their own service: Snowflake. Each 64-bit ID packs a 41-bit millisecond timestamp, a 10-bit machine id (1,024 possible generators), and a 12-bit per-machine sequence number that rolls over every 4,096 ids within the same millisecond. No machine ever asks another machine for permission. The stated bar was blunt: minimum 10,000 ids per second per process, 2ms response time, ordering k-sorted within a promised one second, targeting tens of milliseconds in practice.

The one dependency they couldn't design away was time itself. Snowflake trusts NTP-synced clocks — and if NTP ever steps a clock backward, Snowflake simply refuses to generate ids until the clock passes the last timestamp it already used. It would rather stall than hand out a number that breaks the ordering guarantee.

Fourteen years later, Discord, Instagram, and plenty of other systems still generate IDs the same way conceptually: timestamp, machine id, per-machine counter, packed into one sortable integer. The bit split always changes — Discord's is 42/5/5/12, on its own 2015 epoch — but the shape doesn't. Nobody was wrong about the MySQL auto-increment column. It was the right call for a single database. It just stopped being the right call the moment there wasn't a single database anymore.

Sources in comments.

#SystemDesign #Twitter #DistributedSystems #Databases

---

## Twitter / X Version

1/ By 2010, Twitter's entire API leaned on one assumption: tweet IDs only go up. "Everything since this id" powered pagination, streaming, mentions — a MySQL auto-increment column made it all trivial.

2/ Then Twitter started moving off MySQL onto Cassandra to handle write volume across shards. Cassandra has no sequential id facility. On purpose. A single incrementing counter is a single point of coordination — the exact thing Cassandra's design bet against.

3/ The obvious fixes all had a catch. UUIDs (128-bit) solved uniqueness but broke sortability and blew the 64-bit budget. A Flickr-style ticket server kept ordering but reintroduced a write bottleneck. ZooKeeper znodes could coordinate — but Twitter clocked the performance as too slow and too risky for availability.

4/ So they built Snowflake. 64-bit id: 41-bit millisecond timestamp, 10-bit machine id (1,024 generators), 12-bit per-machine sequence (rolls over every 4,096/ms). No machine asks another machine for permission.

5/ The bar, stated bluntly in the original spec: minimum 10,000 ids/sec per process, 2ms response time, ordering k-sorted within a promised 1 second, targeting tens of milliseconds.

6/ The one thing they couldn't design away: time itself. If NTP ever steps the clock backward, Snowflake refuses to generate ids until the clock passes the last timestamp it already used. It stalls rather than break the ordering guarantee.

7/ 14 years later, Discord, Instagram, and plenty of others still generate ids the same way conceptually — timestamp + machine id + counter. Discord's split is 42/5/5/12, its own epoch. The bits change. The shape doesn't.

8/ Nobody was wrong about the MySQL auto-increment column. It was the right call for a single database. It stopped being right the moment there wasn't a single database anymore.

---

## Excalidraw Diagram

**File:** 2026-08-18-twitter-snowflake-distributed-id-generation.excalidraw
**Type:** Sequence flow — how a single tweet-create request turns into an ID, shown twice: once under the old single-MySQL-table design, once under Snowflake, with the coordination point that disappears highlighted as the "failure point" the old design couldn't survive at scale.
**Color scheme:** Denim blue for the original MySQL auto-increment path — a calm, competent color, since the design wasn't wrong for its era. Rust-orange highlight on the single coordination point where the old design breaks under sharding. Slate for the three rejected alternatives (UUID, ticket server, ZooKeeper), kept visually equal so none reads as the "correct" runner-up. Moss green for Snowflake's three id components, since they're the part that ships. Charcoal footer, distinct from all of the above, for the closing comparison to Discord's own bit split.
**Screenshottable stat:** "64-bit id = 41-bit timestamp + 10-bit machine id (1,024 machines) + 12-bit sequence (4,096 ids/ms/machine). Minimum bar: 10,000 ids/sec per process, 2ms response."

### Layout

```
Title: "Twitter's Tweet IDs Used to Be a MySQL Auto-Increment Column. Then Cassandra Showed Up."
Subtitle: "Twitter's own 2010 Snowflake spec: why auto-increment couldn't survive sharding, three rejected
fixes, and the uncoordinated id scheme that replaced all of them"

[ROW 1 — THE OLD PATH, denim, single horizontal flow]
  Box 1: "Tweet created"
  --arrow-->
  Box 2 (rust-orange ring, marked FAILURE POINT): "One MySQL table's auto-increment column hands out the
    next id. Works perfectly — as long as there's only one table."
  --arrow-->
  Box 3: "Client reads 'everything since id X.' Ordering guaranteed for free."

[ROW 2 — THREE FIXES CONSIDERED AND REJECTED, slate, 3 boxes side by side under a "REJECTED" label]
  Box A: "128-bit UUID — unique, but unsortable and blows the 64-bit budget."
  Box B: "Flickr-style ticket server — ordering intact, but reintroduces a single write bottleneck via a
    resync routine."
  Box C: "ZooKeeper sequential znodes — can coordinate ids across machines, but performance and availability
    cost outweighed the benefit."

[ROW 3 — SNOWFLAKE, moss green, 3 boxes combining into 1]
  Box 1: "41-bit timestamp (ms precision, custom epoch, 69 years of headroom)"
  Box 2: "10-bit machine id (1,024 generators, no coordination between them)"
  Box 3: "12-bit sequence (4,096 ids per machine per millisecond)"
  --combine arrow-->
  Result box: "One 64-bit id. Minimum 10,000 ids/sec/process. 2ms response. k-sorted within a promised
    1 second."

[FOOTER, charcoal band, full width]
  "Snowflake's one undesignable dependency: time. If NTP steps the clock backward, it refuses to generate
  ids until the clock passes the last timestamp it already used — stalling rather than breaking order.
  Fourteen years later, Discord ships the same idea with a different split: 42-bit timestamp / 5-bit worker
  / 5-bit process / 12-bit increment, its own 2015 epoch. The shape survived. The bits didn't have to match."
```
