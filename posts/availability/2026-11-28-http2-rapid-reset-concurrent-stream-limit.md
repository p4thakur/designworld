---
date: 2026-11-28
company: HTTP/2 Rapid Reset (CVE-2023-44487; Google, Go x/net/http2, nghttp2)
topic: HTTP/2 bounds a connection by SETTINGS_MAX_CONCURRENT_STREAMS, which counts open streams, not work. RST_STREAM is unilateral and takes effect immediately, so a client that sends HEADERS then RST_STREAM never exceeds the limit while the server has already allocated stream state, decompressed headers, mapped the URL and possibly proxied to a backend. Google absorbed a peak above 398M rps in August 2023. Go's fix (CVE-2023-39325) caps running handler goroutines at MaxConcurrentStreams (default 250), queues the rest, skips streams reset while queued, and sends GOAWAY ENHANCE_YOUR_CALM once the queue exceeds 4x the limit. nghttp2 uses a per-connection token bucket: 1,000 resets burst, refilled at 33/s. Attackers adapted with batch-wait-cancel (evades per-second RST limits) and over-opening streams. Google scores connections (>100 requests, >50% cancelled) and closes the whole connection with an immediate GOAWAY.
category: availability
post_type: narrative
opening_style: mid_scene
slug: http2-rapid-reset-concurrent-stream-limit
---

## Sources

- Google Cloud Blog, Juho Snellman and Daniele Iamartino, [How it works: The novel HTTP/2 'Rapid Reset' DDoS attack](https://cloud.google.com/blog/products/identity-security/how-it-works-the-novel-http2-rapid-reset-ddos-attack), October 10, 2023. Primary.
  - "a novel HTTP/2-based DDoS attack which peaked in August... the largest attack surpassing 398 million requests per second... did not lead to any outages."
  - "in practice clients may open 100 streams per request and the servers process these requests in parallel... This will typically lead to almost 100 times higher utilization of each connection."
  - "The protocol does not require the client and server to coordinate the cancellation in any way, the client may do it unilaterally... before any other data from that TCP connection is processed."
  - "By explicitly canceling the requests, the attacker never exceeds the limit on the number of concurrent open streams. The number of in-flight requests is no longer dependent on the round-trip time (RTT), but only on the available network bandwidth."
  - "the server will still have to do significant amounts of work for canceled requests, such as allocating new stream data structures, parsing the query and doing header decompression, and mapping the URL to a resource. For reverse proxy implementations, the request may be proxied to the backend server before the RST_STREAM frame is processed."
  - Cancelling before a response is written "reduces downlink (server/proxy to attacker) bandwidth."
  - Variant 1 "opens a batch of streams at once, waits for some time, and then cancels those streams... may bypass mitigations that are based on just the rate of inbound RST_STREAM frames (such as allow at most 100 RST_STREAMs per second on a connection before closing it)." Variant 2 "optimistically tries to open more concurrent streams than the server advertised"; "RFC 9113... suggests that an attempt to open too many streams should invalidate only the streams that exceeded the limit, not the entire connection."
  - "We don't expect that simply blocking individual requests is a viable mitigation... the entire TCP connection needs to be closed." The graceful two-GOAWAY process "leaves the connection vulnerable to Rapid Reset attacks for too long"; "the GOAWAY should be set up to limit stream creation immediately."
  - "if a connection has more than 100 requests with more than 50% of the given requests canceled, it could be a candidate for a mitigation response." Legitimate cancellation: "the user navigating away from the page, or applications using a long polling approach with a client-side timeout."
- golang/net, commit [b225e7ca](https://github.com/golang/net/commit/b225e7ca6dde1ef5a5ae5ce922861bda011cfabd) "http2: limit maximum handler goroutines to MaxConcurrentStreams", 2023-10-06. "Fixes golang/go#63417, Fixes CVE-2023-39325." Primary.
- golang/net master, [http2/server.go](https://github.com/golang/net/blob/master/http2/server.go). Primary. `defaultMaxStreams = 250 // TODO: make this 100 as the GFE seems to?`. `scheduleHandler()`: if `curHandlers < maxHandlers` start a goroutine, else if `len(sc.unstartedHandlers) > int(4*sc.advMaxStreams)` return `countError("too_many_early_resets", ConnectionError(ErrCodeEnhanceYourCalm))`, else queue. `handlerDone()`: "This stream was reset before its goroutine had a chance to start." and skips it.
- nghttp2 master, [lib/nghttp2_session.h](https://github.com/nghttp2/nghttp2/blob/master/lib/nghttp2_session.h) and [lib/nghttp2_session.c](https://github.com/nghttp2/nghttp2/blob/master/lib/nghttp2_session.c), [lib/nghttp2_ratelim.c](https://github.com/nghttp2/nghttp2/blob/master/lib/nghttp2_ratelim.c). Primary. `NGHTTP2_DEFAULT_STREAM_RESET_BURST 1000`, `NGHTTP2_DEFAULT_STREAM_RESET_RATE 33`. `session_update_stream_reset_ratelim()` drains one token per received RST_STREAM (server side only) and calls `nghttp2_session_terminate_session(session, NGHTTP2_INTERNAL_ERROR)` when empty. The bucket refills `rate * seconds_elapsed`, capped at burst.
- Not used: Cloudflare's and AWS's write-ups (201M and 155M rps) and RFC 9113 itself were blocked by this session's network settings. No number from them appears in the post.

**Key primary-source detail:** Go's fix doesn't add a reset counter at all. It moves the limit from "streams open" to "handler goroutines running", queues the overflow, and lets a stream that was reset while queued die without ever spawning a goroutine. The only cut-off is a queue longer than 4 × MaxConcurrentStreams, reported internally as `too_many_early_resets` and on the wire as ENHANCE_YOUR_CALM. A second detail: Go's default is 250 streams, and the source carries a TODO asking whether it should be 100 "as the GFE seems to".

Derived/interpretive (the author's reading, not stated verbatim by a source): "the limit measured concurrency, the cost was work" is the author's framing of Google's cost-asymmetry argument. The observation that nghttp2's 33/s sustained refill sits below the 100/s example Google calls bypassable is the author's comparison of the two sources; Google doesn't mention nghttp2.

---

## LinkedIn Post

The client sent a request, then cancelled it a moment later. The server did the work anyway. Repeat that fast enough and you get the 398 million requests per second Google's edge absorbed in August 2023.

HTTP/2 was built for efficiency. One TCP connection carries many streams, one request each. Google's write-up describes clients opening 100 streams per round trip instead of one, "almost 100 times higher utilization of each connection."

The brake was SETTINGS_MAX_CONCURRENT_STREAMS. It counts open streams. A cancelled stream isn't open.

RST_STREAM lets a client cancel unilaterally, effective immediately. Browsers need it when a user navigates away or a long-poll times out. The attack sends HEADERS, then RST_STREAM right behind it, over and over. The client never crosses the limit, so in-flight requests stop depending on round-trip time. Only on bandwidth.

The client pays almost nothing. By the time the reset is read, the server has allocated stream state, decompressed headers and mapped the URL. A reverse proxy may already have forwarded it to a backend. No response is written, so even the attacker's downlink stays quiet.

The patches show how hard it is to tell abuse from a browser being a browser.

Go's x/net/http2 fix (CVE-2023-39325 on Go's side) stopped counting streams and started counting goroutines. At most MaxConcurrentStreams handlers run per connection, 250 by default. New streams wait in a queue, and any stream reset while queued is dropped before a goroutine ever starts. Let the queue pass 4× the limit and the connection gets GOAWAY with ENHANCE_YOUR_CALM. That's the real error code name. The internal counter is called too_many_early_resets.

nghttp2 chose a token bucket: 1,000 resets of burst per connection, refilled at 33 per second. Empty it and the session is terminated.

Then the attackers adapted. Google describes one variant that opens a batch of streams, waits, cancels them all, and opens the next batch, which slips past anything that only counts resets per second. Another skips cancelling and simply opens more streams than advertised, betting the server rejects only the extras, which is what RFC 9113 suggests.

Google's own mitigation isn't a single threshold. It scores connections: more than 100 requests with over half cancelled makes one a candidate. And it argues that blocking individual requests won't work. You close the whole connection, with a GOAWAY that stops new streams now, not the polite two-step version.

HTTP/2's limit measured concurrency. The thing it was meant to protect was work. Those were the same number until someone sent a cancel right behind every request.

#HTTP2 #DDoS #SystemDesign #Networking

---

## Twitter Version

398M requests/sec. The trick was the cancel button.

HTTP/2 caps a connection with MAX_CONCURRENT_STREAMS. It counts open streams. Send HEADERS, then RST_STREAM straight away, and the stream is closed before it counts. The server has already parsed, decompressed and routed it.

Go's fix stopped counting streams and started counting goroutines: at most MaxConcurrentStreams (250) handlers per connection. The rest queue, resets in the queue never start, and a queue past 4× the limit gets GOAWAY ENHANCE_YOUR_CALM.

nghttp2: a token bucket of 1,000 resets, refilled at 33/s.

Attackers answered with batch-wait-cancel, which slides under per-second reset limits. Google's answer was scoring whole connections (>100 requests, >50% cancelled) and closing them.

The limit measured concurrency. The cost was work.
