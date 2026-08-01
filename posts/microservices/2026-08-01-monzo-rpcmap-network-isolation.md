<!-- sources -->
<!-- Primary: -->
<!--   Monzo Engineering Blog, "We built network isolation for 1,500 services to make Monzo more secure" (Dec 2019) -->
<!--   URL: https://monzo.com/blog/we-built-network-isolation-for-1-500-services -->
<!--   Monzo Engineering Blog, "Building a Modern Bank Backend" (2016) — https://monzo.com/blog/2016/09/19/building-a-modern-bank-backend -->
<!--   Monzo Engineering Blog, "Argo Rollouts at scale: Bringing Automated Rollbacks to 2,100+ services at Monzo" (Nov 2022) -->
<!--   URL: https://monzo.com/blog/2022/11/02/argo-rollouts-at-scale -->
<!--   Monzo Engineering Blog, "How we run migrations across 2,800 microservices" (2024) -->
<!--   URL: https://monzo.com/blog/how-we-run-migrations-across-2800-microservices -->
<!-- Note: direct fetch of monzo.com returned HTTP 403 under this session's egress policy (same class of -->
<!-- gateway-level denial hit on prior posts in this series, e.g. usenix.org/googleusercontent.com on the -->
<!-- Spanner post). web.archive.org fetches were also unavailable in this environment. Facts below were -->
<!-- cross-checked across multiple independent web-search-result excerpts that quote or closely paraphrase -->
<!-- the primary Monzo posts directly, plus corroborating secondary technical writeups: -->
<!--   InfoQ, "How Monzo Isolated Their Microservices Using Kubernetes Network Policies" (Dec 2019) -->
<!--   URL: https://www.infoq.com/news/2019/12/network-isolation-kubernetes/ -->
<!--   BestDevOps, "How Monzo Isolated Their Microservices Using Kubernetes Network Policies" -->
<!--   URL: https://www.bestdevops.com/how-monzo-isolated-their-microservices-using-kubernetes-network-policies/ -->
<!--   The Register, "How does Monzo keep 1,600 microservices spinning?" (Mar 2020) -->
<!--   URL: https://www.theregister.com/2020/03/09/monzo_microservices/ -->
<!--   InfoQ, "monzo microservices migrations" (Sep 2024) — https://www.infoq.com/news/2024/09/monzo-microservices-migrations -->
<!-- Key verifiable details (cross-referenced across primary + corroborating sources): -->
<!-- 1. By 2019 Monzo ran roughly 1,500 microservices with more than 9,300 live inter-service RPC calls, on a -->
<!--    flat Kubernetes pod network with no isolation — any pod could reach any other pod by default. -->
<!-- 2. Monzo built rpcmap, a static-analysis tool that reads the Go source of every service and identifies -->
<!--    the code pattern of one service constructing another service's RPC client, deriving the real -->
<!--    call graph directly from source rather than from a hand-maintained document or runtime observation. -->
<!-- 3. Backend engineer Jack Kleeman explained the team chose static analysis over runtime traffic -->
<!--    observation because not every code path has integration test coverage, and because a bank has -->
<!--    processes that only execute on a yearly cadence — a short observation window would miss them and -->
<!--    silently produce a policy that later blocks a legitimate, rare call. -->
<!-- 4. The derived call graph is compiled into Calico NetworkPolicy / GlobalNetworkPolicy manifests: -->
<!--    default-deny all ingress, with explicit allow-lists keyed to pod labels (e.g. a "service.<name>" -->
<!--    label), not IP addresses — because Kubernetes pod IPs are ephemeral and churn on every reschedule -->
<!--    or autoscale event, while Calico enforces policy against pod labels at the CNI layer on every packet. -->
<!-- 5. Rollout was staged deliberately: policies first ran in an alerts-only mode with packet-dropping and -->
<!--    logging both disabled; logging was enabled only after using a tool called calico-accountant to -->
<!--    confirm log volume would stay manageable; packet-dropping then stayed disabled for a further month -->
<!--    specifically to surface rarely-triggered (including yearly) code paths before final enforcement. -->
<!-- 6. The same fleet kept growing past this point: Monzo migrated 2,100+ services onto Argo Rollouts with -->
<!--    automated, Prometheus-metrics-driven rollback (2022), replacing a human watching a deploy dashboard, -->
<!--    and by 2024 ran cross-fleet code migrations across 2,800 services via a dedicated central migrations -->
<!--    team using a config service for gradual, criticality-tiered rollout rather than per-team coordination. -->

# Monzo Turned Its Codebase Into the Network's Only Security Policy

**Date:** 2026-08-01
**Company:** Monzo
**Category:** microservices
**Post type:** structured case study
**Opening style:** the_decision
**Slug:** monzo-rpcmap-network-isolation
**Character count (LinkedIn):** ~2845

---

## LinkedIn Post

Monzo made an unusual call for a bank running 1,500 microservices: deny every connection between services by default and only reopen paths a machine could prove were real.

The problem was scale, not paranoia. By 2019 Monzo ran roughly 1,500 services with 9,300+ live service-to-service calls on a flat Kubernetes network where any pod could reach any other pod. For a regulated bank that's a PCI DSS and GDPR scoping problem — a buggy service anywhere could reach the ledger, card data, or KYC data anywhere else.

The obvious fix is a human-maintained policy: each team documents who can call their service, security signs off, done. That survives 20 services. It doesn't survive a codebase where someone wires up a new RPC client daily and nobody updates a separate policy file three sprints later. The document drifts from the code until it either silently blocks a rare-but-real call, or teams pre-widen it to "allow everything" to stop getting paged — erasing the point of having it.

So Monzo skipped hand-writing the policy. They built rpcmap: static analysis that reads the actual Go source of every service and finds the pattern of one service constructing another's RPC client — the real call graph, pulled from the only place it can't lie, the code. That graph compiles into Calico NetworkPolicy manifests: default-deny all ingress, allow-listed by pod label, not IP, because pod IPs churn on every reschedule and only identity survives that churn. The policy is generated from the code, not maintained beside it, so it can't drift.

They rejected an easier shortcut too: watch live traffic a while and infer the graph. Engineer Jack Kleeman's reasoning — not every path has test coverage, and a bank has processes that run once a year, so a short observation window would confidently miss the rare, correct call. Silently dropping a real payment path is worse than the risk being removed.

That caution shaped the rollout: alerts only for weeks, then logging once they'd sized the volume with calico-accountant, then dropping stayed off a full month more, specifically to let yearly processes surface first.

The cost is real: security now trusts a pipeline over hand review, and static analysis has a blind spot — a reflection-built call can hide from it. The risk didn't vanish, it moved into the tool.

The same shape recurred as the fleet grew: automated Prometheus-driven rollback replaced a human watching deploys at 2,100+ services in 2022, and a dedicated migrations team with config-driven rollout replaced ad hoc coordination at 2,800 services in 2024. Past a few hundred services, anything assuming a human keeps two systems in sync is already lying to you. The fix isn't better documentation — it's generating the documentation from the thing it describes.

#SystemDesign #Microservices #Kubernetes #Fintech

---

## Twitter / X Version

1/ Monzo made an unusual call for a bank running 1,500 microservices: deny every connection between services by default, and only reopen the paths a machine could prove were real.

2/ By 2019 Monzo had ~1,500 services and 9,300+ live service-to-service calls on a flat Kubernetes network — any pod could reach any other pod. For a bank, that's a PCI DSS/GDPR scoping problem: a buggy service anywhere could reach the ledger or card data.

3/ The obvious fix — teams hand-document who can call their service, security reviews it — survives 20 services. It doesn't survive a codebase adding RPC clients daily. The doc drifts from the code until it blocks something real, or teams pre-widen it to "allow everything."

4/ So Monzo skipped hand-writing the policy. rpcmap statically analyzes the actual Go source of every service, finds the pattern of one service constructing another's RPC client, and derives the real call graph from the only place it can't lie: the code.

5/ That graph compiles straight into Calico NetworkPolicy: default-deny, allow-listed by pod label (not IP, because pod IPs churn constantly). Generated from the code, not maintained beside it — so it can't drift.

6/ They even rejected "just watch traffic and infer the graph." Engineer Jack Kleeman's reasoning: a bank has processes that run once a year. A short observation window would confidently miss the rare, correct call — and silently dropping a real payment is the worse failure.

7/ Rollout matched that caution: alerts only for weeks, then logging once they'd sized the volume, then drops stayed off a full month more — specifically to let yearly processes surface before enforcement.

8/ Cost: security now trusts a generated pipeline over hand review, and static analysis has blind spots (reflection-built calls can hide from it). The risk didn't disappear, it moved into the tool.

9/ Same shape kept showing up as the fleet grew: automated rollback replaced a human watching deploys at 2,100+ services (2022), a dedicated migrations team replaced ad hoc coordination at 2,800 (2024). Past a few hundred services, anything assuming a human keeps two systems in sync is already lying to you.

---

## Excalidraw Diagram

**File:** 2026-08-01-monzo-rpcmap-network-isolation.excalidraw
**Type:** Structured-case-study migration/pipeline flow — a horizontal three-box derivation pipeline (Code → rpcmap → generated NetworkPolicy) at the top, paired with a horizontal rollout timeline below it showing the four staged enforcement steps with durations.
**Color scheme:** Indigo for the derivation pipeline (the deliberate, higher-investment engineering choice). Teal for the headline stat box and timeline dots for the low-risk early stages. Amber, dashed, for the "drops stay off +1 month" callout — the single most load-bearing, cautious step, not a failure state. Slate for connecting lines and footnote. No red/green: nothing here was broken, the old approach (hand-maintained policy) just didn't survive the fleet's growth.
**Screenshottable stat:** "~1,500 services · 9,300+ live service-to-service calls · 1 flat network — and the fix was to stop writing the network policy by hand."

### Layout

```
Title: "Monzo Turned Its Codebase Into the Network's Only Security Policy"
Subtitle: "rpcmap derives Calico network policy for 1,500+ microservices from static analysis of Go
source — not a hand-maintained doc"

[STAT BAR — teal outline]
"~1,500 services · 9,300+ live service-to-service calls · 1 flat network"

[PIPELINE — three indigo boxes connected by slate arrows]
CODE                        rpcmap                       CALICO NETWORKPOLICY
Every service that    -->   Static analysis walks   -->   default-deny all ingress,
calls another                every service's source,       allow-listed by pod label
constructs its RPC           extracts the real call        (not IP — labels survive
client in Go source          graph                         churn)

Caption under pipeline (teal): "Generated from the code, not maintained beside it —
one copy of the truth, so it can't drift."

[TIMELINE — dashed slate line, four stages left to right]
"THE ROLLOUT — enforcement staged behind the risk it was protecting against"

(teal dot) Alerts only          (teal dot) Logging on           (amber dashed box, amber dot)     (indigo dot) Enforced
(weeks) — no drops,              volume sized with                Drops stay off — +1 month         default-deny live,
no logs yet                      calico-accountant                 more, waiting for yearly-run       rpcmap-generated
                                                                    code paths to fire

[FOOTNOTE — slate]
The cost didn't disappear, it moved: security now trusts a generated pipeline instead of reviewing
each policy by hand, and static analysis has its own blind spot — a call built through reflection can
hide from rpcmap the same way an undocumented call used to hide from a human. The fleet kept the same
shape as it grew: Prometheus-driven automated rollback replaced a human watching deploys at 2,100+
services (2022); a dedicated migrations team with config-driven rollout replaced ad hoc coordination
at 2,800 services (2024).
```
