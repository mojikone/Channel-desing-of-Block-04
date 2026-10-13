import geopandas as gpd, pandas as pd, numpy as np, rasterio, sys
from shapely.geometry import LineString, Point, box
sys.path.insert(0,'.'); from d8lib import downstream_index, DR, DC
pd.set_option("display.width",250); pd.set_option("display.max_rows",200)
W2=(sys.argv[1].rstrip("/\\")+"/") if len(sys.argv)>1 else "D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Claude Block 04/W2/output/hms/"
P="D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/SHP/temp/CH WALL for HMS channels/"
sub=gpd.read_file(W2+"Basin_2_review.gpkg", layer="subbasins_new"); wall=gpd.read_file(P+"WALL.shp"); ch=gpd.read_file(P+"CH.shp")
sub["geometry"]=sub.geometry.make_valid()
wall_u=wall.geometry.union_all() if hasattr(wall.geometry,"union_all") else wall.geometry.unary_union
rows=[]
for r in sub.itertuples():
    inner=r.geometry.buffer(-15)
    inside=wall_u.intersection(inner).length if not inner.is_empty else 0.0
    onb=wall_u.intersection(r.geometry.buffer(15).difference(inner)).length if not inner.is_empty else wall_u.intersection(r.geometry.buffer(15)).length
    rows.append(dict(S=r.S, area_km2=round(r.area_km2,2), ch_type=r.ch_type, wall_inside_m=round(inside), wall_on_boundary_m=round(onb)))
df=pd.DataFrame(rows); bad=df[df.wall_inside_m>100].sort_values("wall_inside_m",ascending=False)
print(f"new subbasins: {len(df)} | with >100 m of wall running through the interior: {len(bad)} | total interior wall length {bad.wall_inside_m.sum()/1000:.1f} km")
print(bad.to_string(index=False)); df.to_csv(W2+"wall_inside_subbasins.csv", index=False)
# ---- flow arcs crossing walls (new grid) ----
with rasterio.open("new/d8.tif") as s: w=s.read(1); tr=s.transform; H,W=w.shape
fd=np.full((H,W),-32768,np.int16)
for k,v in {1:2,2:1,4:8,8:7,16:6,32:5,64:4,128:3}.items(): fd[w==k]=v
ds=downstream_index(fd,-32768)
wc=np.load("new/wall_center.npy"); cc=np.load("new/ch_center.npy")
# candidate arcs: from a non-wall cell within 1 cell of a wall cell
from scipy.ndimage import binary_dilation
near=binary_dilation(wc, structure=np.ones((3,3),bool)) & ~wc
idx=np.flatnonzero(near.ravel()); idx=idx[ds[idx]>=0]
xs=lambda c: tr.c+(c%W+0.5)*tr.a; ys=lambda c: tr.f+(c//W+0.5)*tr.e
arcs=[]
for c in idx:
    d=int(ds[c]); seg=LineString([(xs(c),ys(c)),(xs(d),ys(d))])
    if seg.intersects(wall_u):
        kind="through burn cell" if (cc.ravel()[c] or cc.ravel()[d]) else ("into wall cell" if wc.ravel()[d] else "diagonal between two wall cells")
        arcs.append(dict(geometry=seg, kind=kind, x=xs(c), y=ys(c)))
A=gpd.GeoDataFrame(arcs, crs="EPSG:32640"); print("\nflow arcs crossing a wall line:", len(A)); print(A.kind.value_counts().to_string())
A=gpd.sjoin(A, sub[["S","geometry"]], how="left", predicate="within")
print("\ncrossings per subbasin (top 25):"); print(A.groupby(["S","kind"]).size().unstack(fill_value=0).assign(total=lambda t:t.sum(axis=1)).sort_values("total",ascending=False).head(25).to_string())
A.drop(columns=["index_right"],errors="ignore").to_file(W2+"Basin_2_review.gpkg", layer="wall_crossings", driver="GPKG")
# ---- S124 picture ----
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
s=sub[sub.S=="S124"].iloc[0]; b=s.geometry.buffer(400).bounds
fig,ax=plt.subplots(figsize=(11,11)); sub.cx[b[0]:b[2],b[1]:b[3]].boundary.plot(ax=ax,color="grey",lw=0.8)
gpd.GeoSeries([s.geometry]).plot(ax=ax,color="none",edgecolor="red",lw=2)
wall.cx[b[0]:b[2],b[1]:b[3]].plot(ax=ax,color="black",lw=2); ch.cx[b[0]:b[2],b[1]:b[3]].plot(ax=ax,color="blue",lw=1.5)
A.cx[b[0]:b[2],b[1]:b[3]].plot(ax=ax,color="magenta",lw=3)
for r in sub.cx[b[0]:b[2],b[1]:b[3]].itertuples(): ax.annotate(r.S,(r.geometry.representative_point().x,r.geometry.representative_point().y),fontsize=9)
for i,r in wall.cx[b[0]:b[2],b[1]:b[3]].iterrows(): ax.annotate(f"W{i}",(r.geometry.interpolate(0.5,normalized=True).x,r.geometry.interpolate(0.5,normalized=True).y),color="black",fontsize=8,fontweight="bold")
for i,r in ch.cx[b[0]:b[2],b[1]:b[3]].iterrows(): ax.annotate(f"CH{i}",(r.geometry.interpolate(0.5,normalized=True).x,r.geometry.interpolate(0.5,normalized=True).y),color="blue",fontsize=8)
ax.set_xlim(b[0],b[2]); ax.set_ylim(b[1],b[3]); ax.set_title("S124 (red): walls black, channels blue, flow arcs crossing walls magenta"); ax.set_aspect("equal")
plt.savefig("s124.png",dpi=110,bbox_inches="tight"); print("\nS124 map saved")
