---
date: 2026-10-07
company: Dropbox
topic: Nucleus, the Rust rewrite of Dropbox's desktop sync engine - three trees, a single control thread, and deterministic randomized testing replacing OS-scheduled threads and global locks.
category: storage
post_type: narrative
opening_style: mid_scene
slug: dropbox-nucleus-three-trees-sync-engine
---

## Sources

- Dropbox Tech, [Rewriting the heart of our sync engine](https://dropbox.tech/infrastructure/rewriting-the-heart-of-our-sync-engine) - primary: four-year rebuild, Remote/Local/Synced trees, Synced Tree as merge base, Rust types to design away invalid states.
- Dropbox Tech, [Testing sync at Dropbox](https://dropbox.tech/infrastructure/-testing-our-new-sync-engine) - primary: Sync Engine Classic threading and global locks, single control thread, CanopyCheck, Trinity, seeded deterministic runs, tens of millions of nightly randomized runs.
- InfoQ, [Dropbox testing sync engine](https://www.infoq.com/news/2020/04/dropbox-testing-sync-engine) - secondary corroboration.

**Note on sourcing:** direct fetches of dropbox.tech were blocked by this environment's egress policy. Facts come from search-indexed excerpts of the two primary posts plus InfoQ. Figures not seen in excerpts were left out.

**Key primary-source detail:** Trinity mocks more of the system than CanopyCheck, so it cannot shrink failing cases as easily - the more emergent behavior you test, the less you can perturb input without behavior diverging.

---

## LinkedIn Post

Picture a sync test that fails on Tuesday, passes on Wednesday, and nothing in the code changed.

That was the risk inside Dropbox's Sync Engine Classic. Components were free to fork threads internally and coordinated through a set of global locks. Execution order belonged to the operating system, so a bug that depended on one particular interleaving might appear once a month, on one machine, and never again.

Dropbox spent four years rebuilding it from scratch as Nucleus, in Rust. The interesting part isn't the language.

The first decision was the data model. Nucleus represents state as three trees: what the remote filesystem looks like, what the local one looks like, and the last state known to be fully synced. That third tree does the heavy lifting. Each node in it acts like a merge base in version control, so the engine can answer the one question every sync bug comes back to: did the user change this file locally, or did it change on dropbox.com? Two trees alone can't tell you which side moved.

The second decision was to take scheduling away from the OS. Nucleus keeps all control logic on a single thread. Only I/O and hashing go to background threads, and in tests even those can be serialized onto the main thread. Same inputs, same order, same result.

That makes randomized testing honest. Tests run from a pseudo-random seed, and the seed is logged, so a failure on a build server replays exactly on a laptop. Tens of millions of randomized runs execute every night.

Two tools split the work. CanopyCheck tests the three trees converging from arbitrary starting states, and because it mocks so much, it can shrink a failing case to something readable. Trinity goes after concurrency in the engine at large, injecting async behavior, I/O failures and timing changes.

Trinity pays for its realism. It mocks less, so it can't minimize failures as cleanly. The more emergent behavior a test exercises, the less you can trim its input before the behavior itself changes.

Dropbox didn't remove that tradeoff. They made it explicit: one tool for small and shrinkable, one for broad and messy.

#SystemDesign #Rust #DistributedSystems #Testing

---

## Twitter Version

Picture a sync test that fails Tuesday, passes Wednesday, no code change.

Sync Engine Classic let components fork threads and coordinate via global locks. The OS decided ordering. Bugs were interleavings.

The rewrite, Nucleus (Rust, four years), made two moves.

1) Three trees: remote, local, last-synced. The synced tree is a merge base, so "who changed this file?" has an answer.

2) One control thread. I/O and hashing in the background, serializable in tests. Seeded runs replay exactly. Tens of millions of randomized runs a night.

CanopyCheck shrinks failures well. Trinity, more realistic, can't. Realism and debuggability trade off, so they built both.

---

## Diagram

See `2026-10-07-dropbox-nucleus-three-trees-sync-engine.excalidraw` (sequence/flow: Classic's OS-scheduled threads vs Nucleus' single control thread, with the three trees converging).
