"""Currency & commodity universe + per-event asset impacts.

Asset scores are -10..+10, same convention as sector scores.
For currency pairs the direction is the PAIR direction:
  USDINR +5 means the pair rises (rupee WEAKENS).
"""

CURRENCIES = ["USDINR", "EURINR", "GBPINR", "JPYINR"]
COMMODITIES = ["GOLD", "SILVER", "CRUDEOIL", "NATURALGAS", "COPPER", "ZINC", "ALUMINIUM"]

ASSET_LABEL = {
    "USDINR": "USD/INR", "EURINR": "EUR/INR", "GBPINR": "GBP/INR", "JPYINR": "JPY/INR",
    "GOLD": "Gold (MCX)", "SILVER": "Silver (MCX)", "CRUDEOIL": "Crude Oil (MCX)",
    "NATURALGAS": "Natural Gas (MCX)", "COPPER": "Copper (MCX)", "ZINC": "Zinc (MCX)",
    "ALUMINIUM": "Aluminium (MCX)",
}

# event name (from events.EVENT_RULES) -> asset impacts
EVENT_ASSET_IMPACTS = {
    "MIDDLE_EAST_CONFLICT": {"CRUDEOIL": +8, "GOLD": +7, "SILVER": +5, "NATURALGAS": +4,
                             "USDINR": +5, "JPYINR": +3},
    "CRUDE_UP":            {"CRUDEOIL": +7, "USDINR": +3},
    "CRUDE_DOWN":          {"CRUDEOIL": -7, "USDINR": -2},
    "US_FED_OR_RECESSION": {"GOLD": +5, "USDINR": +4, "COPPER": -4, "CRUDEOIL": -3},
    "RUPEE_WEAK":          {"USDINR": +6, "EURINR": +4, "GBPINR": +4, "GOLD": +3},
    "RATE_CUT":            {"USDINR": +2, "GOLD": +2},
    "RATE_HIKE":           {"USDINR": -2, "GOLD": -2},
    "INFRA_SPENDING":      {"COPPER": +4, "ZINC": +3, "ALUMINIUM": +3},
    "METAL_DUTY_CHINA":    {"COPPER": +5, "ZINC": +4, "ALUMINIUM": +4},
    "MONSOON_GOOD":        {"GOLD": +1},
    "MONSOON_BAD":         {},
}

# direct keyword triggers when news names the asset itself
ASSET_KEYWORDS = {
    "GOLD": ["gold price", "gold rate", "gold import", "bullion"],
    "SILVER": ["silver price", "silver rate"],
    "CRUDEOIL": ["crude", "brent", "wti", "opec", "oil price"],
    "NATURALGAS": ["natural gas", "lng"],
    "COPPER": ["copper"],
    "ZINC": ["zinc"],
    "ALUMINIUM": ["aluminium", "aluminum"],
    "USDINR": ["rupee", "usd/inr", "usdinr", "dollar index"],
    "EURINR": ["euro", "eur/inr"],
    "GBPINR": ["pound sterling", "gbp/inr"],
    "JPYINR": ["yen", "jpy/inr"],
}
