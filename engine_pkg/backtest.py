import datetime as dt
from dataclasses import dataclass
from typing import List, Optional, Tuple
import pandas as pd
import yfinance as yf
from .signals import decide_ratio

# ---------------------------------------------------------
# Config dataclasses
# ---------------------------------------------------------

@dataclass
class BacktestConfig:
    start_date: str
    end_date: str
    budget: float = 500.0
    stop_loss_pct: float = -0.03
    take_profit_pct: Optional[float] = 0.03
    intraday_interval: str = "5m"
    tickers: Tuple[str, str] = ("TQQQ", "SQQQ")

@dataclass
class DailyResult:
    date: pd.Timestamp
    ratio_t: float
    ratio_s: float
    pnl: float
    ret: float
    exit_reason: str

# ---------------------------------------------------------
# Daily signal construction (same logic as app)
# ---------------------------------------------------------

def get_daily_close(tickers: Tuple[str, str],
                    start: str,
                    end: str) -> pd.DataFrame:
    data = yf.download(list(tickers), start=start, end=end, interval="1d")["Close"]
    data.index = data.index.tz_localize(None)
    data = data.sort_index()
    return data.dropna(how="any")


def build_signal_df(daily_close: pd.DataFrame,
                    lookback_ret: int = 5,
                    lookback_vol: int = 5) -> pd.DataFrame:
    """
    Build a DataFrame with daily ratios for TQQQ/SQQQ using decide_ratio.
    Ratios on day D are based on data up to D (like your app),
    and will be used for trading on D+1.
    """
    t_col, s_col = daily_close.columns[0], daily_close.columns[1]

    ret_t = daily_close[t_col].pct_change(lookback_ret)
    ret_s = daily_close[s_col].pct_change(lookback_ret)

    vol_t = daily_close[t_col].pct_change().rolling(lookback_vol).std()
    vol_s = daily_close[s_col].pct_change().rolling(lookback_vol).std()

    rows = []
    for date in daily_close.index:
        if pd.isna(ret_t.loc[date]) or pd.isna(ret_s.loc[date]):
            continue
        rt = ret_t.loc[date]
        rs = ret_s.loc[date]
        vt = vol_t.loc[date]
        vs = vol_s.loc[date]
        w_t, w_s = decide_ratio(rt, rs, vt, vs)
        rows.append(
            {
                "Date": date,
                "TQQQ_weight": w_t,
                "SQQQ_weight": w_s,
            }
        )

    sig_df = pd.DataFrame(rows).set_index("Date").sort_index()
    return sig_df

# ---------------------------------------------------------
# Intraday execution for a single day
# ---------------------------------------------------------

def get_intraday_for_day(ticker: str,
                         day: pd.Timestamp,
                         interval: str = "5m") -> pd.DataFrame:
    """
    Download intraday data for a single calendar day (local time).
    We request from day to day+1 and then filter.
    """
    start = day
    end = day + dt.timedelta(days=1)

    df = yf.download(ticker, start=start, end=end, interval=interval)
    if df.empty:
        return df

    df.index = df.index.tz_localize(None)
    df = df.sort_index()
    # Keep only rows with the same date as 'day'
    df = df[df.index.date == day.date()]
    return df

# ---------------------------------------------------------
# Simulate one day of trading given the ratios and config
# ---------------------------------------------------------  

def simulate_day(
    day: pd.Timestamp,
    ratio_t: float,
    ratio_s: float,
    cfg: BacktestConfig
) -> Optional[DailyResult]:

    t_ticker, s_ticker = cfg.tickers

    # -----------------------------
    # 1. Download intraday data
    # -----------------------------
    t_intraday = get_intraday_for_day(t_ticker, day, cfg.intraday_interval)
    s_intraday = get_intraday_for_day(s_ticker, day, cfg.intraday_interval)

    # If either is empty, skip the day
    if t_intraday.empty or s_intraday.empty:
        return None

    # -----------------------------
    # 2. Ensure both have >= 2 rows
    # -----------------------------
    if len(t_intraday) < 2 or len(s_intraday) < 2:
        return None

    # -----------------------------
    # 3. Ensure both have DatetimeIndex
    # -----------------------------
    if not isinstance(t_intraday.index, pd.DatetimeIndex):
        return None
    if not isinstance(s_intraday.index, pd.DatetimeIndex):
        return None

    # -----------------------------
    # 4. Align timestamps safely
    # -----------------------------
    intraday = pd.DataFrame(index=t_intraday.index)
    intraday["T_close"] = t_intraday["Close"]

    s_aligned = s_intraday["Close"].reindex(t_intraday.index, method=None)
    intraday["S_close"] = s_aligned

    intraday = intraday.dropna()

    if intraday.empty:
        return None

    # -----------------------------
    # 5. Entry at first bar
    # -----------------------------
    first = intraday.iloc[0]
    t_entry = float(first["T_close"])
    s_entry = float(first["S_close"])

    if t_entry <= 0 or s_entry <= 0:
        return None

    # -----------------------------
    # 6. Position sizing
    # -----------------------------
    budget = cfg.budget
    alloc_t = budget * ratio_t
    alloc_s = budget * ratio_s

    shares_t = alloc_t / t_entry
    shares_s = alloc_s / s_entry

    entry_value = alloc_t + alloc_s
    stop_loss_level = entry_value * (1.0 + cfg.stop_loss_pct)
    take_profit_level = (
        entry_value * (1.0 + cfg.take_profit_pct)
        if cfg.take_profit_pct is not None
        else None
    )

    exit_reason = "close"
    exit_value = entry_value

    # -----------------------------
    # 7. Intraday simulation
    # -----------------------------
    for ts, row in intraday.iterrows():
        t_price = float(row["T_close"])
        s_price = float(row["S_close"])

        portfolio_value = shares_t * t_price + shares_s * s_price

        if portfolio_value <= stop_loss_level:
            exit_reason = "stop_loss"
            exit_value = portfolio_value
            break

        if take_profit_level is not None and portfolio_value >= take_profit_level:
            exit_reason = "take_profit"
            exit_value = portfolio_value
            break

        exit_value = portfolio_value

    pnl = exit_value - entry_value
    ret = pnl / entry_value if entry_value != 0 else 0.0

    return DailyResult(
        date=day,
        ratio_t=ratio_t,
        ratio_s=ratio_s,
        pnl=pnl,
        ret=ret,
        exit_reason=exit_reason,
    )

# ---------------------------------------------------------
# Backtest loop
# ---------------------------------------------------------

def run_backtest(cfg: BacktestConfig) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main backtest driver.
    Returns a DataFrame with daily results and equity curve.
    """
    # 1) Build daily signals
    daily_close = get_daily_close(cfg.tickers, cfg.start_date, cfg.end_date)
    signals = build_signal_df(daily_close)

    # Compute 10-day SMA for trend filter
    sma10 = daily_close.rolling(10).mean()

    # We will trade from the second signal day onward (use D's signal on D+1)
    signal_dates = signals.index

    results: List[DailyResult] = []
    equity = cfg.budget
    equity_curve = []
    no_trade_log = []

    for i in range(len(signal_dates) - 1):
        signal_day = signal_dates[i]
        trade_day = signal_dates[i + 1]

        # Extract weights FIRST
        w_t = float(signals.loc[signal_day, "TQQQ_weight"])
        w_s = float(signals.loc[signal_day, "SQQQ_weight"])

        # 1. No-trade zone
        if 0.45 <= w_t <= 0.55:
            no_trade_log.append({
                "Date": trade_day,
                "Reason": "No-trade zone (weak ratio)",
                "TQQQ_weight": w_t,
                "SQQQ_weight": w_s
            })
            continue

        # 2. Missing daily data
        if trade_day not in daily_close.index:
            no_trade_log.append({
                "Date": trade_day,
                "Reason": "Missing daily close data",
                "TQQQ_weight": w_t,
                "SQQQ_weight": w_s
            })
            continue

        # 3. Missing SMA
        if trade_day not in sma10.index:
            no_trade_log.append({
                "Date": trade_day,
                "Reason": "SMA not ready",
                "TQQQ_weight": w_t,
                "SQQQ_weight": w_s
            })
            continue

        # 4. Trend filter
        t_close = daily_close.loc[trade_day, cfg.tickers[0]]
        s_close = daily_close.loc[trade_day, cfg.tickers[1]]
        t_sma10 = sma10.loc[trade_day, cfg.tickers[0]]
        s_sma10 = sma10.loc[trade_day, cfg.tickers[1]]

        if w_t > w_s and not (t_close > t_sma10):
            no_trade_log.append({
                "Date": trade_day,
                "Reason": "Trend filter blocked (TQQQ not above SMA10)",
                "TQQQ_close": float(t_close),
                "TQQQ_SMA10": float(t_sma10),
            "TQQQ_weight": w_t
            })
            continue

        if w_s > w_t and not (s_close > s_sma10):
            no_trade_log.append({
                "Date": trade_day,
                "Reason": "Trend filter blocked (SQQQ not above SMA10)",
                "SQQQ_close": float(s_close),
                "SQQQ_SMA10": float(s_sma10),
                "SQQQ_weight": w_s
            })
            continue

        # Execute trade
        day_result = simulate_day(trade_day, w_t, w_s, cfg)
        if day_result is None:
            no_trade_log.append({
                "Date": trade_day,
                "Reason": "Intraday data missing or insufficient",
                "TQQQ_weight": w_t,
                "SQQQ_weight": w_s
            })
            continue

        equity += day_result.pnl
        equity_curve.append({"Date": day_result.date, "Equity": equity})
        results.append(day_result)

    if not results:
        return pd.DataFrame(), pd.DataFrame(no_trade_log)

    res_df = pd.DataFrame(
        {
            "Date": [r.date for r in results],
            "TQQQ_weight": [r.ratio_t for r in results],
            "SQQQ_weight": [r.ratio_s for r in results],
            "PnL": [r.pnl for r in results],
            "Return": [r.ret for r in results],
            "ExitReason": [r.exit_reason for r in results],
        }
    ).sort_values("Date")

    eq_df = pd.DataFrame(equity_curve).sort_values("Date")
    res_df = res_df.merge(eq_df, on="Date", how="left")

    return res_df, pd.DataFrame(no_trade_log)

# ---------------------------------------------------------
# Simple metrics helper
# ---------------------------------------------------------

def summarize_backtest(results: pd.DataFrame) -> pd.Series:
    if results.empty:
        return pd.Series(dtype=float)

    rets = results["Return"].values
    equity = results["Equity"].values

    total_ret = equity[-1] / equity[0] - 1.0 if len(equity) > 1 else 0.0
    avg_ret = np.mean(rets)
    std_ret = np.std(rets, ddof=1) if len(rets) > 1 else 0.0
    sharpe = avg_ret / std_ret * np.sqrt(252) if std_ret > 0 else np.nan

    wins = (rets > 0).sum()
    losses = (rets < 0).sum()
    win_rate = wins / (wins + losses) if (wins + losses) > 0 else np.nan

    return pd.Series(
        {
            "TotalReturn": total_ret,
            "AvgDailyReturn": avg_ret,
            "StdDailyReturn": std_ret,
            "SharpeApprox": sharpe,
            "WinRate": win_rate,
            "FinalEquity": equity[-1],
        }
    )

# ---------------------------------------------------------
# Example usage (manual, not called automatically)
# ---------------------------------------------------------

if __name__ == "__main__":
    cfg = BacktestConfig(
        start_date="2025-12-01",
        end_date="2026-03-06",
        budget=500.0,
        stop_loss_pct=-0.03,
        take_profit_pct=0.03,
        intraday_interval="5m",
        tickers=("TQQQ", "SQQQ"),
    )

    trades, skipped = run_backtest(cfg)

    print("\n=== TRADES EXECUTED ===")
    print(trades)

    print("\n=== SUMMARY ===")
    print(trades.describe())

    print("\n=== DAYS SKIPPED (DIAGNOSTIC DASHBOARD) ===")
    print(skipped.sort_values("Date"))