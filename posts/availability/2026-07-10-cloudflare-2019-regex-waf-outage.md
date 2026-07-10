<!-- sources -->
<!-- Primary: -->
<!--   Cloudflare Blog, "Details of the Cloudflare outage on July 2, 2019" (John Graham-Cumming) -->
<!--   URL: https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/ -->
<!--   Cloudflare Blog, "Cloudflare outage caused by bad software deploy" (initial incident writeup) -->
<!--   URL: https://blog.cloudflare.com/cloudflare-outage/ -->
<!-- Note: direct fetch of blog.cloudflare.com returned HTTP 403 under this session's egress policy (bot -->
<!-- protection). Facts below were cross-checked across multiple independent search-result excerpts that quote -->
<!-- the primary Cloudflare postmortem directly, plus corroborating technical writeups, including: -->
<!--   https://www.theregister.com/2019/07/12/cloudflare_cpu_cockup/ -->
<!--   https://surfingcomplexity.blog/2019/08/02/contributors-mitigators-risks-cloudflare-2019-07-02-outage/ -->
<!--   https://news.ycombinator.com/item?id=20421538 (HN thread discussing the postmortem in detail) -->
<!--   https://postmortems.app/postmortem/a0e252d3-10a6-4345-84c3-f271124e2d7b -->
<!--   https://medium.com/@sohail_saifii/the-regex-pattern-that-brought-down-cloudflare-for-27-minutes-5841b985f45e -->
<!--   https://www.packtpub.com/en-us/learning/tech-news/cloudflare-rca-major-outage-was-a-lot-more-than-a-regular-expression-went-bad -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. July 2, 2019, 13:42 UTC: an engineer deployed a routine WAF rule change (XSS detection) through the -->
<!--    normal path — no staged rollout, pushed to every edge server globally at once, by design, since Cloudflare's -->
<!--    WAF needs to react to live attacks in seconds -->
<!-- 2. 13:45 UTC: first PagerDuty alert for a WAF fault; CPU spiked to near 100% on machines handling -->
<!--    HTTP/HTTPS traffic worldwide -->
<!-- 3. Root cause: the new rule contained a regular expression with nested wildcards (a .* inside another -->
<!--    effective .*) that triggered catastrophic/excessive backtracking on certain inputs instead of failing fast -->
<!-- 4. Contributing factor (the confessional core): weeks earlier, during a WAF refactor whose goal was to make -->
<!--    the WAF use LESS CPU, a protection mechanism meant to catch/limit excessive CPU use by a regex was -->
<!--    mistakenly removed -->
<!-- 5. Other systemic factors per the postmortem: the regex engine in use had no runtime/complexity guarantees; -->
<!--    the test suite had no way to catch excessive CPU consumption in a rule before deploy; the SOP allowed -->
<!--    non-emergency rule changes to go straight to global production without a staged/canary rollout -->
<!-- 6. 14:02 UTC: team isolated the cause and issued a "global kill" — disabling WAF Managed Rules everywhere -->
<!--    at once, the same instant-global-push mechanism that had caused the incident -->
<!-- 7. 14:09 UTC: CPU back to normal, traffic restored — total outage duration 27 minutes (13:42-14:09) -->
<!-- 8. Remediation: switched the regex engine to one with a runtime guarantee (RE2 / Rust regex engine) instead -->
<!--    of a backtracking engine; reinstated the CPU-usage protection; manually audited all ~3,868 existing WAF -->
<!--    Managed Rules for the same failure shape; changed the SOP so routine rule changes get staged rollout like -->
<!--    other software deploys, while retaining a fast path for genuine active-attack emergencies -->

# Cloudflare's Global Kill Switch Was Also the Thing That Broke It

**Date:** 2026-07-10
**Company:** Cloudflare
**Category:** availability
**Post type:** confessional
**Opening style:** specific_number
**Slug:** cloudflare-2019-regex-waf-outage
**Character count (LinkedIn):** ~1,973

---

## LinkedIn Post

One misconfigured regex. 100% CPU across Cloudflare's entire global network. It took 27 minutes to reach for a kill switch nobody had planned to use against themselves.

July 2, 2019, 13:42 UTC. An engineer deploys a routine update to the WAF's XSS-detection rules. Standard process: no staged rollout, no canary — straight to every edge server on the planet at once. That instant global push is the whole point of Cloudflare's WAF. During a real attack, you want a fix live everywhere in seconds, not hours.

Three minutes later, the pages start. CPU is pinned near 100% on the machines serving HTTP and HTTPS traffic worldwide. Inside the new rule sits a regex with nested wildcards — a .* inside another .* — and on the wrong input, instead of failing fast, it backtracks combinatorially.

Here's the part that makes this a confession rather than just a bug: three weeks earlier, in a refactor meant to make the WAF use less CPU, the circuit breaker built to catch exactly this kind of runaway regex had been quietly removed. The optimization deleted its own safety net.

It takes until 14:02 — twenty minutes of pegged CPU — to isolate the cause. The fix is the same mechanism that caused the outage: a global kill of WAF Managed Rules, pushed everywhere instantly. Traffic recovers by 14:09. Twenty-seven minutes, start to finish.

Cloudflare didn't slow the push mechanism down afterward — during a live attack, that speed is the product. Instead they bounded what rides on it: switched the regex engine to one with a runtime guarantee instead of backtracking search, hand-audited all 3,868 existing WAF rules for the same shape of bug, and split routine changes onto a staged rollout while keeping the instant path for genuine emergencies.

They kept the tool that can push a fix everywhere in seconds. They just made sure it could no longer push an unbounded bug everywhere in seconds without anyone noticing first.

#SystemDesign #Cloudflare #WAF #SRE

---

## Twitter / X Version

1/ July 2, 2019, 13:42 UTC: an engineer at Cloudflare deploys a routine WAF rule update for XSS detection. Normal process — straight to every edge server on the planet at once, no staged rollout.

2/ Three minutes later: CPU pinned near 100% on every machine serving HTTP/HTTPS traffic, globally. Inside the new rule: a regex with nested wildcards that backtracks combinatorially on the wrong input instead of failing fast.

3/ The confession: three weeks earlier, a refactor meant to make the WAF use LESS CPU had quietly deleted the circuit breaker built to catch exactly this failure. The optimization removed its own safety net.

4/ 20 minutes of pegged CPU before the team isolates the cause. The fix: the same mechanism that caused it — a global kill of WAF Managed Rules, pushed everywhere instantly. Recovered by 14:09 UTC. 27 minutes, total.

5/ Cloudflare didn't slow the push mechanism down afterward — during a live attack, that speed is the whole point. They bounded what rides on it instead: regex engine with runtime guarantees, all 3,868 existing rules hand-audited, staged rollout for routine changes.

6/ They kept the tool that pushes a fix everywhere in seconds. They made sure it can't push an unbounded bug everywhere in seconds without anyone catching it first.

---

## Excalidraw Diagram

**File:** 2026-07-10-cloudflare-2019-regex-waf-outage.excalidraw
**Type:** Timeline (confessional) — five chronological stages left to right, with the human cause ("3 weeks earlier") placed first in the sequence rather than as a side note, plus a result strip underneath. This deliberately shows the removed safety net as part of the timeline, not an afterthought.
**Color scheme:** Amber for the human decision that removed the safety net (the earned "something's off" color, not full alarm), slate/blue for the routine deploy step, crimson for the CPU-spike moment (used once, the pivotal failure), indigo for the moment the team reaches for the same push mechanism to fix it, teal for recovery, violet for the remediation result. No red/green good/bad pairing — the 13:42 deploy box is neutral slate, not villainized, since the instant-push design is the reasonable, intentional choice that a live-attack WAF requires.
**Screenshottable stat:** "13:42 deploy → 13:45 CPU pinned near 100% worldwide → 14:02 root cause found → 14:09 recovered · 27 minutes total · 3,868 WAF rules hand-audited afterward"

### Layout

```
Title: "Cloudflare's Global Kill Switch Was Also the Thing That Broke It"
Subtitle: "July 2, 2019 · 100% CPU worldwide in 3 minutes · 27-minute outage · fixed by the same mechanism that caused it"

[3 WEEKS EARLIER]         [13:42 UTC]              [13:45 UTC]                [14:02 UTC]              [14:09 UTC]
A WAF refactor meant   →  Engineer deploys a    →  CPU pinned near 100%   →  Root cause isolated:  →  Global kill flips
to cut CPU use            routine XSS-detection     on every machine          a regex with nested      off. CPU normal
quietly deletes the       rule. No staged          serving HTTP/HTTPS        wildcards backtracking   everywhere at once.
circuit breaker built     rollout — instant         worldwide. First          combinatorially on       Traffic recovers.
to catch a runaway        global push to every      PagerDuty page fires      certain input.           27 minutes, start
regex like this one.      edge server at once.      3 minutes after deploy.  Team reaches for the      to finish.
                                                                              same global-push tool
                                                                              that caused this.

[RESULT — screenshottable]
Regex engine switched to one with a runtime guarantee (RE2 / Rust regex) instead of backtracking search. CPU
protection reinstated. All 3,868 existing WAF Managed Rules hand-audited for the same failure shape. Routine
rule changes now get staged rollout like every other deploy — the instant global push stays reserved for
genuine active-attack emergencies.
```
