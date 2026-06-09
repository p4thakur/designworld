---
date: 2026-06-09
company: Slack
category: caching
post_type: contrarian
opening_style: challenge_assumption
slug: slack-flannel-edge-cache
---

**Sources (verified primary):**
- Slack Engineering Blog: https://slack.engineering/flannel-an-application-level-edge-cache-to-make-slack-scale/
- InfoQ "Scaling Slack" (2018): https://www.infoq.com/presentations/slack-scalability-2018/

---

## LinkedIn Post

Everyone assumed Slack's slow startup was a caching problem. It was. But adding Memcache would have made it worse.

When Slack scaled to enterprise workspaces with tens of thousands of users, the client boot payload became enormous. On a 32K-user workspace, your client was pulling down 44 times more data than it needed at startup — just to render the sidebar.

The obvious fix: cache the workspace data in Memcache, like every other team does.

The problem: Slack's QuickSwitcher needs to autocomplete channel and user names from a searchable in-memory index. Memcache is a key-value store. You can't search it. The index doesn't fit the pattern.

So Slack built Flannel — a stateful, per-process edge cache that keeps an in-memory model of every user and channel in a workspace, deployed to 7 edge locations worldwide.

At boot, instead of sending you the full workspace dump, the web tier hands you off to your nearest Flannel. Flannel returns a slimmed-down startup payload. Your client populates the rest on demand as you interact with it.

The results:
- P99 startup latency dropped from 2,000ms to 200ms
- Boot payload on a 1.5K-user team: 7x smaller
- Boot payload on a 32K-user team: 44x smaller
- Fleet-wide: 1.1TB of memory saved across shared object caching

But here's the part that doesn't show up in summaries: Flannel's in-memory index per process was the intentional tradeoff. The "waste" of keeping all workspace data in RAM per Flannel instance — rather than sharing it through a remote cache — was the point. Shared caches can't do full-text search. Local memory can.

What looks like over-engineering is often a consequence of a constraint the simple solution didn't account for. In Slack's case, QuickSwitcher wasn't a feature built on top of the cache. It was the constraint that determined what cache was even possible.

Sometimes the architecture you see isn't what the team wanted. It's what the product forced them to build.

#SystemDesign #SoftwareEngineering #DistributedSystems #Caching

---

## Twitter Version

Everyone assumed Slack's startup was a caching problem.

It was. But adding Memcache would have made it worse.

At 32K users per workspace, your client was loading 44x more data than it needed at boot — just to render the sidebar.

The "obvious" fix: throw Memcache at it.

The problem: QuickSwitcher autocomplete needs a searchable in-memory index. Memcache is a key-value store. You can't search it.

So Slack built Flannel — a stateful, per-process edge cache at 7 edge locations worldwide. Your client boots lean. It fetches the rest on demand.

Results:
• P99 latency: 2,000ms → 200ms
• Boot payload (32K workspace): 44x smaller
• Fleet memory: 1.1TB saved

The "waste" of keeping workspace data in RAM per Flannel process was the point. Local memory can search. Shared caches can't.

The constraint wasn't Slack's scale. It was QuickSwitcher. The product decided the architecture.
