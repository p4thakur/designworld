# How Dropbox Built Magic Pocket: The Exabyte-Scale Storage That Replaced Amazon S3

**Sources (primary):**
- https://dropbox.tech/infrastructure/inside-the-magic-pocket (Dropbox Engineering Blog, 2016)
- https://dropbox.tech/infrastructure/magic-pocket-infrastructure (Dropbox Engineering Blog — "Scaling to exabytes and beyond", 2017)
- https://dropbox.tech/infrastructure/pocket-watch (Dropbox Engineering Blog — "Pocket watch: Verifying exabytes of data")
- Dropbox S-1 filing (2018) — gross margin and cost savings figures
- QCon San Francisco 2022 — "Magic Pocket: Dropbox's Exabyte-Scale Blob Storage System" (Facundo Agriel)

---

More than half the disk reads inside Dropbox's Magic Pocket aren't serving user files. They're Dropbox checking if the data is still there.

That detail — from the Pocket Watch post on the Dropbox engineering blog — reframes the entire architecture. Magic Pocket isn't just a cost-optimized storage system. It's a system where durability is a scheduled, first-class workload that consumes more I/O budget than serving users.

This is how it got there.

---

## The economics that forced the decision

In summer 2013, Dropbox was one of the largest consumers of Amazon S3. Their product was file storage and sync. Their cost structure was paying AWS per byte per month.

As Dropbox approached exabyte scale, the gap between S3 pricing and the cost of owning equivalent hardware became too large to ignore. The company's gross margins depended on closing it.

The choice wasn't "optimize S3 usage" or "move to a different cloud." The choice was: own the storage layer entirely, or accept that margins would be permanently capped at whatever Amazon allowed.

A small team started Magic Pocket in summer 2013.

---

## The architecture

Magic Pocket is a multi-zone blob storage system distributed across three US regions: west, central, and east. Every block of data is stored in at least two separate zones, with cross-zone replication happening asynchronously in the background.

At the data model level: user files are chunked into immutable blobs. Blocks are aggregated into 1–2 GB logical containers called "buckets" — a bucket maps to a set of physical extents on disk. Metadata about bucket locations is maintained separately from the data itself.

**Erasure coding over full replication**

The most consequential architectural decision was moving from 2x full replication to erasure coding.

Full replication at 2x is simple: write every byte twice, store copies in separate locations. The durability is predictable. The cost is 2x raw storage for every byte of user data.

Dropbox moved to a Reed-Solomon erasure coding variant — effectively a 6+3 configuration (6 data shards + 3 parity shards). The effective storage overhead drops from 2x to roughly 1.5x. That's approximately a 25% reduction in raw storage cost across hundreds of petabytes — a substantial number at the scale Dropbox operates.

The warm tier uses a 1+1 per-zone scheme (one data fragment, one parity); the cold tier uses a 2+1 scheme across three regions, resulting in a replication factor of ~1.5x rather than the prior ~2x.

The tradeoff: erasure coding adds reconstruction complexity when a drive or zone fails. For a system where reads are dominated by sync operations rather than random access, this tradeoff is manageable. Dropbox made it work.

**Hardware**

Each storage server holds approximately 1 petabyte of capacity. The cluster runs more than 600,000 drives across thousands of machines — custom-built hardware optimized for storage density, not general-purpose cloud compute.

---

## Pocket Watch: durability as a workload

The detail that distinguishes Magic Pocket from other large storage systems is Pocket Watch: a continuous, running verification system that re-reads stored data across the cluster to confirm it hasn't been silently corrupted.

Pocket Watch accounts for more than 50% of disk and database I/O inside the cluster.

That number is worth sitting with. More than half the work the disks do has nothing to do with serving user files. It's the system reading its own data, comparing checksums, and confirming nothing has gone wrong.

Why is this necessary?

At exabyte scale with 600,000+ drives, the per-drive failure rate isn't a probability — it's a budget item. Drives fail. Firmware bugs silently flip bits. Cosmic ray events corrupt individual sectors. At this scale, silent corruption events are happening continuously, somewhere in the cluster.

Reactive durability — detecting corruption only when a user reads a file — is too late. By the time a user hits a corrupted file, the window for recovery from redundant copies may have passed if multiple failures have accumulated undetected.

Pocket Watch runs proactively. It continuously re-reads data, verifies checksums, and triggers repair when discrepancies are found. This converts silent corruption from a user-visible failure into an internal cluster event handled automatically.

The result: 12 nines of durability (10^12) and 99.99% availability. The cost: more than half the cluster's I/O capacity is permanently allocated to verification, not user traffic.

---

## The migration and its business impact

Magic Pocket launched and gradually took on production traffic over roughly two and a half years. By October 2015, 90% of Dropbox's 600 petabytes of user data had migrated off Amazon S3.

The financial impact appeared quickly and compounded.

Between 2015 and 2016, Dropbox saved $39.5 million from the S3 exit — a $92.5 million decline in third-party infrastructure expenses offset by $53 million in new owned-infrastructure costs. Within two years, total infrastructure savings reached $74.6 million, as reported in the 2018 S-1 filing.

The gross margin trajectory was more striking: from 46% in Q1 2016 to 70% by Q4 2017. Revenue grew from roughly $185 million to $305 million over that period. The savings weren't just cost reduction — they were margin expansion that changed what Dropbox looked like as a business.

---

## What the design says about the problem

Magic Pocket is often cited as a case study in "leaving the cloud" to save money. That framing is accurate but incomplete.

The more interesting story is what the system allocates most of its capacity to: verification, not serving files. This is what 12 nines actually requires at exabyte scale — not just fault-tolerant architecture, but a system that continuously re-proves its own correctness.

Most storage systems are designed to handle failures when they happen. Magic Pocket is designed around the assumption that failures are always happening, at a rate proportional to the cluster's size. Pocket Watch isn't a feature. It's a design commitment: we will spend more than half our I/O budget on confirming the data is still there, because at exabyte scale, that's the only way to know.

The generalization: at sufficient scale, maintaining correctness is a larger workload than doing the actual work.
