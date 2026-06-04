# designworld

One small automation script per day.

## Structure

```
scripts/
  day001_ai_digest/    # Daily AI research digest from HN, Reddit, HuggingFace, RSS
  day002_*/            # Next script...
data/
  digests/             # Saved markdown digests (one per day)
```

## Scripts

| Day | Script | What it does |
|-----|--------|-------------|
| 001 | `day001_ai_digest` | Pulls trending AI content from Hacker News, Reddit, HuggingFace, and RSS feeds into a daily markdown digest |

## Running

```bash
# Run today's AI digest (saves to data/digests/YYYY-MM-DD.md)
python scripts/day001_ai_digest/main.py

# Print only, don't save
python scripts/day001_ai_digest/main.py --print
```

No API keys needed. All sources are free and public.
