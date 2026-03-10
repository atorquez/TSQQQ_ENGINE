import yfinance as yf
import pandas as pd
import numpy as np


class RangeTradingEngine:

    def __init__(
        self,
        ticker,
        window=7,
        entry_percentile=25,
        exit_percentile=75,
        stop_loss_pct=0.02
    ):

        self.ticker = ticker
        self.window = window
        self.entry_percentile = entry_percentile
        self.exit_percentile = exit_percentile
        self.stop_loss_pct = stop_loss_pct


    def download_data(self):
        """
        Download recent price data
        """

        df = yf.download(
            self.ticker,
            period="1mo",
            interval="1d",
            progress=False
        )

        df = df.dropna()

        return df


    def compute_levels(self, df):
        """
        Compute entry and exit levels based on percentiles
        """

        recent_prices = df["Close"].tail(self.window)

        entry_level = np.percentile(recent_prices, self.entry_percentile)
        exit_level = np.percentile(recent_prices, self.exit_percentile)

        return entry_level, exit_level


    def momentum(self, df):
        """
        Simple momentum detection
        """

        if len(df) < 2:
            return "FLAT"

        today = df["Close"].iloc[-1]
        yesterday = df["Close"].iloc[-2]

        if today > yesterday:
            return "UP"

        elif today < yesterday:
            return "DOWN"

        else:
            return "FLAT"


    def generate_signal(self, df, position=None, entry_price=None):

        price = df["Close"].iloc[-1]

        entry_level, exit_level = self.compute_levels(df)
        momentum = self.momentum(df)

        signal = "HOLD"
        stop_loss = None

        if position is None:

            if price <= entry_level and momentum == "UP":
                signal = "BUY"

        else:

            stop_loss = entry_price * (1 - self.stop_loss_pct)

            if price >= exit_level and momentum == "DOWN":
                signal = "SELL"

            elif price <= stop_loss:
                signal = "STOP_LOSS"

        return {
            "ticker": self.ticker,
            "current_price": float(price),
            "entry_level": float(entry_level),
            "exit_level": float(exit_level),
            "momentum": momentum,
            "signal": signal,
            "stop_loss": stop_loss
        }


if __name__ == "__main__":

    ticker = "TQQQ"

    engine = RangeTradingEngine(ticker)

    df = engine.download_data()

    result = engine.generate_signal(df)

    print("\nTrading Decision\n")
    for k, v in result.items():
        print(f"{k}: {v}")