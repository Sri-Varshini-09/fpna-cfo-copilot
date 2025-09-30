from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from dateutil import parser

@dataclass
class DataBundle:
    actuals: pd.DataFrame
    budget: pd.DataFrame
    cash: pd.DataFrame
    fx: pd.DataFrame

# ---------- Load Data ----------
def load_data(fixtures_path: str = "fixtures") -> DataBundle:
    actuals = pd.read_csv(f"{fixtures_path}/actuals.csv")
    budget = pd.read_csv(f"{fixtures_path}/budget.csv")
    cash = pd.read_csv(f"{fixtures_path}/cash.csv")
    fx = pd.read_csv(f"{fixtures_path}/fx.csv")

    # Normalize month column to datetime
    for df in (actuals, budget, cash, fx):
        df["month"] = pd.to_datetime(df["month"])

    return DataBundle(actuals=actuals, budget=budget, cash=cash, fx=fx)

def _month_param_to_ts(bundle: DataBundle, month_str: Optional[str]) -> pd.Timestamp:
    if month_str is None:
        return bundle.actuals["month"].max()
    return pd.Timestamp(month_str + "-01")

# ---------- Revenue vs Budget ----------
def revenue_vs_budget(bundle: DataBundle, month_str: Optional[str]) -> Dict[str, Any]:
    m = _month_param_to_ts(bundle, month_str)
    a = bundle.actuals
    b = bundle.budget
    fx = bundle.fx.rename(columns={"rate_to_usd": "rate_usd_per_unit"})

    a_ = a[(a["month"] == m) & (a["account_category"] == "Revenue")].merge(fx, on=["month", "currency"], how="left")
    b_ = b[(b["month"] == m) & (b["account_category"] == "Revenue")].merge(fx, on=["month", "currency"], how="left")

    a_["usd"] = a_["amount"] * a_["rate_usd_per_unit"]
    b_["usd"] = b_["amount"] * b_["rate_usd_per_unit"]

    act = float(a_["usd"].sum())
    bud = float(b_["usd"].sum())
    delta = act - bud
    pct = (delta / bud) if bud else np.nan

    return {"month": m, "actual_usd": act, "budget_usd": bud, "delta_usd": delta, "delta_pct": pct}

# ---------- Gross Margin ----------
def gross_margin_trend(bundle: DataBundle, last_n: int = 3) -> pd.DataFrame:
    a = bundle.actuals
    months = sorted(a["month"].unique())[-last_n:]
    rows = []

    for m in months:
        sub = a[a["month"] == m]
        rev = sub[sub["account_category"] == "Revenue"]["amount"].sum()
        cogs = sub[sub["account_category"] == "COGS"]["amount"].sum()
        gm = (rev - cogs) / rev if rev else np.nan
        rows.append({"month": m, "gross_margin_pct": gm * 100})

    return pd.DataFrame(rows)

# ---------- Opex Breakdown ----------
def opex_breakdown(bundle: DataBundle, month_str: Optional[str]) -> pd.DataFrame:
    m = _month_param_to_ts(bundle, month_str)
    a = bundle.actuals
    sub = a[(a["month"] == m) & (a["account_category"].str.startswith("Opex:"))].copy()
    sub["category"] = sub["account_category"].str.split(":", n=1).str[1]
    return sub.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)

# ---------- EBITDA ----------
def ebitda_month(bundle: DataBundle, m: pd.Timestamp) -> float:
    a = bundle.actuals
    sub = a[a["month"] == m]
    rev = sub[sub["account_category"] == "Revenue"]["amount"].sum()
    cogs = sub[sub["account_category"] == "COGS"]["amount"].sum()
    opex = sub[sub["account_category"].str.startswith("Opex:")]["amount"].sum()
    return float(rev - cogs - opex)

# ---------- Cash Runway ----------
def cash_runway(bundle: DataBundle) -> Dict[str, Any]:
    months = sorted(bundle.actuals["month"].unique())[-3:]
    ebs = [ebitda_month(bundle, m) for m in months]
    avg_net_burn = -float(np.mean(ebs))
    current_month = months[-1]
    cur_cash = float(bundle.cash[bundle.cash["month"] == current_month]["cash_usd"].sum())

    if avg_net_burn <= 0:
        return {
            "current_month": current_month,
            "cash_usd": cur_cash,
            "runway_months": None,
            "note": "Company is not burning cash over the last 3 months (positive EBITDA). Runway is not applicable."
        }

    runway = cur_cash / avg_net_burn
    return {
        "current_month": current_month,
        "cash_usd": cur_cash,
        "avg_net_burn": avg_net_burn,
        "runway_months": runway
    }
