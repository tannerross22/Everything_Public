import numpy as np

n = 10
A = np.zeros((n, n))

for i in range(n):
    A[i,i] =4
    if i>0:
        A[i,i-1] = -1
    if i<n-1:
        A[i,i+1] = -1

b = np.full(n, 5.0)
b[0] = 9.0

# Doolittle
L = np.zeros((n, n))
U = np.zeros((n, n))

for i in range(n):
    L[i, i] = 1.0
    for j in range(i, n):
        U[i,j] = A[i,j] - sum(L[i,k] * U[k,j] for k in range(i))
    for j in range(i + 1, n):
        L[j, i] = (A[j, i] - sum(L[j, k] * U[k,i] for k in range(i))) / U[i,i]

y = np.zeros(n)
for i in range(n):
    y[i] = b[i] - sum(L[i, j]*y[j] for j in range(i))

x = np.zeros(n)
for i in reversed(range(n)):
    x[i] = (y[i] - sum(U[i, j]*x[j] for j in range(i + 1, n)))/U[i, i]

print("x=")
print(x)
