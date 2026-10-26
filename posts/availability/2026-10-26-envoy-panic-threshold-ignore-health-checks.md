---
date: 2026-10-26
company: Envoy Proxy (CNCF)
topic: Envoy's panic threshold - below 50% healthy hosts the load balancer stops trusting health status, and outlier ejection is capped at 10% so one bad signal cannot empty a cluster.
category: availability
post_type: structured
opening_style: specific_number
slug: envoy-panic-threshold-ignore-health-checks
---

## Sources

- GitHub, [envoyproxy/envoy - Panic threshold](https://github.com/envoyproxy/envoy/blob/main/docs/root/intro/arch_overview/upstream/load_balancing/panic_threshold.rst) - primary: 50% default, "avoid a situation in which host failures cascade", fail_traffic_on_panic tradeoff, priority interaction table.
- GitHub, [envoyproxy/envoy - Overprovisioning Factor](https://github.com/envoyproxy/envoy/blob/main/docs/root/intro/arch_overview/upstream/load_balancing/overprovisioning.rst) - primary: default 140, so unavailable only below 72%.
- GitHub, [envoyproxy/envoy - Outlier detection](https://github.com/envoyproxy/envoy/blob/main/docs/root/intro/arch_overview/upstream/outlier.rst) - primary: ejection algorithm, `max_ejection_percent` check, ejection time multiplied per consecutive ejection, ejected hosts used again in panic.
- GitHub, [envoyproxy/envoy - outlier_detection.proto](https://github.com/envoyproxy/envoy/blob/main/api/envoy/config/cluster/v3/outlier_detection.proto) - primary: max_ejection_percent default 10%, base_ejection_time 30s, max_ejection_time 300s.

**Key primary-source detail:** the priority table. With two priorities at 25% healthy each, normalized health is 70%, both enter panic, and traffic splits 50/50 across all hosts. The 72% line comes from the overprovisioning default of 140 (100/1.4), not from the panic threshold itself.

---

## LinkedIn Post

Envoy will deliberately send traffic to hosts it believes are dead. By default, that starts the moment fewer than 50% of a cluster is healthy.

It sounds like a bug. It's one of the more carefully reasoned defaults in the proxy.

A load balancer normally only considers healthy or degraded hosts. That works until the health signal itself becomes the failure. Say 60% of a cluster fails checks and gets removed. The surviving 40% now carry 100% of the traffic, run hot, start failing their own checks, and get removed too. The Envoy docs name this directly: the panic threshold exists "to avoid a situation in which host failures cascade throughout the cluster as load increases."

So below 50% healthy, Envoy disregards health status and spreads load across all hosts. A degraded cluster serving some requests beats a perfectly "correct" one serving none.

The detail that makes it more than a one-liner is priorities. The thresholds interact. With P=0 and P=1 both at 25% healthy, normalized total health is 70%, both levels panic, and traffic splits 50/50 by host count. With P=0 at 5% and P=1 at 65%, only P=0 panics: it keeps 7% of traffic, P=1 takes 93%. And you don't see panic at all while P=1 is fully healthy, because Envoy just shifts load to it. Even the "unavailable" line isn't 50%. The overprovisioning factor defaults to 140, so a priority isn't treated as unavailable until healthy hosts drop below 72%.

The same logic shows up on the ejection side. Outlier detection ejects hosts that return consecutive 5xx, but `max_ejection_percent` defaults to 10%. If the ejection would push past that, the host stays in. A hundred hosts, a bad deploy, and the detector can still only remove ten. Ejection time also scales with repeat offenses: 30s base, multiplied per consecutive ejection, capped at 300s by default.

There's an escape hatch, and it's a real tradeoff. `fail_traffic_on_panic` sends nothing during panic. The docs say that's right for services that fail all-or-nothing, and pointless for ones that keep serving some requests while degraded.

Health checks are a sensor. A sensor that reads "everything is dead" is more often broken than right, and the proxy is built to say so.

#Envoy #SystemDesign #SRE #ServiceMesh

---

## Twitter Version

Envoy will send traffic to hosts it thinks are dead.

Default: once fewer than 50% of a cluster is healthy, it ignores health status and balances across everyone.

Why: remove 60% of hosts, the other 40% take all the load, fail their checks, get removed. Envoy's docs call this the cascade the panic threshold exists to stop.

Same idea on ejection: max_ejection_percent defaults to 10%. A bad deploy on 100 hosts still ejects at most 10.

Priorities are the subtle part: 25%/25% healthy gives 70% normalized health, both panic, 50/50 split.

When the sensor says everything is dead, suspect the sensor.

---

## Diagram

See `2026-10-26-envoy-panic-threshold-ignore-health-checks.excalidraw` (scaling curve: healthy hosts % vs where traffic goes, with the 72%, 50% and 10% lines).
