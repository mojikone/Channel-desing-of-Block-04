"""Step 06 - shapefiles (and one GeoPackage) of every element with the peak flow and volume of all return periods.

For Basin 3 (reservoirs) and Basin 2 (no reservoirs):
  Subbasins_B<b>.shp : polygons from the HMS basin SQLite (subbasin2d) + HMS parameters (area, CN, Ia, lag, downstream)
  Reaches_B<b>.shp   : lines from reach2d + HMS routing parameters (length, slope, bottom width, side slope, n)
  Points_B<b>.shp    : junctions, outfalls, dam junctions and reservoirs at their HMS canvas coordinates
Every feature carries Q<rp> (peak, m3/s) and V<rp> (volume, Mm3) for 2yr ... PMP, read at its own depth-area analysis point.
Field names are kept within the 10-character shapefile limit; the GeoPackage Block04_elements_B<b>.gpkg holds the same layers.
EPSG:32640. Writes W3/elements/shp/B<b>/ and W3/elements/shp/Block04_elements_B<b>.gpkg
"""
import sys, sqlite3
from pathlib import Path
import pandas as pd, geopandas as gpd
from shapely import wkb
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DAMS, RPS, MODEL, RESULTS_CB04, CRS, W3, ensure
import basinfile as bf

def rpf(prefix, rp): return f"{prefix}{rp.replace('yr', '')}"      # Q2 ... Q10000, QPMP

def qv_table(b):
    df = pd.read_csv(RESULTS_CB04 / f"basin{b}_peak_flow_volume_long.csv")
    q = df.pivot(index="element", columns="rp", values="peak_m3s")[RPS].round(3); v = df.pivot(index="element", columns="rp", values="vol_Mm3")[RPS].round(4)
    q.columns = [rpf("Q", rp) for rp in RPS]; v.columns = [rpf("V", rp) for rp in RPS]
    return q.join(v)

def geoms(sqlite, table):
    """name -> 2D geometry (HMS stores 3D WKB whose Z can be NaN, which the shapefile driver rejects)."""
    import shapely
    con = sqlite3.connect(sqlite); rows = con.execute(f"select name, GEOMETRY from {table}").fetchall(); con.close()
    return {n: shapely.force_2d(wkb.loads(g)) for n, g in rows if g is not None}

for b in ("3", "2"):
    els = bf.parse(MODEL / f"Basin_{b}.basin"); qv = qv_table(b); out = ensure(W3 / "elements" / "shp" / f"B{b}"); gpkg = W3 / "elements" / "shp" / f"Block04_elements_B{b}.gpkg"
    if gpkg.exists(): gpkg.unlink()
    # ---- subbasins
    poly = geoms(MODEL / f"Basin_{b}.sqlite", "subbasin2d"); rows = []
    for n, e in els.items():
        if e["type"] != "Subbasin": continue
        if n not in poly: print("no polygon for", n); continue
        rows.append(dict(name=n, type="Subbasin", area_km2=bf.num(e, "Area"), cn=bf.num(e, "Curve Number"), ia_mm=bf.num(e, "Initial Abstraction"), lag_min=bf.num(e, "Lag"),
                         downstream=e["attrs"].get("Downstream", ""), geometry=poly[n]))
    sub = gpd.GeoDataFrame(rows, crs=CRS).set_index("name").join(qv).reset_index()
    # ---- reaches
    line = geoms(MODEL / f"Basin_{b}.sqlite", "reach2d"); rows = []
    for n, e in els.items():
        if e["type"] != "Reach": continue
        if n not in line: print("no line for", n); continue
        rows.append(dict(name=n, type="Reach", length_m=bf.num(e, "Length"), slope=bf.num(e, "Energy Slope"), bottom_w=bf.num(e, "Bottom Width"), side_slope=bf.num(e, "Side Slope"),
                         manning_n=bf.num(e, "Mannings n"), route=e["attrs"].get("Route", ""), downstream=e["attrs"].get("Downstream", ""), geometry=line[n]))
    rch = gpd.GeoDataFrame(rows, crs=CRS).set_index("name").join(qv).reset_index()
    # ---- points
    rows = []
    for n, e in els.items():
        if e["type"] not in ("Junction", "Reservoir"): continue
        x, y = bf.xy(e); ds = e["attrs"].get("Downstream", "")
        typ = "Reservoir" if e["type"] == "Reservoir" else ("Dam junction" if n in DAMS else ("Outfall" if not ds else "Junction"))
        rows.append(dict(name=n, type=typ, downstream=ds, x=round(x, 1), y=round(y, 1), geometry=gpd.points_from_xy([x], [y])[0]))
    pts = gpd.GeoDataFrame(rows, crs=CRS).set_index("name").join(qv).reset_index()
    for gdf, nm in ((sub, "Subbasins"), (rch, "Reaches"), (pts, "Points")):
        miss = gdf[gdf[rpf("Q", "200yr")].isna()]
        if len(miss): print(f"B{b} {nm}: no results for", list(miss.name)[:8])
        gdf.to_file(out / f"{nm}_B{b}.shp", driver="ESRI Shapefile", encoding="utf-8"); gdf.to_file(gpkg, layer=nm, driver="GPKG")
    print(f"B{b}: subbasins {len(sub)} ({sub.area_km2.sum():.0f} km2) | reaches {len(rch)} | points {len(pts)} ({(pts['type'] == 'Outfall').sum()} outfalls, {(pts['type'] == 'Reservoir').sum()} reservoirs, {(pts['type'] == 'Dam junction').sum()} dam junctions) -> {out}")
