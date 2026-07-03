<!-- sources -->
<!-- Primary: Evan Wallace (Figma co-founder/CTO), "Building a professional design tool on the web" — Figma Blog -->
<!-- URL: https://www.figma.com/blog/building-a-professional-design-tool-on-the-web/ -->
<!-- Mirror: https://madebyevan.com/figma/building-a-professional-design-tool-on-the-web/ -->
<!-- Mirror: https://medium.com/figma-design/building-a-professional-design-tool-on-the-web-6332ed4f1fcc -->
<!-- Primary: Evan Wallace, "WebAssembly cut Figma's load time by 3x" — Figma Blog -->
<!-- URL: https://www.figma.com/blog/webassembly-cut-figmas-load-time-by-3x/ -->
<!-- Mirror: https://madebyevan.com/figma/webassembly-cut-figmas-load-time-by-3x/ -->
<!-- Mirror: https://medium.com/figma-design/webassembly-cut-figmas-load-time-by-3x-76f3f2395164 -->
<!-- Note: full page fetch was blocked by this session's egress policy (403 on aws.amazon.com, figma.com, -->
<!-- wikipedia.org, etc.); facts and quotes below are cross-checked across multiple independent search -->
<!-- result excerpts pulling directly from the two primary posts above (Figma Blog / Made by Evan / Medium -->
<!-- all mirror identical text from Evan Wallace) rather than a single full-text fetch. -->
<!-- Key verifiable details (cross-referenced across the mirrors above): -->
<!-- 1. Figma's editor is written in C++, cross-compiled to run in the browser instead of JavaScript -->
<!-- 2. Rejected HTML/SVG/2D Canvas as the rendering layer: "HTML and SVG contain a lot of baggage and are -->
<!--    often much slower than the 2D canvas API due to DOM access" -->
<!-- 3. Built their own DOM, own compositor, own text layout engine ("we have our own DOM, our own -->
<!--    compositor, our own text layout engine") because text layout is inconsistent between browsers and -->
<!--    even inconsistent on the same browser across different platforms/OSes -->
<!-- 4. Renderer is a tile-based engine running entirely on the GPU via WebGL — masking, blurring, dithered -->
<!--    gradients, blend modes, nested layer opacity, fully anti-aliased -->
<!-- 5. Shipped first compiled to asm.js (via Emscripten) because WebAssembly wasn't yet ready; later swapped -->
<!-- 6. WebAssembly swap cut load time more than 3x, regardless of document size, with zero feature changes -->
<!-- 7. WebAssembly parses roughly 20x faster than asm.js; once a browser caches the native translation of the -->
<!--    module, a second load has virtually no load time at all -->
<!-- 8. Download size barely changed after the WASM swap — compressed asm.js and compressed WASM end up close -->
<!--    in size, so the win was parse/compile time, not bytes transferred -->

# Figma: Compiling Past the Browser

**Date:** 2026-07-03
**Company:** Figma
**Category:** performance
**Post type:** contrarian
**Opening style:** challenge_assumption
**Slug:** figma-cpp-wasm-rendering-engine
**Character count (LinkedIn):** ~2,082

---

## LinkedIn Post

Everyone assumed a serious design tool had to be a native app. Photoshop, Sketch, Illustrator — all native. Figma's founders bet the opposite: build a tool that rivals them, running entirely inside a browser tab. To get there, they had to reject most of what the browser gives you for free.

The obvious path is HTML, SVG, or the 2D canvas API — the browser's own tools for drawing things. Figma's engineering blog is blunt about why none of it worked: HTML and SVG carry the baggage of general-purpose document formats and are slow because every change touches the DOM. A canvas rendering thousands of nested, blurred, masked layers at 60fps can't afford that overhead. Text layout was worse — it renders differently between browsers, and even differently on the same browser across operating systems. Unacceptable when your whole product is pixel-perfect fidelity.

So Figma didn't optimize the web stack. It replaced it. The editor is written in C++ and compiled to run in the browser instead of JavaScript. On top of that, Figma built its own DOM, its own compositor, its own text layout engine, its own font rasterizer — a tile-based renderer that runs entirely on the GPU through WebGL, handling masking, blurring, blend modes, and layer opacity by hand instead of asking the browser to do any of it.

It first shipped compiled to asm.js, because WebAssembly wasn't ready yet. Years later, when it was, the swap paid for itself without a single feature change: load time dropped more than 3x, regardless of document size, because WebAssembly parses roughly 20x faster than asm.js and a browser can cache the native translation — the second load is nearly instant. Download size barely moved. The win was never about bytes over the wire. It was about how much of the browser's own machinery Figma could skip.

Most teams treat the browser's defaults as the ceiling. Figma treated them as a starting point to compile past. The browser was never the constraint — it was just everyone else's assumption about what a browser is for.

#SystemDesign #WebAssembly #Figma #Engineering

---

## Twitter / X Version

1/ Photoshop, Sketch, Illustrator — every serious design tool was a native app. Figma's founders decided a browser tab could do the same job. To pull it off, they had to throw out most of what a browser gives you for free.

2/ The obvious path — HTML, SVG, the 2D canvas API — didn't survive contact. HTML/SVG carry document-format baggage and choke on DOM updates. Text layout differs between browsers, even between the same browser on different OSes. Not okay when your product is pixel-perfect fidelity.

3/ So Figma replaced the stack instead of tuning it. The editor: C++, compiled to run in the browser. Then their own DOM, own compositor, own text layout engine, own font rasterizer — a tile-based renderer running entirely on the GPU via WebGL, doing masking and blend modes by hand.

4/ It shipped on asm.js first because WebAssembly wasn't ready. When WASM landed, the swap alone cut load time more than 3x, any document size — WASM parses ~20x faster and browsers cache the native translation. Download size barely changed. The win was pure parse time, not bytes.

5/ The lesson isn't "use WebAssembly." It's that the browser's defaults are a starting point, not a ceiling. Figma didn't hit a wall the browser put up. It compiled straight past it.

---

## Excalidraw Diagram

**File:** 2026-07-03-figma-cpp-wasm-rendering-engine.excalidraw
**Type:** Side-by-side architecture comparison + scaling bar chart (contrarian)
**Color scheme:** Rose (the web-native path, rejected — not "bad," just the default) vs. deep teal (what Figma built instead), with a gold stat bar for the load-time comparison. No red/green good/bad coding.
**Screenshottable stat:** "WebAssembly swap cut load time >3x, any document size · WASM parses ~20x faster than asm.js"

### Layout

```
Title: "Figma: Compiling Past the Browser"
Subtitle: "C++ compiled into the browser · own DOM, compositor, text engine, GPU renderer · load time cut >3x with WebAssembly"

[The web-native way (rejected)]                    [What Figma built]

[HTML & SVG — document-format                       [C++ engine, compiled to run in
 baggage, every change touches                       the browser (asm.js → WebAssembly)
 the DOM]                                             instead of JavaScript]

[2D Canvas API — faster, but no                     [Own DOM, own compositor,
 built-in GPU compositing,                           own text layout engine,
 blending, or tiling]                                own font rasterizer]

[Browser's text layout engine —                     [Tile-based renderer, 100% GPU
 renders differently across                          via WebGL — masking, blur, blend
 browsers, and even across OSes                      modes, layer opacity done by hand]
 on the same browser]

Load time (relative, same document):
[bar: asm.js — baseline, long bar]
[bar: WebAssembly — same code, >3x shorter]

Callout: WASM parses ~20x faster than asm.js. Browsers cache the native translation,
so a second load has virtually no load time. Download size barely changed —
the win was parse/compile time, not bytes over the wire.

Timeline: Ships on asm.js (WebAssembly not ready) → years later, swaps to WebAssembly,
          zero feature changes → load time cut >3x, any document size
```
