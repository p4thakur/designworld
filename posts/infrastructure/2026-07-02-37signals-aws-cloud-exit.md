<!-- sources -->
<!-- Primary: David Heinemeier Hansson (DHH), "We have left the cloud" — 37signals/HEY World -->
<!-- URL: https://world.hey.com/dhh/we-have-left-the-cloud-251760fb -->
<!-- Primary: DHH, "Our cloud-exit savings will now top ten million over five years" -->
<!-- URL: https://world.hey.com/dhh/our-cloud-exit-savings-will-now-top-ten-million-over-five-years-c7d9b5bd -->
<!-- Primary: Basecamp, "Leaving the Cloud" hub page — https://basecamp.com/cloud-exit -->
<!-- Primary (technical): 37signals Dev, "Moving Mountains of Data off S3" — https://dev.37signals.com/moving-mountains-of-data-off-s3/ -->
<!-- Corroborating (cross-checked, consistent on figures below): -->
<!--   https://www.theregister.com/2024/10/21/37signals_aws_savings/ -->
<!--   https://www.theregister.com/2025/05/09/37signals_cloud_repatriation_storage_savings/ -->
<!--   https://www.datacenterdynamics.com/en/news/37signals-begins-exiting-aws-storage-service/ -->
<!--   https://www.thestack.technology/dhh-aws-egress-s3-pure/ -->
<!--   https://shiftmag.dev/leaving-the-cloud-314/ -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. 2022 AWS run rate: $3,201,564/year; database costs alone exceeded $500,000/year -->
<!-- 2. 2023: bought ~20 Dell R7625 servers (two pallets) for ~$600-700K — 4,000 vCPUs, 7,680GB RAM, 384TB NVMe -->
<!-- 3. Hardware cost fully recouped during 2023 as cloud contract commitments rolled off (paid back within ~6 months) -->
<!-- 4. Built Kamal, an open-source deploy tool (plain SSH + Docker, no Kubernetes/orchestration platform) -->
<!-- 5. 2024 actual AWS bill: down to ~$1.3M/year from the $3.2M/year run rate — original 5-yr savings estimate of $7M revised upward to >$10M -->
<!-- 6. 2025: exiting S3 (~10PB, billions of objects) for a dual-datacenter Pure Storage deployment (~18PB combined capacity, S3-compatible API) -->
<!-- 7. Migration built custom tooling to run bucket listings in parallel — cut a multi-day listing job to ~30 minutes -->
<!-- 8. AWS waived a ~$250,000 data egress fee for the departing account -->
<!-- 9. DHH quote: "We were paying for the privilege of renting computers at obscene margins." -->

# 37signals: The Cloud Bill That Had an Expiration Date

**Date:** 2026-07-02
**Company:** 37signals (Basecamp, HEY)
**Category:** infrastructure
**Post type:** confessional
**Opening style:** cold_fact
**Slug:** 37signals-aws-cloud-exit
**Character count (LinkedIn):** ~2,033

---

## LinkedIn Post

For 16 years, 37signals ran Basecamp and HEY entirely on the cloud. In 2022, the AWS bill hit $3.2 million a year — with the databases alone costing over $500,000 of that. Then they canceled the account.

The cloud wasn't a bad call in 2006. It let a small team launch products without hiring anyone to rack servers, and scale up during traffic spikes without guessing capacity months in advance. For a startup that didn't know its own future load, renting made sense.

But by 2022, 37signals wasn't guessing anymore. They'd run the same workloads for over a decade. They knew exactly how much compute, memory, and storage they needed, every day, within a rounding error. Elastic capacity they never used had quietly become a tax, not a feature.

So DHH ran the numbers on owning hardware outright instead. "We were paying for the privilege of renting computers at obscene margins," he wrote. The math wasn't close: two pallets of Dell servers — 20 machines, 4,000 vCPUs, 7.5TB of RAM, 384TB of NVMe — cost around $700,000 and paid for themselves within six months. They also wrote their own deploy tool, Kamal, using plain SSH and Docker, because container orchestration was the one thing the cloud had quietly been doing for them.

By 2024 the AWS bill had dropped from $3.2M to $1.3M a year. Original five-year savings estimate: $7M. Revised estimate: over $10M.

The last, hardest leg was moving roughly 10 petabytes of data out of S3 — billions of objects, zero downtime allowed. They built custom tooling to run bucket listings in parallel, turning a job that would've taken days into about 30 minutes. When AWS realized the account was really leaving, it waived a $250,000 egress fee on the way out.

None of this means the cloud was a mistake. It means the decision has an expiration date. The right call at year one — pay for flexibility you can't yet predict — becomes the wrong call at year fifteen, once you've already learned exactly what you need.

#SystemDesign #CloudComputing #Infrastructure #Engineering

---

## Twitter / X Version

1/ In 2022, 37signals (Basecamp, HEY) paid Amazon $3.2 million for cloud hosting. Database costs alone: over $500K of that.

Then they canceled the AWS account entirely.

2/ This wasn't a "cloud bad" take. Renting made total sense in 2006 — no ops hires needed, capacity scaled with traffic they couldn't predict yet.

By 2022 they weren't predicting anymore. Same workloads, over a decade of data. They knew their exact load, every day.

3/ DHH's line: "We were paying for the privilege of renting computers at obscene margins."

The math: ~$700K on Dell servers — 20 machines, 4,000 vCPUs, 384TB of NVMe — paid for itself in 6 months.

4/ They even wrote their own deploy tool, Kamal (plain SSH + Docker, no Kubernetes) — because container orchestration was the one thing the cloud had been quietly handling for them.

5/ Result: AWS bill went from $3.2M/yr to $1.3M/yr. First 5-year savings estimate was $7M. Revised: north of $10M.

6/ The hardest part was last: pulling ~10 petabytes out of S3, billions of files, zero downtime. They parallelized bucket listings to turn a multi-day job into ~30 minutes.

When AWS saw they were really leaving, it waived a $250,000 egress fee on the way out.

7/ The lesson isn't "leave the cloud." It's that the decision has an expiration date. Paying for flexibility you can't predict is smart at year one. At year fifteen, once you already know exactly what you need, it's just a tax.

---

## Excalidraw Diagram

**File:** 2026-07-02-37signals-aws-cloud-exit.excalidraw
**Type:** Timeline with cost bar-chart and callout (confessional)
**Color scheme:** Amber (cloud-era growth), slate (the decision point), indigo (owning hardware), teal (post-exit results/savings), violet (S3 exit callout). Light canvas. No red/green good/bad coding — the cloud era is amber, not red, since it was the right call for its time.
**Screenshottable stat:** "$3.2M → $1.3M/yr · $700K in servers, paid back in 6 months · AWS waived a $250K exit fee"

### Layout

```
Title: "37signals: The Cloud Bill That Had an Expiration Date"
Subtitle: "$3.2M → $1.3M per year · $700K in servers, paid back in 6 months · AWS waived a $250K exit fee"

[2006–2021: All-in on AWS] -> [2022: bill hits $3.2M/yr,   -> [2023: buys $700K hardware, -> [2024–2025: bill at $1.3M/yr,
 no ops hires needed,           DBs alone $500K+, DHH          writes Kamal (SSH+Docker),      exits S3 (~10PB) for Pure
 scaled with unknown growth]    runs the numbers]              recouped in 6 months]           Storage, AWS waives $250K egress]

Annual AWS bill:
[bar: 2022, $3.2M/yr, tall]  ↘ ~$2M/yr saved ↘  [bar: 2024, $1.3M/yr, short]

                                                    [Callout: The last, hardest leg — moving ~10PB
                                                     and billions of files out of S3 with zero downtime.
                                                     Custom tooling ran bucket listings in parallel,
                                                     turning a multi-day job into ~30 minutes. When AWS
                                                     saw the account was really leaving, it waived a
                                                     $250,000 egress fee on the way out.]

Timeline: 2006 goes all-in on AWS -> 2022 bill hits $3.2M/yr -> 2023 buys hardware, paid back in 6 months
          -> 2024 bill at $1.3M/yr -> 2025 exits S3, AWS waives $250K fee
```
