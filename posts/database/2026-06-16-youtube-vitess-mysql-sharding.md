---
date: 2026-06-16
company: YouTube
slug: youtube-vitess-mysql-sharding
category: database
post_type: confessional
opening_style: cold_fact
---

## Sources

- Vitess History (primary): https://vitess.io/docs/20.0/overview/history/
- SE Daily — Vitess with Sugu Sougoumarane: https://softwareengineeringdaily.com/2018/05/15/vitess-scaling-mysql-with-sugu-sougoumarane/
- Changelog Podcast #485 — Deepthi Sigireddi, Vitess maintainer: https://changelog.com/podcast/485
- Kubernetes Podcast Ep. 81 — Vitess: https://kubernetespodcast.com/episode/081-vitess/
- PlanetScale origin story (TechCrunch): https://techcrunch.com/2018/12/13/planetscale/

---

## LinkedIn Post

YouTube scaled MySQL to hundreds of nodes. The database wasn't the problem. The 500 engineers who had to know how it was sharded were.

By 2010, YouTube's data lived across many MySQL instances. Every service that queried user data, video metadata, or watch history had to be shard-aware: route this request to shard 1, that one to shard 7. When a shard filled up and needed to be split, you didn't just resize a database. You updated every service that talked to it.

The obvious fix was to replace MySQL with something that handled sharding natively — Cassandra, HBase, something designed for horizontal scale from the ground up. But YouTube had years of tooling, schemas, and operational runbooks built around MySQL. MySQL worked. It was fast, predictable, and well-understood. The problem wasn't the database. It was the cognitive overhead of making every engineer responsible for where the data lived.

So in 2010, Sugu Sougoumarane and Mike Solomon started building Vitess.

The idea: don't change the database, change how you connect to it. Put a query router — VTGate — between your applications and MySQL. It knows the sharding topology and routes queries transparently. Your application sends a normal SQL query. VTGate figures out which shard owns the data. If you reshard, you update the proxy config, not fifty services.

That solved routing. There was a harder problem: online schema changes.

A 200GB MySQL table can't be ALTER TABLE'd in production. The table lock can hold for hours. Vitess added online DDL — schema changes that run as background operations without blocking reads or writes.

YouTube open sourced Vitess in 2012. By 2019, it was a CNCF graduated project. It now powers Slack, Pinterest, GitHub, and PlanetScale — a company built entirely on managed Vitess.

The honest reflection: not replacing MySQL was the right call. Not because MySQL is infinitely scalable, but because the proxy model kept everything reliable about MySQL while hiding everything painful about operating it at scale.

Not every database problem needs a new database. Sometimes it needs a smarter door.

#SystemDesign #Databases #MySQL #Vitess #Engineering

---

**Character count: ~2,180**

---

## Twitter / X Version

YouTube's database lived across hundreds of MySQL shards.

Every service that touched it had to know exactly which shard to query.

When a shard filled up and split? You didn't resize the DB. You updated every service that knew about it.

This is the hidden cost of application-level sharding.

In 2010, Sugu Sougoumarane and Mike Solomon started building Vitess.

The insight: don't replace the database. Change how you connect to it.

VTGate sits between your apps and MySQL. Your app sends a normal SQL query. VTGate handles the routing.

Reshard? Update VTGate. Not 50 services.

The other hard problem: ALTER TABLE on a 200GB table in production = hours of table locks.

Vitess added online DDL. Schema changes run in the background. Reads and writes continue.

YouTube open sourced it in 2012. CNCF graduated in 2019. Now powers Slack, Pinterest, GitHub, and PlanetScale.

The honest part: not replacing MySQL was the right call.

The proxy model preserved everything reliable about MySQL while hiding everything painful about operating it at scale.

Not every database problem needs a new database.

---

## Diagram (Excalidraw)

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [
    {
      "id": "before-title", "type": "text", "x": 80, "y": 15, "width": 320, "height": 28,
      "angle": 0, "strokeColor": "#c92a2a", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false, "text": "BEFORE VITESS (2009)",
      "fontSize": 16, "fontFamily": 1, "textAlign": "center", "verticalAlign": "top",
      "containerId": null, "originalText": "BEFORE VITESS (2009)"
    },
    {
      "id": "svc-a-before", "type": "rectangle", "x": 30, "y": 60, "width": 110, "height": 44,
      "angle": 0, "strokeColor": "#495057", "backgroundColor": "#dee2e6",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": {"type": 3},
      "boundElements": [], "updated": 1, "link": null, "locked": false
    },
    {
      "id": "svc-a-before-txt", "type": "text", "x": 30, "y": 75, "width": 110, "height": 20,
      "angle": 0, "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false, "text": "Service A",
      "fontSize": 14, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle",
      "containerId": null, "originalText": "Service A"
    },
    {
      "id": "svc-b-before", "type": "rectangle", "x": 180, "y": 60, "width": 110, "height": 44,
      "angle": 0, "strokeColor": "#495057", "backgroundColor": "#dee2e6",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": {"type": 3},
      "boundElements": [], "updated": 1, "link": null, "locked": false
    },
    {
      "id": "svc-b-before-txt", "type": "text", "x": 180, "y": 75, "width": 110, "height": 20,
      "angle": 0, "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false, "text": "Service B",
      "fontSize": 14, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle",
      "containerId": null, "originalText": "Service B"
    },
    {
      "id": "svc-c-before", "type": "rectangle", "x": 330, "y": 60, "width": 130, "height": 44,
      "angle": 0, "strokeColor": "#495057", "backgroundColor": "#dee2e6",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": {"type": 3},
      "boundElements": [], "updated": 1, "link": null, "locked": false
    },
    {
      "id": "svc-c-before-txt", "type": "text", "x": 330, "y": 75, "width": 130, "height": 20,
      "angle": 0, "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false, "text": "50+ Services",
      "fontSize": 14, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle",
      "containerId": null, "originalText": "50+ Services"
    },
    {
      "id": "router-before", "type": "rectangle", "x": 135, "y": 160, "width": 220, "height": 55,
      "angle": 0, "strokeColor": "#c92a2a", "backgroundColor": "#ffe3e3",
      "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": {"type": 3},
      "boundElements": [], "updated": 1, "link": null, "locked": false
    },
    {
      "id": "router-before-txt", "type": "text", "x": 135, "y": 170, "width": 220, "height": 35,
      "angle": 0, "strokeColor": "#c92a2a", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false, "text": "Shard Router\n(hardcoded in each service)",
      "fontSize": 13, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle",
      "containerId": null, "originalText": "Shard Router\n(hardcoded in each service)"
    },
    {
      "id": "mysql1-before", "type": "rectangle", "x": 30, "y": 280, "width": 120, "height": 44,
      "angle": 0, "strokeColor": "#0b7285", "backgroundColor": "#e3fafc",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": {"type": 3},
      "boundElements": [], "updated": 1, "link": null, "locked": false
    },
    {
      "id": "mysql1-before-txt", "type": "text", "x": 30, "y": 295, "width": 120, "height": 20,
      "angle": 0, "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false, "text": "MySQL Shard 1",
      "fontSize": 13, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle",
      "containerId": null, "originalText": "MySQL Shard 1"
    },
    {
      "id": "mysql2-before", "type": "rectangle", "x": 180, "y": 280, "width": 120, "height": 44,
      "angle": 0, "strokeColor": "#0b7285", "backgroundColor": "#e3fafc",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": {"type": 3},
      "boundElements": [], "updated": 1, "link": null, "locked": false
    },
    {
      "id": "mysql2-before-txt", "type": "text", "x": 180, "y": 295, "width": 120, "height": 20,
      "angle": 0, "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false, "text": "MySQL Shard 2",
      "fontSize": 13, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle",
      "containerId": null, "originalText": "MySQL Shard 2"
    },
    {
      "id": "mysql3-before", "type": "rectangle", "x": 330, "y": 280, "width": 130, "height": 44,
      "angle": 0, "strokeColor": "#0b7285", "backgroundColor": "#e3fafc",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": {"type": 3},
      "boundElements": [], "updated": 1, "link": null, "locked": false
    },
    {
      "id": "mysql3-before-txt", "type": "text", "x": 330, "y": 295, "width": 130, "height": 20,
      "angle": 0, "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false, "text": "MySQL Shard N",
      "fontSize": 13, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle",
      "containerId": null, "originalText": "MySQL Shard N"
    },
    {
      "id": "before-warn", "type": "text", "x": 20, "y": 345, "width": 460, "height": 24,
      "angle": 0, "strokeColor": "#c92a2a", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false,
      "text": "✗  Resharding = update 50+ services + coordinated deploy",
      "fontSize": 13, "fontFamily": 1, "textAlign": "left", "verticalAlign": "top",
      "containerId": null, "originalText": "✗  Resharding = update 50+ services + coordinated deploy"
    },
    {
      "id": "divider", "type": "line", "x": 510, "y": 10, "width": 0, "height": 380,
      "angle": 0, "strokeColor": "#adb5bd", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "dashed", "roughness": 0,
      "opacity": 70, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false, "points": [[0, 0], [0, 380]]
    },
    {
      "id": "after-title", "type": "text", "x": 660, "y": 15, "width": 300, "height": 28,
      "angle": 0, "strokeColor": "#2b8a3e", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false, "text": "WITH VITESS",
      "fontSize": 16, "fontFamily": 1, "textAlign": "center", "verticalAlign": "top",
      "containerId": null, "originalText": "WITH VITESS"
    },
    {
      "id": "svc-a-after", "type": "rectangle", "x": 540, "y": 60, "width": 110, "height": 44,
      "angle": 0, "strokeColor": "#495057", "backgroundColor": "#dee2e6",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": {"type": 3},
      "boundElements": [], "updated": 1, "link": null, "locked": false
    },
    {
      "id": "svc-a-after-txt", "type": "text", "x": 540, "y": 75, "width": 110, "height": 20,
      "angle": 0, "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false, "text": "Service A",
      "fontSize": 14, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle",
      "containerId": null, "originalText": "Service A"
    },
    {
      "id": "svc-b-after", "type": "rectangle", "x": 690, "y": 60, "width": 110, "height": 44,
      "angle": 0, "strokeColor": "#495057", "backgroundColor": "#dee2e6",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": {"type": 3},
      "boundElements": [], "updated": 1, "link": null, "locked": false
    },
    {
      "id": "svc-b-after-txt", "type": "text", "x": 690, "y": 75, "width": 110, "height": 20,
      "angle": 0, "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false, "text": "Service B",
      "fontSize": 14, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle",
      "containerId": null, "originalText": "Service B"
    },
    {
      "id": "svc-c-after", "type": "rectangle", "x": 840, "y": 60, "width": 130, "height": 44,
      "angle": 0, "strokeColor": "#495057", "backgroundColor": "#dee2e6",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": {"type": 3},
      "boundElements": [], "updated": 1, "link": null, "locked": false
    },
    {
      "id": "svc-c-after-txt", "type": "text", "x": 840, "y": 75, "width": 130, "height": 20,
      "angle": 0, "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false, "text": "50+ Services",
      "fontSize": 14, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle",
      "containerId": null, "originalText": "50+ Services"
    },
    {
      "id": "vtgate", "type": "rectangle", "x": 655, "y": 160, "width": 180, "height": 55,
      "angle": 0, "strokeColor": "#1864ab", "backgroundColor": "#d0ebff",
      "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": {"type": 3},
      "boundElements": [], "updated": 1, "link": null, "locked": false
    },
    {
      "id": "vtgate-txt", "type": "text", "x": 655, "y": 170, "width": 180, "height": 35,
      "angle": 0, "strokeColor": "#1864ab", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false, "text": "VTGate\n(query router)",
      "fontSize": 14, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle",
      "containerId": null, "originalText": "VTGate\n(query router)"
    },
    {
      "id": "mysql1-after", "type": "rectangle", "x": 540, "y": 280, "width": 120, "height": 44,
      "angle": 0, "strokeColor": "#0b7285", "backgroundColor": "#e3fafc",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": {"type": 3},
      "boundElements": [], "updated": 1, "link": null, "locked": false
    },
    {
      "id": "mysql1-after-txt", "type": "text", "x": 540, "y": 295, "width": 120, "height": 20,
      "angle": 0, "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false, "text": "MySQL Shard 1",
      "fontSize": 13, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle",
      "containerId": null, "originalText": "MySQL Shard 1"
    },
    {
      "id": "mysql2-after", "type": "rectangle", "x": 685, "y": 280, "width": 120, "height": 44,
      "angle": 0, "strokeColor": "#0b7285", "backgroundColor": "#e3fafc",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": {"type": 3},
      "boundElements": [], "updated": 1, "link": null, "locked": false
    },
    {
      "id": "mysql2-after-txt", "type": "text", "x": 685, "y": 295, "width": 120, "height": 20,
      "angle": 0, "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false, "text": "MySQL Shard 2",
      "fontSize": 13, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle",
      "containerId": null, "originalText": "MySQL Shard 2"
    },
    {
      "id": "mysql3-after", "type": "rectangle", "x": 840, "y": 280, "width": 130, "height": 44,
      "angle": 0, "strokeColor": "#0b7285", "backgroundColor": "#e3fafc",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": {"type": 3},
      "boundElements": [], "updated": 1, "link": null, "locked": false
    },
    {
      "id": "mysql3-after-txt", "type": "text", "x": 840, "y": 295, "width": 130, "height": 20,
      "angle": 0, "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false, "text": "MySQL Shard N",
      "fontSize": 13, "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle",
      "containerId": null, "originalText": "MySQL Shard N"
    },
    {
      "id": "after-ok", "type": "text", "x": 530, "y": 345, "width": 470, "height": 24,
      "angle": 0, "strokeColor": "#2b8a3e", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false,
      "text": "✓  Resharding = update VTGate config · zero app changes",
      "fontSize": 13, "fontFamily": 1, "textAlign": "left", "verticalAlign": "top",
      "containerId": null, "originalText": "✓  Resharding = update VTGate config · zero app changes"
    },
    {
      "id": "stat-bar", "type": "text", "x": 40, "y": 400, "width": 980, "height": 24,
      "angle": 0, "strokeColor": "#495057", "backgroundColor": "transparent",
      "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
      "opacity": 100, "groupIds": [], "frameId": null, "roundness": null, "boundElements": [],
      "updated": 1, "link": null, "locked": false,
      "text": "YouTube: 70,000+ nodes  ·  20 data centers  ·  Open sourced 2012  ·  CNCF Graduated 2019  ·  Powers: Slack, Pinterest, GitHub, PlanetScale",
      "fontSize": 12, "fontFamily": 1, "textAlign": "center", "verticalAlign": "top",
      "containerId": null,
      "originalText": "YouTube: 70,000+ nodes  ·  20 data centers  ·  Open sourced 2012  ·  CNCF Graduated 2019  ·  Powers: Slack, Pinterest, GitHub, PlanetScale"
    }
  ],
  "appState": {
    "gridSize": null,
    "viewBackgroundColor": "#ffffff"
  },
  "files": {}
}
```
