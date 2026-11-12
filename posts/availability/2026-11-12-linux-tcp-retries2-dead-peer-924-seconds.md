---
date: 2026-11-12
company: Linux kernel (TCP stack)
topic: tcp_retries2=15 - a peer that vanishes mid-request keeps a Linux TCP connection "alive" for at least 924.6 s, and keepalive can't help because it refuses to run while data is unacknowledged; TCP_USER_TIMEOUT is the real bound.
category: availability
post_type: narrative
opening_style: mid_scene
slug: linux-tcp-retries2-dead-peer-924-seconds
---

## Sources

- Linux kernel, [Documentation/networking/ip-sysctl.rst](https://github.com/torvalds/linux/blob/master/Documentation/networking/ip-sysctl.rst) - primary: `tcp_retries2` "The default value of 15 yields a hypothetical timeout of 924.6 seconds and is a lower bound for the effective timeout"; RFC 1122 recommends at least 100 s (value >= 8). `tcp_retries1` default 3 only "reports this suspicion to the network layer". Keepalive defaults: 2 hours, 9 probes, 75 s interval.
- Linux kernel, [include/net/tcp.h](https://github.com/torvalds/linux/blob/master/include/net/tcp.h) - primary: `TCP_RETR2 15`, `TCP_RTO_MIN (HZ / 5)` = 200 ms, `TCP_RTO_MAX_SEC 120`, `TCP_KEEPALIVE_TIME (120*60*HZ)`, `TCP_KEEPALIVE_PROBES 9`, `TCP_KEEPALIVE_INTVL (75*HZ)`.
- Linux kernel, [net/ipv4/tcp_timer.c](https://github.com/torvalds/linux/blob/master/net/ipv4/tcp_timer.c) - primary: `tcp_model_timeout()` (doubling up to `ilog2(rto_max / rto_base)`, then linear at rto_max); `tcp_write_timeout()` where retries1 triggers only MTU probing + `__dst_negative_advice()` ("Black hole detection") and `icsk_user_timeout` replaces the retries2 model; `tcp_keepalive_timer()` with `if (tp->packets_out || !tcp_write_queue_empty(sk)) goto resched;` under the comment `/* It is alive without keepalive 8) */`.
- Linux kernel, [include/uapi/linux/tcp.h](https://github.com/torvalds/linux/blob/master/include/uapi/linux/tcp.h) - primary: `#define TCP_USER_TIMEOUT 18 /* How long for loss retry before timeout */`.
- PostgreSQL, [doc/src/sgml/libpq.sgml](https://github.com/postgres/postgres/blob/master/doc/src/sgml/libpq.sgml) - primary: `tcp_user_timeout` "Controls the number of milliseconds that transmitted data may remain unacknowledged before a connection is forcibly closed" (present since the REL_12_STABLE docs).

**Key primary-source detail:** the keepalive timer explicitly skips any connection with unacknowledged data (`packets_out`) or a non-empty write queue, with the comment `/* It is alive without keepalive 8) */`. So the exact case where people expect keepalive to save them, a request sent to a peer that just died, is the case keepalive is coded to ignore.

Derived (author's arithmetic from `tcp_model_timeout()` with rto_base = 200 ms, rto_max = 120 s): ilog2(120 / 0.2) = 9, so the first 10 RTOs double 0.2 -> 102.4 s (sum 204.6 s), then 6 more at 120 s (720 s). 204.6 + 720 = 924.6 s, about 15.4 minutes. With retries1 = 3 the "suspicion" fires at 0.2 x (2^4 - 1) = 3 s. Real RTOs start above 200 ms (they are RTT-derived), so real timeouts are longer, which is why the doc calls 924.6 s a lower bound.

---

## LinkedIn Post

The database host just lost power mid-query. Your app sent the request 200 ms ago. No FIN, no RST, nothing will ever come back. And Linux will keep that socket open for at least 924.6 seconds.

That number is in the kernel's own docs for tcp_retries2. Default 15. Here's where it comes from.

When a segment goes unacknowledged, TCP retransmits after an RTO and doubles it each time. The floor is TCP_RTO_MIN, 200 ms. The ceiling is TCP_RTO_MAX, 120 s. tcp_model_timeout() in tcp_timer.c models exactly that: ten doublings from 0.2 s to 102.4 s (204.6 s total), then six more at 120 s (720 s). Sum: 924.6 s. And the doc calls it a lower bound, because real RTOs start above 200 ms.

The kernel does notice early. tcp_retries1 (default 3) fires after about 3 s. But read the code. All it does is MTU probing and __dst_negative_advice(), a hint to re-check the route. The comment says "Black hole detection." It assumes the path is broken, not the peer. The connection keeps living.

Meanwhile your thread is blocked in read(). Your pool reports a healthy connection. Your failover finished in 30 seconds, but this process is still talking to a corpse.

The first instinct is "turn on TCP keepalive." It doesn't help, in two ways. The defaults are 2 hours idle, then 9 probes 75 s apart. Worse, tcp_keepalive_timer() skips any socket with unacknowledged data:

if (tp->packets_out || !tcp_write_queue_empty(sk)) goto resched;

The comment above it: "It is alive without keepalive 8)". Keepalive is for idle connections. A request in flight is, by definition, not idle. The exact moment you need it is the moment it steps aside.

What actually bounds this is socket option 18, TCP_USER_TIMEOUT: how long transmitted data may stay unacknowledged before the kernel kills the connection. When set, tcp_write_timeout() uses it in place of the retries2 model. PostgreSQL's libpq exposes it as tcp_user_timeout, documented since version 12. Many drivers don't expose it at all, which is why application-level query timeouts still matter.

None of this is a bug. RFC 1122 asks for at least 100 s, and 15 retries is generous for a reason: on a lossy WAN, killing a connection too early is its own outage. The default was tuned for links that drop packets, not for peers that drop dead.

The kernel is patient. Your failover isn't. Somebody has to pick the number.

#SystemDesign #Linux #Networking #Reliability

---

## Twitter Version

Your DB host loses power mid-query. No FIN, no RST.

Linux keeps that socket alive for at least 924.6 s. It's in the docs for tcp_retries2 (default 15).

Math: RTO doubles 0.2 s -> 102.4 s (204.6 s), then 6 x 120 s cap (720 s).

"Just enable keepalive"? tcp_keepalive_timer() skips sockets with unacked data:
if (tp->packets_out ...) goto resched;
Comment: "It is alive without keepalive 8)"

The fix is TCP_USER_TIMEOUT (option 18). libpq: tcp_user_timeout.

The kernel is patient. Your failover isn't.

---

## Diagram

See `2026-11-12-linux-tcp-retries2-dead-peer-924-seconds.excalidraw` (sequence/timeline: the 16 RTO waits on one axis, the 3 s retries1 "suspicion" mark, the 30 s failover mark, the 924.6 s kill; a second lane shows keepalive stepping aside while data is in flight, and a third shows TCP_USER_TIMEOUT cutting it short). Palette: slate + amber + violet, no red/green.
