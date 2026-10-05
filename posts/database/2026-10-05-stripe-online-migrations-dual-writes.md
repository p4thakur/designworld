---
date: 2026-10-05
company: Stripe
topic: Stripe's four-step dual-writing pattern for online migrations, used to move ~100 million subscription objects out of the Customer document in MongoDB without downtime.
category: database
post_type: structured
opening_style: shared_pain_point
slug: stripe-online-migrations-dual-writes
---

## Sources

- Jacqueline Xu, Stripe, [Online migrations at scale](https://stripe.com/blog/online-migrations) — primary source: the four-step pattern (dual write, change reads, change writes, remove old data), the single `subscription` to `subscriptions` array change, and Scalding/Hadoop backfill over a database snapshot.
- Arpit Bhayani, [summary of the post](https://x.com/arpit_bhayani/status/2033885886027600335) — source of the ~100 million objects / "more than 3 years at 1 second each" framing (derived arithmetic, labelled as such in the post).

**Note on sourcing:** stripe.com and other direct fetches were blocked by this environment's egress policy. Facts come from search-indexed excerpts of the primary post and a secondary summary. The "100 million" and "3 years" figures were seen only in the secondary summary and should be re-checked against the original before publishing. The "thousands of tasks" phrasing is general MapReduce description, not a Stripe figure; consider softening it.

**Key primary-source detail:** the backfill runs on a snapshot via Scalding/Hadoop, which is why dual writing must come first, so records created after the snapshot are not lost.

---

## LinkedIn Post

Every schema change on a live payments system hits the same arithmetic. Stripe once had to restructure about 100 million subscription objects. At one second per object, that is more than three years of work, and the system still has to serve traffic the whole time.

Early on, Stripe's data model said a customer had at most one subscription, so the subscription lived inside the Customer document in MongoDB. Product needs changed: customers needed several active subscriptions. That meant turning a single `subscription` field into a `subscriptions` array, and moving subscriptions into their own table.

Stripe's answer was a four-step dual-writing pattern, and the discipline is in what it refuses to do: flip anything all at once.

First, dual write. Every new or updated subscription goes to both the old Customers table and the new Subscriptions table. Second, change the read paths so the application reads from the new table. Third, change the write paths so the application stops writing the old one. Fourth, delete the old data once you trust the new.

That sequence only works if the new table is complete. Dual writing covers new traffic, but millions of old records are untouched. For those, Stripe takes a snapshot of the database and runs a distributed backfill job over it, using Scalding on a Hadoop cluster (MapReduce). A single-process migration script would run for years. A cluster job splits the same work across thousands of tasks.

What makes this safe is that no step is a one-way door. Each is deployed on its own and can be rolled back on its own. If the new reads look wrong, you flip back to the old table, which is still being written. Reading from the new table is a deploy, not a leap of faith.

The pattern is slower than a migration script. It takes more deploys, more code that exists only to be deleted, and a stretch where two sources of truth have to agree. Stripe accepted that cost because the alternative was betting a payments system on one cutover.

A schema change at this scale is not a script. It is a series of small reversible moves, with the old system kept alive until the new one has earned the right to replace it.

#SystemDesign #Databases #Stripe #Migrations

**Character count: 2213 / 3,000**

---

## Twitter / X Thread

1/ Stripe once had to restructure ~100M subscription objects in MongoDB. At 1 second each, that is 3+ years, with live traffic the whole time.

2/ Old model: one subscription per customer, stored inside the Customer document. New need: several per customer, in their own table.

3/ The pattern: (1) dual write to old and new tables, (2) switch reads to new, (3) switch writes to new only, (4) delete old data.

4/ Old records get backfilled from a database snapshot with a Scalding/Hadoop job. Dual write comes first so nothing created after the snapshot is lost.

5/ Every step ships separately and rolls back separately. Slower than a script, but nothing is ever a one-way door.
