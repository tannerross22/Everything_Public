import numpy as np
import matplotlib.pyplot as plt
import math
from numpy import sign

T = np.arange(0, 1200 + 10, 10)

def Cp(T):
    return (0.99403
      + 1.671e-4 * T
      + 9.7215e-8 * T**2
      - 9.5838e-11 * T**3
      + 1.9520e-14 * T**4)

# Plot — call the function to get the array
plt.figure()
plt.plot(T, Cp(T))
plt.axhline(1.10)
plt.xlabel("Temperature (K)")
plt.ylabel("Cp (kJ/kg·K)")
plt.title("Specific Heat of Dry Air vs Temperature")
plt.show()

def bisection(f, x1, x2, switch=1, tol=1.0e-9):
    f1 = f(x1)
    if f1 == 0.0: return x1
    f2 = f(x2)
    if f2 == 0.0: return x2
    if sign(f1) == sign(f2):
        raise ValueError('Root is not bracketed')
    n = int(math.ceil(math.log(abs(x2 - x1) / tol) / math.log(2.0)))
    for i in range(n):
        x3 = 0.5 * (x1 + x2); f3 = f(x3)
        if (switch == 1) and (abs(f3) > abs(f1)) and (abs(f3) > abs(f2)):
            return None
        if f3 == 0.0: return x3
        if sign(f2) != sign(f3):
            x1 = x3; f1 = f3
        else:
            x2 = x3; f2 = f3
    return (x1 + x2) / 2.0

target = 1.10
print(f'Bisection 1.10 kJ/(kg*K) intersect within 0.1K = {bisection(lambda T: Cp(T) - target, 500, 600, 1, 0.1)}K')



def dCp(T):
    return (1.671e-4
      + 2 * 9.7215e-8 * T
      - 3 * 9.5838e-11 * T**2
      + 4 * 1.9520e-14 * T**3)


## module newtonRaphson
''' root = newtonRaphson(f,df,a,b,tol=1.0e-9).
    Finds a root of f(x) = 0 by combining the Newton-Raphson
    method with bisection. The root must be bracketed in (a,b).
    Calls user-supplied functions f(x) and its derivative df(x).   
'''


def newtonRaphson(f, df, a, b, tol=1.0e-9):
    import error
    from numpy import sign

    fa = f(a)
    if fa == 0.0: return a
    fb = f(b)
    if fb == 0.0: return b
    if sign(fa) == sign(fb): error.err('Root is not bracketed')
    x = 0.5 * (a + b)
    for i in range(30):
        fx = f(x)
        if fx == 0.0: return x
        # Tighten the brackets on the root
        if sign(fa) != sign(fx):
            b = x
        else:
            a = x
        # Try a Newton-Raphson step
        dfx = df(x)
        # If division by zero, push x out of bounds
        try:
            dx = -fx / dfx
        except ZeroDivisionError:
            dx = b - a
        x = x + dx
        # If the result is outside the brackets, use bisection
        if (b - x) * (x - a) < 0.0:
            dx = 0.5 * (b - a)
            x = a + dx
        # Check for convergence
        if abs(dx) < tol * max(abs(b), 1.0): return x
    print('Too many iterations in Newton-Raphson')

print(f'Newton-Raphson 1.10 kJ/(kg*K) intersect within 0.1K = {newtonRaphson(lambda T: Cp(T) - target, lambda T: dCp(T), 500, 600)}K')