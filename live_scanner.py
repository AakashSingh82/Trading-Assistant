"""Live loop: poll news feeds, analyze every new headline, print alerts.

Run during market hours:  python3 live_scanner.py
Later: replace print() with a Telegram bot call, and feed the stock scores
into signal_engine.make_signal() together with your live technical data.
"""
import time

from news_impact import analyze, format_report
from news_impact.feed import fetch_headlines

POLL_SECONDS = 90
seen = set()

print("Live news scanner started (Ctrl+C to stop)...")
while True:
    try:
        for title, link, source in fetch_headlines():
            key = title.lower()
            if key in seen:
                continue
            seen.add(key)
            r = analyze(title)
            # only alert when the news actually moves something
            if r.ranked("up") or r.ranked("down"):
                print()
                print(format_report(r))
                print(f"  Source: {source}  {link}")
    except KeyboardInterrupt:
        break
    except Exception as e:
        print("scanner error:", e)
    time.sleep(POLL_SECONDS)
