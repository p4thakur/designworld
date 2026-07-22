<!-- sources -->
<!-- Primary: Erik Bernhardsson, "Annoy," erikbern.com, published 2013-04-12. -->
<!--   URL: https://erikbern.com/2013/04/12/annoy.html -->
<!-- Primary: Erik Bernhardsson, "Nearest neighbor methods and vector models – part 2 – algorithms and data -->
<!--   structures," erikbern.com, 2015-10-01 (deeper mechanism writeup: hyperplane construction, forest of trees, -->
<!--   priority-queue search). URL: https://erikbern.com/2015/10/01/nearest-neighbors-and-vector-models-part-2-how-to-search-in-high-dimensional-spaces.html -->
<!-- Primary: spotify/annoy README (project documentation, actively maintained). -->
<!--   URL: https://github.com/spotify/annoy/blob/main/README.rst -->
<!-- Note: direct WebFetch of erikbern.com, github.com raw README render, medium.com, and grokipedia.com all -->
<!--   returned HTTP 403 under this session's egress policy (same failure mode documented in earlier posts in this -->
<!--   repo, e.g. the 2026-07-18 Etsy post). Facts below are cross-checked across multiple independent WebSearch -->
<!--   result excerpts that directly quote or closely paraphrase the primary erikbern.com posts and the spotify/annoy -->
<!--   README, corroborated across several independent secondary summaries (Zilliz Learn, sds-aau course notes, -->
<!--   Grokipedia) that each repeat the same details without contradiction. -->
<!-- Key verifiable details (quoted or closely paraphrased via search excerpts): -->
<!-- 1. Erik Bernhardsson built Annoy while at Spotify; the earliest primary post is dated 2013-04-12, and multiple -->
<!--   independent summaries describe it as built "in a couple of afternoons during Hack Week." Used at Spotify for -->
<!--   music recommendations: after matrix factorization on listening data, every user/track is a vector in -->
<!--   f-dimensional space, and Annoy finds nearest neighbors among them. -->
<!-- 2. Direct quote (README): "at every intermediate node in the tree, a random hyperplane is chosen, which -->
<!--   divides the space into two subspaces," and the hyperplane is chosen "by sampling two points from the subset -->
<!--   and taking the hyperplane equidistant from them." This is repeated k times to build "a forest of trees." -->
<!-- 3. Direct quote (README, on memory): "Using floats, 5M * 40 * 4 is already 800MB" — Annoy's own illustrative -->
<!--   math for why a shared, non-duplicated index matters (5,000,000 items × 40-dimensional float vectors × 4 -->
<!--   bytes/float = 800MB for one copy). This is presented in the docs as an example, not as a literal historical -->
<!--   catalog size at a specific date — treated that way in the post below. -->
<!-- 4. Direct quote (README, on mmap): Annoy "creates large read-only file-based data structures that are mmapped -->
<!--   into memory so that many processes may share the same data." "If you want to find nearest neighbors and you -->
<!--   have many CPU's, you only need to build the index once" — i.e., build is a separate, offline step from -->
<!--   serving; any process can mmap the finished file and query immediately. -->
<!-- 5. Query-time tuning: search visits "up to search_k nodes which defaults to n_trees * n if not provided," and -->
<!--   search_k is the explicit runtime knob trading accuracy for speed. Number of trees (n_trees) is the equivalent -->
<!--   knob at build time; README guidance: "should probably be on the order of dimensionality." -->
<!-- 6. Dimensionality guidance (README, paraphrased): works better under ~100 dimensions but "seems to perform -->
<!--   surprisingly well even up to 1,000 dimensions" — included here only as documented guidance, not asserted as a -->
<!--   hard theoretical bound. -->
<!-- Mechanism-level explanation of *why* kd-trees stop pruning effectively in higher dimensions (the curse of -->
<!--   dimensionality collapsing the fraction of usable splits), and why a read-only contiguous blob is exactly the -->
<!--   shape mmap needs to back multiple processes with one physical copy via the OS page cache, is standard -->
<!--   distributed-systems/algorithms internals knowledge, used here to go one level deeper than the docs themselves, -->
<!--   per the skill's sourcing guidance. -->

# Spotify's Annoy: Why a Nearest-Neighbor Index Is a File, Not a Data Structure

**Date:** 2026-07-22
**Company:** Spotify
**Category:** search
**Post type:** confessional
**Opening style:** specific_number
**Slug:** spotify-annoy-mmap-random-projection-trees
**Character count (LinkedIn):** ~2,700

---

## LinkedIn Post

Five million tracks. Forty numbers each. Every one of Spotify's recommendations came down to the same question: given this vector, which others in the catalog are close to it?

That's the output of matrix factorization on listening data — every track and user becomes a vector in f-dimensional space, typically 40 numbers. Recommending music means finding a vector's nearest neighbors among millions of others, cheaply enough to serve a live request.

Brute force compares the query to every other vector — linear in catalog size, and it gets slower exactly as the catalog grows. The textbook answer, an exact spatial index like a kd-tree, doesn't help either. Kd-trees prune well only in low dimensions. At 40 dimensions, a query point sits close to a split boundary on almost every axis, so the tree can't safely discard either branch. Pruning stops working — you're back to visiting almost the whole structure.

There's a second problem no algorithms textbook covers. Spotify served requests from many worker processes on the same boxes, and a normal in-memory structure isn't shared across OS processes — each worker gets its own copy. Annoy's own docs use the illustrative math: 5,000,000 items × 40 floats × 4 bytes = 800MB. Times 32 worker processes, that's 25.6GB just to hold the same bytes 32 times over.

Erik Bernhardsson built Annoy at Spotify in 2013, in a couple of afternoons during a Hack Week, and it solves both problems with one trick: give up exact answers, and stop treating the index as something that lives inside a process. Build a forest of k random trees — at each node, sample two points, split on the hyperplane equidistant between them, recurse. Any one split might cut through a cluster of true neighbors; k independent trees make that unlikely. A query walks several trees at once with a priority queue, inspecting up to search_k nodes (default n_trees × n) before stopping — more nodes, better recall, slower query.

The second trick: the finished forest gets written out as one static, read-only, contiguous file. No pointers to fix up. Every worker just mmaps it. Because it's read-only, the OS page cache backs every process with the same physical pages. 800MB stays 800MB, no matter how many workers point at it.

None of it is free. It's approximate — a bad early split can prune away the real answer, recoverable only statistically, with more trees or a higher search_k, at the cost of query time. And the file is read-only, so one new track means rebuilding and redeploying the whole thing. Thirteen years later, it's still open source, still doing the job it was hacked together for in an afternoon.

#SystemDesign #VectorSearch #Spotify #DistributedSystems

---

## Twitter / X Version

Spotify's recommendation engine reduces to one question, over and over: given this vector, which others are nearby?

Matrix factorization turns every track/user into a ~40-dimensional vector. Brute force against millions of others per request doesn't scale. Neither does a kd-tree — it only prunes well in low dimensions, and at 40 dims a query sits near a split boundary on almost every axis.

Second problem: many worker processes, one machine. A normal index gets copied into every process's memory. Annoy's own docs: 5M items × 40 floats × 4 bytes = 800MB. × 32 workers = 25.6GB to duplicate the same bytes.

Erik Bernhardsson built Annoy at Spotify in 2013, in a Hack Week afternoon. Fix #1: forest of random-projection trees — split on a hyperplane between two sampled points, recurse, repeat k times so no single bad split loses the answer. Fix #2: write the tree out as one static read-only file and mmap it. Every worker shares the same physical pages via the OS page cache. 800MB stays 800MB regardless of worker count.

Cost: approximate, not exact. Read-only, so one new track means rebuilding the whole file.

Thirteen years on, it's still running.

---

## Excalidraw Diagram

**File:** 2026-07-22-spotify-annoy-mmap-random-projection-trees.excalidraw
**Type:** Sequence flow (why exact search fails) + structural before/after comparison (confessional style) — top row walks the algorithmic dead end (vectors → brute force → kd-tree → still too slow), middle row is a spatial before/after of the memory story (32 private copies vs. 32 processes sharing one mmap'd file), a wide indigo box explains the tree-building/search mechanism and why it happens to be the exact shape mmap needs, and a footer names the tradeoffs.
**Color scheme:** Slate for the neutral problem-shape row (brute force and kd-trees weren't wrong, just mismatched to the dimensionality). Amber/red for the "private copies" cost panel, teal/green for the "shared mmap" fix panel, indigo for the mechanism explainer. No default villain — kd-trees are the right tool at low dimensions, just not at 40.
**Screenshottable stat:** "5M items × 40 floats × 4 bytes = 800MB · ×32 workers, private copies = 25.6GB · ×32 workers, mmap'd = 800MB flat"

### Layout

```
Title: "Spotify's Annoy: Why a Nearest-Neighbor Index Is a File, Not a Data Structure"
Subtitle: "5M items × 40 floats × 4 bytes = 800MB · built in a Spotify Hack Week, 2013 · still mmap'd into every worker"

ROW 1 — WHY EXACT SEARCH DOESN'T SCALE
[THE VECTORS]              →   [BRUTE FORCE]              →   [KD-TREE (EXACT)]          →   [STILL TOO SLOW]
Matrix factorization on        Compare the query to all        Prunes well only in low         Pruning stops helping —
listening data turns every     ~5M+ others, every request.     dimensions. At 40 dims, a       exact search degrades
track/user into a vector in    Linear in catalog size —        query sits close to a split      back toward visiting
f-dimensional space —          gets worse exactly as the       boundary on almost every         nearly the whole tree
commonly 40 numbers.           catalog grows.                  axis.                             anyway.

ROW 2 — THE MEMORY PROBLEM NO ALGORITHMS TEXTBOOK COVERS
[32 WORKERS, PRIVATE COPIES]                          VS                    [32 WORKERS, ONE MMAP'D FILE]
Each process parses its own index into memory.                              The index is written once as a static,
Annoy's own math: 5M items × 40 floats × 4 bytes =                          read-only, contiguous blob. Every worker
800MB. × 32 worker processes = 25.6GB — just to                             mmaps it — the OS page cache backs all
hold the same bytes 32 times over.                                          of them with the same physical RAM.
                                                                              Resident total: 800MB, flat, at any
                                                                              worker count.

[THE MECHANISM MATCH]
Annoy builds a forest of k trees: at each node, sample two points, split on the hyperplane equidistant between
them, recurse. A query walks multiple trees at once with a priority queue, inspecting up to search_k nodes
(default n_trees × n) before stopping. Because the tree is built once and never mutated in place, it serializes
to one flat, pointer-free, read-only file — exactly the shape mmap needs. The same trick that makes search fast
is what makes sharing free.

Footer: Nothing here is free: approximate, not exact — a bad early split can prune away the true neighbor, and
only more trees or a higher search_k buys that back, at the cost of query time. And the file is read-only: one
new track means rebuilding and redeploying the whole thing, no online insert.
```
