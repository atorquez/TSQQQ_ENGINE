
import sys
import os

# ---------------------------------------------------------
# Ensure project root is in sys.path (so engine_pkg imports work)
# ---------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

from engine_pkg.signals import decide_ratio
# ---------------------------------------------------------
# Page config + Dark Theme CSS
# ---------------------------------------------------------
st.set_page_config(page_title="Short-Term TQQQ/SQQQ Explorer", layout="wide")

st.markdown("""
<style>
    .stMetric {
        background-color: #111827 !important;
        border-radius: 8px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Download 30-day data
# ---------------------------------------------------------
tickers = ["TQQQ", "SQQQ"]
data = yf.download(tickers, period="30d", interval="1d")["Close"]

# Clean index
data.index = data.index.tz_localize(None)
data = data.sort_index()

# ---------------------------------------------------------
# Display current prices
# ---------------------------------------------------------
col1, col2 = st.columns(2)

tqqq_price = float(data["TQQQ"].iloc[-1])
sqqq_price = float(data["SQQQ"].iloc[-1])

col1.metric("TQQQ Price", f"${tqqq_price:,.2f}")
col2.metric("SQQQ Price", f"${sqqq_price:,.2f}")

# ---------------------------------------------------------
# Price Chart (TQQQ + SQQQ)
# ---------------------------------------------------------
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=data.index,
    y=data["TQQQ"],
    mode="lines",
    name="TQQQ",
    line=dict(color="dodgerblue", width=2)
))

fig.add_trace(go.Scatter(
    x=data.index,
    y=data["SQQQ"],
    mode="lines",
    name="SQQQ",
    line=dict(color="crimson", width=2)
))

fig.update_layout(
    title="30-Day Price Comparison: TQQQ vs SQQQ",
    xaxis_title="Date",
    yaxis_title="Price",
    height=600,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# Ratio Table (5-day return → decide_ratio)
# ---------------------------------------------------------

ratio_rows = []

for i in range(5, len(data)):  # need at least 5 days to compute 5d return
    window = data.iloc[:i]

    # 5-day returns
    ret_t = window["TQQQ"].pct_change(5).iloc[-1]
    ret_s = window["SQQQ"].pct_change(5).iloc[-1]

    # 5-day volatility (std of daily returns)
    vol_t = window["TQQQ"].pct_change().rolling(10).std().iloc[-1]
    vol_s = window["SQQQ"].pct_change().rolling(10).std().iloc[-1]

    ratio_t, ratio_s = decide_ratio(ret_t, ret_s, vol_t, vol_s)

    ratio_rows.append({
        "Date": window.index[-1],
        "TQQQ Return (5d)": f"{ret_t * 100:.2f}%",
        "SQQQ Return (5d)": f"{ret_s * 100:.2f}%",
        "TQQQ %": ratio_t * 100,
        "SQQQ %": ratio_s * 100,
        "TQQQ % (display)": f"{ratio_t * 100:.2f}%",
        "SQQQ % (display)": f"{ratio_s * 100:.2f}%"
    })

ratio_df = pd.DataFrame(ratio_rows)

st.markdown("### 📄 Daily Ratio Table (Last 30 Days)")
st.dataframe(
    ratio_df[[
        "Date",
        "TQQQ Return (5d)",
        "SQQQ Return (5d)",
        "TQQQ % (display)",
        "SQQQ % (display)"
    ]],
    use_container_width=True
)

# ---------------------------------------------------------
# Ratio Line Chart
# ---------------------------------------------------------
fig_ratio = go.Figure()

fig_ratio.add_trace(go.Scatter(
    x=ratio_df["Date"],
    y=ratio_df["TQQQ %"],
    mode="lines+markers",
    name="TQQQ %",
    line=dict(color="dodgerblue", width=2)
))

fig_ratio.add_trace(go.Scatter(
    x=ratio_df["Date"],
    y=ratio_df["SQQQ %"],
    mode="lines+markers",
    name="SQQQ %",
    line=dict(color="crimson", width=2)
))

fig_ratio.update_layout(
    title="Daily Recommended Ratio (TQQQ vs SQQQ)",
    xaxis_title="Date",
    yaxis_title="Allocation %",
    height=400,
    yaxis=dict(range=[0, 100])
)

st.plotly_chart(fig_ratio, use_container_width=True)