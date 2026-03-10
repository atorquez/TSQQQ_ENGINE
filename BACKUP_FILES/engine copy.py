import yfinance as yf
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# Core data fetcher
# ---------------------------------------------------------
def _get_history(ticker, period="90d", interval="1d"):
    data = yf.download(ticker, period=period, interval=interval)

    if data.empty:
        return None

    data.index = pd.to_datetime(data.index)
    data = data[~data.index.duplicated(keep="last")]
    data = data.sort_index()

    return data

# ---------------------------------------------------------
# 5-day return + last close
# ---------------------------------------------------------
def get_5d_return(ticker):
    data = _get_history(ticker, period="15d", interval="1d")
    if data is None:
        return np.nan, np.nan

    close = data["Close"].dropna()
    if len(close) < 6:
        return np.nan, float(close.iloc[-1]) if len(close) > 0 else np.nan

    ret_5d_series = close.pct_change(5)
    ret_5d = ret_5d_series.iloc[-1]

    price_today = close.iloc[-1]

    return float(ret_5d), float(price_today)

# ---------------------------------------------------------
# 5-day volatility
# ---------------------------------------------------------
def get_5d_volatility(ticker):
    data = _get_history(ticker, period="15d", interval="1d")
    if data is None:
        return np.nan

    close = data["Close"].dropna()
    if len(close) < 6:
        return np.nan

    returns = close.pct_change().dropna()
    if len(returns) < 5:
        return np.nan

    vol_5d = returns.tail(5).std()
    return float(vol_5d)

# ---------------------------------------------------------
# Trend features: MA20, MA60, slopes, classification
# ---------------------------------------------------------
def get_trend_features(ticker):
    data = _get_history(ticker, period="90d", interval="1d")
    if data is None:
        return {
            "ma20": np.nan,
            "ma60": np.nan,
            "ma20_slope": np.nan,
            "ma60_slope": np.nan,
            "trend_label": "unknown",
        }

    close = data["Close"].dropna()
    if len(close) < 60:
        return {
            "ma20": np.nan,
            "ma60": np.nan,
            "ma20_slope": np.nan,
            "ma60_slope": np.nan,
            "trend_label": "insufficient",
        }

    ma20 = close.rolling(20).mean()
    ma60 = close.rolling(60).mean()

    ma20_last = ma20.iloc[-1]
    ma60_last = ma60.iloc[-1]

    # Simple slope: last MA vs MA 5 days ago
    ma20_slope = ma20.iloc[-1] - ma20.iloc[-6] if not pd.isna(ma20.iloc[-6]) else np.nan
    ma60_slope = ma60.iloc[-1] - ma60.iloc[-6] if not pd.isna(ma60.iloc[-6]) else np.nan

    # Trend classification
    if ma20_last > ma60_last and ma20_slope > 0:
        trend_label = "bullish"
    elif ma20_last < ma60_last and ma20_slope < 0:
        trend_label = "bearish"
    else:
        trend_label = "choppy"

    return {
        "ma20": float(ma20_last),
        "ma60": float(ma60_last),
        "ma20_slope": float(ma20_slope),
        "ma60_slope": float(ma60_slope),
        "trend_label": trend_label,
    }

# ---------------------------------------------------------
# Volatility regime classification
# ---------------------------------------------------------
def classify_vol_regime(vol_t, vol_s):
    vols = [v for v in [vol_t, vol_s] if not pd.isna(v)]
    if not vols:
        return "unknown"

    avg_vol = np.mean(vols)

    if avg_vol < 0.02:
        return "low"
    elif avg_vol < 0.05:
        return "medium"
    else:
        return "high"

# ---------------------------------------------------------
# Core ratio decision (risk-adjusted)
# ---------------------------------------------------------
def decide_ratio(ret_t, ret_s, vol_t, vol_s):
    if pd.isna(ret_t) or pd.isna(ret_s) or vol_t == 0 or vol_s == 0 or pd.isna(vol_t) or pd.isna(vol_s):
        return 0.5, 0.5

    score_t = max(ret_t / vol_t, 0)
    score_s = max(ret_s / vol_s, 0)

    total = score_t + score_s
    if total == 0:
        return 0.5, 0.5

    w_t = score_t / total
    w_s = score_s / total

    return float(w_t), float(w_s)

# ---------------------------------------------------------
# High-level engine: all features in one call
# ---------------------------------------------------------
def run_engine():
    # 5d returns + prices
    ret_t, price_t = get_5d_return("TQQQ")
    ret_s, price_s = get_5d_return("SQQQ")

    # 5d volatility
    vol_t = get_5d_volatility("TQQQ")
    vol_s = get_5d_volatility("SQQQ")

    # trend features
    trend_t = get_trend_features("TQQQ")
    trend_s = get_trend_features("SQQQ")

    # ratio
    w_t, w_s = decide_ratio(ret_t, ret_s, vol_t, vol_s)

    # volatility regime
    vol_regime = classify_vol_regime(vol_t, vol_s)

    return {
        "ret_t": ret_t,
        "ret_s": ret_s,
        "price_t": price_t,
        "price_s": price_s,
        "vol_t": vol_t,
        "vol_s": vol_s,
        "trend_t": trend_t,
        "trend_s": trend_s,
        "w_t": w_t,
        "w_s": w_s,
        "vol_regime": vol_regime,
    }