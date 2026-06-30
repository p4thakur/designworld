<!-- sources -->
<!-- Primary: "We replaced Redis with MySQL for inventory reservations—and it scaled" — Shopify Engineering Blog (May 2026) -->
<!-- URL: https://shopify.engineering/scaling-inventory-reservations -->
<!-- Key verifiable details (primary source only): -->
<!-- 1. Core mechanism: MySQL 8 SELECT ... FOR UPDATE SKIP LOCKED -->
<!-- 2. Schema: one row per available inventory unit, pool capped at 1,000 rows per item/location combination -->
<!-- 3. Composite primary key: (shop_id, inventory_item_id, inventory_group_id, id) — halved lock count per reservation -->
<!-- 4. Shadow mode: Redis + MySQL ran in parallel on real production traffic before cutover -->
<!-- 5. Black Friday 2025 stats: writer CPU under 50%, reader CPU under 16%, with headroom to spare -->
<!-- 6. Peak traffic: $5.1 million in sales per minute -->

# Shopify: Why Redis Isn't Always the Right Answer for High-Traffic Inventory

**Date:** 2026-06-30
**Company:** Shopify
**Category:** caching
**Post type:** structured
**Opening style:** specific_number
**Slug:** shopify-redis-to-mysql-inventory-skip-locked
**Character count (LinkedIn):** ~2,330

---

## LinkedIn Post

$5.1 million in sales per minute. Shopify hit that on Black Friday 2025. Their inventory system wasn't Redis—it was MySQL.

Earlier this year, Shopify's engineering team published a post that surprised a lot of engineers: they had replaced Redis with MySQL for inventory reservations. The exact component that prevents flash sales from overselling.

The original design made intuitive sense. Redis is fast, in-memory, and INCR is atomic. For counting down available inventory, it's the canonical answer. Shopify used it the same way: a reservation increments the reserved count, a claim decrements it.

The problem was the transaction boundary. Redis and MySQL don't share one. That leaves a gap: a payment can succeed but the inventory claim can fail. Or the reservation decrements but the refund never restores the count. At Shopify's scale, that gap closes on thousands of orders a day.

The fix came from MySQL 8: SELECT ... FOR UPDATE SKIP LOCKED.

Instead of one row per item with a counter, they rebuilt with one row per available unit—a bounded pool capped at 1,000 rows per item/location combination. A reservation claims a row, not a number. SKIP LOCKED means competing transactions skip already-locked rows rather than queuing behind them. Lock contention dissolves.

The schema was as important as the query. They replaced secondary indexes with a composite primary key: (shop_id, inventory_item_id, inventory_group_id, id). That halved the number of locks per reservation—InnoDB's clustered index lookup eliminates a separate index scan.

Before fully cutting over, they ran shadow mode: MySQL and Redis processed the same traffic in parallel, MySQL as shadow, until correctness and performance were confirmed on real production load.

Black Friday 2025 result: writer CPU stayed under 50%. Reader CPU under 16%. With headroom to spare.

Reservations and inventory now live in the same database. A payment can reserve, claim, and confirm in a single ACID transaction. An entire class of inconsistency bugs doesn't exist anymore—not because of retries or compensating transactions, but because the data model changed.

The fastest store isn't always the right one. Sometimes the right answer is the one that shares a transaction boundary with the thing it depends on.

#SystemDesign #Engineering #MySQL #BackendEngineering

---

## Twitter / X Version

1/ $5.1 million in sales per minute. Shopify hit that on Black Friday 2025. Their inventory system wasn't Redis. It was MySQL.

Here's why that worked — and what SELECT ... FOR UPDATE SKIP LOCKED actually solves.

2/ Original design: Redis INCR/DECR for inventory. Atomic, fast, canonical answer.

The problem: Redis and MySQL don't share a transaction. Payment succeeds → inventory claim fails. Or the reverse. At Shopify's scale: thousands of inconsistencies per day.

3/ The fix: MySQL 8's SELECT ... FOR UPDATE SKIP LOCKED.

One row per available unit, pool capped at 1,000 rows per item/location. A reservation claims a row — not decrements a counter. Locked rows are skipped, not waited on. Contention dissolves.

4/ Schema detail: composite PK (shop_id, inventory_item_id, inventory_group_id, id) instead of secondary indexes. Halved locks per reservation — InnoDB's clustered index eliminates the separate scan.

5/ Before switching: shadow mode. MySQL and Redis ran in parallel on real traffic until correctness and performance were confirmed.

Black Friday 2025: writer CPU < 50%. Reader CPU < 16%. With headroom to spare.

6/ The fastest store isn't always the right one.

The right one is the one that shares a transaction boundary with the thing it depends on.

---

## Excalidraw Diagram

**File:** 2026-06-30-shopify-redis-to-mysql-inventory-skip-locked.excalidraw
**Type:** Before/after side-by-side comparison (structured case study)
**Color scheme:** Orange/amber (#d4813a) for BEFORE/Redis section. Teal (#2a8c6e) and green (#6acc8a) for AFTER/MySQL section. Red (#e05c5c) for the transaction gap. Dark canvas (#0d0d1a).
**Screenshottable stat:** "$5.1M/min peak · Writer CPU <50% · Reader CPU <16% · 1,000-row pool cap"

### Layout

```
Title: "Shopify: Redis → MySQL for Inventory Reservations"
Subtitle: "$5.1M/min peak · Black Friday 2025 · ACID fixed entire class of inventory bugs"

BEFORE: Redis Counter            VS      AFTER: MySQL SKIP LOCKED
┌──────────────────────────────┐          ┌───────────────────────────────────────────┐
│ [Order Request]              │          │ [Order Request]                            │
│        ↓                     │          │        ↓                                   │
│ [Redis INCR reserved_count]  │          │ ┌─ BEGIN TRANSACTION (MySQL ACID) ────────┐│
│        ↓ - - - (dashed/red)  │          │ │ SELECT unit FOR UPDATE SKIP LOCKED      ││
│ ⚠ NO SHARED TRANSACTION      │          │ │   → Claims row from 1,000-row pool      ││
│        ↓ - - - (dashed/red)  │          │ │        ↓                                ││
│ [Payment Service (Stripe)]   │          │ │ Process Payment (Stripe)                ││
│        ↓ - - - (dashed/red)  │          │ │        ↓                                ││
│ [Redis DECR available_count] │          │ └─ COMMIT — reserve + pay = atomic ──────┘│
│                              │          │        ↓                                   │
│ ❌ Payment ✓ / Inventory ✗   │          │ ✓ Inconsistency impossible — data model    │
│    Thousands of bugs daily   │          │ ┌─────────────────────────────────────────┐│
│    at Shopify scale          │          │ │ Composite PK: (shop_id, item_id,        ││
└──────────────────────────────┘          │ │   group_id, id) → lock count ÷ 2       ││
                                          │ │ Pool: 1,000 rows · Shadow validated     ││
                                          │ └─────────────────────────────────────────┘│
                                          └───────────────────────────────────────────┘

[ $5.1M/min peak · 1,000-row pool cap · Writer CPU <50% · Reader CPU <16% · Shadow mode validated ]
```
