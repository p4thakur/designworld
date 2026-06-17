---
date: 2026-06-17
company: Google
topic: google-zanzibar-permissions-at-scale
category: infrastructure
post_type: contrarian
opening_style: challenge_assumption
---

<!-- Sources -->
<!-- Primary: Pang et al., "Zanzibar: Google's Consistent, Global Authorization System" -->
<!-- USENIX ATC 2019 — https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/ -->
<!-- Secondary: Authzed/SpiceDB docs, Ory Keto docs, Airbnb Himeji engineering blog (2021) -->

## LinkedIn Post

The obvious way to build permissions is a role hierarchy. Admins can do X. Users can do Y. Owners can do everything.

Google had that. Then they had to share a Google Doc with a specific person outside any role. Then make that share expire. Then check if the user was blocked. Then verify they weren't seeing content from a share that was just revoked.

Role hierarchies break when relationships become the permission.

In 2016, Google rewrote authorization from scratch. They called it Zanzibar. By 2019, it was handling Drive, Calendar, YouTube, Maps, and Cloud — 10 million client requests per second, p95 latency under 10ms globally.

The core model is disarmingly simple. Instead of roles, Zanzibar stores tuples: (user, relation, object). "alice is a viewer of document:42." Permissions are graph traversals over these tuples. If alice is a member of group:eng, and group:eng is a viewer of document:42, a traversal connects them.

Simple models hide hard problems. The "new enemy" problem: share a folder, revoke access, but the user has a cached permission for the next few seconds. In most systems, that's acceptable. In Google Drive, it's a data leak.

Zanzibar solves this with zookies — consistency tokens returned on every permission write. Any future read that includes the zookie is guaranteed to see permission state at least as new as the write. The check is linearized against the mutation.

The tradeoff is latency. Checking a permission requires a Spanner read with a timestamp bound, not a cache hit. For large groups, Zanzibar pre-indexes memberships in a layer called Leopard. Without it, a single group membership check becomes a full graph traversal on every request.

Two things make this worth studying. First, the model composes. Time-based shares, nested groups, conditional access — all tuples, not server-side special cases. Second, Zanzibar treats the new enemy problem as a correctness requirement, not an acceptable tradeoff.

Most teams won't build Zanzibar. But the model has escaped into open source: Ory Keto, SpiceDB, and Airbnb's Himeji all borrow the tuple approach. They exist because role hierarchies break at exactly the point where user relationships get complicated.

Roles model org charts. Relationships model how people actually use software.

#SystemDesign #Authorization #Infrastructure #DistributedSystems

---

**Character count: ~2,360 / 3,000**

---

## Twitter / X Thread

Google's authorization system checks permissions 10 million times per second, globally, under 10ms p95.

They don't use a role hierarchy. They never did — at this scale.

---

Zanzibar (2016) stores tuples: (user, relation, object). "alice is a viewer of document:42." Every permission check is a graph traversal over 10 trillion of these tuples.

---

The hard part isn't the graph. It's the new enemy problem.

Share a folder → revoke access → user still sees it for a few seconds because the permission is cached. Most systems: acceptable. Google Drive: a data leak.

---

Zanzibar solves this with zookies — consistency tokens tied to Spanner timestamps. Any read carrying a zookie sees permission state at least as new as the write that issued it. No stale cache.

---

The cost: every permission check is a Spanner read, not a cache hit. For large groups, a pre-indexing layer called Leopard runs ahead of requests.

---

The model escaped into open source: Ory Keto, SpiceDB, Airbnb's Himeji all borrowed the tuple approach.

They exist because role hierarchies crack at exactly the moment user relationships get complicated.

Roles model org charts. Relationships model how software is actually used.
