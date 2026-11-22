---
date: 2026-11-22
company: glibc malloc (and Apache Hadoop, HADOOP-7154)
topic: glibc's per-thread arenas (2.10 experimental in 2009, default by 2.15 in 2012) fixed main-arena lock contention by giving threads their own arenas, capped at 8 × online cores on 64-bit (NARENAS_FROM_NCORES). Every non-main arena heap is an mmap of HEAP_MAX_SIZE = 2 × DEFAULT_MMAP_THRESHOLD_MAX = 64 MiB, reserved PROT_NONE and aligned to 64 MiB so free() can find a chunk's arena by masking the pointer (heap_for_ptr). That alignment is the reason the reservation exists. Many-threaded JVMs on RHEL 6 saw virtual memory "explode", and Hadoop shipped export MALLOC_ARENA_MAX=${MALLOC_ARENA_MAX:-4} in hadoop-config.sh. YARN's vmem check (vmem-pmem-ratio 2.1, enabled by default) is where it hurts. The core count comes from /sys/devices/system/cpu/online, which shows host CPUs and not the container's CPU quota.
category: performance
post_type: confessional
opening_style: specific_number
slug: glibc-malloc-arenas-8x-cores-vmem-explosion
---

## Sources

- glibc master, [malloc/malloc.c](https://raw.githubusercontent.com/bminor/glibc/master/malloc/malloc.c). Primary. `#define NARENAS_FROM_NCORES(n) ((n) * (sizeof (long) == 4 ? 2 : 8))`, `.arena_test = NARENAS_FROM_NCORES (1)`, and on 64-bit `DEFAULT_MMAP_THRESHOLD_MAX (4 * 1024 * 1024 * sizeof(long))` = 32 MiB.
- glibc master, [malloc/arena.c](https://raw.githubusercontent.com/bminor/glibc/master/malloc/arena.c). Primary. `HEAP_MAX_SIZE (2 * DEFAULT_MMAP_THRESHOLD_MAX)` = 64 MiB on 64-bit, with the comment "The maximum size must be a power of two, for fast determination of which heap belongs to a chunk". `heap_for_ptr()` is `PTR_ALIGN_DOWN (ptr, max_size)`. `alloc_new_heap()` does `MMAP (NULL, max_size << 1, PROT_NONE, ...)` and trims the result to an aligned 64 MiB region, with the comment "No swap space needs to be reserved for the following large mapping". `arena_get2()` computes `narenas_limit = NARENAS_FROM_NCORES (__get_nprocs ())` unless `arena_max` is set. A thread keeps its arena in `static __thread mstate thread_arena`.
- glibc master, [sysdeps/unix/sysv/linux/getsysstats.c](https://raw.githubusercontent.com/bminor/glibc/master/sysdeps/unix/sysv/linux/getsysstats.c). Primary. `__get_nprocs()` reads `/sys/devices/system/cpu/online` first and only falls back to sched_getaffinity. CFS quota is not consulted.
- glibc master, [manual/tunables.texi](https://raw.githubusercontent.com/bminor/glibc/master/manual/tunables.texi). Primary. `glibc.malloc.arena_max` "supersedes the MALLOC_ARENA_MAX environment variable". Default 0 means "on 64-bit systems, it is 8 times the number of cores online."
- glibc [NEWS](https://raw.githubusercontent.com/bminor/glibc/master/NEWS), 2.23 entry for Bug 19048. Primary. It describes a malloc defect "present since glibc 2.15 (2012) or glibc 2.10 via --enable-experimental-malloc (2009)", which dates the per-thread arena code.
- Apache Hadoop branch-1 [bin/hadoop-config.sh](https://raw.githubusercontent.com/apache/hadoop/branch-1/bin/hadoop-config.sh). Primary. "Newer versions of glibc use an arena memory allocator that causes virtual memory usage to explode. This interacts badly with the many threads that we use in Hadoop. Tune the variable down to prevent vmem explosion." followed by `export MALLOC_ARENA_MAX=${MALLOC_ARENA_MAX:-4}`.
- [HADOOP-7154](https://issues.apache.org/jira/browse/HADOOP-7154), "Should set MALLOC_ARENA_MAX in hadoop-config.sh". Reporter Todd Lipcon, about RHEL 6's newer glibc. Fix versions 0.22.0 and 1.0.4. issues.apache.org was blocked in this run, so these details come from search-result excerpts.
- Hadoop trunk [yarn-default.xml](https://raw.githubusercontent.com/apache/hadoop/trunk/hadoop-yarn-project/hadoop-yarn/hadoop-yarn-common/src/main/resources/yarn-default.xml). Primary. `yarn.nodemanager.vmem-check-enabled` = true, `yarn.nodemanager.vmem-pmem-ratio` = 2.1.
- Also from search results and not used for numbers: a Red Hat KB note ("based on HADOOP-7154 we set MALLOC_ARENA_MAX=4. That brought our VM usage back to levels we would expect"), CASSANDRA-6126 and JBoss JBEAP-11565, which copied the same setting. devcenter.heroku.com could not be reached, so Heroku's MALLOC_ARENA_MAX guidance is not cited.

**Key primary-source detail:** the 64 MiB reservation is not waste. It exists so that `free()` can find a chunk's arena with one mask, `PTR_ALIGN_DOWN(ptr, 64 MiB)`, with no lookup table and no lock. The same choice that made free() cheap is the one that made VSZ jump. The core count comes from `/sys/devices/system/cpu/online`, so a container limited to 2 CPUs on a 64-core host gets a cap of 512 arenas.

Derived/interpretive (the author's arithmetic, not stated verbatim by a source): 8 × 16 cores = 128 arenas × 64 MiB ≈ 8 GiB of address space, and the 2-CPU container on a 64-core host gets 512 arenas, or ≈ 32 GiB. Arenas are created lazily, so these are ceilings and not typical numbers. Linking this to YARN container kills goes through the vmem-pmem-ratio of 2.1. The 2-CPU container example is the author's own illustration.

---

## LinkedIn Post

A JVM with 200 threads on a 16-core box could reserve 8 GB of address space before it allocated anything meaningful. That came from glibc's malloc, and glibc was doing what it was designed to do.

Here's the good part first. Before 2009, a multithreaded C program shared one malloc arena behind one mutex. Every thread that wanted memory waited in that line. glibc 2.10 added per-thread arenas: when a thread hits a locked arena, it gets its own, with a limit of 8 × online cores on 64-bit. Contention dropped, and by 2.15 it was the default.

The detail most people miss is that each extra arena heap is an mmap of 64 MiB, PROT_NONE, aligned to 64 MiB. That alignment is the clever part. free() finds a chunk's arena by masking the pointer down to the 64 MiB boundary, so it needs no lookup table and no global lock. The source comment says the size "must be a power of two, for fast determination of which heap belongs to a chunk."

It's cheap for the kernel, since nothing is committed. But it adds 64 MiB of VSZ per arena, and at 8 × 16 cores you can have up to 128 arenas.

Then RHEL 6 shipped the new glibc to Hadoop clusters. YARN kills containers that exceed 2.1× their physical memory in virtual memory, and that check is on by default. Healthy JVMs started dying. Hadoop added a line to hadoop-config.sh with a candid comment: the arena allocator "causes virtual memory usage to explode... Tune the variable down." The line was MALLOC_ARENA_MAX=4. Cassandra and JBoss copied it.

Containers brought a second problem. glibc counts cores by reading /sys/devices/system/cpu/online, which shows the host's CPUs. A pod limited to 2 CPUs on a 64-core node still gets a cap of 512 arenas.

No one designed this badly. In 2009 the cost was address space nobody was counting, on machines nobody was slicing up. The design stayed the same. What changed was how operators measured memory and how they shared CPUs.

#Linux #Performance #Java #Hadoop

---

## Twitter Version

glibc malloc gives each contended thread its own arena, up to 8 × cores. That was a real fix for one global malloc lock.

Each arena heap reserves 64 MiB, aligned to 64 MiB, so free() can find the owner by masking the pointer. No table, no lock.

16 cores means up to 128 arenas, or about 8 GB of VSZ. YARN kills containers above 2.1× vmem.

Hadoop's fix was one line: MALLOC_ARENA_MAX=4. The comment says the allocator "causes virtual memory usage to explode."

The core count comes from /sys/devices/system/cpu/online, so the host counts, not your pod's CPU limit.

---

## Diagram

See `2026-11-22-glibc-malloc-arenas-8x-cores-vmem-explosion.excalidraw`. It's a confessional timeline with three stops. 2009 (glibc 2.10): one arena + one mutex → per-thread arenas, 8 × cores. ~2011 (RHEL 6 + Hadoop): 128 arenas × 64 MiB ≈ 8 GiB VSZ vs YARN's 2.1× vmem check → MALLOC_ARENA_MAX=4. Today (containers): 2-CPU pod on a 64-core host → 512-arena cap. A callout under the first stop explains why 64 MiB: free() runs PTR_ALIGN_DOWN(ptr, 64 MiB) to find the arena. Palette: teal, plum and sand, with no red or green.
