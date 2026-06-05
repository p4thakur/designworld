# Twitter/X Thread — Dropbox Magic Pocket

---

**1/**
More than half the disk reads inside Dropbox's Magic Pocket aren't serving user files.

They're Dropbox checking if the files are still there.

That's 10^12 durability at exabyte scale.

---

**2/**
In 2013, Dropbox was paying AWS to store exabytes. Storage was the product. Every byte had a line item.

So a small team started Magic Pocket — build the storage layer from scratch. Two and a half years. 600 petabytes.

---

**3/**
The cost decision: ditch 2x full replication for Reed-Solomon erasure coding (6 data + 3 parity).

~25% less storage overhead. Higher theoretical durability. 600,000+ drives across 3 US zones. Each server: ~1PB.

---

**4/**
The number most summaries skip:

>50% of all disk and database I/O inside the cluster is Pocket Watch — their continuous verification job — re-reading data just to check it's still intact.

Durability isn't a property of the system. It's a workload.

---

**5/**
By Oct 2015: 90% of 600PB migrated off S3.
Year-one savings: $39.5M.
Two-year savings: $74.6M (per 2018 S-1).
Gross margins: 46% → 70% in 18 months.

Not infrastructure optimization. Business model transformation.
