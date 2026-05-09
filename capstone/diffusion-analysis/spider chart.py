"""
LMD Hardfacing — Business Case Model
=====================================
All assumptions are in the INPUTS section. Edit and re-run to update.
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches
import numpy as np

# ── INPUTS ───────────────────────────────────────────────────────────────────

MACHINE_COST = 3_000_000          # CapEx: 2x LMD machines (vendor quote)

# --- Bit categories ---
BIT_SIZES = ["<12.25\"", "12.25–17.25\"", ">17.25\""]

# Annual production volume (bits/year)
BITS_PER_YEAR = {
    "<12.25\"":      800,
    "12.25–17.25\"": 400,
    ">17.25\"":      100,
}

# HF material actually needed per bit (lb) — net, before waste
HF_MATERIAL_NET = {
    "<12.25\"":      3.6,
    "12.25–17.25\"": 6.6,
    ">17.25\"":      12.5,
}

# Current (manual) labor hours per bit
CURRENT_LABOR_HRS = {
    "<12.25\"":      7.3,
    "12.25–17.25\"": 11.1,
    ">17.25\"":      12.5,
}

# --- Process parameters ---
MATERIAL_COST_PER_LB   = 75      # $/lb (HF powder)
LABOR_RATE             = 220     # $/hr

CURRENT_WASTE_FRACTION = 0.60    # 60% waste (overspray/rod waste)
LMD_WASTE_FRACTION     = 0.10    # 10% waste

CURRENT_MACHINES_PER_EE = 1      # Manual: 1 employee per machine
LMD_MACHINES_PER_EE     = 2      # Semi-attended: 1 EE runs 2 machines

CURRENT_SHIFT_UTIL = 0.50        # 50% utilization
LMD_SHIFT_UTIL     = 0.75        # 75% utilization

BIT_LIFE_IMPROVEMENT = 0.10      # 10% longer bit life → 10% fewer bits needed

# CNC programming
PROGRAMMING_LABOR_HRS_PER_BIT = 1.5
BITS_NEEDING_NEW_PROGRAMS_PER_YR = 300

# LMD deposition parameters — density-based time calculation
# Chain: mass → volume → ÷ bead cross-section → path length → ÷ rate → time
DEPOSITION_RATE_MM_PER_MIN = 1_100   # mm/min (linear travel speed)
TRACK_WIDTH_MM              = 2.5    # mm (bead width)
LAYER_THICKNESS_MM          = 1.0    # mm (Z-height per layer)
N_LAYERS                    = 2      # number of deposited layers
POWDER_DENSITY_G_CM3        = 10.34  # g/cm³ (HF powder density)

# ── CALCULATIONS ─────────────────────────────────────────────────────────────

results = {}

# Bead cross-section (mm²) — width × thickness per layer
bead_xsection_mm2 = TRACK_WIDTH_MM * LAYER_THICKNESS_MM

for size in BIT_SIZES:
    # --- Bit life: fewer bits needed under LMD ---
    bits_current = BITS_PER_YEAR[size]
    bits_lmd     = bits_current / (1 + BIT_LIFE_IMPROVEMENT)

    # --- Material cost ---
    net_lb = HF_MATERIAL_NET[size]
    gross_current = net_lb / (1 - CURRENT_WASTE_FRACTION)
    gross_lmd     = net_lb / (1 - LMD_WASTE_FRACTION)

    mat_cost_current_per_bit = gross_current * MATERIAL_COST_PER_LB
    mat_cost_lmd_per_bit     = gross_lmd     * MATERIAL_COST_PER_LB

    annual_mat_current = mat_cost_current_per_bit * bits_current
    annual_mat_lmd     = mat_cost_lmd_per_bit     * bits_lmd

    # --- LMD deposition time via density ---
    # 1. Net mass deposited (grams) — only the material that stays on the bit
    net_mass_g = net_lb * 453.592                             # g
    # 2. Deposited volume (mm³) — 1 cm³ = 1000 mm³
    volume_mm3 = (net_mass_g / POWDER_DENSITY_G_CM3) * 1000
    # 3. Path length: volume spread over N_LAYERS bead cross-sections
    #    Each layer lays down bead_xsection_mm2 per mm of travel
    #    Total path = volume / (bead_xsection × N_LAYERS) would double-count;
    #    correct: total volume = path_length × bead_xsection_mm2 (layers already
    #    captured in the net volume deposited)
    path_length_mm = volume_mm3 / bead_xsection_mm2
    # 4. Time at travel speed
    deposition_time_hrs = path_length_mm / (DEPOSITION_RATE_MM_PER_MIN * 60)
    # 5. Labor: 1 EE attends LMD_MACHINES_PER_EE machines simultaneously
    lmd_labor_hrs_per_bit = deposition_time_hrs / LMD_MACHINES_PER_EE

    current_labor_hrs = CURRENT_LABOR_HRS[size]
    labor_cost_current_per_bit = current_labor_hrs              * LABOR_RATE
    labor_cost_lmd_per_bit     = lmd_labor_hrs_per_bit          * LABOR_RATE

    annual_labor_current = labor_cost_current_per_bit * bits_current
    annual_labor_lmd     = labor_cost_lmd_per_bit     * bits_lmd

    results[size] = {
        "bits_current":          bits_current,
        "bits_lmd":              bits_lmd,
        "mat_current":           annual_mat_current,
        "mat_lmd":               annual_mat_lmd,
        "labor_current":         annual_labor_current,
        "labor_lmd":             annual_labor_lmd,
        "lmd_labor_hrs_per_bit": lmd_labor_hrs_per_bit,
        "deposition_time_hrs":   deposition_time_hrs,
        "path_length_mm":        path_length_mm,
        "volume_mm3":            volume_mm3,
    }

# --- Programming cost (one-time amortized over year) ---
annual_programming_cost = PROGRAMMING_LABOR_HRS_PER_BIT * BITS_NEEDING_NEW_PROGRAMS_PER_YR * LABOR_RATE

# --- Aggregate savings ---
total_mat_current   = sum(r["mat_current"]   for r in results.values())
total_mat_lmd       = sum(r["mat_lmd"]       for r in results.values())
total_labor_current = sum(r["labor_current"] for r in results.values())
total_labor_lmd     = sum(r["labor_lmd"]     for r in results.values())

# Bit life saving: bits NOT produced × average current total cost per bit
# (material + labor under current process, weighted)
life_saving = 0
for size, r in results.items():
    bits_avoided = r["bits_current"] - r["bits_lmd"]
    cost_per_bit_current = (r["mat_current"] + r["labor_current"]) / r["bits_current"]
    life_saving += bits_avoided * cost_per_bit_current

material_saving    = total_mat_current   - total_mat_lmd
labor_saving       = total_labor_current - total_labor_lmd
programming_cost   = annual_programming_cost   # this is a new cost (negative saving)

total_annual_saving = material_saving + labor_saving + life_saving - programming_cost
payback_years = MACHINE_COST / total_annual_saving

# ── PRINT SUMMARY ────────────────────────────────────────────────────────────

print("=" * 70)
print("  LMD HARDFACING — BUSINESS CASE SUMMARY")
print("=" * 70)
print(f"\n  Bead cross-section: {bead_xsection_mm2:.2f} mm²  "
      f"(width {TRACK_WIDTH_MM}mm × thickness {LAYER_THICKNESS_MM}mm)")
print(f"  Density: {POWDER_DENSITY_G_CM3} g/cm³  |  Layers: {N_LAYERS}  |  Rate: {DEPOSITION_RATE_MM_PER_MIN} mm/min\n")
print(f"{'Bit Size':<18} {'Net lb':>7} {'Vol (cm³)':>10} {'Dep Time(hr)':>13} {'LMD Labor(hr)':>14} {'Cur Bits':>9} {'LMD Bits':>9}")
print(f"  {'-'*82}")
for size, r in results.items():
    net_lb   = HF_MATERIAL_NET[size]
    vol_cm3  = (net_lb * 453.592) / POWDER_DENSITY_G_CM3
    print(f"  {size:<16} {net_lb:>7.1f} {vol_cm3:>10.2f} {r['deposition_time_hrs']:>13.3f} "
          f"{r['lmd_labor_hrs_per_bit']:>14.3f} {r['bits_current']:>9,.0f} {r['bits_lmd']:>9,.1f}")
print(f"\n  Material Savings/yr:     ${material_saving:>12,.0f}")
print(f"  Labor Savings/yr:        ${labor_saving:>12,.0f}")
print(f"  Bit Life Savings/yr:     ${life_saving:>12,.0f}")
print(f"  Programming Cost/yr:    (${programming_cost:>11,.0f})")
print(f"  {'─'*48}")
print(f"  NET Annual Savings:      ${total_annual_saving:>12,.0f}")
print(f"\n  Machine CapEx (2x):     (${MACHINE_COST:>11,.0f})")
print(f"  Payback Period:          {payback_years:>11.1f} yrs")
print("=" * 70)

# ── WATERFALL CHART ───────────────────────────────────────────────────────────

CAPEX_COLOR   = "#C0392B"
SAVING_COLOR  = "#2980B9"
COST_COLOR    = "#E67E22"
NET_COLOR     = "#1A5276"

labels = [
    "Machine\nCapEx",
    "Material\nSavings",
    "Labor\nSavings",
    "Bit Life\nSavings",
    "Programming\nCost",
    "Net Position\n(Yr 1)",
]

deltas = [
    -MACHINE_COST,
    material_saving,
    labor_saving,
    life_saving,
    -programming_cost,
]

# Build waterfall bottoms
running = 0
bottoms, heights, colors = [], [], []
for i, d in enumerate(deltas):
    if i == 0:
        bottoms.append(0)
        heights.append(d)
        colors.append(CAPEX_COLOR)
    elif d < 0:
        bottoms.append(running + d)
        heights.append(abs(d))
        colors.append(COST_COLOR)
    else:
        bottoms.append(running)
        heights.append(d)
        colors.append(SAVING_COLOR)
    running += d

# Net position bar
net = running
bottoms.append(min(0, net))
heights.append(abs(net))
colors.append(NET_COLOR)

fig, ax = plt.subplots(figsize=(8, 5))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

x = np.arange(len(labels))
bar_width = 0.72
bars = ax.bar(x, heights, bottom=bottoms, color=colors,
              width=bar_width, edgecolor="white", linewidth=0.8, zorder=3)

# Zero line only
ax.axhline(0, color="#333333", linewidth=1.5, zorder=4)

# Connector lines
conn = 0
for i in range(len(deltas) - 1):
    conn += deltas[i]
    ax.plot([x[i] + bar_width/2, x[i+1] - bar_width/2], [conn, conn],
            color="#aaaaaa", linewidth=1.0, linestyle="--", zorder=2)

# Value labels inside bars — $M format
all_deltas = deltas + [net]
for i, (bar, val) in enumerate(zip(bars, all_deltas)):
    prefix = "−$" if val < 0 else "+$"
    if i == len(all_deltas) - 1:
        prefix = "$"
    label = f"{prefix}{abs(val)/1_000_000:.2f}M"
    y_center = bar.get_y() + bar.get_height() / 2
    ax.text(bar.get_x() + bar.get_width() / 2, y_center,
            label, ha="center", va="center",
            fontsize=11, fontweight="bold", color="white", zorder=5)

# Payback annotation
ax.annotate(
    f"Payback: ~{payback_years:.1f} yrs",
    xy=(x[-1], net / 2),
    xytext=(x[-1] - 1.0, net * 0.72),
    fontsize=11, color="#333333",
    arrowprops=dict(arrowstyle="->", color="#555555", lw=1.0),
)

# Y-axis $M formatting
def fmt(val, _):
    return f"${val/1_000_000:.1f}M"

ax.yaxis.set_major_formatter(ticker.FuncFormatter(fmt))
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=11, fontweight="bold")
ax.set_ylabel("USD", fontsize=12, fontweight="bold")
for label in ax.get_yticklabels():
    label.set_fontweight("bold")
    label.set_fontsize(11)

# Closed border
for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_linewidth(1.2)
    spine.set_color("#333333")

# No gridlines
ax.yaxis.grid(False)
ax.xaxis.grid(False)

# Tighten x margins so bars fill the space
ax.set_xlim(-0.6, len(labels) - 0.4)

legend_handles = [
    mpatches.Patch(color=CAPEX_COLOR,  label="Capital cost"),
    mpatches.Patch(color=SAVING_COLOR, label="Savings"),
    mpatches.Patch(color=COST_COLOR,   label="New cost"),
    mpatches.Patch(color=NET_COLOR,    label="Net position"),
]
ax.legend(handles=legend_handles, fontsize=12, frameon=True,
          framealpha=0.9, edgecolor="#cccccc", loc="lower right")

plt.tight_layout()
out = "lmd_economic_waterfall.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
print(f"\nChart saved: {out}  (same folder as this script)")
plt.show()