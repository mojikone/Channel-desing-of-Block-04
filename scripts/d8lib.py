import numpy as np, numba as nb
# TauDEM-style: 1=E 2=NE 3=N 4=NW 5=W 6=SW 7=S 8=SE  (dr, dc)
DR = np.array([0, 0,-1,-1,-1, 0, 1, 1, 1], dtype=np.int64)
DC = np.array([0, 1, 1, 0,-1,-1,-1, 0, 1], dtype=np.int64)
@nb.njit(cache=True)
def downstream_index(fd, nod):
    H,W = fd.shape; ds = np.full(H*W, -1, np.int64)
    for r in range(H):
        for c in range(W):
            d = fd[r,c]
            if d==nod or d<1 or d>8: continue
            rr=r+DR[d]; cc=c+DC[d]
            if 0<=rr<H and 0<=cc<W and fd[rr,cc]!=nod: ds[r*W+c]=rr*W+cc
    return ds
@nb.njit(cache=True)
def upstream_csr(ds):
    n=ds.size; cnt=np.zeros(n+1, np.int64)
    for i in range(n):
        if ds[i]>=0: cnt[ds[i]+1]+=1
    for i in range(n): cnt[i+1]+=cnt[i]
    fill=cnt[:-1].copy(); up=np.empty(n, np.int64)
    for i in range(n):
        j=ds[i]
        if j>=0: up[fill[j]]=i; fill[j]+=1
    return cnt, up
@nb.njit(cache=True)
def watershed(seed, cnt, up, label, lab):
    """label all cells draining to seed (stop at cells already labelled with another id? no: pure upstream)"""
    stack=[seed]; n=0
    while len(stack):
        i=stack.pop()
        if label[i]!=0: continue
        label[i]=lab; n+=1
        for k in range(cnt[i], cnt[i+1]): 
            if label[up[k]]==0: stack.append(up[k])
    return n
@nb.njit(cache=True)
def accum(ds, order_dummy):
    n=ds.size; acc=np.ones(n, np.int64); indeg=np.zeros(n, np.int64)
    for i in range(n):
        if ds[i]>=0: indeg[ds[i]]+=1
    q=np.empty(n, np.int64); h=0; t=0
    for i in range(n):
        if indeg[i]==0: q[t]=i; t+=1
    while h<t:
        i=q[h]; h+=1; j=ds[i]
        if j>=0:
            acc[j]+=acc[i]; indeg[j]-=1
            if indeg[j]==0: q[t]=j; t+=1
    return acc
