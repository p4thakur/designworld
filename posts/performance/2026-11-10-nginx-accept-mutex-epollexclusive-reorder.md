---
date: 2026-11-10
company: nginx
topic: accept_mutex (a cross-process lock so only one worker accepts) vs. EPOLLEXCLUSIVE, which skews load to the first worker and forces nginx to re-add the listen socket every 16 accepts.
category: performance
post_type: confessional
opening_style: cold_fact
slug: nginx-accept-mutex-epollexclusive-reorder
---

## Sources

- GitHub, nginx/nginx [src/event/ngx_event.c](https://github.com/nginx/nginx/blob/master/src/event/ngx_event.c) - primary: ngx_process_events_and_timers (trylock, NGX_POST_EVENTS, accept_mutex_delay timer cap), defaults `accept_mutex` = 0, `accept_mutex_delay` = 500 ms, mutex only enabled when worker_processes > 1.
- GitHub, nginx/nginx [src/event/ngx_event_accept.c](https://github.com/nginx/nginx/blob/master/src/event/ngx_event_accept.c) - primary: `ngx_accept_disabled = connection_n / 8 - free_connection_n`; `ngx_reorder_accept_events` and its source comment on EPOLLEXCLUSIVE skew, re-add every 16 requests.
- GitHub, nginx/nginx [src/event/modules/ngx_epoll_module.c](https://github.com/nginx/nginx/blob/master/src/event/modules/ngx_epoll_module.c) - primary: EPOLLEXCLUSIVE usage.

**Key primary-source detail:** the nginx source comment admits that with EPOLLEXCLUSIVE "most of the connections are handled by the first worker process", so nginx deletes and re-adds the listening socket to the epoll set every 16th accept to rotate the queue.

Note: blog.cloudflare.com was unreachable from the session network; all facts come from the nginx source on GitHub. No company incident is claimed, and release dates/kernel versions are deliberately not stated because they were not verified.

---

## LinkedIn Post

nginx has a lock whose only job is to decide which worker gets to call accept(). In the current source it is off by default, and the reason is a little embarrassing for everyone who tried to fix the same problem the "right" way.

The original problem is the thundering herd. Several workers all wait on the same listening socket, one connection arrives, the kernel wakes all of them, one wins accept(), the rest go back to sleep having burned a context switch. So nginx built accept_mutex: before polling, each worker tries a lock in shared memory. Only the holder adds the listen socket to its event loop. In ngx_event.c, a worker that fails the lock caps its wait at accept_mutex_delay, 500 ms by default, and retries later. A worker that holds it flags its events as posted, so it releases the lock quickly, before it processes slow work.

It also had a built-in fairness rule. After every accept, a worker computes ngx_accept_disabled = connection_n / 8 - free_connection_n. Once a worker is using more than seven eighths of its connection slots, the value goes positive and it sits out the next rounds of the lottery. A good design for 2000s kernels.

Then Linux added EPOLLEXCLUSIVE, which wakes only one waiter in the kernel. That makes the lock redundant. But it did not give a fair rotation. The nginx comment says it plainly: "Linux with EPOLLEXCLUSIVE usually notifies only the process which was first to add the listening socket to the epoll instance. As a result most of the connections are handled by the first worker process."

The workaround is in ngx_reorder_accept_events. Every 16th request on the listener, or whenever accept_disabled is positive, the worker removes the socket from epoll and adds it back. Re-adding puts it at the back of the wake order, so the other workers get a turn. The kernel gives you wakeup efficiency. The balancing is still your job.

None of this was a mistake at the time. The lock was right for the kernel that existed. EPOLLEXCLUSIVE was right for the herd. The gap is that "wake one" and "wake fairly" are different promises, and one of them was not written down.

Today accept_mutex defaults to 0, and even when enabled it only engages with more than one worker process. SO_REUSEPORT (the reuseport listen parameter) skips the whole problem by giving each worker its own socket, and the reorder code returns early if it is set.

The trade-off did not go away. It moved from user space into the kernel's wait queue, and the load balancer for your load balancer is still sometimes you.

#nginx #Linux #SystemDesign #BackendEngineering

---

## Twitter Version

nginx has a lock whose only job is deciding which worker calls accept(). In current source it's off by default.

The lock (accept_mutex) fixed the thundering herd: only the holder polls the listen socket. Workers over 7/8 of their connection slots even sit out the lottery.

Then Linux added EPOLLEXCLUSIVE: wake one waiter. No more herd.

But nginx's own comment admits: "most of the connections are handled by the first worker process."

Fix: every 16th accept, delete and re-add the listen socket to epoll to rotate the queue.

"Wake one" and "wake fairly" are different promises.

---

## Diagram

See `2026-11-10-nginx-accept-mutex-epollexclusive-reorder.excalidraw` (timeline: thundering herd -> accept_mutex -> EPOLLEXCLUSIVE skew -> re-add every 16 accepts -> reuseport).
