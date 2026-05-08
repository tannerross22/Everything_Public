import numpy as np

a = np.array([[2,-1,0],[-1,2,-1],[0,-1,2]])
b = np.array([[1,0,0],[0,1,0],[0,0,1]])
def gaussElim(a,b):
    n = a.shape[0]
    a = a.astype(float)
    b = b.astype(float)
    for k in range(0,n-1):
        for i in range(k+1,n):
            if a[i,k] != 0:
                lam = a[i,k]/a[k,k]
                a[i,k+1:n] = a[i,k+1:n]-lam*a[k,k+1:n]
                b[i, :] -= lam * b[k, :]
    for k in range(n-1,-1,-1):
        b[k,:] = (b[k,:] - a[k, k+1:n] @ b[k+1:n,:]) / a[k,k]

    return b

print(gaussElim(a,b))