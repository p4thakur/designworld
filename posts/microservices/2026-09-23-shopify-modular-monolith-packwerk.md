---
date: 2026-09-23
company: Shopify
topic: While the industry consensus in 2019 was "decompose monoliths into microservices," Shopify deliberately kept Shopify Core as a single Rails application on a single database -- because splitting the data model would turn in-process lookups (shop config, catalog, inventory, checkout) into network calls with their own latency and failure modes. Instead they built Packwerk, a static analyzer enforcing component boundaries inside the monolith, and their own retrospective admits the "easier" half of that tool (privacy checks) became the default effort while the harder half (real dependency isolation) lagged -- and the resulting tech debt still isn't paid off years later.
category: microservices
post_type: contrarian
opening_style: challenge_assumption
slug: shopify-modular-monolith-packwerk
---

## Sources

- Shopify Engineering: ["Deconstructing the Monolith: Designing Software that Maximizes Developer Productivity"](https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity) (Feb 21, 2019) -- primary source for the decision to build a modular monolith instead of microservices: the single-database rationale (data accessibility without network hops), the multi-pipeline/infrastructure overhead microservices would add, and the original component model.
- Shopify Engineering: ["Under Deconstruction: The State of Shopify's Monolith"](https://shopify.engineering/shopify-monolith) (Sep 16, 2020) -- 18-months-later follow-up with the concrete numbers: 2.8 million lines of Ruby, 500,000+ commits, "Shopify Core" as one Rails app internally split into (at time of writing) 37 components mapped to business domains (Shop, Product Catalog, Checkout, Payments, Fulfillment, etc.), Packwerk enforced on roughly a third of components, and the "majestic monolith" framing.
- Shopify Engineering / Rails at Scale: ["A Packwerk Retrospective"](https://shopify.engineering/a-packwerk-retrospective) (Jan 26, 2024) -- the primary-source detail most summaries skip: Packwerk enforces two distinct checks (dependency violations and privacy violations), privacy checking was never intended to be the tool's main feature but was easier to implement so effort gravitated there, and Shopify's own admission that "the technical debt introduced from privacy checking is still a long way from being paid off."
- `Shopify/packwerk` GitHub README and `RESOLVING_VIOLATIONS.md` -- corroborates the dependency-vs-privacy violation mechanics and Sorbet-based constant/type analysis described above.

**Note on sourcing:** Direct fetch of shopify.engineering, engineering.fyi, and other mirrors was blocked by this environment's network egress policy at write time. The facts above are drawn from search-indexed excerpts of the three Shopify Engineering posts themselves (the 2.8M-line/500K-commit/37-component figures, the single-database rationale, and the Packwerk privacy-debt admission all appear as direct quoted/paraphrased content from those posts in the indexed excerpts), cross-checked across multiple independent secondary write-ups (Milan Milanović's newsletter, ByteByteGo, InfoQ's 2019 coverage) that describe the same architecture and numbers consistently.

**Key primary-source detail (not in most summaries):** Most retellings of "Shopify didn't do microservices" stop at "they built a modular monolith with Packwerk." What Shopify's own 2024 retrospective actually admits is more interesting: Packwerk was built to enforce two kinds of boundaries, dependency violations (do you declare what you depend on?) and privacy violations (do you expose only your public API?). Privacy checking was never meant to be the main feature -- it was just simpler to implement, closely mirroring Ruby's existing public/private method concept. So that's where adoption and engineering effort concentrated. Years later, Shopify states plainly that the technical debt from privacy checking is still far from paid off, while the actually-hard problem -- real dependency isolation across the monolith -- lagged behind the easier, more visible win.

---

## LinkedIn Post

By 2019, "monolith" was basically a slur at tech conferences. The accepted move was obvious: break it up, give each service its own database, let teams ship independently. Shopify had a Rails codebase with 2.8 million lines of Ruby and 500,000 commits behind it — and did the opposite on purpose.

The obvious fix breaks down on a boring detail: money and latency. A single storefront request at Shopify touches shop config, product catalog, inventory, and checkout in one transaction. Split those into services and every one of those lookups becomes a network call — its own latency budget, its own failure mode, its own retry logic. During Black Friday, when Shopify moves tens of terabytes of data a minute, that tradeoff isn't academic.

So the contrarian move: one Rails app, one database, one deploy pipeline — the exact opposite of the decade's conventional wisdom — but with tooling that fakes the isolation microservices would have given for free. They built Packwerk, a static analyzer that scans Ruby constant references and flags when one of the monolith's 37 components reaches into another's internals without declaring the dependency.

Here's what doesn't make it into most case studies. Packwerk ships two kinds of checks: dependency violations and privacy violations. Privacy — marking which constants a component exposes — was never meant to be the main feature. It was just easier to build than real dependency enforcement, so that's where engineering effort gravitated. Years later, Shopify's own retrospective admits the technical debt from privacy checking still isn't close to paid off, while the harder problem it was supposed to be a stepping stone toward — actual dependency isolation — lagged behind.

We reach for microservices because a monolith's pain is visible on day one: slow test suites, scary deploys, merge conflicts. Premature service decomposition's pain shows up eighteen months later, disguised as a distributed systems problem instead of what it actually is: a database you split too early.

Shopify's bet was never "monoliths are good." It was that the cost of fragmenting your data model early outweighs the cost of a big codebase — and no amount of Kubernetes fixes a bad boundary.

#SystemDesign #SoftwareArchitecture #Microservices #Engineering

**Character count: 2,291 / 3,000 ✓**
**First ~145 chars (mobile hook):** "By 2019, "monolith" was basically a slur at tech conferences. The accepted move was obvious: break it up, give each service its own..." ✓

---

## Twitter / X Thread

1/ Everyone agreed monoliths didn't scale. Shopify had 2.8M lines of Ruby, 500K commits — and spent years making that codebase harder to break apart. On purpose.

2/ Why: a single storefront request touches shop config, catalog, inventory, and checkout in one transaction. Split into services and each becomes a network call. At Black Friday scale (tens of TB/min), that's not free.

3/ So: one Rails app, one DB, one deploy pipeline. But they built Packwerk — a static analyzer that flags when any of the monolith's 37 components reaches into another's internals without declaring it.

4/ The part most retellings skip: Packwerk checks two things — dependencies and privacy. Privacy (marking what's public) was never meant to be the main feature. It was just easier to ship. Years later, Shopify admits that tech debt still isn't paid off.

5/ Microservices pain is invisible until month 18. Monolith pain is visible on day one — slow tests, scary deploys. We optimize for the visible pain, not the real cost.

6/ Shopify's bet: fragmenting your data model too early costs more than a big codebase does. No amount of Kubernetes fixes a bad boundary.

---

## Diagram

See: `2026-09-23-shopify-modular-monolith-packwerk.excalidraw`

Type: Side-by-side architecture snapshot (contrarian style) — left block shows the "obvious playbook" (four services, each with its own database, connected by network-call arrows, with a callout on per-call latency/failure cost); right block shows what Shopify actually built (one Rails monolith box containing a Packwerk-bounded component group and a single shared database, connected by an in-process call, with a callout on zero network hops). A plum callout box below calls out the Packwerk privacy-debt admission (the detail most retellings skip), and a slate numbers banner holds the screenshottable stats.
Color scheme: steel blue for the "conventional" microservices side (not wrong, just the default everyone reaches for), mustard/amber for Shopify's actual modular-monolith architecture, muted plum isolated to the "debt still unpaid" callout, and neutral slate for the numbers banner — deliberately avoids the red/violet palette used in the prior (storage) post and the red=bad/green=good default.
Key screenshottable numbers: 2.8 million lines of Ruby, 500,000+ commits, 37 components, tens of terabytes of data moved per minute on Black Friday — on one database.
