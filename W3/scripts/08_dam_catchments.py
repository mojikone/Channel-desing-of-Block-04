"""Step 08 - one polygon per dam catchment = union of the Basin 2 subbasins upstream of the dam junction.

Attributes: name (dam), area_km2 (polygon), hms_km2 (sum of HMS subbasin areas), cn_w (area-weighted curve number),
n_sub, junction x/y, FSL, crest (dams sheet). The same file goes to the RUSLE pipeline as Data/SHP/Catchments.shp
(column 'name' required) and to the maps.
Writes W3/sediment/catchments/Dam_catchments.shp (+ .gpkg) and a comparison with Basin 1's dam catchment areas.
"""
import sys, sqlite3
from pathlib import Path
import pandas as pd, geopandas as gpd
from shapely import wkb
from shapely.ops import unary_union
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DAMS, MODEL, DAMS_SHP, CRS, W3, CB04, ensure
import basinfile as bf

OUT = ensure(W3 / "sediment" / "catchments")
els = bf.parse(MODEL / "Basin_2.basin")
con = sqlite3.connect(MODEL / "Basin_2.sqlite"); poly = {n: wkb.loads(g) for n, g in con.execute("select name, GEOMETRY from subbasin2d") if g}; con.close()
dams = gpd.read_file(DAMS_SHP).set_index("Dam Name")
rows = []
for dam in DAMS:
    up = [n for n in bf.upstream_of(els, dam) if els[n]["type"] == "Subbasin"]
    import shapely
    geom = unary_union([shapely.force_2d(poly[n]).buffer(0) for n in up]).buffer(2.0).buffer(-2.0)   # 2 m close/open removes slivers between subbasins
    if geom.geom_type == "MultiPolygon":
        parts = sorted(geom.geoms, key=lambda p: p.area, reverse=True); small = [p for p in parts if p.area < 1e4]
        if small: print(f"{dam}: dropping {len(small)} sliver part(s), largest {max(p.area for p in small):.0f} m2"); geom = unary_union([p for p in parts if p.area >= 1e4])
        if geom.geom_type == "MultiPolygon": print(f"{dam}: still {len(geom.geoms)} parts, areas km2:", [round(p.area / 1e6, 3) for p in geom.geoms])
    areas = {n: bf.num(els[n], "Area") for n in up}; hms = sum(areas.values())
    cn = sum(bf.num(els[n], "Curve Number") * areas[n] for n in up) / hms
    x, y = bf.xy(els[dam])
    rows.append(dict(name=dam, area_km2=round(geom.area / 1e6, 2), hms_km2=round(hms, 2), cn_w=round(cn, 1), n_sub=len(up), jx=round(x, 1), jy=round(y, 1),
                     fsl_m=float(dams.loc[dam, "FSL"]), crest_m=float(dams.loc[dam, "Crest El"]), subbasins=", ".join(sorted(up)), geometry=geom))
g = gpd.GeoDataFrame(rows, crs=CRS)
g.drop(columns="subbasins").to_file(OUT / "Dam_catchments.shp", driver="ESRI Shapefile", encoding="utf-8"); g.to_file(OUT / "Dam_catchments.gpkg", layer="dam_catchments", driver="GPKG")
cmp = pd.read_csv(CB04 / "gis" / "dam_catchment_comparison.csv") if (CB04 / "gis" / "dam_catchment_comparison.csv").exists() else None
pd.set_option("display.width", 200); print(g.drop(columns=["geometry", "subbasins"]).to_string(index=False))
if cmp is not None: print("\nBasin 1 comparison file columns:", list(cmp.columns)); print(cmp.to_string(index=False))
print("multi-part polygons:", list(g[g.geometry.geom_type != "Polygon"].name), "->", OUT)
