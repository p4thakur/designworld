---
date: 2026-11-02
company: Apache Lucene
topic: TieredMergePolicy - deletesPctAllowed=20 means up to a fifth of an index's doc-id space can be dead docs, and the merge policy refuses merges that don't grow the biggest segment by 50% to avoid O(N^2) rewriting.
category: search
post_type: structured
opening_style: specific_number
slug: lucene-tieredmergepolicy-deletes-pct-allowed
---

## Sources

- GitHub, [apache/lucene - TieredMergePolicy.java](https://github.com/apache/lucene/blob/main/lucene/core/src/java/org/apache/lucene/index/TieredMergePolicy.java) - primary: defaults (maxMergedSegment 5GB, floorSegment 16MB, segsPerTier 8.0, deletesPctAllowed 20.0), merge scoring (skew, size^0.05, nonDelRatio^2), the 1.5x growth rule and its comment, and the "dark forest" javadoc for values below 5%.

**Key primary-source detail:** an in-code comment explains that merges whose output is not at least 50% larger than the biggest input are skipped, because otherwise the policy "could run into pathological O(N^2) merging where merges keep rewriting again and again the biggest input segment". The javadoc also warns that deletesPctAllowed below 5% leads to "singleton merges" and calls it a "dark forest".

**Note on sourcing:** only GitHub-hosted content was reachable from this environment. Elastic/Lucene blog posts were not. Defaults are from the current main branch and have changed across Lucene versions (older docs cite 10 segments per tier). No measured disk-usage numbers are cited; the 25% figure is arithmetic on the documented 20% definition.

---

## LinkedIn Post

By default, up to 20% of a Lucene index's document slots can be dead documents, and the merge policy will not lift a finger about it.

That is deletesPctAllowed in TieredMergePolicy, set to 20.0. The javadoc defines the denominator as active plus deleted docs. So at the limit, deleted docs equal a quarter of the live ones. On a 5GB segment, the default maximum, that is roughly a gigabyte of rows nobody can see but every query still skips over.

Why allow it? Because the alternative costs more. Lucene never edits a segment. An update marks the old doc deleted and writes a new one elsewhere. Reclaiming space means rewriting whole segments, and the javadoc is blunt about the price: lowering the threshold means merges are called more often and write amplification goes up. Below 5%, it says, indexing can continuously merge nearly all segments and fall into "degenerate merge selection like singleton merges". Their words for this territory: a dark forest.

The same file shows how much effort goes into not rewriting data twice. Each candidate merge gets a score. Skew (biggest input divided by total output) is favored strongly, so lopsided merges lose. Output size is penalized gently, with an exponent of 0.05, because a steeper one would push the policy into bad small merges to dodge big ones. Merges that reclaim deletes get squared credit.

Then there is the rule that explains the most. A natural merge is skipped unless its output is at least 50% larger than the biggest input. The comment gives the reason: otherwise merges keep rewriting the biggest segment into one that is barely bigger, an O(N^2) pattern. The single exception is when the biggest segment is already past the 20% deletes line.

So a segment with 19% deletes can sit there indefinitely, and that is the design working. The index is trading disk and some query work for a bounded write amplification.

Floor size matters here too: segments under 16MB are treated as 16MB when scoring, so a flood of tiny flushes does not each get its own tier.

The takeaway for anyone running update-heavy search: the disk bill that looks like waste is the policy's budget for not rewriting your index in a loop. Change the 20 only after measuring what the rewrite will cost.

#Lucene #Elasticsearch #SearchEngineering #SystemDesign

---

## Twitter Version

Lucene's default merge policy lets 20% of an index's doc slots be deleted docs. On purpose.

TieredMergePolicy: deletesPctAllowed=20.0. Updates mark old docs deleted and write new ones, so space only comes back by rewriting segments. The javadoc warns that going below 5% means near-constant merging, "singleton merges", a "dark forest".

Another rule: a merge is skipped unless its output is 50% larger than the biggest input. The code comment: otherwise you get O(N^2) rewriting of the biggest segment.

Wasted disk? It's the budget for not rewriting your index forever.

---

## Diagram

See `2026-11-02-lucene-tieredmergepolicy-deletes-pct-allowed.excalidraw` (side-by-side: 5GB segment at 20% deletes left alone vs. a threshold under 5% that triggers repeated rewrites).
