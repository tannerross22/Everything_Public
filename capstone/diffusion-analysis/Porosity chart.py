import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# ================= USER SETTINGS =================
doe2_porosity   = [0.0343, 0.1330, 0.1866, 0.6086,
                   0.1534, 0.2788, 0.1954, 0.2794]
rod_porosity    = [5.305918182]
spray_porosity  = [3.581181818]

doe2_std_porosity  = [0, 0.0608, 0.1699, 0.1389,
                      0.1206, 0.2169, 0.1689, 0.1873]
rod_std_porosity   = [3.899975966]
spray_std_porosity = [0.9521285437]

doe2_thickness  = [136.1/1000,
46.5/1000,
121.8/1000,
59.0/1000,
186.8/1000,
64.8/1000,
65.0/1000,
37.3/1000]
rod_thickness   = [.296]
spray_thickness = [0.21]

#doe2_std_thickness  = [0.02868484921, 0.01581742622, 0.0337562242, 0.01433415346,
                       #0.04181759464, 0.07357007796, 0.02006360402, 0.01222237397]
#rod_std_thickness   = [0.160]
#spray_std_thickness = [0.045]


doe2_std_thickness  = [0,0,0,0,0,0,0,0]
rod_std_thickness   = [0]
spray_std_thickness = [0]
# ── Font sizes (bumped up for poster) ──
FONT_AXIS_LABEL  = 16
FONT_TICK        = 13
FONT_LEGEND      = 12
FONT_TARGET      = 13   # larger target line labels

GROUP_GAP        = 0.5
BAR_WIDTH        = 0.22
TARGET_POROSITY  = 1.0
TARGET_THICKNESS = 0.4
# =================================================

n_doe2 = len(doe2_porosity)
n_base = 2

x_centers = np.arange(n_doe2, dtype=float)
# x_centers = np.concatenate([
#     np.arange(n_doe2, dtype=float),
#     np.arange(n_base, dtype=float) + n_doe2 + GROUP_GAP
# ])

all_porosity  = doe2_porosity  # + rod_porosity  + spray_porosity
all_por_err   = doe2_std_porosity # + rod_std_porosity + spray_std_porosity
all_thickness = doe2_thickness # + rod_thickness + spray_thickness
all_thk_err   = doe2_std_thickness # + rod_std_thickness + spray_std_thickness

all_pt_colors = ['#2a7a4a'] * (n_doe2 + n_base)

all_labels = [str(i) for i in range(1, 9)] # + ['Rod', 'Spray']

# ── Figure (wider for poster legibility) ──
fig, ax1 = plt.subplots(figsize=(7.5, 4.5))
ax2 = ax1.twinx()

# --- Porosity bars ---
ax1.bar(x_centers, all_porosity,
        width=BAR_WIDTH, yerr=all_por_err, capsize=4,
        color=['#378ADD'] * n_doe2, # + ['#888888'] * n_base,
        edgecolor='black', linewidth=0.9,
        error_kw=dict(elinewidth=1.2, ecolor='black'),
        zorder=3)

# --- Thickness variation points ---
for x, y, err, c in zip(x_centers, all_thickness, all_thk_err, all_pt_colors):
    ax2.errorbar(x, y, yerr=err,
                 fmt='D', color=c, markeredgecolor='black',
                 markeredgewidth=0.9, markersize=7,
                 capsize=4, elinewidth=1.2, ecolor=c,
                 zorder=5)

# --- Target lines ---
#ax1.axhline(TARGET_POROSITY, color='#378ADD', linewidth=1.4, linestyle='--', zorder=4)

#ax2.axhline(TARGET_THICKNESS, color='#2a7a4a', linewidth=1.4, linestyle='--', zorder=4)
#ax2.text(x_centers[1] + 3, TARGET_THICKNESS - 0.01, 'Target Variation',
         #va='top', ha='left', fontsize=FONT_TARGET, color='#2a7a4a', fontweight='bold')

# --- Axes formatting ---
ax1.set_xticks(x_centers)
ax1.set_ylim(0,1)
ax1.set_xticklabels(all_labels, fontsize=FONT_TICK)
ax1.set_xlabel("Sample Number", fontsize=FONT_AXIS_LABEL, labelpad=8)
ax1.set_ylabel("Porosity (%)", fontsize=FONT_AXIS_LABEL, color='#378ADD')
ax1.tick_params(axis='y', labelsize=FONT_TICK, colors='#378ADD')
ax1.tick_params(axis='x', labelsize=FONT_TICK)

ax2.set_ylabel("Thickness Variation (mm)", fontsize=FONT_AXIS_LABEL, color='#2a7a4a')
ax2.tick_params(axis='y', labelsize=FONT_TICK, colors='#2a7a4a')
ax2.set_ylim(0,0.4)

# --- Group separator ---
# sep_x = (x_centers[n_doe2 - 1] + x_centers[n_doe2]) / 2
# ax1.axvline(sep_x, color='black', linewidth=0.9, linestyle='--', alpha=0.4)

# --- Spine thickness (makes it crisper when shrunk) ---
for spine in ax1.spines.values():
    spine.set_linewidth(1.2)

# --- Legend ---
legend_elements = [
    Patch(facecolor='#378ADD', edgecolor='black', label='DOE 2 — Porosity'),
    # Patch(facecolor='#888888', edgecolor='black', label='Baseline — Porosity'),
    Line2D([0], [0], marker='D', color='w', markerfacecolor='#2a7a4a',
           markeredgecolor='black', markersize=8, label='DOE 2 — Thickness Variation'),
]
ax1.legend(handles=legend_elements, fontsize=FONT_LEGEND, loc='upper left', framealpha=1.0, edgecolor='black', facecolor='white')

plt.tight_layout()
plt.savefig("poster_chart.png", dpi=800, bbox_inches='tight')
plt.show()