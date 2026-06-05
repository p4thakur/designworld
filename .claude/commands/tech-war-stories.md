# System Design Post Writer

A skill for writing LinkedIn and Twitter posts about system design case studies — the kind of post that makes an engineer stop scrolling and actually learn something.

The posts should read like they were written by a staff engineer or architect who actually read the engineering blog, not someone summarizing a summary.

## What this skill produces

For each post, you produce three things:

1. A **LinkedIn post** (under 3,000 characters — aim for 2,000-2,500 for best engagement)
2. A **Twitter version** (shorter, thread-friendly)
3. An **Excalidraw diagram** that visualizes the story (style matches the post type)

## Hard constraints

- **LinkedIn character limit: 3,000 characters maximum** (including spaces, emojis, hashtags). Aim for 2,000-2,500 characters. Always count before finalizing.
- **First 210 characters** are visible before "see more" on desktop (140 on mobile). The opener must hook within this window.
- **Every factual claim** must come from a verified primary source (engineering blog, conference talk, repo). Never write from memory alone.
- **Depth over breadth.** One detail that only appears in the primary source (not in any secondary summary) is worth more than five generic facts. This is what makes the post read like an architect wrote it, not a content creator.

---

## When to use

Trigger this skill when the user wants content about:
- How a specific company scaled something (Discord messages, Netflix caching, Uber queues, etc.)
- System design patterns with real-world examples
- Database migrations or architectural decisions at tech companies
- Any content that pulls from the [awesome-scalability repo](https://github.com/binhnguyennus/awesome-scalability)

---

## The workflow

Follow these steps in order.

### Step 1: Suggest the topic

Propose 3 candidates. Don't ask the user to pick cold.

Before suggesting:

1. **Check `covered.json`** — flat list of topic slugs already posted. Never repeat unless user asks for a different angle.

2. **Check `recent.json`** — last 3 posts (category, post_type, opening_style). Use this to vary all three dimensions.

3. **Vary the category** from recent posts. If the last 2 were databases, suggest caching/messaging/search instead.

4. **Vary the post type** from recent posts. If the last 2 were structured case studies, suggest a confessional or contrarian post instead. (See "Post Types" below.)

5. **Pull from three buckets:**
   - awesome-scalability repo (curated list)
   - Recent engineering blog posts (2024-2026 preferred)
   - Trending topics (recent open-source releases, outage postmortems, migrations)

6. **For each suggestion, include:**
   - One-line description
   - The counterintuitive or interesting angle
   - Category
   - Suggested post type (structured / confessional / narrative / contrarian)

### Step 2: Verify the facts

**Non-negotiable.** Before writing:

- Search for the **primary source** (the actual company engineering blog or conference talk, not a summary site)
- Verify exact numbers (latency, node counts, timelines)
- Find at least **one detail that wouldn't appear in a secondary summary** — this is what makes the post credible. Examples: Netflix's midnight spike was caused by users copying a cron example from the docs. Slack can't use Memcache for Flannel because autocomplete needs a searchable in-memory index. These details only show up when you read the actual blog or watch the actual talk.

### Step 3: Choose the post type and opener

**This is where variation happens.** Don't write every post the same way.

See "Post Types" below for the four available structures. Pick the one that fits the story best, and **check `recent.json`** to make sure you're not repeating the same type or opener style.

### Step 4: Draft the post

Write the post following the chosen post type structure. Keep it under 3,000 characters. Make the first 140 characters hook the reader (mobile "see more" cutoff).

### Step 5: Run the tic check

Before finalizing, compare the draft against `recent.json`:

- **Opener style:** Did the last post also start with a question? A number? A pain point? If so, change it.
- **Post type:** Is this the third structured case study in a row? Consider rewriting as confessional or contrarian.
- **Arc:** Does this post follow the exact same problem-solution-lesson shape as the last one? If so, vary the ending (reflection instead of lesson, open question instead of principle).
- **Length:** Are all recent posts the same length? Vary — some posts should be 250 words, some 400.

If the tic check finds repetition, rewrite the opener and/or restructure before finalizing.

### Step 6: Create the diagram

Use the Excalidraw skill. **The diagram style must match the post type.** See "Diagram Types" below.

### Step 7: Verify character count

Count the LinkedIn post characters. Must be under 3,000. Aim for 2,000-2,500.

### Step 8: Update tracking files

Two files to update — both stay small forever:

1. **`covered.json`** — append one slug for the new topic (e.g. `"stripe-idempotency-keys"`). Never grows past one line per post.
2. **`recent.json`** — prepend a new entry with `{company, category, post_type, opening_style}`. Delete the oldest if list exceeds 3 entries. File stays at 3 entries maximum.

---

## Post Types

### 1. Structured Case Study
**When to use:** A clear migration or architectural decision with before/after numbers.
**Arc:** Problem (with specific numbers) → Root cause → Counterintuitive decision → Results → Lesson
**Ending:** Generalizable principle ("Your database's ceiling is often the runtime beneath it")
**Example:** Discord Cassandra to ScyllaDB, Cloudflare containers to V8 isolates

### 2. Confessional
**When to use:** A company admits a limitation, or a decision that made sense at the time but aged badly.
**Arc:** What worked → Why it stopped working → The realization → What changed → Honest reflection
**Ending:** Reflection or reframe, not a packaged principle ("Sometimes the right fix isn't optimizing the system you have. It's building one where the problem doesn't exist.")
**Tone:** Shorter (250-350 words). Empathy for the original designers. Admits imperfection.
**Example:** Netflix Meson to Maestro (single-leader hit a ceiling, midnight spike was a documentation problem)

### 3. Narrative
**When to use:** A story with a tension that unfolds over time, or a bug/incident with layers.
**Arc:** Tension → Original design → Problem discovered → Architectural shift → Ongoing complexity
**Ending:** No forced lesson. Can end with "No one was wrong" or "The tradeoffs don't disappear, they move." Let readers extract their own takeaway.
**Tone:** Medium-long (350-450 words). Story-first. Shows the mess.
**Example:** Slack's message ordering bug (broadcast-first to persist-first, crash window, second-order ordering problems)

### 4. Contrarian
**When to use:** A company rejected the "obvious" approach, or common engineering wisdom is wrong in a specific context.
**Arc:** Challenge the assumption → Show why the obvious fix doesn't work → The contrarian move → Why we default to the wrong thing → The real cost
**Ending:** Punchy judgment ("Sometimes the right architecture is the complicated one. Not because it's clever. But because the simple one has a fundamental misalignment with the problem's shape.")
**Tone:** Opinionated. Shorter paragraphs. Pushes back on defaults.
**Example:** Slack's Flannel (loading everything at boot was elegant but wrong at 366K users)

---

## Opener Bank

Never use the same opener type twice in a row. Check `opening_style` in the last 2-3 history entries.

| Opener Type | Example | Best For |
|-------------|---------|----------|
| **Cold fact** | "Netflix's workflow orchestrator ran 500,000 jobs a day. Then it started choking every night at midnight." | Confessional, structured |
| **Shared pain point** | "Every serverless platform has the same problem: cold starts." | Structured, contrarian |
| **Challenge assumption** | "Everyone said Slack's startup sequence was efficient." | Contrarian |
| **Specific number that doesn't add up** | "Slack's largest workspace has 366,000 users. The boot payload was over 100MB." | Contrarian, narrative |
| **Mid-scene drop** | "Slack's original message send flow had a design flaw that took years to fix." | Narrative |
| **The decision** | "Cloudflare looked at this problem and made an unusual call: don't use containers at all." | Structured |

---

## Writing Style

**Prose, not bullets.** Short paragraphs. 2-4 sentences each.

**No filler.** Cut "In today's world of distributed systems..." Just make the point.

**Active voice.** "Discord migrated" not "The migration was performed."

**Specific over general.** "72 nodes" not "fewer nodes." "15ms p99" not "faster."

**Sound like a person.** Occasional opinion is good ("This is a pattern I see constantly"). Empathy for original designers. No textbook voice.

**Vary the energy.** Some posts are measured and reflective. Some are punchy and opinionated. Match the tone to the post type.

---

## Diagram Types

**Do NOT use the same diagram layout for every post.** Match the diagram to the post type and story shape.

### For Structured Case Study:
- **Before/after comparison** or **migration timeline** (horizontal flow)
- Show the journey with specific numbers at each stage

### For Confessional:
- **Timeline** showing how the system evolved over years (2016: worked → 2020: cracks → 2022: rebuilt)
- **Bar chart or spike visualization** showing the specific problem (e.g., midnight traffic spike)
- Focus on the *human cause*, not just architecture boxes

### For Narrative:
- **Sequence flow** showing how a request moves through the system
- Highlight **where the failure happens** (crash window, ordering bug)
- Show before/after flows side by side

### For Contrarian:
- **Scaling curve** showing how a metric grows with usage (payload size vs team size)
- **Side-by-side architecture** showing "obvious" approach vs what they built
- Include the specific numbers that make someone stop scrolling

### General diagram rules:

- **Don't use the same color scheme every time.** Red=bad, green=good is fine once. Vary colors to match the story. Sometimes the "old" system wasn't bad — it was right for its time.
- **Include at least one number or specific detail** in the diagram that makes it worth screenshotting on its own.
- **Keep it readable** at LinkedIn preview size. Max ~12 elements. If it's busier, simplify.
- **Vary the visual form.** Rotate between: timeline, sequence flow, scaling curve, comparison matrix, architecture snapshot. Don't do the same layout twice in a row.

---

## Tracking Posts

Two files. Both stay small forever.

### `covered.json` — deduplication

Flat list of topic slugs. One line per post. Only thing needed to answer "has this been done?"

```json
{
  "topics": [
    "discord-cassandra-to-scylladb",
    "shopify-pods-architecture",
    "stripe-idempotency-keys"
  ]
}
```

**At the start of every run:** read this list. If a candidate topic slug matches (or is clearly the same story), skip it.
**After writing:** append one slug for the new post. That's it.

Slug format: `company-short-topic-description` in kebab-case, 3-6 words.

### `recent.json` — tic check

Last 3 posts only. Prepend new entry, drop the oldest. Never more than 3 entries.

```json
{
  "recent": [
    {
      "company": "Uber",
      "category": "stability",
      "post_type": "contrarian",
      "opening_style": "challenge_assumption"
    },
    {
      "company": "Airbnb",
      "category": "messaging",
      "post_type": "confessional",
      "opening_style": "cold_fact"
    },
    {
      "company": "Netflix",
      "category": "availability",
      "post_type": "narrative",
      "opening_style": "mid_scene"
    }
  ]
}
```

**At the start of every run:** read this to see what post types and opener styles were used recently. Vary all dimensions.
**After writing:** prepend new entry `{company, category, post_type, opening_style}`, delete entry at index 3 if it exists.

### Categories to rotate

databases, caching, messaging, microservices, search, availability, performance, stability, storage, real-time systems, infrastructure/serverless

If 2 in a row from same category, strongly prefer a different one.

---

## The Twitter version

Same story, compressed. 3-6 short paragraphs. Keeps the hook front and center. Has its own rhythm — not just the LinkedIn version chopped up.

---

## Checklist before finalizing

- [ ] Checked `covered.json` — topic slug not already listed
- [ ] Every specific number came from a verified primary source
- [ ] Found at least one detail that only appears in the primary source (not summaries)
- [ ] Sources listed at top of output file (not in the post itself)
- [ ] **Tic check passed:** opener, post type, arc, and length differ from last 2-3 posts
- [ ] **Character count under 3,000** (aim 2,000-2,500)
- [ ] First 140 characters hook the reader (mobile cutoff)
- [ ] Post type matches the story shape
- [ ] Diagram style matches the post type (not the same layout as last time)
- [ ] Diagram contains at least one screenshottable number/detail
- [ ] Twitter version exists with its own rhythm
- [ ] Hashtags: 2-4, relevant
- [ ] **`covered.json`** updated — new slug appended
- [ ] **`recent.json`** updated — new entry prepended, oldest dropped if list exceeds 3

---

## What NOT to do

- Don't write from memory. Always verify with the primary source.
- Don't use vague numbers ("millions of users", "very fast"). Get specifics.
- Don't use the same post structure every time. Rotate between the 4 types.
- Don't start every post with "Ever wonder..." or any repeated opener. Check history.
- Don't force a lesson on every post. Confessional and narrative posts can end with reflection.
- Don't use the same diagram layout every time. Match it to the post type.
- Don't use red=bad green=good colors on every diagram. Vary the palette.
- Don't end with a generic CTA ("What do you think?"). End with substance.
- Don't exceed 3,000 characters. Count before finalizing.
- Don't skip the diagram. The visual is what makes people stop scrolling.
- Don't use heavy formatting (headers, lots of bullets). Use prose.
- Don't pitch the post as "Here are 10 things..." Listicle posts feel cheap.
- Don't sound like a template. Sound like one person writing about different topics in different moods.
