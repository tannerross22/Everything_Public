import math as m
import matplotlib.pyplot as plt
import numpy as np

N_max = 10
x_values = [0.1,0.5,1,5]
def f(x,N):
    result = 1
    for n in range(1,N+1):
        result += x**n/m.factorial(n)
    return result

print("x     N     f(x,N)")

error = []
for j in (x_values):
    for i in range(1,N_max+1):
        print (j,', ',i,', ',f(j,i))
        error.append(abs((f(j, i) - np.exp(j)) / np.exp((j)) * 100))
        i+=1
    plt.plot(range(1, N_max + 1), error)
    plt.title(f'Error at {j} for increasing N')
    plt.xlabel("N")
    plt.ylabel("True % Error")
    plt.xlim([1, N_max + 1])
    plt.show()
    error.clear()


