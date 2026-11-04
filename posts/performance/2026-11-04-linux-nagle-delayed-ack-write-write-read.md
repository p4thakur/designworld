---
date: 2026-11-04
company: Linux kernel
topic: Nagle's algorithm only stalls when it meets the receiver's delayed ACK; the root cause is the application's write-write-read pattern, and TCP_NODELAY hides it.
category: performance
post_type: contrarian
opening_style: challenge_assumption
slug: linux-nagle-delayed-ack-write-write-read
---

## Sources

- GitHub, [torvalds/linux net/ipv4/tcp_output.c](https://github.com/torvalds/linux/blob/master/net/ipv4/tcp_output.c) - primary: `tcp_nagle_check`, `tcp_minshall_check`, `tcp_nagle_test`.
- GitHub, [torvalds/linux include/net/tcp.h](https://github.com/torvalds/linux/blob/master/include/net/tcp.h) - primary: `TCP_DELACK_MIN` = HZ/25, `TCP_DELACK_MAX` = HZ/5.
- GitHub, [torvalds/linux net/ipv4/tcp_timer.c](https://github.com/torvalds/linux/blob/master/net/ipv4/tcp_timer.c) - primary: `tcp_delack_timer_handler` doubles ATO outside pingpong mode, resets to `TCP_ATO_MIN` on exit.
- GitHub, [torvalds/linux Documentation/networking/ip-sysctl.rst](https://github.com/torvalds/linux/blob/master/Documentation/networking/ip-sysctl.rst) - primary: `tcp_pingpong_thresh` wording.
- GitHub, [golang/go src/net/tcpsock_posix.go](https://github.com/golang/go/blob/master/src/net/tcpsock_posix.go) and [tcpsock.go](https://github.com/golang/go/blob/master/src/net/tcpsock.go) - primary: `setNoDelay(fd, true)` on new connections; `SetNoDelay` doc says default is true.

**Note on sourcing:** all facts read from current master. 40 ms / 200 ms assume HZ >= 100 (the `#else` branch uses 4 jiffies). The write-write-read scenario is the standard illustrative case, not a report of a specific company incident.

**Key primary-source detail:** Minshall's variant means Nagle only waits on unacked *small* segments, so the stall needs the peer's delayed ACK to complete the deadlock.

---

## LinkedIn Post

The standard fix for "my small writes take 40 milliseconds" is setting TCP_NODELAY. It works. It is also treating a symptom, and the Linux source shows exactly which one.

The Nagle check in tcp_output.c is short. A partial segment is held back if TCP_CORK is set, or if nonagle is off, packets are still in flight, and the Minshall check says a previous small segment is unacknowledged. Minshall's variant matters: the sender only waits for an ACK of small segments, not of everything outstanding.

So Nagle alone never stalls a clean request-response exchange. The stall needs a second party. The receiver's delayed ACK timer.

The kernel defines TCP_DELACK_MIN as HZ/25, which is 40 ms on a HZ>=100 kernel, and TCP_DELACK_MAX as HZ/5, which is 200 ms. A receiver holding an ACK hoping to piggyback it on response data will sit on it for roughly that long. If the sender is also holding its second small write until that ACK arrives, both sides wait on each other until a timer fires.

The trigger is a specific code shape: write, write, read. A header goes out as one small write, the body as another. The first segment leaves immediately. The second is small, a segment is unacked, so Nagle holds it. The peer has nothing to send back yet, so it delays its ACK. 40 ms later the timer fires and everything moves.

The kernel even adapts to this. When the delack timer fires and the connection is not in pingpong mode, tcp_delack_timer_handler doubles the ACK timeout, up to TCP_DELACK_MAX. A connection that keeps hitting the stall drifts toward the 200 ms ceiling. In pingpong mode, the timer expiring exits it and resets the timeout to the minimum. The docs describe pingpong as the request-response case "for which delayed acknowledgments can provide benefits."

Go's net package sets TCP_NODELAY on every TCP connection by default (setNoDelay(fd, true) in tcpsock_posix.go). That is a defensible default for a language built for network servers. It also means many Go services never meet this stall, and engineers who move to other stacks meet it for the first time in production.

TCP_NODELAY removes the wait. It does not remove the reason the application made two tiny writes where one would do. With NODELAY on, that header and body now leave as two packets, two syscalls, two chances at loss. Gathering the message into one write (writev, a buffered writer, a flush at the message boundary) fixes the stall and the waste.

The setsockopt is the right emergency lever. The write pattern is the actual bug.

#TCP #Linux #Performance #SystemDesign

(2556 characters)

---

## Twitter Version

"Set TCP_NODELAY" is the standard fix for 40 ms stalls on small writes. It treats a symptom.

Nagle in tcp_output.c holds a partial segment only if an earlier small segment is unACKed (Minshall's variant). Alone it can't stall a clean request-response.

The second party: the receiver's delayed ACK. TCP_DELACK_MIN = HZ/25 (40 ms), TCP_DELACK_MAX = HZ/5 (200 ms).

The trigger is write, write, read. Header goes out, body is held by Nagle, the peer delays its ACK. Both wait for the timer.

The kernel doubles the ACK timeout each miss outside pingpong mode, toward 200 ms.

Go sets TCP_NODELAY by default, so Go services rarely see it.

NODELAY removes the wait. It doesn't remove the two tiny writes. Batch them: one write per message.

---

## Diagram

See `2026-11-04-linux-nagle-delayed-ack-write-write-read.excalidraw` (side-by-side sequence: write-write-read with a 40 ms wait vs a single batched write).
