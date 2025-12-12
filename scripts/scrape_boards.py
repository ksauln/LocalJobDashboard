"""
Best-effort discovery of Greenhouse and Lever company slugs without a GitHub token.

Approach:
- Query the public Common Crawl index for URLs under boards.greenhouse.io and jobs.lever.co.
- Extract the first path segment as the board/company slug.
- Not exhaustive; rerun periodically to refresh.

Usage:
    python scripts/scrape_boards.py --max-urls 5000

Outputs:
- data/greenhouse_slugs.txt
- data/lever_slugs.txt

Paste comma-separated values from these files into GREENHOUSE_BOARDS / LEVER_COMPANIES in your .env.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional, Set
from urllib.parse import unquote, urlparse

import requests

DATA_DIR = Path("data")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def latest_index_api() -> str:
    """Return the cdx-api URL for the latest Common Crawl index."""
    try:
        resp = requests.get("https://index.commoncrawl.org/collinfo.json", timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data[0]["cdx-api"]
    except Exception:
        # Fallback to a known recent index if lookup fails.
        return "https://index.commoncrawl.org/CC-MAIN-2025-47-index"


def extract_slug(url: str, host: str) -> Optional[str]:
    parsed = urlparse(url)
    if host not in parsed.netloc:
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if not parts:
        return None
    slug = unquote(parts[0]).strip().lower()
    slug = slug.split("?")[0]
    if SLUG_RE.match(slug):
        return slug
    return None


def collect_slugs(index_api: str, host: str, max_urls: int) -> Set[str]:
    params = {"url": f"{host}/*", "output": "json", "limit": max_urls}
    slugs: Set[str] = set()
    with requests.get(index_api, params=params, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            slug = extract_slug(data.get("url", ""), host)
            if slug:
                slugs.add(slug)
    return slugs


def write_list(path: Path, values: Set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(sorted(values)), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Greenhouse/Lever company slugs via Common Crawl index.")
    parser.add_argument("--max-urls", type=int, default=5000, help="Max index rows to pull per host.")
    parser.add_argument("--index-api", type=str, default=None, help="Override the Common Crawl cdx-api URL.")
    args = parser.parse_args()

    index_api = args.index_api or latest_index_api()
    print(f"Using Common Crawl index: {index_api}")

    print(f"Fetching Greenhouse slugs (limit {args.max_urls} index rows)...")
    gh_slugs = collect_slugs(index_api, "boards.greenhouse.io", args.max_urls)
    print(f"Found {len(gh_slugs)} Greenhouse slugs.")

    print(f"Fetching Lever slugs (limit {args.max_urls} index rows)...")
    lever_slugs = collect_slugs(index_api, "jobs.lever.co", args.max_urls)
    print(f"Found {len(lever_slugs)} Lever slugs.")

    gh_path = DATA_DIR / "greenhouse_slugs.txt"
    lever_path = DATA_DIR / "lever_slugs.txt"
    write_list(gh_path, gh_slugs)
    write_list(lever_path, lever_slugs)
    print(f"Wrote Greenhouse slugs to {gh_path}")
    print(f"Wrote Lever slugs to {lever_path}")
    print("Next: open the files and copy comma-separated lists into GREENHOUSE_BOARDS and LEVER_COMPANIES.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
