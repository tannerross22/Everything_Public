import numpy as np
np.set_printoptions(precision=10, suppress=True)

A = np.array([[3, -2, 1, 0, 0, 1],
              [-2, 4, -2, 1, 0, 0],
              [1, -2, 4, -2, 1, 0],
              [0, 1, -2, 4, -2, 1],
              [0, 0, 1, -2, 4, -2],
              [1, 0, 0, 1, -2, 3]])

b = [10, -8, 10, 10, -8, 10]

#Direct method (cholseky)
import numpy as np


def cholesky(A, b):
    n = len(b)
    L = np.zeros((n, n))
    for i in range(n):
        for j in range(i+1):
            s = sum(L[i,k] * L[j,k] for k in range(j))
            if i == j:
                L[i,j] = np.sqrt(A[i,i] - s)
            else:
                L[i,j] = (A[i,j]-s)/L[j,j]

    y = np.zeros(n)
    for i in range(n):
        y[i] = (b[i]-sum(L[i,j]*y[j]for j in range(i))) / L[i,i]

    x = np.zeros(n)
    for i in reversed(range(n)):
        x[i] = (y[i] - sum(L[j, i] * x[j] for j in range(i + 1, n))) / L[i, i]

    return x

print(f'Directly solved with Cholesky: {cholesky(A, b)}')


#Gauss Seidel Method
def gauss_seidel(A, b, tol=1e-9, max_iter=100000):
    n = len(b)
    x = np.zeros(n)
    x_old = np.zeros(n)
    for iteration in range(max_iter):
        x_old[:] = x[:]

        for i in range(n):
            s1 = sum(A[i,j]*x[j] for j in range(i))
            s2 = sum(A[i,j]*x_old[j] for j in range(i + 1, n))

            x[i] = (b[i]-s1-s2)/A[i,i]

        #stopping
        if np.max(np.abs(x - x_old)) < tol:
            print("Converged in", iteration + 1, "iterations")
            return x


    print("Did not converge")
    return x
print(f'Indirectly solved with Gauss-Seidel: {gauss_seidel(A, b)}')