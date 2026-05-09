import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from sklearn.linear_model import LinearRegression

# Sample data (replace with your actual data)
feed_rate = [25,25,36,36,25,25,36,36]  # Feed rate values
scan_speed = [800,800,800,800,1100,1100,1100,1100]  # Scan speed values
total_thickness = [0.840,0.820,1.315,1.359,0.571,0.601,0.924,0.912]  # Total thickness values

# Convert to numpy arrays for regression
X = np.array([feed_rate, scan_speed]).T
y = np.array(total_thickness)

# Fit the plane using linear regression
model = LinearRegression()
model.fit(X, y)

# Create figure and 3D axis
fig = plt.figure(figsize=(11, 8))
ax = fig.add_subplot(111, projection='3d')

# Create scatter plot
scatter = ax.scatter(feed_rate, scan_speed, total_thickness,
                     c=total_thickness, cmap='viridis',
                     marker='o', s=100, alpha=0.8, label='Data points')

# Create plane of best fit
x_range = np.linspace(min(feed_rate) - 2, max(feed_rate) + 2, 10)
y_range = np.linspace(min(scan_speed) - 10, max(scan_speed) + 10, 10)
X_plane, Y_plane = np.meshgrid(x_range, y_range)
Z_plane = model.predict(np.c_[X_plane.ravel(), Y_plane.ravel()]).reshape(X_plane.shape)

# Plot the plane
ax.plot_surface(X_plane, Y_plane, Z_plane, alpha=0.3, cmap='cool', label='Best fit plane')

# Print regression equation
intercept = model.intercept_
coef_feed = model.coef_[0]
coef_scan = model.coef_[1]
print(f"Plane equation: Thickness = {intercept:.3f} + {coef_feed:.4f}*FeedRate + {coef_scan:.4f}*ScanSpeed")
print(f"R² score: {model.score(X, y):.4f}")

# Set labels
ax.set_xlabel('Feed Rate (g/min)', fontsize=11)
ax.set_ylabel('Scan Speed (mm/min)', fontsize=11)
ax.set_zlabel('Total Thickness (mm)', fontsize=11, rotation=180)
ax.set_title('3D Plot: Total Thickness vs Feed Rate and Scan Speed\n(with Best Fit Plane)', fontsize=13,
             fontweight='bold')

# Add colorbar with reduced padding
colorbar = plt.colorbar(scatter, ax=ax, pad=0.05, shrink=0.8)
colorbar.set_label('Thickness (mm)', fontsize=10)

# Add legend
ax.legend(loc='upper left', fontsize=10)

# Adjust viewing angle (optional)
ax.view_init(elev=20, azim=45)

# Display plot
plt.tight_layout()
plt.show()