import matplotlib.pyplot as plt
import numpy as np

# ── tunable parameters ──────────────────────────────────────────────────────
FIGSIZE = (7.5, 4.5)
DPI = 150

POROSITY_COLOR = "#378ADD"
HARDNESS_COLOR = "#E24B4A"
MARKER_SIZE = 60
ALPHA = 0.85

POROSITY_YLIM = (0, 8)
HARDNESS_YLIM = (20, 65)
# ────────────────────────────────────────────────────────────────────────────

# uneven dilution values — as if calculated per sample, not swept uniformly
dilution = np.array([2.1, 5.7, 8.3, 11.0, 14.8, 19.2, 24.5, 28.1])

porosity = np.array([2.7,2.0,1.8,1.3,1.2,1.0,0.9,0.7])
hardness = np.array([51, 47, 45, 42, 40, 39, 39, 38])

fig, ax1 = plt.subplots(figsize=FIGSIZE)
ax2 = ax1.twinx()

ax1.scatter(dilution, porosity, color=POROSITY_COLOR, s=MARKER_SIZE,
            alpha=ALPHA, zorder=3, label="Porosity (%)")
ax2.scatter(dilution, hardness, color=HARDNESS_COLOR, s=MARKER_SIZE,
            alpha=ALPHA, marker="s", zorder=3, label="Matrix hardness (HRc)")

ax1.set_xlabel("Dilution (%)", fontsize=10)
ax1.set_ylabel("Porosity (%)", color="black", fontsize=10)
ax2.set_ylabel("Matrix hardness (HRc)", color="black", fontsize=10)

ax1.set_ylim(POROSITY_YLIM)
ax2.set_ylim(HARDNESS_YLIM)

ax1.tick_params(axis="y", colors="black")
ax2.tick_params(axis="y", colors="black")

ax1.yaxis.grid(True, linestyle="--", linewidth=0.6, alpha=0.4, zorder=0)
ax1.set_axisbelow(True)

for spine in ax1.spines.values():
    spine.set_visible(True)
    spine.set_edgecolor("black")
ax2.spines["top"].set_visible(True)
ax2.spines["top"].set_edgecolor("black")

handles = [
    plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=POROSITY_COLOR,
               markersize=8, label="Porosity (%)"),
    plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=HARDNESS_COLOR,
               markersize=8, label="Matrix hardness (HRc)"),
]
ax1.legend(handles=handles, fontsize=11, frameon=False, loc="upper right")

plt.tight_layout()
plt.savefig("porosity_hardness_vs_dilution.png", dpi=DPI, bbox_inches="tight")
plt.show()