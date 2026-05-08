"""
Bimodal Powder Packing Optimizer
=================================
Furnas model + Brouwers (2006) analytical correction for finite size ratios.

Designed for: WOKA 50512 (large WC-Co pellets) + small spherical WC particles
Reference:    Brouwers, H.J.H. (2006). Particle-size distribution and packing
              fraction of geometric random packings. Physical Review E, 74(3).

Edit the INPUTS section and re-run. All other sections are automatic.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

# ── INPUTS ────────────────────────────────────────────────────────────────────

# Large particles (WOKA 50512)
D_L_MIN_UM      = 125       # µm — lower sieve limit
D_L_MAX_UM      = 250       # µm — upper sieve limit
RHO_LARGE       = 14.75      # g/cm³ — WC-6Co sintered density

# Small particles (your new 15–45 µm spherical WC)
D_S_MIN_UM      = 15        # µm — lower sieve limit
D_S_MAX_UM      = 45        # µm — upper sieve limit
RHO_SMALL       = 16.5      # g/cm³ — update to your actual particle density
                             # (pure WC ≈ 15.7, WC-Co ≈ 14.5, WC-W2C ≈ 10.8)

# Monosize random close packing fraction (0.64 for spheres)
PHI_MONO        = 0.64

# ── MODEL ─────────────────────────────────────────────────────────────────────

def brouwers_void(u: float, c_L: float, phi_mono: float = PHI_MONO) -> float:
    """
    Bimodal void fraction via Brouwers (2006) Redlich-Kister-Smoker equation.

    Parameters
    ----------
    u       : size ratio d_L / d_S  (must be >= 1.0)
    c_L     : volume fraction of large particles in the TOTAL MIX (0–1)
    phi_mono: monosize random close packing fraction

    Returns
    -------
    h : void fraction (1 – packing fraction)
    """
    beta  = 0.125                      # Fitted from Furnas RCP data
    m     = -0.08 * u ** (-1.7)        # Size-ratio-dependent asymmetry term
    h0    = 1.0 - phi_mono             # Monosize void fraction
    c_S   = 1.0 - c_L
    h     = h0 * (1.0 - 4.0 * beta * (1.0 - 1.0 / u)
                  * c_L * c_S * (1.0 + m * (1.0 - 2.0 * c_L)))
    return float(np.clip(h, 0.0, 1.0))


def furnas_ideal(phi_mono: float = PHI_MONO):
    """
    Furnas infinite-asymmetry limit (u → ∞).
    Returns (phi_max, c_L_optimal, c_S_optimal).
    """
    phi_max = phi_mono + (1.0 - phi_mono) * phi_mono
    c_L_opt = phi_mono / phi_max
    return phi_max, c_L_opt, 1.0 - c_L_opt


# ── CALCULATIONS ──────────────────────────────────────────────────────────────

d_L = (D_L_MIN_UM + D_L_MAX_UM) / 2.0
d_S = (D_S_MIN_UM + D_S_MAX_UM) / 2.0
u   = d_L / d_S

C_L = np.linspace(0.001, 0.999, 10_000)
phi_curve = 1.0 - np.array([brouwers_void(u, c) for c in C_L])

idx_opt   = int(np.argmax(phi_curve))
c_L_opt   = float(C_L[idx_opt])
c_S_opt   = 1.0 - c_L_opt
phi_max   = float(phi_curve[idx_opt])
phi_gain  = phi_max - PHI_MONO

# Convert optimal volume fractions → weight fractions
mass_L = c_L_opt * RHO_LARGE
mass_S = c_S_opt * RHO_SMALL
wt_L   = mass_L / (mass_L + mass_S)
wt_S   = mass_S / (mass_L + mass_S)

phi_furnas, c_L_furnas, c_S_furnas = furnas_ideal()

# Size-ratio sensitivity sweep
u_sweep    = np.linspace(1.01, 15.0, 400)
phi_sweep  = []
cL_sweep   = []
for u_s in u_sweep:
    phi_s = 1.0 - np.array([brouwers_void(u_s, c) for c in C_L])
    idx_s = int(np.argmax(phi_s))
    phi_sweep.append(float(phi_s[idx_s]))
    cL_sweep.append(float(C_L[idx_s]))

# ── CONSOLE SUMMARY ───────────────────────────────────────────────────────────

W = 68
print("=" * W)
print("  BIMODAL PACKING OPTIMIZER — RESULTS")
print("=" * W)
print(f"\n  Large particles:  {D_L_MIN_UM}–{D_L_MAX_UM} µm  →  median {d_L:.0f} µm  |  ρ = {RHO_LARGE} g/cm³")
print(f"  Small particles:  {D_S_MIN_UM}–{D_S_MAX_UM} µm  →  median {d_S:.0f} µm  |  ρ = {RHO_SMALL} g/cm³")
print(f"  Size ratio u:     {u:.2f}")

# Size ratio interpretation
if u >= 5.75:
    regime = "✓ FULL Furnas decoupling regime — small particles fit freely in voids"
elif u >= 3.5:
    regime = "✓ GOOD — near-Furnas, small particles mostly fit in interstices"
elif u >= 2.4:
    regime = "⚠  MARGINAL — some interaction between size classes"
else:
    regime = "✗ POOR — particles too similar in size, minimal packing benefit"
print(f"  Regime:           {regime}")

print(f"\n  {'─'*62}")
print(f"  Monosize RCP baseline:      φ = {PHI_MONO:.4f}  ({PHI_MONO*100:.2f}%)")
print(f"  Brouwers optimum (u={u:.1f}):  φ = {phi_max:.4f}  ({phi_max*100:.2f}%)")
print(f"  Furnas ideal (u → ∞):       φ = {phi_furnas:.4f}  ({phi_furnas*100:.2f}%)")
print(f"  Packing gain vs monosize:  Δφ = +{phi_gain:.4f}  (+{phi_gain*100:.2f}%)")
print(f"  {'─'*62}")

print(f"\n  OPTIMAL BLEND (carbide mix, NiCr added separately):")
print(f"  {'Component':<35} {'Vol %':>8} {'Wt %':>8}")
print(f"  {'─'*52}")
print(f"  {'Large — WOKA 50512 ('+str(D_L_MIN_UM)+'–'+str(D_L_MAX_UM)+' µm)':<35} {c_L_opt*100:>7.1f}% {wt_L*100:>7.1f}%")
print(f"  {'Small — spherical WC ('+str(D_S_MIN_UM)+'–'+str(D_S_MAX_UM)+' µm)':<35} {c_S_opt*100:>7.1f}% {wt_S*100:>7.1f}%")
print(f"  {'─'*52}")
print(f"  Predicted packing fraction: {phi_max*100:.2f}%")

print(f"\n  Furnas ideal composition (reference):")
print(f"    Large: {c_L_furnas*100:.1f} vol%   Small: {c_S_furnas*100:.1f} vol%")
print(f"    (Converges to this as u → ∞; your u={u:.1f} is {'close' if u>5 else 'approaching'})")

print(f"\n{'=' * W}")

# ── PLOT ──────────────────────────────────────────────────────────────────────

COLORS = {
    "large":    "#2980B9",
    "small":    "#E67E22",
    "optimal":  "#27AE60",
    "furnas":   "#8E44AD",
    "mono":     "#95A5A6",
    "sweep":    "#2C3E50",
    "cL_line":  "#C0392B",
}

fig = plt.figure(figsize=(14, 6))
fig.patch.set_facecolor("white")
gs  = GridSpec(1, 2, figure=fig, wspace=0.38)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])

# ── LEFT: φ vs c_L ────────────────────────────────────────────────────────────
ax1.set_facecolor("white")

# Monosize baseline
ax1.axhline(PHI_MONO, color=COLORS["mono"], lw=1.2, ls="--",
            label=f"Monosize RCP ({PHI_MONO:.2f})")

# Furnas ideal limit
ax1.axhline(phi_furnas, color=COLORS["furnas"], lw=1.2, ls=":",
            label=f"Furnas ideal limit ({phi_furnas:.3f})")

# Brouwers curve for your particles
ax1.plot(C_L * 100, phi_curve, color=COLORS["large"], lw=2.8,
         label=f"Brouwers model  u = {u:.1f}")

# Optimal point
ax1.plot(c_L_opt * 100, phi_max, "o", color=COLORS["optimal"], ms=11, zorder=6,
         label=f"Optimum: φ = {phi_max:.4f}\nc_L = {c_L_opt*100:.0f} vol%  |  {wt_L*100:.0f} wt%")

# Shaded gain region
ax1.fill_between(C_L * 100, PHI_MONO, phi_curve,
                 where=(phi_curve > PHI_MONO),
                 alpha=0.12, color=COLORS["large"], label="Packing gain region")

# Annotation
ax1.annotate(
    f"+{phi_gain*100:.2f}% gain\n({phi_max*100:.2f}% vs {PHI_MONO*100:.1f}%)",
    xy=(c_L_opt * 100, phi_max),
    xytext=(c_L_opt * 100 + 12, phi_max - 0.005),
    fontsize=9, color=COLORS["optimal"], fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=COLORS["optimal"], lw=1.0),
)

ax1.set_xlabel("Vol% of large particles  (c_L)", fontsize=11, fontweight="bold")
ax1.set_ylabel("Packing fraction  φ", fontsize=11, fontweight="bold")
ax1.set_title(
    f"Packing Fraction vs Blend Composition\n"
    f"WOKA 50512 ({D_L_MIN_UM}–{D_L_MAX_UM} µm)  +  spherical WC ({D_S_MIN_UM}–{D_S_MAX_UM} µm)",
    fontsize=10.5, fontweight="bold"
)
ax1.legend(fontsize=8.5, frameon=True, framealpha=0.92, loc="upper left")
ax1.set_xlim(0, 100)
ax1.set_ylim(PHI_MONO - 0.01, phi_furnas + 0.04)
ax1.grid(True, ls="--", lw=0.5, color="#e0e0e0")
for sp in ax1.spines.values():
    sp.set_linewidth(1.0); sp.set_color("#555")

# ── RIGHT: Max φ and optimal c_L vs size ratio ────────────────────────────────
ax2.set_facecolor("white")
ax2b = ax2.twinx()

ax2.plot(u_sweep, phi_sweep, color=COLORS["sweep"], lw=2.5,
         label="φ_max (packing fraction)")
ax2b.plot(u_sweep, [c * 100 for c in cL_sweep], color=COLORS["cL_line"],
          lw=1.8, ls="--", label="Optimal large-particle vol%")

# Your actual case
idx_u = int(np.argmin(np.abs(u_sweep - u)))
ax2.plot(u, phi_sweep[idx_u], "o", color=COLORS["optimal"], ms=11, zorder=6,
         label=f"Your case: u={u:.1f},  φ={phi_sweep[idx_u]:.4f}")

# Furnas limit line
ax2.axhline(phi_furnas, color=COLORS["furnas"], lw=1.0, ls=":",
            label=f"Furnas limit ({phi_furnas:.3f})")
ax2.axhline(PHI_MONO,   color=COLORS["mono"],   lw=1.0, ls="--")
ax2.text(13.5, PHI_MONO + 0.001, "monosize", fontsize=8, color=COLORS["mono"], ha="right")

# Threshold verticals
thresholds = [
    (2.4,  "BCC threshold",       "#F39C12"),
    (3.5,  "RCP interstice",      "#27AE60"),
    (5.75, "Sub-jamming / Furnas","#8E44AD"),
]
for u_t, lbl, col in thresholds:
    ax2.axvline(u_t, color=col, lw=1.0, ls="--", alpha=0.6)
    ax2.text(u_t + 0.15, PHI_MONO + 0.003, lbl, rotation=90,
             color=col, fontsize=7.5, va="bottom")

# Shade "your regime"
ax2.axvspan(u - 0.5, u + 0.5, alpha=0.08, color=COLORS["optimal"])

ax2.set_xlabel("Size ratio  u = d_L / d_S", fontsize=11, fontweight="bold")
ax2.set_ylabel("Maximum packing fraction  φ", fontsize=11, fontweight="bold")
ax2b.set_ylabel("Optimal large-particle vol%", fontsize=10,
                color=COLORS["cL_line"], fontweight="bold")
ax2b.tick_params(colors=COLORS["cL_line"])
ax2.set_title(
    "Max Packing & Optimal Composition vs Size Ratio\n(Brouwers model, optimal c_L at each u)",
    fontsize=10.5, fontweight="bold"
)

lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2b.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, fontsize=8.5, frameon=True, loc="lower right")
ax2.set_xlim(1, 15)
ax2.set_ylim(PHI_MONO - 0.005, phi_furnas + 0.04)
ax2.grid(True, ls="--", lw=0.5, color="#e0e0e0")
for sp in ax2.spines.values():
    sp.set_linewidth(1.0); sp.set_color("#555")

plt.suptitle(
    "Bimodal Packing Optimization — WOKA 50512 + Spherical WC Fines\n"
    "Brouwers (2006) model  |  NiCr matrix treated separately as volumetric spacer",
    fontsize=12, fontweight="bold", y=1.02
)
plt.tight_layout()

out = "bimodal_packing_result.png"
plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
print(f"\nChart saved: {out}")
plt.show()