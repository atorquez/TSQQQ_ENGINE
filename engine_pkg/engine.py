import yfinance as yf
import pandas as pd

def get_5d_return(ticker):
    data = yf.download(ticker, period="10d", interval="1d")

    data.index = pd.to_datetime(data.index)
    data = data[~data.index.duplicated(keep="last")]
    data = data.sort_index()

    close = data["Close"].dropna()

    ret_5d_series = close.pct_change(5)
    ret_5d = ret_5d_series.iloc[-1]
    if isinstance(ret_5d, pd.Series):
        ret_5d = ret_5d.iloc[-1]

    price_today = close.iloc[-1]
    if isinstance(price_today, pd.Series):
        price_today = price_today.iloc[-1]

    return float(ret_5d), float(price_today)


def decide_ratio(ret_t, ret_s, vol_t, vol_s):
    if pd.isna(ret_t) or pd.isna(ret_s) or vol_t == 0 or vol_s == 0:
        return 0.5, 0.5

    score_t = max(ret_t / vol_t, 0)
    score_s = max(ret_s / vol_s, 0)

    total = score_t + score_s
    if total == 0:
        return 0.5, 0.5

    w_t = score_t / total
    w_s = score_s / total

    return w_t, w_s