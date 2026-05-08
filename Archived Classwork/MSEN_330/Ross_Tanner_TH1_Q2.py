import numpy as np

n = 10
A = np.zeros((n, n))
b = np.ones(n)


A[0,0] = 7
A[0,1] = -4
A[0,2] = 1

A[1,0] = -4
A[1,1] = 6
A[1,2] = -4
A[1,3] = 1

for i in range(2, 8):
    A[i,i-2] = 1
    A[i,i-1] = -4
    A[i,i]   = 6
    A[i,i+1] = -4
    A[i,i+2] = 1

A[8,6] = 1
A[8,7] = -4
A[8,8] = 6
A[8,9] = -4

A[9,7] = 1
A[9,8] = -4
A[9,9] = 7

for k in range(n-1):
    for i in range(k+1,n):
        if A[i,k] != 0:
            factor = A[i,k]/A[k,k]
            A[i,k:] -= factor*A[k,k:]
            b[i] -= factor*b[k]

x = np.zeros(n)
for i in range(n-1, -1, -1):
    x[i] = (b[i]-np.dot(A[i,i+1:], x[i+1:]))/A[i,i]

print(x)