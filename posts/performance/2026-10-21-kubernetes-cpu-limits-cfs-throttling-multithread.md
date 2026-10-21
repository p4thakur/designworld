---
date: 2026-10-21
company: Linux / Kubernetes
topic: CPU limits, CFS bandwidth throttling and why low average CPU still means frozen containers.
category: performance
post_type: contrarian
opening_style: number_that_doesnt_add_up
slug: kubernetes-cpu-limits-cfs-throttling-multithread
---

## Sources

- Linux kernel, [CFS Bandwidth Control (sched-bwc.rst)](https://github.com/torvalds/linux/blob/master/Documentation/scheduler/sched-bwc.rst) - primary: default `cpu.cfs_period_us` 100ms, quota semantics, 5ms `sched_cfs_bandwidth_slice_us`, global pool distributed to per-CPU run queues, `nr_periods`/`nr_throttled`/`throttled_time`, burst past quota by up to ~1ms per CPU, `cpu.cfs_burst_us`.
- Kubernetes, [Resource Management for Pods and Containers](https://github.com/kubernetes/website/blob/main/content/en/docs/concepts/configuration/manage-resources-containers.md) - primary: CPU limits enforced by throttling, memory limits by OOM kill, larger CPU requests get more CPU time under contention.

**Note on sourcing:** only these two GitHub-hosted docs were reachable. The 8-thread, 12.5ms / 87.5ms timeline is arithmetic on the documented 100ms default, an illustration and not an incident report. The 12% average is a hypothetical.

**Key primary-source detail:** quota lives in a global pool and is handed to per-CPU run queues in 5ms slices, so a limit is a time budget shared by every thread, not a core count.

---

## LinkedIn Post

A service averages 12% CPU. Its latency graph looks like it is being strangled.

The CPU limit is 1 core. Nothing is near it. And the container is being paused anyway.

The Kubernetes docs say CPU limits are enforced by throttling, and that the kernel treats the limit as a hard ceiling. Underneath, the Linux CFS bandwidth controller turns "1 CPU" into a quota: 100ms of CPU time per 100ms period by default (cpu.cfs_period_us). Once the group has spent its quota, every thread in it is throttled until the next period starts.

The word that matters is time, not cores. A limit of 1 CPU is a budget of 100ms of CPU time, and that budget is spent across all threads at once.

Run 8 threads in parallel and they burn 100ms in about 12.5ms of wall clock. Then the whole container sits frozen for the remaining 87.5ms. That arithmetic is an illustration, not a measurement, but it is the shape of the bug. Average usage over a second is tiny. Within a single period the process is either running flat out or not running at all. A request that lands in the frozen stretch waits for it.

The kernel doc adds a detail that explains why this is hard to see. Quota is not held in one place. It sits in a global pool and moves to per-CPU run queues in slices, 5ms by default (sched_cfs_bandwidth_slice_us). So a many-threaded service on a big node pays for runtime on every core it touches.

The only honest signal is in the cgroup stats: nr_periods, nr_throttled and throttled_time. For a CPU-bound app the doc says nr_periods roughly equals nr_throttled. For a bursty one, a high nr_throttled next to low utilization is the fingerprint.

Here is the contrarian part. Teams set CPU limits to be safe. But the CPU request already gives a workload its fair share under contention, because the docs say larger requests get more CPU time than smaller ones. The limit adds nothing to fairness. It only adds a ceiling that bites in the one situation where the node has idle CPU to give.

Memory is the opposite. Exceed the limit and the kernel OOM-kills. CPU is compressible, so the instinct to cap it the same way is a category error. Capping memory protects the node. Capping CPU, when requests are set, mostly protects nothing and costs tail latency.

If a limit is needed, size it in time, not threads: a quota that covers the burst across every thread, or a burst allowance (cpu.cfs_burst_us) so a quiet period can pay for a loud one.

Sometimes the safe default is the one with the hidden bill.

#Kubernetes #Linux #SystemDesign #Performance

---

## Twitter Version

A service averages 12% CPU. Its p99 looks strangled.

Limit: 1 core. In Linux CFS that means 100ms of CPU time per 100ms period, shared by ALL threads.

8 threads burn that in ~12.5ms. The container then freezes for the other 87.5ms. (Illustrative math, not a measurement.)

Check nr_throttled and throttled_time in the cgroup stats, not average CPU.

The request already gives fair share under contention. The limit only adds a ceiling that bites when the node has idle CPU.

Memory limit = OOM kill. CPU is compressible. Don't cap them alike.

---

## Diagram

See `2026-10-21-kubernetes-cpu-limits-cfs-throttling-multithread.excalidraw` (one 100ms period: 8 threads spend the quota in 12.5ms, then 87.5ms throttled).
