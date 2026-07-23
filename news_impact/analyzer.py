"""News Impact Analyzer.

headline -> which sectors, stocks, currencies and commodities are likely to
move UP or DOWN.

Pipeline:
  1. Detect macro/policy events (events.EVENT_RULES)      -> sector-level scores
  2. Detect named companies (mappings.COMPANY_ALIASES)    -> direct stock hits
  3. Company-level events (earnings, orders, probes...)   -> score for named stock
  4. Propagate: sector score -> member stocks; named stock -> peers (dampened)
  5. Asset layer: events + direct mentions -> currency/commodity scores
  6. Blend with keyword sentiment, output ranked UP/DOWN lists
"""
import re
from dataclasses import dataclass, field

from .events import EVENT_RULES, COMPANY_EVENT_RULES
from .mappings import SECTOR_STOCKS, PEER_MAP, COMPANY_ALIASES, STOCK_SECTOR
from .assets import EVENT_ASSET_IMPACTS, ASSET_KEYWORDS
from .sentiment import score_sentiment

PEER_DAMPING = 0.5      # peer stocks get half the named stock's impact
SECTOR_TO_STOCK = 0.8   # member stocks get 80% of their sector's score
MIN_REPORT_SCORE = 1.5  # ignore noise below this absolute score


@dataclass
class NewsImpact:
    headline: str
    sentiment: float = 0.0                       # -1..+1
    events: list = field(default_factory=list)   # [(event_name, note)]
    sector_scores: dict = field(default_factory=dict)  # sector -> -10..+10
    stock_scores: dict = field(default_factory=dict)   # symbol -> -10..+10
    asset_scores: dict = field(default_factory=dict)   # currency/commodity -> -10..+10
    reasons: dict = field(default_factory=dict)        # symbol -> why

    def ranked(self, direction: str, scores=None):
        scores = self.stock_scores if scores is None else scores
        items = [(s, v) for s, v in scores.items()
                 if (v > 0 if direction == "up" else v < 0) and abs(v) >= MIN_REPORT_SCORE]
        return sorted(items, key=lambda x: -abs(x[1]))


def _find_companies(text_lc: str):
    hits = []
    for alias, symbol in COMPANY_ALIASES.items():
        if re.search(r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])", text_lc):
            hits.append(symbol)
    return list(dict.fromkeys(hits))


def analyze(headline: str) -> NewsImpact:
    text = headline.lower()
    result = NewsImpact(headline=headline, sentiment=score_sentiment(headline))

    # 1. macro / policy / sector events
    for rule in EVENT_RULES:
        if any(re.search(t, text) for t in rule["triggers"]):
            result.events.append((rule["name"], rule["note"]))
            for sector, score in rule["impacts"].items():
                prev = result.sector_scores.get(sector, 0.0)
                result.sector_scores[sector] = max(prev, score, key=abs)
            # 5a. event-driven currency/commodity impacts
            for asset, score in EVENT_ASSET_IMPACTS.get(rule["name"], {}).items():
                prev = result.asset_scores.get(asset, 0.0)
                result.asset_scores[asset] = max(prev, score, key=abs)
                result.reasons.setdefault(asset, f'{rule["name"]} event')

    # 2. named companies
    named = _find_companies(text)

    # 3. company-level events for named stocks
    company_score = 0.0
    company_event = None
    for rule in COMPANY_EVENT_RULES:
        if any(re.search(t, text) for t in rule["triggers"]):
            if abs(rule["score"]) > abs(company_score):
                company_score, company_event = rule["score"], rule["name"]

    # 4a. sector -> member stocks
    for sector, s_score in result.sector_scores.items():
        for sym in SECTOR_STOCKS.get(sector, []):
            sc = s_score * SECTOR_TO_STOCK
            if abs(sc) > abs(result.stock_scores.get(sym, 0.0)):
                result.stock_scores[sym] = sc
                result.reasons[sym] = f"{sector} sector impact"

    # 4b. named stock: direct hit (company event, else sector event, else sentiment)
    for sym in named:
        if company_score:
            direct = company_score
            why = f"named in news ({company_event})"
        else:
            sector = STOCK_SECTOR.get(sym)
            base = result.sector_scores.get(sector, 0.0)
            direct = base if base else result.sentiment * 6.0
            why = "named in news"
        boosted = direct * 1.25 if direct else direct
        if abs(boosted) > abs(result.stock_scores.get(sym, 0.0)):
            result.stock_scores[sym] = max(-10.0, min(10.0, boosted))
            result.reasons[sym] = why

        # 4c. propagate to peers
        for peer in PEER_MAP.get(sym, []):
            p = result.stock_scores.get(sym, 0.0) * PEER_DAMPING
            if abs(p) > abs(result.stock_scores.get(peer, 0.0)):
                result.stock_scores[peer] = p
                result.reasons[peer] = f"peer of {sym}"

    # 5b. direct asset mentions: score by headline sentiment when no event set it
    for asset, keywords in ASSET_KEYWORDS.items():
        if any(k in text for k in keywords):
            if asset not in result.asset_scores and abs(result.sentiment) >= 0.15:
                result.asset_scores[asset] = result.sentiment * 6.0
                result.reasons[asset] = "named in news (sentiment)"

    return result


def format_report(r: NewsImpact) -> str:
    lines = [f'NEWS: "{r.headline}"',
             f"  Sentiment: {r.sentiment:+.2f}"]
    if r.events:
        for name, note in r.events:
            lines.append(f"  Event: {name} - {note}")
    else:
        lines.append("  Event: none matched (sentiment-only analysis)")
    if r.sector_scores:
        secs = sorted(r.sector_scores.items(), key=lambda x: -abs(x[1]))
        lines.append("  Sector impact: " + ", ".join(f"{s} {v:+.1f}" for s, v in secs))
    if r.asset_scores:
        assets = sorted(r.asset_scores.items(), key=lambda x: -abs(x[1]))
        lines.append("  Currency/Commodity: " + ", ".join(f"{a} {v:+.1f}" for a, v in assets))
    ups, downs = r.ranked("up"), r.ranked("down")
    if ups:
        lines.append("  LIKELY UP:")
        for sym, v in ups[:8]:
            lines.append(f"    {sym:<12} {v:+5.1f}  ({r.reasons.get(sym, '')})")
    if downs:
        lines.append("  LIKELY DOWN:")
        for sym, v in downs[:8]:
            lines.append(f"    {sym:<12} {v:+5.1f}  ({r.reasons.get(sym, '')})")
    if not ups and not downs:
        lines.append("  No clear stock impact - WAIT.")
    return "\n".join(lines)
