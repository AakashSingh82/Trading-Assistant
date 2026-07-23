"""Event rules: news pattern -> which sectors move up/down and how strongly.

Scores are -10 (very bearish) .. +10 (very bullish) at the SECTOR level.
Rules fire on regex triggers over the lowercased headline text.
"""

EVENT_RULES = [
    # ---------------- Geopolitical / macro ----------------
    {
        "name": "MIDDLE_EAST_CONFLICT",
        "triggers": [r"\bwar\b.*\b(iran|israel|middle east|gulf|iraq|saudi)",
                     r"\b(iran|israel|middle east|gulf)\b.*\bwar\b",
                     r"strait of hormuz", r"attack(s|ed)? .*oil (facility|field|tanker)",
                     r"declares? war", r"military strike", r"missile attack"],
        "impacts": {
            "OIL_PRODUCERS": +7,   # crude spikes -> upstream gains
            "DEFENCE": +6,
            "GOLD_FINANCE": +4,    # gold safe-haven
            "OMC": -7,             # OMCs buy crude -> margins crushed
            "PAINTS": -6,          # crude-derivative input costs
            "AVIATION": -7,        # ATF cost surge
            "TYRES": -5,
            "IT": -2, "BANKS": -3, # broad risk-off
        },
        "note": "War/conflict in oil-producing region: crude up, safe-havens up, crude consumers down, broad risk-off.",
    },
    {
        "name": "CRUDE_UP",
        "triggers": [r"crude .*(surge|spike|jump|rall|rise|soar)", r"oil price.*(surge|spike|jump|rise|soar)",
                     r"opec .*cut", r"brent .*(above|crosses|tops)"],
        "impacts": {"OIL_PRODUCERS": +6, "OMC": -6, "PAINTS": -5, "AVIATION": -6, "TYRES": -4},
        "note": "Crude oil rising: producers gain, fuel/derivative consumers lose.",
    },
    {
        "name": "CRUDE_DOWN",
        "triggers": [r"crude .*(fall|drop|slump|crash|plunge|decline)", r"oil price.*(fall|drop|slump|crash|plunge)",
                     r"opec .*(raise|increase) .*output"],
        "impacts": {"OIL_PRODUCERS": -5, "OMC": +6, "PAINTS": +5, "AVIATION": +6, "TYRES": +4},
        "note": "Crude oil falling: consumers of crude benefit.",
    },
    {
        "name": "US_FED_OR_RECESSION",
        "triggers": [r"us recession", r"fed .*(hike|raises)", r"us .*slowdown", r"nasdaq .*(crash|plunge|slump)",
                     r"h-?1b (visa )?(fee|restriction|curb)"],
        "impacts": {"IT": -6, "PHARMA": -2, "METALS": -3},
        "note": "US demand/visa headwinds hit export-oriented IT first.",
    },
    {
        "name": "RUPEE_WEAK",
        "triggers": [r"rupee .*(fall|weak|low|depreciat|slump)"],
        "impacts": {"IT": +4, "PHARMA": +3, "TEXTILES": +3, "OMC": -4, "AVIATION": -3},
        "note": "Weak rupee helps exporters (IT/pharma/textiles), hurts importers.",
    },
    # ---------------- RBI / rates ----------------
    {
        "name": "RATE_CUT",
        "triggers": [r"rbi .*(cut|lower|reduc).*(rate|repo)", r"repo rate .*cut"],
        "impacts": {"BANKS": +6, "NBFC": +7, "AUTO": +5, "REALTY": +6, "INFRA": +4},
        "note": "Cheaper money: rate-sensitive sectors rally.",
    },
    {
        "name": "RATE_HIKE",
        "triggers": [r"rbi .*(hike|raise|increas).*(rate|repo)", r"repo rate .*(hike|raise)"],
        "impacts": {"BANKS": -3, "NBFC": -6, "AUTO": -4, "REALTY": -6, "INFRA": -3},
        "note": "Costlier money: rate-sensitives fall (NBFC/realty most).",
    },
    # ---------------- Budget / policy ----------------
    {
        "name": "EV_POLICY_BOOST",
        "triggers": [r"(benefit|incentive|subsidy|pli|tax (cut|break|exemption)|budget).*(electric vehicle|ev maker|ev compan|ev sector)",
                     r"(electric vehicle|ev).*(benefit|incentive|subsidy|pli|tax (cut|break|exemption)|budget)",
                     r"fame([- ]?(ii|iii|2|3))? (scheme|subsidy|allocation)"],
        "impacts": {"EV": +8, "AUTO": +3},
        "note": "Government incentives for EV makers: EV chain (OEMs, batteries, charging) bullish.",
    },
    {
        "name": "INFRA_SPENDING",
        "triggers": [r"(infrastructure|infra|capex) (spending|outlay|allocation|push).*(increase|boost|hike|crore)",
                     r"(increase|boost|hike)s? .*(infrastructure|infra|capex) (spending|outlay|allocation)",
                     r"highway|road project|capital expenditure .*(increase|record)"],
        "impacts": {"CEMENT": +7, "CONSTRUCTION": +7, "CAPITAL_GOODS": +6, "INFRA": +7, "METALS": +4},
        "note": "Higher public capex: cement, construction, capital goods, steel benefit.",
    },
    {
        "name": "RAILWAY_BUDGET",
        "triggers": [r"railway.*(allocation|budget|order|capex).*(increase|boost|record|crore)",
                     r"(vande bharat|rail) .*(order|expansion|new trains)"],
        "impacts": {"RAILWAYS": +7, "CAPITAL_GOODS": +4},
        "note": "Railway capex/orders: rail-linked PSUs and wagon makers rally.",
    },
    {
        "name": "DEFENCE_ORDERS",
        "triggers": [r"defence .*(order|contract|acquisition|deal|budget|allocation)",
                     r"(hal|bel|bharat dynamics|mazagon).*(order|contract|deal)"],
        "impacts": {"DEFENCE": +7},
        "note": "Defence procurement: order-book driven rally in defence PSUs.",
    },
    {
        "name": "SOLAR_RENEWABLE_POLICY",
        "triggers": [r"(solar|renewable|green energy).*(subsidy|incentive|pli|allocation|target|push)",
                     r"rooftop solar"],
        "impacts": {"SOLAR": +7, "CAPITAL_GOODS": +3},
        "note": "Renewables policy push: solar/wind chain bullish.",
    },
    {
        "name": "TAX_ON_SECTOR_FMCG",
        "triggers": [r"gst .*(hike|increase).*(fmcg|consumer|tobacco|cigarette)",
                     r"(cigarette|tobacco) tax"],
        "impacts": {"FMCG": -5},
        "note": "Consumption tax hikes hurt FMCG volumes (ITC most for tobacco).",
    },
    {
        "name": "INCOME_TAX_RELIEF",
        "triggers": [r"income tax .*(cut|relief|rebate|slab)", r"tax relief .*middle class"],
        "impacts": {"FMCG": +5, "AUTO": +5, "REALTY": +4, "BANKS": +3},
        "note": "More disposable income: consumption plays benefit.",
    },
    # ---------------- Sector-specific regulatory ----------------
    {
        "name": "USFDA_WARNING",
        "triggers": [r"usfda .*(warning|observation|483|import alert|inspection fail)",
                     r"fda .*(warning letter|import alert)"],
        "impacts": {"PHARMA": -7},
        "note": "USFDA action: named company hit hardest, sector-wide sentiment negative.",
    },
    {
        "name": "PHARMA_APPROVAL",
        "triggers": [r"(usfda|fda) .*(approval|nod|clears)", r"(anda|drug) approval"],
        "impacts": {"PHARMA": +5},
        "note": "US drug approval: bullish for the named company, mildly for sector.",
    },
    {
        "name": "BANK_NPA_FRAUD",
        "triggers": [r"(npa|bad loan)s? .*(surge|rise|spike)", r"bank .*fraud", r"rbi .*(penalty|restriction).*bank"],
        "impacts": {"BANKS": -6, "NBFC": -4},
        "note": "Asset-quality/regulatory shock for lenders.",
    },
    {
        "name": "TELECOM_TARIFF_HIKE",
        "triggers": [r"(tariff|recharge) .*hike", r"telecom .*price .*(increase|hike)"],
        "impacts": {"TELECOM": +6},
        "note": "Tariff hikes lift telecom ARPU.",
    },
    {
        "name": "METAL_DUTY_CHINA",
        "triggers": [r"china .*(stimulus|infrastructure)", r"steel .*(price|demand).*(rise|increase)",
                     r"export duty .*(remov|cut).*steel"],
        "impacts": {"METALS": +6},
        "note": "China stimulus / steel price strength lifts metal stocks.",
    },
    {
        "name": "MONSOON_GOOD",
        "triggers": [r"(good|above.normal|normal) monsoon", r"monsoon .*(above|normal|good)"],
        "impacts": {"FERTILIZERS": +5, "FMCG": +4, "AUTO": +3, "SUGAR": +3},
        "note": "Good monsoon: rural demand plays benefit.",
    },
    {
        "name": "MONSOON_BAD",
        "triggers": [r"(deficient|weak|below.normal|poor) monsoon", r"drought"],
        "impacts": {"FERTILIZERS": -4, "FMCG": -4, "AUTO": -3, "SUGAR": +4},
        "note": "Weak monsoon hurts rural demand; sugar can rise on supply fears.",
    },
]

# Generic company-level events (applied to the NAMED stock, propagated to peers).
COMPANY_EVENT_RULES = [
    {"name": "EARNINGS_BEAT",   "triggers": [r"(profit|revenue|net income).*(jump|surge|rise|beat|record)", r"strong (q\d|quarter|results)"], "score": +7},
    {"name": "EARNINGS_MISS",   "triggers": [r"(profit|revenue).*(fall|drop|miss|decline|plunge)", r"weak (q\d|quarter|results)", r"loss widens"], "score": -7},
    {"name": "BIG_ORDER_WIN",   "triggers": [r"(wins|bags|secures).*(order|contract|deal)", r"order (win|worth|book)"], "score": +6},
    {"name": "MGMT_EXIT",       "triggers": [r"(ceo|cfo|md) .*(resign|quit|steps down|exit)"], "score": -5},
    {"name": "REGULATORY_PROBE","triggers": [r"(sebi|ed|cbi|income tax) .*(probe|raid|investigation|notice)", r"show.cause notice"], "score": -7},
    {"name": "STAKE_BUY",       "triggers": [r"(acquir|buys? stake|merger|takeover)"], "score": +4},
    {"name": "RATING_UPGRADE",  "triggers": [r"(upgrade|raises? target|outperform|buy rating)"], "score": +4},
    {"name": "RATING_DOWNGRADE","triggers": [r"(downgrade|cuts? target|underperform|sell rating)"], "score": -4},
]
