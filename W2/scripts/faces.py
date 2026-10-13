import re
import sqlite3, geopandas as gpd, pandas as pd, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from shapely import wkb
from shapely.ops import polygonize, unary_union, nearest_points
from shapely.geometry import LineString, Point
U="D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Claude Block 04/W2/output/hms/user_edited_20261005/"
P="D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/SHP/temp/CH WALL for HMS channels/"
red=gpd.read_file("georef/red_lines.gpkg"); wall=gpd.read_file(P+"WALL.shp"); ch=gpd.read_file(P+"CH.shp")
cu=sqlite3.connect(U+"Basin_2.sqlite"); poly=gpd.GeoDataFrame([dict(name=n, geometry=wkb.loads(g)) for g,n in cu.execute("select GEOMETRY,name from subbasin2d")], crs="EPSG:32640")
faces=[]; vw=[]
for k,grp in red.groupby("img"):
    lines=list(grp.geometry); bridges=[]
    for i,g in enumerate(lines):
        a,b=Point(g.coords[0]),Point(g.coords[-1])
        if 0.5<a.distance(b)<=300: bridges.append(LineString([a,b]))          # a loop drawn as one stroke
        for pt in (a,b):
            others=[h for j,h in enumerate(lines) if j!=i]
            if not others: continue
            d=[h.distance(pt) for h in others]; j=int(np.argmin(d))
            if 0.5<d[j]<=300: bridges.append(LineString([pt, nearest_points(pt, others[j])[1]]))
    if k in (10,): vw.extend(lines+bridges)   # "as shown": the latest loops are hard boundaries
    from shapely.ops import snap
    merged=unary_union(lines+bridges); merged=unary_union(snap(merged, merged, 5)); polys=[p for p in polygonize(merged) if p.area>2e5]
    for i,p in enumerate(polys): faces.append(dict(src=f"img{k}", face=i, kind="red loop", geometry=p, area_km2=round(p.area/1e6,2)))
    b=grp.total_bounds; b=(b[0]-500,b[1]-500,b[2]+500,b[3]+500)
    fig,ax=plt.subplots(figsize=(10,10*(b[3]-b[1])/(b[2]-b[0]))); poly.cx[b[0]:b[2],b[1]:b[3]].plot(ax=ax,color="#eeffee",edgecolor="grey",lw=0.6)
    wall.cx[b[0]:b[2],b[1]:b[3]].plot(ax=ax,color="black",lw=1.5); ch.cx[b[0]:b[2],b[1]:b[3]].plot(ax=ax,color="blue",lw=1)
    if polys: gpd.GeoSeries(polys).plot(ax=ax,alpha=0.35,color=plt.cm.tab10(np.arange(len(polys))%10),edgecolor="red",lw=2)
    for i,p in enumerate(polys): ax.annotate(f"face {i}: {p.area/1e6:.1f} km2",(p.representative_point().x,p.representative_point().y),fontsize=10,fontweight="bold")
    grp.plot(ax=ax,color="red",lw=1); 
    if bridges: gpd.GeoSeries(bridges).plot(ax=ax,color="magenta",lw=3)
    for r in poly.cx[b[0]:b[2],b[1]:b[3]].itertuples(): ax.annotate(r.name,(r.geometry.representative_point().x,r.geometry.representative_point().y),fontsize=7,color="darkgreen")
    ax.set_xlim(b[0],b[2]); ax.set_ylim(b[1],b[3]); ax.set_aspect("equal"); ax.set_title(f"screenshot {k}: faces of the red loops (bridged gaps magenta)")
    plt.savefig(f"georef/faces_{k}.png",dpi=90,bbox_inches="tight"); plt.close()
F=gpd.GeoDataFrame(faces, crs="EPSG:32640")
gpd.GeoDataFrame(geometry=vw, crs="EPSG:32640").to_file("georef/faces.gpkg", layer="vwalls", driver="GPKG")
# + the engineer's own HMS merges (their current polygons, named Subbasin-n in his latest saved model) and S111 -> S16
from shapely import wkb
UC="D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Claude Block 04/W2/output/hms/user_edited_20261005c/"
cc=sqlite3.connect(UC+"Basin_2.sqlite"); txtc=open(UC+"Basin_2.basin",encoding="utf-8",errors="replace").read()
subs_c=set(re.findall(r'^Subbasin: (.+?)$', txtc, re.M))
extra=[dict(src="user HMS merge", face=n, kind="user merge", geometry=wkb.loads(g).buffer(0), area_km2=0) for g,n in cc.execute("select GEOMETRY,name from subbasin2d") if n.startswith("Subbasin-") and n in subs_c]
ue={n:wkb.loads(g) for g,n in cu.execute("select GEOMETRY,name from subbasin2d")}
extra.append(dict(src="img8", face="S111->S16", kind="merge into Basin 1 S16", geometry=ue["S111"].buffer(0), area_km2=0))
F=pd.concat([F, gpd.GeoDataFrame(extra, crs="EPSG:32640")], ignore_index=True); F["area_km2"]=(F.geometry.area/1e6).round(2)
print(F.drop(columns="geometry").to_string(index=False))
F.to_file("georef/merge_regions.gpkg", layer="regions", driver="GPKG")
