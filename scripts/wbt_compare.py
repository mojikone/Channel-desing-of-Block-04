import rasterio, numpy as np, re, sys, time
sys.path.insert(0,'.'); from d8lib import *
T="D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/HEC_HMS_Block_04/terrain/NSA_5m_B04_Res10m/00/"
with rasterio.open("wbt_hms/d8.tif") as s: w=s.read(1); tr=s.transform; wn=s.nodata
print("wbt d8 values", np.unique(w)[:12], "nodata", wn)
# whitebox (non-esri): 1=NE 2=E 4=SE 8=S 16=SW 32=W 64=NW 128=N  -> taudem 1=E 2=NE 3=N 4=NW 5=W 6=SW 7=S 8=SE
m={1:2,2:1,4:8,8:7,16:6,32:5,64:4,128:3}
fd=np.full(w.shape,-32768,np.int16)
for k,v in m.items(): fd[w==k]=v
ds=downstream_index(fd,-32768); cnt,up=upstream_csr(ds); acc=accum(ds,0); H,W=fd.shape
with rasterio.open(T+"flowaccum.tif") as s: fa=s.read(1)
txt=open("D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/HEC_HMS_Block_04/Basin_1.basin",encoding="utf-8",errors="replace").read()
J=re.findall(r'^Junction: (.+?)\n.*?Canvas X: (\S+)\n\s*Canvas Y: (\S+)', txt, re.S|re.M)
print(f"{'junction':14s} {'HMSgrid':>9s} {'WBT':>9s} {'diff':>7s}")
for n,x,y in J:
    c,r=~tr*(float(x),float(y)); r,c=int(r),int(c)
    win=fa[r-3:r+4,c-3:c+4]; k=np.unravel_index(np.argmax(win),win.shape); rs,cs=r-3+k[0],c-3+k[1]
    hms=fa[rs,cs]*100/1e6
    # on wbt grid snap to max acc within 3 cells
    win2=acc.reshape(H,W)[r-3:r+4,c-3:c+4]; k2=np.unravel_index(np.argmax(win2),win2.shape); r2,c2=r-3+k2[0],c-3+k2[1]
    wb=acc[r2*W+c2]*100/1e6
    print(f"{n:14s} {hms:9.3f} {wb:9.3f} {wb-hms:7.3f}")
