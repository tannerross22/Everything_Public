import math

def linear_regression(x, y):
    if len(x) != len(y):
        raise ValueError("x and y must have same length")

    n = len(x)

    sum_x = sum(x)
    sum_y = sum(y)
    sum_xx = sum(xi ** 2 for xi in x)
    sum_xy = sum(x[i] * y[i] for i in range(n))

    denominator = n * sum_xx - sum_x ** 2

    if denominator == 0:
        raise ValueError("Denominator is zero — cannot compute regression.")

    m = (n * sum_xy - sum_x * sum_y) / denominator
    b = (sum_y - m * sum_x) / n

    return m, b

x = [-1,-0.5,0,0.5,1]
y = [-1,-0.55,0,0.45,1]

def std_dev(x, y):
    n = len(x)
    mean = sum(x) / n
    variance = sum((xi-mean)**2 for xi in x) / (n-1)
    return math.sqrt(variance)

m, b = linear_regression(x, y)
print(f'Slope: {m}')
print(f'Intercept: {b}')
print(f'Standard Deviation: {std_dev(x, y)}')