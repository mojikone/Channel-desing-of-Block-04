import sys, re, geopandas as gpd, pandas as pd, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from shapely.geometry import Point
N=sys.argv[1].rstrip("/\\")+"/"; OUTD=sys.argv[2].rstrip("/\\")+"/"
P="D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/SHP/temp/CH WALL for HMS channels/"
sub=gpd.read_file(N+"Basin_2_review.gpkg", layer="subbasins_new"); b1=gpd.read_file(N+"Basin_2_review.gpkg", layer="subbasins_basin1_carried_over")
jn=gpd.read_file(N+"Basin_2_review.gpkg", layer="junctions"); rch=gpd.read_file(N+"Basin_2_review.gpkg", layer="reaches_new")
wall=gpd.read_file(P+"WALL.shp"); ch=gpd.read_file(P+"CH.shp"); red=gpd.read_file("georef/red_lines.gpkg")
for k,grp in red.groupby("img"):
    b=grp.total_bounds; b=(b[0]-700,b[1]-700,b[2]+700,b[3]+700)
    fig,ax=plt.subplots(figsize=(11,11*(b[3]-b[1])/(b[2]-b[0])))
    b1.cx[b[0]:b[2],b[1]:b[3]].plot(ax=ax,color="#e8e8e8",edgecolor="grey",lw=0.6)
    s=sub.cx[b[0]:b[2],b[1]:b[3]]; s.plot(ax=ax,color=plt.cm.Pastel1(np.arange(len(s))%9),edgecolor="black",lw=0.8,alpha=0.9)
    wall.cx[b[0]:b[2],b[1]:b[3]].plot(ax=ax,color="black",lw=1.8); ch.cx[b[0]:b[2],b[1]:b[3]].plot(ax=ax,color="blue",lw=1)
    rch.cx[b[0]:b[2],b[1]:b[3]].plot(ax=ax,color="navy",lw=1.5,linestyle="--")
    grp.plot(ax=ax,color="red",lw=1.2,alpha=0.7)
    for r in s.itertuples(): ax.annotate(f"{r.S}\n{r.area_km2:.1f}",(r.geometry.representative_point().x,r.geometry.representative_point().y),fontsize=7,ha="center",color="darkgreen")
    for r in jn.cx[b[0]:b[2],b[1]:b[3]].itertuples(): ax.plot(r.geometry.x,r.geometry.y,"s",color="navy",ms=4); ax.annotate(r.name,(r.geometry.x,r.geometry.y),fontsize=6,color="navy")
    ax.set_xlim(b[0],b[2]); ax.set_ylim(b[1],b[3]); ax.set_aspect("equal"); ax.set_title(f"screenshot {k} area: NEW Basin 2 (your red lines thin red; reaches dashed navy)")
    plt.savefig(f"{OUTD}result_{k}.png",dpi=100,bbox_inches="tight"); plt.close()
print("result overlays written to", OUTD)
