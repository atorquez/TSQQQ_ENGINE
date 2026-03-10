import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import altair as alt
import sys
import os

# ---------------------------------------------------------
# Ensure project root is in sys.path
# ---------------------------------------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ---------------------------------------------------------
# Import engine functions
# ---------------------------------------------------------
try:
    from engine_pkg.engine import get_5d_return, get_5d_volatility, get_trend_features, decide_ratio, classify_vol_regime
except ModuleNotFoundError:
    st.error("engine_pkg not found. Ensure your project structure includes engine_pkg/engine.py")
    st.stop()

# ---------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------
if "engine_started" not in st.session_state:
    st.session_state.engine_started = False

if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "TQQQ"

# ---------------------------------------------------------
# Page title
# ---------------------------------------------------------
st.title("📈 Engine Overview (2-Year Chart)")
st.write("This page shows a 2-year chart with MA20, MA60, MA200, returns, volatility, and TQQQ/SQQQ ratio.")

# ---------------------------------------------------------
# Ticker selection
# ---------------------------------------------------------
st.subheader("Select Ticker")
ticker = st.selectbox("Ticker", ["TQQQ", "SQQQ"], index=0)

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import altair as alt

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import altair as alt

# ---------------------------------------------------------
# Fetch 2-year historical data robustly
# ---------------------------------------------------------
@st.cache_data
def get_last_2y(ticker):
    df = yf.download(ticker, period="2y", interval="1d", auto_adjust=True, progress=False)
    
    # If df is empty or None, return DataFrame with required columns
    required_cols = ["Date", "Close", "MA20", "MA60", "MA200"]
    if df is None or df.empty:
        return pd.DataFrame(columns=required_cols)
    
    # Ensure Close column exists
    if "Close" not in df.columns:
        df["Close"] = np.nan

    # Keep only Close column
    df = df[["Close"]].copy()
    
    # Compute moving averages
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA60"] = df["Close"].rolling(60).mean()
    df["MA200"] = df["Close"].rolling(200).mean()
    
    # Reset index to get Date as a column
    df = df.reset_index()
    
    # Force column name Date
    if df.columns[0] != "Date":
        df.rename(columns={df.columns[0]: "Date"}, inplace=True)
    
    # Ensure all required columns exist
    for col in required_cols[1:]:  # skip Date
        if col not in df.columns:
            df[col] = np.nan
    
    # Keep only required columns in correct order
    df = df[required_cols]
    
    return df

# ---------------------------------------------------------
# Streamlit page
# ---------------------------------------------------------
st.title("📈 2-Year Chart with MA20/MA60/MA200")
ticker = st.selectbox("Select Ticker", ["TQQQ", "SQQQ"])

df = get_last_2y(ticker)

# Check columns
required_cols = ["Date", "Close", "MA20", "MA60", "MA200"]
missing_cols = [c for c in required_cols if c not in df.columns]

if df.empty or missing_cols:
    st.warning(f"⚠️ Cannot display chart. Missing columns: {missing_cols}")
    st.write(df.head())
else:
    # Melt for Altair
    chart_df = pd.melt(
        df,
        id_vars=["Date"],
        value_vars=["Close", "MA20", "MA60", "MA200"],
        var_name="Series",
        value_name="Price"
    )
    
    chart = (
        alt.Chart(chart_df)
        .mark_line(strokeWidth=2)
        .encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y("Price:Q", title="Price", scale=alt.Scale(zero=False)),
            color="Series:N",
            tooltip=["Date", "Series", "Price"]
        )
        .properties(height=400)
    )
    
    st.altair_chart(chart, use_container_width=True)

# ---------------------------------------------------------
# Run Engine button
# ---------------------------------------------------------
if st.button("Run Engine"):
    st.session_state.engine_started = True
    
    df = get_last_2y(ticker)
    
    required_cols = ["Date", "Close", "MA20", "MA60", "MA200"]
    
    if df.empty or not all(col in df.columns for col in required_cols):
        st.warning(f"⚠️ Data not ready for chart for {ticker}")
        st.write(df.head())
    else:
        # ---------------------------------------------------------
        # Chart
        # ---------------------------------------------------------
        chart_df = df.melt(
            id_vars=["Date"],
            value_vars=["Close", "MA20", "MA60", "MA200"],
            var_name="Series",
            value_name="Price"
        )
        
        chart = (
            alt.Chart(chart_df)
            .mark_line(strokeWidth=2)
            .encode(
                x=alt.X("Date:T", title="Date"),
                y=alt.Y("Price:Q", title="Price", scale=alt.Scale(zero=False)),
                color="Series:N",
                tooltip=["Date", "Series", "Price"]
            )
            .properties(height=400)
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        # ---------------------------------------------------------
        # 5-Day Returns
        # ---------------------------------------------------------
        st.subheader("📈 5-Day Returns")
        ret_t, price_t = get_5d_return("TQQQ")
        ret_s, price_s = get_5d_return("SQQQ")
        st.write(f"**TQQQ 5-day return:** {ret_t:.2%}, Last Close: {price_t}")
        st.write(f"**SQQQ 5-day return:** {ret_s:.2%}, Last Close: {price_s}")
        
        # ---------------------------------------------------------
        # 5-Day Volatility
        # ---------------------------------------------------------
        st.subheader("📉 5-Day Volatility")
        vol_t = get_5d_volatility("TQQQ")
        vol_s = get_5d_volatility("SQQQ")
        st.write(f"**TQQQ volatility:** {vol_t:.2%}")
        st.write(f"**SQQQ volatility:** {vol_s:.2%}")
        
        # ---------------------------------------------------------
        # Trend Features
        # ---------------------------------------------------------
        st.subheader("📊 Trend Features")
        trend_t = get_trend_features("TQQQ")
        trend_s = get_trend_features("SQQQ")
        st.write("**TQQQ:**", trend_t)
        st.write("**SQQQ:**", trend_s)
        
        # ---------------------------------------------------------
        # Ratio Decision
        # ---------------------------------------------------------
        st.subheader("⚖️ Ratio Recommendation")
        w_t, w_s = decide_ratio(ret_t, ret_s, vol_t, vol_s)
        vol_regime = classify_vol_regime(vol_t, vol_s)
        
        MAX_WEIGHT = 0.70
        MIN_WEIGHT = 0.30
        
        if w_t > w_s:
            w_t, w_s = MAX_WEIGHT, MIN_WEIGHT
            bias = "TQQQ Bias (Bullish)"
        else:
            w_t, w_s = MIN_WEIGHT, MAX_WEIGHT
            bias = "SQQQ Bias (Bearish)"
        
        strength = abs(w_t - w_s)
        if strength < 0.10:
            signal = "Very Weak"
        elif strength < 0.20:
            signal = "Weak"
        elif strength < 0.35:
            signal = "Moderate"
        else:
            signal = "Strong"
        
        st.info(f"""
        **Recommended Split:** {round(w_t*100,2)}% TQQQ / {round(w_s*100,2)}% SQQQ
        **Directional Bias:** {bias}
        **Signal Strength:** {signal} (|TQQQ − SQQQ| = {strength:.2f})
        **Volatility Regime:** {vol_regime}
        """)
        
        # ---------------------------------------------------------
        # Trade Decision
        # ---------------------------------------------------------
        st.subheader("📌 Today's Trade Decision")
        no_trade_zone = 0.45 <= w_t <= 0.55
        trade_allowed = not no_trade_zone
        if trade_allowed:
            st.success("✅ **TRADE ALLOWED TODAY**")
        else:
            st.error("❌ **NO TRADE TODAY**")
        st.write(f"No-trade zone: {no_trade_zone}")