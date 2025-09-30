from dataclasses import dataclass
from dateutil import parser
import re
from typing import Optional, Dict, Any

@dataclass
class Intent:
    name: str
    params: Dict[str, Any]

# Regex to detect "June 2025", "Jan 2024", etc.
MONTH_PAT = re.compile(r"(jan|feb|mar|apr|may|jun|jul|aug|sept?|oct|nov|dec)[a-z]*\s+\d{4}", re.I)

def parse_month(text: str) -> Optional[str]:
    match = MONTH_PAT.search(text)
    if match:
        dt = parser.parse(match.group(0))
        return dt.strftime("%Y-%m")
    return None

def route_question(q: str) -> Intent:
    t = q.lower()

    if "revenue" in t and ("budget" in t or "vs" in t or "versus" in t):
        return Intent("revenue_vs_budget", {"month": parse_month(t)})

    if "gross margin" in t and ("trend" in t or "last" in t or "%" in t):
        m = re.search(r"last\s+(\d+)\s+month", t)
        return Intent("gross_margin_trend", {"last_n": int(m.group(1)) if m else 3})

    if "opex" in t and ("break" in t or "by" in t or "category" in t):
        return Intent("opex_breakdown", {"month": parse_month(t)})

    if "runway" in t or ("cash" in t and "runway" in t):
        return Intent("cash_runway", {})

    if "gross margin" in t:
        return Intent("gross_margin_trend", {"last_n": 6})

    if "opex" in t:
        return Intent("opex_breakdown", {"month": parse_month(t)})

    if "revenue" in t:
        return Intent("revenue_vs_budget", {"month": parse_month(t)})

    return Intent("revenue_vs_budget", {"month": None})
