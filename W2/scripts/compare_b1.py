"""Match delineated subbasins to Basin 1 polygons and compare area, longest flow path and 10-85 slope."""
import sqlite3, sys, geopandas as gpd, pandas as pd, numpy as np
from shapely import wkb
HMS = "D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/HEC_HMS_Block_04/"
N = sys.argv[1].rstrip("/\\") + "/"
c = sqlite3.connect(HMS + "Basin_1.sqlite")
b1 = gpd.GeoDataFrame([dict(name=n, geometry=wkb.loads(g)) for g, n in c.execute("select GEOMETRY, name from subbasin2d")], crs="EPSG:32640")
st = pd.DataFrame(c.execute("select subbasin_name, longest_length, [10_85_length], [10_85_slope] from subbasin_statistics").fetchall(),
                  columns=["name", "b1_Lfp", "b1_L1085", "b1_S1085"]).astype({"b1_Lfp": float, "b1_L1085": float, "b1_S1085": float})
b1 = b1.merge(st, on="name"); b1["b1_area"] = b1.geometry.area / 1e6
me = gpd.read_file(N + "out/review.gpkg", layer="subbasins")
rows = []
for r in b1.itertuples():
    inter = me.geometry.make_valid().intersection(r.geometry.buffer(0)).area / 1e6
    k = int(inter.idxmax()); m = me.loc[k]
    rows.append(dict(b1=r.name, b1_area=round(r.b1_area, 2), mine=m["sub"], my_area=round(m.area_km2, 2), overlap=round(inter[k] / max(r.b1_area, m.area_km2), 3),
                     b1_Lfp=round(r.b1_Lfp), my_Lfp=round(m.Lfp_m), b1_S1085=round(r.b1_S1085, 5), my_S1085=round(m.S1085, 5),
                     my_CN=round(m.CN, 1), my_lag=round(m.Lag_min, 1)))
df = pd.DataFrame(rows).sort_values("b1", key=lambda s: s.str[1:].astype(int))
pd.set_option("display.width", 250); print(df.to_string(index=False))
# Basin 1 CN / lag from basin file for reference
import re
txt = open(HMS + "Basin_1.basin", encoding="utf-8", errors="replace").read()
b1p = {n: (float(cn), float(lag)) for n, cn, lag in re.findall(r'^Subbasin: (\S+)\n.*?Curve Number: (\S+)\n.*?Lag: (\S+)', txt, re.S | re.M)}
df["b1_CN"] = df.b1.map(lambda n: b1p[n][0]); df["b1_lag"] = df.b1.map(lambda n: b1p[n][1])
print("\nCN and lag, Basin 1 vs recomputed (Kirpich on 10-85):")
print(df[["b1", "b1_CN", "my_CN", "b1_lag", "my_lag", "b1_S1085", "my_S1085"]].to_string(index=False))
df.to_csv(N + "out/compare_basin1.csv", index=False)
