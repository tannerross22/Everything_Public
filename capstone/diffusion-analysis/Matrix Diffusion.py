import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------------------------------------
# LOAD DATA
# -------------------------------------------------------

csv_path = "40_60_Scan_Substrate.csv"
df = pd.read_csv(csv_path)

x = df["Distance (um)"].values
y_raw = df["Fe"].values

# Normalize Fe content so max = 1.0
y = y_raw / np.max(y_raw)

# -------------------------------------------------------
# USER INPUT: ONLY REGION BOUNDARIES
# -------------------------------------------------------

print("Enter the distances that separate the regions:")
boundary12 = float(input("Boundary between Region 1 and 2: "))
boundary23 = float(input("Boundary between Region 2 and 3: "))

# Automatically handled boundaries
x_min = x.min()
x_max = x.max()

# -------------------------------------------------------
# REGION SELECTION
# -------------------------------------------------------

def select_region(x, y, low, high):
    mask = (x >= low) & (x <= high)
    return x[mask], y[mask]

# Define regions
x1, y1 = select_region(x, y, x_min, boundary12)
x2, y2 = select_region(x, y, boundary12, boundary23)
x3, y3 = select_region(x, y, boundary23, x_max)

# -------------------------------------------------------
# LINEAR FITS
# -------------------------------------------------------

def linear_fit(x, y):
    m, b = np.polyfit(x, y, 1)
    return m, b

m1, b1 = linear_fit(x1, y1)
m2, b2 = linear_fit(x2, y2)
m3, b3 = linear_fit(x3, y3)

# -------------------------------------------------------
# INTERSECTION POINTS
# -------------------------------------------------------

def intersection(mA, bA, mB, bB):
    x_int = (bB - bA) / (mA - mB)
    y_int = mA * x_int + bA
    return x_int, y_int

x_int_12, y_int_12 = intersection(m1, b1, m2, b2)
x_int_23, y_int_23 = intersection(m3, b3, m2, b2)

diffusion_width = abs(x_int_23 - x_int_12)

print("\n------------------------------")
print("Intersection (Region 1 & 2):  x =", x_int_12)
print("Intersection (Region 2 & 3):  x =", x_int_23)
print("Diffusion Width =", diffusion_width, "microns")
print("------------------------------\n")

# -------------------------------------------------------
# PLOT
# -------------------------------------------------------

plt.scatter(x, y, s=10, label="Data (Normalized)", color="black")

# Smooth plot ranges
xx1 = np.linspace(x_min, boundary12, 200)
xx2 = np.linspace(boundary12, boundary23, 200)
xx3 = np.linspace(boundary23, x_max, 200)

plt.plot(xx1, m1*xx1 + b1, label="Fit Region 1", linewidth=2)
plt.plot(xx2, m2*xx2 + b2, label="Fit Region 2", linewidth=2)
plt.plot(xx3, m3*xx3 + b3, label="Fit Region 3", linewidth=2)

# Mark intersections
plt.scatter([x_int_12, x_int_23], [y_int_12, y_int_23],
            s=80, color="red", label="Intersections")

plt.xlabel("Distance (microns)")
plt.ylabel("Fraction Fe (normalized)")

plt.title("Iron Concentration Profile – Flame Spray")
plt.grid(True)

# Outside tick marks
plt.tick_params(direction='out', length=6, width=1.2)

plt.legend()
plt.show()
