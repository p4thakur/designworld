<!-- sources -->
<!-- Primary: Uber Engineering, "H3: Uber's Hexagonal Hierarchical Spatial Index," Uber Blog (2018, ongoing). -->
<!--   URL: https://www.uber.com/blog/h3/ -->
<!-- Primary/technical reference: H3 open-source project documentation (Uber-originated, now community-governed). -->
<!--   URL: https://h3geo.org/docs/core-library/overview/ and https://h3geo.org/docs/core-library/restable/ -->
<!-- Note: direct WebFetch of uber.com/blog/h3, h3geo.org, and even a neutral control URL (example.com) all -->
<!--   returned HTTP 403 under this session's egress policy -- the same session-wide WebFetch outage noted in -->
<!--   the prior two days' posts, not a per-site block. Facts below are cross-checked across multiple independent -->
<!--   WebSearch result excerpts that quote or closely paraphrase the primary Uber blog post and the official H3 -->
<!--   docs, corroborated across several independent secondary sources (Geospatial World, Anagraph, Felt, -->
<!--   akshayghalme.com) that each independently repeat the same "edge effect"/surge-cliff framing and the same -->
<!--   neighbor-distance/hexagon-vs-square reasoning. -->
<!-- Key verifiable details (via search excerpts): -->
<!-- 1. Pre-H3, Uber computed surge pricing over geofenced zones/coarse grids per city. Riders near a zone -->
<!--   boundary could see a sharply different multiplier than riders meters away in the neighboring zone -->
<!--   ("edge effect" / "surge cliff"), and drivers learned to wait inside the high-multiplier zone rather than -->
<!--   cross the boundary for a lower-priced nearby fare -- from the Uber blog post and multiple summaries of it. -->
<!-- 2. H3 resolution table (h3geo.org, extrapolated/measured average edge lengths, resolutions 0-15): res 0 -->
<!--   average edge ~1,107.71 km; res 8 average edge ~0.4614 km (~461m); res 15 average edge ~0.00051 km (~0.51m). -->
<!--   16 total resolutions. Each child cell is aperture-7 (avg. ~1/7 the area of its parent). -->
<!-- 3. Resolution 8 (~0.5 km^2 per cell) is repeatedly cited across independent sources as the resolution Uber -->
<!--   commonly runs surge-pricing calculations at ("block or two" granularity). -->
<!-- 4. Square-grid neighbor asymmetry (4 edge-adjacent neighbors at distance d, 4 corner-adjacent neighbors at -->
<!--   d*sqrt(2)) vs. hexagon uniform neighbors (6 neighbors, single shared-edge distance) is standard geometric -->
<!--   fact, confirmed by the H3 docs' own stated rationale for choosing hexagons. -->
<!-- 5. H3 resolution 0 has exactly 122 base cells: 110 hexagons + 12 pentagons, one pentagon centered on each -->
<!--   vertex of the underlying icosahedron. It is topologically impossible to tile a sphere/icosahedron with -->
<!--   only hexagons (a consequence of Euler's formula) -- every H3 resolution therefore has exactly 12 pentagon -->
<!--   cells (5 neighbors instead of 6). The icosahedron is oriented per R. Buckminster Fuller's projection so -->
<!--   that all 12 vertices fall in open ocean, away from populated areas -- from H3 docs and multiple secondary -->
<!--   sources describing the same design choice. -->
<!-- 6. NOT independently verified with hard production numbers: exact current-day city count or QPS running on -->
<!--   H3 surge calculations, or an exact date/dollar figure tied to the pre-H3 "edge effect" complaints (these -->
<!--   are described qualitatively in the sources, not quantified with a specific incident metric). -->
<!-- Mechanism-level explanation of *why* uniform neighbor distance is precisely the property a gradient-style -->
<!-- price-smoothing algorithm requires, and why sphere topology forces exactly 12 pentagons via Euler's formula, -->
<!-- is standard computational-geometry/topology knowledge, used here to go one level deeper than the blog and -->
<!-- docs themselves, per the skill's sourcing guidance. -->

# Uber's H3: Why Surge Pricing Needed a Grid Where Every Neighbor Is the Same Distance Away

**Date:** 2026-07-19
**Company:** Uber
**Category:** geospatial
**Post type:** contrarian
**Opening style:** challenge_assumption
**Slug:** uber-h3-hexagonal-surge-pricing
**Character count (LinkedIn):** ~2,537

---

## LinkedIn Post

Every mapping tool you've ever used defaults to squares. Pixels are squares. Lat/lon grids are squares. Spreadsheets are squares. Uber's surge-pricing team looked at that default and threw it out — they rebuilt the map out of hexagons.

Before H3, Uber priced surge by zone: a geofenced polygon or a coarse grid laid over each city, and your multiplier was whichever cell you happened to be standing in. That's a lookup, not a price. A rider forty meters from a zone boundary could pay double the person standing next to them on the other side of an invisible line. Drivers noticed fast — Uber's own writeup calls it the "edge effect": drivers would park inside the high-multiplier zone and wait rather than cross the street for a normal fare thirty seconds away.

The obvious fix is a finer grid. It doesn't work, and the reason is geometry, not resolution. A square has two kinds of neighbors: four sharing an edge at distance d, and four sharing only a corner at distance d×1.41. Shrinking the squares doesn't remove that asymmetry — "one cell over" still means two different distances depending which of eight directions you look. You can't smoothly interpolate a price across a shape where the very notion of "one step" is direction-dependent.

Hexagons are the only regular tiling where that problem doesn't exist. Every hexagon has exactly six neighbors, every one sharing an edge, every one the same distance from center to center — no diagonals, no second distance to account for. That single property is what lets a price ripple outward from a demand hot spot like heat diffusing, cell to cell, because every step costs the same regardless of direction. Uber's H3 index builds a 16-level hierarchy on that guarantee — from ~1,108km hexagons at the coarsest resolution down to sub-meter ones at the finest — and resolution 8, roughly 461m edges, half a square kilometer per cell, is where most surge math actually runs.

It isn't free. You cannot tile a sphere with only hexagons — Euler's formula forces exactly 12 pentagon cells into existence at every single resolution, sitting at the 12 vertices of the icosahedron H3 wraps around the globe. Those 12 cells have five neighbors, not six, which is exactly the uniformity guarantee the whole design depends on. Uber didn't eliminate that cost. They hid it — orienting the icosahedron, per Buckminster Fuller's projection, so all 12 singular points land in open ocean, nowhere near a city anyone's pricing a ride in.

#SystemDesign #GeospatialIndexing #Uber #DistributedSystems

---

## Twitter / X Version

Uber used to price surge by zone. Stand 40m from the boundary line and you could pay double the person next to you. Drivers learned to camp inside the expensive zone instead of crossing the street for a normal fare.

Finer grid doesn't fix it. Squares have two neighbor distances — 4 edge-neighbors at distance d, 4 corner-neighbors at d×1.41. Shrinking the squares keeps the asymmetry.

Hexagons don't have that problem: 6 neighbors, all sharing an edge, all the exact same distance. That's what lets a price diffuse outward like heat instead of jumping at a hard line.

H3: 16 resolutions, ~1/7 area per level down. Res 8 (~461m edge, ~0.5km²) is what most surge math runs on.

Cost: you can't tile a sphere in only hexagons. 12 pentagons are topologically mandatory, every resolution, forever. Uber's fix was cartographic, not mathematical — orient the icosahedron so all 12 land in open ocean.

---

## Excalidraw Diagram

**File:** 2026-07-19-uber-h3-hexagonal-surge-pricing.excalidraw
**Type:** Structural/spatial comparison (contrarian style) — top row is the old zone-map approach and why finer squares don't fix it, bottom row is the hex-grid fix as a build-up (property → hierarchy → production resolution → result), a wide indigo box spells out the mechanism match, and a footer names the topological tradeoff.
**Color scheme:** Slate for the neutral old-design boxes, amber for the emerging problem, red for the consequence — mirroring that zones weren't a mistake, just the wrong shape for smoothing. Teal/green for the hex-grid fix row and its result. Indigo for the mechanism explainer. No default villain: squares are still the right shape for pixels and spreadsheets, just not for a gradient.
**Screenshottable stat:** "Squares: 2 neighbor distances (d, d×1.41) · Hexagons: 6 neighbors, 1 distance · res 8 ≈ 0.5 km² runs surge · 12 pentagons, every resolution, forever"

### Layout

```
Title: "Uber's H3: Why Surge Pricing Needed a Grid Where Every Neighbor Is the Same Distance Away"
Subtitle: "Squares: 2 neighbor distances (d, d×1.41)  ·  Hexagons: 6 neighbors, 1 distance  ·  res 8 ≈ 0.5 km² runs surge"

ROW 1 — THE OLD MAP, AND WHY FINER RESOLUTION DIDN'T FIX IT
[THE ZONE MAP]             →   [THE EDGE EFFECT]           →   [THE SQUARE PROBLEM]        →   [THE CONSEQUENCE]
Pre-H3, Uber priced surge      A rider 40m from a zone         Even a finer square grid        Can't smoothly interpolate
by geofenced city zones.       line could pay double the       keeps two neighbor               a price across neighbors
A rider's multiplier was       person next to them.            distances: 4 edge-               when the neighbor distance
a polygon lookup: which        Drivers idled inside the        neighbors at distance d,         depends on which of 8
zone are you standing in.      high-price zone instead of      4 corner-neighbors at            directions you're looking.
                                crossing for a normal fare.      d×1.41.                          Boundaries stay hard.

ROW 2 — THE FIX: A HEX GRID BUILT FOR UNIFORM NEIGHBORS
[ONE SHAPE, ONE DISTANCE]  →   [THE HIERARCHY]             →   [RESOLUTION 8 IN PROD]      →   [SMOOTH RIPPLE]
Hexagons are the only          H3: 16 resolutions, each        ~461m edge, ~0.5km² per         A price can now diffuse
regular tiling where every     child cell ~1/7 the area        cell — the granularity          outward from a demand
neighbor shares an edge,       of its parent. Edge length       most surge multipliers          hot spot hex by hex, like
at the same distance. 6        runs ~1,108km (res 0) down       are actually computed           heat — every step costs
neighbors, 1 distance, no      to under a meter (res 15).       and blended at.                  the same, any direction.
diagonals.

[THE MECHANISM MATCH]
Surge needs to interpolate a continuous value (price) across discrete cells — a gradient, not a lookup table. That only
works if every neighbor is the same distance away, so "one step" means one consistent thing in every direction. Squares
fail this by construction (edge- vs. corner-neighbors differ by √2); hexagons satisfy it by construction (6 neighbors,
one shared-edge distance). H3 doesn't make pricing smoother by being cleverer about zones — it changes the shape of
space so smoothing becomes arithmetic.

Footer: The tradeoff didn't disappear — it moved to the globe itself. You cannot tile a sphere with only hexagons:
Euler's formula forces exactly 12 pentagon cells into existence at every resolution, each with 5 neighbors instead of
6, breaking the exact uniformity everywhere else. Uber's fix wasn't mathematical, it was cartographic: orient the
icosahedron (per Buckminster Fuller's projection) so all 12 land in open ocean, nowhere near a city anyone is pricing
a ride in.
```
