# GitHub's Code Search: How Blackbird Replaced Elasticsearch at 53 Billion Files

**Date:** 2026-06-19  
**Category:** search  
**Post type:** narrative  
**Opening style:** mid_scene  
**Slug:** `github-code-search-blackbird-elasticsearch`

## Sources

- [The technology behind GitHub's new code search](https://github.blog/2023-02-06-the-technology-behind-githubs-new-code-search/) — primary source (GitHub Engineering Blog, Feb 2023)
- [A brief history of code search at GitHub](https://github.blog/2021-12-15-a-brief-history-of-code-search-at-github/) — historical context

---

## LinkedIn Post

When GitHub first deployed Elasticsearch for code search, it took months to finish indexing 8 million repositories.

That number is worth sitting with. Months. For 8 million repos.

Today GitHub has 200 million. And 53 billion source files. And a p95 search latency the team describes as "well under a second."

The gap between those two realities is a five-year engineering story, and the decision at its center was unusual: don't fix Elasticsearch. Replace it with something GitHub wrote from scratch, in Rust, specifically for the problem of code.

They called it Blackbird.

The core insight that makes Blackbird work isn't about query speed or index format. It's about what you shard on. Elasticsearch shards by repository. Blackbird shards by Git blob object ID.

That's a subtle shift with a large consequence. If the same file exists in a thousand forks — which on GitHub it almost certainly does — Elasticsearch indexes it a thousand times. Blackbird indexes it once. The same deduplication that Git uses to store code efficiently, Blackbird uses to search it.

The engineers also had to confront an uncomfortable truth about general-purpose search engines: they optimize for recall over precision. Web search wants to show you something relevant even when it's not an exact match. Code search has the opposite problem. When you search for `getUser(`, you want `getUser(`. Not `getUserById(`, not `GetUser(`, not a comment mentioning it.

No off-the-shelf solution got this right at GitHub's scale.

The result: a cluster running 5,184 vCPUs, 40TB of RAM, and 1.25PB of storage. It handles 200 requests per second on average, indexes 120,000 documents per second, and delivers most search results in a few hundred milliseconds.

Compared to the 0.01 queries per second that ripgrep can sustain over the same corpus, Blackbird handles 640 per second.

That's not an optimization. That's a different category of solution.

No one was wrong to try Elasticsearch. It was the right call when GitHub had 8 million repos. The problem isn't that general-purpose tools fail. It's that they fail at a specific size — and by then, the corpus is already too big to rebuild with anything slow.

The tradeoffs didn't disappear. They moved into the infrastructure budget.

#SystemDesign #SoftwareEngineering #GitHub #SearchEngineering

---

## Twitter Version

GitHub's Elasticsearch took months to index 8 million repositories.

They now have 200 million. And 53 billion files.

The answer wasn't scaling Elasticsearch. It was replacing it.

—

The key decision in Blackbird (GitHub's custom Rust search engine):

Don't shard by repository. Shard by Git blob SHA.

If the same file lives in 1,000 forks, Elasticsearch indexes it 1,000 times. Blackbird indexes it once — the same trick Git already uses for storage.

—

General search optimizes for recall. Code search needs exact match.

When you search for `getUser(` you want that string exactly — not `GetUser(`, not `getUserById(`, not a comment that mentions it.

No off-the-shelf tool handled this at 53 billion files.

—

What "getting it right" costs:

5,184 vCPUs · 40TB RAM · 1.25PB storage

Throughput: 640 queries/sec
(ripgrep over the same corpus: 0.01 qps)

—

No one was wrong to use Elasticsearch at 8 million repos. It was the right call.

The problem is it fails at a specific size — and by then you're already too big to rebuild with anything slow.

The tradeoffs don't disappear. They move to the infrastructure budget.
