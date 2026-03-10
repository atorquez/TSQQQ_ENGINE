import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

tickers = ['TQQQ', 'SQQQ']

# Use the reliable endpoint
dfs = []

for t in tickers:
    df = yf.Ticker(t).history(period="2y", interval="1d")
    if df.empty:
        print(f"No data for {t}")
        continue

    # Use Close instead of Adj Close (always present)
    df = df[['Close']].rename(columns={'Close': t})
    dfs.append(df)

# Merge all tickers on date index
merged = pd.concat(dfs, axis=1)

print("Shape:", merged.shape)
print(merged.head())

# Plot
plt.figure(figsize=(12, 6))
merged.plot()
plt.title('2-Year Close Price History')
plt.xlabel('Date')
plt.ylabel('Price (USD)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
