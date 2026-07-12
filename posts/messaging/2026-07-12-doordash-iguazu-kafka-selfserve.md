<!-- sources -->
<!-- Primary: -->
<!--   DoorDash Engineering Blog, "Building Scalable Real Time Event Processing with Kafka and Flink" -->
<!--   URL: https://careersatdoordash.com/blog/building-scalable-real-time-event-processing-with-kafka-and-flink/ -->
<!--   DoorDash Engineering Blog, "API-First Approach to Kafka Topic Creation" -->
<!--   URL: https://careersatdoordash.com/blog/api-first-approach-to-kafka-topic-creation/ -->
<!--   DoorDash Engineering Blog, "DoorDash Empowers Engineers with Kafka Self-Serve" -->
<!--   URL: https://careersatdoordash.com/blog/doordash-engineers-with-kafka-self-serve/ -->
<!-- Note: direct fetch of careersatdoordash.com returned HTTP 403 under this session's egress policy (same -->
<!-- class of restriction hit on the Backblaze post — gateway-level denial, not a per-page block). Facts below -->
<!-- were cross-checked across multiple independent search-result excerpts that quote the primary DoorDash blog -->
<!-- posts directly, plus a corroborating conference talk covering the same system by the same team: -->
<!--   InfoQ / QCon SF 2022, "From Zero to a Hundred Billion: Building Scalable Real-Time Event Processing at -->
<!--   DoorDash" (Allen Wang) — https://www.infoq.com/presentations/doordash-event-system/ -->
<!--   Factor House, "How DoorDash uses Apache Kafka in production" — https://factorhouse.io/articles/doordash-kafka-architecture -->
<!--   Kai Waehner, "Why DoorDash Migrated From Cloud-Native Amazon SQS and Kinesis to Apache Kafka and Flink" -->
<!--   URL: https://www.kai-waehner.de/blog/2022/08/18/why-doordash-migrated-from-cloud-native-amazon-sqs-and-kinesis-to-apache-kafka-and-flink/ -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. Pre-Iguazu, DoorDash ran separate one-off pipelines per event type (built on Amazon SQS and Kinesis, -->
<!--    among others), each with multiple hops and no unified observability. End-to-end latency into Snowflake -->
<!--    could run up to a full day. -->
<!-- 2. Iguazu: producers (microservices + mobile clients) publish via an HTTP-based Kafka REST proxy that -->
<!--    DoorDash extended from Confluent's open-source proxy with multi-cluster routing and async producing. -->
<!--    Apache Flink jobs consume each topic and fan out per destination — Snowflake via S3 Parquet + Snowpipe, -->
<!--    Redis, and Chronosphere (metrics) — with schemas defined in Protobuf in a shared repo, validated at CI. -->
<!-- 3. Result: latency to Snowflake fell from up to a day to a few minutes, at a sustained scale of hundreds of -->
<!--    billions of events per day, with 99.99% delivery reliability. -->
<!-- 4. Separately, and after Iguazu existed: onboarding a brand-new event source was still gated on Kafka topic -->
<!--    creation, guaranteed within two business days (~48 hours). The slowest step was a GitOps chain — an -->
<!--    orchestrator opened a GitHub PR against the Kafka-topics repo, Atlantis ran `terraform plan`, and an -->
<!--    on-call engineer had to notice an automated email and manually approve/merge the PR before Atlantis ran -->
<!--    `terraform apply`. During product launches, the volume of new-topic PRs could exceed 20/hour; on-call -->
<!--    sometimes missed the email notification entirely, causing the request to time out. -->
<!-- 5. DoorDash replaced that manual-approval chain with an in-house, API-first self-service provisioning -->
<!--    system (no PR, no email, no manual click). Result: onboarding time fell ~95%, from the ~48-hour -->
<!--    guarantee to under an hour (often ~15 minutes). Manual on-call intervention dropped by roughly 4 -->
<!--    hours/week. The system now self-serves on the order of 100 new Kafka topics a week without manual -->
<!--    approval. (DoorDash's later, separate 2024 "Kafka Self-Serve" post reports a related but distinct -->
<!--    figure — 12 hours to under 5 minutes for full resource creation — for a broader self-serve platform; -->
<!--    that later system is not the one quoted in the numbers above, which are specific to the 2022 API-first -->
<!--    topic-creation post.) -->

# DoorDash's Event Platform Moves Hundreds of Billions of Events a Day. Its Bottleneck Was a GitHub Pull Request.

**Date:** 2026-07-12
**Company:** DoorDash
**Category:** messaging
**Post type:** structured
**Opening style:** cold_fact
**Slug:** doordash-iguazu-kafka-selfserve
**Character count (LinkedIn):** ~2,640

---

## LinkedIn Post

DoorDash's event platform moves hundreds of billions of events a day into Snowflake at 99.99% reliability, with latency down to minutes. For years, the actual bottleneck in that system wasn't Kafka throughput. It was an on-call engineer's inbox.

Before this platform — DoorDash calls it Iguazu — event data moved through a pile of one-off pipelines, one per event type, built on Amazon SQS and Kinesis, each with its own hops and no shared observability. Getting a single event from a service into Snowflake, DoorDash's data warehouse, could take up to a full day. That's too slow for anything that needs same-day numbers: fraud checks, pricing, logistics.

The fix was consolidation, not more pipelines. Microservices and mobile clients now publish through one HTTP-based Kafka proxy, which DoorDash extended from Confluent's open-source version with multi-cluster routing and async producing. Apache Flink jobs read each topic and fan out to wherever it needs to go — Snowflake via S3 Parquet files picked up by Snowpipe, Redis, their metrics store Chronosphere — with schemas defined in Protobuf and validated in CI, so a malformed field never makes it downstream. Latency to Snowflake dropped from a day to a few minutes, at a scale of hundreds of billions of events daily.

Here's the part that doesn't make the architecture diagrams: even after all that, onboarding a new event source still took up to two business days. Not because Kafka couldn't handle another topic — because creating one meant opening a GitHub pull request against DoorDash's Kafka-topics repo, having Atlantis run a Terraform plan, and waiting for an on-call engineer to notice an automated email and manually approve the PR before Atlantis could apply it. During product launches, that queue could run past twenty new-topic requests an hour. On-call sometimes just missed the email, and the request timed out.

DoorDash replaced the whole chain — PR, email, human click — with a self-service API that provisions the topic directly. Onboarding time fell from a two-day guarantee to under an hour, often about fifteen minutes: a 95% reduction. On-call load dropped roughly four hours a week. The platform now self-serves around a hundred new topics a week with nobody approving anything.

The part of a system engineers spend the most time optimizing is rarely the part that's actually slowing it down. DoorDash tuned Kafka and Flink to move hundreds of billions of events a day. The slowest step in the whole pipeline was a pull request, waiting for someone to click approve.

#SystemDesign #ApacheKafka #DataEngineering #DoorDash #Infrastructure

---

## Twitter / X Version

1/ DoorDash's event platform moves hundreds of billions of events a day into Snowflake at 99.99% reliability. For years, the real bottleneck wasn't Kafka. It was an on-call engineer's inbox.

2/ Before Iguazu (DoorDash's event platform), every event type had its own SQS or Kinesis pipeline, no shared observability, and data could take up to a full day to reach Snowflake.

3/ The fix: one HTTP Kafka proxy for every producer, Flink jobs fanning out to Snowflake (S3 + Snowpipe), Redis, and Chronosphere, Protobuf schemas checked in CI. Latency: a day → a few minutes.

4/ But onboarding a new event source still took up to 2 business days — because creating a Kafka topic meant a GitHub PR, an Atlantis Terraform plan, and an on-call engineer manually approving it by email. During launches, that queue hit 20+ PRs/hour. Missed emails = timeouts.

5/ DoorDash cut the PR-and-email chain entirely and built a self-service API for topic creation instead. Onboarding: 2 days → under an hour, often ~15 min. 95% reduction. ~4 hours/week of on-call time back. ~100 topics self-served a week now.

6/ The system moving hundreds of billions of events a day wasn't throttled by Kafka. It was throttled by a pull request waiting on a human.

---

## Excalidraw Diagram

**File:** 2026-07-12-doordash-iguazu-kafka-selfserve.excalidraw
**Type:** Migration timeline (structured case study) — five-stage horizontal flow from fragmented pipelines through the platform rebuild to the hidden approval bottleneck and its fix, plus a full-width results bar as the screenshottable centerpiece.
**Color scheme:** Slate for the pre-Iguazu fragmented world (not a villain — just an earlier, reasonable answer), blue for the platform build, emerald for the scale achieved, amber for the hidden human bottleneck (the twist), violet for the fix. No red/green good/bad pairing.
**Screenshottable stat:** "Topic onboarding: 2-business-day guarantee → under 1 hour (often ~15 min) — a 95% reduction. On-call load: -4 hrs/week. ~100 topics self-served a week, zero approvals. The system moving hundreds of billions of events a day wasn't throttled by Kafka — it was throttled by a pull request waiting on a human."

### Layout

```
Title: "DoorDash's Event Platform Moves Hundreds of Billions of Events a Day. Its Bottleneck Was a GitHub Pull Request."
Subtitle: "Iguazu: SQS/Kinesis fragmentation → Kafka + Flink at scale, then the 2-day topic-approval chain that throttled onboarding anyway"

[PRE-IGUAZU]        [THE CONSOLIDATION]     [THE SCALE ACHIEVED]    [THE HIDDEN BOTTLENECK]   [THE FIX]
One SQS or Kinesis   HTTP Kafka proxy,       Hundreds of billions    New topic = GitHub PR     Replaced the PR +
pipeline per event   Flink fans out to       of events a day.        + Atlantis + Terraform    email + approval
type. No shared      Snowflake (via S3 +     99.99% delivery.        + on-call manual          chain with an
observability. Up    Snowpipe), Redis,       Latency to Snowflake:   approval by email.        API-first self-
to a full day to     Chronosphere. Proto-    a day → a few           SLA: 2 business days.     service provis-
reach Snowflake.     buf schemas checked     minutes.                Launches: 20+ PRs/hr,     ioning service.
                     in CI.                                          missed emails = timed     No PR. No email.
                                                                      out requests.             No click.

[RESULT — screenshottable]
Topic onboarding time: 2-business-day guarantee → under an hour, often ~15 minutes — a 95% reduction.
On-call manual work: down roughly 4 hours a week. Platform now self-serves ~100 new topics a week, zero approvals required.
The system moving hundreds of billions of events a day wasn't throttled by Kafka. It was throttled by a pull request waiting on a human.
```
