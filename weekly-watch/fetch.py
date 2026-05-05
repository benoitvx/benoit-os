#!/usr/bin/env python3
"""
Veille — generic RSS/Atom collector.

Reads sources.yml, fetches each feed, filters items by date range
(default: last calendar week), writes the result to watch/watch_latest.json.

Stage 1 of the pipeline. Stage 2 (synthesis) consumes the JSON.

Adapted from benoitvx/veille-IAE — public template version.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

try:
    import yaml
except ImportError as e:
    raise SystemExit("PyYAML required: pip install pyyaml") from e


OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", Path(__file__).parent / "watch"))
OUTPUT_FILE = "watch_latest.json"
UA = "Mozilla/5.0 (compatible; weekly-watch-bot/1.0)"
SOURCES_FILE = Path(__file__).parent / "sources.yml"


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def parse_xml_lenient(raw: bytes) -> ET.Element:
    """Tolerate control chars some feeds inject (Beehiiv, etc.)."""
    text = raw.decode("utf-8", errors="replace")
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", text)
    return ET.fromstring(cleaned)


def get_last_week_range() -> tuple[date, date]:
    today = date.today()
    last_monday = today - timedelta(days=today.weekday() + 7)
    return last_monday, last_monday + timedelta(days=6)


def strip_html(s: str, limit: int = 3000) -> str:
    return re.sub(r"<[^>]+>", " ", s)[:limit].strip() if s else ""


def parse_rss(root: ET.Element, source_name: str, week_start: date, week_end: date) -> list[dict]:
    """Parse RSS 2.0 <channel><item>."""
    channel = root.find("channel")
    if channel is None:
        return []
    out = []
    for item in channel.findall("item"):
        pub_raw = item.findtext("pubDate", "")
        if not pub_raw:
            continue
        try:
            pub_date = parsedate_to_datetime(pub_raw).date()
        except Exception:
            continue
        if not (week_start <= pub_date <= week_end):
            continue
        out.append({
            "source": source_name,
            "title": item.findtext("title", ""),
            "url": item.findtext("link", ""),
            "published": pub_date.isoformat(),
            "summary": strip_html(item.findtext("description", "") or ""),
        })
    return out


def parse_atom(root: ET.Element, source_name: str, week_start: date, week_end: date) -> list[dict]:
    """Parse Atom <feed><entry>."""
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    out = []
    for entry in root.findall("atom:entry", ns):
        pub = entry.findtext("atom:published", "", ns) or entry.findtext("atom:updated", "", ns)
        if not pub:
            continue
        try:
            pub_date = datetime.fromisoformat(pub.replace("Z", "+00:00")).date()
        except ValueError:
            continue
        if not (week_start <= pub_date <= week_end):
            continue
        title = entry.findtext("atom:title", "", ns)
        link_el = entry.find("atom:link", ns)
        link = link_el.get("href", "") if link_el is not None else ""
        content_el = entry.find("atom:content", ns) or entry.find("atom:summary", ns)
        summary = strip_html(content_el.text) if content_el is not None and content_el.text else ""
        out.append({
            "source": source_name,
            "title": title,
            "url": link,
            "published": pub_date.isoformat(),
            "summary": summary,
        })
    return out


def fetch_feed(name: str, url: str, week_start: date, week_end: date) -> list[dict]:
    print(f"\n🔍 {name} — {url}")
    try:
        root = parse_xml_lenient(http_get(url))
    except Exception as e:
        print(f"  ❌ {e}")
        return []
    if root.tag and "feed" in root.tag.lower():
        items = parse_atom(root, name, week_start, week_end)
    else:
        items = parse_rss(root, name, week_start, week_end)
    print(f"  ✅ {len(items)} item(s)")
    return items


def main():
    if not SOURCES_FILE.exists():
        raise SystemExit(f"sources.yml not found — copy from sources.example.yml")

    sources = yaml.safe_load(SOURCES_FILE.read_text(encoding="utf-8"))
    week_start, week_end = get_last_week_range()
    iso_week = week_start.isocalendar()[1]
    print(f"📡 Weekly watch — S{iso_week} ({week_start} → {week_end})")

    all_articles = []
    for s in sources.get("sources", []):
        all_articles.extend(fetch_feed(s["name"], s["url"], week_start, week_end))

    result = {
        "week": iso_week,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sources": [s["name"] for s in sources.get("sources", [])],
        "articles_count": len(all_articles),
        "articles": all_articles,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / OUTPUT_FILE
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n💾 {len(all_articles)} article(s) → {output_path}")


if __name__ == "__main__":
    main()
