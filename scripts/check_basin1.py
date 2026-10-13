import rasterio, numpy as np, re, time, sys
sys.path.insert(0,'.')
from d8lib import *
T="D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/HEC_HMS_Block_04/terrain/NSA_5m_B04_Res10m/00/"
t=time.time()
with rasterio.open(T+"flowdir.tif") as s: fd=s.read(1); tr=s.transform; nod=int(s.nodata)
with rasterio.open(T+"sinkfill.tif") as s: sf=s.read(1)
with rasterio.open(T+"flowaccum.tif") as s: fa=s.read(1)
H,W=fd.shape
# encoding check: does target have lower-or-equal sinkfill?
ok=0; tot=0; rng=np.random.default_rng(0)
for r,c in zip(rng.integers(0,H,20000), rng.integers(0,W,20000)):
    d=fd[r,c]
    if d==nod: continue
    rr,cc=r+DR[d],c+DC[d]
    if 0<=rr<H and 0<=cc<W and sf[rr,cc]>-1e30 and sf[r,c]>-1e30:
        tot+=1; ok+= sf[rr,cc]<=sf[r,c]+1e-3
print("encoding check: target not higher in", ok, "of", tot)
ds=downstream_index(fd, nod); cnt,up=upstream_csr(ds); print("graph built", round(time.time()-t,1),"s")
acc=accum(ds,0); print("my accum max", acc.max(), "HMS flowaccum max", fa.max())
# Basin 1 network
txt=open("D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/HEC_HMS_Block_04/Basin_1.basin",encoding="utf-8",errors="replace").read()
blocks=re.findall(r'^(Subbasin|Junction|Reach): (.+?)\n(.*?)^End:', txt, re.S|re.M)
def g(b,k):
    m=re.search(r'^\s*'+re.escape(k)+r': (.*)$', b, re.M); return m.group(1).strip() if m else None
el={n:(t,float(g(b,"Canvas X")),float(g(b,"Canvas Y")),g(b,"Downstream"),float(g(b,"Area") or 0)) for t,n,b in blocks}
# upstream area of each junction by topology
def up_area(n):
    return sum(up_area(m)+el[m][4] if el[m][0]=="Subbasin" else up_area(m) for m in el if el[m][3]==n)
print(f"{'junction':14s} {'HMS_area':>9s} {'D8_area':>9s} {'snap(cells)':>11s} {'HMSacc':>8s}")
for n,(t,x,y,dsn,a) in el.items():
    if t!="Junction": continue
    c,r=~tr*(x,y); r,c=int(r),int(c)
    # snap to max flowaccum within 3 cells
    win=fa[max(r-3,0):r+4, max(c-3,0):c+4]; k=np.unravel_index(np.argmax(win),win.shape); rs,cs=max(r-3,0)+k[0], max(c-3,0)+k[1]
    label=np.zeros(H*W, np.int8); nc=watershed(rs*W+cs, cnt, up, label, 1)
    print(f"{n:14s} {up_area(n):9.3f} {nc*100/1e6:9.3f} {abs(rs-r)+abs(cs-c):11d} {fa[rs,cs]*100/1e6:8.1f}")
print("done", round(time.time()-t,1),"s")
