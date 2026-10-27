---
date: 2026-10-27
company: Kubernetes / CoreDNS
topic: The ndots:5 default - every external hostname with fewer than five dots walks the pod's DNS search list first, and the server-side fix (CoreDNS autopath) has its own caveats.
category: infrastructure
post_type: confessional
opening_style: cold_fact
slug: kubernetes-ndots-5-dns-search-path-amplification
---

## Sources

- GitHub, [kubernetes/website - DNS for Services and Pods](https://github.com/kubernetes/website/blob/main/content/en/docs/concepts/services-networking/dns-pod-service.md) - primary: default pod resolv.conf (3 search entries, `options ndots:5`), search list limits (32 domains / 2048 chars).
- GitHub, [mkerrisk/man-pages - resolv.conf(5)](https://github.com/mkerrisk/man-pages/blob/master/man5/resolv.conf.5) - primary: names with fewer than ndots dots are attempted via each search path component in turn before an absolute query.
- GitHub, [coredns/coredns - autopath plugin](https://github.com/coredns/coredns/blob/master/plugin/autopath/README.md) - primary: server-side search completion, CNAME back to the original name, Bugs section (IP reuse race, no Windows, NXDOMAIN defeats the optimization).
- GitHub, [coredns/coredns - kubernetes plugin](https://github.com/coredns/coredns/blob/master/plugin/kubernetes/README.md) - primary: autopath requires `pods verified` and the source IP must be the pod's.

**Key primary-source detail:** the autopath IP-reuse race in the plugin's own Bugs section, and that a negative (NXDOMAIN) answer makes the client re-walk the search path itself.

**Note on sourcing:** only GitHub-hosted docs were reachable from this environment. The "4 lookups per address family, 3 NXDOMAIN" count is arithmetic on the documented search list and ndots rule for `api.stripe.com`, not a measured figure. The "per address family" framing assumes the resolver queries A and AAAA separately, which none of the sources above state; treat that as background knowledge, not a cited claim.

---

## LinkedIn Post

Kubernetes gives every pod a DNS setting that makes most external lookups fail three times before they succeed.

Open /etc/resolv.conf in any pod and it looks like this: `search <namespace>.svc.cluster.local svc.cluster.local cluster.local` and `options ndots:5`. That is straight from the Kubernetes DNS docs.

The reasoning was sound. A service in the same namespace should resolve as just `data`. A service in another one as `data.prod`. Neither has five dots, so the resolver walks the search list and expands them. ndots:5 means any name with fewer than five dots is tried against the search path before it is tried as-is. The resolv.conf man page says it plainly: names with fewer than ndots dots go through each search component in turn until one matches.

Now call `api.stripe.com`. Two dots. The resolver asks for `api.stripe.com.<ns>.svc.cluster.local`, then `api.stripe.com.svc.cluster.local`, then `api.stripe.com.cluster.local`. All three come back NXDOMAIN. Only the fourth query, the real one, returns an answer. Every external call pays for four lookups per address family, and CoreDNS answers three of them with nothing.

Nobody notices at 10 requests a second. It shows up as DNS load, as latency on cold connections, and as a CoreDNS dashboard that looks busier than the traffic justifies.

The fixes are all trade-offs. A trailing dot (`api.stripe.com.`) skips the search list but means editing every hostname. `dnsConfig` can lower ndots per pod to 2, but then `data.prod` stops expanding the way people expect. CoreDNS has an `autopath` plugin that does the walk server-side and returns the first non-NXDOMAIN answer with a CNAME back to the original name. One round trip.

The catch is in its own README. It needs the kubernetes plugin in `pods verified` mode, so every query is checked against a Pod cache. The source IP in the packet has to be the pod's. And there is a documented race: a pod is deleted, its IP is reassigned to a pod in another namespace, that pod queries before the API watch updates CoreDNS, and autopath builds the search path from the previous pod's namespace. If the real answer is NXDOMAIN, the client then searches every path again itself and the optimization disappears.

The default was never careless. It optimized for the lookup that is hardest to explain to a new user: why `data` does not resolve. The cost landed on a different lookup, the one nobody was thinking about.

Not every default that hurts was a mistake. Some were just tuned for the first problem someone had.

#Kubernetes #DNS #CoreDNS #SystemDesign

---

## Twitter Version

Every Kubernetes pod ships with options ndots:5.

Call api.stripe.com (2 dots) and the resolver tries it against the search list first:
- api.stripe.com.<ns>.svc.cluster.local
- api.stripe.com.svc.cluster.local
- api.stripe.com.cluster.local
Three NXDOMAINs. Then the real query.

Why: so `data` and `data.prod` resolve without typing the full service name. Reasonable.

Fixes all cost something. Trailing dot means editing every hostname. Lower ndots breaks short names. CoreDNS autopath does the walk server-side, but needs `pods verified` and has a documented IP-reuse race that can pick the wrong namespace.

The default solved the first problem. The bill went to the second.

---

## Diagram

See `2026-10-27-kubernetes-ndots-5-dns-search-path-amplification.excalidraw` (query ladder for api.stripe.com: three NXDOMAIN lookups vs one with autopath).
