import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── tunable parameters ──────────────────────────────────────────────────────
FIGSIZE = (9, 5.5)   # bigger figure
Y_MIN, Y_MAX = 20, 70
BAR_WIDTH = 0.6
GROUP_GAP = 0.8
TRADITIONAL_COLOR = "#6e6d67"   # slightly darker gray
LASER_COLOR = "#1f5fbf"         # darker blue for contrast
ERROR_COLOR = "black"
ERROR_CAPSIZE = 6
ERROR_LW = 2.0
DPI = 200
# ────────────────────────────────────────────────────────────────────────────

# data
traditional = {
    "labels": ["Rod weld", "Flame spray"],
    "hardness": [40, 31],
    "std": [1.4, 2.0],
}
laser = {
    "labels": ["Cu matrix\n(22 HRc)", "40 HRc\nmatrix", "60 HRc\nmatrix"],
    "hardness": [34, 47, 60],
    "std": [2.8, 0.5, 1.6],
}

# x positions
n_trad = len(traditional["labels"])
n_laser = len(laser["labels"])
x_trad = np.arange(n_trad, dtype=float)
x_laser = np.arange(n_laser, dtype=float) + n_trad + GROUP_GAP

fig, ax = plt.subplots(figsize=FIGSIZE)

# bars
ax.bar(x_trad, traditional["hardness"], width=BAR_WIDTH,
       color=TRADITIONAL_COLOR, yerr=traditional["std"],
       error_kw=dict(ecolor=ERROR_COLOR, capsize=ERROR_CAPSIZE,
                     lw=ERROR_LW, capthick=ERROR_LW),
       zorder=3)

ax.bar(x_laser, laser["hardness"], width=BAR_WIDTH,
       color=LASER_COLOR, yerr=laser["std"],
       error_kw=dict(ecolor=ERROR_COLOR, capsize=ERROR_CAPSIZE,
                     lw=ERROR_LW, capthick=ERROR_LW),
       zorder=3)

# axes
all_x = np.concatenate([x_trad, x_laser])
all_labels = traditional["labels"] + laser["labels"]
ax.set_xticks(all_x)
ax.set_xticklabels(all_labels, fontsize=14, fontweight='bold')
ax.set_ylim(Y_MIN, Y_MAX)
ax.set_ylabel("Matrix hardness (HRc)", fontsize=16, fontweight='bold')
ax.set_xlim(-0.7, x_laser[-1] + 0.7)

# REMOVE GRIDLINES
ax.grid(False)

# THICK BLACK BORDER (all spines visible)
for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_linewidth(2.5)
    spine.set_color("black")

# BOLD, LARGE TICKS
ax.tick_params(axis='both',
               which='major',
               labelsize=14,
               width=2,
               length=6,
               color='black')

# legend (bigger + bold)
legend_handles = [
    mpatches.Patch(color=TRADITIONAL_COLOR, label="Traditional Methods"),
    mpatches.Patch(color=LASER_COLOR, label="Laser Metal Deposition"),
]
ax.legend(handles=legend_handles,
          fontsize=13,
          frameon=False)

plt.tight_layout()
plt.savefig("hardness_chart.png", dpi=DPI, bbox_inches="tight")
plt.show()