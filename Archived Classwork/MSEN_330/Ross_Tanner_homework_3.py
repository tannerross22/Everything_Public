#%%
def grouped_weighted_linear_regression(x, y_lists, weights):

    n = len(x)
    num_machines = len(y_lists)


    S_w = 0.0
    S_wx = 0.0
    S_wy = 0.0
    S_wxx = 0.0
    S_wxy = 0.0

    for k in range(num_machines):
        w = weights[k]
        y = y_lists[k]

        for i in range(n):
            xi = x[i]
            yi = y[i]

            S_w += w
            S_wx += w * xi
            S_wy += w * yi
            S_wxx += w * xi * xi
            S_wxy += w * xi * yi

    denominator = S_w * S_wxx - S_wx ** 2


    m = (S_w * S_wxy - S_wx * S_wy) / denominator
    b = (S_wy - m * S_wx) / S_w

    return m, b

x = [34.5, 69, 103.5, 138]
y1 = [0.46,0.95,1.48,1.93]
y2 = [0.34,1.02,1.51,2.09]
y3 = [0.73,1.10,1.62,2.12]
y_lists = [y1,y2,y3]
weights = [1,1,1]
m, b = grouped_weighted_linear_regression(x, y_lists, weights)

print(f'Elastic Modulus: {(1/m):.2f}')
#%%
x = [34.5, 69, 103.5, 138]
y1 = [0.46,0.95,1.48,1.93]
y2 = [0.34,1.02,1.51,2.09]
y3 = [0.73,1.10,1.62,2.12]
y_lists = [y1,y2,y3]
weights = [1,1,0.5]
m, b = grouped_weighted_linear_regression(x, y_lists, weights)

print(f'Elastic Modulus: {(1/m):.2f}')
#%%
def linear_regression(x, y):

    n = len(x)

    sum_x = sum(x)
    sum_y = sum(y)
    sum_xx = sum(xi ** 2 for xi in x)
    sum_xy = sum(x[i] * y[i] for i in range(n))

    denominator = n * sum_xx - sum_x ** 2

    m = (n * sum_xy - sum_x * sum_y) / denominator
    b = (sum_y - m * sum_x) / n

    return m, b


def quadratic_regression(x, y):
    n = len(x)

    Sx = sum(x)
    Sx2 = sum(xi ** 2 for xi in x)
    Sx3 = sum(xi ** 3 for xi in x)
    Sx4 = sum(xi ** 4 for xi in x)

    Sy = sum(y)
    Sxy = sum(x[i] * y[i] for i in range(n))
    Sx2y = sum((x[i] ** 2) * y[i] for i in range(n))

    A = [
        [Sx4, Sx3, Sx2],
        [Sx3, Sx2, Sx],
        [Sx2, Sx, n]
    ]

    B = [Sx2y, Sxy, Sy]

    for i in range(3):
        pivot = A[i][i]

        for j in range(i, 3):
            A[i][j] /= pivot
        B[i] /= pivot

        for k in range(i + 1, 3):
            factor = A[k][i]
            for j in range(i, 3):
                A[k][j] -= factor * A[i][j]
            B[k] -= factor * B[i]

    f = B[2]
    e = B[1] - A[1][2] * f
    d = B[0] - A[0][1] * e - A[0][2] * f

    return d, e, f

def r_squared(x, y, m, b):

    n = len(y)
    y_mean = sum(y) / n

    SS_res = 0.0
    SS_tot = 0.0

    for i in range(n):
        y_hat = m * x[i] + b
        SS_res += (y[i] - y_hat) ** 2
        SS_tot += (y[i] - y_mean) ** 2

    return 1 - SS_res / SS_tot


def r_squared_quadratic(x, y, d, e, f):
    n = len(y)
    y_mean = sum(y) / n

    SS_res = 0.0
    SS_tot = 0.0

    for i in range(n):
        y_hat = d * x[i] ** 2 + e * x[i] + f
        SS_res += (y[i] - y_hat) ** 2
        SS_tot += (y[i] - y_mean) ** 2

    if SS_tot == 0:
        return 1.0

    return 1 - SS_res / SS_tot


x = [1.0,2.5,3.5,4.0,1.1,1.8,2.2,3.7]

y = [6.008,15.722,27.130,33.772,5.257,9.549,11.098,28.828]

m, b = linear_regression(x, y)
d,e,f = quadratic_regression(x, y)
R2 = r_squared(x, y, m, b)
print(f'Linear Fit m: {m:.2f} b: {b:.2f},  R^2: {R2:.5f}')
R2 = r_squared_quadratic(x, y, d, e, f)
print(f'Quadratic fit: {d:.2f}x^2 {e:.2f}x + {f:.2f}, R^2 {R2:.5f}')



#%%
import math

def power_law_regression(x, y):
    X = [math.log(xi) for xi in x]
    Y = [math.log(yi) for yi in y]

    n = len(X)

    sum_X = sum(X)
    sum_Y = sum(Y)
    sum_XX = sum(Xi ** 2 for Xi in X)
    sum_XY = sum(X[i] * Y[i] for i in range(n))

    denominator = n * sum_XX - sum_X ** 2

    b = (n * sum_XY - sum_X * sum_Y) / denominator
    A = (sum_Y - b * sum_X) / n

    a = math.exp(A)

    return a, b

x  =[0.5,1,1.5,2.0,2.5]
y = [0.49,1.60,3.36,6.44,10.16]

a, b = power_law_regression(x, y)
print(f'F(x) = {a:.2f}x^{b:.2f}')
#%%
def multiple_linear_regression(x, y, z):

    n = len(x)

    Sx = sum(x)
    Sy = sum(y)
    Sz = sum(z)
    Sxx = sum(xi ** 2 for xi in x)
    Syy = sum(yi ** 2 for yi in y)
    Sxy = sum(x[i] * y[i] for i in range(n))
    Sxz = sum(x[i] * z[i] for i in range(n))
    Syz = sum(y[i] * z[i] for i in range(n))

    A = [
        [n, Sx, Sy],
        [Sx, Sxx, Sxy],
        [Sy, Sxy, Syy]
    ]

    B = [Sz, Sxz, Syz]

    for i in range(3):
        pivot = A[i][i]
        for j in range(i, 3):
            A[i][j] /= pivot
        B[i] /= pivot

        for k in range(i + 1, 3):
            factor = A[k][i]
            for j in range(i, 3):
                A[k][j] -= factor * A[i][j]
            B[k] -= factor * B[i]

    c = B[2]
    b = B[1] - A[1][2] * c
    a = B[0] - A[0][1] * b - A[0][2] * c

    return a, b, c

x = [0,0,1,2,2,2]
y = [0,1,0,0,1,2]
z = [1.42,1.85,.78,0.18,0.6,1.05]
a, b, c = multiple_linear_regression(x, y, z)
print(f'F(x,y) = {a:.2f}x + {b:.2f}y + {c:.2f}z')
#%%
