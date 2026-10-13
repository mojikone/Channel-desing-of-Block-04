import geopandas as gpd, rasterio, numpy as np
from shapely.geometry import Point
from shapely.ops import linemerge
P="D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/SHP/temp/CH WALL for HMS channels/"
T="D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/HEC_HMS_Block_04/terrain/NSA_5m_B04_Res10m/00/"
ch=gpd.read_file(P+"CH.shp"); dem=rasterio.open(T+"elevation.tif")
def z(p):
    v=list(dem.sample([(p.x,p.y)]))[0][0]; return float(v) if v<1e30 else np.nan
ch["geom2"]=ch.geometry.apply(lambda g: linemerge(g) if g.geom_type=="MultiLineString" else g)
ch["is_channel"]=ch["CHtt"].fillna("").str.contains("CH")
rows=[]
for i,r in ch.iterrows():
    g=r.geom2; a=Point(g.coords[0][:2]); b=Point(g.coords[-1][:2]); za,zb=z(a),z(b)
    # downstream end: nan (sea) beats lower z
    if np.isnan(zb) and not np.isnan(za): ds,us="end","start"
    elif np.isnan(za) and not np.isnan(zb): ds,us="start","end"
    else: ds,us=("end","start") if zb<=za else ("start","end")
    dpt = b if ds=="end" else a; upt = a if ds=="end" else b
    rows.append(dict(i=i, tt=r.CHtt, chan=r.is_channel, L=round(g.length/1000,2), ds_end=ds, zd=round(zb if ds=="end" else za,1), zu=round(za if ds=="end" else zb,1), dpt=dpt, upt=upt))
import pandas as pd; df=pd.DataFrame(rows)
# where does each downstream end land? on another CH line (within 15 m), at nodata (sea), or free
tol=15
for k,r in df.iterrows():
    hits=[j for j,g in ch.geom2.items() if j!=r.i and g.distance(r.dpt)<tol]
    sea=np.isnan(r.zd)
    df.loc[k,"lands_on"]=("SEA" if sea else "") + ("/".join("CH%d"%j for j in hits) if hits else ("" if sea else "FREE"))
    df.loc[k,"dist_to_hit"]=round(min([ch.geom2[j].distance(r.dpt) for j in hits]),1) if hits else None
    # also: does the upstream end sit on another line (i.e. this is a branch starting from a channel)?
    uh=[j for j,g in ch.geom2.items() if j!=r.i and g.distance(r.upt)<tol]
    df.loc[k,"up_on"]="/".join("CH%d"%j for j in uh)
pd.set_option("display.width",250); pd.set_option("display.max_rows",100)
print(df.drop(columns=["dpt","upt"]).to_string())
print("\nchannels:", df.chan.sum(), " non-channel (mountain burns/dyke):", (~df.chan).sum())
print("downstream ends FREE (neither sea nor another channel):", df[df.lands_on=="FREE"].i.tolist())
df["dx"]=df.dpt.apply(lambda p:p.x); df["dy"]=df.dpt.apply(lambda p:p.y)
df.drop(columns=["dpt","upt"]).to_csv("ch_topology.csv", index=False)
