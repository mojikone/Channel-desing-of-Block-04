import rasterio, numpy as np, geopandas as gpd
from rasterio.features import rasterize
from scipy.ndimage import distance_transform_edt
T="D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/HEC_HMS_Block_04/terrain/NSA_5m_B04_Res10m/00/"
S="D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/SHP/for HMS/1/"
with rasterio.open(T+"elevation.tif") as s: el=s.read(1); tr=s.transform; shp=s.shape
with rasterio.open(T+"reconditioned.tif") as s: rc=s.read(1)
valid=(el<1e30)&(rc<1e30); d=np.where(valid, rc-el, 0)
burn=rasterize(((g,1) for g in gpd.read_file(S+"Burn.shp").geometry), out_shape=shp, transform=tr, dtype=np.uint8).astype(bool)
wall=rasterize(((g,1) for g in gpd.read_file(S+"Wall.shp").geometry), out_shape=shp, transform=tr, dtype=np.uint8).astype(bool)
dist=distance_transform_edt(~burn)
target=-d*(d<0); mask=(d<=0)&valid&~wall
# HMS ring membership by observed value
for val,k in [(3.75,1),(2.5,2),(1.25,3)]:
    sel=(np.round(target,3)==val)&mask
    print(f"HMS ring {val}: n={sel.sum()}, edt dist min {dist[sel].min():.3f} max {dist[sel].max():.3f} mean {dist[sel].mean():.3f}")
far=(target==0)&mask&(dist<=3.6); print("cells within edt 3.6 with NO burn effect:", far.sum(), "dist min", dist[far].min() if far.any() else None)
# try bins by thresholds
for bins in [(1.5,2.5,3.5),(1.42,2.3,3.2),(1.0,2.0,3.0),(1.5,2.83,3.61)]:
    m=np.zeros(shp,np.float32); m[burn]=1005
    m[(dist>0)&(dist<=bins[0])&~burn]=3.75; m[(dist>bins[0])&(dist<=bins[1])]=2.5; m[(dist>bins[1])&(dist<=bins[2])]=1.25
    print("bins",bins,"mismatch", ((np.round(m,3)!=np.round(target,3))&mask).sum())
