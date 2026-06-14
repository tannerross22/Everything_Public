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
raw_data = yf.download(tickers, start=start_date, end=end_date, progress=False)

# Extract price data - try Adj Close first, then Close
try:
    data = raw_data['Adj Close'].copy()
except KeyError:
    try:
        data = raw_data['Close'].copy()
    except KeyError:
        print("Error: Could not find price data. Available columns:")
        print(raw_data.columns)
        raise

# Ensure data is a DataFrame
if isinstance(data, pd.Series):
    data = data.to_frame()

# Drop any columns with all NaN values (tickers with no data)
data = data.dropna(axis=1, how='all')

# Check which tickers actually have data
available_tickers = list(data.columns)
missing_tickers = [t for t in tickers if t not in available_tickers]

if missing_tickers:
    print(f"⚠ No data available for: {', '.join(missing_tickers)}")
    print(f"✓ Plotting available tickers: {', '.join(available_tickers)}\n")

if not available_tickers:
    print("Error: No data available for any requested tickers.")
    exit()

# Drop rows with any NaN to get the overlapping date range
data_clean = data.dropna()

if len(data_clean) == 0:
    print("Error: No overlapping dates found across all tickers.")
    exit()

print(f"Data available from {data_clean.index[0].date()} to {data_clean.index[-1].date()}")
print(f"Using {len(data_clean)} trading days\n")

# Calculate percentage gain/loss from start date
pct_change = (data_clean / data_clean.iloc[0] - 1) * 100

# Create two subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# Plot 1: Percentage gain/loss
for ticker in available_tickers:
    ax1.plot(pct_change.index, pct_change[ticker], label=ticker, linewidth=2)

ax1.set_xlabel('Date', fontsize=12)
ax1.set_ylabel('% Gain/Loss from Start Date', fontsize=12)
ax1.set_title(f'Stock Performance - Percentage Gain/Loss ({data_clean.index[0].date()} to {data_clean.index[-1].date()})', fontsize=14)
ax1.legend(fontsize=11)
ax1.grid(True, alpha=0.3)

# Plot 2: Absolute prices
for ticker in available_tickers:
    ax2.plot(data_clean.index, data_clean[ticker], label=ticker, linewidth=2)

ax2.set_xlabel('Date', fontsize=12)
ax2.set_ylabel('Price ($)', fontsize=12)
ax2.set_title(f'Stock Price ({data_clean.index[0].date()} to {data_clean.index[-1].date()})', fontsize=14)
ax2.legend(fontsize=11)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
