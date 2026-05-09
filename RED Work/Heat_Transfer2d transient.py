"""
2D Finite Element TRANSIENT Heat Conduction Solver
- Linear triangular elements (3-node)
- Backward Euler time integration
- Lumped mass matrix (diagonal), reassembled each Picard iteration for Cp(T)
- Both materials: temperature-dependent k(T) and Cp(T) via lookup tables
- Dirichlet and/or convective (Newton cooling) boundary conditions

Governing PDE:  rho*Cp(T) * dT/dt = div(k(T) * grad(T)) + Q

Backward Euler:  (M(T)/dt + K(T) + K_conv) * T^{n+1} = M(T)/dt * T^n + f + f_conv
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
from scipy.sparse import lil_matrix, diags
from scipy.sparse.linalg import spsolve

# ============================================================
# TUNABLE PARAMETERS
# ============================================================

# --- Domain geometry ---
Lx = 0.0453898          # domain width  [m]
Ly = 0.0381          # domain height [m]
nx = 60           # elements in x
ny = 30           # elements in y

interface_pts = [
    (0.0362, 0.0),     # bottom of domain
    (0.0362, 0.0254),    # kink point
    (0.0453898, 0.0381)     # top of domain
]

# --- Material interface ---
x_interface = 0.72 * Lx       # [m]

# --- Material 1 (left): k(T) and Cp(T) tables ---
#   Linear interpolation, clamped outside range.
k1_table_T  = [22.6,
101,
199.3,
301.6,
401.6,
501.6,
601.6,
701.7,
801.3,
900.8,
1000.9]   # [°C]
k1_table_k  = [133.02,
128.54,
117.62,
106.03,
96.7,
88.61,
82.22,
76.52,
71.78,
67.88,
64.26]   # [W/m·K]
cp1_table_T = [22.6,
101,
199.3,
301.6,
401.6,
501.6,
601.6,
701.7,
801.3,
900.8,
1000.9]          # [°C]
cp1_table_cp= [726.19,
933.15,
1154.47,
1341.07,
1486.83,
1603.53,
1697.43,
1773.6,
1835.58,
1886.68,
1929.44]          # [J/kg·K]
rho1 = 1800      # density [kg/m^3] (constant)

# --- Material 2 (right): k(T) and Cp(T) tables ---
k2_table_T  = [0,
93,
204,
315.6,
427.7,
571]   # [°C]
k2_table_k  = [162,
177,
192,
207,
223,
253]   # [W/m·K]
cp2_table_T = [0,
93,
204,
315.6,
427.7,
571]   # [°C]
cp2_table_cp= [917,
978,
1028,
1078,
1133,
1230]   # [J/kg·K]

rho2 = 2700 # [kg/m^3]

# --- Internal heat generation [W/m^3] ---
Q1 = 0.0
Q2 = 0.0

# --- Time stepping ---
t_end = 20  # total simulation time [s]
dt = 0.5  # time step [s]
n_steps = int(t_end / dt)

# --- Initial condition ---
T_init = 25.0  # initial temperature everywhere [°C]

# --- Dirichlet boundary conditions (applied at t > 0) ---
#   Set to None for no Dirichlet BC on that edge.
T_left = 2000  # [°C]
T_right = None
T_top = None
T_bottom = None

# --- Convective (Newton cooling) boundary conditions ---
#   Set to (h, T_ambient) or None for insulated.
#   h = heat transfer coefficient [W/m^2·K], T_ambient [°C]
#   Convective and Dirichlet should NOT both be set on the same edge.
conv_left = None
conv_right = (50.0, 25.0)  # h=50 W/m^2K, T_amb=25°C
conv_top = None
conv_bottom = None

# --- Picard iteration settings (per time step) ---
max_iter = 20
k_tol = 1e-4
relax = 1.0

# --- Output settings ---
n_snapshots = 8


# ============================================================
# MESH GENERATION
# ============================================================

def generate_mesh(Lx, Ly, nx, ny):
    x = np.linspace(0, Lx, nx + 1)
    y = np.linspace(0, Ly, ny + 1)
    X, Y = np.meshgrid(x, y)
    nodes = np.column_stack([X.ravel(), Y.ravel()])
    elements = []
    for j in range(ny):
        for i in range(nx):
            n0 = j * (nx + 1) + i
            n1 = n0 + 1
            n2 = n0 + (nx + 1)
            n3 = n2 + 1
            elements.append([n0, n1, n3])
            elements.append([n0, n3, n2])
    return nodes, np.array(elements), len(nodes)


# ============================================================
# PROPERTY INTERPOLATORS
# ============================================================

def make_interp(table_T, table_val):
    """Return a function that linearly interpolates (clamped) from a table."""
    T_arr = np.array(table_T, dtype=float)
    v_arr = np.array(table_val, dtype=float)

    def interp_fn(T):
        return np.interp(T, T_arr, v_arr)

    return interp_fn


# ============================================================
# ELEMENT ROUTINES
# ============================================================

def element_area(nodes_e):
    x, y = nodes_e[:, 0], nodes_e[:, 1]
    return 0.5 * abs((x[1] - x[0]) * (y[2] - y[0]) - (x[2] - x[0]) * (y[1] - y[0]))


def element_stiffness_and_load(nodes_e, k_e, Q_e):
    x, y = nodes_e[:, 0], nodes_e[:, 1]
    A = element_area(nodes_e)
    denom = 2.0 * A
    b = np.array([y[1] - y[2], y[2] - y[0], y[0] - y[1]]) / denom
    c = np.array([x[2] - x[1], x[0] - x[2], x[1] - x[0]]) / denom
    K_e = k_e * A * (np.outer(b, b) + np.outer(c, c))
    f_e = Q_e * A / 3.0 * np.ones(3)
    return K_e, f_e


# ============================================================
# LUMPED MASS MATRIX (temperature-dependent Cp)
# ============================================================

def assemble_lumped_mass(nodes, elements, mat_ids, rho_per_mat, cp_per_elem):
    """Lumped mass with per-element Cp (already evaluated at current T)."""
    n = len(nodes)
    M_diag = np.zeros(n)
    for ie, elem in enumerate(elements):
        A = element_area(nodes[elem])
        rho = rho_per_mat[mat_ids[ie]]
        contrib = rho * cp_per_elem[ie] * A / 3.0
        for a in range(3):
            M_diag[elem[a]] += contrib
    return M_diag


# ============================================================
# STIFFNESS ASSEMBLY
# ============================================================

def assemble_stiffness(nodes, elements, k_per_elem, Q_per_elem):
    n = len(nodes)
    K = lil_matrix((n, n))
    f = np.zeros(n)
    for ie, elem in enumerate(elements):
        K_e, f_e = element_stiffness_and_load(nodes[elem], k_per_elem[ie], Q_per_elem[ie])
        for a in range(3):
            f[elem[a]] += f_e[a]
            for b_idx in range(3):
                K[elem[a], elem[b_idx]] += K_e[a, b_idx]
    return K.tocsr(), f


# ============================================================
# CONVECTIVE BOUNDARY CONDITIONS
# ============================================================

def assemble_convective_bc(nodes, Lx, Ly, conv_bcs):
    """
    Assemble convective contributions to K and f.
    conv_bcs: dict of edge_name -> (h, T_amb) or None

    For each boundary edge with convection:
      K_conv += h * L/6 * [2,1; 1,2]
      f_conv += h * T_amb * L/2 * [1; 1]
    """
    n = len(nodes)
    K_conv = lil_matrix((n, n))
    f_conv = np.zeros(n)

    tol = 1e-10
    edge_coords = {
        "left": (0, 0.0, 1),  # (axis_idx, axis_val, sort_idx)
        "right": (0, Lx, 1),
        "bottom": (1, 0.0, 0),
        "top": (1, Ly, 0),
    }

    for edge_name, conv in conv_bcs.items():
        if conv is None:
            continue
        h, T_amb = conv
        ax_idx, val, sort_idx = edge_coords[edge_name]

        on_edge = np.where(np.abs(nodes[:, ax_idx] - val) < tol)[0]
        order = np.argsort(nodes[on_edge, sort_idx])
        sorted_nodes = on_edge[order]

        for i in range(len(sorted_nodes) - 1):
            ni, nj = sorted_nodes[i], sorted_nodes[i + 1]
            L = np.linalg.norm(nodes[nj] - nodes[ni])

            K_conv[ni, ni] += h * L / 3.0
            K_conv[ni, nj] += h * L / 6.0
            K_conv[nj, ni] += h * L / 6.0
            K_conv[nj, nj] += h * L / 3.0

            f_conv[ni] += h * T_amb * L / 2.0
            f_conv[nj] += h * T_amb * L / 2.0

    return K_conv.tocsr(), f_conv


# ============================================================
# DIRICHLET BOUNDARY CONDITIONS
# ============================================================

def get_boundary_nodes(nodes, Lx, Ly):
    tol = 1e-10
    return {
        "left": np.where(np.abs(nodes[:, 0]) < tol)[0],
        "right": np.where(np.abs(nodes[:, 0] - Lx) < tol)[0],
        "bottom": np.where(np.abs(nodes[:, 1]) < tol)[0],
        "top": np.where(np.abs(nodes[:, 1] - Ly) < tol)[0],
    }


def apply_dirichlet(K, f, bc_nodes, bc_vals):
    K = K.tolil()
    bc_set = set(bc_nodes)
    for node, val in zip(bc_nodes, bc_vals):
        col = np.array(K[:, node].todense()).flatten()
        for i in range(len(f)):
            if i not in bc_set:
                f[i] -= col[i] * val
    for node, val in zip(bc_nodes, bc_vals):
        K[node, :] = 0
        K[:, node] = 0
        K[node, node] = 1.0
        f[node] = val
    return K.tocsr(), f


# ============================================================
# MATERIAL ASSIGNMENT
# ============================================================

def assign_materials(nodes, elements, interface_pts):
    """Assign material ID based on which side of the interface polyline
    each element centroid falls on.

    Uses signed area (cross product) test against each segment.
    Material 0 = left of polyline, Material 1 = right.
    """
    centroids = np.mean(nodes[elements], axis=1)  # (n_elem, 2)
    pts = np.array(interface_pts)
    n_elem = len(elements)
    mat_ids = np.zeros(n_elem, dtype=int)

    for ie in range(n_elem):
        cx, cy = centroids[ie]

        # Find which segment this centroid's y-coordinate falls in
        # Walk segments from bottom to top
        assigned = False
        for s in range(len(pts) - 1):
            y0, y1 = pts[s, 1], pts[s + 1, 1]
            y_lo, y_hi = min(y0, y1), max(y0, y1)

            if cy < y_lo or cy > y_hi:
                continue

            # Interpolate the interface x at this y
            if abs(y1 - y0) < 1e-30:
                x_int = 0.5 * (pts[s, 0] + pts[s + 1, 0])
            else:
                frac = (cy - y0) / (y1 - y0)
                x_int = pts[s, 0] + frac * (pts[s + 1, 0] - pts[s, 0])

            mat_ids[ie] = 0 if cx < x_int else 1
            assigned = True
            break

        if not assigned:
            # Fallback: use nearest segment endpoint
            dists = np.abs(pts[:, 1] - cy)
            nearest = np.argmin(dists)
            mat_ids[ie] = 0 if cx < pts[nearest, 0] else 1

    return mat_ids


# ============================================================
# HEAT FLUX
# ============================================================

def compute_heat_flux(nodes, elements, T, k_per_elem):
    n_elem = len(elements)
    qx, qy = np.zeros(n_elem), np.zeros(n_elem)
    for ie, elem in enumerate(elements):
        nodes_e = nodes[elem]
        T_e = T[elem]
        A = element_area(nodes_e)
        x, y = nodes_e[:, 0], nodes_e[:, 1]
        denom = 2.0 * A
        b = np.array([y[1] - y[2], y[2] - y[0], y[0] - y[1]]) / denom
        c = np.array([x[2] - x[1], x[0] - x[2], x[1] - x[0]]) / denom
        qx[ie] = -k_per_elem[ie] * (b @ T_e)
        qy[ie] = -k_per_elem[ie] * (c @ T_e)
    return qx, qy


# ============================================================
# PLOTTING
# ============================================================

def plot_snapshots(nodes, elements, snapshots, snap_times, interface_pts):
    n = len(snapshots)
    ncols = 3
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(7.5, 2.5 * nrows),
                             constrained_layout=True)
    if nrows * ncols == 1:
        axes = np.array([axes])
    axes = np.atleast_2d(axes).flatten()
    tri = Triangulation(nodes[:, 0], nodes[:, 1], elements)
    T_all = np.concatenate(snapshots)
    vmin, vmax = T_all.min(), T_all.max()

    tcf = None
    for i, (T_snap, t) in enumerate(zip(snapshots, snap_times)):
        ax = axes[i]
        tcf = ax.tricontourf(tri, T_snap, levels=30, cmap='inferno', vmin=vmin, vmax=vmax)
        ipts = np.array(interface_pts)
        ax.plot(ipts[:, 0], ipts[:, 1], color='w', ls='--', lw=0.8)
        ax.set_title(f't = {t:.1f} s', fontsize=9)
        ax.set_aspect('equal')
        ax.set_xlabel('x [m]', fontsize=7)
        ax.set_ylabel('y [m]', fontsize=7)
        ax.tick_params(labelsize=6)
    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)
    fig.colorbar(tcf, ax=axes.tolist(), label='Temperature [°C]', shrink=0.6)
    fig.suptitle('Transient Temperature Evolution', fontsize=11)
    plt.savefig('fem_transient_snapshots.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Saved: fem_transient_snapshots.png")


def plot_centerline_history(nodes, snapshots, snap_times, Ly):
    tol = Ly / 40
    center_mask = np.abs(nodes[:, 1] - Ly / 2) < tol
    x_center = nodes[center_mask, 0]
    sort_idx = np.argsort(x_center)
    x_sorted = x_center[sort_idx]

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for T_snap, t in zip(snapshots, snap_times):
        T_center = T_snap[center_mask][sort_idx]
        ax.plot(x_sorted, T_center, label=f't={t:.0f}s')
    ax.set_xlabel('x [m]')
    ax.set_ylabel('Temperature [°C]')
    ax.set_title('Centerline Temperature vs. Time')
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('fem_transient_centerline.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Saved: fem_transient_centerline.png")


# ============================================================
# MAIN — TRANSIENT SOLVER
# ============================================================

if __name__ == "__main__":
    # --- Mesh ---
    nodes, elements, n_nodes = generate_mesh(Lx, Ly, nx, ny)
    n_elem = len(elements)
    mat_ids = assign_materials(nodes, elements, interface_pts)
    mat1_mask = (mat_ids == 0)
    mat2_mask = (mat_ids == 1)
    print(f"Mesh: {n_nodes} nodes, {n_elem} elements")
    print(f"Material 1: {np.sum(mat1_mask)} elem | Material 2: {np.sum(mat2_mask)} elem")
    print(f"Time: {n_steps} steps x dt={dt}s = {t_end}s")

    # --- Property interpolators ---
    k1_fn = make_interp(k1_table_T, k1_table_k)
    cp1_fn = make_interp(cp1_table_T, cp1_table_cp)
    k2_fn = make_interp(k2_table_T, k2_table_k)
    cp2_fn = make_interp(cp2_table_T, cp2_table_cp)

    rho_per_mat = [rho1, rho2]

    # --- Source term (constant) ---
    Q_per_elem = np.where(mat1_mask, Q1, Q2)

    # --- Convective BC (assembled once — h and T_amb are constant) ---
    conv_bcs = {
        "left": conv_left, "right": conv_right,
        "top": conv_top, "bottom": conv_bottom,
    }
    K_conv, f_conv = assemble_convective_bc(nodes, Lx, Ly, conv_bcs)
    has_conv = any(v is not None for v in conv_bcs.values())
    if has_conv:
        active = [f"{e}: h={v[0]}, T_amb={v[1]}" for e, v in conv_bcs.items() if v]
        print(f"Convective BCs: {'; '.join(active)}")

    # --- Dirichlet BCs ---
    bnd = get_boundary_nodes(nodes, Lx, Ly)
    bc_node_list, bc_val_list = [], []
    for edge, T_bc in [("left", T_left), ("right", T_right),
                       ("top", T_top), ("bottom", T_bottom)]:
        if T_bc is not None:
            bc_node_list.append(bnd[edge])
            bc_val_list.append(np.full(len(bnd[edge]), T_bc))
    if bc_node_list:
        bc_nodes = np.concatenate(bc_node_list)
        bc_vals = np.concatenate(bc_val_list)
        has_dirichlet = True
    else:
        bc_nodes, bc_vals = np.array([], dtype=int), np.array([])
        has_dirichlet = False

    # --- Initial condition ---
    T = np.full(n_nodes, T_init)

    # --- Snapshot schedule ---
    snap_steps = np.linspace(0, n_steps, n_snapshots + 1, dtype=int)
    snap_steps = np.unique(np.concatenate([[0, n_steps], snap_steps]))
    snapshots = [T.copy()]
    snap_times = [0.0]

    # --- Initialize property fields from T_init ---
    k_per_elem = np.empty(n_elem)
    cp_per_elem = np.empty(n_elem)
    k_per_elem[mat1_mask] = k1_fn(T_init)
    k_per_elem[mat2_mask] = k2_fn(T_init)
    cp_per_elem[mat1_mask] = cp1_fn(T_init)
    cp_per_elem[mat2_mask] = cp2_fn(T_init)

    # --- Time loop ---
    print(f"\n{'Step':>6s}  {'t [s]':>8s}  {'T_min':>8s}  {'T_max':>8s}  {'Picard':>6s}")
    print("-" * 46)

    for step in range(1, n_steps + 1):
        t = step * dt
        T_old = T.copy()

        for it in range(max_iter):
            # Update Cp and k fields from current T
            T_elem = np.mean(T[elements], axis=1)
            cp_per_elem[mat1_mask] = cp1_fn(T_elem[mat1_mask])
            cp_per_elem[mat2_mask] = cp2_fn(T_elem[mat2_mask])

            # Reassemble lumped mass with updated Cp
            M_diag = assemble_lumped_mass(nodes, elements, mat_ids, rho_per_mat, cp_per_elem)
            M_over_dt = M_diag / dt

            # Assemble stiffness with current k
            K, f_source = assemble_stiffness(nodes, elements, k_per_elem, Q_per_elem)

            # Effective system: (M/dt + K + K_conv) T^{n+1} = M/dt * T^n + f + f_conv
            A_eff = diags(M_over_dt) + K + K_conv
            rhs = M_over_dt * T_old + f_source + f_conv

            # Apply Dirichlet BCs
            if has_dirichlet:
                A_sys, rhs_sys = apply_dirichlet(A_eff, rhs.copy(), bc_nodes, bc_vals)
            else:
                A_sys, rhs_sys = A_eff.tocsr(), rhs

            # Solve
            T = spsolve(A_sys, rhs_sys)

            # Update k for both materials
            T_elem = np.mean(T[elements], axis=1)
            k_new = k_per_elem.copy()
            k_new[mat1_mask] = k1_fn(T_elem[mat1_mask])
            k_new[mat2_mask] = k2_fn(T_elem[mat2_mask])
            k_new = relax * k_new + (1.0 - relax) * k_per_elem

            with np.errstate(divide='ignore', invalid='ignore'):
                max_dk = np.max(np.abs(k_new - k_per_elem) / np.maximum(np.abs(k_per_elem), 1e-30))

            k_per_elem = k_new

            if max_dk < k_tol:
                break

        if step in snap_steps or step % max(1, n_steps // 10) == 0:
            print(f"{step:6d}  {t:8.2f}  {T.min():8.2f}  {T.max():8.2f}  {it + 1:6d}")

        if step in snap_steps:
            snapshots.append(T.copy())
            snap_times.append(t)

    print(f"\nDone. Final T range: [{T.min():.2f}, {T.max():.2f}]")

    # --- Final property ranges ---
    print(f"Mat1 k: [{k_per_elem[mat1_mask].min():.1f}, {k_per_elem[mat1_mask].max():.1f}] W/m·K")
    print(f"Mat1 Cp: [{cp_per_elem[mat1_mask].min():.1f}, {cp_per_elem[mat1_mask].max():.1f}] J/kg·K")
    print(f"Mat2 k: [{k_per_elem[mat2_mask].min():.1f}, {k_per_elem[mat2_mask].max():.1f}] W/m·K")
    print(f"Mat2 Cp: [{cp_per_elem[mat2_mask].min():.1f}, {cp_per_elem[mat2_mask].max():.1f}] J/kg·K")

    # --- Final heat flux ---
    qx, qy = compute_heat_flux(nodes, elements, T, k_per_elem)
    q_mag = np.sqrt(qx ** 2 + qy ** 2)
    print(f"|q|_max at t_end = {q_mag.max():.1f} W/m^2")

    # --- Plots ---
    plot_snapshots(nodes, elements, snapshots, snap_times, interface_pts)
    plot_centerline_history(nodes, snapshots, snap_times, Ly)
