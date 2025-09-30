import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from agent.planner import route_question
from agent.tools import load_data, revenue_vs_budget, gross_margin_trend, opex_breakdown, cash_runway

# ---------- Streamlit Page Setup ----------
st.set_page_config(page_title="FP&A CFO Copilot", page_icon="📊", layout="wide")
st.title("📊 FP&A CFO Copilot")

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### 📁 Data Files")
    st.caption("Using CSVs from `fixtures/`")
    st.markdown("- actuals.csv\n- budget.csv\n- cash.csv\n- fx.csv")


# ---------- Load Data ----------
bundle = load_data("fixtures")

# ---------- Utility ----------
def fmt_usd(x):
    return "${:,.0f}".format(x)

# ---------- Answer + Chart Generator ----------
def answer_and_plot(intent_name, params):
    if intent_name == "revenue_vs_budget":
        res = revenue_vs_budget(bundle, params.get("month"))
        m = pd.to_datetime(res["month"]).strftime("%b %Y")
        delta_pct = res["delta_pct"] * 100 if not np.isnan(res["delta_pct"]) else np.nan
        text = f"**Revenue — {m}**\nActual: {fmt_usd(res['actual_usd'])} | Budget: {fmt_usd(res['budget_usd'])} | Δ: {fmt_usd(res['delta_usd'])} ({delta_pct:.1f}%)"
        fig = go.Figure(data=[
            go.Bar(name="Actual", x=["Revenue"], y=[res["actual_usd"]]),
            go.Bar(name="Budget", x=["Revenue"], y=[res["budget_usd"]])
        ])
        fig.update_layout(barmode="group", title=f"Revenue vs Budget — {m}", yaxis_title="USD")
        return text, fig

    if intent_name == "gross_margin_trend":
        last_n = int(params.get("last_n", 3))
        df = gross_margin_trend(bundle, last_n=last_n)
        df["label"] = df["month"].dt.strftime("%b %Y")
        text = f"**Gross Margin % — last {last_n} months**"
        fig = go.Figure(data=[go.Scatter(x=df["label"], y=df["gross_margin_pct"], mode="lines+markers")])
        fig.update_layout(title="Gross Margin % Trend", yaxis_title="%")
        return text, fig

    if intent_name == "opex_breakdown":
        df = opex_breakdown(bundle, params.get("month"))
        text = f"**Opex Breakdown — {params.get('month') or 'latest month'}**"
        fig = go.Figure(data=[go.Pie(labels=df["category"], values=df["amount"], hole=0.4)])
        fig.update_layout(title="Opex by Category")
        return text, fig

    if intent_name == "cash_runway":
        res = cash_runway(bundle)
        m = pd.to_datetime(res["current_month"]).strftime("%b %Y")
        if res.get("runway_months") is None:
            text = f"**Cash Runway — {m}**\nCash: {fmt_usd(res['cash_usd'])}. {res['note']}"
            return text, go.Figure()
        else:
            text = f"**Cash Runway — {m}**\nCash: {fmt_usd(res['cash_usd'])} | Avg net burn (3m): {fmt_usd(res['avg_net_burn'])} → **Runway: {res['runway_months']:.1f} months**"
            cash_df = bundle.cash.sort_values("month").tail(6).copy()
            cash_df["label"] = cash_df["month"].dt.strftime("%b %Y")
            fig = go.Figure(data=[go.Bar(x=cash_df["label"], y=cash_df["cash_usd"])])
            fig.update_layout(title="Cash Balance (last 6 months)", yaxis_title="USD")
            return text, fig

    return "_Sorry, I didn't understand that question._", go.Figure()

# ---------- Chat Interface ----------
if "history" not in st.session_state:
    st.session_state.history = []

user_q = st.chat_input("Ask a finance question…")
if user_q:
    st.session_state.history.append(("user", user_q))
    intent = route_question(user_q)
    text, fig = answer_and_plot(intent.name, intent.params)
    st.session_state.history.append(("assistant", text, fig))

for role, *content in st.session_state.history:
    if role == "user":
        with st.chat_message("user"):
            st.write(content[0])
    else:
        text, fig = content
        with st.chat_message("assistant"):
            st.markdown(text)
            if fig and len(fig.data) > 0:
                st.plotly_chart(fig, use_container_width=True)
