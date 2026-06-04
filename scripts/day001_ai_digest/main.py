#!/usr/bin/env python3
"""
Day 001 — Daily AI Research Digest
Pulls trending AI content from HN, Reddit, HuggingFace, and RSS.
Saves a markdown digest to data/digests/.

Usage:
    python main.py             # save + print
    python main.py --print     # print only, don't save
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running from any directory
sys.path.insert(0, os.path.dirname(__file__))
from digest import build_digest


def main():
    parser = argparse.ArgumentParser(description="Daily AI Digest")
    parser.add_argument("--print", action="store_true", dest="print_only",
                        help="Print digest to stdout without saving")
    args = parser.parse_args()

    content = build_digest()

    if args.print_only:
        print("\n" + content)
        return

    # Save to data/digests/YYYY-MM-DD.md
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / "data" / "digests"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{today}.md"

    out_file.write_text(content, encoding="utf-8")
    print(f"\n[+] Digest saved → {out_file}")
    print("\n" + content)


if __name__ == "__main__":
    main()
