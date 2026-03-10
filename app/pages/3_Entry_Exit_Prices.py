import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.title("Entry / Exit Price Engine")

st.write("Determine ideal entry and exit prices based on recent price ranges.")

# Sidebar inputs
ticker = st.sidebar.text_input("Ticker", "TQQQ")
window = st.sidebar.slider("Days Window", 5, 20, 7)
entry_percentile = st.sidebar.slider("Entry Percentile", 5, 40, 25)
exit_percentile = st.sidebar.slider("Exit Percentile", 60, 95, 75)

# Download data
@st.cache_data
def load_data(ticker):
    df = yf.download(
        ticker,
        period="3mo",
        interval="1d",
        progress=False
    )
    df = df.dropna()
    return df

df = load_data(ticker)

# ---------------------------------------------------------
# Calculate levels (ALL VALUES FORCED TO FLOAT)
# ---------------------------------------------------------
recent = df["Close"].tail(window)

entry_price = float(np.percentile(recent, entry_percentile))
exit_price = float(np.percentile(recent, exit_percentile))

price_now = float(df["Close"].iloc[-1])

# ---------------------------------------------------------
# Momentum calculation (SAFE)
# ---------------------------------------------------------
if len(df) > 1:
    today = float(df["Close"].iloc[-1])
    yesterday = float(df["Close"].iloc[-2])

    if today > yesterday:
        momentum = "UP"
    elif today < yesterday:
        momentum = "DOWN"
    else:
        momentum = "FLAT"
else:
    momentum = "FLAT"

# ---------------------------------------------------------
# Signal logic (SAFE COMPARISONS)
# ---------------------------------------------------------
signal = "HOLD"

if price_now <= entry_price and momentum == "UP":
    signal = "BUY"

elif price_now >= exit_price and momentum == "DOWN":
    signal = "SELL"

# ---------------------------------------------------------
# Display metrics
# ---------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Current Price", f"{price_now:.2f}")
col2.metric("Entry Price", f"{entry_price:.2f}")
col3.metric("Exit Price", f"{exit_price:.2f}")
col4.metric("Signal", signal)

st.divider()

st.subheader("Recent Prices")
st.dataframe(df.tail(10))

st.subheader("Price Chart")
st.line_chart(df["Close"])

# ---------------------------------------------------------
# Explanation
# ---------------------------------------------------------
with st.expander("Calculation Details"):
    st.write(f"""
Entry price = {entry_percentile}th percentile of last {window} days.

Exit price = {exit_percentile}th percentile of last {window} days.

Momentum compares today's close with yesterday's close.
""")