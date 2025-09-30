import pandas as pd
from agent.tools import load_data, revenue_vs_budget, gross_margin_trend, opex_breakdown, cash_runway

def test_revenue_vs_budget_june_2025():
    bundle = load_data("fixtures")
    res = revenue_vs_budget(bundle, "2025-06")
    assert "actual_usd" in res
    assert "budget_usd" in res
    assert res["actual_usd"] > 0

def test_gross_margin_trend_has_values():
    bundle = load_data("fixtures")
    df = gross_margin_trend(bundle, last_n=3)
    assert len(df) == 3
    assert "gross_margin_pct" in df.columns

def test_opex_breakdown_not_empty():
    bundle = load_data("fixtures")
    df = opex_breakdown(bundle, "2025-06")
    assert not df.empty
    assert "category" in df.columns

def test_cash_runway_structure():
    bundle = load_data("fixtures")
    res = cash_runway(bundle)
    assert "cash_usd" in res
    assert "current_month" in res
