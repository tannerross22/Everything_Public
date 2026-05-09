#%%
import numpy as np
## module trapezoid
''' Inew = trapezoid(f,a,b,Iold,k).
    Recursive trapezoidal rule:
    Iold = Integral of f(x) from x = a to b computed by
    trapezoidal rule with 2^(k-1) panels.
    Inew = Same integral computed with 2^k panels.
'''
def trapezoid(f,a,b,Iold,k):
    if k == 1:Inew = (f(a) + f(b))*(b - a)/2.0
    else:
        n = 2**(k -2 )      # Number of new points
        h = (b - a)/n       # Spacing of new points
        x = a + h/2.0       # Coord. of 1st new point
        sum = 0.0
        for i in range(n):
            sum = sum + f(x)
            x = x + h
        Inew = (Iold + h*sum)/2.0
    return Inew

def f(x):
    return np.log(1 + np.tan(x))

a, b    = 0.0, np.pi/4
tol     = 1.0e-9
Iold    = 0.0

print(f'{"k":>4}  {"Integral":>16}')

for k in range(1, 10):
    Inew = trapezoid(f, a, b, Iold, k)
    print(f'{k:>4}  {Inew:>16.9f}')
    if k > 1 and abs(Inew - Iold) < tol:
        print(f'\nConverged at k = {k}')
        print(f'Result  = {Inew:.9f}')
        print(f'Exact   = {np.pi*np.log(2)/8:.9f}')
        break
    Iold = Inew


print("Observations:\n The integral converges in only 1 iteration, and the function is very linear "
      "for x values < pi/4, so the area is approximately a triangle with base = height = pi/4")

#%%
import numpy as np

def simpson(f, a, b, n):

    h = (b - a) / n
    x = np.linspace(a, b, n+1)
    y = f(x)

    coeffs        = np.ones(n+1)
    coeffs[1:-1:2] = 4   # odd indices
    coeffs[2:-2:2] = 2   # even interior indices

    return np.dot(coeffs, y) * h/3

def f(x):
    return np.cos(2 * np.arccos(x))

a, b   = -1.0, 1.0

print(f'{"Panels"}  {"Integral"}')
for n in [2, 4, 6]:
    I = simpson(f, a, b, n)
    print(f'{n} {I}')

print("Observations\nThis function is equivalent to 2x^2-1, and for polynomials less than n=3, the results are exact, so converge to the result in 1 step at any number of panels")

#%%
## module romberg
''' I,nPanels = romberg(f,a,b,tol=1.0e-6).
    Romberg intergration of f(x) from x = a to b.
    Returns the integral and the number of panels used.
'''
import numpy as np
## module trapezoid
''' Inew = trapezoid(f,a,b,Iold,k).
    Recursive trapezoidal rule:
    Iold = Integral of f(x) from x = a to b computed by
    trapezoidal rule with 2^(k-1) panels.
    Inew = Same integral computed with 2^k panels.
'''
def trapezoid(f,a,b,Iold,k):
    if k == 1:Inew = (f(a) + f(b))*(b - a)/2.0
    else:
        n = 2**(k -2 )      # Number of new points
        h = (b - a)/n       # Spacing of new points
        x = a + h/2.0       # Coord. of 1st new point
        sum = 0.0
        for i in range(n):
            sum = sum + f(x)
            x = x + h
        Inew = (Iold + h*sum)/2.0
    return Inew

def romberg(f,a,b,tol=1.0e-6):

    def richardson(r,k):
        for j in range(k-1,0,-1):
            const = 4.0**(k-j)
            r[j] = (const*r[j+1] - r[j])/(const - 1.0)
        return r

    r = np.zeros(21)
    r[1] = trapezoid(f,a,b,0.0,1)
    r_old = r[1]
    for k in range(2,21):
        r[k] = trapezoid(f,a,b,r[k-1],k)
        r = richardson(r,k)
        if abs(r[1]-r_old) < tol*max(abs(r[1]),1.0):
            return r[1],2**(k-1)
        r_old = r[1]
    print("Romberg quadrature did not converge")

def f(x):
    return x**5 +3*x**3 - 2
a,b=0,2
print(f'Area of function: {romberg(f,a,b,tol=1.0e-6)[0]}')
#%%
