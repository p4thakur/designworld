---
date: 2026-10-28
company: gRPC
topic: gRPC balances per call, but an L4 load balancer only sees one long-lived HTTP/2 connection, so new replicas sit idle until the server starts closing connections on purpose (MAX_CONNECTION_AGE).
category: microservices
post_type: narrative
opening_style: mid_scene
slug: grpc-l4-load-balancer-max-connection-age
---

## Sources

- GitHub, [grpc/grpc - Load Balancing in gRPC](https://github.com/grpc/grpc/blob/master/doc/load-balancing.md) - primary: balancing is per call, `pick_first` is the default and sends every RPC to one address.
- GitHub, [grpc/proposal - A9 Server-side Connection Management](https://github.com/grpc/proposal/blob/master/A9-server-side-conn-mgt.md) - primary: why L4 LBs fail with HTTP/2, `MAX_CONNECTION_AGE` + GOAWAY, +/-10% jitter, stampede caveats.
- GitHub, [grpc/grpc - keepalive guide](https://github.com/grpc/grpc/blob/master/doc/keepalive.md) - primary: keepalive defaults (client disabled, server 2 hours).
- GitHub, [grpc/grpc - channel_arg_names.h](https://github.com/grpc/grpc/blob/master/include/grpc/impl/channel_arg_names.h) - primary: `grpc.max_connection_age_ms` defaults to INT_MAX (disabled).

**Key primary-source detail:** the A9 proposal's own warning that the fix can recreate the problem: a connection storm repeating at a fixed period without jitter, and GOAWAY on long-lived RPCs leaving "many old but active connections with few RPCs on them."

**Note on sourcing:** only GitHub-hosted docs were reachable from this environment. The "scale-out replica gets nothing" scenario is an inference from the A9 text ("not able to quickly distribute load away from hot nodes or to new nodes"), not a measured incident.

---

## LinkedIn Post

A team scales a gRPC service from 4 pods to 12 during a traffic spike. The dashboard shows 12 healthy pods. The CPU graph shows 4 of them on fire and 8 doing nothing.

Nothing is broken. gRPC is doing exactly what its docs say.

The load-balancing doc is explicit: balancing in gRPC happens per call, not per connection. Even one client should spread its requests across every server. But that is a client-side promise. It needs the client to know the server addresses, and the default policy, `pick_first`, connects to one address and sends every RPC there.

So teams put a Layer 4 load balancer in front. It is simple and protocol agnostic. It also balances TCP connections, not requests. HTTP/2 multiplexes everything over one connection, and clients keep it open by default after use. The A9 server-side connection management proposal says it directly: with HTTP/2 and idle connections held open, L4 load balancers cannot quickly move load off hot nodes or onto new ones.

The 8 new pods have no connections to receive. The old 4 have all of them, and nothing ever closes them. Client keepalive is disabled by default, the server default is 2 hours, and `MAX_CONNECTION_AGE` defaults to infinite.

The fix lives on the server. Set a max connection age and the server sends a GOAWAY with NO_ERROR and debug data `max_age`. In-flight RPCs finish. The client reconnects through the L4 balancer, which picks a pod again. Eventually the 12 pods share the work.

A9 is candid that this creates its own problems. Closing a connection makes the client open a new one, so closing many at once means many connects at once. That is why a +/-10% jitter is added per connection. Without it, a connection storm would repeat at a fixed period. And long-lived streams can hold a connection open past the GOAWAY, leaving "many old but active connections with few RPCs on them."

One more detail from the rationale: all of this is server-side on purpose. The service owner can roll it out without updating a single client.

Nobody designed a bug here. The protocol removed the per-request signal the balancer depended on, and the fix is to make connections expire so the balancer gets to decide again.

#gRPC #LoadBalancing #SystemDesign #Microservices

---

## Twitter Version

A gRPC service scales from 4 pods to 12.

4 pods are at 90% CPU. 8 are idle.

Why: gRPC balances per call, but an L4 load balancer only balances TCP connections. HTTP/2 puts every call on one long-lived connection, and clients keep it open. New pods never get a connection.

The server-side fix is MAX_CONNECTION_AGE: after N seconds, send GOAWAY, let in-flight RPCs finish, force a reconnect through the LB.

The spec adds +/-10% jitter per connection. Without it, the reconnect storm repeats on a fixed period.

Default is infinite.

---

## Diagram

See `2026-10-28-grpc-l4-load-balancer-max-connection-age.excalidraw` (before/after sequence: connections pinned to 4 pods vs. GOAWAY at max_age spreading across 12).
