import numpy as np
import matplotlib.pyplot as plt

# ================= USER SETTINGS =================
TOTAL_YEARS      = 20
DISCOUNT_RATE    = 0.08
UPFRONT_MACHINE1 = 1_200_000
UPFRONT_MACHINE2 = 1_200_000
RD_ANNUAL        = 3_000_000
SAVINGS_1M       = 4_200_000
SAVINGS_2M       = 5_200_000

FIGSIZE          = (9, 5.5)
DPI              = 300

FONT_AXIS_LABEL  = 16
FONT_TICK        = 14
FONT_LEGEND      = 13
FONT_ANNOT       = 13

ANNOT_COLOR      = "#4d4d4d"   # darker grey for readability
BLUE             = "#1f5fbf"
GREEN            = "#1f6f4a"
# =================================================

years = np.arange(0, TOTAL_YEARS + 1)

# ── Build annual cash flow ──────────────────────
cash_flow = np.zeros(TOTAL_YEARS + 1)

cash_flow[0] = -UPFRONT_MACHINE1

for y in range(1, 7):
    cash_flow[y] = -RD_ANNUAL

cash_flow[7] = SAVINGS_1M

for y in range(8, 10):
    cash_flow[y] = SAVINGS_1M

cash_flow[10] = SAVINGS_2M - UPFRONT_MACHINE2

for y in range(11, TOTAL_YEARS + 1):
    cash_flow[y] = SAVINGS_2M

# ── Cumulative ──────────────────────────────────
cumulative = np.cumsum(cash_flow)

# ── NPV cumulative ──────────────────────────────
discounted = np.array([cf / (1 + DISCOUNT_RATE)**y
                       for y, cf in enumerate(cash_flow)])
cumulative_npv = np.cumsum(discounted)

# ── Break-even (interpolated) ───────────────────
breakeven = None
for y in range(1, TOTAL_YEARS + 1):
    if cumulative[y - 1] < 0 and cumulative[y] >= 0:
        frac = -cumulative[y - 1] / (cumulative[y] - cumulative[y - 1])
        breakeven = (y - 1) + frac
        break

# ── Plot ────────────────────────────────────────
fig, ax = plt.subplots(figsize=FIGSIZE)

# Main curves (thicker, higher contrast)
ax.plot(years, cumulative / 1e6, color=BLUE, linewidth=3.0,
        label='Cumulative Cash Flow (Undiscounted)')
ax.plot(years, cumulative_npv / 1e6, color=GREEN, linewidth=3.0,
        linestyle='--', label=f'Cumulative NPV ({int(DISCOUNT_RATE*100)}%)')

# Zero line (strong)
ax.axhline(0, color='black', linewidth=1.8)



# Stage lines + labels (bold, darker)
ax.axvline(6, color=ANNOT_COLOR, linewidth=1.8, linestyle='--')
ax.axvline(10, color=ANNOT_COLOR, linewidth=1.8, linestyle='--')

y_top = ax.get_ylim()[1]

ax.text(6.2, y_top * 0.92, '1 Machine\nOperational',
        fontsize=FONT_ANNOT, color=ANNOT_COLOR,
        fontweight='bold', va='top')

ax.text(10.2, y_top * 0.92, '2 Machines\nOperational',
        fontsize=FONT_ANNOT, color=ANNOT_COLOR,
        fontweight='bold', va='top')

# Break-even marker
if breakeven:
    ax.axvline(breakeven, color=BLUE, linewidth=1.5, linestyle=':')
    ax.annotate(f'Break-even\nYear {breakeven:.1f}',
                xy=(breakeven, 0),
                xytext=(breakeven + 2, 4),
                fontsize=FONT_ANNOT, color=BLUE, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color=BLUE, lw=1.5))

# Final value callouts
final_val = cumulative[-1] / 1e6
final_npv = cumulative_npv[-1] / 1e6

ax.annotate(f'Year 20: ${final_val:.1f}M',
            xy=(20, final_val),
            xytext=(14, y_top * 0.85),
            fontsize=FONT_ANNOT, color=BLUE, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=BLUE, lw=1.5))

ax.annotate(f'NPV: ${final_npv:.1f}M',
            xy=(20, final_npv),
            xytext=(15, y_top * 0.4),
            fontsize=FONT_ANNOT, color=GREEN, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.5))

# Positive / negative shading
ax.fill_between(years, cumulative / 1e6, 0,
                where=(cumulative >= 0), alpha=0.08, color=BLUE)
ax.fill_between(years, cumulative / 1e6, 0,
                where=(cumulative < 0), alpha=0.08, color='red')

# Labels
ax.set_xlabel("Year", fontsize=FONT_AXIS_LABEL, fontweight='bold')
ax.set_ylabel("Cumulative Value ($M)", fontsize=FONT_AXIS_LABEL, fontweight='bold')

ax.set_xticks(np.arange(0, TOTAL_YEARS + 1, 2))

# Ticks (thicker + larger)
ax.tick_params(axis='both',
               which='major',
               labelsize=FONT_TICK,
               width=2,
               length=6,
               color='black')

# Legend (clean + visible)
ax.legend(fontsize=FONT_LEGEND,
          frameon=True,
          edgecolor='black')

# Thick black border
for spine in ax.spines.values():
    spine.set_linewidth(2.2)
    spine.set_color("black")

# Layout spacing (avoid tight_layout clipping)
plt.subplots_adjust(left=0.12, right=0.97, top=0.92, bottom=0.14)

plt.savefig("economic_impact.png", dpi=DPI, bbox_inches='tight')
plt.show()