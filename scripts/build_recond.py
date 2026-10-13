import rasterio, numpy as np, geopandas as gpd, whitebox, os, time, sys
from rasterio.features import rasterize
from scipy.ndimage import distance_transform_edt
bins=tuple(float(x) for x in sys.argv[1].split(",")) if len(sys.argv)>1 else (1.5,2.5,3.5)
T="D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/HEC_HMS_Block_04/terrain/NSA_5m_B04_Res10m/00/"
P="D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/SHP/temp/CH WALL for HMS channels/"
O=os.path.abspath("new"); os.makedirs(O, exist_ok=True); t=time.time()
with rasterio.open(T+"elevation.tif") as s: el=s.read(1); prof=s.profile; tr=s.transform; shp=s.shape; nod=s.nodata
valid=el<1e30
def taper(lines, drop, all_touched=False):
    # walls: all_touched=True gives a 4-connected (diagonal-tight) line so D8 flow cannot slip between two
    # diagonally adjacent wall cells; burns stay 8-connected like HMS
    center=rasterize(((g,1) for g in lines), out_shape=shp, transform=tr, dtype=np.uint8, all_touched=all_touched).astype(bool)
    dist=distance_transform_edt(~center); m=np.zeros(shp,np.float32); m[center]=drop
    for lo,hi,v in [(0,bins[0],3.75),(bins[0],bins[1],2.5),(bins[1],bins[2],1.25)]:
        m[(dist>lo)&(dist<=hi)&~center]=v*np.sign(drop)
    return m, center
ch=gpd.read_file(P+"CH.shp"); wl=gpd.read_file(P+"WALL.shp")
# snap dyke ends that stop within one DEM cell (10 m) of another dyke; wider gaps are intended openings
from shapely.geometry import Point, LineString
from shapely.ops import linemerge, nearest_points
SNAP_M=10.0; extra=[]
for i,g in wl.geometry.items():
    gg=linemerge(g) if g.geom_type=="MultiLineString" else g
    for pt in (Point(gg.coords[0][:2]), Point(gg.coords[-1][:2])):
        others=wl.geometry.drop(i); d=others.distance(pt)
        if 0.0 < d.min() <= SNAP_M:
            q=nearest_points(pt, others.loc[d.idxmin()])[1]; extra.append(LineString([pt,q])); print(f"  snapped wall {i} end to wall {d.idxmin()} ({d.min():.1f} m)")
wall_lines=list(wl.geometry)+extra; print("wall gaps snapped:", len(extra))
mb,cb=taper(ch.geometry,-1005.0); mw,cw=taper(wall_lines,1005.0, all_touched=True)
# virtual walls: hand-drawn catchment boundaries (georeferenced red lines), raised like dykes but letting real wadis
# (accumulation >= VW_PASS_KM2 on the previous terrain) pass through
VW=[a for a in sys.argv if a.startswith("--vwalls=")]
if VW:
    vpath,layer=VW[0].split("=")[1].split(":"); VW_PASS_KM2=1.0
    vl=gpd.read_file(vpath, layer=layer); vl=vl[vl.img.isin([6,7])] if "img" in vl.columns else vl
    cv=rasterize(((g,1) for g in vl.geometry), out_shape=shp, transform=tr, dtype=np.uint8, all_touched=True).astype(bool)
    if os.path.exists(O+"/acc.tif"):
        with rasterio.open(O+"/acc.tif") as s: accp=s.read(1)
        passing=cv&(accp>=VW_PASS_KM2*1e6/100); cv&=~passing; print("virtual wall cells", cv.sum(), "| opened for wadis:", passing.sum())
    mw=np.where(cv&(mw==0), 1005.0, mw); cw=cw|cv
# HMS order: walls first, then burn (centre and taper) overrides wherever the burn touches
# priority: burn centre (the channel itself, i.e. a culvert through the dyke) > wall centre+taper > burn taper
mod=np.where(cb, mb, np.where(mw!=0, mw, mb))
rc=np.where(valid, el+mod, el).astype(np.float32)
prof.update(compress="lzw"); 
with rasterio.open(O+"/reconditioned.tif","w",**prof) as d: d.write(rc,1)
np.save(O+"/ch_center.npy", cb); np.save(O+"/wall_center.npy", cw)
print("recond written; burn cells", cb.sum(), "wall cells", cw.sum(), round(time.time()-t),"s")
wbt=whitebox.WhiteboxTools(); wbt.set_verbose_mode(False); wbt.set_working_dir(O)
wbt.fill_depressions("reconditioned.tif","fill.tif", fix_flats=True); print("fill", round(time.time()-t))
wbt.d8_pointer("fill.tif","d8.tif", esri_pntr=False); print("d8", round(time.time()-t))
wbt.d8_flow_accumulation("d8.tif","acc.tif", out_type="cells", pntr=True, esri_pntr=False); print("acc", round(time.time()-t))
