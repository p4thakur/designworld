# Tech War Stories — Staff Engineer LinkedIn Post Skill

Posts that sound like they were written by one person who has been burned by the thing they're writing about.

## What this skill produces

For each post:
1. LinkedIn post — under 3,000 characters, aim for 1,800–2,400
2. Twitter/X thread — compressed, punchier, its own rhythm
3. Excalidraw diagram — visualizes the "aha" moment
4. Long-form blog post — complete explanation, no gaps

## Hard constraints

- LinkedIn character limit: 3,000 characters maximum. Count before finalizing.
- First 140 characters visible on mobile before "see more". Hook must land here.
- No first person. No "I", no "we", no "our team". Ever. Write as an observer.
- No question hooks. Never open with "Have you ever..." or "Ever wonder why..."
- Specific numbers beat vague claims. "50M rows", "40 minutes", "Postgres 11" beats "large table".
- No listicles. No "5 things you didn't know about X." Prose. Short paragraphs.
- End on substance. Never "what do you think?" or "drop your thoughts below."
- No backticks or markdown formatting in post text.

## Post DNA

Every post has four parts in this order:

### 1. The hook — surprising outcome or broken assumption
One or two lines. Something that makes the reader stop.
- Good: "A schema migration took down writes for 40 minutes. The change was one line."
- Bad: "Have you ever wondered why your database slows down under load?"

The hook is not a setup. It is the surprising thing itself, stated plainly.

### 2. The reveal
What actually happened. Specific. Numbers where possible. The mechanism exposed.

### 3. The reframe
One sentence that makes the whole thing click. This is the line that gets screenshotted.
- Good: "The cost isn't memory per request. It's duration."

### 4. The implication
What changes once you know this. Not a CTA. Just: here is what you will do differently.

---

## Post Types

**Type A — Hidden Cost**
Something assumed to be free or cheap — isn't. Here's what it actually costs.
Tone: Calm, dry. Ending: The cost framed as a tradeoff to know, not avoid.

**Type B — Default Is Wrong**
The obvious choice has a specific failure mode most people hit too late.
Tone: Opinionated. Backed by specifics. Ending: The question that changes the decision.

**Type C — Under the Hood**
When you do X, here is the sequence of things the system actually does.
Tone: Educational but not textbook. Ending: The one detail that explains the surprising behavior.

**Type D — Architecture Decision**
A decision that looks local has system-wide consequences.
Tone: Measured. Ending: The constraint the decision creates downstream.

---

## Writing Style

No first person. Reframe everything:
- Bad: "We had 20 pods each with a pool of 10."
- Good: "20 pods. Each with a connection pool of 10."

Short paragraphs. 2–4 sentences. One idea per paragraph.
Active, declarative sentences. "Postgres rewrote every row." Not "Every row was rewritten."
End paragraphs on strong words. No filler.
Avoid: "game-changing", "deep dive", "unpack", "let's explore", "paradigm"

---

## Diagram Guidance

The diagram shows the hidden mechanism, not the full topic.
- Type A: Side-by-side comparison. Before assumption vs. actual cost. Numbers in boxes.
- Type B: Two paths. "What everyone does" vs. "what actually happens". Annotate failure point.
- Type C: Sequence of steps. Show invisible work. Highlight where surprising thing happens.
- Type D: Fork or decision tree. Show downstream consequences.

Rules:
- Max ~10 elements. Readable at LinkedIn preview size.
- At least one specific number in the diagram worth screenshotting independently.
- No emoji in Excalidraw text.
- Vary diagram form and color scheme across posts.
- Read Excalidraw read_me before drawing every time.

---

## Blog Post Structure

1. **Opening** — the problem stated plainly (1-2 paragraphs)
2. **Background** — what most people know (1-2 paragraphs)
3. **The mechanism** — what actually happens (core section, deep, code examples)
4. **How to detect it** — specific metrics, tools, queries
5. **How to fix it** — concrete steps, real order
6. **The tradeoff** — every fix has a cost, be honest
7. **Closing** — the one sentence that should stick

Blog voice: conversational tech blog. First person allowed. Address the reader directly.
Length: write until concept is fully explained. 800–3000 words. No padding, no premature cuts.

What NOT to do in the blog:
- No "In this post, I will cover..."
- No "As we can see from the above..."
- No hype ("this blew my mind", "game changer")
- No unanswered "but why?" questions

---

## Topic Backlog (100 posts)

Check `post-history.json` before picking. Never repeat a topic.

### Database & Storage
1. Adding more indexes slowed down the writes
2. Cursor pagination breaks on mutable data
3. The migration added a NOT NULL column — locked the table for 40 minutes
4. Soft deletes quietly broke the query planner
5. The read replica wasn't actually reducing load — ORM opened write transactions by default
6. Foreign keys have a runtime cost on every INSERT
7. Long-running transactions and the queue of blocked writers behind them
8. NoSQL didn't remove the schema — it moved it to the application
9. Partial indexes: half the size, same query speed — and most engineers never use them
10. Backfilling a column on a live table — why batching is not optional
11. The hot row problem: one record getting hammered that no shard can fix
12. The migration ran. The rollback didn't.

### Caching
13. Cache stampede: the cache helped until expiry hit
14. The 5% cache miss was the most expensive traffic
15. Caching fixed latency and introduced a consistency bug
16. Redis evicted the wrong keys under memory pressure
17. Write-through cache doubled the write latency
18. Local in-process cache is faster than Redis — and wrong more often across pods

### Networking & Connections
19. DNS resolution isn't always cached the way you think
20. TLS handshake cost disappears in benchmarks and shows up in production
21. TCP TIME_WAIT fills up the port table at high throughput
22. Keep-alive is on by default. It's also misconfigured by default.
23. Nagle's algorithm makes small messages slow
24. The load balancer has a connection limit too

### Async, Queues & Events
25. Making it async didn't make it faster — it hid where it was slow
26. The DLQ was a graveyard — messages expired before anyone investigated
27. At-least-once + no idempotency key = silent double charge
28. The consumer was fast. The acknowledgement was slow. Lag grew anyway.
29. Event ordering isn't guaranteed unless you designed for it
30. Retry storms: correct backoff at one service, wrong at system scale
31. Message size has a cost nobody budgets for
32. Outbox pattern: why you can't trust "publish after commit"

### Memory, CPU & Runtime
33. Garbage collection pauses are latency spikes in disguise
34. Memory leak was a growing event listener, not a data structure
35. JSON serialization burned 20% of CPU at scale
36. String interning made the memory profile look clean — until it didn't
37. CPU throttling in containers is not the same as CPU limit
38. The pod was OOM-killed with no graceful shutdown
39. Thread pool size is a hidden throughput ceiling

### APIs & Service Communication
40. The service had 3 downstream calls. One had no timeout. That one took everything down.
41. Circuit breakers don't trigger until it's already too late
42. Timeout cascades: not setting them is worse than wrong values
43. The endpoint returned 200 for every request — including the failed ones
44. API gateway added 8ms to every request before any business logic ran
45. gRPC is faster than REST — until you add a service mesh
46. Response compression has a CPU cost on the server

### Observability & Debugging
47. Metrics looked healthy during the outage — averages hid the tail
48. High cardinality labels broke the metrics system
49. Correlation IDs existed. They weren't propagated across the async boundary.
50. Sampling traces at 1% misses the rare slow request
51. Alert fatigue made the real alert invisible
52. The load test passed. It tested the wrong thing.

### Scaling & Infrastructure
53. Autoscaling reacted to CPU — bottleneck was memory
54. Horizontal scaling hit a vertical limit in the database
55. Provisioned concurrency "solved" Lambda cold starts by making it always-on
56. Rolling deploys caused a mixed-version state nobody planned for
57. The CDN cached a 500 error for 24 hours
58. Pod resource limits set too low caused CFS throttling, not OOM
59. Secrets rotation broke the service — old secret cached in memory

### Security & Auth
60. JWTs don't expire until they expire — revoking requires more than logout
61. bcrypt is intentionally slow — and that's a DoS surface without rate limiting
62. CORS misconfiguration: teams flip to reflecting the Origin header, which is worse
63. Rate limiting at the app layer doesn't protect the app layer

### Concurrency & Race Conditions
64. Check-then-act: the race condition hiding in plain readable logic
65. Optimistic locking failed silently — nobody handled the conflict exception
66. Distributed locks expire while the work is still running
67. Thread-local state leaks between requests in thread-pool servers

### Deployments & Reliability
68. Feature flags reduced risk — until there were 200 of them
69. Health check passed but the service wasn't healthy
70. Graceful shutdown was 30 seconds. The LB drained in 5.
71. Canary was green — the bug caused silent data corruption, not errors

### Data & Consistency
72. Eventual consistency is not "it'll be fine eventually"
73. Timezone handling broke silently at DST rollover
74. Duplicate event processing corrupted the balance
75. Schema migration removed a column still used by the old deploy
76. NOT IN with a subquery returns zero rows when any value is NULL

### Architecture Tradeoffs
77. The monolith wasn't slow — the deploys were slow
78. Shared database between services couples what the architecture separated
79. The abstraction layer added latency you can't measure directly
80. Event sourcing is a read problem dressed up as a write solution
81. CQRS doubled the infrastructure and the eventual consistency bugs
82. "We'll fix it after launch" — and the data model became load-bearing technical debt

### Real-time & Streaming
83. SSE reconnects automatically. WebSocket doesn't.
84. Kafka consumer lag is not the same as Kafka being slow
85. Kafka consumer group rebalance paused all processing
86. Heartbeats on WebSocket aren't optional on mobile

### Engineering & System Thinking
87. The SLA was 99.9%. That's 8.7 hours of downtime per year.
88. Technical debt isn't code quality — it's decision lag
89. The abstraction that made v1 fast made v2 impossible
90. Dependency updates are risk management, not maintenance
91. Staging didn't reproduce the bug — it had 1% of the data
92. The runbook existed. Nobody had run it before the incident.
93. Rewriting the service didn't fix the underlying data model
94. Complexity doesn't announce itself — it accumulates
95. The fastest code is the code that doesn't run
96. The connection pool is a rate limiter — horizontal scaling makes it worse
97. The benchmark showed 2ms. Production showed 200ms. The difference was network hops.
98. The feature shipped. The cleanup ticket never did.
99. Two services, one schema — the microservice boundary was a lie
100. The system was observable. It just wasn't understandable.

---

## Workflow (follow every time)

1. **Pick topic** — check `post-history.json`, never repeat, state number + post type
2. **Verify numbers** — web search if unsure, use "typically" framing if unverifiable
3. **Draft LinkedIn post** — hook → reveal → reframe → implication
4. **Tic check** — different post type from last 2? different hook style? different length?
5. **Create LinkedIn diagram** (Excalidraw) — match type to post type
6. **Write Twitter/X version** — same structure, half the length, own rhythm
7. **Write blog post** — full structure, code examples, expanded diagrams
8. **Count LinkedIn characters** — must be under 3,000
9. **Update post-history.json**

## Push location

Push post files organized by technology/type category:
- `posts/database/` — all Database & Storage topics
- `posts/caching/` — Caching topics
- `posts/networking/` — Networking & Connections
- `posts/async-queues/` — Async, Queues & Events
- `posts/memory-cpu/` — Memory, CPU & Runtime
- `posts/apis/` — APIs & Service Communication
- `posts/observability/` — Observability & Debugging
- `posts/scaling/` — Scaling & Infrastructure
- `posts/security/` — Security & Auth
- `posts/concurrency/` — Concurrency & Race Conditions
- `posts/deployments/` — Deployments & Reliability
- `posts/data-consistency/` — Data & Consistency
- `posts/architecture/` — Architecture Tradeoffs
- `posts/real-time/` — Real-time & Streaming
- `posts/engineering/` — Engineering & System Thinking

Each post folder: `posts/<category>/<NN>-<slug>/`
Files: `linkedin.md`, `twitter.md`, `blog.md`, `diagram.excalidraw`

## Post History Format

```json
{
  "posts": [
    {
      "date": "2026-06-05",
      "number": 1,
      "topic": "Adding more indexes slowed down the writes",
      "bucket": "hidden_cost",
      "post_type": "type_a",
      "hook_style": "surprising_outcome",
      "reframe_line": "Every index is a write tax. The query optimizer sees the benefit. The write path pays every time.",
      "key_numbers": "8,000 → 3,200 inserts/sec, 3 indexes, ~15M rows/day, 60% throughput lost",
      "char_count": 1487,
      "linkedin_filename": "posts/database/01-indexes-write-cost/linkedin.md",
      "blog_filename": "posts/database/01-indexes-write-cost/blog.md"
    }
  ]
}
```

Hook styles to rotate: `surprising_outcome` | `broken_assumption` | `the_number` | `the_decision_that_backfired` | `two_things_that_disagree`

## Checklist before finalizing

LinkedIn post:
- [ ] Topic not in post-history.json
- [ ] Post type varied from last 2 posts
- [ ] Hook style varied from last 2 posts
- [ ] No first person (no I, we, our)
- [ ] Hook is not a question
- [ ] No backticks or markdown formatting in post text
- [ ] All numbers verified or hedged
- [ ] Reframe line is one punchy sentence
- [ ] Ends on substance, not engagement bait
- [ ] No listicle format
- [ ] Character count under 3,000
- [ ] First 140 chars hook the reader
- [ ] LinkedIn diagram matches post type, has one screenshottable number
- [ ] Twitter version written with its own rhythm

Blog post:
- [ ] Opens without "In this post I will..."
- [ ] Background establishes what reader already knows
- [ ] Mechanism answers every "but why?" question
- [ ] Code examples show problem first, then fix
- [ ] Detect section is specific — real metrics, real tools
- [ ] Fix section is actionable — real steps, real order
- [ ] Tradeoff section is honest
- [ ] Closes on the concept, not yourself
- [ ] No unanswered questions remain

Both:
- [ ] post-history.json updated with both filenames
