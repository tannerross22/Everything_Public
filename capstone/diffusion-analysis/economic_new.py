"""
LMD Hardfacing CapEx Justification — Waterfall Chart
=====================================================
Edit the values in the INPUTS section below, then run the script.
All dollar figures are in USD.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── INPUTS (edit these) ──────────────────────────────────────────────────────

MACHINE_COST = 3000000          # CapEx: LMD machine

# Annual savings by category (positive = savings vs. current process)
LABOR_SAVINGS          =  120_000  # Reduced labor hours per year
MATERIAL_SAVINGS       =   80_000  # Improved powder yield / less waste
REWORK_SCRAP_SAVINGS   =   50_000  # Reduced scrap and rework

# Payback annotation
ANNUAL_PRODUCTION_BITS = 1_000     # Estimated bits per year (for context label)

# ── STYLE ────────────────────────────────────────────────────────────────────

CAPEX_COLOR   = "#C0392B"   # Red  — cost
SAVING_COLOR  = "#2980B9"   # Blue — savings bars
NET_COLOR     = "#1A252F"   # Dark — net position line
ANNOT_COLOR   = "#555555"
FIGSIZE       = (10, 6)
DPI           = 150

# ── CALCULATIONS ─────────────────────────────────────────────────────────────

total_annual_savings = LABOR_SAVINGS + MATERIAL_SAVINGS + REWORK_SCRAP_SAVINGS
payback_years        = MACHINE_COST / total_annual_savings

# Running balance for waterfall
categories = [
    "Machine\nCapEx",
    "Labor\nSavings\n(Yr 1)",
    "Material\nSavings\n(Yr 1)",
    "Rework /\nScrap\nSavings (Yr 1)",
    "Net Position\nEnd of Yr 1",
]

values = [
    -MACHINE_COST,
    LABOR_SAVINGS,
    MATERIAL_SAVINGS,
    REWORK_SCRAP_SAVINGS,
]

# Build running bottoms for waterfall
running = 0
bottoms = []
heights = []
colors  = []

for i, v in enumerate(values):
    if i == 0:
        bottoms.append(0)
        heights.append(v)          # negative
        colors.append(CAPEX_COLOR)
    else:
        bottoms.append(running)
        heights.append(v)
        colors.append(SAVING_COLOR)
    running += v

# Final "net" bar — full bar from 0 to running value
net_value = running
bottoms.append(min(0, net_value))
heights.append(abs(net_value))
colors.append(CAPEX_COLOR if net_value < 0 else SAVING_COLOR)

# ── PLOT ─────────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=FIGSIZE)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

x = np.arange(len(categories))
bar_width = 0.5

bars = ax.bar(x, heights, bottom=bottoms, color=colors,
              width=bar_width, edgecolor="white", linewidth=0.8, zorder=3)

# Zero line
ax.axhline(0, color="#333333", linewidth=1.0, zorder=4)

# Connector lines between waterfall bars (skip before final bar)
running_conn = 0
for i in range(len(values) - 1):
    running_conn += values[i]
    ax.plot([x[i] + bar_width / 2, x[i + 1] - bar_width / 2],
            [running_conn, running_conn],
            color="#999999", linewidth=0.8, linestyle="--", zorder=2)

# Value labels on bars
bar_totals = values + [net_value]
for i, (bar, val) in enumerate(zip(bars, bar_totals)):
    label = f"${abs(val):,.0f}"
    prefix = "−" if val < 0 else "+"
    if i == len(bar_totals) - 1:
        prefix = ""
        label = f"${val:,.0f}"
    y_pos = bar.get_y() + bar.get_height() / 2
    ax.text(bar.get_x() + bar.get_width() / 2, y_pos,
            f"{prefix}{label}", ha="center", va="center",
            fontsize=9.5, fontweight="bold", color="white", zorder=5)

# Payback annotation
ax.annotate(
    f"Payback period: ~{payback_years:.1f} years\n"
    f"(at {ANNUAL_PRODUCTION_BITS:,} bits/yr)",
    xy=(x[-1], net_value / 2),
    xytext=(x[-1] + 0.6, net_value * 0.65),
    fontsize=9, color=ANNOT_COLOR,
    arrowprops=dict(arrowstyle="->", color=ANNOT_COLOR, lw=0.8),
)

# Axes formatting
def fmt_millions(val, _):
    if abs(val) >= 1_000_000:
        return f"${val/1_000_000:.1f}M"
    elif abs(val) >= 1_000:
        return f"${val/1_000:.0f}K"
    return f"${val:.0f}"

import matplotlib.ticker as ticker
ax.yaxis.set_major_formatter(ticker.FuncFormatter(fmt_millions))
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=9.5)
ax.set_ylabel("USD", fontsize=10)
ax.set_title("LMD Hardfacing — Year 1 CapEx vs. Manufacturing Savings",
             fontsize=13, fontweight="bold", pad=14)
ax.spines[["top", "right"]].set_visible(False)
ax.yaxis.grid(True, linestyle="--", linewidth=0.5, color="#dddddd", zorder=0)
ax.set_axisbelow(True)

# Legend
legend_handles = [
    mpatches.Patch(color=CAPEX_COLOR, label="Cost / Net negative"),
    mpatches.Patch(color=SAVING_COLOR, label="Annual savings"),
]
ax.legend(handles=legend_handles, fontsize=9, frameon=False, loc="lower right")

plt.tight_layout()
plt.savefig("lmd_economic_waterfall.png", dpi=DPI, bbox_inches="tight")
print(f"Saved: lmd_economic_waterfall.png")
print(f"\nSummary:")
print(f"  Machine CapEx:          ${MACHINE_COST:>12,.0f}")
print(f"  Total annual savings:   ${total_annual_savings:>12,.0f}")
print(f"  Payback period:         {payback_years:>11.1f} yrs")
plt.show()