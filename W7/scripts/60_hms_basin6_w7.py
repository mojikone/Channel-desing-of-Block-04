"""Step 60 (W7) - Basin 6 becomes the channel hydrology of record, with the Shafan 08 dam and its FULL catchment (engineer,
2026-10-12: "fix it"). Basin 6 (step 52 of W6) was Basin 3 + the Basin 4 reservoir below the junction "Shafan 08 site", but the
dam's local catchment in Basin 3 was 79.7 km2 against 89.7 km2 in Basin 1/4: the Basin 4 polygon S23 (31.037 km2) is SHA-S23
(20.25 km2 of its 20.95) + 9.66 km2 of SHA-S44 (which drained to SHA-J42, below the dam) + 1.12 km2 of SHA-S46 (to SHA-J45).
The fix, by the polygons:
  * SHA-S23 := S23 of Basin 4 (polygon, area 31.037, CN 86.2, Ia 8.11, lag 97.5, statistics and flow path), draining straight to
    "Shafan 08 site" as S23 drains to the dam in Basin 4 (it left SHA-J20 and SHA-R18, whose length stays the 3094 m of step 52);
  * SHA-S44 := SHA-S44 minus S23 (2.75 km2) and SHA-S46 := SHA-S46 minus S23 (16.53 km2): CN = mean of the CN grid over the
    polygon, Ia = 0.2 S, lag by the project's decision 6 (0.6/52 * L1085^0.77 / S1085^0.385, L1085 = 0.75 Ltot, longest flow path by
    WhiteboxTools on the 10 m HMS terrain), downstream unchanged (SHA-J42, SHA-J45);
  * Basin_6.sqlite follows (subbasin2d, centroid, outlet, longest_flowpath, subbasin_statistics; the Shafan 08 reservoir point).
Then the eight 12-point "DA <rp> B6" analyses of step 52 are replaced by 13 analyses copied from "DA <rp> B3" with ALL their
analysis points (362), the old DA_*_B6 files are deleted, the Basin 6 description in the project is made live, and the headless
compute script is written to --out (a folder without spaces; run from C:\\Program Files\\HEC\\HEC-HMS\\4.12: HEC-HMS.cmd -script).
HMS must be closed. Backup of every file touched in <HMS>/_backup_before_w7_<stamp>/.
    python 60_hms_basin6_w7.py --out <folder>"""
import os, sys, re, shutil, math, datetime, json, sqlite3
import numpy as np, geopandas as gpd, rasterio, rasterio.mask, whitebox, warnings
from shapely import wkb
from shapely.geometry import Point, LineString, MultiPolygon, Polygon, mapping
from shapely.ops import unary_union
from rasterio.features import rasterize
from pyproj import Transformer
warnings.filterwarnings("ignore")
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
OUT = opt("--out"); assert OUT and " " not in OUT, "--out <folder without spaces>"
HERE = os.path.dirname(os.path.abspath(__file__)); W7 = os.path.dirname(HERE); CB = os.path.dirname(W7)
HMS = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydrology\HEC_HMS_Block_04"
TERRAIN = os.path.join(HMS, "terrain", "NSA_5m_B04_Res10m", "00", "elevation.tif"); CNR = os.path.join(HMS, "Hydrology Data", "CN_Include_Hill_Area.tif")
RPS = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr", "1000yr", "2000yr", "5000yr", "10000yr", "PMP"]
HMSOUT = os.path.join(W7, "hms"); WRK = os.path.join(HMSOUT, "lfp"); os.makedirs(WRK, exist_ok=True); os.makedirs(OUT, exist_ok=True)
now = datetime.datetime.now(); DATE = now.strftime("%d %B %Y").lstrip("0"); TIME = now.strftime("%H:%M:%S")
log = []
def L(s): log.append(s); print(s)

# ---------------------------------------------------------------- backup
stamp = now.strftime("%Y%m%d_%H%M%S"); bk = os.path.join(HMS, "_backup_before_w7_" + stamp); os.makedirs(bk)
for f in ["HEC_HMS_Block_04.hms", "HEC_HMS_Block_04.nals", "HEC_HMS_Block_04.run", "Basin_6.basin", "Basin_6.sqlite"] + ["FM_%s.met" % rp for rp in RPS]:
    if os.path.exists(os.path.join(HMS, f)): shutil.copy2(os.path.join(HMS, f), bk)
L("backup: " + bk)

# ---------------------------------------------------------------- the polygons
b3 = gpd.read_file(os.path.join(HMS, "Basin_3.sqlite"), layer="subbasin2d").set_index("name")
b4 = gpd.read_file(os.path.join(HMS, "Basin_4.sqlite"), layer="subbasin2d").set_index("name")
S23 = b4.loc["S23"].geometry
old = {n: b3.loc[n].geometry for n in ("SHA-S23", "SHA-S44", "SHA-S46")}
new = {"SHA-S23": S23, "SHA-S44": old["SHA-S44"].difference(S23), "SHA-S46": old["SHA-S46"].difference(S23)}
for n in new:
    g = new[n]; parts = sorted([p for p in getattr(g, "geoms", [g])], key=lambda p: -p.area)
    L("%s: old %.3f km2 -> new %.3f km2 in %d part(s) %s" % (n, old[n].area / 1e6, g.area / 1e6, len(parts), [round(p.area / 1e6, 3) for p in parts[:4]]))
    if len(parts) > 1 and parts[1].area / 1e6 < 0.05:   # slivers of the boundary, dropped
        new[n] = unary_union(parts[:1]); L("   slivers under 0.05 km2 dropped -> %.3f km2" % (new[n].area / 1e6))
L("old SHA-S23 outside S23 (left unassigned, as in Basin 4): %.3f km2" % (old["SHA-S23"].difference(S23).area / 1e6))
tr4326 = Transformer.from_crs("EPSG:32640", "EPSG:4326", always_xy=True)

# ---------------------------------------------------------------- CN and Ia from the grid; lag by decision 6 from the longest flow path
def cn_of(poly):
    with rasterio.open(CNR) as s:
        arr, _ = rasterio.mask.mask(s, [mapping(poly)], crop=True, nodata=255, all_touched=False); a = arr[0]
    valid = (a != 127) & (a != 255) & (a > 0); CN = float(a[valid].mean()); return CN, 0.2 * 25.4 * (1000.0 / CN - 10.0), int(valid.sum())
def lfp_of(poly, tag):
    wd = os.path.join(WRK, tag); os.makedirs(wd, exist_ok=True)
    with rasterio.open(TERRAIN) as s:
        dem, tr = rasterio.mask.mask(s, [mapping(poly.buffer(30))], crop=True, nodata=-9999.0); prof = s.profile.copy()
    dem = dem[0].astype("float32"); dem[dem > 1e30] = -9999.0
    prof.update(height=dem.shape[0], width=dem.shape[1], transform=tr, nodata=-9999.0, dtype="float32", count=1)
    with rasterio.open(os.path.join(wd, "dem.tif"), "w", **prof) as d: d.write(dem, 1)
    bas = rasterize([(mapping(poly), 1)], out_shape=dem.shape, transform=tr, fill=0, dtype="int32")
    bprof = prof.copy(); bprof.update(dtype="int32", nodata=0)
    with rasterio.open(os.path.join(wd, "basin.tif"), "w", **bprof) as d: d.write(bas, 1)
    wbt = whitebox.WhiteboxTools(); wbt.set_verbose_mode(False); wbt.set_working_dir(wd)
    wbt.fill_depressions("dem.tif", "fill.tif", fix_flats=True)
    wbt.longest_flowpath("fill.tif", "basin.tif", "lfp.shp")
    lfp = gpd.read_file(os.path.join(wd, "lfp.shp")); line = lfp.loc[lfp.geometry.length.idxmax()].geometry
    with rasterio.open(os.path.join(wd, "fill.tif")) as s:
        pts = list(line.coords); zs = np.array([v[0] for v in s.sample([(x, y) for x, y in pts])], dtype=float)
    if zs[0] < zs[-1]: pts = pts[::-1]; zs = zs[::-1]
    d = np.r_[0.0, np.cumsum([math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]) for i in range(1, len(pts))])]
    Ltot = float(d[-1]); dfo = Ltot - d
    def zat(frac): return float(np.interp(frac * Ltot, dfo[::-1], zs[::-1]))
    z10, z85 = zat(0.10), zat(0.85); L1085 = 0.75 * Ltot; S1085 = (z85 - z10) / L1085; S_used = max(S1085, 0.0005)
    lag = 0.6 * (1.0 / 52.0) * L1085 ** 0.77 / S_used ** 0.385
    return dict(Ltot=Ltot, z_head=float(zs[0]), z_out=float(zs[-1]), L1085=L1085, S1085=S1085, lag=lag, line=[(x, y, float(z)) for (x, y), z in zip(pts, zs)])

c4 = sqlite3.connect(os.path.join(HMS, "Basin_4.sqlite"))
st4 = c4.execute("select longest_length,longest_slope,[10_85_length],[10_85_slope],basin_relief from subbasin_statistics where subbasin_name='S23'").fetchone()
lfp4 = c4.execute("select GEOMETRY from longest_flowpath where subbasin='S23'").fetchone(); out4 = c4.execute("select GEOMETRY from outlet where name='S23'").fetchone()
cen4 = c4.execute("select GEOMETRY from centroid where subbasin='S23'").fetchone(); res4 = c4.execute("select GEOMETRY,name from reservoir where name like 'Shafan 08%'").fetchone()
c4.close()
b4txt = open(os.path.join(HMS, "Basin_4.basin"), encoding="utf-8").read()
s23blk = re.search(r"^Subbasin: S23\r?\n(.*?)^End:", b4txt, re.S | re.M).group(1)
def fld(blk, key): return re.search(r"\n?\s*%s: (.+)" % re.escape(key), blk).group(1).strip()
params = {}
params["SHA-S23"] = dict(area=float(fld(s23blk, "Area")), CN=float(fld(s23blk, "Curve Number")), Ia=float(fld(s23blk, "Initial Abstraction")), lag=float(fld(s23blk, "Lag")),
                         lat=float(fld(s23blk, "Latitude Degrees")), lon=float(fld(s23blk, "Longitude Degrees")), cx=float(fld(s23blk, "Canvas X")), cy=float(fld(s23blk, "Canvas Y")),
                         down="Shafan 08 site", stats=st4, line=None)
cnchk = cn_of(S23); L("SHA-S23 <- Basin 4 S23: area %.3f, CN %.1f (grid check %.1f), Ia %.2f, lag %.1f min, -> Shafan 08 site" % (params["SHA-S23"]["area"], params["SHA-S23"]["CN"], cnchk[0], params["SHA-S23"]["Ia"], params["SHA-S23"]["lag"]))
for n, down in (("SHA-S44", "SHA-J42"), ("SHA-S46", "SHA-J45")):
    poly = new[n]; CN, Ia, nv = cn_of(poly); f = lfp_of(poly, n.replace("-", "_"))
    cx, cy = poly.centroid.x, poly.centroid.y; lon, lat = tr4326.transform(cx, cy)
    params[n] = dict(area=poly.area / 1e6, CN=CN, Ia=Ia, lag=f["lag"], lat=lat, lon=lon, cx=cx, cy=cy, down=down,
                     stats=(f["Ltot"], (f["z_head"] - f["z_out"]) / f["Ltot"], f["L1085"], f["S1085"], f["z_head"] - f["z_out"]), line=f["line"])
    L("%s: area %.3f km2, CN %.1f (%d cells), Ia %.2f mm, longest flow path %.0f m, S1085 %.5f, lag %.1f min (was %s) -> %s" % (n, params[n]["area"], CN, nv, Ia, f["Ltot"], f["S1085"], f["lag"], {"SHA-S44": "58.4", "SHA-S46": "61.6"}[n], down))
json.dump({n: {k: v for k, v in p.items() if k not in ("line", "stats")} for n, p in params.items()}, open(os.path.join(HMSOUT, "60_basin6_fix_parameters.json"), "w"), indent=1)

# ---------------------------------------------------------------- Basin_6.basin
b6 = open(os.path.join(HMS, "Basin_6.basin"), encoding="utf-8").read()
def patch_block(txt, name, p):
    m = re.search(r"^Subbasin: %s\r?\n.*?^End:\n" % re.escape(name), txt, re.S | re.M); blk = m.group(0)
    reps = {"Last Modified Date": DATE, "Last Modified Time": TIME, "Latitude Degrees": "%.14f" % p["lat"], "Longitude Degrees": "%.14f" % p["lon"],
            "Canvas X": "%.10f" % p["cx"], "Canvas Y": "%.10f" % p["cy"], "Area": "%.3f" % p["area"], "Downstream": p["down"],
            "Curve Number": "%.1f" % p["CN"], "Initial Abstraction": "%.2f" % p["Ia"], "Lag": "%.1f" % p["lag"]}
    nb = blk
    for k, v in reps.items():
        nb, c = re.subn(r"^(\s*%s:\s*).*$" % re.escape(k), lambda mm: mm.group(1) + v, nb, count=1, flags=re.M); assert c == 1, (name, k)
    return txt.replace(blk, nb, 1)
for n in ("SHA-S23", "SHA-S44", "SHA-S46"): b6 = patch_block(b6, n, params[n])
hdr = re.search(r"^Basin: Basin 6\r?\n.*?^End:\n", b6, re.S | re.M).group(0)
b6 = b6.replace(hdr, re.sub(r"^(\s*Last Modified Date: ).*$", r"\g<1>" + DATE, re.sub(r"^(\s*Last Modified Time: ).*$", r"\g<1>" + TIME, hdr, flags=re.M), flags=re.M), 1)
assert "Downstream: Shafan 08 site" in re.search(r"^Subbasin: SHA-S23\r?\n.*?^End:", b6, re.S | re.M).group(0)
open(os.path.join(HMS, "Basin_6.basin"), "w", encoding="utf-8", newline="\n").write(b6); L("Basin_6.basin written")

# ---------------------------------------------------------------- Basin_6.sqlite
c = sqlite3.connect(os.path.join(HMS, "Basin_6.sqlite"))
sample = c.execute("select GEOMETRY from subbasin2d where name='SHA-S44'").fetchone()[0]; gt = wkb.loads(sample).geom_type; L("subbasin2d geometry type in the file: " + gt)
def as_multi(g): return MultiPolygon([g]) if (gt == "MultiPolygon" and g.geom_type == "Polygon") else g
for n, p in params.items():
    c.execute("update subbasin2d set GEOMETRY=?, centroid_x=?, centroid_y=?, area_sqkm=?, latitude=?, longitude=? where name=?",
              (wkb.dumps(as_multi(new[n])), p["cx"], p["cy"], round(p["area"], 4), p["lat"], p["lon"], n))
    c.execute("delete from centroid where subbasin=?", (n,)); c.execute("insert into centroid (GEOMETRY,subbasin) values (?,?)", (cen4[0] if n == "SHA-S23" else wkb.dumps(Point(p["cx"], p["cy"], 0.0)), n))
    c.execute("delete from longest_flowpath where subbasin=?", (n,))
    c.execute("insert into longest_flowpath (GEOMETRY,subbasin) values (?,?)", (lfp4[0] if n == "SHA-S23" else wkb.dumps(LineString(p["line"])), n))
    c.execute("delete from subbasin_statistics where subbasin_name=?", (n,))
    c.execute("insert into subbasin_statistics (subbasin_name,longest_length,longest_slope,[10_85_length],[10_85_slope],basin_relief,length_units) values (?,?,?,?,?,?,?)", (n,) + tuple(str(v) for v in p["stats"]) + ("m",))
    for t in ("centroidal_flowpath", "teneightyfive_flowpath"): c.execute("delete from %s where subbasin=?" % t, (n,))
if out4: c.execute("delete from outlet where name='SHA-S23'"); c.execute("insert into outlet (GEOMETRY,name) values (?,?)", (out4[0], "SHA-S23"))
if res4 and not c.execute("select count(*) from reservoir where name='Shafan 08 Reservoir'").fetchone()[0]:
    c.execute("insert into reservoir (GEOMETRY,name) values (?,?)", (res4[0], "Shafan 08 Reservoir"))
c.commit(); c.close(); L("Basin_6.sqlite updated (3 subbasins, centroids, flow paths, statistics, S23 outlet, the reservoir point)")

# ---------------------------------------------------------------- the project description, the analyses, the met models
hms = open(os.path.join(HMS, "HEC_HMS_Block_04.hms"), encoding="utf-8").read()
blk = re.search(r"^Basin: Basin 6\r?\n.*?^End:\r?\n", hms, re.S | re.M).group(0)
nb = re.sub(r"Description: .*", "Description: channel hydrology of record from W7 (2026-10-12): Basin 3 with the Shafan 08 reservoir and its full catchment (S23 of Basin 4)", blk)
hms = hms.replace(blk, nb, 1); open(os.path.join(HMS, "HEC_HMS_Block_04.hms"), "w", encoding="utf-8", newline="\n").write(hms); L("project: Basin 6 description made live")
for rp in RPS:
    p = os.path.join(HMS, "FM_%s.met" % rp); m = open(p, encoding="utf-8").read()
    if "Use Basin Model: Basin 6" not in m:
        m = m.replace("     Use Basin Model: Basin 5\n", "     Use Basin Model: Basin 5\n     Use Basin Model: Basin 6\n", 1); open(p, "w", encoding="utf-8", newline="\n").write(m); L("met %s: Basin 6 allowed" % rp)
nals = open(os.path.join(HMS, "HEC_HMS_Block_04.nals"), encoding="utf-8").read()
nals, nrem = re.subn(r"^Analysis: DA \S+ B6\r?\n.*?^End:\r?\n\r?\n?", "", nals, flags=re.S | re.M); L("old B6 analyses removed: %d" % nrem)
added = 0; npts = {}
for rp in RPS:
    blk = re.search(r"^Analysis: DA " + rp + r" B3\r?\n.*?^End:\r?\n", nals, re.S | re.M).group(0)
    nb = blk.replace("Analysis: DA %s B3" % rp, "Analysis: DA %s B6" % rp).replace("DA_%s_B3.dss" % rp, "DA_%s_B6.dss" % rp).replace("Basin Model Name: Basin 3", "Basin Model Name: Basin 6")
    nb = re.sub(r"^\s*Last Execution (Date|Time): .*\n", "", nb, flags=re.M)
    nb = re.sub(r"^(\s*Last Modified Date: ).*$", r"\g<1>" + DATE, nb, flags=re.M); nb = re.sub(r"^(\s*Last Modified Time: ).*$", r"\g<1>" + TIME, nb, flags=re.M)
    npts[rp] = len(re.findall(r"Analysis Point: ", nb)); nals = nals.rstrip("\n") + "\n\n" + nb; added += 1
open(os.path.join(HMS, "HEC_HMS_Block_04.nals"), "w", encoding="utf-8", newline="\n").write(nals); L("analyses added: %d, analysis points per analysis: %s" % (added, sorted(set(npts.values()))))
for rp in RPS + ["2yr"]:
    for suf in (".dss", ".out", "_daa.log"):
        f = os.path.join(HMS, "DA_%s_B6%s" % (rp, suf))
        if os.path.exists(f): os.remove(f)
L("old DA_*_B6 result files deleted")
# ---------------------------------------------------------------- the headless compute script
open(os.path.join(OUT, "names.txt"), "w").write("\n".join("DA %s B6" % rp for rp in RPS) + "\n")
src = open(os.path.join(CB, "scripts", "hms_compute_all.py"), encoding="utf-8").read()
src = re.sub(r'HERE = r"[^"]+"', 'HERE = r"%s"' % OUT, src, count=1)
open(os.path.join(OUT, "hms_compute_b6w7.py"), "w", encoding="utf-8", newline="\n").write(src)
L("compute script: " + os.path.join(OUT, "hms_compute_b6w7.py"))
open(os.path.join(HMSOUT, "60_hms_basin6_w7.log"), "w", encoding="utf-8").write("\n".join(log) + "\n")
