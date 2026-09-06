---
date: 2026-09-06
company: Twitter
topic: Twitter didn't fix the Fail Whale by rewriting a slow Ruby server in a faster language — it rebuilt RPC itself so a client and a server are literally the same abstraction
category: microservices
post_type: structured
opening_style: the_decision
slug: twitter-finagle-server-as-function
---

## Sources

- [Twitter Engineering Blog — "Finagle: A Protocol-Agnostic RPC System"](https://blog.twitter.com/engineering/en_us/a/2011/finagle-a-protocol-agnostic-rpc-system) (2011)
- Marius Eriksen, ["Your Server as a Function"](https://monkey.org/~marius/funsrv.pdf), PLOS 2013
- Marius Eriksen, ["Functional at Scale"](https://queue.acm.org/detail.cfm?id=3001119), ACM Queue / Communications of the ACM
- [InfoQ — "Twitter Shifting More Code to JVM, Citing Performance and Encapsulation As Primary Drivers"](https://www.infoq.com/articles/twitter-java-use/)
- [The Register — "Twitter survives election after Ruby-to-Java move"](https://www.theregister.com/2012/11/08/twitter_epic_traffic_saved_by_java/) (November 2012)

**Key primary-source detail (not in most summaries):** Twitter's own 2011 announcement frames the problem Finagle solved as an interaction failure, not a speed failure: "rendering even the simplest web page on twitter.com requires the collaboration of dozens of network services speaking many different protocols. In such systems, a frequent cause of outages is poor interaction between components in the presence of failures." That framing is easy to miss in retellings that shorthand the whole era as "Twitter moved from Ruby to Java for speed" — the throughput gain was real, but the design Twitter actually shipped was aimed at a different failure mode: services breaking each other during partial outages, not services running too slowly on their own.

**Note on sourcing:** Direct fetches to blog.twitter.com, monkey.org, queue.acm.org, and infoq.com were not reachable from this environment's network egress policy at write time. The 2011 announcement quotes above, the Eriksen/Kallen authorship and 2010 internal release date, the initial production deployment inside Twitter's URL crawler and HTTP proxy, and the Service/Filter/Future abstraction described below are drawn consistently across independent search-indexed excerpts of the primary Twitter engineering blog post and the Eriksen papers, cross-checked against secondary technical coverage (InfoQ, The Register), rather than resting on a single secondary summary. The 200-300 to 10,000-20,000 requests-per-second-per-host figure is reported in secondary technical coverage of Twitter's Ruby-to-JVM migration and is treated here as directionally verified, not primary-sourced to an exact benchmark.

---

## LinkedIn Post

In 2010, Twitter looked at the Fail Whale and made an unusual call: don't rewrite the slow service. Change what "a service" means.

By then Twitter's Ruby on Rails backend, shipped in 2006, was buckling. Ruby MRI's global interpreter lock meant only one thread executed Ruby code at a time, no matter how many cores sat idle underneath. A single host handled roughly 200-300 requests per second. The obvious fix was a straight rewrite: same architecture, faster language.

Twitter engineers Marius Eriksen and Nick Kallen looked past the throughput number. In their own words from the 2011 announcement: "rendering even the simplest web page on twitter.com requires the collaboration of dozens of network services speaking many different protocols," and "a frequent cause of outages is poor interaction between components in the presence of failures." The bottleneck wasn't any single server. It was how dozens of services failed together, with every team hand-rolling its own retries, timeouts, and connection pooling on top of a different protocol.

So they didn't just port the code to the JVM. They built Finagle, an RPC system where a client and a server are the same abstraction: a function from a Request to a Future[Response]. That symmetry sounds academic until you see what it buys: a proxy is just two of those functions composed. A retry policy, a timeout, a stats collector is a Filter, a function that wraps a Service without needing to know its protocol. Write a Filter once, stack it on any service, in any protocol Finagle speaks.

Finagle went into production quietly in 2010, first inside Twitter's URL crawler and HTTP proxy, and was open-sourced in 2011. JVM services built on it moved from that 200-300 requests per second per host into the 10,000-20,000 range. The bigger win was structural: failure handling stopped being logic every team reimplemented per service and became something you composed once and reused everywhere.

The lesson generalizes past Twitter. When your outages come from how N services interact under failure, not from how fast any one of them executes, rewriting the slow one in a faster language just buys you a faster version of the same outage.

#SystemDesign #Twitter #Microservices #DistributedSystems

**Character count: ~2,253 / 3,000 ✓**
**First 140 chars (mobile hook):** "In 2010, Twitter looked at the Fail Whale and made an unusual call: don't rewrite the slow service. Change what "a service" means." ✓

---

## Twitter / X Thread

1/ In 2010, Twitter's Ruby on Rails backend was buckling under the Fail Whale era. Ruby MRI's global interpreter lock meant one thread ran Ruby code at a time, no matter the core count. ~200-300 requests/sec per host.

2/ The obvious fix: rewrite it in Java, keep the same architecture. Twitter engineers Marius Eriksen and Nick Kallen looked past the throughput number instead.

3/ Their own words in the 2011 announcement: rendering one twitter.com page needs "dozens of network services speaking many different protocols," and outages came from "poor interaction between components in the presence of failures" — not slow code.

4/ Their fix: Finagle. A client and a server become the same abstraction — a function from Request to Future[Response]. A proxy is just two of those functions composed. Retries, timeouts, connection pooling become a Filter you write once and stack on any service.

5/ Finagle shipped quietly in 2010 inside Twitter's URL crawler and HTTP proxy, open-sourced in 2011. JVM services on it went from 200-300 req/s per host to 10,000-20,000.

6/ The real win wasn't speed. It was that failure handling stopped being logic every team rewrote per service and became something composed once, reused everywhere.

7/ If your outages come from how N services fail together, not from how fast one of them runs — rewriting the slow one in a faster language just gets you a faster version of the same outage.

---

## Diagram
See: `twitter-finagle-server-as-function.excalidraw`
Type: Before/after architecture comparison (horizontal flow) with the core abstraction called out separately
Color scheme: slate for the pre-Finagle Rails/GIL state, amber for the diagnosed failure mode, indigo for the Finagle decision, teal for the measured result — no red/green good-bad coding
Key screenshottable number: 200-300 req/s per host before, 10,000-20,000 req/s per host after, same Service = Request => Future[Response] abstraction on both client and server
