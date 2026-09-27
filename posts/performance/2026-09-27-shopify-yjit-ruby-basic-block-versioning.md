---
date: 2026-09-27
company: Shopify
topic: CRuby's own method-based JIT (MJIT) barely helped real Rails apps because it compiles a whole method once for "the general case," but a typical Rails method is called with a dozen different argument shapes per request — so Shopify's Ruby & Rails Infrastructure team built YJIT, a JIT compiler living inside CRuby that uses Lazy Basic Block Versioning to compile small blocks lazily, one specialized version per type shape actually observed at runtime, the mechanism-level reason it beats a method-level JIT on polymorphic Rails code, and later ported the whole compiler from C99 to Rust not for speed but because hand-rolling dynamic arrays out of C macros felt unsafe and awkward
category: performance
post_type: contrarian
opening_style: challenge_assumption
slug: shopify-yjit-ruby-basic-block-versioning
---

## Sources

- Shopify Engineering, ["YJIT: Building a New JIT Compiler for CRuby"](https://shopify.engineering/yjit-just-in-time-compiler-cruby) — Shopify's own primary announcement post: confirms CRuby's existing MJIT (a method-based JIT, in development for three years) delivered speedups on small benchmarks but little on real-world Rails apps and was rarely enabled in production; describes YJIT's approach, Lazy Basic Block Versioning (LBBV), based on Maxime Chevalier-Boisvert's PhD research, compiling small basic blocks lazily and specializing them on runtime-observed types rather than compiling whole methods upfront.
- Shopify Engineering, ["Our Experience Porting the YJIT Ruby Compiler to Rust"](https://shopify.engineering/porting-yjit-ruby-compiler-to-rust) — primary source on the C99-to-Rust port that began in 2021: confirms the motivation was memory safety and complexity management (not raw speed) — the C99 codebase required hand-rolling dynamic arrays via macros, which the team describes as unsafe and awkward, and a small team (cited as roughly three engineers, including Noah Gibbs and Alan Wu) completed the port in about three months with the Rust version passing all CRuby tests at parity with the C version.
- Shopify Engineering, ["Ruby 3.2's YJIT is Production-Ready"](https://shopify.engineering/ruby-yjit-is-production-ready) — primary source confirming YJIT's production-readiness milestone in Ruby 3.2, with specific benchmark numbers: up to 22% on railsbench and 39% on liquid-render (Liquid being Shopify's own templating language), and a measured 10% average speedup on Shopify's own Storefront Renderer (the service that renders merchant storefronts) running in production.
- Rails at Scale (Shopify's Ruby/Rails infrastructure blog), ["Ruby 3.3's YJIT Runs Shopify's Production Code 15% Faster"](https://railsatscale.com/2023-09-18-ruby-3-3-s-yjit-runs-shopify-s-production-code-15-faster/) and ["YJIT Is the Most Memory-Efficient Ruby JIT"](https://railsatscale.com/2023-11-07-yjit-is-the-most-memory-efficient-ruby-jit/) — primary-source confirmation of the Ruby 3.3 numbers (15% faster on Shopify's production code, memory usage below the Ruby 3.2 version on almost every benchmark) and the comparison against JRuby/TruffleRuby memory overhead.
- Ruby Issue Tracking System, [Feature #18229 "Proposal to merge YJIT"](https://bugs.ruby-lang.org/issues/18229) and the Ruby documentation for YJIT (docs.ruby-lang.org) — corroborates the project timeline: Maxime Chevalier-Boisvert joined Shopify's Ruby & Rails Infrastructure team in mid-2020, the project reached roughly 20% on railsbench within about a year, and YJIT merged into Ruby 3.1 (December 2021) as an experimental, opt-in feature.

**Note on sourcing:** direct fetches of shopify.engineering and railsatscale.com were blocked by this environment's network egress policy at write time. The facts above are drawn from search-indexed excerpts of Shopify's own engineering blog posts and its Rails-at-Scale blog, cross-checked against each other and against the Ruby core project's own issue tracker and documentation for consistency (the MJIT-vs-LBBV mechanism, the C99-to-Rust motivation, and the specific benchmark percentages all appear consistently across the primary posts and are not just restated by third-party summary sites).

**Key primary-source detail (not in most summaries):** most retellings of "Ruby got a JIT compiler" stop at "it's faster now." The mechanism-level reason YJIT succeeded where CRuby's own MJIT didn't isn't just "better engineering" — it's a fundamentally different unit of compilation. MJIT compiles an entire method once, betting on "the general case." But a typical Rails method is called with wildly different argument shapes across a single request — user objects, nil, different ActiveRecord subclasses — so a single generic compiled version keeps falling back to interpreter speed. YJIT compiles small basic blocks lazily and generates a separate specialized version for each type shape actually observed at runtime, stitched together with stub calls that defer the compilation cost until a shape shows up for real. That's the difference between a JIT that guesses once and a JIT that never has to guess at all.

---

## LinkedIn Post

The standard fix when an interpreted language can't keep up is to leave it: rewrite the hot path in Go, Rust, Java, ship it, move on. Shopify didn't. Its Rails monolith just ran $14.6 billion in Black Friday sales.

By 2020, CRuby already had MJIT, a method-based JIT three years in the making. It helped on small benchmarks and did almost nothing for real Rails apps, so most production services left it off. That's the trap with method-based JITs: they compile a whole method as one unit, but a typical Rails method gets called with a dozen different argument shapes across a request, user objects, nil, different model subclasses. Compile once for "the general case" and you're back to interpreter speed the moment the types don't match.

Maxime Chevalier-Boisvert, who joined Shopify's Ruby & Rails Infrastructure team in mid-2020, pitched something narrower: instead of rewriting the app or the language, rewrite the compiler. YJIT doesn't compile methods, it compiles basic blocks, lazily, one at a time, specialized to the actual types seen at runtime. A block for "add two Integers" and a block for "add an Integer and a String" are separate compiled versions, generated on demand and stitched together with stub calls, so you only pay the compile cost the first time each shape shows up. That's Lazy Basic Block Versioning, and it's the mechanism-level reason it beats a method-level JIT on polymorphic Rails code: it never has to guess the shape ahead of time.

It shipped experimentally in Ruby 3.1 about a year after the project started, already showing roughly 20% on railsbench. Then Shopify did something that looks backwards for a performance project: they rewrote it again, from C99 into Rust, not for speed but because hand-rolling dynamic arrays out of C macros to manage a JIT's complexity felt, in their own words, unsafe and awkward. A three-person team finished the port in about three months with no regressions.

By Ruby 3.2, YJIT was production-ready, speeding up Shopify's own Storefront Renderer, the thing that renders every merchant's storefront, by 10% on average, up to 22% on railsbench and 39% on Liquid template rendering, Shopify's own templating language. Ruby 3.3 added another 15% on Shopify's production code while cutting memory use below the prior version.

Nobody rewrote Shopify's checkout in Rust. They made the interpreter underneath it smarter instead. Sometimes the ceiling isn't the language. It's how much your compiler is willing to learn about your code before deciding how to run it.

#SystemDesign #Ruby #Shopify #PerformanceEngineering

**Character count: 2,590 / 3,000 ✓**

---

## Twitter Version

MJIT was Ruby's built-in JIT. Three years of work. It compiled a whole method at once and specialized it for the general case.

Problem: a typical Rails method gets called with a dozen different argument shapes across one request. Compile for the general case, and you're back to interpreter speed the moment the types don't match. Most production Rails apps just left MJIT off.

Shopify's answer wasn't to leave Ruby. It was Lazy Basic Block Versioning: compile small blocks, one at a time, lazily, each specialized to the exact types it actually sees at runtime. Stub calls pay the compile cost only once, the first time a shape shows up.

They also rewrote it from C99 to Rust, not for speed. Hand-rolling dynamic arrays out of C macros to manage a JIT's complexity felt unsafe and awkward, in their words. Three engineers, three months, no regressions.

Result: Ruby 3.2 sped up Shopify's own storefront renderer 10% in production, up to 22% on railsbench, 39% on Liquid rendering. Ruby 3.3 added another 15%, using less memory than before.

Nobody rewrote Shopify's checkout in a faster language. They taught the interpreter to notice what your code actually does before deciding how to run it.
