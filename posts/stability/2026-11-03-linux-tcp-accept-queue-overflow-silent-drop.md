---
date: 2026-11-03
company: Linux kernel
topic: Accept queue overflow - the kernel drops the final ACK silently (tcp_abort_on_overflow=0), so clients see ESTABLISHED on a connection the server never created.
category: stability
post_type: narrative
opening_style: mid_scene
slug: linux-tcp-accept-queue-overflow-silent-drop
---

## Sources

- GitHub, [torvalds/linux net/ipv4/tcp_minisocks.c](https://github.com/torvalds/linux/blob/master/net/ipv4/tcp_minisocks.c) - primary: `listen_overflow` label; with `tcp_abort_on_overflow` off it sets `acked = 1` and returns NULL, no RST.
- GitHub, [torvalds/linux net/ipv4/tcp_input.c](https://github.com/torvalds/linux/blob/master/net/ipv4/tcp_input.c) - primary: `tcp_conn_request` drops a new SYN when `sk_acceptq_is_full` and increments `LINUX_MIB_LISTENOVERFLOWS`.
- GitHub, [torvalds/linux include/net/sock.h](https://github.com/torvalds/linux/blob/master/include/net/sock.h) and [net/socket.c](https://github.com/torvalds/linux/blob/master/net/socket.c) - primary: `sk_acceptq_is_full`, and backlog capped to `somaxconn` in `__sys_listen_socket`.
- GitHub, [Documentation/networking/ip-sysctl.rst](https://github.com/torvalds/linux/blob/master/Documentation/networking/ip-sysctl.rst) - primary: somaxconn default 4096 (128 before 5.4), `tcp_abort_on_overflow` rationale, `tcp_synack_retries` 5 = 31s last retransmit / 63s final timeout.

**Note on sourcing:** all facts read directly from kernel master. The opening scene (load test, hung clients) is an illustrative composite, not a report of a specific company incident.

**Key primary-source detail:** the overflow path on the final ACK is silent by design; the kernel docs justify the default as burst recovery.

---

## LinkedIn Post

The load test passed. Production fell over at the first real traffic burst, and the server's own graphs looked fine.

Clients reported connections that opened instantly and then hung. Netstat on the client side showed ESTABLISHED. Nothing in the app logs. The process was alive, the CPU was idle-ish, and the port was open.

Here is what the Linux kernel is doing. A TCP listener has two queues. The SYN queue holds half-open connections. The accept queue holds connections that finished the handshake and are waiting for the app to call accept(). The size of the accept queue is the backlog passed to listen(), silently capped by net.core.somaxconn. That cap was 128 until Linux 5.4 and is 4096 now.

When the app is busy (GC pause, blocked event loop, a burst), the accept queue fills. Then the interesting part. In tcp_conn_request, a new SYN that arrives with a full accept queue is dropped, and LINUX_MIB_LISTENOVERFLOWS is incremented. But a connection that already sent its SYN and got a SYN-ACK is different. Its final ACK arrives, the kernel tries to create the child socket, the full check fails, and the code path labeled listen_overflow runs. With the default tcp_abort_on_overflow=0, it sets acked=1 on the request and returns NULL. No RST. No error.

So the client believes the connection is established, because from its side it is. It sends its request into a socket the server has not created. The server's request socket stays in SYN_RECV and keeps retransmitting SYN-ACK, tcp_synack_retries=5 by default, which the kernel docs put at 31 seconds to the last retransmit and 63 seconds to the final timeout. Each retransmit is another chance for the ACK to land when there is room.

The kernel docs say why this is the default: "if overflow occurred due to a burst, connection will recover." Dropping is a deliberate bet that the burst ends before the clients give up. Turning on tcp_abort_on_overflow gives faster failures, but the docs warn it "can harm clients of your server."

The fix was not in the kernel. The listen backlog in the app was 128 and the framework default had not been touched since the 128-era. And the one metric that exposed the problem, the ListenOverflows counter in nstat or netstat -s, was on no dashboard.

No one made a mistake in the kernel. A queue has to be full of something, and the design chooses to drop quietly and hope. The mistake is trusting that a handshake that succeeded means the server noticed.

#Linux #TCP #SystemDesign #SRE

(2488 characters)

---

## Twitter Version

The load test passed. Production fell over at the first burst, and the server's graphs looked fine.

Clients saw ESTABLISHED, then hung. No app logs.

Linux has two queues per listener: SYN queue, and accept queue (size = listen() backlog, capped by somaxconn: 128 before 5.4, 4096 now).

When the accept queue is full and the final ACK arrives, tcp_minisocks.c hits listen_overflow. With tcp_abort_on_overflow=0 it sets acked=1 and returns NULL. No RST. The client thinks it's connected.

The server keeps retransmitting SYN-ACK (tcp_synack_retries=5, about 63s to final timeout). The kernel docs: "connection will recover" if it was a burst.

The metric that tells you: ListenOverflows in nstat. On almost nobody's dashboard.

A handshake that succeeded doesn't mean the server noticed.

---

## Diagram

See `2026-11-03-linux-tcp-accept-queue-overflow-silent-drop.excalidraw` (sequence flow: client/kernel/app timeline showing the silent drop on the final ACK).
