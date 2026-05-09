import numpy as np
import matplotlib.pyplot as plt

# Original data
x_data = np.array([0.5,1.0,1.5,2.0,2.5], dtype=float)
y_data = np.array([0.541,0.398,0.232,0.106,0.052], dtype=float)

# Transform for linear regression
Y = np.log(y_data / x_data)
X = x_data.copy()

# Linear regression
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

b, ln_a = linear_regression(X, Y)
a = np.exp(ln_a)
print(f'a = {a}')
print(f'b = {b}')
# Generate x values
x_vals = np.arange(0.5, 2.5 + 0.025, 0.025)

# Compute y values
y_vals = a * x_vals * np.exp(b * x_vals)

# Plot
plt.figure()
plt.plot(x_vals, y_vals)
plt.scatter(x_data, y_data)
plt.xlabel("x")
plt.ylabel("y")
plt.title("Fitted Curve and Data Points")
plt.show()

SSE = 0

for i in range(len(x_data)):
    y_pred = a * x_data[i] * np.exp(b * x_data[i])   # model prediction
    error = y_data[i] - y_pred                  # actual - predicted
    SSE += error**2

print("Sum of squared errors:", SSE)