"""Live news ingestion from free RSS feeds (no API key needed).

Poll every 60-120s during market hours; dedupe by title hash.
"""
import hashlib
import re
import urllib.request
import xml.etree.ElementTree as ET

FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://www.moneycontrol.com/rss/buzzingstocks.xml",
    "https://www.livemint.com/rss/markets",
    "https://www.business-standard.com/rss/markets-106.rss",
]

def fetch_headlines(timeout=10):
    """Return list of (title, link, source). Silently skips feeds that fail."""
    out, seen = [], set()
    for url in FEEDS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                root = ET.fromstring(resp.read())
            for item in root.iter("item"):
                title = (item.findtext("title") or "").strip()
                title = re.sub(r"<[^>]+>", "", title)
                link = (item.findtext("link") or "").strip()
                h = hashlib.md5(title.lower().encode()).hexdigest()
                if title and h not in seen:
                    seen.add(h)
                    out.append((title, link, url.split("/")[2]))
        except Exception:
            continue
    return out
