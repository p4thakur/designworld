---
date: 2026-11-14
company: Kubernetes (kubelet / EndpointSlice)
topic: Pod deletion starts kubelet shutdown and EndpointSlice removal "at the same time"; the community workaround was an exec preStop `sh -c "sleep 20"`, which needs a sleep binary that distroless images lack; KEP-3960 moved the sleep into the kubelet itself (time.After), GA in v1.34.
category: infrastructure
post_type: confessional
opening_style: cold_fact
slug: kubernetes-prestop-sleep-endpoint-race
---

## Sources

- Kubernetes docs, [Pod Lifecycle - Pod Termination Flow](https://github.com/kubernetes/website/blob/main/content/en/docs/concepts/workloads/pods/pod-lifecycle.md) - primary: "At the same time as the kubelet is starting graceful shutdown of the Pod, the control plane evaluates whether to remove that shutting-down Pod from EndpointSlice objects". Default `terminationGracePeriodSeconds` is 30 s; if preStop is still running at the deadline the kubelet grants a one-off 2 s extension. Terminating endpoints are kept with `ready: false`, `serving` reflects real readiness.
- Kubernetes docs, [Container Lifecycle Hooks](https://github.com/kubernetes/website/blob/main/content/en/docs/concepts/containers/container-lifecycle-hooks.md) - primary: `httpGet`, `tcpSocket` and `sleep` "are executed by the kubelet process, and `exec` is executed in the container". PreStop "must complete its execution before the TERM signal can be sent"; the grace period covers hook + shutdown.
- [KEP-3960: Introducing Sleep Action for PreStop Hook](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/3960-pod-lifecycle-sleep-action/README.md) and [kep.yaml](https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/3960-pod-lifecycle-sleep-action/kep.yaml) - primary: created 2023-04-22; alpha v1.29, beta v1.30, stable v1.34; Story 1: "I want to do it without needing a sleep binary in my image"; Story 2 quotes the old `command: ["/bin/sh","-c","sleep 20"]` workaround; metric `sleep_action_terminated_early_total`.
- kubernetes/kubernetes, [pkg/kubelet/lifecycle/handlers.go](https://github.com/kubernetes/kubernetes/blob/master/pkg/kubelet/lifecycle/handlers.go) - primary: `runSleepHandler()` is a `select` on `time.After(seconds)` vs `ctx.Done()`; the early path increments `LifecycleHandlerSleepTerminated` and returns "container terminated before sleep hook finished".
- kubernetes/kubernetes, [pkg/apis/core/validation/validation.go](https://github.com/kubernetes/kubernetes/blob/master/pkg/apis/core/validation/validation.go) - primary: `validateSleepAction()` rejects `sleep.Seconds < 0 || sleep.Seconds > *gracePeriod` ("must be non-negative and less than terminationGracePeriodSeconds").
- kubernetes/kubernetes, [pkg/kubelet/metrics/metrics.go](https://github.com/kubernetes/kubernetes/blob/master/pkg/kubelet/metrics/metrics.go) - primary: counter `sleep_action_terminated_early_total` in the `kubelet` subsystem, ALPHA stability.

**Key primary-source detail:** the native sleep is not run inside the container at all. It is a ~10-line `select { case <-ctx.Done(): ...; case <-time.After(...): }` in the kubelet. The whole feature exists because the widely copied workaround (exec `sleep` in preStop) silently depended on a binary that minimal images removed.

Framing note (author's reading, not a quote): the two-path termination is a consequence of Kubernetes' independent-controller design. The docs state the simultaneity; they do not call it a mistake.

---

## LinkedIn Post

Kubernetes' fix for a classic rollout problem is about ten lines of Go. A time.After, running inside the kubelet, waiting N seconds.

Here's why it had to exist.

When you delete a Pod, the docs say two things happen "at the same time." The kubelet starts shutting the container down. The control plane starts pulling the Pod out of EndpointSlices. Neither waits for the other.

That was a reasonable call. Kubernetes is a set of independent controllers watching the API server. Making the kubelet wait on the endpoint pipeline would tie every termination to every node catching up.

But the two paths aren't the same length. The kubelet is one local hop. Endpoint removal has to travel from the EndpointSlice controller through the API server to kube-proxy on every node, plus any ingress or load balancer. If your app exits the moment it sees SIGTERM, it can win that race, and traffic keeps arriving at a process that has stopped listening.

The fix everyone copied was a preStop hook running sh -c "sleep 20". preStop finishes before SIGTERM is sent, so the pod keeps serving while the rest of the cluster catches up.

Then images got smaller. Distroless and scratch images ship no shell and no sleep binary. The workaround for the race was quietly depending on /bin/sleep.

KEP-3960, filed April 2023, says it in one line: "I want to do it without needing a sleep binary in my image."

The answer was preStop: sleep: seconds: N. The docs are explicit that sleep, like httpGet, runs in the kubelet process, not in the container. runSleepHandler() is a select on time.After and the context. Alpha in 1.29, beta in 1.30, GA in 1.34.

Two details from the source are worth knowing. The sleep spends your grace period: validation rejects any value above terminationGracePeriodSeconds, which defaults to 30. And if the container dies before the timer fires, the kubelet bumps sleep_action_terminated_early_total.

None of this means the original designers got it wrong. Independent controllers are a big part of why Kubernetes scales. But eventual consistency gets paid for somewhere, and for years the payment was a sleep command baked into people's container images.

The new field doesn't remove the race. It just stops pretending it isn't there.

#Kubernetes #SystemDesign #DistributedSystems #SRE

---

## Twitter Version

Kubernetes' fix for a classic rollout bug: ~10 lines of Go. A time.After inside the kubelet.

Delete a Pod and two things start "at the same time": kubelet shutdown, and removal from EndpointSlices. The second has to reach kube-proxy on every node.

Exit fast on SIGTERM and you win the race. Traffic keeps coming.

Everyone's fix: preStop sh -c "sleep 20". Then distroless images dropped /bin/sleep.

KEP-3960: preStop.sleep, run by the kubelet. GA in 1.34. Counts against your 30 s grace period.

It doesn't remove the race. It admits it.

---

## Diagram

See `2026-11-14-kubernetes-prestop-sleep-endpoint-race.excalidraw`: left side shows the two parallel lanes from t = 0 (kubelet: preStop sleep -> SIGTERM; control plane: EndpointSlice controller -> API server -> kube-proxy on every node -> LB) with a callout where an app with no sleep exits while traffic still arrives. Right side is a confessional timeline: pre-2023 exec `sleep` workaround -> 2023-04 KEP-3960 filed -> v1.29/1.30 alpha/beta -> v1.34 GA. Footer: sleep must be <= terminationGracePeriodSeconds; `sleep_action_terminated_early_total`. Palette: teal + plum + amber, no red/green.
