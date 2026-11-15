---
date: 2026-11-15
company: Python websockets / ws (Node.js) / zlib
topic: WebSocket permessage-deflate with context takeover keeps a live zlib compressor + decompressor per connection; at zlib defaults (windowBits 15, memLevel 8) that is ~316 KiB per connection. Python websockets ships 12/5 (64 KiB) by default; ws disables compression on the server by default and caps global zlib concurrency at 10.
category: real-time
post_type: structured
opening_style: number_doesnt_add_up
slug: websocket-permessage-deflate-context-takeover-memory
---

## Sources

- python-websockets, [docs/topics/compression.rst](https://github.com/python-websockets/websockets/blob/main/docs/topics/compression.rst) - primary: context takeover "requires retaining the compression context and state between messages, which increases the memory footprint of a connection." Benchmark table on a JSON corpus: windowBits 15 / memLevel 8 = **316 KiB per connection**, -10% size, +10% time vs default; **12 / 5 = 64 KiB** (the shipped server default); 10 / 3 = 37 KiB but +70% size; no context takeover = 14 KiB but +350% size. Server compression window is "always 12", but the decompression window "may be 12 or 15 depending on whether the client supports configuring it." Option `require_client_max_window_bits`.
- python-websockets, [src/websockets/extensions/permessage_deflate.py](https://github.com/python-websockets/websockets/blob/main/src/websockets/extensions/permessage_deflate.py) - primary: default server factory `server_max_window_bits=12, client_max_window_bits=12, compress_settings={"memLevel": 5}`.
- madler/zlib, [zconf.h](https://github.com/madler/zlib/blob/master/zconf.h) - primary: deflate memory = `(1 << (windowBits+2)) + (1 << (memLevel+9))`, "128K for windowBits=15 + 128K for memLevel = 8 (default values)"; inflate = `1 << windowBits`, "32K for windowBits=15 ... plus about 7 kilobytes".
- websockets/ws, [README.md](https://github.com/websockets/ws/blob/master/README.md) - primary: permessage-deflate "is disabled by default on the server and enabled by default on the client. It adds a significant overhead in terms of performance and memory consumption"; Node.js concurrency "can lead to catastrophic memory fragmentation" ([nodejs/node#8871](https://github.com/nodejs/node/issues/8871)).
- websockets/ws, [lib/permessage-deflate.js](https://github.com/websockets/ws/blob/master/lib/permessage-deflate.js) and [doc/ws.md](https://github.com/websockets/ws/blob/master/doc/ws.md) - primary: a module-level `zlibLimiter` ("Intentionally global; it's the global thread pool that's an issue"), `concurrencyLimit` default 10; `threshold` default 1024 bytes (payloads smaller are not compressed when context takeover is disabled).
- RFC 7692 (Compression Extensions for WebSocket) - the negotiated parameters `server_no_context_takeover`, `client_no_context_takeover`, `server_max_window_bits`, `client_max_window_bits` (names as implemented in both libraries above; RFC host not reachable from this run, parameter names verified via the two implementations).

**Key primary-source detail:** the 316 KiB vs 64 KiB table in the python-websockets docs, and the asymmetry behind it: a server can always shrink the window it compresses *with*, but shrinking the window it decompresses *with* needs the client to support `client_max_window_bits`. If the client doesn't, the server still allocates the full 32 KiB inflate window, unless you set `require_client_max_window_bits=True` and accept no compression for those clients.

Arithmetic (author's, from the zlib formula): 15/8 deflate = 128 KiB + 128 KiB = 256 KiB, inflate 32 KiB + ~7 KiB, ~295 KiB before small objects, consistent with the measured 316 KiB. 100,000 connections x 316 KiB = ~30 GiB; x 64 KiB = ~6 GiB.

---

## LinkedIn Post

A WebSocket server with 100,000 mostly idle connections. Each sends a few tiny JSON messages a minute. Turn on compression at zlib defaults and the compression state alone costs about 30 GB of RAM.

Not the messages. The state.

Here's where it comes from.

WebSocket compression (permessage-deflate, RFC 7692) has a mode called context takeover. Instead of compressing each message on its own, the compressor keeps its history between messages. Your 40th {"type":"price","symbol":...} message compresses down to almost nothing, because zlib has already seen the 39 before it.

That's why it works so well for JSON streams. It's also why it's expensive. The history has to live somewhere, and it lives in a zlib stream that stays open for the whole lifetime of the connection. One compressor, one decompressor, per socket.

zlib's own header gives you the formula. Deflate needs (1 << (windowBits+2)) + (1 << (memLevel+9)) bytes. At the defaults, windowBits 15 and memLevel 8, that's 128K + 128K. Inflate adds another 32K.

The Python websockets library measured it on a JSON corpus: 316 KiB per connection at zlib defaults.

So the maintainers made a call that looks backwards at first. The server default is windowBits 12, memLevel 5. That's 64 KiB per connection, 5x less, and the cost is payloads about 10% bigger than the max setting. They stopped there on purpose: at windowBits 10 the output is 70% bigger, and without context takeover it's 350% bigger.

The detail most people miss is that the two directions aren't symmetric. A server can always shrink the window it compresses with. Shrinking the window it decompresses with needs the client to support client_max_window_bits. If the client doesn't, the server still holds a full 32K inflate window for that socket.

Node's ws went further. Compression is off by default on the server, with a README warning about "catastrophic memory fragmentation" under concurrent zlib use. Its fix is a module-level limiter that allows 10 concurrent zlib calls across the whole process. The code comment: "Intentionally global; it's the global thread pool that's an issue."

The general rule: a setting that's per-message on paper can be per-connection in memory. On a server with a long tail of idle sockets, that's the number that counts.

#WebSockets #SystemDesign #RealTime #Performance

---

## Twitter Version

100,000 idle WebSockets. Compression at zlib defaults. ~30 GB of RAM, and none of it is messages.

permessage-deflate with context takeover keeps a live zlib stream per socket so message #40 compresses against #1 through #39.

zlib's formula at windowBits 15 / memLevel 8: 128K + 128K deflate, 32K inflate. Python websockets measured 316 KiB per connection.

Their default: 12 / 5. 64 KiB. Payloads ~10% bigger.

Node's ws: off by default on the server, plus one process-wide limit of 10 concurrent zlib calls.

Per-message on paper. Per-connection in RAM.

---

## Diagram

See `2026-11-15-websocket-permessage-deflate-context-takeover-memory.excalidraw`: a before/after comparison. Left column "zlib defaults (15 / 8)": a tall stacked bar per connection (deflate window 128K, deflate hash 128K, inflate 32K) = 316 KiB, then "x 100,000 sockets = ~30 GiB". Right column "websockets default (12 / 5)": short bar = 64 KiB, "x 100,000 = ~6 GiB", "payloads ~10% bigger". Bottom strip: the trade-off curve from the benchmark table (37 KiB / +70% size; 14 KiB no takeover / +350% size) and the asymmetry note (server can shrink its compress window alone; shrinking the decompress window needs client_max_window_bits). Palette: indigo + sand + slate, no red/green.
