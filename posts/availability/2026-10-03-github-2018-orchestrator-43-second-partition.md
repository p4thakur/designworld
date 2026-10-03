---
date: 2026-10-03
company: GitHub
topic: October 2018 incident where a 43-second network partition made Orchestrator fail MySQL primaries over to US West, leaving unreplicated writes on both coasts and causing 24h11m of degraded service.
category: availability
post_type: narrative
opening_style: number_that_doesnt_add_up
slug: github-2018-orchestrator-43-second-partition
---

## Sources

- GitHub Blog, [October 21 post-incident analysis](https://github.blog/news-insights/company-news/oct21-post-incident-analysis/) — primary source: 22:52 UTC trigger (replacing failing 100G optical equipment), 43 seconds, 24h11m, Orchestrator/Raft quorum, ~40 min of writes to West, 954 unreplicated writes on a busy cluster, restore-from-backup time.
- InfoQ, [GitHub Incident Analysis Shows How to Improve Service Reliability](https://www.infoq.com/news/2018/11/github-incident-analysis/) — secondary corroboration.

**Note on sourcing:** direct fetches of github.blog and infoq.com were blocked by this environment's egress policy. Facts come from search-indexed excerpts of the primary post-incident analysis and secondary coverage. the post deliberately avoids latency figures not seen in excerpts.

**Key primary-source detail:** the 954 unreconciled writes on one cluster, and that the quorum was valid: nothing malfunctioned, the topology assumption was wrong.

---

## LinkedIn Post

GitHub's East Coast data center lost connectivity to its network hub for 43 seconds. The outage that followed lasted 24 hours and 11 minutes.

The trigger was routine: engineers were replacing failing 100G optical equipment. For 43 seconds, the primary East Coast data center couldn't talk to the East Coast hub, and by extension the rest of the world.

GitHub runs MySQL clusters with Orchestrator managing topology and failover, on top of Raft for consensus. During the partition, the Orchestrator nodes in US West and the East Coast public cloud could still reach each other and formed a quorum. By design, they did the right thing: they promoted West Coast databases to primary and pointed writes there.

But East Coast had not stopped. For those 43 seconds it kept accepting writes that never replicated west. When connectivity came back, both coasts held writes the other lacked. Neither was a clean copy of the other, so failing back to East meant losing data.

For nearly 40 minutes the application tier wrote to West. Roughly 30 minutes of that data was critical user data that could not be thrown away. One of the busiest clusters alone had 954 writes that had never reached the other side.

So GitHub made a call: keep data integrity ahead of availability. They kept the site degraded and rebuilt the East Coast clusters from backups, then reconciled. Restoring terabytes took hours, mostly decompressing, checksumming and loading. Replicas then had to catch up while traffic piled up, along with queued webhooks and Pages builds.

Two things stand out. First, nothing malfunctioned. Orchestrator behaved as configured, and the quorum was valid. The flaw was the assumption that a promoted replica would be a safe place for write traffic from an app tier still sitting in the East.

Second, the 43 seconds were never the real cost. The cost was the replication lag at the moment of failover and a restore path measured in hours.

Automated failover answers "who is primary now?" It doesn't answer "what happens to the writes the old primary took?" That second question is where the 24 hours went.

#DistributedSystems #MySQL #Postmortem #SRE

(2219 characters)

---

## Twitter Version

GitHub's East Coast data center lost connectivity for 43 seconds in Oct 2018. The outage lasted 24h 11m.

Orchestrator (Raft-based) saw the partition, got quorum from US West + a cloud node, and promoted West to primary. Correct, by design.

But East kept accepting writes for those 43 seconds that never replicated. Both coasts now had data the other didn't.

~40 minutes of writes landed on West. One busy cluster alone had 954 unreplicated writes. Failing back = data loss.

GitHub chose integrity over availability and restored East from backups. Terabytes: decompress, checksum, load. Hours.

Failover tells you who is primary. It doesn't tell you what to do with the old primary's last writes.

---

## Diagram

See `2026-10-03-github-2018-orchestrator-43-second-partition.excalidraw` (sequence/timeline: 43s partition -> promote West -> divergent writes -> 24h11m recovery).
