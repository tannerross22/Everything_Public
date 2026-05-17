import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Get user input for tickers
tickers = []
print("Enter stock tickers (one per line, press Enter with no input to finish):")
while True:
    ticker = input("Ticker: ").strip().upper()
    if not ticker:
        break
    tickers.append(ticker)

if not tickers:
    print("No tickers entered. Exiting.")
    exit()

# Get date range
default_start = (datetime.now() - timedelta(days=365*10)).strftime("%Y-%m-%d")
default_end = datetime.now().strftime("%Y-%m-%d")

print(f"\nDefault date range: {default_start} to {default_end}")
start_input = input(f"Enter start date (YYYY-MM-DD) or press Enter for {default_start}: ").strip()
end_input = input(f"Enter end date (YYYY-MM-DD) or press Enter for {default_end}: ").strip()

start_date = start_input if start_input else default_start
end_date = end_input if end_input else default_end

# Fetch data
print(f"\nFetching data for {', '.join(tickers)}...")
data = yf.download(tickers, start=start_date, end=end_date, progress=False)['Adj Close']

# Handle single ticker case (returns Series instead of DataFrame)
if isinstance(data, pd.Series):
    data = data.to_frame(name=tickers[0])

# Calculate percentage gain/loss from start date
pct_change = (data / data.iloc[0] - 1) * 100

# Plot
plt.figure(figsize=(12, 7))
for ticker in tickers:
    plt.plot(pct_change.index, pct_change[ticker], label=ticker, linewidth=2)

plt.xlabel('Date', fontsize=12)
plt.ylabel('% Gain/Loss from Start Date', fontsize=12)
plt.title(f'Stock Performance ({start_date} to {end_date})', fontsize=14)
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
