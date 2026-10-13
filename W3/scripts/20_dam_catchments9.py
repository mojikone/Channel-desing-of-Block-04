"""Step 20 - the nine dam catchments from Basin 1 (the hydrology study's model) with the physiographic table the engineer
asked for: area, longest flow path length and 10-85 slope, basin slope, time of concentration, lag, weighted CN, relief.
Longest flow path = the Basin 1 subbasin longest-flowpath line whose length plus the reaches down to the dam is greatest;
its 10-85 slope from the 10 m terrain along that line; lag = 0.6 (1/52) L^0.77 S^-0.385 (Kirpich, minutes, L in m);
Tc = lag / 0.6; basin slope = mean cell slope of the terrain inside the catchment; relief = highest cell - outlet.
Writes sediment/catchments/Dam_catchments9.shp/.gpkg (+ 'name' column) and copies it to the RUSLE input as Catchments.shp.
"""
import sys, sqlite3, shutil
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio import mask as rmask
from shapely import wkb
from shapely.ops import unary_union, linemerge
from shapely.geometry import LineString, Point
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DAMS9, HMS, DAMS_SHP, CRS, W3, ensure
import basinfile as bf
import shapely

OUT = ensure(W3 / "sediment" / "catchments"); DEM = HMS / "terrain" / "NSA_5m_B04_Res10m" / "00" / "elevation.tif"
els = bf.parse(HMS / "Basin_1.basin"); ds = bf.downstream(els)
con = sqlite3.connect(HMS / "Basin_1.sqlite")
poly = {n: shapely.force_2d(wkb.loads(g)) for n, g in con.execute("select name, GEOMETRY from subbasin2d") if g}
reach = {n: shapely.force_2d(wkb.loads(g)) for n, g in con.execute("select name, GEOMETRY from reach2d") if g}
lfp = {n: shapely.force_2d(wkb.loads(g)) for g, n in con.execute("select GEOMETRY, subbasin from longest_flowpath") if g}
stats = {n: (float(a), float(b)) for n, a, b in con.execute("select subbasin_name, longest_length, [10_85_slope] from subbasin_statistics")}; con.close()
dams = gpd.read_file(DAMS_SHP).set_index("Dam Name")

def sample(src, line, frac):
    p = line.interpolate(frac, normalized=True); v = list(src.sample([(p.x, p.y)]))[0][0]; return float(v) if np.isfinite(v) and -1e4 < v < 1e30 else np.nan

rows = []
with rasterio.open(DEM) as src:
    for dam in DAMS9:
        up = [n for n in bf.upstream_of(els, dam) if els[n]["type"] == "Subbasin"]
        geom = unary_union([poly[n].buffer(0) for n in up]).buffer(2).buffer(-2)
        if geom.geom_type == "MultiPolygon": geom = unary_union([p for p in geom.geoms if p.area >= 1e4])
        areas = {n: bf.num(els[n], "Area") for n in up}; hms = sum(areas.values()); cn = sum(bf.num(els[n], "Curve Number") * areas[n] for n in up) / hms
        # longest path: subbasin flowpath + the reaches down to the dam
        best = None
        for s in up:
            if s not in lfp: continue
            parts = [lfp[s]]; cur = ds.get(s); seen = set(); L = lfp[s].length
            while cur and cur != dam and cur not in seen:
                seen.add(cur)
                if els[cur]["type"] == "Reach" and cur in reach: parts.append(reach[cur]); L += reach[cur].length
                cur = ds.get(cur)
            if best is None or L > best[0]: best = (L, parts, s)
        L, parts, s0 = best
        # stitch the pieces in flow order (the reach lines do not touch the flowpath end exactly, so linemerge would split them)
        pieces = []
        for part in parts:
            pieces.extend(list(part.geoms) if part.geom_type == "MultiLineString" else [part])
        coords = []
        for k, pc in enumerate(pieces):
            c = list(pc.coords)
            if k == 0:
                if len(pieces) > 1:   # the end nearer to the next piece is the downstream end
                    if pieces[1].distance(Point(c[0])) < pieces[1].distance(Point(c[-1])): c = c[::-1]
                else:                 # a single piece: from the higher end down
                    if sample(src, pc, 0.0) < sample(src, pc, 1.0): c = c[::-1]
            elif Point(coords[-1]).distance(Point(c[-1])) < Point(coords[-1]).distance(Point(c[0])): c = c[::-1]
            coords.extend(c)
        line = LineString(coords)
        z0, z1 = sample(src, line, 0.0), sample(src, line, 1.0)
        if z1 > z0: print("  WARNING", dam, "path ends higher than it starts", z0, z1)
        z10, z85 = sample(src, line, 0.10), sample(src, line, 0.85); s1085 = (z10 - z85) / (0.75 * line.length)
        arr, tr = rmask.mask(src, [geom], crop=True, nodata=np.nan); z = arr[0].astype(float); z[(z > 1e30) | (z < -1e4)] = np.nan
        gy, gx = np.gradient(z, abs(tr.e), tr.a); slope = np.nanmean(np.hypot(gx, gy))
        jx, jy = bf.xy(els[dam]); o_arr, _ = rmask.mask(src, [geom.intersection(Point(jx, jy).buffer(100))], crop=True, nodata=np.nan); zo = o_arr[0]; zo = zo[np.isfinite(zo) & (zo < 1e30)]
        z_out = float(zo.min()) if zo.size else float(np.nanmin(z)); relief = float(np.nanmax(z)) - z_out
        lag = 0.6 * (1 / 52) * (line.length) ** 0.77 * max(s1085, 1e-4) ** -0.385; tc = lag / 0.6
        rows.append(dict(name=dam, area_km2=round(geom.area / 1e6, 2), hms_km2=round(hms, 2), cn_w=round(cn, 1), n_sub=len(up), lfp_km=round(line.length / 1000, 2), s1085=round(s1085, 5), basin_slope=round(slope, 4),
                         lag_min=round(lag, 1), tc_min=round(tc, 1), relief_m=round(relief, 0), z_max_m=round(float(np.nanmax(z)), 1), z_outlet_m=round(z_out, 1), jx=round(jx, 1), jy=round(jy, 1),
                         fsl_m=float(dams.loc[dam, "FSL"]), crest_m=float(dams.loc[dam, "Crest El"]), subbasins=", ".join(sorted(up)), geometry=geom))
g = gpd.GeoDataFrame(rows, crs=CRS)
g.drop(columns="subbasins").to_file(OUT / "Dam_catchments9.shp", driver="ESRI Shapefile", encoding="utf-8"); g.to_file(OUT / "Dam_catchments9.gpkg", layer="dam_catchments", driver="GPKG")
R = W3 / "sediment" / "rusle" / "Data" / "SHP"
for f in R.glob("Catchments.*"): f.unlink()
for ext in ("shp", "shx", "dbf", "prj", "cpg"):
    if (OUT / f"Dam_catchments9.{ext}").exists(): shutil.copy2(OUT / f"Dam_catchments9.{ext}", R / f"Catchments.{ext}")
pd.set_option("display.width", 220); print(g.drop(columns=["geometry", "subbasins", "jx", "jy"]).to_string(index=False)); print("written", OUT, "and RUSLE Data/SHP/Catchments.shp")
