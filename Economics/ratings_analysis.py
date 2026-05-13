"""
ratings_analysis.py
--------------------
Simulates a long-only portfolio built from analyst "Buy" ratings
(Morningstar-preferred, falls back to full consensus) and compares
performance against the S&P 500.

Data source : Yahoo Finance via yfinance (upgrades_downgrades).

Caveats
-------
1. Survivorship bias  : The universe is TODAY's top 30 stocks.  Companies
   like NVDA and META were far smaller or non-existent in 2004.  Results
   before ~2012 should be treated with extra scepticism.

2. Rating history depth : Yahoo Finance's upgrades_downgrades typically
   covers only the last few years for most firms.  Morningstar coverage
   may be even thinner.  The program will tell you exactly how much data
   was found before you run the simulation.

3. Ratings are point-in-time signals, not continuous.  A stock rated
   "Buy" in 2018 keeps that rating until a new one appears — which
   may not reflect real Morningstar updates if they aren't in Yahoo's
   feed.
"""

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")


# ── Universe ───────────────────────────────────────────────────────────────────

UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "BRK-B", "LLY",
    "JPM", "V", "UNH", "XOM", "MA", "COST", "HD", "PG", "JNJ", "ABBV",
    "NFLX", "AMD", "CRM", "ORCL", "ADBE", "INTC", "CSCO", "PEP", "KO", "WMT",
]

# ── Grade → score mapping ──────────────────────────────────────────────────────

BUY_GRADES = {
    "strong buy", "buy", "outperform", "accumulate", "overweight",
    "market outperform", "sector outperform", "add", "positive",
    "long-term buy", "conviction buy", "top pick",
}
SELL_GRADES = {
    "sell", "strong sell", "underperform", "reduce", "underweight",
    "market underperform", "sector underperform", "negative",
    "long-term sell", "tender",
}

def grade_to_score(grade):
    """1 = buy, -1 = sell, 0 = hold/neutral/unknown."""
    if pd.isna(grade):
        return 0
    g = str(grade).lower().strip()
    if g in BUY_GRADES:
        return 1
    if g in SELL_GRADES:
        return -1
    return 0


# ── Input helpers ──────────────────────────────────────────────────────────────

def get_date_input(prompt, default=None):
    while True:
        raw = input(prompt).strip()
        if not raw and default:
            return default
        try:
            datetime.strptime(raw, "%Y-%m-%d")
            return raw
        except ValueError:
            print("  Invalid format. Use YYYY-MM-DD.")


def get_float_input(prompt):
    while True:
        raw = input(prompt).strip().lstrip("$").replace(",", "")
        try:
            val = float(raw)
            if val > 0:
                return val
            print("  Must be a positive number.")
        except ValueError:
            print("  Invalid number.")


# ── Data fetching ──────────────────────────────────────────────────────────────

def fetch_all_ratings(tickers):
    """
    Pull upgrades_downgrades for every ticker.
    Returns a combined DataFrame with columns:
      GradeDate, Ticker, Firm, ToGrade, FromGrade, Action, Score
    """
    rows = []
    print(f"\nFetching analyst ratings for {len(tickers)} tickers...")

    for ticker in tickers:
        try:
            t  = yf.Ticker(ticker)
            ud = t.upgrades_downgrades
            if ud is None or ud.empty:
                print(f"  {ticker:<8} no data")
                continue

            ud = ud.copy().reset_index()
            # Column name varies slightly across yfinance versions
            date_col = ud.columns[0]
            ud = ud.rename(columns={date_col: "GradeDate"})
            ud["GradeDate"] = pd.to_datetime(ud["GradeDate"]).dt.tz_localize(None)
            ud["Ticker"] = ticker
            ud["Score"]  = ud["ToGrade"].apply(grade_to_score)

            keep = ["GradeDate", "Ticker", "Firm", "ToGrade", "FromGrade", "Action", "Score"]
            keep = [c for c in keep if c in ud.columns]
            rows.append(ud[keep])

            span = f"{ud.GradeDate.min().date()} to {ud.GradeDate.max().date()}"
            print(f"  {ticker:<8} {len(ud):>4} ratings  ({span})")

        except Exception as e:
            print(f"  {ticker:<8} error: {e}")

    if not rows:
        return pd.DataFrame()

    combined = pd.concat(rows, ignore_index=True).sort_values("GradeDate")
    return combined


def summarise_firms(df):
    """Print a ranked list of analyst firms and how many stocks they cover."""
    print("\nAnalyst firms found in dataset:")
    print(f"  {'Firm':<40} {'Ratings':>7}  {'Tickers':>7}")
    print("  " + "-" * 58)
    summary = (df.groupby("Firm")
                 .agg(ratings=("Score", "count"), tickers=("Ticker", "nunique"))
                 .sort_values("ratings", ascending=False))
    for firm, row in summary.head(30).iterrows():
        print(f"  {firm:<40} {row.ratings:>7}  {row.tickers:>7}")
    return summary


def filter_by_firm(df, firm_name):
    """Case-insensitive partial match on firm name."""
    mask     = df["Firm"].str.lower().str.contains(firm_name.lower(), na=False)
    filtered = df[mask]
    n_stocks = filtered["Ticker"].nunique()
    print(f"\n  '{firm_name}' matched {len(filtered)} ratings across {n_stocks} stocks.")
    if n_stocks < 3:
        print("  WARNING: fewer than 3 stocks covered — portfolio will be very concentrated.")
    return filtered


# ── Rating history matrix ──────────────────────────────────────────────────────

def build_rating_matrix(ratings_df, tickers, start_date, end_date):
    """
    At each monthly rebalance date, record each stock's most recent rating
    (1=buy, 0=hold, -1=sell) based only on ratings published BEFORE that date.

    Returns a DataFrame: index=monthly dates, columns=tickers, values=score.
    """
    start       = pd.Timestamp(start_date)
    end         = pd.Timestamp(end_date)
    rebal_dates = pd.date_range(start=start, end=end, freq="MS")  # month start

    matrix = pd.DataFrame(0.0, index=rebal_dates, columns=tickers)

    for ticker in tickers:
        t_df = ratings_df[ratings_df["Ticker"] == ticker].sort_values("GradeDate")
        if t_df.empty:
            continue
        for rebal in rebal_dates:
            prior = t_df[t_df["GradeDate"] < rebal]
            if not prior.empty:
                matrix.at[rebal, ticker] = prior.iloc[-1]["Score"]

    return matrix


# ── Portfolio simulation ───────────────────────────────────────────────────────

def simulate_portfolio(rating_matrix, price_df, start_date, end_date, mode="long_buy"):
    """
    mode='long_buy'   : equal-weight long in all Buy-rated stocks
    mode='long_short' : long Buy, short Sell (zero net exposure)

    Returns normalised portfolio Series (start=100).
    Also returns a Series of daily holding counts for diagnostics.
    """
    start  = pd.Timestamp(start_date)
    end    = pd.Timestamp(end_date)
    prices = price_df.loc[start:end].ffill()

    if prices.empty:
        return None, None

    rebal_dates   = sorted(rating_matrix.index)
    rebal_idx     = 0
    long_holdings  = []
    short_holdings = []

    port_val   = 100.0
    values     = [100.0]
    hold_counts = [0]
    dates      = [prices.index[0]]

    for i in range(1, len(prices)):
        date      = prices.index[i]
        prev_date = prices.index[i - 1]

        # Advance rebalance pointer
        while rebal_idx < len(rebal_dates) and rebal_dates[rebal_idx] <= date:
            rd   = rebal_dates[rebal_idx]
            row  = rating_matrix.loc[rd]
            long_holdings  = [t for t in row.index if row[t] == 1  and t in prices.columns]
            short_holdings = [t for t in row.index if row[t] == -1 and t in prices.columns]
            rebal_idx += 1

        # Daily P&L
        long_rets  = []
        short_rets = []

        for t in long_holdings:
            p0 = prices.at[prev_date, t] if prev_date in prices.index else None
            p1 = prices.at[date, t]
            if pd.notna(p0) and pd.notna(p1) and p0 > 0:
                long_rets.append(p1 / p0 - 1)

        if mode == "long_short":
            for t in short_holdings:
                p0 = prices.at[prev_date, t] if prev_date in prices.index else None
                p1 = prices.at[date, t]
                if pd.notna(p0) and pd.notna(p1) and p0 > 0:
                    short_rets.append(-(p1 / p0 - 1))  # short = inverse return

        all_rets = long_rets + short_rets
        if all_rets:
            port_val *= (1 + sum(all_rets) / len(all_rets))

        values.append(port_val)
        hold_counts.append(len(long_holdings))
        dates.append(date)

    series = pd.Series(values,      index=pd.DatetimeIndex(dates))
    counts = pd.Series(hold_counts, index=pd.DatetimeIndex(dates))
    return series, counts


# ── Diagnostics ───────────────────────────────────────────────────────────────

def print_monthly_holdings(rating_matrix, firm_label):
    """Show how many stocks were rated Buy at each rebalance date."""
    print(f"\nMonthly Buy count ({firm_label}):")
    print(f"  {'Date':<12}  {'Buy':>4}  {'Hold':>5}  {'Sell':>5}  Holdings")
    print("  " + "-" * 65)
    for date, row in rating_matrix.iterrows():
        buys  = [t for t in row.index if row[t] ==  1]
        holds = [t for t in row.index if row[t] ==  0]
        sells = [t for t in row.index if row[t] == -1]
        print(f"  {str(date.date()):<12}  {len(buys):>4}  {len(holds):>5}  {len(sells):>5}"
              f"  {', '.join(buys) if buys else '(none — holding cash)'}")


# ── Plot ───────────────────────────────────────────────────────────────────────

def plot_results(sp_norm, port_norm, port_label, hold_counts, start, end):
    sp_ret   = float(sp_norm.iloc[-1])   - 100
    port_ret = float(port_norm.iloc[-1]) - 100
    days     = (sp_norm.index[-1] - sp_norm.index[0]).days
    sp_ann   = ((float(sp_norm.iloc[-1])   / 100) ** (365 / days) - 1) * 100
    port_ann = ((float(port_norm.iloc[-1]) / 100) ** (365 / days) - 1) * 100

    fig, axes = plt.subplots(3, 1, figsize=(14, 13),
                             gridspec_kw={"height_ratios": [3, 1.2, 1.2]})
    fig.suptitle(f"Analyst Ratings Portfolio vs S&P 500  |  {start} to {end}",
                 fontsize=14, fontweight="bold")

    # Panel 1: equity curves
    ax = axes[0]
    ax.plot(sp_norm.index,   sp_norm.values,
            label=f"S&P 500 B&H  ({sp_ret:+.1f}%,  ann {sp_ann:+.1f}%)",
            color="#1f77b4", linewidth=2)
    ax.plot(port_norm.index, port_norm.values,
            label=f"{port_label}  ({port_ret:+.1f}%,  ann {port_ann:+.1f}%)",
            color="#d62728", linewidth=2, linestyle="--")
    ax.set_ylabel("Portfolio Value (start = $100)", fontsize=11)
    ax.set_title("Normalised Performance", fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Panel 2: rolling outperformance
    ax2 = axes[1]
    outperf = port_norm.reindex(sp_norm.index, method="ffill") - sp_norm
    ax2.fill_between(outperf.index, outperf.values, 0,
                     where=outperf.values >= 0, alpha=0.5, color="#2ca02c", label="Ahead of S&P")
    ax2.fill_between(outperf.index, outperf.values, 0,
                     where=outperf.values <  0, alpha=0.5, color="#d62728", label="Behind S&P")
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_ylabel("Outperformance ($)", fontsize=10)
    ax2.set_title("Rolling Outperformance vs S&P 500", fontsize=11)
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Panel 3: number of holdings over time
    ax3 = axes[2]
    ax3.fill_between(hold_counts.index, hold_counts.values,
                     alpha=0.6, color="#ff7f0e", step="post")
    ax3.set_ylabel("# Stocks Held", fontsize=10)
    ax3.set_title("Number of Buy-Rated Stocks in Portfolio", fontsize=11)
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha="right")

    plt.tight_layout()
    out = "ratings_comparison.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"\nPlot saved -> {out}")
    plt.show()


# ── Investment calculator ──────────────────────────────────────────────────────

def print_results(sp_norm, port_norm, port_label, initial):
    days = (sp_norm.index[-1] - sp_norm.index[0]).days

    def stats(norm, label):
        final   = initial * float(norm.iloc[-1]) / 100
        ret_pct = float(norm.iloc[-1]) - 100
        ann     = ((float(norm.iloc[-1]) / 100) ** (365 / days) - 1) * 100 if days > 0 else 0
        pl      = final - initial
        print(f"  {label}")
        print(f"    Initial             ${initial:>12,.2f}")
        print(f"    Final Value         ${final:>12,.2f}")
        print(f"    Profit / Loss       ${pl:>+12,.2f}")
        print(f"    Total Return        {ret_pct:>+11.1f}%")
        print(f"    Annualised Return   {ann:>+11.2f}%")
        print()

    print("\n" + "=" * 54)
    print("  INVESTMENT RESULTS")
    print("=" * 54)
    stats(sp_norm,   "S&P 500 (Buy & Hold)")
    stats(port_norm, port_label)
    print("=" * 54)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("\n+=============================================+")
    print("|  Analyst Ratings Portfolio vs S&P 500      |")
    print("+=============================================+")
    print("\nNOTE: Morningstar keeps its ratings behind a paywall and does NOT")
    print("      appear in Yahoo Finance's free feed.  This program uses Wall")
    print("      Street analyst upgrades/downgrades instead (Morgan Stanley,")
    print("      Goldman Sachs, Barclays, JPMorgan, Wedbush, etc.).")
    print("      After fetching, you will see every firm available and can")
    print("      filter to any single firm or use the full consensus.")

    start = get_date_input("\nAnalysis start date (YYYY-MM-DD) [default: 2015-01-01]: ", "2015-01-01")
    end   = get_date_input("Analysis end date   (YYYY-MM-DD) [default: today]:      ",
                           datetime.today().strftime("%Y-%m-%d"))

    # Step 1: Fetch all ratings
    all_ratings = fetch_all_ratings(UNIVERSE)
    if all_ratings.empty:
        print("ERROR: No ratings data found.")
        return

    # Step 2: Show firms and let user pick
    firm_summary = summarise_firms(all_ratings)

    print("\nWhich analyst firm to use?")
    print("  Press Enter to use ALL firms (consensus)")
    print("  Or type a firm name (partial match, e.g. 'morningstar', 'goldman', 'jpmorgan')")
    firm_input = input("  Firm filter: ").strip()

    if firm_input:
        ratings = filter_by_firm(all_ratings, firm_input)
        firm_label = firm_input.title()
        if ratings.empty or ratings["Ticker"].nunique() < 2:
            print(f"  Too few stocks matched '{firm_input}'. Falling back to all firms.")
            ratings   = all_ratings
            firm_label = "All Analysts (Consensus)"
    else:
        ratings   = all_ratings
        firm_label = "All Analysts (Consensus)"

    # Coverage summary
    date_range = ratings["GradeDate"]
    print(f"\n  Using: {firm_label}")
    print(f"  Ratings span: {date_range.min().date()} to {date_range.max().date()}")
    print(f"  Stocks covered: {ratings['Ticker'].nunique()}/{len(UNIVERSE)}")
    buy_ct  = (ratings["Score"] ==  1).sum()
    sell_ct = (ratings["Score"] == -1).sum()
    hold_ct = (ratings["Score"] ==  0).sum()
    print(f"  Buy: {buy_ct}  |  Hold: {hold_ct}  |  Sell: {sell_ct}")

    # Step 3: Portfolio mode
    print("\nPortfolio mode:")
    print("  1. Long-only Buy (equal-weight all Buy-rated stocks)")
    print("  2. Long Buy / Short Sell (zero net exposure)")
    while True:
        mode_raw = input("  Choice [1/2, default 1]: ").strip()
        if mode_raw in ("", "1"):
            mode = "long_buy"
            break
        if mode_raw == "2":
            mode = "long_short"
            break
        print("  Enter 1 or 2.")

    # Step 4: Build rating matrix
    print("\nBuilding monthly rating matrix...")
    rating_matrix = build_rating_matrix(ratings, UNIVERSE, start, end)

    buy_counts = (rating_matrix == 1).sum(axis=1)
    print(f"  Average Buy-rated stocks per month: {buy_counts.mean():.1f}")
    print(f"  Min: {buy_counts.min()}  Max: {buy_counts.max()}")

    if buy_counts.max() == 0:
        print("\nERROR: No Buy ratings found in this date range.")
        print("       Try a different firm filter, a later start date, or use All Analysts.")
        return

    show_holdings = input("\nShow monthly holdings table? (y/N): ").strip().lower()
    if show_holdings == "y":
        print_monthly_holdings(rating_matrix, firm_label)

    # Step 5: Download prices
    print(f"\nDownloading price data ({start} to {end})...")
    all_tickers = ["^GSPC"] + UNIVERSE
    raw_df = yf.download(all_tickers, start=start, end=end, progress=False, auto_adjust=True)

    # Extract Close prices into a flat DataFrame
    price_df = raw_df["Close"].copy()
    price_df.columns.name = None
    sp_close = price_df["^GSPC"].dropna()
    stock_prices = price_df.drop(columns=["^GSPC"])

    # Step 6: Simulate
    mode_label = "Long Buy" if mode == "long_buy" else "Long Buy / Short Sell"
    port_label = f"{firm_label} — {mode_label}"
    print(f"\nSimulating '{port_label}'...")
    port_series, hold_counts = simulate_portfolio(
        rating_matrix, stock_prices, start, end, mode=mode
    )

    if port_series is None:
        print("ERROR: Simulation produced no results.")
        return

    # Normalise S&P to 100
    sp_aligned = sp_close.reindex(port_series.index, method="ffill")
    sp_norm    = sp_aligned / float(sp_aligned.iloc[0]) * 100

    sp_ret   = float(sp_norm.iloc[-1])   - 100
    port_ret = float(port_series.iloc[-1]) - 100
    print(f"\n  S&P 500 return      : {sp_ret:+.1f}%")
    print(f"  Portfolio return    : {port_ret:+.1f}%")

    # Step 7: Plot
    plot_results(sp_norm, port_series, port_label, hold_counts, start, end)

    # Step 8: Investment calculator
    amount = get_float_input("\nInvestment amount ($): ")
    print_results(sp_norm, port_series, port_label, amount)


if __name__ == "__main__":
    main()
