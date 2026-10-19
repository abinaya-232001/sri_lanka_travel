"""Download Wikipedia thumbnails for Discover cards into public/images."""
from __future__ import annotations

import csv
import re
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = (
    ROOT.parent
    / "tourism_risk_system (1)"
    / "tourism_risk_system"
    / "data"
    / "tourist_sites.csv"
)
OUTPUT_DIR = ROOT / "public" / "images"
HEADERS = {"User-Agent": "TourCeylon-LiveData/1.0 (student project; image restore)"}


def site_image_slug(site_name: str) -> str:
    slug = site_name.lower()
    slug = re.sub(r"['\u2018\u2019]", "", slug)
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def wiki_image_url(site_name: str) -> str | None:
    queries = [site_name, f"{site_name} Sri Lanka"]
    for query in queries:
        try:
            search = requests.get(
                "https://en.wikipedia.org/w/api.php",
                headers=HEADERS,
                params={
                    "action": "opensearch",
                    "search": query,
                    "limit": 1,
                    "namespace": 0,
                    "format": "json",
                },
                timeout=12,
            )
            if search.status_code != 200:
                continue
            titles = search.json()[1]
            if not titles:
                continue
            title = titles[0].replace(" ", "_")
            summary = requests.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}",
                headers=HEADERS,
                timeout=12,
            )
            if summary.status_code != 200:
                continue
            data = summary.json()
            thumb = data.get("originalimage") or data.get("thumbnail")
            if thumb and thumb.get("source"):
                return thumb["source"]
        except Exception as exc:
            print(f"    lookup error for '{query}': {exc}")
    return None


def download(url: str, out_path: Path) -> bool:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 800:
            out_path.write_bytes(resp.content)
            return True
        print(f"    download status={resp.status_code} bytes={len(resp.content)}")
    except Exception as exc:
        print(f"    download error: {exc}")
    return False


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8")))
    print(f"Loaded {len(rows)} sites. Output: {OUTPUT_DIR}")
    ok = skip = fail = 0
    for i, row in enumerate(rows, 1):
        name = row["site_name"]
        out = OUTPUT_DIR / f"{site_image_slug(name)}.jpg"
        if out.is_file() and out.stat().st_size > 800:
            print(f"[{i}/{len(rows)}] {name} (exists)")
            skip += 1
            continue
        print(f"[{i}/{len(rows)}] {name} -> {out.name}")
        url = wiki_image_url(name)
        if url and download(url, out):
            print(f"    saved {out.stat().st_size} bytes")
            ok += 1
        else:
            print("    FAILED")
            fail += 1
        time.sleep(0.7)
    print(f"done saved={ok} skipped={skip} failed={fail}")


if __name__ == "__main__":
    main()
