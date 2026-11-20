---
date: 2026-11-20
company: Linux kernel (2012 leap second)
topic: On 2012-06-30 23:59:60 UTC the kernel stepped CLOCK_REALTIME back one second inside the timer interrupt (second_overflow() returned -1) but never called clock_was_set(), because it runs on_each_cpu() and can't be called from atomic context. Each CPU's cached hrtimer realtime offset stayed one second stale, so absolute CLOCK_REALTIME timers fired 1 s early and any deadline under 1 s away fired at once. pthread_cond_timedwait (futex FUTEX_WAIT_BITSET|FUTEX_CLOCK_REALTIME) returned ETIMEDOUT straight away, and Java, MySQL and Hadoop spun at 100% CPU. `date -s "$(date)"` fixed it by calling clock_was_set(). The kernel fix was commit bb88e924 (clock_was_set_delayed() via HRTIMER_SOFTIRQ) in 3.5. Google had avoided the problem by smearing the second.
category: stability
post_type: narrative
opening_style: mid_scene
slug: linux-2012-leap-second-hrtimer-futex-spin
---

## Sources

- Linux v3.4, [kernel/time/ntp.c](https://raw.githubusercontent.com/torvalds/linux/v3.4/kernel/time/ntp.c). Primary. `second_overflow()`: "If in leap-insert state at the end of the day, the system clock is set back one second". In `TIME_INS`, `if (secs % 86400 == 0) { leap = -1; ... printk("Clock: inserting leap second 23:59:60 UTC") }`. Runs under `spin_lock_irqsave(&ntp_lock, ...)`.
- Linux v3.4, [kernel/time/timekeeping.c](https://raw.githubusercontent.com/torvalds/linux/v3.4/kernel/time/timekeeping.c). Primary. In `logarithmic_accumulation()`: `leap = second_overflow(timekeeper.xtime.tv_sec); timekeeper.xtime.tv_sec += leap;`. No `clock_was_set()` follows. In the same file, `do_settimeofday()` and `timekeeping_inject_offset()` do call `clock_was_set()`.
- Linux v3.4, [kernel/hrtimer.c](https://raw.githubusercontent.com/torvalds/linux/v3.4/kernel/hrtimer.c). Primary. `clock_was_set()` calls `on_each_cpu(retrigger_next_event, NULL, 1)`. `retrigger_next_event()` is the only thing that rewrites `base->clock_base[HRTIMER_BASE_REALTIME].offset` from `wall_to_monotonic` and reprograms the timer.
- Linux v3.4, [kernel/futex.c](https://raw.githubusercontent.com/torvalds/linux/v3.4/kernel/futex.c). Primary. `FUTEX_CLOCK_REALTIME` sets `FLAGS_CLOCKRT` and is allowed only with `FUTEX_WAIT_BITSET` / `FUTEX_WAIT_REQUEUE_PI`. Timeouts use `hrtimer_init_on_stack(..., CLOCK_REALTIME, HRTIMER_MODE_ABS)`.
- Linux v3.5, [kernel/time/timekeeping.c](https://raw.githubusercontent.com/torvalds/linux/v3.5/kernel/time/timekeeping.c) and [kernel/hrtimer.c](https://raw.githubusercontent.com/torvalds/linux/v3.5/kernel/hrtimer.c). Primary. After the fix: `if (leap) clock_was_set_delayed();`. `clock_was_set_delayed()` is commented "If called from the timer interrupt context we defer it to softirq context". It sets `cpu_base->clock_was_set = 1` and raises `HRTIMER_SOFTIRQ`, and `run_hrtimer_softirq()` then calls `clock_was_set()`. v3.5 also adds `hrtimer_update_base()` → `ktime_get_update_offsets()`, which refreshes the offsets on every hrtimer interrupt.
- John Stultz, LKML, July 1, 2012: ["[RFC] Potential fix for leapsecond caused futex related load spikes"](https://lkml.iu.edu/hypermail/linux/kernel/1207.0/00026.html) and the [v2 cover letter](https://lists.openwall.net/linux-kernel/2012/07/01/191). Load spikes were seen "usually in MySQL, Firefox, Thunderbird, and Java". `date -s "`date`"` works because it forces `clock_was_set()`. CLOCK_REALTIME hrtimers fire one second early, and sub-second ones fire immediately. Stultz reproduced the spike with Thunderbird. The fix was merged as [tip commit bb88e924 "time: Fix leapsecond triggered hrtimer/futex load spike issue"](https://lkml.iu.edu/hypermail/linux/kernel/1207.1/00339.html), July 9, 2012, Cc stable. Note: this run could not reach lkml.iu.edu or openwall directly, so these details come from search-result excerpts.
- [Mozilla IT, "MySQL and the leap second, high CPU and the fix"](https://blog.mozilla.org/it/2012/06/30/mysql-and-the-leap-second-high-cpu-and-the-fix/), [Ubuntu LP #1020285](https://bugs.launchpad.net/ubuntu/lucid/+source/linux/+bug/1020285/comments/0) ("high CPU usage and futex lockups ... JVMs, Mysql"), and [SUSE KB 7010351](https://suse.com/support/kb/doc.php?id=7010351). These were read via search excerpts.
- [The Register, 2012-07-02](https://www.theregister.com/2012/07/02/leap_second_crashes_airlines/): Amadeus confirmed that the Altea outage, which affected Qantas check-in, was "caused by a bug in the kernel of the open-source Linux operating system". [Silicon UK](https://silicon.co.uk/workspace/leap-second-84698) lists Reddit, LinkedIn, Gawker, Mozilla (Hadoop, ElasticSearch), Yelp and Foursquare.
- Google: [Christopher Pascoe, "Time, technology and leaping seconds" (Sept 15, 2011)](https://googleblog.blogspot.com/2011/09/time-technology-and-leaping-seconds.html), with the smear `lie(t) = (1.0 - cos(pi * t / w)) / 2.0`. Also [developers.google.com/time/smear](https://developers.google.com/time/smear): smearing "since 2008", and today a 24-hour linear smear from noon to noon UTC. Both were read via search excerpts and mirrors.

**Key primary-source detail:** the leap second itself was handled correctly. `second_overflow()` stepped xtime back on schedule. What failed was a cache invalidation. hrtimers keep CLOCK_REALTIME timers on the monotonic timeline plus a per-CPU cached `REALTIME.offset`. That offset is refreshed only by `retrigger_next_event()`, which runs only from `clock_was_set()`. `clock_was_set()` uses `on_each_cpu()`, which isn't allowed in the interrupt context where the leap was applied. So the cache went stale until something else called settimeofday. That is why `date -s "$(date)"`, which sets the clock to the value it already has, was the fix.

Derived/interpretive (the author's reading, not stated by a kernel source): "every short realtime wait became a busy loop" generalizes how userspace retry loops around `pthread_cond_timedwait` behave once ETIMEDOUT comes back instantly. That glibc's `pthread_cond_timedwait` reaches `FUTEX_WAIT_BITSET|FUTEX_CLOCK_REALTIME` is standard glibc behavior and was not re-read from glibc source in this run. The closing reflection on smearing (time disagrees with UTC by up to half a second at the midpoint) is derived from the 24-hour linear smear.

---

## LinkedIn Post

June 30, 2012, 23:59:60 UTC. On Linux servers everywhere the clock steps back exactly as designed. Right after, Java and MySQL processes with almost no load climb to 100% CPU and stay there.

Reddit, LinkedIn, Gawker and Mozilla's Hadoop and Elasticsearch clusters all stumbled that night. Amadeus, which runs Qantas check-in, later blamed "a bug in the kernel".

The strange part is that the leap second itself worked.

In kernel/time/ntp.c, second_overflow() saw the TIME_INS state at midnight, returned -1, and printed "Clock: inserting leap second 23:59:60 UTC". xtime went back one second. Nothing went wrong there.

The bug was a cache the leap forgot to invalidate.

High-resolution timers don't store CLOCK_REALTIME deadlines in wall time. They store them on the monotonic clock and add a cached per-CPU offset, realtime minus monotonic. Only one function rewrites that offset: retrigger_next_event(). Only one path calls it: clock_was_set(). And clock_was_set() runs on_each_cpu(), which isn't allowed in the timer interrupt where the leap was applied. So nobody called it.

Every CPU now believed wall time was one second later than it really was. Absolute CLOCK_REALTIME timers fired a second early. Any deadline less than a second away had already passed.

That second case is the common one. pthread_cond_timedwait sleeps through a futex with an absolute CLOCK_REALTIME deadline. A thread asks to wait 100ms, the kernel says ETIMEDOUT right away, the loop checks its condition and asks again. Every short timed wait in the JVM and in InnoDB had become a busy loop.

The fix that night was a single command: date -s "$(date)". It sets the clock to the time it already shows. That's pointless, except that settimeofday calls clock_was_set(), which refreshes the stale offsets.

The kernel fix, commit bb88e924, landed nine days later. The leap path now sets a per-CPU flag and raises HRTIMER_SOFTIRQ, and the softirq does the cross-CPU call. 3.5 also started refreshing the offsets on every hrtimer interrupt, so no future step could leave them stale.

Google mostly sat this one out. Since 2008 it hasn't inserted leap seconds at all. It smears them, slowing its NTP clocks so the extra second leaks in over hours. Today that's a linear 24-hour smear from noon to noon UTC.

That doesn't remove the cost, it moves it. A smeared clock is up to half a second away from real UTC at the midpoint, on purpose. The tradeoff was a clock that's slightly wrong for a day in exchange for one that never steps.

#Linux #SRE #DistributedSystems #Reliability

---

## Twitter Version

2012-06-30 23:59:60 UTC: Linux steps the clock back a second, correctly.

Then idle Java and MySQL processes hit 100% CPU. Reddit, LinkedIn, Mozilla and Qantas check-in go down.

The leap worked. The cache didn't. hrtimers keep a per-CPU realtime-minus-monotonic offset, and only clock_was_set() refreshes it. That call can't run inside the timer interrupt, so it never ran.

Every CPU thought it was a second later than it was. Every sub-second pthread_cond_timedwait returned ETIMEDOUT instantly, so the wait loops became spin loops.

Fix that night: date -s "$(date)". Set the clock to itself, which makes the kernel call clock_was_set().

Google skipped all this by smearing the second over a day.

---

## Diagram

See `2026-11-20-linux-2012-leap-second-hrtimer-futex-spin.excalidraw`. It is a narrative sequence flow across four lanes: ntp `second_overflow()` → timekeeper xtime −1 s → hrtimer per-CPU REALTIME.offset (stale, highlighted) → futex/pthread_cond_timedwait → app. The stale-offset box carries the screenshot number: "every deadline < 1 s → ETIMEDOUT now". A side panel shows the missing call `clock_was_set()` with the `date -s "$(date)"` workaround and the 3.5 fix (`clock_was_set_delayed()` → HRTIMER_SOFTIRQ). Palette: navy, amber and slate, with no red or green.
