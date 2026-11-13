---
date: 2026-11-13
company: Go standard library (net/http)
topic: DefaultMaxIdleConnsPerHost = 2 - a shared http.Client keeps only 2 idle connections per host, so an HTTP/1.1 burst of 100 closes 98, parks them in 60 s TIME_WAIT, and caps churn to one upstream at ~470 new conns/s before ephemeral ports run out.
category: microservices
post_type: contrarian
opening_style: challenge_assumption
slug: go-http-maxidleconnsperhost-two-time-wait
---

## Sources

- Go, [src/net/http/transport.go](https://github.com/golang/go/blob/master/src/net/http/transport.go) - primary: `const DefaultMaxIdleConnsPerHost = 2`; `DefaultTransport` sets `MaxIdleConns: 100`, `IdleConnTimeout: 90 * time.Second`, `ForceAttemptHTTP2: true`; `MaxIdleConnsPerHost` doc "If zero, DefaultMaxIdleConnsPerHost is used"; `MaxConnsPerHost` doc "On limit violation, dials will block. Zero means no limit."; `errTooManyIdleHost = errors.New("http: putIdleConn: too many idle connections for host")`; `maxPostCloseReadBytes = 256 << 10` and `maxPostCloseReadTime = 50 * time.Millisecond` for draining a body closed early.
- Go, [src/net/http/transport_pool.go](https://github.com/golang/go/blob/master/src/net/http/transport_pool.go) - primary: `poolPutIdleConnLocked()` returns `errTooManyIdleHost` when `len(ent.idleConns) >= t.maxIdleConnsPerHost()`, and the caller closes the connection. Same check in `tryPutIdleConn()` in [go1.23 transport.go](https://github.com/golang/go/blob/release-branch.go1.23/src/net/http/transport.go).
- Go, [src/net/http/client.go](https://github.com/golang/go/blob/master/src/net/http/client.go) - primary: "If the Body is not both read to EOF and closed, the Client's underlying RoundTripper (typically Transport) may not be able to re-use a persistent TCP connection".
- Linux kernel, [include/net/tcp.h](https://github.com/torvalds/linux/blob/master/include/net/tcp.h) - primary: `#define TCP_TIMEWAIT_LEN (60*HZ)`.
- Linux kernel, [Documentation/networking/ip-sysctl.rst](https://github.com/torvalds/linux/blob/master/Documentation/networking/ip-sysctl.rst) - primary: `ip_local_port_range` "The default values are 32768 and 60999"; `tcp_tw_reuse` "2 - enable for loopback traffic only ... Default: 2".

**Key primary-source detail:** the pool does not queue or age out excess connections. On return, the put path checks the per-host idle count first and, if it's already at 2, returns `errTooManyIdleHost` and the healthy connection is closed immediately. The global `MaxIdleConns: 100` never gets a chance to matter for a single hot upstream.

Verified by release branch: `maxPostCloseReadBytes` (auto-drain on Close) is absent in release-branch.go1.24 through go1.26 and present in release-branch.go1.27; `DefaultMaxIdleConnsPerHost = 2` is present in all of them.

Derived (author's arithmetic): 60999 - 32768 + 1 = 28,232 ports; 28,232 / 60 s = ~470 new connections/s to one destination ip:port before `connect()` fails with EADDRNOTAVAIL. The "tuned for many-hosts programs" explanation for the default is the author's interpretation, labeled as such in the post.

---

## LinkedIn Post

"Reuse one http.Client and Go pools your connections." True. It pools exactly 2 per host. Everything else your service just opened gets closed the moment the request ends.

The number is in net/http/transport.go:

const DefaultMaxIdleConnsPerHost = 2

DefaultTransport sets MaxIdleConns: 100 across all hosts, which looks generous. But when a response finishes and the connection tries to re-enter the pool, the put path checks one thing first: len(idleConns) >= maxIdleConnsPerHost(). If true, it returns errTooManyIdleHost and the connection is closed. No queue, no grace period.

Now picture a service fanning out 100 concurrent HTTP/1.1 calls to one upstream. 100 connections open. 2 go back to the pool. 98 are closed by your side. The next burst dials 98 fresh ones, with a fresh TLS handshake each if it's HTTPS.

And because your client closed first, your kernel holds each of those sockets in TIME_WAIT. TCP_TIMEWAIT_LEN is 60 seconds. The default ephemeral range is 32768 to 60999: 28,232 ports. To a single upstream ip:port, that's a ceiling of roughly 470 new connections per second before connect() starts failing with "cannot assign requested address." tcp_tw_reuse won't rescue you by default either: its default of 2 means loopback only.

The obvious fix people reach for is raising ulimits, widening the port range, or adding a sidecar. All of that treats the symptom. The connection was healthy. Go threw it away on purpose.

The contrarian move is boring: set MaxIdleConnsPerHost to roughly your real per-host concurrency, and consider MaxConnsPerHost so bursts block instead of dial. Then read bodies to EOF before Close. client.go is explicit that an unread body may stop the connection from being reused. Go 1.27's transport finally drains on Close, but only up to 256 KiB and 50 ms.

Why is the default 2? My read: DefaultTransport is tuned for a program that talks to many hosts a little, like a crawler or a CLI, not a microservice that hammers three hosts a lot. A default has to be safe for everyone, so it's optimal for almost no one. And HTTP/2 over TLS mostly hides it, since one multiplexed connection covers a whole burst.

The real cost isn't the 98 handshakes. It's that the failure shows up as a network error on a box with perfectly good network, and nobody thinks to look at a constant from the standard library.

#Golang #Microservices #SystemDesign #Networking

---

## Twitter Version

"Reuse one http.Client, Go pools connections."

It pools 2. Per host.

const DefaultMaxIdleConnsPerHost = 2

100 concurrent HTTP/1.1 calls to one upstream: 2 go back to the pool, 98 hit errTooManyIdleHost and get closed.

Your side closed first, so they sit in TIME_WAIT for 60 s. 28,232 default ephemeral ports / 60 s = ~470 new conns/s to that ip:port. Then: "cannot assign requested address."

Widening the port range treats the symptom. Set MaxIdleConnsPerHost to your real concurrency. Read bodies to EOF.

A safe default is optimal for almost no one.

---

## Diagram

See `2026-11-13-go-http-maxidleconnsperhost-two-time-wait.excalidraw` (side-by-side contrarian layout: left lane is the default transport, 100 conns -> 2 pooled / 98 closed -> 60 s TIME_WAIT -> 28,232 ports / 60 s = ~470 conns/s ceiling; right lane is the tuned transport with MaxIdleConnsPerHost, MaxConnsPerHost, body draining, and the HTTP/2 caveat). Palette: orange + violet, no red/green.
