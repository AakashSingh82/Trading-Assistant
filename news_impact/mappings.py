"""Static market-structure knowledge: sectors -> stocks, stock -> peers, company aliases."""

SECTOR_STOCKS = {
    "IT": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM"],
    "PHARMA": ["SUNPHARMA", "CIPLA", "DRREDDY", "AUROPHARMA", "LUPIN", "DIVISLAB"],
    "BANKS": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK"],
    "NBFC": ["BAJFINANCE", "CHOLAFIN", "SHRIRAMFIN", "MUTHOOTFIN"],
    "AUTO": ["MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO"],
    "EV": ["TATAMOTORS", "M&M", "OLECTRA", "EXIDEIND", "ARE&M", "TATAPOWER", "SERVOTECH"],
    "OIL_PRODUCERS": ["ONGC", "OIL"],
    "OMC": ["IOC", "BPCL", "HPCL"],
    "PAINTS": ["ASIANPAINT", "BERGEPAINT", "KANSAINER"],
    "AVIATION": ["INDIGO", "SPICEJET"],
    "TYRES": ["MRF", "APOLLOTYRE", "CEATLTD", "BALKRISIND"],
    "DEFENCE": ["HAL", "BEL", "BDL", "BHARATFORG", "MAZDOCK", "COCHINSHIP"],
    "GOLD_FINANCE": ["MUTHOOTFIN", "MANAPPURAM"],
    "CEMENT": ["ULTRACEMCO", "ACC", "AMBUJACEM", "SHREECEM", "DALBHARAT"],
    "CONSTRUCTION": ["LT", "NBCC", "NCC", "KNRCON", "IRB"],
    "CAPITAL_GOODS": ["ABB", "SIEMENS", "BHEL", "CUMMINSIND"],
    "INFRA": ["LT", "GMRINFRA", "IRCON", "RVNL", "NBCC"],
    "RAILWAYS": ["IRCTC", "RVNL", "IRFC", "IRCON", "TITAGARH"],
    "REALTY": ["DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE"],
    "FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "DABUR", "MARICO"],
    "METALS": ["TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "SAIL", "NMDC"],
    "TELECOM": ["BHARTIARTL", "IDEA", "INDUSTOWER"],
    "INSURANCE": ["SBILIFE", "HDFCLIFE", "ICICIPRULI", "LICI"],
    "FERTILIZERS": ["CHAMBLFERT", "COROMANDEL", "GNFC"],
    "SUGAR": ["BALRAMCHIN", "TRIVENI", "DHAMPURSUG"],
    "TEXTILES": ["PAGEIND", "TRIDENT", "WELSPUNLIV", "KPRMILL"],
    "SOLAR": ["TATAPOWER", "ADANIGREEN", "SUZLON", "INOXWIND", "WAAREEENER"],
}

# If big news hits one stock, also watch its closest peers (impact propagation).
PEER_MAP = {
    "TCS": ["INFY", "HCLTECH", "WIPRO"],
    "INFY": ["TCS", "HCLTECH", "WIPRO"],
    "RELIANCE": ["ONGC", "BPCL", "IOC"],
    "HDFCBANK": ["ICICIBANK", "AXISBANK", "KOTAKBANK"],
    "SUNPHARMA": ["CIPLA", "DRREDDY", "LUPIN"],
    "TATAMOTORS": ["M&M", "MARUTI", "EICHERMOT"],
    "ULTRACEMCO": ["ACC", "AMBUJACEM", "SHREECEM"],
    "ADANIENT": ["ADANIPORTS", "ADANIGREEN", "ADANIPOWER"],
}

# Free-text company/brand names -> NSE symbol (lowercase keys, matched on word boundaries).
COMPANY_ALIASES = {
    "tcs": "TCS", "tata consultancy": "TCS",
    "infosys": "INFY", "wipro": "WIPRO", "hcl tech": "HCLTECH", "hcltech": "HCLTECH",
    "tech mahindra": "TECHM",
    "reliance": "RELIANCE", "jio": "RELIANCE",
    "hdfc bank": "HDFCBANK", "icici": "ICICIBANK", "sbi": "SBIN",
    "state bank": "SBIN", "kotak": "KOTAKBANK", "axis bank": "AXISBANK",
    "sun pharma": "SUNPHARMA", "cipla": "CIPLA", "dr reddy": "DRREDDY",
    "dr. reddy": "DRREDDY", "aurobindo": "AUROPHARMA", "lupin": "LUPIN",
    "tata motors": "TATAMOTORS", "maruti": "MARUTI", "mahindra": "M&M",
    "bajaj auto": "BAJAJ-AUTO", "hero motocorp": "HEROMOTOCO",
    "larsen": "LT", "l&t": "LT",
    "ultratech": "ULTRACEMCO", "acc": "ACC", "ambuja": "AMBUJACEM",
    "shree cement": "SHREECEM",
    "ongc": "ONGC", "indian oil": "IOC", "bpcl": "BPCL", "hpcl": "HPCL",
    "asian paints": "ASIANPAINT", "berger paints": "BERGEPAINT",
    "indigo": "INDIGO", "interglobe": "INDIGO", "spicejet": "SPICEJET",
    "hindustan aeronautics": "HAL", "bharat electronics": "BEL",
    "bharat dynamics": "BDL", "bharat forge": "BHARATFORG",
    "tata steel": "TATASTEEL", "jsw steel": "JSWSTEEL", "hindalco": "HINDALCO",
    "vedanta": "VEDL",
    "airtel": "BHARTIARTL", "bharti airtel": "BHARTIARTL", "vodafone idea": "IDEA",
    "itc": "ITC", "hindustan unilever": "HINDUNILVR", "hul": "HINDUNILVR",
    "nestle": "NESTLEIND",
    "tata power": "TATAPOWER", "adani green": "ADANIGREEN", "suzlon": "SUZLON",
    "exide": "EXIDEIND", "amara raja": "ARE&M", "olectra": "OLECTRA",
    "dlf": "DLF", "godrej properties": "GODREJPROP",
    "irctc": "IRCTC", "rvnl": "RVNL", "irfc": "IRFC",
    "bajaj finance": "BAJFINANCE",
    "adani": "ADANIENT",
    "nbcc": "NBCC",
}

# Which sector a symbol belongs to (built from SECTOR_STOCKS; first sector wins).
STOCK_SECTOR = {}
for _sector, _stocks in SECTOR_STOCKS.items():
    for _s in _stocks:
        STOCK_SECTOR.setdefault(_s, _sector)
