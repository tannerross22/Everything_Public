#%%
import numpy as np

def forward_diff(x, y, target):

    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)

    h  = x[1] - x[0]
    i  = np.where(np.isclose(x, target))[0][0]

    y0, y1, y2, y3 = y[i], y[i+1], y[i+2], y[i+3]

    # Table 5.3a coefficients
    df  = (-3*y0 + 4*y1 -  y2) / (2*h)
    d2f = ( 2*y0 - 5*y1 + 4*y2 -    y3 ) / (h**2)
    return df, d2f


x = [2.36,2.37, 2.38, 2.39]
y = [0.85866, 0.86289, 0.86710, 0.87129]

target = 2.36
df, d2f = forward_diff(x, y, target)

print(f' df({target}) ≈ {df:.6f}')
print(f' d2f({target}) ≈ {d2f:.6f}')

#%%
import numpy as np

def lagrange_diff_3pt(x, y, target):

    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)

    x0, x1, x2 = x
    y0, y1, y2 = y
    t = target

    # Denominators (reused in both formulas)
    d0 = (x0 - x1) * (x0 - x2)
    d1 = (x1 - x0) * (x1 - x2)
    d2 = (x2 - x0) * (x2 - x1)

    #f'
    df = (y0 * (2*t - x1 - x2) / d0 +
          y1 * (2*t - x0 - x2) / d1 +
          y2 * (2*t - x0 - x1) / d2)

    #f''
    d2f = 2 * (y0/d0 + y1/d1 + y2/d2)

    return df, d2f



x_data = [0.97, 1.00, 1.05]
y_data = [0.85040, 0.84147, 0.82612]
target = 1.0

df, d2f = lagrange_diff_3pt(x_data, y_data, target)

print(f'\n  df({target}) ≈ {df:.6f}')
print(f'  dff({target}) ≈ {d2f:.6f}')

#%%
import numpy as np

x = np.array([0.84, 0.92, 1.00, 1.08, 1.16])
y = np.array([0.431711, 0.398519, 0.367879, 0.339596, 0.313486])

# Central difference
g_h1 = (y[0] - 2*y[2] + y[4]) / 0.16**2   # h = 0.16
g_h2 = (y[1] - 2*y[2] + y[3]) / 0.08**2   # h = 0.08

# Richardson extrapolation p=2
G = (4*g_h2 - g_h1) / 3

print(f"f''(1) ≈ {G:.6f}")
#%%
import numpy as np

x = np.array([0.0, 0.1, 0.2, 0.3, 0.4])
y = np.array([0.000000, 0.078348, 0.138910, 0.192916, 0.244981])

# Central difference O(h²) for f' with two stencil widths
g_h1 = (y[4] - y[0]) / (2*0.2)   # h = 0.2, outer pair
g_h2 = (y[3] - y[1]) / (2*0.1)   # h = 0.1, inner pair

# Richardson extrapolation p=2
G = (4*g_h2 - g_h1) / 3

print(f"f'(0.2) ≈ {G:.6f}")
#%%
import numpy as np

def lagrange_diff_numerical(x_points, y_points, target):
    x = np.array(x_points, dtype=float)
    y = np.array(y_points, dtype=float)
    n = len(x)
    t = float(target)

    df  = 0.0
    d2f = 0.0

    for i in range(n):
        Li = 1.0
        for j in range(n):
            if i != j:
                Li *= (t - x[j]) / (x[i] - x[j])

        S1 = sum(1.0 / (t - x[j]) for j in range(n) if i != j and abs(t - x[j]) > 1e-14)
        S2 = sum(1.0 / (t - x[j])**2 for j in range(n) if i != j and abs(t - x[j]) > 1e-14)

        df  += y[i] * Li * S1
        d2f += y[i] * Li * (S1**2 - S2)

    print(f"f'({target})  = {df}")
    print(f"f''({target}) = {d2f}")

    return df, d2f

x_pts = [-2.2, -0.3, 0.8, 1.9]
y_pts = [15.180, 10.962, 1.920, -2.040]

lagrange_diff_numerical(x_pts, y_pts, target=0)