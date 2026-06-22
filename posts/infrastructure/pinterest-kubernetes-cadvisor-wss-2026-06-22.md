# Pinterest: When Monitoring Became the Bug

**Date:** 2026-06-22  
**Slug:** `pinterest-kubernetes-cadvisor-wss`  
**Category:** infrastructure  
**Post type:** structured case study  
**Opening style:** specific_number  

---

**Primary sources:**
- Pinterest Engineering Blog: "Debugging the One-in-a-Million Failure: Migrating Pinterest's Search Infrastructure to Kubernetes" (2025) — https://medium.com/pinterest-engineering/debugging-the-one-in-a-million-failure-migrating-pinterests-search-infrastructure-to-kubernetes-bef9af9dabf4
- Google cAdvisor GitHub Issue #3679: "Default cadvisor configs caused 80x increase in P100 tail latencies for high-memory containers" — https://github.com/google/cadvisor/issues/3679

---

## LinkedIn Post

1 in every million search requests was taking 5 seconds. Pinterest's expected max was under 60ms. The same system, running on Kubernetes, with production index sizes, was silently regressing.

P50 and P99 looked healthy. Only the very tail betrayed it.

Pinterest runs Manas, their in-house search system. When a leaf node starts, it memory-maps the entire search index — these can reach hundreds of gigabytes. The secondary ranking index can exceed a terabyte.

The migration to Kubernetes was otherwise clean. Functional tests passed. Latency metrics looked normal across all percentiles — except the very tail.

The team ran a systematic elimination. They used kill -STOP to suspend processes one at a time: logging agents, stats pipelines, security daemons, Pinterest-specific infrastructure. They watched the numbers. Each time, no change.

The spikes kept coming.

Then they suspended cAdvisor — the monitoring agent that ships by default in virtually every Kubernetes cluster — and the spikes disappeared immediately.

cAdvisor collects a metric called container_referenced_bytes by default. It uses Brendan Gregg's working set size (WSS) estimation: scan all page table entries, count the access bits, then clear every single one. PinCompute runs cAdvisor every 30 seconds — meaning this scan happens twice a minute, every minute.

For a container with a few hundred megabytes of memory, this is invisible overhead. For a Manas leaf node with 100+ GB of memory-mapped index, scanning and clearing the entire page table twice per minute causes enough memory contention to stall the process — just long enough, just often enough, to hit about 1 request per million with a 5-second delay.

The fix was one configuration line: disable WSS estimation on PinCompute nodes.

Two things are worth keeping.

First: the culprit wasn't search logic, query routing, or gRPC. It was a monitoring agent doing exactly what it was designed to do — in a context where its design assumption (small container footprint) didn't hold.

Second: the bug was invisible below production index sizes. It couldn't be reproduced in staging. It only appeared after a full migration with real 100GB+ indices.

At high enough memory footprint, your observability tooling can become the source of the failure it was supposed to detect.

#SystemDesign #Kubernetes #InfrastructureEngineering #SearchEngineering

---

**Character count:** ~2,385 (target: 2,000–2,500 ✓)  
**First 140 chars hook:** "1 in every million search requests was taking 5 seconds. Pinterest's expected max was under 60ms. The same system, running on Kubernetes, w..." ✓

---

## Twitter Thread

Pinterest migrated their search infra to Kubernetes. Tests passed. P50 and P99 looked fine.

Then they found it: 1 in every million requests was taking 5 seconds. Expected max: 60ms.

That's 83x worse. And it was invisible in staging.

---

Pinterest's search system (Manas) memory-maps its entire index when a leaf node starts.

Leaf nodes: 100GB+ of mapped memory.
Secondary ranking index: can exceed 1TB.

The migration was clean. This only showed up at production index sizes, after the full move.

---

They debugged by suspending processes one at a time: kill -STOP.

Logging agents. Stats pipelines. Security daemons. Pinterest-specific infra.

Nothing changed.

---

Then they suspended cAdvisor — the default Kubernetes monitoring agent.

Spikes vanished.

---

cAdvisor collects container_referenced_bytes by default.

It implements WSS estimation: scan all page table entries, count access bits, clear them all.

Every 30 seconds.

For a typical container: trivial. For 100GB+ of mapped memory: enough to stall the process.

---

Fix: one config line. Disable WSS estimation for PinCompute nodes.

The lesson: the culprit wasn't their search logic, query routing, or Kubernetes itself. It was a monitoring agent doing its job — in a context where its assumptions didn't hold.

At high enough memory footprint, observability can become the failure.

---

## Excalidraw Diagram

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [
    {
      "id": "elem_title",
      "type": "text",
      "x": 100,
      "y": 15,
      "width": 1000,
      "height": 36,
      "angle": 0,
      "strokeColor": "#1e1e1e",
      "backgroundColor": "transparent",
      "fillStyle": "solid",
      "strokeWidth": 1,
      "strokeStyle": "solid",
      "roughness": 0,
      "opacity": 100,
      "groupIds": [],
      "frameId": null,
      "roundness": null,
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false,
      "text": "Pinterest: The 1-in-a-Million Latency Spike",
      "fontSize": 28,
      "fontFamily": 1,
      "textAlign": "center",
      "verticalAlign": "top",
      "containerId": null,
      "originalText": "Pinterest: The 1-in-a-Million Latency Spike",
      "lineHeight": 1.25
    },
    {
      "id": "elem_subtitle",
      "type": "text",
      "x": 100,
      "y": 58,
      "width": 1000,
      "height": 24,
      "angle": 0,
      "strokeColor": "#666666",
      "backgroundColor": "transparent",
      "fillStyle": "solid",
      "strokeWidth": 1,
      "strokeStyle": "solid",
      "roughness": 0,
      "opacity": 100,
      "groupIds": [],
      "frameId": null,
      "roundness": null,
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false,
      "text": "Expected: <60ms     Observed: 5,000ms     Root cause: a default K8s monitoring agent",
      "fontSize": 14,
      "fontFamily": 1,
      "textAlign": "center",
      "verticalAlign": "top",
      "containerId": null,
      "originalText": "Expected: <60ms     Observed: 5,000ms     Root cause: a default K8s monitoring agent",
      "lineHeight": 1.25
    },
    {
      "id": "elem_before_panel",
      "type": "rectangle",
      "x": 30,
      "y": 95,
      "width": 430,
      "height": 295,
      "angle": 0,
      "strokeColor": "#1971c2",
      "backgroundColor": "#dbe4ff",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 1,
      "opacity": 100,
      "groupIds": [],
      "frameId": null,
      "roundness": {"type": 3},
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false
    },
    {
      "id": "elem_before_title",
      "type": "text",
      "x": 45,
      "y": 110,
      "width": 400,
      "height": 28,
      "angle": 0,
      "strokeColor": "#1971c2",
      "backgroundColor": "transparent",
      "fillStyle": "solid",
      "strokeWidth": 1,
      "strokeStyle": "solid",
      "roughness": 0,
      "opacity": 100,
      "groupIds": [],
      "frameId": null,
      "roundness": null,
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false,
      "text": "BEFORE: Manas on VMs",
      "fontSize": 16,
      "fontFamily": 1,
      "textAlign": "center",
      "verticalAlign": "top",
      "containerId": null,
      "originalText": "BEFORE: Manas on VMs",
      "lineHeight": 1.25
    },
    {
      "id": "elem_before_content",
      "type": "text",
      "x": 55,
      "y": 150,
      "width": 390,
      "height": 210,
      "angle": 0,
      "strokeColor": "#1e1e1e",
      "backgroundColor": "transparent",
      "fillStyle": "solid",
      "strokeWidth": 1,
      "strokeStyle": "solid",
      "roughness": 0,
      "opacity": 100,
      "groupIds": [],
      "frameId": null,
      "roundness": null,
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false,
      "text": "• Memory-maps 100GB+ search index\n• All requests: < 60ms\n• P99.999: < 60ms ✓\n\n• No cAdvisor\n• No WSS scan\n• No page-table interference",
      "fontSize": 14,
      "fontFamily": 1,
      "textAlign": "left",
      "verticalAlign": "top",
      "containerId": null,
      "originalText": "• Memory-maps 100GB+ search index\n• All requests: < 60ms\n• P99.999: < 60ms ✓\n\n• No cAdvisor\n• No WSS scan\n• No page-table interference",
      "lineHeight": 1.6
    },
    {
      "id": "elem_vsarrow",
      "type": "arrow",
      "x": 462,
      "y": 240,
      "width": 56,
      "height": 0,
      "angle": 0,
      "strokeColor": "#555555",
      "backgroundColor": "transparent",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "dashed",
      "roughness": 0,
      "opacity": 80,
      "groupIds": [],
      "frameId": null,
      "roundness": {"type": 2},
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false,
      "startBinding": null,
      "endBinding": null,
      "lastCommittedPoint": null,
      "startArrowhead": null,
      "endArrowhead": "arrow",
      "points": [[0, 0], [56, 0]]
    },
    {
      "id": "elem_vslabel",
      "type": "text",
      "x": 458,
      "y": 218,
      "width": 64,
      "height": 20,
      "angle": 0,
      "strokeColor": "#555555",
      "backgroundColor": "transparent",
      "fillStyle": "solid",
      "strokeWidth": 1,
      "strokeStyle": "solid",
      "roughness": 0,
      "opacity": 80,
      "groupIds": [],
      "frameId": null,
      "roundness": null,
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false,
      "text": "migrate",
      "fontSize": 12,
      "fontFamily": 1,
      "textAlign": "center",
      "verticalAlign": "top",
      "containerId": null,
      "originalText": "migrate",
      "lineHeight": 1.25
    },
    {
      "id": "elem_after_panel",
      "type": "rectangle",
      "x": 520,
      "y": 95,
      "width": 680,
      "height": 295,
      "angle": 0,
      "strokeColor": "#c92a2a",
      "backgroundColor": "#fff5f5",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 1,
      "opacity": 100,
      "groupIds": [],
      "frameId": null,
      "roundness": {"type": 3},
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false
    },
    {
      "id": "elem_after_title",
      "type": "text",
      "x": 535,
      "y": 110,
      "width": 650,
      "height": 28,
      "angle": 0,
      "strokeColor": "#c92a2a",
      "backgroundColor": "transparent",
      "fillStyle": "solid",
      "strokeWidth": 1,
      "strokeStyle": "solid",
      "roughness": 0,
      "opacity": 100,
      "groupIds": [],
      "frameId": null,
      "roundness": null,
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false,
      "text": "AFTER: Manas on Kubernetes",
      "fontSize": 16,
      "fontFamily": 1,
      "textAlign": "center",
      "verticalAlign": "top",
      "containerId": null,
      "originalText": "AFTER: Manas on Kubernetes",
      "lineHeight": 1.25
    },
    {
      "id": "elem_manas_box",
      "type": "rectangle",
      "x": 540,
      "y": 150,
      "width": 285,
      "height": 195,
      "angle": 0,
      "strokeColor": "#1971c2",
      "backgroundColor": "#d0ebff",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 1,
      "opacity": 100,
      "groupIds": [],
      "frameId": null,
      "roundness": {"type": 3},
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false
    },
    {
      "id": "elem_manas_text",
      "type": "text",
      "x": 550,
      "y": 162,
      "width": 265,
      "height": 170,
      "angle": 0,
      "strokeColor": "#1971c2",
      "backgroundColor": "transparent",
      "fillStyle": "solid",
      "strokeWidth": 1,
      "strokeStyle": "solid",
      "roughness": 0,
      "opacity": 100,
      "groupIds": [],
      "frameId": null,
      "roundness": null,
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false,
      "text": "Manas Leaf Node\n\n100GB+ memory-\nmapped index\n\nNormal: <60ms\nSpike: 5,000ms\n(1 in ~1M requests)",
      "fontSize": 13,
      "fontFamily": 1,
      "textAlign": "center",
      "verticalAlign": "top",
      "containerId": null,
      "originalText": "Manas Leaf Node\n\n100GB+ memory-\nmapped index\n\nNormal: <60ms\nSpike: 5,000ms\n(1 in ~1M requests)",
      "lineHeight": 1.45
    },
    {
      "id": "elem_cadvisor_box",
      "type": "rectangle",
      "x": 860,
      "y": 150,
      "width": 300,
      "height": 195,
      "angle": 0,
      "strokeColor": "#c92a2a",
      "backgroundColor": "#ffe3e3",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 1,
      "opacity": 100,
      "groupIds": [],
      "frameId": null,
      "roundness": {"type": 3},
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false
    },
    {
      "id": "elem_cadvisor_text",
      "type": "text",
      "x": 870,
      "y": 162,
      "width": 280,
      "height": 170,
      "angle": 0,
      "strokeColor": "#c92a2a",
      "backgroundColor": "transparent",
      "fillStyle": "solid",
      "strokeWidth": 1,
      "strokeStyle": "solid",
      "roughness": 0,
      "opacity": 100,
      "groupIds": [],
      "frameId": null,
      "roundness": null,
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false,
      "text": "cAdvisor (default)\n\ncontainer_referenced\n_bytes: ON\n\nEvery 30s:\n1. Scan ALL page tables\n2. Count access bits\n3. Clear every bit",
      "fontSize": 13,
      "fontFamily": 1,
      "textAlign": "center",
      "verticalAlign": "top",
      "containerId": null,
      "originalText": "cAdvisor (default)\n\ncontainer_referenced\n_bytes: ON\n\nEvery 30s:\n1. Scan ALL page tables\n2. Count access bits\n3. Clear every bit",
      "lineHeight": 1.45
    },
    {
      "id": "elem_contention_arrow",
      "type": "arrow",
      "x": 858,
      "y": 247,
      "width": -33,
      "height": 0,
      "angle": 0,
      "strokeColor": "#c92a2a",
      "backgroundColor": "transparent",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 1,
      "opacity": 100,
      "groupIds": [],
      "frameId": null,
      "roundness": {"type": 2},
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false,
      "startBinding": null,
      "endBinding": null,
      "lastCommittedPoint": null,
      "startArrowhead": null,
      "endArrowhead": "arrow",
      "points": [[0, 0], [-33, 0]]
    },
    {
      "id": "elem_contention_label",
      "type": "text",
      "x": 790,
      "y": 224,
      "width": 130,
      "height": 40,
      "angle": 0,
      "strokeColor": "#c92a2a",
      "backgroundColor": "transparent",
      "fillStyle": "solid",
      "strokeWidth": 1,
      "strokeStyle": "solid",
      "roughness": 0,
      "opacity": 100,
      "groupIds": [],
      "frameId": null,
      "roundness": null,
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false,
      "text": "memory\ncontention",
      "fontSize": 12,
      "fontFamily": 1,
      "textAlign": "center",
      "verticalAlign": "top",
      "containerId": null,
      "originalText": "memory\ncontention",
      "lineHeight": 1.25
    },
    {
      "id": "elem_fix_panel",
      "type": "rectangle",
      "x": 30,
      "y": 430,
      "width": 1170,
      "height": 115,
      "angle": 0,
      "strokeColor": "#2f9e44",
      "backgroundColor": "#ebfbee",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "strokeStyle": "solid",
      "roughness": 1,
      "opacity": 100,
      "groupIds": [],
      "frameId": null,
      "roundness": {"type": 3},
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false
    },
    {
      "id": "elem_fix_title",
      "type": "text",
      "x": 45,
      "y": 446,
      "width": 1140,
      "height": 28,
      "angle": 0,
      "strokeColor": "#2f9e44",
      "backgroundColor": "transparent",
      "fillStyle": "solid",
      "strokeWidth": 1,
      "strokeStyle": "solid",
      "roughness": 0,
      "opacity": 100,
      "groupIds": [],
      "frameId": null,
      "roundness": null,
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false,
      "text": "Fix: 1 config line — disable WSS estimation (container_referenced_bytes) on PinCompute nodes",
      "fontSize": 16,
      "fontFamily": 1,
      "textAlign": "center",
      "verticalAlign": "top",
      "containerId": null,
      "originalText": "Fix: 1 config line — disable WSS estimation (container_referenced_bytes) on PinCompute nodes",
      "lineHeight": 1.25
    },
    {
      "id": "elem_fix_detail",
      "type": "text",
      "x": 45,
      "y": 482,
      "width": 1140,
      "height": 50,
      "angle": 0,
      "strokeColor": "#1e1e1e",
      "backgroundColor": "transparent",
      "fillStyle": "solid",
      "strokeWidth": 1,
      "strokeStyle": "solid",
      "roughness": 0,
      "opacity": 100,
      "groupIds": [],
      "frameId": null,
      "roundness": null,
      "isDeleted": false,
      "boundElements": null,
      "updated": 1750550000000,
      "link": null,
      "locked": false,
      "text": "Spikes disappeared immediately after disabling.\nAt high memory cardinality, observability tooling can become the source of the failure it was meant to detect.",
      "fontSize": 13,
      "fontFamily": 1,
      "textAlign": "center",
      "verticalAlign": "top",
      "containerId": null,
      "originalText": "Spikes disappeared immediately after disabling.\nAt high memory cardinality, observability tooling can become the source of the failure it was meant to detect.",
      "lineHeight": 1.4
    }
  ],
  "appState": {
    "gridSize": null,
    "viewBackgroundColor": "#ffffff"
  }
}
```
