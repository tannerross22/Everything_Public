import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

TOP_SP500 = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "BRK-B", "LLY",
    "JPM", "V", "UNH", "XOM", "MA", "COST", "HD", "PG", "JNJ", "ABBV",
]


# ── Helpers ────────────────────────────────────────────────────────────────────

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


def get_close(df, ticker):
    """Extract Close Series regardless of whether yfinance returns MultiIndex columns."""
    if isinstance(df.columns, pd.MultiIndex):
        return df["Close"][ticker].squeeze()
    return df["Close"]


# ── Data ───────────────────────────────────────────────────────────────────────

def bulk_download(tickers, start, end):
    """Download all tickers in one request. Returns {ticker: Close Series}."""
    print(f"Downloading price data for {len(tickers)} stocks...", flush=True)
    df = yf.download(tickers, start=start, end=end, progress=False, auto_adjust=True)
    prices = {}
    for ticker in tickers:
        try:
            s = df["Close"][ticker].dropna()
            if len(s) > 5:
                prices[ticker] = s
        except Exception:
            pass
    print(f"  Got data for {len(prices)}/{len(tickers)} tickers.")
    return prices


def find_top_performer(prices):
    print("\nFull-period total returns:")
    best_ticker, best_ret = None, -float("inf")
    for ticker, s in prices.items():
        ret = float(s.iloc[-1]) / float(s.iloc[0]) - 1
        print(f"  {ticker:<8} {ret * 100:+.1f}%")
        if ret > best_ret:
            best_ret, best_ticker = ret, ticker
    return best_ticker, best_ret * 100


# ── Rotation simulation ────────────────────────────────────────────────────────

def simulate_rotation(prices, rebalance_freq="W", lookback=20):
    """
    At each rebalance date, rank all stocks by their trailing `lookback`-day
    return and rotate 100 % into the leader.  Returns a portfolio-value Series
    normalised to 100 at the start.

    Decision uses only data up to (and including) the close of the rebalance day,
    so the new position is effective the *next* trading day — no look-ahead bias.
    """
    price_df = pd.DataFrame(prices).ffill()

    if rebalance_freq == "W":
        # Last trading day of each calendar week
        rebal_set = set(price_df.resample("W-FRI").last().index)
    else:
        rebal_set = set(price_df.index)

    port_val  = 100.0
    current   = None          # currently held ticker
    next_hold = None          # position to apply starting tomorrow
    values    = [port_val]

    for i in range(1, len(price_df)):
        today     = price_df.index[i]
        yesterday = price_df.index[i - 1]

        # Switch to the position decided on the previous rebalance day
        if next_hold is not None:
            current   = next_hold
            next_hold = None

        # Mark-to-market: apply today's return for the current holding
        if current is not None:
            p0 = price_df.at[yesterday, current]
            p1 = price_df.at[today,     current]
            if pd.notna(p0) and pd.notna(p1) and p0 > 0:
                port_val *= p1 / p0

        # Decide tomorrow's holding on rebalance days (after enough history)
        if today in rebal_set and i >= lookback:
            window = price_df.iloc[i - lookback: i + 1]
            rets = {}
            for t in price_df.columns:
                col = window[t].dropna()
                if len(col) >= 2:
                    rets[t] = float(col.iloc[-1]) / float(col.iloc[0]) - 1
            if rets:
                next_hold = max(rets, key=rets.get)

        values.append(port_val)

    return pd.Series(values, index=price_df.index)


# ── Visualisation ──────────────────────────────────────────────────────────────

def plot_comparison(sp_norm, stk_norm, stk_ticker, rot_norm, rot_label, start, end):
    sp_ret  = float(sp_norm.iloc[-1])  - 100
    stk_ret = float(stk_norm.iloc[-1]) - 100
    rot_ret = float(rot_norm.iloc[-1]) - 100

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 11))
    fig.suptitle(
        f"S&P 500  vs  {stk_ticker}  vs  Rotation Strategy\n{start} → {end}",
        fontsize=14, fontweight="bold", y=0.99,
    )

    # Normalised growth chart
    ax1.plot(sp_norm.index,  sp_norm.values,  label="S&P 500 (Buy & Hold)",                          color="#1f77b4", linewidth=2)
    ax1.plot(stk_norm.index, stk_norm.values, label=f"{stk_ticker} (Hindsight B&H — oracle only)",  color="#d62728", linewidth=2, linestyle=":")
    ax1.plot(rot_norm.index, rot_norm.values, label=rot_label,                                        color="#2ca02c", linewidth=2, linestyle="--")
    ax1.set_ylabel("Portfolio Value (start = $100)", fontsize=11)
    ax1.set_title("Normalised Performance", fontsize=12)
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Total return bars
    labels  = ["S&P 500", stk_ticker, "Rotation"]
    returns = [sp_ret, stk_ret, rot_ret]
    colors  = ["#1f77b4", "#d62728", "#2ca02c"]
    bars = ax2.bar(labels, returns, color=colors, alpha=0.75, edgecolor="black", width=0.4)
    ax2.set_ylabel("Total Return (%)", fontsize=11)
    ax2.set_title("Total Return Comparison", fontsize=12)
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.grid(True, alpha=0.3, axis="y")
    for bar, ret in zip(bars, returns):
        offset = max(abs(ret) * 0.02, 0.5)
        y_pos = ret + offset if ret >= 0 else ret - offset * 3
        ax2.text(
            bar.get_x() + bar.get_width() / 2, y_pos,
            f"{ret:+.1f}%", ha="center", va="bottom", fontweight="bold", fontsize=12,
        )

    plt.tight_layout()
    out_path = "economics_comparison.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"\nPlot saved → {out_path}")
    plt.show()


# ── Results ────────────────────────────────────────────────────────────────────

def print_results(sp_norm, stk_norm, stk_ticker, rot_norm, rot_label, initial):
    days = (sp_norm.index[-1] - sp_norm.index[0]).days

    def stats(norm):
        final    = initial * float(norm.iloc[-1]) / 100
        ret_pct  = float(norm.iloc[-1]) - 100
        ann      = ((float(norm.iloc[-1]) / 100) ** (365 / days) - 1) * 100 if days > 0 else 0
        return final, ret_pct, ann

    print("\n" + "=" * 58)
    print("  INVESTMENT RESULTS")
    print("=" * 58)
    print(f"  Initial Investment      ${initial:>12,.2f}")
    print(f"  Period                  {sp_norm.index[0].date()} → {sp_norm.index[-1].date()}")
    print()

    rows = [
        ("S&P 500 (Buy & Hold)", stats(sp_norm)),
        (f"{stk_ticker} (Hindsight B&H — oracle only)", stats(stk_norm)),
        (rot_label,                     stats(rot_norm)),
    ]
    for label, (final, ret, ann) in rows:
        print(f"  {label}")
        print(f"    Final Value             ${final:>12,.2f}")
        print(f"    Total Return            {ret:>+11.1f}%")
        print(f"    Annualized Return       {ann:>+11.2f}%")
        print()
    print("=" * 58)


# ── Lookback sweep ─────────────────────────────────────────────────────────────

def sweep_lookback(prices, sp_close, rebalance_freq="W", lo=5, hi=252, step=5):
    """
    Run the rotation strategy for every lookback in range(lo, hi+1, step).
    Returns a DataFrame indexed by lookback window with four metrics:
      total_return (%), annualized_return (%), sharpe_ratio, max_drawdown (%).

    ⚠  All metrics are in-sample.  The 'optimal' window found here is the one
       that happened to work best over this specific historical period — it is
       NOT guaranteed to be optimal going forward.
    """
    days = (sp_close.index[-1] - sp_close.index[0]).days
    sp_ann = ((sp_close.iloc[-1] / sp_close.iloc[0]) ** (365 / days) - 1) * 100

    rows = []
    lookbacks = list(range(lo, hi + 1, step))
    print(f"\nSweeping {len(lookbacks)} lookback windows ({lo}d to {hi}d, step {step})...")

    for lb in lookbacks:
        rot = simulate_rotation(prices, rebalance_freq=rebalance_freq, lookback=lb)

        total_ret = float(rot.iloc[-1]) - 100
        ann_ret   = ((float(rot.iloc[-1]) / 100) ** (365 / days) - 1) * 100 if days > 0 else 0

        daily_rets = rot.pct_change().dropna()
        sharpe = (daily_rets.mean() / daily_rets.std() * (252 ** 0.5)) if daily_rets.std() > 0 else 0

        rolling_max = rot.cummax()
        max_dd = float(((rot - rolling_max) / rolling_max).min()) * 100

        rows.append(dict(lookback=lb, total_return=total_ret, annualized_return=ann_ret,
                         sharpe=sharpe, max_drawdown=max_dd))

    df = pd.DataFrame(rows).set_index("lookback")
    best_lb = df["sharpe"].idxmax()

    print(f"\n  {'Lookback':>8}  {'Total%':>8}  {'Ann%':>8}  {'Sharpe':>8}  {'MaxDD%':>8}")
    print("  " + "-" * 48)
    for lb, row in df.iterrows():
        marker = " <- best Sharpe" if lb == best_lb else ""
        print(f"  {lb:>8d}  {row.total_return:>8.1f}  {row.annualized_return:>8.1f}"
              f"  {row.sharpe:>8.2f}  {row.max_drawdown:>8.1f}{marker}")

    print(f"\n  S&P 500 annualized return over same period: {sp_ann:+.1f}%")
    return df, best_lb


def plot_sweep(df, sp_close, rebalance_freq, start, end):
    days   = (sp_close.index[-1] - sp_close.index[0]).days
    sp_ann = ((float(sp_close.iloc[-1]) / float(sp_close.iloc[0])) ** (365 / days) - 1) * 100
    sp_total = (float(sp_close.iloc[-1]) / float(sp_close.iloc[0]) - 1) * 100
    freq_label = "Weekly" if rebalance_freq == "W" else "Daily"
    best_sharpe = df["sharpe"].idxmax()
    best_ann    = df["annualized_return"].idxmax()

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(
        f"Lookback Window Sweep — {freq_label} Rebalance  |  {start} → {end}\n"
        f"⚠  In-sample optimisation — results reflect the past, not the future",
        fontsize=13, fontweight="bold",
    )

    specs = [
        (axes[0, 0], "annualized_return", "Annualized Return (%)", sp_ann,   "Ann. Return"),
        (axes[0, 1], "total_return",       "Total Return (%)",       sp_total, "Total Return"),
        (axes[1, 0], "sharpe",             "Sharpe Ratio",           None,     "Sharpe"),
        (axes[1, 1], "max_drawdown",       "Max Drawdown (%)",       None,     "Max Drawdown"),
    ]

    for ax, col, ylabel, sp_ref, title in specs:
        ax.plot(df.index, df[col], color="#2ca02c", linewidth=2, marker="o", markersize=3)

        if sp_ref is not None:
            ax.axhline(sp_ref, color="#1f77b4", linestyle="--", linewidth=1.5,
                       label=f"S&P 500 ({sp_ref:+.1f}%)")
            ax.legend(fontsize=9)

        # Mark best Sharpe on every panel
        ax.axvline(best_sharpe, color="orange", linestyle=":", linewidth=1.5,
                   label=f"Best Sharpe (lb={best_sharpe})")

        ax.set_xlabel("Lookback Window (trading days)", fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(title, fontsize=11)
        ax.grid(True, alpha=0.3)

    # Shared best-Sharpe legend entry
    axes[0, 0].legend(fontsize=9)
    axes[1, 0].legend(fontsize=9)

    plt.tight_layout()
    out = "economics_sweep.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"Sweep plot saved → {out}")
    plt.show()


# ── Walk-forward optimization ──────────────────────────────────────────────────

def walk_forward_opt(prices, sp_close, is_days=504, oos_days=126,
                     lo=5, hi=100, step=5, rebalance_freq="W"):
    """
    At each fold:
      1. Find the lookback with the best Sharpe on the IS window (in-sample).
      2. Apply that lookback — blind — to the next OOS window (out-of-sample).
      3. Chain all OOS segments into a single equity curve.

    Every point on the returned curve was generated without any future knowledge.
    """
    price_df = pd.DataFrame(prices).ffill()
    lookbacks = list(range(lo, hi + 1, step))
    n = len(price_df)
    total_folds = max(1, (n - is_days) // oos_days)

    fold_log, oos_segments = [], []
    fold_num, i = 0, 0

    print(f"\nRunning WFO: IS={is_days}d, OOS={oos_days}d, "
          f"~{total_folds} folds, {len(lookbacks)} lookbacks each...")
    print(f"  (each fold optimises over {lo}-{hi}d windows — may take a minute)\n")

    while i + is_days + oos_days <= n:
        fold_num += 1
        is_end  = i + is_days
        oos_end = min(is_end + oos_days, n)

        print(f"  Fold {fold_num}/{total_folds}  "
              f"IS {price_df.index[i].date()} - {price_df.index[is_end-1].date()}  "
              f"OOS {price_df.index[is_end].date()} - {price_df.index[oos_end-1].date()}",
              end="  ", flush=True)

        # IS optimisation: find best lookback by Sharpe ratio
        is_prices = {t: price_df[t].iloc[i:is_end].dropna()
                     for t in price_df.columns
                     if len(price_df[t].iloc[i:is_end].dropna()) > max(lookbacks)}

        best_lb, best_sharpe = lookbacks[0], -float("inf")
        for lb in lookbacks:
            rot = simulate_rotation(is_prices, rebalance_freq=rebalance_freq, lookback=lb)
            dr  = rot.pct_change().dropna()
            sh  = float(dr.mean() / dr.std() * 252 ** 0.5) if dr.std() > 0 else -999
            if sh > best_sharpe:
                best_sharpe, best_lb = sh, lb

        print(f"-> best lb={best_lb:>3d} (IS Sharpe={best_sharpe:.2f})")

        # OOS simulation: seed with `best_lb` days of IS data so the lookback
        # window is already full on the first OOS trading day
        warmup_start = is_end - best_lb
        oos_prices   = {t: price_df[t].iloc[warmup_start:oos_end].dropna()
                        for t in price_df.columns}

        rot_full  = simulate_rotation(oos_prices, rebalance_freq=rebalance_freq, lookback=best_lb)
        warmup_len = is_end - warmup_start
        oos_segments.append(rot_full.iloc[warmup_len:])

        fold_log.append(dict(fold=fold_num,
                             is_start=price_df.index[i].date(),
                             is_end=price_df.index[is_end - 1].date(),
                             oos_start=price_df.index[is_end].date(),
                             oos_end=price_df.index[oos_end - 1].date(),
                             best_lb=best_lb))
        i += oos_days

    if not oos_segments:
        print("  Not enough data for even one fold.")
        return None, pd.DataFrame(fold_log)

    # Chain OOS segments: each segment's first day anchors to previous ending value
    port_val   = 100.0
    all_dates  = [oos_segments[0].index[0]]
    all_values = [100.0]

    for seg in oos_segments:
        norm = seg / float(seg.iloc[0])
        for date, v in zip(seg.index[1:], norm.values[1:]):
            all_dates.append(date)
            all_values.append(port_val * float(v))
        port_val = all_values[-1]

    wfo_curve = pd.Series(all_values, index=pd.DatetimeIndex(all_dates))
    return wfo_curve, pd.DataFrame(fold_log)


def plot_wfo_results(wfo_curve, sp_close, fold_df, start, end):
    sp_aligned = sp_close.reindex(wfo_curve.index, method="ffill")
    sp_norm    = sp_aligned / float(sp_aligned.iloc[0]) * 100

    days    = (wfo_curve.index[-1] - wfo_curve.index[0]).days
    wfo_ret = float(wfo_curve.iloc[-1]) - 100
    sp_ret  = float(sp_norm.iloc[-1])  - 100
    wfo_ann = ((float(wfo_curve.iloc[-1]) / 100) ** (365 / days) - 1) * 100
    sp_ann  = ((float(sp_norm.iloc[-1])  / 100) ** (365 / days) - 1) * 100

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle(
        f"Walk-Forward Optimization  |  {start} to {end}\n"
        "Every point was generated out-of-sample — no look-ahead",
        fontsize=13, fontweight="bold",
    )

    ax1.plot(sp_norm.index,   sp_norm.values,   label=f"S&P 500 B&H ({sp_ret:+.1f}%,  ann {sp_ann:+.1f}%)",
             color="#1f77b4", linewidth=2)
    ax1.plot(wfo_curve.index, wfo_curve.values, label=f"WFO Rotation ({wfo_ret:+.1f}%,  ann {wfo_ann:+.1f}%)",
             color="#2ca02c", linewidth=2, linestyle="--")

    for _, row in fold_df.iterrows():
        ax1.axvspan(pd.Timestamp(str(row.oos_start)), pd.Timestamp(str(row.oos_end)),
                    alpha=0.06, color="green")

    ax1.set_ylabel("Portfolio Value (start = $100)", fontsize=11)
    ax1.set_title("WFO Equity Curve (shaded = OOS windows)", fontsize=12)
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha="right")

    ax2.bar(range(len(fold_df)), fold_df["best_lb"], color="#2ca02c", alpha=0.75, edgecolor="black")
    ax2.set_xlabel("Fold", fontsize=11)
    ax2.set_ylabel("Chosen Lookback (days)", fontsize=11)
    ax2.set_title("Lookback Selected Per Fold (by IS Sharpe) — stability = low variance here", fontsize=12)
    ax2.set_xticks(range(len(fold_df)))
    ax2.set_xticklabels([str(r.oos_start)[:7] for _, r in fold_df.iterrows()],
                        rotation=45, ha="right", fontsize=8)
    ax2.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig("economics_wfo.png", dpi=150, bbox_inches="tight")
    print("WFO plot saved -> economics_wfo.png")
    plt.show()


# ── Stability heatmap ──────────────────────────────────────────────────────────

def compute_stability_matrix(prices, sp_close, lo=5, hi=100, step=5, rebalance_freq="W"):
    """
    For each calendar year and each lookback, compute how much the rotation
    strategy beat (or lagged) the S&P 500 on an annualised basis.

    A lookback with a consistently green column is a robust parameter choice.
    A lookback that's great in some years but red in others is fragile.
    """
    price_df  = pd.DataFrame(prices).ffill()
    lookbacks = list(range(lo, hi + 1, step))
    years     = sorted(set(price_df.index.year))

    matrix = pd.DataFrame(index=years, columns=lookbacks, dtype=float)

    total = len(years) * len(lookbacks)
    done  = 0
    print(f"\nBuilding stability matrix ({len(years)} years x {len(lookbacks)} windows = {total} simulations)...")

    for year in years:
        year_mask   = price_df.index.year == year
        year_idx    = price_df.index[year_mask]
        if len(year_idx) < 20:
            continue

        start_pos = price_df.index.get_loc(year_idx[0])
        end_pos   = price_df.index.get_loc(year_idx[-1]) + 1

        sp_year = sp_close[year_mask]
        if len(sp_year) < 2:
            continue
        span      = (sp_year.index[-1] - sp_year.index[0]).days
        sp_ann    = ((float(sp_year.iloc[-1]) / float(sp_year.iloc[0])) ** (365 / span) - 1) * 100

        for lb in lookbacks:
            warmup_start = max(0, start_pos - lb)
            warmup_len   = start_pos - warmup_start

            slice_px = {t: price_df[t].iloc[warmup_start:end_pos].dropna()
                        for t in price_df.columns}

            rot = simulate_rotation(slice_px, rebalance_freq=rebalance_freq, lookback=lb)
            oos = rot.iloc[warmup_len:]

            if len(oos) < 2:
                matrix.at[year, lb] = 0.0
            else:
                d   = (oos.index[-1] - oos.index[0]).days
                ann = ((float(oos.iloc[-1]) / float(oos.iloc[0])) ** (365 / d) - 1) * 100 if d > 0 else 0
                matrix.at[year, lb] = round(ann - sp_ann, 1)

            done += 1

        pct = done / total * 100
        print(f"  {year}  S&P {sp_ann:+.1f}%  [{pct:4.0f}% done]")

    return matrix


def plot_stability_heatmap(matrix, rebalance_freq, start, end):
    freq_label = "Weekly" if rebalance_freq == "W" else "Daily"
    vmax = max(float(abs(matrix.values.astype(float)).max()), 1)

    fig, ax = plt.subplots(figsize=(max(12, len(matrix.columns) * 0.5 + 3),
                                    max(6, len(matrix.index) * 0.45 + 2)))

    im = ax.imshow(matrix.astype(float).values, aspect="auto",
                   cmap="RdYlGn", vmin=-vmax, vmax=vmax)

    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels([str(c) for c in matrix.columns], rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels([str(y) for y in matrix.index], fontsize=9)
    ax.set_xlabel("Lookback Window (trading days)", fontsize=11)
    ax.set_ylabel("Year", fontsize=11)
    ax.set_title(
        f"Rotation Outperformance vs S&P 500 by Year  ({freq_label} rebalance)\n"
        f"Green = beats S&P  |  Red = lags S&P  |  {start} to {end}",
        fontsize=12,
    )

    for i in range(len(matrix.index)):
        for j in range(len(matrix.columns)):
            val = matrix.iloc[i, j]
            if pd.notna(val):
                ax.text(j, i, f"{float(val):+.0f}%", ha="center", va="center",
                        fontsize=7, fontweight="bold", color="black")

    plt.colorbar(im, ax=ax, label="Annualised Outperformance vs S&P (%)", shrink=0.8)
    plt.tight_layout()
    plt.savefig("economics_stability.png", dpi=150, bbox_inches="tight")
    print("Stability heatmap saved -> economics_stability.png")
    plt.show()

    # Summary: rank lookbacks by number of years they beat S&P
    win_rate = (matrix.astype(float) > 0).sum(axis=0) / matrix.astype(float).notna().sum(axis=0) * 100
    print("\n  Win rate (% of years beating S&P) by lookback:")
    print(f"  {'Window':>8}  {'Win %':>8}")
    for lb, wr in win_rate.sort_values(ascending=False).items():
        bar = "#" * int(wr / 5)
        print(f"  {lb:>8d}  {wr:>7.0f}%  {bar}")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    print("\n╔══════════════════════════════════════════════╗")
    print("║   S&P 500 vs Top Performer — Analysis Tool  ║")
    print("╚══════════════════════════════════════════════╝")

    start = get_date_input("\nAnalysis start date (YYYY-MM-DD) [default: 2020-01-01]: ", "2020-01-01")
    end   = get_date_input("Analysis end date   (YYYY-MM-DD) [default: today]:      ",
                           datetime.today().strftime("%Y-%m-%d"))

    print("\nRotation strategy settings:")
    while True:
        raw = input("  Rebalance frequency — D(aily) or W(eekly) [default: W]: ").strip().upper()
        if not raw:
            raw = "W"
        if raw in ("D", "W"):
            break
        print("  Enter D or W.")

    while True:
        lb_raw = input("  Lookback window for ranking (trading days) [default: 20]: ").strip()
        if not lb_raw:
            lookback = 20
            break
        try:
            lookback = int(lb_raw)
            if lookback > 0:
                break
            print("  Must be positive.")
        except ValueError:
            print("  Enter a whole number.")

    freq_label = "Weekly" if raw == "W" else "Daily"
    rot_label  = f"Rotation ({freq_label}, {lookback}d lookback)"

    # S&P 500
    print(f"\nDownloading S&P 500 data ({start} → {end})...")
    sp_df = yf.download("^GSPC", start=start, end=end, progress=False, auto_adjust=True)
    if sp_df.empty:
        print("ERROR: Could not download S&P 500 data.")
        return
    sp_close = get_close(sp_df, "^GSPC")

    # All stocks (one bulk request)
    prices = bulk_download(TOP_SP500, start, end)
    if not prices:
        print("ERROR: Could not download stock data.")
        return

    # Best buy-and-hold
    top_ticker, top_ret = find_top_performer(prices)
    print(f"\n  ★ Top performer (full period, hindsight): {top_ticker}  ({top_ret:+.1f}%)")
    print(f"     ⚠  This pick required knowing the future — it's an oracle benchmark, not a real strategy.")

    # Rotation simulation
    print(f"\nSimulating {rot_label}...")
    rot_series = simulate_rotation(prices, rebalance_freq=raw, lookback=lookback)

    # Normalise everything to 100
    stk_close = prices[top_ticker]
    sp_norm   = sp_close  / float(sp_close.iloc[0])  * 100
    stk_norm  = stk_close / float(stk_close.iloc[0]) * 100
    rot_norm  = rot_series.reindex(sp_norm.index, method="ffill")

    print(f"\n  S&P 500 return      : {float(sp_norm.iloc[-1])  - 100:+.1f}%")
    print(f"  {top_ticker} return           : {top_ret:+.1f}%")
    print(f"  Rotation return     : {float(rot_norm.iloc[-1]) - 100:+.1f}%")

    plot_comparison(sp_norm, stk_norm, top_ticker, rot_norm, rot_label, start, end)

    print("\nEnter an investment amount to compare all three strategies.")
    amount = get_float_input("Investment amount ($): ")
    print_results(sp_norm, stk_norm, top_ticker, rot_norm, rot_label, amount)

    # Optional lookback sweep
    run_sweep = input("\nRun lookback sweep to find the optimal window? (y/N): ").strip().lower()
    if run_sweep == "y":
        while True:
            try:
                lo_raw   = input("  Sweep from (days) [default: 5]:   ").strip()
                hi_raw   = input("  Sweep to   (days) [default: 252]: ").strip()
                step_raw = input("  Step size  (days) [default: 5]:   ").strip()
                lo   = int(lo_raw)   if lo_raw   else 5
                hi   = int(hi_raw)   if hi_raw   else 252
                step = int(step_raw) if step_raw else 5
                if lo > 0 and hi > lo and step > 0:
                    break
                print("  Check: lo > 0, hi > lo, step > 0.")
            except ValueError:
                print("  Enter whole numbers.")

        sweep_df, best_lb = sweep_lookback(prices, sp_close, rebalance_freq=raw, lo=lo, hi=hi, step=step)
        plot_sweep(sweep_df, sp_close, rebalance_freq=raw, start=start, end=end)
        print(f"\n  Best Sharpe ratio at lookback = {best_lb} trading days.")
        print(f"  Best Ann. return  at lookback = {sweep_df['annualized_return'].idxmax()} trading days.")
        print(f"  Warning: re-running the main analysis with these parameters would be in-sample overfitting.")

    # Robustness analysis
    print("\nRobustness analysis (finds an *acceptable* lookback without overfitting):")
    print("  1. Walk-Forward Optimization  — unbiased OOS equity curve")
    print("  2. Stability Heatmap          — year-by-year outperformance grid")
    print("  3. Both")
    print("  4. Skip")
    choice = input("Choice [1/2/3/4, default 4]: ").strip()

    if choice in ("1", "3"):
        print("\nWalk-Forward settings (press Enter for defaults):")
        try:
            is_raw  = input("  In-sample window  (trading days) [default: 504 = ~2yr]: ").strip()
            oos_raw = input("  Out-of-sample     (trading days) [default: 126 = ~6mo]: ").strip()
            lo_raw  = input("  Lookback range lo (trading days) [default: 5]:          ").strip()
            hi_raw  = input("  Lookback range hi (trading days) [default: 100]:        ").strip()
            st_raw  = input("  Step size         (trading days) [default: 5]:          ").strip()
            is_days  = int(is_raw)  if is_raw  else 504
            oos_days = int(oos_raw) if oos_raw else 126
            wlo      = int(lo_raw)  if lo_raw  else 5
            whi      = int(hi_raw)  if hi_raw  else 100
            wstep    = int(st_raw)  if st_raw  else 5
        except ValueError:
            print("  Bad input, using defaults.")
            is_days, oos_days, wlo, whi, wstep = 504, 126, 5, 100, 5

        wfo_curve, fold_df = walk_forward_opt(
            prices, sp_close, is_days=is_days, oos_days=oos_days,
            lo=wlo, hi=whi, step=wstep, rebalance_freq=raw,
        )
        if wfo_curve is not None:
            plot_wfo_results(wfo_curve, sp_close, fold_df, start, end)
            mode_lb = int(fold_df["best_lb"].mode().iloc[0])
            print(f"\n  Most-selected lookback across all folds: {mode_lb} days")
            print(f"  Low variance in the bar chart = the strategy isn't very sensitive to this parameter.")
            print(f"  High variance = results depend heavily on which window you pick (fragile).")

    if choice in ("2", "3"):
        print("\nStability heatmap settings (press Enter for defaults):")
        try:
            lo_raw  = input("  Lookback range lo [default: 5]:   ").strip()
            hi_raw  = input("  Lookback range hi [default: 100]: ").strip()
            st_raw  = input("  Step size         [default: 5]:   ").strip()
            hlo   = int(lo_raw) if lo_raw else 5
            hhi   = int(hi_raw) if hi_raw else 100
            hstep = int(st_raw) if st_raw else 5
        except ValueError:
            print("  Bad input, using defaults.")
            hlo, hhi, hstep = 5, 100, 5

        matrix = compute_stability_matrix(prices, sp_close, lo=hlo, hi=hhi,
                                          step=hstep, rebalance_freq=raw)
        plot_stability_heatmap(matrix, rebalance_freq=raw, start=start, end=end)


if __name__ == "__main__":
    main()
