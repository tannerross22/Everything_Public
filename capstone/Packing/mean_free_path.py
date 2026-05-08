import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import warnings

warnings.filterwarnings("ignore")

# ── INPUTS ────────────────────────────────────────────────────────────────────
RHO_MATRIX = 8.5
RHO_LARGE = 14.9
RHO_SMALL = 16.5

D_LARGE_MEAN = 188.0
D_SMALL_MEAN = 30.0

WT_LARGE_MIN = 0.01
WT_LARGE_MAX = 0.94
WT_SMALL_MIN = 0.00
WT_SMALL_MAX = 0.50
N_GRID = 300

WT_MATRIX_MIN = 0.05
PHI_MAX = 0.907

ALPHA = 0.7
CONSTRAINED_MATRIX_WT = 0.40

CURRENT_WT_LARGE = 0.42
CURRENT_WT_SMALL = 0.18

BG_COLOR = "white"
PANEL_BG = "#2A2A2A"
TEXT_COLOR = "black"
AXIS_COLOR = "white"
GRID_COLOR = "#3A3A3A"
MARKER_CURRENT = "#00BFFF"
MARKER_OPTIMAL = "#FF4444"
MARKER_CONSTRAINED = "#FFD700"  # Yellow Gold
DPI = 150

R_LARGE = D_LARGE_MEAN / 2.0
R_SMALL = D_SMALL_MEAN / 2.0


# ── MATH (Surface Area Method) ───────────────────────────────────────────────

def wt_to_vol3(wm, wl, ws):
    a, b, c = wm / RHO_MATRIX, wl / RHO_LARGE, ws / RHO_SMALL
    t = a + b + c
    return a / t, b / t, c / t


def mfp_large(phi_l):
    if phi_l <= 1e-9: return np.nan
    sv_l = (3.0 * phi_l) / R_LARGE
    return (4.0 * (1.0 - phi_l)) / sv_l


def mfp_all(phi_l, phi_s):
    phi_t = phi_l + phi_s
    if phi_t <= 1e-9 or phi_t >= 1.0: return np.nan
    sv_l = (3.0 * phi_l) / R_LARGE
    sv_s = (3.0 * phi_s) / R_SMALL
    sv_total = sv_l + sv_s
    return (4.0 * (1.0 - phi_t)) / sv_total


# ── SCAN & OPTIMIZATION ──────────────────────────────────────────────────────

def run_scan():
    wl_vals = np.linspace(WT_LARGE_MIN, WT_LARGE_MAX, N_GRID)
    ws_vals = np.linspace(WT_SMALL_MIN, WT_SMALL_MAX, N_GRID)
    shape = (N_GRID, N_GRID)
    MFP_L, MFP_A = np.full(shape, np.nan), np.full(shape, np.nan)
    FEASIBLE = np.zeros(shape, dtype=bool)
    WM_GRID, PHI_L, PHI_S = np.full(shape, np.nan), np.full(shape, np.nan), np.full(shape, np.nan)

    for i, ws in enumerate(ws_vals):
        for j, wl in enumerate(wl_vals):
            wm = 1.0 - wl - ws
            if wm < WT_MATRIX_MIN: continue
            vm, vl, vs = wt_to_vol3(wm, wl, ws)
            if vl + vs > PHI_MAX or vl <= 0: continue
            FEASIBLE[i, j], WM_GRID[i, j] = True, wm
            PHI_L[i, j], PHI_S[i, j] = vl, vs
            MFP_L[i, j], MFP_A[i, j] = mfp_large(vl), mfp_all(vl, vs)
    return wl_vals, ws_vals, MFP_L, MFP_A, FEASIBLE, WM_GRID, PHI_L, PHI_S


def compute_score(MFP_L, MFP_A, feasible, alpha, phi_l, phi_s):
    eps = 1e-9
    phi_void = np.where(feasible, np.maximum(1.0 - phi_l - phi_s, eps), np.nan)
    f1 = np.where(feasible, phi_l, np.nan)
    f2 = np.where(feasible, phi_s / phi_void, np.nan)
    f1_norm = (f1 - np.nanmin(f1)) / max(np.nanmax(f1) - np.nanmin(f1), eps)
    f2_norm = (f2 - np.nanmin(f2)) / max(np.nanmax(f2) - np.nanmin(f2), eps)
    score = (f1_norm + eps) ** alpha * (f2_norm + eps) ** (1.0 - alpha)
    return np.where(feasible, score, np.nan)


def constrained_optimum(wt_matrix_fixed, alpha, n=2000):
    wl_arr = np.linspace(0.001, 1.0 - wt_matrix_fixed - 0.001, n)
    rows = []
    for wl in wl_arr:
        ws = 1.0 - wt_matrix_fixed - wl
        vm, vl, vs = wt_to_vol3(wt_matrix_fixed, wl, ws)
        if vl + vs > PHI_MAX or vl <= 0: continue
        rows.append((wl, ws, vl, vs, max(1. - vl - vs, 1e-9), mfp_large(vl), mfp_all(vl, vs)))
    if not rows: return None
    arr = np.array(rows)
    f1, f2 = arr[:, 2], arr[:, 3] / arr[:, 4]
    f1_n = (f1 - f1.min()) / max(f1.max() - f1.min(), 1e-9)
    f2_n = (f2 - f2.min()) / max(f2.max() - f2.min(), 1e-9)
    scores = (f1_n + 1e-9) ** alpha * (f2_n + 1e-9) ** (1 - alpha)
    b = np.argmax(scores)
    return {"wt_large": arr[b, 0], "wt_small": arr[b, 1], "wt_matrix": wt_matrix_fixed,
            "mfp_large": arr[b, 5], "mfp_all": arr[b, 6], "score": scores[b],
            "p_wl": arr[:, 0], "p_score": scores, "p_mfp_l": arr[:, 5], "p_mfp_a": arr[:, 6]}


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    wl_v, ws_v, MFP_L, MFP_A, FEAS, WM_G, PHI_L, PHI_S = run_scan()
    SCORE = compute_score(MFP_L, MFP_A, FEAS, ALPHA, PHI_L, PHI_S)

    # Global Optimum Analysis
    score_idx = np.unravel_index(np.nanargmax(np.where(FEAS, SCORE, -np.inf)), SCORE.shape)
    g_wl, g_ws, g_score = wl_v[score_idx[1]], ws_v[score_idx[0]], SCORE[score_idx]
    g_wm = 1.0 - g_wl - g_ws
    g_carbide_ratio = g_wl / (g_wl + g_ws)

    # Constrained Optimum Analysis
    con = constrained_optimum(CONSTRAINED_MATRIX_WT, ALPHA)

    print("=" * 60)
    print("  EXPLICIT COMPOSITION BREAKDOWN (TOTAL MIX WT%)")
    print("=" * 60)
    print(f"\n[GLOBAL OPTIMUM - Entire Map]")
    print(f"  Large WC-Co: {g_wl * 100:>6.2f}%")
    print(f"  Small WC:    {g_ws * 100:>6.2f}%")
    print(f"  NiCr Matrix: {g_wm * 100:>6.2f}%")
    print(f"  -> Carbide Ratio: {g_carbide_ratio * 100:.1f}% Large / {(1 - g_carbide_ratio) * 100:.1f}% Small")

    if con:
        c_wl, c_ws = con["wt_large"], con["wt_small"]
        c_ratio = c_wl / (c_wl + c_ws)
        print(f"\n[CONSTRAINED OPTIMUM - Fixed {CONSTRAINED_MATRIX_WT * 100:.0f}% Matrix]")
        print(f"  Large WC-Co: {c_wl * 100:>6.2f}%")
        print(f"  Small WC:    {c_ws * 100:>6.2f}%")
        print(f"  NiCr Matrix: {CONSTRAINED_MATRIX_WT * 100:>6.2f}% (Fixed)")
        print(f"  -> Carbide Ratio: {c_ratio * 100:.1f}% Large / {(1 - c_ratio) * 100:.1f}% Small")
        print(f"  MFP All:     {con['mfp_all']:.1f} µm")
    print("\n" + "=" * 60)

    # ── VISUALIZATION ─────────────────────────────────────────────────────────

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), facecolor=BG_COLOR)

    # Heatmap
    im = ax1.pcolormesh(wl_v, ws_v, np.where(FEAS, SCORE, np.nan), cmap="viridis", shading="auto")
    ax1.contour(wl_v, ws_v, WM_G, levels=[0.1, 0.2, 0.3, 0.4, 0.5], colors="#777777", alpha=0.4, linestyles="--")

    # Markers for Heatmap
    ax1.plot(g_wl, g_ws, "*", color=MARKER_OPTIMAL, ms=15, label=f"Global Opt (S={g_score:.3f})")
    ax1.plot(CURRENT_WT_LARGE, CURRENT_WT_SMALL, "D", color=MARKER_CURRENT, ms=8, label="Current Design")

    if con:
        # The constraint line
        ax1.plot(con["p_wl"], 1.0 - CONSTRAINED_MATRIX_WT - con["p_wl"], color=MARKER_CONSTRAINED, lw=1.5, ls="--",
                 alpha=0.6)
        # The triangle on the heatmap
        ax1.plot(con["wt_large"], con["wt_small"], "^", color=MARKER_CONSTRAINED, ms=12,
                 label="Constrained Opt (40% Matrix)")

    ax1.set_title(f"Multi-Objective Score Map (Alpha={ALPHA})", color=TEXT_COLOR, fontweight="bold")
    ax1.set_xlabel("wt% Large WC-Co (Total Mix)", color=AXIS_COLOR)
    ax1.set_ylabel("wt% Small WC (Total Mix)", color=AXIS_COLOR)
    ax1.set_facecolor(PANEL_BG)
    ax1.legend(fontsize=8, facecolor="#1A1A1A", labelcolor="white", loc="upper right")
    plt.colorbar(im, ax=ax1).set_label("Score (Higher=Better)", color=TEXT_COLOR)

    # Sensitivity
    if con:
        ax2.set_facecolor(PANEL_BG)
        ax2.plot(con["p_wl"] * 100, con["p_mfp_l"], color="#E67E22", lw=2, label="MFP Large Only")
        ax2.plot(con["p_wl"] * 100, con["p_mfp_a"], color="#3498DB", lw=2, label="MFP All (Surface Area)")
        ax2.set_ylabel("Mean Free Path (µm)", color=AXIS_COLOR)

        ax2b = ax2.twinx()
        ax2b.plot(con["p_wl"] * 100, con["p_score"], color="#2ECC71", lw=2.5, label="Tradeoff Score")
        ax2b.plot(con["wt_large"] * 100, con["score"], "^", color=MARKER_CONSTRAINED, ms=12, label="Constrained Best")
        ax2b.set_ylabel("Score", color="#2ECC71")

        ax2.set_title(f"L/S Ratio Sensitivity at {CONSTRAINED_MATRIX_WT * 100:.0f} wt% Matrix", color=TEXT_COLOR,
                      fontweight="bold")
        ax2.set_xlabel("wt% Large WC-Co (Total Mix)", color=AXIS_COLOR)
        ax2.set_ylim(0, np.nanpercentile(con["p_mfp_l"], 70))

        lines, labels = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2b.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc="upper right", fontsize=8, facecolor="#1A1A1A",
                   labelcolor="white")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()