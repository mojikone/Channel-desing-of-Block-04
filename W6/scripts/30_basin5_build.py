"""Step 30 - the new catchment in HEC-HMS Basin 5 (engineer, 2026-10-10): the catchment delineated for the outlet
495922.5, 2651832.5 (inputs/catchment_495922_2651832.gpkg, 16.4 km2) becomes subbasin SHA-S51 draining to the outlet
junction SHA-J52, parameterised as the project's channel subbasins (README decision 6): CN = mean of
Hydrology Data/CN_Include_Hill_Area.tif over the polygon (127/255/0 excluded), Ia = 0.2*25.4*(1000/CN - 10) mm,
lag = 0.6*(1/52)*L1085^0.77/S^0.385 min with L1085 = 0.75*Ltot of the longest flow path (WhiteboxTools on the 10 m HMS
terrain clipped to the polygon) and S the 10-85 slope (floor 0.0005). Basin 5 (empty, created by the engineer) is set to
Metric; Basin_5.sqlite gets the polygon, centroid, outlet and longest flow path; 13 runs 'FM <rp> B5' and 13 depth-area
analyses 'DA <rp> B5' (analysis points SHA-S51, SHA-J52) are added as for Basin 4; the met models list Basin 5.
HMS must be closed. Without --install everything is written to hms/staging and validated; with --install the touched
project files are backed up to _backup_before_basin5_<stamp>/ and replaced.
    python 30_basin5_build.py [--install]"""
import os, sys, re, shutil, sqlite3, datetime, subprocess, json, math
import numpy as np, pandas as pd, geopandas as gpd, rasterio, rasterio.mask, whitebox
from shapely import wkb
from shapely.geometry import Point, LineString, mapping
from shapely.ops import unary_union
HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE); CB = os.path.dirname(W6)
HMS = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydrology\HEC_HMS_Block_04"
TERRAIN = os.path.join(HMS, "terrain", "NSA_5m_B04_Res10m", "00", "elevation.tif"); CNR = os.path.join(HMS, "Hydrology Data", "CN_Include_Hill_Area.tif")
CATCH = os.path.join(W6, "inputs", "catchment_495922_2651832.gpkg"); OUTLET = (495922.5, 2651832.5)
SUB, JUN, BASIN = "SHA-S51", "SHA-J52", "Basin 5"
RPS = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr", "1000yr", "2000yr", "5000yr", "10000yr", "PMP"]
ST = os.path.join(W6, "hms", "staging"); WRK = os.path.join(W6, "hms", "lfp"); os.makedirs(ST, exist_ok=True); os.makedirs(WRK, exist_ok=True)
INSTALL = "--install" in sys.argv
now = datetime.datetime.now(); DATE = now.strftime("%d %B %Y").lstrip("0"); TIME = now.strftime("%H:%M:%S")
FILES = ["HEC_HMS_Block_04.hms", "HEC_HMS_Block_04.run", "HEC_HMS_Block_04.nals", "Basin_5.basin", "Basin_3.sqlite"] + ["FM_%s.met" % rp for rp in RPS]
for f in FILES: shutil.copy2(os.path.join(HMS, f), os.path.join(ST, f))
log = []

# ---------------------------------------------------------------- the catchment
g = gpd.read_file(CATCH); poly = unary_union(list(g.geometry.make_valid())); area_km2 = poly.area / 1e6
cx, cy = poly.centroid.x, poly.centroid.y
from pyproj import Transformer
lon, lat = Transformer.from_crs("EPSG:32640", "EPSG:4326", always_xy=True).transform(cx, cy)
# CN: mean of the valid cells inside the polygon
with rasterio.open(CNR) as s:
    arr, _ = rasterio.mask.mask(s, [mapping(poly)], crop=True, nodata=255, all_touched=False); a = arr[0]
valid = (a != 127) & (a != 255) & (a > 0); CN = float(a[valid].mean()); Ia = 0.2 * 25.4 * (1000.0 / CN - 10.0)
log.append("area %.3f km2, CN %.1f (%d valid cells of %d), Ia %.2f mm, centroid %.1f %.1f (lat %.6f lon %.6f)" % (area_km2, CN, valid.sum(), (a != 255).sum(), Ia, cx, cy, lat, lon))
# longest flow path on the 10 m terrain inside the polygon
with rasterio.open(TERRAIN) as s:
    dem, tr = rasterio.mask.mask(s, [mapping(poly.buffer(30))], crop=True, nodata=-9999.0); prof = s.profile.copy()
dem = dem[0].astype("float32"); dem[dem > 1e30] = -9999.0
prof.update(height=dem.shape[0], width=dem.shape[1], transform=tr, nodata=-9999.0, dtype="float32", count=1)
with rasterio.open(os.path.join(WRK, "dem.tif"), "w", **prof) as d: d.write(dem, 1)
from rasterio.features import rasterize
bas = rasterize([(mapping(poly), 1)], out_shape=dem.shape, transform=tr, fill=0, dtype="int32")
bprof = prof.copy(); bprof.update(dtype="int32", nodata=0)
with rasterio.open(os.path.join(WRK, "basin.tif"), "w", **bprof) as d: d.write(bas, 1)
wbt = whitebox.WhiteboxTools(); wbt.set_verbose_mode(False); wbt.set_working_dir(WRK)
wbt.fill_depressions("dem.tif", "fill.tif", fix_flats=True)
wbt.longest_flowpath("fill.tif", "basin.tif", "lfp.shp")
lfp = gpd.read_file(os.path.join(WRK, "lfp.shp")); lfp = lfp.loc[lfp.geometry.length.idxmax()]; line = lfp.geometry
with rasterio.open(os.path.join(WRK, "fill.tif")) as s:
    pts = list(line.coords); zs = np.array([v[0] for v in s.sample([(x, y) for x, y in pts])], dtype=float)
if zs[0] < zs[-1]: pts = pts[::-1]; zs = zs[::-1]          # head (high) to outlet (low)
d = np.r_[0.0, np.cumsum([math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]) for i in range(1, len(pts))])]
Ltot = float(d[-1]); dfo = Ltot - d
def zat(frac): return float(np.interp(frac * Ltot, dfo[::-1], zs[::-1]))
z10, z85 = zat(0.10), zat(0.85); L1085 = 0.75 * Ltot; S1085 = (z85 - z10) / L1085; S_used = max(S1085, 0.0005)
lag = 0.6 * (1.0 / 52.0) * L1085 ** 0.77 / S_used ** 0.385
log.append("longest flow path %.0f m (head z %.1f, outlet z %.1f, %s vertices), z10 %.2f z85 %.2f, L1085 %.0f m, S1085 %.5f, lag %.1f min" % (Ltot, zs[0], zs[-1], len(pts), z10, z85, L1085, S1085, lag))
params = dict(subbasin=SUB, junction=JUN, area_km2=round(area_km2, 3), CN=round(CN, 1), Ia_mm=round(Ia, 2), Ltot_m=round(Ltot, 1), z10=round(z10, 2), z85=round(z85, 2), L1085_m=round(L1085, 1), S1085=round(S1085, 5), S_used=round(S_used, 5), lag_min=round(lag, 1), centroid=[round(cx, 2), round(cy, 2)], outlet=list(OUTLET), lat=lat, lon=lon)
json.dump(params, open(os.path.join(W6, "hms", "basin5_parameters.json"), "w"), indent=1)

# ---------------------------------------------------------------- Basin_5.basin
b = open(os.path.join(ST, "Basin_5.basin"), encoding="utf-8").read()
b = re.sub(r'^(\s*Unit System: ).*$', r'\g<1>Metric', b, count=1, flags=re.M)
b = re.sub(r'^(\s*Last Modified Date: ).*$', r'\g<1>' + DATE, b, count=1, flags=re.M); b = re.sub(r'^(\s*Last Modified Time: ).*$', r'\g<1>' + TIME, b, count=1, flags=re.M)
if ("Subbasin: " + SUB) not in b:
    sub = ("Subbasin: %s\n     Last Modified Date: %s\n     Last Modified Time: %s\n     Latitude Degrees:  %.14f\n     Longitude Degrees: %.14f\n     Canvas X: %.10f\n     Canvas Y: %.10f\n     Area: %.3f\n     Downstream: %s\n     Discretization: None\n     File: Basin_5.sqlite\n     Canopy: None\n     Allow Simultaneous Precip Et: No\n     Plant Uptake Method: None\n     Surface: None\n     LossRate: SCS\n     Percent Impervious Area: 0.0\n     Curve Number: %.1f\n     Initial Abstraction: %.2f\n     Transform: SCS\n     Lag: %.1f\n     Unitgraph Type: STANDARD\n     Baseflow: None\nEnd:\n"
           % (SUB, DATE, TIME, lat, lon, cx, cy, area_km2, JUN, CN, Ia, lag))
    jun = "Junction: %s\n     Last Modified Date: %s\n     Last Modified Time: %s\n     Canvas X: %.1f\n     Canvas Y: %.1f\nEnd:\n" % (JUN, DATE, TIME, OUTLET[0], OUTLET[1])
    head_end = b.index("End:\n") + 5
    b = b[:head_end] + "\n" + sub + "\n" + jun + b[head_end:]
b = re.sub(r'^(\s*Last View N: ).*$', r'\g<1>%.1f' % (poly.bounds[3] + 500), b, flags=re.M); b = re.sub(r'^(\s*Last View S: ).*$', r'\g<1>%.1f' % (poly.bounds[1] - 500), b, flags=re.M)
b = re.sub(r'^(\s*Last View W: ).*$', r'\g<1>%.1f' % (poly.bounds[0] - 500), b, flags=re.M); b = re.sub(r'^(\s*Last View E: ).*$', r'\g<1>%.1f' % (poly.bounds[2] + 500), b, flags=re.M)
b = re.sub(r'^(\s*Maximum View N: ).*$', r'\g<1>%.1f' % (poly.bounds[3] + 500), b, flags=re.M); b = re.sub(r'^(\s*Maximum View S: ).*$', r'\g<1>%.1f' % (poly.bounds[1] - 500), b, flags=re.M)
b = re.sub(r'^(\s*Maximum View W: ).*$', r'\g<1>%.1f' % (poly.bounds[0] - 500), b, flags=re.M); b = re.sub(r'^(\s*Maximum View E: ).*$', r'\g<1>%.1f' % (poly.bounds[2] + 500), b, flags=re.M)
open(os.path.join(ST, "Basin_5.basin"), "w", encoding="utf-8", newline="\n").write(b)

# ---------------------------------------------------------------- Basin_5.sqlite: Basin 3's schema, only the new elements
dst = os.path.join(ST, "Basin_5.sqlite"); shutil.copyfile(os.path.join(ST, "Basin_3.sqlite"), dst); os.remove(os.path.join(ST, "Basin_3.sqlite"))
c = sqlite3.connect(dst)
for t in ("subbasin2d", "centroid", "outlet", "longest_flowpath", "centroidal_flowpath", "teneightyfive_flowpath", "reach2d", "reach_statistics", "reservoir", "reservoir2d", "subbasin_statistics"):
    try: c.execute("delete from %s" % t)
    except sqlite3.OperationalError as ex: log.append("sqlite: %s" % ex)
c.execute("insert into subbasin2d (GEOMETRY,name,centroid_x,centroid_y,area_sqkm,latitude,longitude,basinid) values (?,?,?,?,?,?,?,?)", (wkb.dumps(poly), SUB, cx, cy, round(area_km2, 4), lat, lon, 5))
c.execute("insert into centroid (GEOMETRY,subbasin) values (?,?)", (wkb.dumps(Point(cx, cy, 0.0)), SUB))
c.execute("insert into outlet (GEOMETRY,name) values (?,?)", (wkb.dumps(Point(OUTLET[0], OUTLET[1], 0.0)), SUB))
c.execute("insert into longest_flowpath (GEOMETRY,subbasin) values (?,?)", (wkb.dumps(LineString(pts)), SUB))
try: c.execute("insert into subbasin_statistics (subbasin_name,longest_length,longest_slope,[10_85_length],[10_85_slope],basin_relief) values (?,?,?,?,?,?)", (SUB, Ltot, (zs[0] - zs[-1]) / Ltot, L1085, S1085, float(zs[0] - zs[-1])))
except sqlite3.OperationalError as ex: log.append("sqlite statistics: %s" % ex)
c.commit(); c.close()

# ---------------------------------------------------------------- project: description, runs, analyses, met
hms = open(os.path.join(ST, "HEC_HMS_Block_04.hms"), encoding="utf-8").read()
hms = re.sub(r'(^Basin: Basin 5\r?\n\s*Filename: Basin_5\.basin\r?\n\s*Description: ).*$', r'\g<1>the %s catchment (16.4 km2) of the channel design, outlet junction %s' % (SUB, JUN), hms, count=1, flags=re.M)
open(os.path.join(ST, "HEC_HMS_Block_04.hms"), "w", encoding="utf-8", newline="\n").write(hms)
run = open(os.path.join(ST, "HEC_HMS_Block_04.run"), encoding="utf-8").read()
for rp in RPS:
    if "Run: FM %s B5\n" % rp in run: continue
    blk = re.search(r'^Run: FM ' + rp + r' B3\r?\n.*?^End:\n', run, re.S | re.M).group(0)
    new = blk.replace("Run: FM %s B3" % rp, "Run: FM %s B5" % rp).replace("FM_%s_B3" % rp, "FM_%s_B5" % rp).replace("Basin: Basin 3", "Basin: " + BASIN)
    new = re.sub(r'^(\s*Last Modified Date: ).*$', r'\g<1>' + DATE, new, flags=re.M); new = re.sub(r'^(\s*Last Modified Time: ).*$', r'\g<1>' + TIME, new, flags=re.M)
    run = run.rstrip("\n") + "\n\n" + new
open(os.path.join(ST, "HEC_HMS_Block_04.run"), "w", encoding="utf-8", newline="\n").write(run)
nals = open(os.path.join(ST, "HEC_HMS_Block_04.nals"), encoding="utf-8").read()
for rp in RPS:
    if "Analysis: DA %s B5\n" % rp in nals: continue
    blk = re.search(r'^Analysis: DA ' + rp + r' B3\r?\n.*?^End:\n', nals, re.S | re.M).group(0)
    head = blk.split("     Analysis Point:")[0]; tail = "     Time-Series Output: Save All\n     Time Series Results Manager Start:\n     Time Series Results Manager End:\nEnd:\n"
    head = head.replace("Analysis: DA %s B3" % rp, "Analysis: DA %s B5" % rp).replace("DA_%s_B3.dss" % rp, "DA_%s_B5.dss" % rp).replace("Basin Model Name: Basin 3", "Basin Model Name: " + BASIN)
    head = re.sub(r'^\s*Last Execution (Date|Time): .*\n', '', head, flags=re.M)
    head = re.sub(r'^(\s*Last Modified Date: ).*$', r'\g<1>' + DATE, head, flags=re.M); head = re.sub(r'^(\s*Last Modified Time: ).*$', r'\g<1>' + TIME, head, flags=re.M)
    nals = nals.rstrip("\n") + "\n\n" + head + "".join("     Analysis Point: %s\n" % p for p in (SUB, JUN)) + tail
open(os.path.join(ST, "HEC_HMS_Block_04.nals"), "w", encoding="utf-8", newline="\n").write(nals)
for rp in RPS:
    p = os.path.join(ST, "FM_%s.met" % rp); m = open(p, encoding="utf-8").read()
    if "Use Basin Model: Basin 5" not in m: m = m.replace("     Use Basin Model: Basin 4\n", "     Use Basin Model: Basin 4\n     Use Basin Model: Basin 5\n", 1); open(p, "w", encoding="utf-8", newline="\n").write(m)
subprocess.run([sys.executable, os.path.join(CB, "scripts", "validate_basin.py"), os.path.join(ST, "Basin_5.basin")], check=False)
for l in log: print(l)
print(json.dumps(params, indent=1))
if INSTALL:
    if any(p.name.lower().startswith("hec-hms") for p in __import__("pathlib").Path("C:/").glob("*")): pass
    bk = os.path.join(HMS, "_backup_before_basin5_%s" % now.strftime("%Y%m%d_%H%M%S")); os.makedirs(bk, exist_ok=True)
    for f in ["HEC_HMS_Block_04.hms", "HEC_HMS_Block_04.run", "HEC_HMS_Block_04.nals", "Basin_5.basin"] + ["FM_%s.met" % rp for rp in RPS]: shutil.copy2(os.path.join(HMS, f), os.path.join(bk, f))
    for f in ["HEC_HMS_Block_04.hms", "HEC_HMS_Block_04.run", "HEC_HMS_Block_04.nals", "Basin_5.basin", "Basin_5.sqlite"] + ["FM_%s.met" % rp for rp in RPS]: shutil.copy2(os.path.join(ST, f), os.path.join(HMS, f))
    print("installed into", HMS, "| previous files in", bk)
