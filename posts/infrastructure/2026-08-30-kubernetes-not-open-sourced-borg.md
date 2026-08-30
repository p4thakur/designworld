<!-- sources -->
<!-- Primary: -->
<!--   Brendan Burns, Brian Grant, David Oppenheimer, Eric Brewer, John Wilkes, "Borg, Omega, and Kubernetes: -->
<!--   Lessons learned from three container-management systems over a decade," ACM Queue, Vol 14, No 1 (Jan 2016) -->
<!--   https://queue.acm.org/detail.cfm?id=2898444 (also published in Communications of the ACM, May 2016: -->
<!--   https://cacm.acm.org/magazines/2016/5/201605-borg-omega-and-kubernetes/fulltext, and as a Google Research -->
<!--   publication: https://research.google/pubs/borg-omega-and-kubernetes/) -->
<!--   Kubernetes.io official blog, "Borg: The Predecessor to Kubernetes" (April 2015) -->
<!--   https://kubernetes.io/blog/2015/04/borg-predecessor-to-kubernetes/ -->
<!--   Brian Grant (co-author of the ACM Queue paper, Borg and Kubernetes engineer), "The Technical History of -->
<!--   Kubernetes," ITNEXT -->
<!--   https://itnext.io/the-technical-history-of-kubernetes-2fe1988b522a -->
<!--     — direct WebFetch of queue.acm.org and opensourcerers.org both returned EGRESS_BLOCKED under this -->
<!--     session's network policy (same class of gateway-level denial noted on prior posts in this series). -->
<!--     Facts below were cross-checked across multiple independent web-search-result excerpts that directly -->
<!--     quote or closely paraphrase the ACM Queue paper, Google's own Kubernetes.io blog, and Brian Grant's own -->
<!--     technical history (Grant co-authored both), not written from memory. -->
<!-- Corroborating (independent secondary sources, cross-referenced for consistency): -->
<!--   TechCrunch, "As Kubernetes hits 1.0, Google donates technology to newly formed Cloud Native Computing -->
<!--   Foundation" (July 21, 2015) -->
<!--   https://techcrunch.com/2015/07/21/as-kubernetes-hits-1-0-google-donates-technology-to-newly-formed-cloud-native-computing-foundation-with-ibm-intel-twitter-and-others/ -->
<!--   GeekWire, "Kubernetes at 5: Joe Beda, Brendan Burns, and Craig McLuckie on its past, future, and the true -->
<!--   value of open source" (2019) -->
<!--   https://www.geekwire.com/2019/kubernetes-5-joe-beda-brendan-burns-craig-mcluckie-past-future-true-value-open-source/ -->
<!--   The Next Platform, "Ma Bell, Not Google, Creates The Real Open Source Borg" (Oct 2019) -->
<!--   https://www.nextplatform.com/2019/10/24/ma-bell-not-google-creates-the-real-open-source-borg/ -->
<!--   Dejanu Alex, "Borg: Kubernetes' Predecessor" -->
<!--   https://dejanualex.medium.com/borg-kubernetes-predecessor-a1d37d64b53a -->
<!-- Key verifiable details (cross-referenced across independent search excerpts that quote/summarize the ACM -->
<!-- Queue paper, Kubernetes' own blog, and Brian Grant's own writing consistently): -->
<!-- 1. Google ran Borg, a unified internal container-management system, for more than a decade before -->
<!--   Kubernetes existed, managing both long-running services and batch jobs. -->
<!-- 2. Borg's task identity ran through the Borg Naming Service (BNS), backed by Chubby, Google's internal -->
<!--   Paxos-based lock service; other processes resolved a BNS name to an IP:port rather than addressing a -->
<!--   task directly. Borg's storage model assumed Colossus, Google's cluster-wide filesystem. Borg jobs were -->
<!--   specified in BCL (Borg Config Language), itself built on Google's own general configuration language. -->
<!--   None of Chubby, Colossus, or BCL exists outside Google, which is why Borg could not simply be released -->
<!--   as-is. -->
<!-- 3. Kubernetes was written from scratch in Go — a language Borg had never been implemented in (Borg is -->
<!--   C++) — specifically so the new, open system carried no code-level dependency on Borg's internal codebase. -->
<!-- 4. Kubernetes was founded by three Google engineers, Joe Beda, Craig McLuckie, and Brendan Burns, who were -->
<!--   quickly joined by other Google engineers including Brian Grant and Tim Hockin. The project's internal -->
<!--   codename was "Project Seven," a reference to the Star Trek character Seven of Nine, a former Borg drone -->
<!--   — chosen because the founders wanted the project to have an identity independent of Google from the start. -->
<!-- 5. Between Borg and Kubernetes, Google built and ran Omega, an internal experimental scheduler that stored -->
<!--   cluster state in a centralized Paxos-based transaction store, letting multiple independent schedulers read -->
<!--   the whole cluster state and claim resources using optimistic concurrency control instead of funneling -->
<!--   every change through one monolithic master. Several of Omega's ideas, including multiple schedulers, were -->
<!--   eventually folded back into Borg itself. -->
<!-- 6. The same underlying concept was renamed across all three systems: Borg's "alloc" (a reserved block of -->
<!--   resources on a machine that teams pinned bundles of tasks into, commonly a sidecar next to a main task) -->
<!--   became Omega's "SUnit," then Kubernetes' "Pod." -->
<!-- 7. Kubernetes' control-plane design — many small controllers, each watching and reconciling one slice of -->
<!--   state independently — is described by its own creators as a middle ground struck after watching Omega's -->
<!--   shared-state, optimistic-concurrency model handle conflicts well under light contention but grow -->
<!--   increasingly conflict-heavy for tightly coupled jobs at scale. -->
<!-- 8. Kubernetes was announced by Google in 2014. It reached v1.0 on July 21, 2015, the same day Google -->
<!--   donated it to the newly formed Cloud Native Computing Foundation (CNCF), alongside founding members -->
<!--   including IBM, Intel, Twitter, Docker, Red Hat, and others. -->
<!-- Publication: ACM Queue / Communications of the ACM, "Borg, Omega, and Kubernetes: Lessons learned from -->
<!-- three container-management systems over a decade" (Burns, Grant, Oppenheimer, Brewer, Wilkes; Jan/May 2016), -->
<!-- corroborated by Kubernetes' own official blog and Brian Grant's first-person technical history. -->

# Kubernetes Isn't Open-Sourced Borg. It's Google's Third Rewrite Of The Same Idea.

**Date:** 2026-08-30
**Company:** Google
**Category:** infrastructure
**Post type:** contrarian
**Opening style:** challenge_assumption
**Slug:** kubernetes-not-open-sourced-borg
**Character count (LinkedIn):** ~2241

---

## LinkedIn Post

Everyone repeats the same line about Kubernetes: Google took its internal weapon, Borg, and open-sourced it. That's not what happened.

Borg's identity system ran through Chubby, Google's internal lock service — every task got a Borg Naming Service name backed by Chubby, resolved to an IP:port. Its storage assumed Colossus, Google's cluster filesystem. Its job specs were written in BCL, a config language built on Google's own general config language. None of that exists outside Google's walls. You can't tar up Borg and hand it to the public — it stops working the moment you remove the private infrastructure underneath it.

So Google didn't strip Borg down. Three engineers — Joe Beda, Craig McLuckie, and Brendan Burns — wrote something new, in Go, a language Borg had never run in, specifically so the new system carried zero code-level dependency on the old one. Internally it was even codenamed Project Seven, after Star Trek's reformed Borg drone — chosen because the team wanted an identity that didn't have "Google" stapled to it from day one.

What actually survived wasn't code. It was one idea, renamed twice already. Borg had "allocs" — a shared resource wrapper teams pinned sidecar tasks into, next to the thing they actually cared about. Omega, Google's mid-2010s attempt to fix Borg's centralized scheduler with a shared-state store and optimistic concurrency, renamed it "SUnit." Kubernetes renamed it again: Pod. Three systems, one concept, rebuilt from scratch each time because each generation disagreed with the last about who gets to hold the lock on shared state.

That's the real difference hiding under the rename. Borg leaned on one mostly-centralized master. Kubernetes runs on small controllers, each watching one slice of state and reconciling it independently — a design earned by watching Omega's optimistic-concurrency model fight itself under contention, not copied from a system that already worked.

The "open-sourced Borg" story is the tidier one for a conference stage. The real one is less flattering and more useful: Kubernetes is Google's third attempt at the same problem, cleaned up for people who don't have Chubby.

#Kubernetes #SystemDesign #DistributedSystems #Infrastructure

---

## Twitter / X Version

1/ Everyone repeats the same line: Kubernetes is Google open-sourcing its internal weapon, Borg. That's not what happened.

2/ Borg's identity system ran through Chubby, Google's lock service. Its storage assumed Colossus, Google's cluster filesystem. Job specs were written in BCL, Google's own config language. None of that exists outside Google. You can't tar up Borg and ship it.

3/ So Google didn't strip Borg down — it wrote something new. Three engineers (Beda, McLuckie, Burns) built Kubernetes in Go, a language Borg had never touched, specifically to keep zero code-level tie to the old system. Internal codename: Project Seven, after Star Trek's reformed Borg drone.

4/ What survived wasn't code. It was one idea, renamed twice already: Borg's "alloc" (a shared wrapper for pinning sidecar tasks) became Omega's "SUnit," then Kubernetes' "Pod." Three systems, one concept, rebuilt from scratch each time.

5/ Why rebuilt? Borg leaned on one mostly-centralized master. Omega tried a shared-state store with optimistic concurrency and watched it fight itself under contention. Kubernetes' answer: small controllers, each reconciling one slice of state independently.

6/ "Open-sourced Borg" is the tidier story for a conference talk. The real one: Kubernetes is Google's third pass at the same problem, cleaned up for people who don't have Chubby.

---

## Excalidraw Diagram

**File:** 2026-08-30-kubernetes-not-open-sourced-borg.excalidraw
**Type:** Side-by-side architecture comparison — four linked panels (assumption → obstacle → actual rewrite →
what survived), matching the Contrarian post type's recommended "obvious approach vs what they built" layout,
closed out with a timeline band and a principle band.
**Color scheme:** Red for the common assumption, blue for Borg's Google-only dependencies, purple for the
from-scratch rewrite, green for the surviving idea — a four-color set distinct from the red/blue/purple/green
run already used on the prior Netflix post, but reused deliberately here since this post's shape (obvious myth
vs. verified reality) mirrors that one's before/after logic more than it mirrors the slate/rose/cyan/amber or
amber/indigo/teal/violet runs used on the messaging and storage posts before it.
**Screenshottable stat:** "Borg's 'alloc' → Omega's 'SUnit' → Kubernetes' 'Pod' — the same concept, rebuilt
from scratch three times, because each generation disagreed with the last about who gets to hold the lock on
shared state."

### Layout

```
Title: "Kubernetes Isn't Open-Sourced Borg. It's Google's Third Rewrite Of The Same Idea."

[THE ASSUMPTION, x 40-320, red]      ->      [WHY YOU CAN'T JUST SHIP IT, x 355-635, blue]      ->      [THE ACTUAL REWRITE, x 670-950, purple]      ->      [ONE IDEA, THREE NAMES, x 985-1265, green]
"'Google took its                             "Borg's task identity ran                             "3 engineers (Beda,                                  "Borg's 'alloc' (shared
internal weapon, Borg,                        through Chubby (lock                                  McLuckie, Burns) wrote it                           wrapper for sidecar
and open-sourced it.'                         service). Storage                                     from scratch in Go — a                              tasks) became Omega's
The line everyone                             assumed Colossus                                      language Borg never ran                             'SUnit,' then
repeats at conferences                        (cluster filesystem).                                 in — on purpose, for zero                           Kubernetes' 'Pod.' Same
and in blog posts about                       Job specs were written                                code-level tie to Borg.                             concept, rebuilt from
Kubernetes' origin."                          in BCL, Google's own                                  Codename: Project                                   scratch three times."
                                               config language."                                     Seven."

[TIMELINE BAND, full width, slate]
"Borg runs Google's clusters for 10+ years before any of this. Omega (Google's shared-state, optimistic-
concurrency scheduler experiment) is built mid-decade to fix Borg's centralized master, and its ideas get
folded back into Borg. Kubernetes is announced in 2014; it hits v1.0 and is donated to the newly formed Cloud
Native Computing Foundation on the same day — July 21, 2015."

[PRINCIPLE BAND, full width, amber]
"'Open-sourced Borg' is the tidier story for a conference stage. The real one is less flattering and more
useful: Kubernetes is Google's third attempt at the same problem — small controllers reconciling their own
slice of state, instead of one master holding the whole lock — cleaned up for people who don't have Chubby."
```
