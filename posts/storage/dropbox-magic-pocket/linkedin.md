# LinkedIn Post — Dropbox Magic Pocket: S3 to Exabyte-Scale Self-Storage
# Structured Case Study | Hook: specific_number | ~2,240 chars

---

More than half the disk reads inside Dropbox's Magic Pocket aren't serving your files.

They're Dropbox checking if your files are still there.

That's what 10^12 durability — 12 nines — actually costs at exabyte scale.

The problem started in summer 2013. Dropbox was growing toward exabytes and every byte lived on Amazon S3, with a line item on an AWS invoice. Storage was the product. The margin math was unsustainable.

So a small team started Magic Pocket. Not to optimize S3 usage. To own the storage layer entirely — custom hardware, custom erasure coding, and a verification system that never stops running.

The architecture runs across three US zones (west, central, east). Every block written to at least two zones, replicated asynchronously across regions. But the key cost decision was moving from 2x full replication to erasure coding.

Dropbox uses a Reed-Solomon variant — 6 data shards + 3 parity (a 6+3 configuration). That shift saved roughly 25% of raw storage overhead while maintaining or improving durability. Each storage server: ~1 petabyte. Total cluster: 600,000+ drives.

Here's the detail that stops engineers cold.

More than 50% of disk and database I/O inside Magic Pocket is Pocket Watch — their continuous verification system — re-reading data to confirm it's still intact. Not serving files. Not writing new ones. Just checking.

At exabyte scale, bit rot, hardware degradation, and cosmic ray flips aren't edge cases. They're a scheduled workload. You don't achieve 12 nines by designing a good system. You achieve it by spending more than half your I/O budget making sure the system is still working.

The results:

By October 2015 — two and a half years after launch — 90% of 600 petabytes was off S3.
Year-one savings: $39.5 million.
Two-year savings: $74.6 million (per the 2018 S-1 filing).
Gross margins: 46% in Q1 2016 → 70% by Q4 2017.

Not a cost optimization. A different business.

The principle: when storage is the product, your durability guarantee isn't a feature. It's a workload. One that consumes more resources than serving users ever will.

#SystemDesign #DistributedSystems #StorageEngineering #CloudInfrastructure
