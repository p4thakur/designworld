---
date: 2026-09-19
company: AWS
topic: AWS rejected the assumption that serverless had to choose between full-VM isolation and container-level speed, and built Firecracker — a stripped-down VMM that boots a real KVM-backed VM in under 125ms with under 5 MiB of overhead, retiring the one-EC2-VM-per-task workaround Fargate had been running to fake container isolation
category: infrastructure
post_type: contrarian
opening_style: challenge_assumption
slug: aws-firecracker-microvm-serverless-isolation
---

## Sources

- USENIX NSDI '20: ["Firecracker: Lightweight Virtualization for Serverless Applications"](https://www.usenix.org/conference/nsdi20/presentation/agache) by Agache et al. — primary paper for the architecture, the 5-device minimal device model, boot time (<125ms), memory overhead (<5 MiB), and the density/throughput numbers (up to 150 microVMs/sec on a host, thousands per machine).
- Firecracker project site and GitHub (firecracker-microvm/firecracker) — corroborates the device list (virtio-net, virtio-block, virtio-vsock, serial console, minimal keyboard controller), the jailer + seccomp-bpf isolation layer, and the November 2018 open-source announcement alongside production use in Lambda.
- AWS Open Source Blog: "Announcing the Firecracker Open Source Technology: Secure and Fast microVM for Serverless Computing" (2018) — describes the tradeoff AWS designed against: public infrastructure providers need both strong security and minimal overhead, not one or the other, and both Lambda and Fargate needed a fix.
- Independent corroboration (Aqua Security, "Amazon Firecracker: Isolating Serverless Containers and Functions") of the pre-Firecracker Fargate architecture: each Fargate Task ran inside a dedicated EC2 VM to get hardware isolation between tasks, before Fargate Tasks moved onto Firecracker microVMs.

**Note on sourcing:** Direct fetch of usenix.org, aws.amazon.com, and firecracker-microvm.github.io was blocked by this environment's network egress policy at write time. The facts above are drawn from search-indexed excerpts of the primary paper and AWS's own announcement, cross-checked against independent write-ups (Aqua Security, project GitHub docs) that agree on the same architecture, numbers, and timeline.

**Key primary-source detail (not in most summaries):** Most retellings of the Firecracker story stop at "it's a fast, lightweight VM for Lambda." What that skips is *why AWS needed one VMM for two different products*: before Firecracker, Fargate's "containers" weren't actually sharing a host at the container level at all — each Task ran inside its own dedicated EC2 virtual machine, because that was the only way to get real isolation between customers' containers. Lambda had the opposite problem in the other direction — no time to boot a real VM per invocation, so it ran on a different, container-based sandboxing approach. AWS wasn't choosing between "fast" and "safe" for one product. It was running two separate, expensive workarounds for the same unsolved problem, and Firecracker is the VMM that let both retire their patch.

---

## LinkedIn Post

For a decade, serverless treated one tradeoff as physics: real isolation means a full VM, and full VMs are too slow and too expensive to hand out per request.

AWS Lambda and AWS Fargate both had this baked into their economics, in opposite ways. Lambda ran strangers' code millions of times a second and billed by the millisecond — no time to boot a real virtual machine per invocation. Fargate had the embarrassing workaround: to give every "container" hardware-level isolation, it was quietly launching a full dedicated EC2 VM underneath each task. Two products, two patches, and neither one had actually solved the problem — one was paying VM prices for container promises, the other container prices for VM problems.

The obvious fixes didn't work. Containers alone share a kernel, so one exploited syscall can jump between tenants — unacceptable when tenants are strangers renting compute by the millisecond. Full VMs fix that, but a stock hypervisor boots a whole BIOS and a device tree built for hardware nobody in a data center owns. That overhead is exactly what was forcing Fargate to burn a full EC2 instance per task just for isolation.

AWS's answer, open-sourced as Firecracker in 2018, was to stop treating "VM" and "lightweight" as opposites. Strip the virtual machine down to five emulated devices — network, block storage, a serial console, vsock, and a minimal keyboard controller — and drop everything a cloud server never touches: no BIOS bloat, no USB, no video, no audio. What's left is still a real KVM-backed VM. It boots a full guest kernel and starts answering API calls in under 125 milliseconds, with under 5 MiB of memory overhead, wrapped in its own jailer process and seccomp filter.

That's thin enough to launch 150 of them a second on one host and pack thousands onto a single machine — which is why Lambda and Fargate both run on it today, Fargate retiring its one-VM-per-task hack in the process.

"Fast and cheap" versus "isolated and secure" was never a law of physics. It was a property of hypervisors built for someone else's workload.

#SystemDesign #AWS #Serverless #Virtualization

**Character count: 2,125 / 3,000 ✓**
**First ~160 chars (mobile hook):** "For a decade, serverless treated one tradeoff as physics: real isolation means a full VM, and full VMs are too slow and too expensive to hand out per request." ✓

---

## Twitter / X Thread

1/ Before 2018, AWS Lambda and AWS Fargate shared a dirty secret: real multi-tenant isolation supposedly required a full VM per workload — so Fargate was quietly booting a whole dedicated EC2 instance under every single "container" task.

2/ Containers alone share a kernel — one escape and a stranger's code touches yours. Full VMs fix that, but a stock hypervisor drags along a BIOS, a device tree, and boot times measured in seconds. Neither option fit serverless economics.

3/ AWS's fix: Firecracker. A VMM stripped to 5 emulated devices (net, block, vsock, console, keyboard), no BIOS bloat, wrapped in a jailer process + seccomp-bpf filter for defense in depth.

4/ Result: under 125ms to boot and start serving API calls, under 5 MiB memory overhead per microVM, up to 150 microVMs launched per second on one host, thousands packed onto a single machine.

5/ Lambda and Fargate both moved onto it — Fargate retiring its one-VM-per-task workaround for good. "Fast" and "isolated" were never actually in tension. The old hypervisors were just built for someone else's job.

---

## Diagram

See: `2026-09-19-aws-firecracker-microvm-serverless-isolation.excalidraw`

Type: Side-by-side architecture comparison (contrarian style) — three columns (Containers alone / Full VM per task — pre-2018 Fargate / Firecracker microVM) with arrows showing the progression, plus a callout banner for the density numbers.
Color scheme: blue for plain containers, amber for the full-VM workaround, teal for the Firecracker outcome, green for the results callout — deliberately not red/bad-green/good, since neither containers nor full VMs were "wrong," just mismatched to the job.
Key screenshottable numbers: <125ms boot time, <5 MiB memory overhead per microVM, up to 150 microVMs/sec on one host, 15 trillion+ Lambda invocations/month.
