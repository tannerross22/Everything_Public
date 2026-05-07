## module cubicSpline
''' k = curvatures(xData,yData).
    Returns the curvatures of cubic spline at its knots.

    y = evalSpline(xData,yData,k,x).
    Evaluates cubic spline at x. The curvatures k can be
    computed with the function 'curvatures'.
'''

Eval = [10,30,60,90]
import numpy as np

##LU DECOMP 3 AS A PREREQ
#######################################
def LUdecomp3(c,d,e):
    n = len(d)
    for k in range(1,n):
        lam = c[k-1]/d[k-1]
        d[k] = d[k] - lam*e[k-1]
        c[k-1] = lam
    return c,d,e

def LUsolve3(c,d,e,b):
    n = len(d)
    for k in range(1,n):
        b[k] = b[k] - c[k-1]*b[k-1]
    b[n-1] = b[n-1]/d[n-1]
    for k in range(n-2,-1,-1):
        b[k] = (b[k] - e[k]*b[k+1])/d[k]
    return b
###########################################
##CUBIC SPLINE CODE

def curvatures(xData, yData):
    n = len(xData) - 1
    c = np.zeros(n)
    d = np.ones(n + 1)
    e = np.zeros(n)
    k = np.zeros(n + 1)
    c[0:n - 1] = xData[0:n - 1] - xData[1:n]
    d[1:n] = 2.0 * (xData[0:n - 1] - xData[2:n + 1])
    e[1:n] = xData[1:n] - xData[2:n + 1]
    k[1:n] = 6.0 * (yData[0:n - 1] - yData[1:n]) \
             / (xData[0:n - 1] - xData[1:n]) \
             - 6.0 * (yData[1:n] - yData[2:n + 1]) \
             / (xData[1:n] - xData[2:n + 1])
    LUdecomp3(c, d, e)
    LUsolve3(c, d, e, k)
    return k


def evalSpline(xData, yData, k, x):
    def findSegment(xData, x):
        iLeft = 0
        iRight = len(xData) - 1
        while 1:
            if (iRight - iLeft) <= 1: return iLeft
            i = (iLeft + iRight) // 2
            if x < xData[i]:
                iRight = i
            else:
                iLeft = i

    i = findSegment(xData, x)
    h = xData[i] - xData[i + 1]
    y = ((x - xData[i + 1]) ** 3 / h - (x - xData[i + 1]) * h) * k[i] / 6.0 \
        - ((x - xData[i]) ** 3 / h - (x - xData[i]) * h) * k[i + 1] / 6.0 \
        + (yData[i] * (x - xData[i + 1]) \
           - yData[i + 1] * (x - xData[i])) / h
    return y

xData = np.array([0,21.1,37.8,54.4,71.1,87.8,100])
yData = np.array([0.00179, 0.00113, 0.000696,0.000519,0.000338,0.000321, 0.000269])

k = curvatures(xData,yData)
for i in Eval:
    mu = evalSpline(xData,yData,k,i)
    print(f'Cubic Spline at {i} C = {mu} m^2/s')

# --- Gauss Elimination ---
def gaussElimin(a, b):
    n = len(b)
    for k in range(0, n-1):
        for i in range(k+1, n):
            if a[i,k] != 0.0:
                lam = a[i,k] / a[k,k]
                a[i,k+1:n] = a[i,k+1:n] - lam*a[k,k+1:n]
                b[i] = b[i] - lam*b[k]
    for k in range(n-1, -1, -1):
        b[k] = (b[k] - np.dot(a[k,k+1:n], b[k+1:n])) / a[k,k]
    return b

# --- LU Decomp for Spline ---
def LUdecomp3(c, d, e):
    n = len(d)
    for k in range(1, n):
        lam = c[k-1] / d[k-1]
        d[k] = d[k] - lam*e[k-1]
        c[k-1] = lam
    return c, d, e

def LUsolve3(c, d, e, b):
    n = len(d)
    for k in range(1, n):
        b[k] = b[k] - c[k-1]*b[k-1]
    b[n-1] = b[n-1] / d[n-1]
    for k in range(n-2, -1, -1):
        b[k] = (b[k] - e[k]*b[k+1]) / d[k]
    return b

# --- Cubic Spline ---
def curvatures(xData, yData):
    n = len(xData) - 1
    c = np.zeros(n)
    d = np.ones(n + 1)
    e = np.zeros(n)
    k = np.zeros(n + 1)
    c[0:n-1] = xData[0:n-1] - xData[1:n]
    d[1:n] = 2.0 * (xData[0:n-1] - xData[2:n+1])
    e[1:n] = xData[1:n] - xData[2:n+1]
    k[1:n] = 6.0*(yData[0:n-1] - yData[1:n]) \
             / (xData[0:n-1] - xData[1:n]) \
             - 6.0*(yData[1:n] - yData[2:n+1]) \
             / (xData[1:n] - xData[2:n+1])
    LUdecomp3(c, d, e)
    LUsolve3(c, d, e, k)
    return k

def evalSpline(xData, yData, k, x):
    def findSegment(xData, x):
        iLeft = 0
        iRight = len(xData) - 1
        while 1:
            if (iRight - iLeft) <= 1: return iLeft
            i = (iLeft + iRight) // 2
            if x < xData[i]: iRight = i
            else:             iLeft = i
    i = findSegment(xData, x)
    h = xData[i] - xData[i+1]
    y = ((x - xData[i+1])**3/h - (x - xData[i+1])*h)*k[i]/6.0 \
      - ((x - xData[i])**3/h   - (x - xData[i])*h)  *k[i+1]/6.0 \
      + (yData[i]*(x - xData[i+1]) - yData[i+1]*(x - xData[i])) / h
    return y

# --- Regression ---
def quadratic_regression(xData, yData, xEval):
    n = len(xData)
    s0 = float(n)
    s1 = sum(xData);       s2 = sum(x**2 for x in xData)
    s3 = sum(x**3 for x in xData); s4 = sum(x**4 for x in xData)
    r0 = sum(yData)
    r1 = sum(xData[i]*yData[i] for i in range(n))
    r2 = sum(xData[i]**2*yData[i] for i in range(n))
    A = np.array([[s0,s1,s2],[s1,s2,s3],[s2,s3,s4]], dtype=float)
    r = np.array([r0,r1,r2], dtype=float)
    c = gaussElimin(A, r)
    return [float(c[0] + c[1]*x + c[2]*x**2) for x in xEval]

def cubic_regression(xData, yData, xEval):
    n = len(xData)
    s0 = float(n)
    s1 = sum(xData);       s2 = sum(x**2 for x in xData)
    s3 = sum(x**3 for x in xData); s4 = sum(x**4 for x in xData)
    s5 = sum(x**5 for x in xData); s6 = sum(x**6 for x in xData)
    r0 = sum(yData)
    r1 = sum(xData[i]*yData[i] for i in range(n))
    r2 = sum(xData[i]**2*yData[i] for i in range(n))
    r3 = sum(xData[i]**3*yData[i] for i in range(n))
    A = np.array([[s0,s1,s2,s3],[s1,s2,s3,s4],[s2,s3,s4,s5],[s3,s4,s5,s6]], dtype=float)
    r = np.array([r0,r1,r2,r3], dtype=float)
    c = gaussElimin(A, r)
    return [float(c[0] + c[1]*x + c[2]*x**2 + c[3]*x**3) for x in xEval]

# --- Run ---
k = curvatures(xData, yData)
quad = quadratic_regression(xData, yData, Eval)
cub  = cubic_regression(xData, yData, Eval)

print("Viscosity Interpolation Results\n" + "-"*45)
for i, x in enumerate(Eval):
    spline = evalSpline(xData, yData, k, x)
    print(f"Cubic Spline      at {x:3d} C = {spline:.10f} m^2/s")
    print(f"Quadratic Reg.    at {x:3d} C = {quad[i]:.10f} m^2/s")
    print(f"Cubic Reg.        at {x:3d} C = {cub[i]:.10f} m^2/s")
    print(f"Spline - Cubic    at {x:3d} C = {spline - cub[i]:.10f} m^2/s")
    print()




