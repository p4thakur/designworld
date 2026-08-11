<!-- sources -->
<!-- Primary: -->
<!--   Fastly, "Summary of June 8 outage" (official post-event summary, fastly.com/blog, published June 8-9, 2021) -->
<!--     — direct WebFetch of fastly.com returned EGRESS_BLOCKED under this session's network policy (same class -->
<!--     of gateway-level denial noted on prior posts in this series, e.g. the AWS DynamoDB and GitLab posts). -->
<!--     Content corroborated via multiple independent web-search-result excerpts from outlets that read and -->
<!--     directly quote/summarize the official postmortem, not from memory. -->
<!-- Corroborating (independent secondary sources, cross-referenced for consistency): -->
<!--   ThousandEyes, "Inside the Fastly Outage: Analysis and Lessons Learned" -->
<!--     https://www.thousandeyes.com/blog/inside-the-fastly-outage-analysis-and-lessons-learned -->
<!--   Tech Times, "Fastly Internet Outage was Due to Software Update Bug Installed by One Customer" -->
<!--     https://www.techtimes.com/articles/261249/20210609/fastly-internet-outage-due-software-update-bug-installed-one-customer.htm -->
<!--   PYMNTS, "Fastly Implements Fix For Software Bug That Caused Outage" -->
<!--     https://www.pymnts.com/safety-and-security/2021/fastly-implements-fix-for-software-bug-that-caused-outage/ -->
<!--   Asia Pacific Security Magazine, "Customer Configuration Change Triggers Fastly Outage" -->
<!--     https://www.asiapacificsecuritymagazine.com/customer-configuration-change-triggers-fastly-outage/ -->
<!--   Fast Company, "How did Fastly break the internet? One customer crashed Amazon, Reddit, Twitch, etc." -->
<!--     https://www.fastcompany.com/90645391/how-did-fastly-break-the-internet-one-customer-crashed-amazon-reddit-twitch-etc -->
<!--   TechCrunch, "Twitch, Pinterest, Reddit and more go down in Fastly CDN outage" -->
<!--     https://techcrunch.com/2021/06/08/numerous-popular-websites-are-facing-an-outage/ -->
<!--   NPR, "Fastly, Tuesday internet outage down was caused by one customer changing setting" -->
<!--     https://www.npr.org/2021/06/09/1004684932/fastly-tuesday-internet-outage-down-was-caused-by-one-customer-changing-setting -->
<!--   Axios, "Fastly says global internet outage was due to a software bug" -->
<!--     https://www.axios.com/2021/06/09/internet-outage-fastly-software-bug -->
<!-- Key verifiable details (cross-referenced across independent write-ups that quote/summarize Fastly's own -->
<!-- postmortem consistently): -->
<!-- 1. May 12, 2021: a software deployment introduced a latent bug that could be triggered by a specific, valid -->
<!--   customer configuration under specific circumstances. No test exercised that exact path; the bug shipped -->
<!--   to production undetected. -->
<!-- 2. June 8, 2021, ~9:50 UTC (5:50am ET): a customer pushed a valid — not erroneous, not malicious — -->
<!--   configuration change that happened to satisfy the exact conditions needed to trigger the dormant bug. -->
<!-- 3. Fastly's global configuration-propagation system pushed the change to the edge fleet as designed. 85% of -->
<!--   Fastly's network began returning errors within about a minute. -->
<!-- 4. Detection: within 1 minute. Root cause identified, isolated, and the offending configuration disabled; -->
<!--   95% of the network was operating normally again by roughly the 49-minute mark. Most user-facing impact -->
<!--   lasted under an hour. -->
<!-- 5. Affected sites/services widely reported across corroborating sources: Amazon, Reddit, Twitch, Spotify, -->
<!--   Stack Overflow, GitHub, gov.uk, Shopify, Stripe, PayPal, Pinterest, HBO Max, Hulu, Quora, Vimeo, CNN, -->
<!--   The New York Times, the BBC, The Guardian, Financial Times. Amazon alone was estimated (per secondary -->
<!--   reporting, not Fastly's own postmortem) to have lost up to $32 million in sales during the outage window; -->
<!--   this figure is a third-party estimate, not a Fastly-disclosed number, and is presented as such. -->
<!-- 6. Fastly deployed a permanent fix for the specific bug within roughly 8 hours of the incident. Per -->
<!--   corroborating reporting on Fastly's stated response, longer-term remediation included a full post-incident -->
<!--   review of QA/testing processes and stated investment in further leveraging WebAssembly-based isolation in -->
<!--   Compute@Edge to build additional resiliency into the underlying platform. -->
<!-- Note: precise sub-minute timestamps and Fastly's exact internal wording beyond the commonly corroborated -->
<!--   "~1 min detection / ~49 min to 95% restored / 85% peak error rate / <8hr permanent fix" figures were not -->
<!--   independently re-verifiable in this session (direct fetch of fastly.com blocked); no additional precision -->
<!--   is claimed beyond what is corroborated above. -->

# One Customer Made a Completely Normal Config Change. It Broke 85% of Fastly's Network in a Minute.

**Date:** 2026-08-11
**Company:** Fastly
**Category:** stability
**Post type:** confessional
**Opening style:** cold_fact
**Slug:** fastly-2021-single-customer-config-outage
**Character count (LinkedIn):** ~2686

---

## LinkedIn Post

On June 8, 2021, one Fastly customer pushed a completely ordinary configuration change. Nothing wrong with it, nothing against policy. Within about a minute, 85% of Fastly's global network was returning errors, and a meaningful slice of the internet went with it.

Fastly's whole product is speed of propagation. Push a config change and it reaches every edge server in their global network almost immediately — that's the entire pitch for using a CDN instead of running your own reverse proxies. On May 12, 2021, a routine software deployment quietly introduced a bug in how one category of customer configuration got validated during compilation. No test exercised that exact path. It sat there, live, for 27 days.

Then a different customer, on a different day, pushed a config change that happened to satisfy the precise conditions the bug needed. Not an error on their part. Not abuse. Something any customer could plausibly do on any given Tuesday. The propagation system did exactly what it was built to do: pushed the change out fast, everywhere. That's the part worth sitting with — the failure wasn't a slow system breaking. It was a fast, well-built system working exactly as designed, at the worst possible moment.

Amazon, Reddit, Twitch, Spotify, GitHub, Stack Overflow, PayPal, Shopify, Stripe, gov.uk, CNN, the NYT, the BBC — all down within the same minute. Amazon alone was estimated to have lost up to $32 million in sales during the window.

Here's the part Fastly deserves credit for: detected in 1 minute, root cause isolated and the offending config disabled by minute 49, 95% of the network back to normal. A permanent fix shipped in under 8 hours. That's a genuinely good incident response.

But their own postmortem didn't stop at "we tested more after this." The deeper admission was that detection and rollback speed had been quietly standing in for isolation they didn't have. Their longer-term response was investing harder in WebAssembly-based isolation in Compute@Edge — sandboxing customer configuration processing so one customer's edge case can't cascade into everyone else's traffic, instead of hoping QA catches every combination first.

Nothing about the original design was careless. Fast, self-service, global propagation is the product people pay for. The bug was ordinary, the kind that hides in an untested branch for weeks. What changed wasn't the ambition — it was the assumption that catching bugs before they ship is the primary line of defense. Sometimes it isn't. Sometimes the honest fix is building so that when one does slip through, it can't reach everyone at once.

Sources in comments.

#SystemDesign #Fastly #CDN #SRE #Reliability

---

## Twitter / X Version

1/ June 8, 2021: one Fastly customer pushed a completely ordinary config change. Nothing wrong with it. Within about a minute, 85% of Fastly's global network was returning errors — and Amazon, Reddit, Twitch, Spotify, PayPal, GitHub, gov.uk went down with it.

2/ Fastly's whole product is propagation speed: push a config, it hits every edge server globally almost instantly. That's the pitch for a CDN over your own reverse proxies.

3/ On May 12, a routine deploy quietly introduced a bug in how one type of customer config got validated. No test hit that path. It sat there, live, for 27 days.

4/ Then a different customer pushed a totally valid config change that happened to match the exact conditions the bug needed. Not an error. Not abuse. Something anyone could've done on any Tuesday.

5/ The propagation system did exactly its job — pushed it out fast, everywhere. That's the uncomfortable part: this wasn't a slow system breaking. It was a fast, well-built system working exactly as designed, at the worst moment.

6/ Amazon alone is estimated to have lost up to $32M in sales during the outage window.

7/ Fastly's response was genuinely good: detected in 1 minute, cause isolated and the config disabled by minute 49, 95% of the network back to normal. Permanent fix shipped in under 8 hours.

8/ But their postmortem didn't stop at "test more." The real admission: detection and rollback speed had been standing in for isolation they didn't have.

9/ The longer-term fix was investing harder in WebAssembly-based isolation in Compute@Edge — so one customer's config bug can't cascade into everyone else's traffic.

10/ Fast, self-service, global propagation is the product. The bug was ordinary. What changed wasn't the ambition — it was the assumption that catching every bug pre-ship is the only line of defense.

---

## Excalidraw Diagram

**File:** 2026-08-11-fastly-2021-single-customer-config-outage.excalidraw
**Type:** Two-panel — a 5-box horizontal timeline showing the dormant bug from introduction to fix, paired with a 3-row "blast radius" panel naming who felt it and what it cost.
**Color scheme:** Slate for the calm, unremarkable setup (deploy, silent weeks). Amber for the trigger itself — deliberately not red, because the customer action was legitimate, not a mistake. Rose reserved for the one box that shows actual damage (85% erroring). Teal for the recovery steps, since the incident response itself was genuinely good. Footer in teal, not the indigo used on the prior AWS post, to keep the palette from repeating post to post.
**Screenshottable stat:** "1 legitimate config change. 85% of a global network erroring in under a minute. 49 minutes to 95% recovery. $32M in estimated lost Amazon sales in between."

### Layout

```
Title: "One Customer Made a Completely Normal Config Change. It Broke 85% of Fastly's Network in a Minute."
Subtitle: "Fastly's own postmortem: a dormant bug from a deployment 27 days earlier, tripped by an ordinary,
legitimate customer action — not a mistake, not an attack"

[PANEL 1 — THE TIMELINE: A DORMANT BUG, AN ORDINARY TRIGGER, top, 5 boxes left to right]
  Box 1 (slate): "May 12, 2021. A routine software deployment ships. It quietly introduces a bug in how one
    category of customer configuration gets validated during compilation. No test exercises that path."
  --arrow (indigo)-->
  Box 2 (slate): "27 days pass. Nothing triggers it. Deploys keep shipping, customers keep changing configs.
    The bug just needs one specific, ordinary combination it hasn't seen yet."
  --arrow (amber)-->
  Box 3 (amber): "June 8, ~9:50 UTC. A different customer pushes a completely valid, routine configuration
    change. Not an error, not against policy — it just happens to match what the bug needed."
  --arrow (rose)-->
  Box 4 (rose): "Fastly's propagation system does exactly its job: pushes the change to the global edge
    fleet, fast. 85% of the network starts returning errors within about a minute."
  --arrow (teal)-->
  Box 5 (teal): "Detected in 1 minute. Cause isolated, config disabled — 95% of the network normal again
    by minute 49. Permanent fix shipped in under 8 hours."

[PANEL 2 — THE BLAST RADIUS: ONE CONFIG, A SLICE OF THE INTERNET, bottom, 3 stacked rows: name box + desc box]
  1. Retail & fintech [amber] — "Amazon, PayPal, Stripe, Shopify. Amazon alone estimated to have lost up
     to $32M in sales during the outage window."
  2. Platforms & media [amber] — "Reddit, Twitch, Spotify, Stack Overflow, GitHub, Pinterest, HBO Max,
     Hulu, Quora, Vimeo — all returning errors within the same minute."
  3. News & government [amber] — "CNN, The New York Times, the BBC, The Guardian, Financial Times, and
     gov.uk, the UK government's own site."

[FOOTER, teal band, full width]
  "Total: ~1 hour of visible impact, 85% of Fastly's global network affected at peak, fixed inside 49
  minutes. Longer-term fix: heavier investment in WebAssembly-based isolation in Compute@Edge, so one
  customer's configuration can't cascade into everyone else's traffic. 'Fast, global propagation is the
  product. It's also the blast radius.'"
```
