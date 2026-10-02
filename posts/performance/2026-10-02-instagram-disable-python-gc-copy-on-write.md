---
date: 2026-10-02
company: Instagram
topic: Instagram disabled Python's garbage collector (gc.set_threshold(0) plus os._exit at shutdown) because GC writes to every object's header and silently un-shared forked worker memory; the gains later eroded as the codebase grew, leading to gc.freeze() and re-enabling GC.
category: performance
post_type: contrarian
opening_style: challenge_assumption
slug: instagram-disable-python-gc-copy-on-write
---

## Sources

- Instagram Engineering, [Dismissing Python Garbage Collection at Instagram](https://instagram-engineering.com/dismissing-python-garbage-collection-at-instagram-4dca40b29172) — primary source: Django on uWSGI prefork, copy-on-write, gc.disable() being re-enabled by a third-party library, gc.set_threshold(0), atexit.register(os._exit, 0), ~10% capacity gain.
- Instagram Engineering, [Copy-on-write friendly Python garbage collection](https://instagram-engineering.com/copy-on-write-friendly-python-garbage-collection-ad6ed5233ddf) — the follow-up that led to gc.freeze().
- Zekun Li, PyCon 2018, [There and Back Again: Disable and re-enable garbage collector at Instagram](https://speakerdeck.com/pycon2018/zekun-li-there-and-back-again-disable-and-re-enable-garbage-collector-at-instagram) — shared memory per worker 140 MB -> 225 MB, ~25% RAM saved, gains eroding as the codebase grew.
- CPython tracker, [Issue 31558: gc.freeze()](https://bugs.python.org/issue31558) — the API that came out of this.

**Note on sourcing:** direct fetches of instagram-engineering.com, bugs.python.org and medium were blocked by this environment's egress policy. Facts come from search-indexed excerpts of these primary sources. The 140 -> 225 MB and 25% RAM figures were seen only in excerpts of the talk summary, so they are attributed to the talk and worded cautiously.

**Key primary-source detail:** gc.disable() was not enough, because some third-party library would silently re-enable it. Instagram had to set the threshold to 0, and also skip interpreter shutdown cleanup (os._exit), since Py_Finalize runs a final GC that triggers copy-on-write again.

---

## LinkedIn Post

Everyone knows Python's garbage collector is there to save memory. At Instagram, it was quietly costing them memory, and turning it off bought about 10% more capacity.

Instagram's web tier ran Django under uWSGI in prefork mode: one master process loads the code, then forks dozens of workers. On Linux those workers start out sharing the master's memory pages through copy-on-write. A page only gets copied when someone writes to it. Shared pages are free. Copied pages are not.

The problem: the workers weren't writing to their data. The collector was. Each time CPython's cyclic GC runs, it walks tracked objects and updates a small header on every one of them, even the ones that stay alive. One tiny write dirties the whole 4KB page. Reference counting does the same thing on every read. So memory that should have been shared got copied, worker by worker.

The obvious fix, gc.disable(), didn't hold. Some third-party library would call gc.enable() again and the problem came back. Instagram set the collection threshold to zero instead, which no library flips back by accident.

Then a second trap. At worker exit, CPython's finalization runs cleanup and a final GC pass, touching the same pages once more. So they registered os._exit(0) as the last atexit handler and skipped the cleanup entirely.

Result: about 10% more capacity per server. According to Instagram's PyCon 2018 talk, shared memory per worker went from 140 MB to 225 MB.

Here's the part that most retellings skip. The win eroded. As the codebase grew, memory crept up, and the team ended up re-enabling GC and pushing a patch upstream: gc.freeze(), which moves all pre-fork objects into a permanent generation the collector never touches.

Disabling GC wasn't wrong. It was a patch over a deeper mismatch: a runtime that writes to memory it only reads, in a deployment that depends on never writing to it. The fix that lasted was telling the runtime which memory is off limits, not turning the whole system off.

#Python #SystemDesign #Performance #Instagram

**Character count: 2036 / 3,000**

---

## Twitter / X Thread

1/ Python's GC exists to save memory. At Instagram it was burning it. Turning it off gave them roughly 10% more capacity per server.

2/ Why: Django on uWSGI forks dozens of workers from one master. Workers share pages via copy-on-write, until something writes. The GC writes to a header on every tracked object, even live ones. One write, one 4KB page copied.

3/ gc.disable() didn't stick, since a third-party library re-enabled it. So: gc.set_threshold(0). Then os._exit(0) as the last atexit handler, because interpreter shutdown runs a final GC and dirties the pages again.

4/ Per their PyCon 2018 talk, shared memory per worker went 140 MB -> 225 MB.

5/ The twist: the gains eroded as the codebase grew. They re-enabled GC and upstreamed gc.freeze(), which marks pre-fork objects as untouchable. Don't turn the system off. Tell it what's off limits.
