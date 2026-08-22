<!-- sources -->
<!-- Primary: -->
<!--   Reddit (reddit-archive/reddit), "Architecture Overview" — Reddit's own open-source wiki documenting the -->
<!--   Thing/Data EAV schema, column repurposing (e.g. a Subreddit's "ups" holds its subscriber count), and the -->
<!--   Data table's join-overhead tradeoff — https://github.com/reddit-archive/reddit/wiki/architecture-overview -->
<!--     — fetched directly via WebFetch and loaded successfully, unlike most prior posts in this series (many -->
<!--     engineering-blog domains return EGRESS_BLOCKED under this session's network policy). -->
<!-- Corroborating (independent secondary sources, cross-referenced for consistency; direct WebFetch of -->
<!-- highscalability.com, kevin.burke.dev, qconsf.com, and infoq.com all returned EGRESS_BLOCKED, so the -->
<!-- following facts were verified across multiple independent web-search-result excerpts that directly quote -->
<!-- or closely paraphrase these primary talks, not written from memory): -->
<!--   High Scalability, "7 Lessons Learned While Building Reddit to 270 Million Page Views a Month" (2010), -->
<!--   summarizing a talk by Reddit co-founder Steve Huffman — -->
<!--   http://highscalability.com/blog/2010/5/17/7-lessons-learned-while-building-reddit-to-270-million-page.html -->
<!--   Neil Williams (Reddit infrastructure lead), "The Evolution of Reddit.com's Architecture," QCon SF 2017 / -->
<!--   InfoQ — https://www.infoq.com/presentations/reddit-architecture-evolution/ -->
<!-- Key verifiable details: -->
<!-- 1. Reddit's original data model treats every object — links, comments, accounts, subreddits, awards — as a -->
<!--   generic "Thing," stored across two tables per thing type: a fixed-schema Thing table (id, vote counts, -->
<!--   deleted/spam flags) and a Data table holding every other attribute as an individual keyed row. -->
<!-- 2. Columns on the Thing table are repurposed per type when they don't have a literal meaning for that type -->
<!--   — e.g. a Subreddit's "ups" column stores its subscriber count. -->
<!-- 3. Reddit's own documentation states the Data table's tradeoff explicitly: "zero-effort flexibility in the -->
<!--   schema of things, but does mean higher overhead via joins and the like to fetch the data." -->
<!-- 4. Steve Huffman's 2010 talk cites the motivation: normalized schema changes at scale required slow, -->
<!--   locking ALTER TABLE operations — in Postgres, adding a column takes an AccessExclusiveLock on the whole -->
<!--   table, halting writes to a table with millions of rows for the duration. -->
<!-- 5. In 2011, per Neil Williams' 2017 QCon SF talk, Postgres replication to a secondary began falling behind; -->
<!--   Reddit's cached listings kept referencing Thing IDs the lagging replica hadn't caught up to, producing -->
<!--   failures where a listing pointed to (for example) item 1234 while that replica's Thing table only had -->
<!--   items 1, 2, and 4. -->
<!-- 6. Reddit's own wiki confirms it runs two core permanent data stores, PostgreSQL and Cassandra — Cassandra -->
<!--   was added to absorb heavy write/scalability and replication pressure rather than replacing the Thing/Data -->
<!--   design outright. -->
<!-- Publication: Reddit engineering wiki (ongoing); Steve Huffman talk covered by High Scalability, May 2010; -->
<!-- Neil Williams talk, QCon San Francisco, November 2017. -->

# The Database Anti-Pattern Reddit Built Its Entire Site On

**Date:** 2026-08-22
**Company:** Reddit
**Category:** storage
**Post type:** contrarian
**Opening style:** challenge_assumption
**Slug:** reddit-thingdb-eav-schema
**Character count (LinkedIn):** ~2280

---

## LinkedIn Post

Every database course teaches the same rule: never build an EAV schema. Entity-attribute-value tables are the textbook anti-pattern — slow to query, easy to corrupt, brutal to index. Reddit built one anyway, and ran the entire site on it.

In Reddit's original architecture, everything was a "Thing" — links, comments, accounts, subreddits, even awards. Every Thing type shared two tables: a fixed-schema Thing table (id, vote counts, deleted/spam flags — columns often repurposed per type, so a subreddit's "ups" column held its subscriber count) and a Data table, where every other attribute was stored as its own row keyed to the thing's id. One schema, every object type, no exceptions.

The reason wasn't ideology. It was a specific cost that normalized schemas hide until you're at scale: in Postgres, adding a column takes an AccessExclusiveLock on the whole table. On a table with millions of rows, that's not a quick migration — it's a write freeze. Reddit's early team decided a fast-moving startup couldn't afford to stop writes every time a Link needed a new field. So "add an attribute" became "insert a row," never a schema change.

It worked, for years — until the design's own flexibility hid a different failure. When Postgres replication to a secondary started falling behind, Reddit's cached listings kept pointing at Thing IDs the lagging replica hadn't caught up to yet. A listing would reference item 1234. That replica's Thing table only actually had items 1, 2, and 4. Pages started trying to render objects that, as far as that copy of the database was concerned, didn't exist.

Normalization isn't free, and neither is skipping it. Reddit paid the EAV tax — join overhead, weaker constraints, harder debugging — because the alternative cost, locked tables during a land-grab phase of growth, was worse for where they were. They didn't reverse the decision when it started to hurt, either. They added Cassandra alongside Postgres, pulling the heaviest write paths off Postgres instead of tearing out a schema that had already bought them years of runway.

The anti-pattern wasn't the mistake. Treating "never do X" as a law instead of a tradeoff would have been.

#SystemDesign #DatabaseArchitecture #SoftwareEngineering #BackendEngineering

---

## Twitter / X Version

1/ Every database course teaches: never build an EAV schema. Reddit built one anyway — and ran the whole site on it.

2/ Every object on Reddit — links, comments, accounts, subreddits — was a "Thing." Two tables per type: a fixed Thing table (id, vote counts, flags — often repurposed, so a subreddit's "ups" held its subscriber count) and a Data table storing every other attribute as its own row.

3/ Why: in Postgres, adding a column takes an AccessExclusiveLock on the whole table. On millions of rows, that's a write freeze, not a migration. Reddit's early team decided a startup couldn't afford that every time a Link needed a new field.

4/ It worked for years — until the flexibility hid a different bug. When Postgres replication to a secondary fell behind, cached listings kept pointing at Thing IDs the lagging replica hadn't caught up to. A listing pointed to item 1234; that replica only had items 1, 2, and 4.

5/ They didn't reverse the design. They added Cassandra alongside Postgres to pull the heaviest writes off, keeping the schema that had bought them years of runway.

6/ The anti-pattern wasn't the mistake. Treating "never do X" as law instead of a tradeoff would have been.

---

## Excalidraw Diagram

**File:** 2026-08-22-reddit-thingdb-eav-schema.excalidraw
**Type:** Side-by-side architecture comparison ("obvious"/textbook normalized approach vs. what Reddit actually
built), plus an incident callout and a resolution footer — matching the contrarian post type's recommended
layout.
**Color scheme:** Slate for the "textbook" normalized approach (not villainized — it's the default for good
reason), gold/amber for Reddit's Thing/Data EAV design, red reserved only for the real failure (the 2011
replication incident, not the design choice itself), and teal for the Cassandra resolution — deliberately not
a red=bad/green=good post, and a fresh palette versus the blue/amber/red/green four-stage set used on the
prior database post.
**Screenshottable stat:** "Listing pointed to item 1234. That replica's Thing table only had items 1, 2, and 4."

### Layout

```
Title: "The Database Anti-Pattern Reddit Built Its Entire Site On"
Subtitle: "Reddit's own engineering wiki + Neil Williams, QCon SF 2017 — why Reddit's Thing/Data EAV schema
was a deliberate tradeoff, not a mistake"
Stat callout (amber): "One schema. Every object type. Links, comments, accounts, subreddits, awards — all
just a 'Thing' plus a Data table of rows."

[2 boxes side by side]

THE TEXTBOOK WAY [slate]                          WHAT REDDIT BUILT [amber]
Normalized tables, one per object type.           One Thing table (id, vote counts, flags —
Adding a field means ALTER TABLE —                repurposed per type) + one Data table.
in Postgres, an AccessExclusiveLock on             New attribute = new row. Zero migrations,
the whole table. Millions of rows =                zero locks, one schema for every kind
a write freeze, not a quick migration.             of object on the site.

        \                                                /
         \                                              /
          v                                            v
[INCIDENT BAND, red, full width]
"2011 — Postgres replication to a secondary falls behind. Cached listings keep pointing at Thing IDs the
lagging replica hasn't caught up to: a listing references item 1234, but that replica's Thing table only
has items 1, 2, and 4."

        v (center arrow)

[FOOTER, teal band, full width]
"THE RESOLUTION — Reddit didn't reverse the EAV design. They added Cassandra alongside Postgres to absorb
the heaviest write paths instead. Normalization isn't free, and neither is skipping it — the anti-pattern
wasn't the mistake. Treating 'never do X' as a law instead of a tradeoff would have been."
```
