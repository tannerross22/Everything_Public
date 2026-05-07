import numpy as np
import matplotlib.pyplot as plt

# ================= USER INPUT =================
def f(t, y):
    return y*t**2-1.1*y  # dy/dt = f(t,y)

def analytical(t):
    return np.exp((t**3)/3-1.1*t)  # exact solution

t0 = 0
y0 = 1
t_end = 5

dt_list = [0.5, 0.25, 0.125]  # time steps to compare
dt_compare = 0.5  # for method comparison


# ================= METHODS =================
def euler(F,x,y,xStop,h):
    X = []
    Y = []
    X.append(x)
    Y.append(y)
    while x < xStop:
        h = min(h,xStop - x)
        y = y + h*F(x,y)
        x = x + h
        X.append(x)
        Y.append(y)
    return np.array(X),np.array(Y)


def heun(f, t0, y0, t_end, dt):
    t_vals = np.arange(t0, t_end + dt, dt)
    y_vals = np.zeros_like(t_vals)
    y_vals[0] = y0

    for i in range(len(t_vals) - 1):
        k1 = f(t_vals[i], y_vals[i])
        y_predict = y_vals[i] + dt * k1
        k2 = f(t_vals[i] + dt, y_predict)
        y_vals[i + 1] = y_vals[i] + (dt / 2) * (k1 + k2)

    return t_vals, y_vals


def midpoint(f, t0, y0, t_end, dt):
    t_vals = np.arange(t0, t_end + dt, dt)
    y_vals = np.zeros_like(t_vals)
    y_vals[0] = y0

    for i in range(len(t_vals) - 1):
        k1 = f(t_vals[i], y_vals[i])
        k2 = f(t_vals[i] + dt / 2, y_vals[i] + dt / 2 * k1)
        y_vals[i + 1] = y_vals[i] + dt * k2

    return t_vals, y_vals


def rk4(f, t0, y0, t_end, dt):
    t_vals = np.arange(t0, t_end + dt, dt)
    y_vals = np.zeros_like(t_vals)
    y_vals[0] = y0

    for i in range(len(t_vals) - 1):
        t = t_vals[i]
        y = y_vals[i]

        k1 = f(t, y)
        k2 = f(t + dt / 2, y + dt / 2 * k1)
        k3 = f(t + dt / 2, y + dt / 2 * k2)
        k4 = f(t + dt, y + dt * k3)

        y_vals[i + 1] = y + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)

    return t_vals, y_vals


#PLOT 1: EULER and analytical
t_fine = np.linspace(t0, t_end, 500)
plt.figure(figsize=(7.5,4.5))

plt.plot(t_fine, analytical(t_fine), label="Analytical", linewidth=2)

for dt in dt_list:
    t_vals, y_vals = euler(f, t0, y0, t_end, dt)
    plt.plot(t_vals, y_vals, label=f"Euler dt={dt}")

plt.xlabel("t")
plt.ylabel("y")
plt.ylim(0,10)
plt.xlim(0,5)
plt.title("Euler Method vs Analytical Solution")
plt.legend()
plt.grid()

# ================= PLOT 2: METHOD COMPARISON =================
plt.figure(figsize=(7.5,4.5))

plt.plot(t_fine, analytical(t_fine), label="Analytical", linewidth=2)

t_h, y_h = heun(f, t0, y0, t_end, dt_compare)
t_m, y_m = midpoint(f, t0, y0, t_end, dt_compare)
t_rk, y_rk = rk4(f, t0, y0, t_end, dt_compare)

plt.plot(t_h, y_h, label="Heun (dt=0.5)")
plt.plot(t_m, y_m, label="Midpoint (dt=0.5)")
plt.plot(t_rk, y_rk, label="RK4 (dt=0.5)")

plt.xlabel("t")
plt.ylabel("y")
plt.title("Method Comparison (dt = 0.5)")
plt.legend()
plt.grid()
plt.ylim(0,10)
plt.xlim(0,5)

plt.show()