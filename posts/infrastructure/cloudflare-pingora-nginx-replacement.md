<!-- sources -->
<!-- Primary: https://blog.cloudflare.com/how-we-built-pingora-the-proxy-that-connects-cloudflare-to-the-internet/ -->
<!-- Published: September 14, 2022 — Cloudflare Engineering Blog -->
<!-- Key verifiable detail: connection reuse 87.1% → 99.92%, 160x fewer new origin connections -->

# Cloudflare Pingora: When 10 Years of Nginx Wasn't Enough

**Date:** 2026-06-12
**Category:** infrastructure
**Post type:** confessional
**Slug:** cloudflare-pingora-nginx-replacement
**Character count (LinkedIn):** ~2,010

---

## LinkedIn Post

Cloudflare ran Nginx for nearly a decade. It proxied every HTTP request that crossed their network. It worked.

Then they replaced it entirely. Not because Nginx was broken. Because the architecture that made it simple also made a critical optimization impossible.

Nginx uses a multi-process model — each worker is a separate OS process, and each worker maintains its own connection pool to origin servers. If worker 12 has an established TLS connection to your origin, and the next request for your origin lands on worker 43, worker 43 cannot use that connection. It opens a new one.

This is fine with 4 workers. It's a compounding problem at scale. At Cloudflare — hundreds of workers per machine, thousands of machines — requests were constantly competing for connection slots that another worker already held but couldn't share.

For one major customer, connection reuse was 87.1%. That sounds okay until you flip it: 12.9% of requests were opening fresh TCP + TLS handshakes that didn't need to exist. Each one adds latency. At a trillion requests a day, that was an enormous amount of avoidable cost hitting origins.

They couldn't fix this with Nginx modules. Per-process isolation is a core architectural property — the same thing that makes Nginx stable is what prevents connection sharing. You can't configure your way out of a design choice.

So they built Pingora in Rust: multi-threaded, one shared connection pool across all threads. One pool. Any thread. Any connection.

For that same customer: connection reuse went from 87.1% to 99.92%. New connections to origin dropped 160x. Not 160% — 160 times fewer.

Across all traffic: 70% less CPU, 67% less memory than Nginx at the same load.

Nginx was right for years. The problem wasn't that it aged badly. The problem was that Cloudflare grew into a shape its architecture never anticipated. You can't fix a fundamental model mismatch from the outside. Sometimes you have to build a new inside.

#SystemDesign #Rust #Infrastructure #Engineering

---

## Twitter Version

Cloudflare ran Nginx for a decade. Then replaced it entirely. Not because Nginx was broken — because of one architectural property they couldn't work around.

Nginx uses per-worker connection pools. Each OS process can only reuse connections it personally opened. Add more workers to scale up → connection reuse actually gets worse.

For one customer: 12.9% of requests were opening fresh TCP+TLS handshakes that didn't need to exist. At a trillion requests a day, that's an enormous amount of avoidable latency hitting origins.

They built Pingora in Rust — multi-threaded, with one shared connection pool. Any thread. Any connection. No wasted handshakes.

Result: connection reuse from 87.1% → 99.92%. New connections to origin dropped 160x. Across all traffic: 70% less CPU, 67% less memory vs Nginx.

Nginx was the right call for years. The architecture just didn't fit the shape Cloudflare eventually grew into. That's not a failure. It's how systems age.

---

## Excalidraw Diagram

**Type:** Side-by-side architecture comparison (matches confessional post type)
**Color scheme:** Warm amber (#d4813a) for Nginx — not red, it wasn't bad. Cool teal (#2a6e8c) for Pingora. Dark slate background.

### Layout

**Left panel — NGINX (multi-process):**
```
┌─────────────────────────────────────────┐
│          NGINX: Per-Worker Pools         │
│                                         │
│  Worker 1  [Pool: conn A, conn B]  ──►  │
│  Worker 2  [Pool: conn C        ]  ──►  │  Origin
│  Worker 3  [Pool: ∅ EMPTY       ]  ─ ─►│
│  Worker 4  [Pool: conn D        ]  ──►  │
│            ▲                            │
│     NEW TCP+TLS handshake               │
│     (conn B in worker 1 sat unused)     │
└─────────────────────────────────────────┘
  Connection reuse: 87.1%
  12.9% of requests = wasted handshakes
```

**Right panel — Pingora (multi-threaded):**
```
┌─────────────────────────────────────────┐
│         Pingora: Shared Pool             │
│                                         │
│  Thread 1 ─┐                           │
│  Thread 2 ─┼──► [Shared Pool:     ] ──►│  Origin
│  Thread 3 ─┘    [conn A,B,C,D,E…  ]   │
│                                         │
│  Any thread uses any connection         │
└─────────────────────────────────────────┘
  Connection reuse: 99.92%
  160x fewer new connections to origin
```

**Bottom bar (screenshottable numbers):**
```
         CPU usage     Memory usage
Nginx    ████████████  ████████████  100%
Pingora  ███           ████          30% / 33%
```

**Key callout box (center):**
> "The more you scaled NGINX, the worse connection reuse got."
> "Scaling Pingora has no such penalty."
