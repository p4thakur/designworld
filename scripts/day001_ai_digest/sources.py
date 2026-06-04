"""
Fetches AI signal from free, no-auth sources:
- Hacker News (Algolia API)
- Reddit r/MachineLearning, r/LocalLLaMA, r/artificial
- HuggingFace trending models
- RSS feeds (TechCrunch AI, MIT Tech Review, ArXiv cs.AI)
"""

import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError

HEADERS = {"User-Agent": "Mozilla/5.0 (AI-Digest-Bot/1.0)"}
AI_KEYWORDS = [
    "llm", "gpt", "claude", "gemini", "mistral", "llama", "agent", "rag",
    "fine-tun", "embedding", "diffusion", "multimodal", "transformer",
    "openai", "anthropic", "deepmind", "huggingface", "langchain",
    "copilot", "cursor", "ai model", "foundation model", "benchmark",
    "sora", "runway", "midjourney", "stable diffusion",
]

RSS_FEEDS = {
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "MIT Tech Review": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    "ArXiv cs.AI": "https://rss.arxiv.org/rss/cs.AI",
    "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
}


def _fetch(url, timeout=10):
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except URLError:
        return None


def _is_ai_relevant(text):
    t = text.lower()
    return any(kw in t for kw in AI_KEYWORDS)


def fetch_hackernews(hours_back=24, limit=30):
    """Top AI stories from HN via Algolia search API."""
    since = int((datetime.now(timezone.utc) - timedelta(hours=hours_back)).timestamp())
    url = (
        f"https://hn.algolia.com/api/v1/search?"
        f"query=AI+LLM+model&tags=story&numericFilters=created_at_i>{since}"
        f"&hitsPerPage={limit}"
    )
    raw = _fetch(url)
    if not raw:
        return []

    items = []
    for hit in json.loads(raw).get("hits", []):
        title = hit.get("title", "")
        if not _is_ai_relevant(title + " " + (hit.get("story_text") or "")):
            continue
        items.append({
            "source": "HackerNews",
            "title": title,
            "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
            "points": hit.get("points", 0),
            "comments": hit.get("num_comments", 0),
        })

    return sorted(items, key=lambda x: x["points"], reverse=True)[:10]


def fetch_reddit(subreddits=("MachineLearning", "LocalLLaMA", "artificial"), limit=10):
    """Hot posts from AI subreddits (no auth needed for JSON API)."""
    items = []
    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}"
        raw = _fetch(url)
        if not raw:
            continue
        for post in json.loads(raw).get("data", {}).get("children", []):
            d = post["data"]
            if d.get("stickied"):
                continue
            title = d.get("title", "")
            items.append({
                "source": f"r/{sub}",
                "title": title,
                "url": "https://reddit.com" + d.get("permalink", ""),
                "score": d.get("score", 0),
                "comments": d.get("num_comments", 0),
            })
        time.sleep(0.5)  # be polite to reddit

    return sorted(items, key=lambda x: x["score"], reverse=True)[:15]


def fetch_huggingface_trending():
    """Trending models and spaces from HuggingFace."""
    items = []

    # Trending models via HF API (no auth for public data)
    for endpoint, label in [
        ("https://huggingface.co/api/models?sort=trending&limit=10", "Model"),
        ("https://huggingface.co/api/spaces?sort=trending&limit=10", "Space"),
    ]:
        raw = _fetch(endpoint)
        if not raw:
            continue
        for entry in json.loads(raw):
            mid = entry.get("id", "")
            likes = entry.get("likes", 0)
            items.append({
                "source": f"HuggingFace ({label})",
                "title": mid,
                "url": f"https://huggingface.co/{mid}",
                "likes": likes,
            })

    return items


def fetch_rss_feeds():
    """Parse configured RSS feeds for AI articles."""
    items = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)

    for name, url in RSS_FEEDS.items():
        raw = _fetch(url)
        if not raw:
            continue
        try:
            root = ET.fromstring(raw)
        except ET.ParseError:
            continue

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        # Handle both RSS 2.0 and Atom
        entries = root.findall(".//item") or root.findall(".//atom:entry", ns)

        for entry in entries[:20]:
            title_el = entry.find("title") or entry.find("atom:title", ns)
            link_el = entry.find("link") or entry.find("atom:link", ns)
            title = (title_el.text or "").strip() if title_el is not None else ""
            link = (link_el.text or link_el.get("href", "")).strip() if link_el is not None else ""

            if not _is_ai_relevant(title):
                continue

            items.append({"source": name, "title": title, "url": link})

    return items
