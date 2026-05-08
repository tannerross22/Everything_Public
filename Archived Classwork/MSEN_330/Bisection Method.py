def bisection(f, a, b, tol = 1*10^-5, iter = 100):
    if f(a)*f(b) > 0:
        print("No root guaranteed")
        return None
    for i in range(iter):
        mid = a + (b-a)/2
        value = f(mid)
        if abs(value) < tol:
            print(i,value,mid)
            return mid
        if f(a) * value <0:
            print(i,value,mid)
            b = mid
        else:
            print(i,value,mid)
            a = mid

    return (a+b)/2

def f(x):
    return 5*x**3 + 3*x**2+27*x - 15
a = float(input("Guess for a: "))
b = float(input("Guess for b: "))
print(bisection(f, a, b))

