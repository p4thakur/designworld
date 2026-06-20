# Uber's Schemaless: When MySQL Became the NoSQL Layer

> **Sources (primary):**
> - [Schemaless: Adding a Document Store to MySQL (Part 1)](https://www.uber.com/blog/schemaless-part-one/) — Uber Engineering Blog, August 2016
> - [Schemaless: Adding a Document Store to MySQL (Part 2)](https://www.uber.com/blog/schemaless-part-two/) — Uber Engineering Blog, 2016
> - [How FriendFeed uses MySQL to store schema-less data](https://backchannel.org/blog/friendfeed-schemaless-mysql) — Bret Taylor, 2009 (the design Uber adapted)

---

## LinkedIn Post

In 2014, Uber was growing fast enough that MySQL had become a liability.

Schema migrations on their dispatch tables — the ones that tracked every active trip and driver in real time — required ALTER TABLE on hundreds of millions of rows. That operation locked the table. On a Friday night at peak load, it could take hours.

The obvious fix was Cassandra. Document model, horizontal scaling, no schema hell. Everyone was migrating to it.

Uber built something different: a document store on top of MySQL. They called it Schemaless.

The design came from a 2009 FriendFeed post by Bret Taylor. The idea: stop storing structured rows. Store "cells" — each a JSON blob with a UUID key, a column name, and an auto-incrementing `added_id`. Every write is an INSERT. Cells are never modified in place. To get the current state of an entity, you query the cell with the highest `added_id` for that key.

This made ALTER TABLE irrelevant. The "schema" lived in application code that read the JSON. MySQL stored opaque blobs.

Why not Cassandra? The honest answer: operations. By 2014, Uber's team had years of MySQL experience — backup pipelines, replication monitoring, incident playbooks, tooling. Adopting Cassandra at their growth rate meant rebuilding all of that from scratch with a team already stretched thin. That's a different kind of risk than schema migrations.

Schemaless gave them document-model flexibility without discarding the operational foundation they trusted. Secondary lookups required maintaining separate "trigger index" tables in MySQL — more complexity, but manageable.

It worked for years. The dispatch system it powered handled tens of millions of trips.

The part worth sitting with: the architecture wasn't chosen because it was elegant. It was chosen because it fit the people and the timeline. Operational knowledge is infrastructure too.

In 2026, with mature Cassandra tooling and CockroachDB and YugabyteDB widely deployed, the same team might make a different call. In 2014, this was the right one.

#SystemDesign #Database #Engineering #Uber #MySQL

---

**Character count: ~2,100** ✓ (limit: 3,000)

---

## Twitter / X Version

In 2014, Uber had a MySQL problem.

ALTER TABLE on hundreds of millions of trip rows locked the table for hours. Engineers routed around schemas. Every migration was a production risk.

The obvious fix: Cassandra. Everyone was migrating to it.

Uber built a document store on top of MySQL instead. They called it Schemaless.

The design traces to a 2009 FriendFeed post by Bret Taylor. Every write is an INSERT — cells are never modified in place. To read current state: find the cell with the highest `added_id` for that key. Schema lives in app code. MySQL stores blobs.

Why not Cassandra? Operations.

By 2014, Uber's team had years of MySQL experience: backup pipelines, replication monitoring, incident playbooks. Adopting Cassandra meant rebuilding that foundation at their growth rate. That's a different category of risk.

Schemaless gave them document-model flexibility without discarding the foundation. The price: secondary lookups needed manual trigger indexes — extra work, manageable.

The dispatch system it powered handled tens of millions of trips.

The architecture wasn't chosen because it was elegant. It was chosen because it fit the people and the timeline. Operational knowledge is infrastructure.

---

## Diagram

See: `2026-06-20-uber-schemaless-nosql-on-mysql.excalidraw`

**Type:** Confessional timeline — three phases (2012–2013: works → 2014: ALTER TABLE crisis → 2014+: Schemaless) with append-only cell model detail below.
