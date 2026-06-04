"""
Aggregates all sources and formats a daily AI digest as markdown.
"""

from datetime import datetime, timezone
from sources import (
    fetch_hackernews,
    fetch_reddit,
    fetch_huggingface_trending,
    fetch_rss_feeds,
)


def _section(title, items, key_field, url_field="url", secondary=None):
    if not items:
        return f"\n## {title}\n_No results today._\n"

    lines = [f"\n## {title}\n"]
    for i, item in enumerate(items, 1):
        title_text = item.get(key_field, "Untitled")
        url = item.get(url_field, "")
        source = item.get("source", "")
        meta = ""
        if secondary:
            parts = [f"{s}: {item.get(s, 0)}" for s in secondary if item.get(s)]
            meta = f" _({', '.join(parts)})_" if parts else ""
        src_tag = f" `[{source}]`" if source else ""
        link = f"[{title_text}]({url})" if url else title_text
        lines.append(f"{i}. {link}{src_tag}{meta}")

    return "\n".join(lines) + "\n"


def build_digest():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"[+] Building AI digest for {today}...")

    print("  → Fetching Hacker News...")
    hn = fetch_hackernews()

    print("  → Fetching Reddit...")
    reddit = fetch_reddit()

    print("  → Fetching HuggingFace trending...")
    hf = fetch_huggingface_trending()

    print("  → Fetching RSS feeds...")
    rss = fetch_rss_feeds()

    lines = [
        f"# AI Daily Digest — {today}",
        f"\n> Auto-generated snapshot of what's moving in AI today.\n",
    ]

    lines.append(_section(
        "Hacker News — Top AI Stories",
        hn, "title",
        secondary=["points", "comments"],
    ))
    lines.append(_section(
        "Reddit — Hot AI Discussions",
        reddit, "title",
        secondary=["score", "comments"],
    ))
    lines.append(_section(
        "HuggingFace — Trending Models & Spaces",
        hf, "title",
        secondary=["likes"],
    ))
    lines.append(_section(
        "RSS — Latest AI Articles (48h)",
        rss, "title",
    ))

    lines.append(f"\n---\n_Generated at {datetime.now(timezone.utc).isoformat()} UTC_\n")

    return "\n".join(lines)
