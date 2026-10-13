"""Step 19 - Basin 4 = Basin 1 (the hydrology study's dam catchments, 32 subbasins) + a reservoir below each of the NINE
dam junctions, Shafan 08 included; 13 depth-area analyses 'DA <rp> B4' with every element as an analysis point.
HMS must be closed. The project files are backed up to _backup_before_basin4_<stamp>/ first.
Reservoir syntax and tables as Basin 3 (write_reservoirs.py); Shafan 08 gets its Elev-Area / Elev-Dis tables from
reservoirs/EAV_Shafan_08.csv and the dams shapefile (C 2.1, spillway length, crest overtopping 1.7 L_crest).
usage: python 19_basin4_build.py [--install]   (without --install: writes to W3/model/basin4_staging and validates only)
"""
import sys, os, re, shutil, sqlite3, datetime, subprocess
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd, hecdss
from shapely import wkb
from shapely.geometry import Point
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import HMS, RESERVOIRS, DAMS_SHP, W3, ensure
import basinfile as bf

INSTALL = "--install" in sys.argv; ST = ensure(W3 / "model" / "basin4_staging")
DAMS9 = ["Hawasinah 02", "Hawasinah 11", "Hawasinah EX", "Shafan 02", "Shafan 08", "Sarami 03", "Sarami 05", "Sakhin 04", "Sakhin 08"]
RPS = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr", "1000yr", "2000yr", "5000yr", "10000yr", "PMP"]
now = datetime.datetime.now(); DATE = now.strftime("%d %B %Y").lstrip("0"); TIME = now.strftime("%H:%M:%S")
FILES = ["HEC_HMS_Block_04.hms", "HEC_HMS_Block_04.run", "HEC_HMS_Block_04.nals", "HEC_HMS_Block_04.pdata", "HEC_HMS_Block_04.dss", "Basin_1.basin", "Basin_1.sqlite"] + [f"FM_{rp}.met" for rp in RPS]
for f in FILES: shutil.copy2(HMS / f, ST / f)
dams = gpd.read_file(DAMS_SHP).set_index("Dam Name")
g = lambda s, k: (re.search(r'^\s*' + re.escape(k) + r': (.*)$', s, re.M) or [None, None])[1]

# ---------------------------------------------------------------- basin file
basin = open(ST / "Basin_1.basin", encoding="utf-8").read()
basin = re.sub(r'^Basin: Basin 1\s*$', 'Basin: Basin 4', basin, count=1, flags=re.M)
basin = re.sub(r'^(\s*Description: ).*$', r'\1Basin 1 + the nine dam reservoirs (Shafan 08 included); elevation-area from the 10 m DEM, spillway rating C L H^1.5', basin, count=1, flags=re.M)
con = sqlite3.connect(ST / "Basin_1.sqlite"); reach_geom = {n: wkb.loads(gg) for gg, n in con.execute("select GEOMETRY, name from reach2d") if gg}
have_res = [r[0] for r in con.execute("select name from sqlite_master where type='table' and name='reservoir'")]
added = []
for dam in DAMS9:
    name = dam; crest_el = float(dams.loc[dam, "Crest El"]); fsl = float(dams.loc[dam, "FSL"]); C = float(dams.loc[dam, "C"]); L = float(dams.loc[dam, "Spillway L"]); Lcrest = float(dams.loc[dam, "geometry"].length)
    eav = pd.read_csv(RESERVOIRS / f"EAV_{dam.replace(' ', '_')}.csv"); zs = eav.elevation_m.values; res = f"{dam} Reservoir"; ta = f"Elev-Area {dam}"; tq = f"Elev-Dis {dam}"
    jb = re.search(r'^Junction: ' + re.escape(dam) + r'\r?\n.*?^End:', basin, re.S | re.M).group(0); down = g(jb, "Downstream"); jx, jy = float(g(jb, "Canvas X")), float(g(jb, "Canvas Y"))
    pt = reach_geom[down].interpolate(150.0) if down in reach_geom else Point(jx + 150, jy); rx, ry = float(pt.x), float(pt.y)
    jb2 = re.sub(r'^(\s*Downstream: ).*$', lambda m: m.group(1) + res, jb, flags=re.M) if down else jb.replace("End:", f"     Downstream: {res}\nEnd:")
    blk = (f"Reservoir: {res}\n     Last Modified Date: {DATE}\n     Last Modified Time: {TIME}\n     Canvas X: {rx}\n     Canvas Y: {ry}\n     From Canvas X: {rx}\n     From Canvas Y: {ry}\n" + (f"     Downstream: {down}\n" if down else "") +
           f"\n     Route: Modified Puls\n     Routing Curve: Elevation-Area-Outflow\n     Initial Elevation: {zs[0]:.1f}\n     Elevation-Area Table: {ta}\n     Elevation-Outflow Table: {tq}\n     Primary Table: Elevation-Area\nEnd:\n")
    basin = basin.replace(jb, jb2 + "\n" + blk)
    if have_res: con.execute("insert into reservoir (GEOMETRY, name) values (?,?)", (wkb.dumps(Point(rx, ry, 0.0)), res))
    added.append(dict(dam=dam, reservoir=res, downstream=down or "", bed=float(zs[0]), fsl=fsl, crest=crest_el, spill_L=L, L_crest=round(Lcrest)))
con.commit(); con.close()
open(ST / "Basin_4.basin", "w", encoding="utf-8", newline="\n").write(basin); shutil.move(ST / "Basin_1.sqlite", ST / "Basin_4.sqlite"); os.remove(ST / "Basin_1.basin")
# ---------------------------------------------------------------- Shafan 08 tables (the other eight exist from Basin 3)
pdata = open(ST / "HEC_HMS_Block_04.pdata", encoding="utf-8").read(); dss = hecdss.HecDss(str(ST / "HEC_HMS_Block_04.dss"))
for dam in DAMS9:
    ta, tq = f"Elev-Area {dam}", f"Elev-Dis {dam}"
    if f"Table: {ta}\n" in pdata: continue
    crest_el = float(dams.loc[dam, "Crest El"]); fsl = float(dams.loc[dam, "FSL"]); C = float(dams.loc[dam, "C"]); L = float(dams.loc[dam, "Spillway L"]); Lcrest = float(dams.loc[dam, "geometry"].length)
    eav = pd.read_csv(RESERVOIRS / f"EAV_{dam.replace(' ', '_')}.csv"); zs = eav.elevation_m.values; areas = eav.area_km2.values * 1e6
    ext = np.arange(zs[-1] + 0.5, crest_el + 5.01, 0.5); slope = (areas[-1] - areas[-4]) / (zs[-1] - zs[-4]); zs_all = np.r_[zs, ext]; a_all = np.r_[areas, areas[-1] + slope * (ext - zs[-1])]
    q = np.where(zs_all > fsl, C * L * np.clip(zs_all - fsl, 0, None) ** 1.5, 0.0) + np.where(zs_all > crest_el, 1.7 * Lcrest * np.clip(zs_all - crest_el, 0, None) ** 1.5, 0.0)
    dss.put(hecdss.PairedData.create(x_values=zs_all.astype(float), y_values=a_all.reshape(-1, 1).astype(float), x_units="M", x_type="Linear", y_units="M2", y_type="Linear", path=f"//{ta}/ELEVATION-AREA///TABLE/"))
    dss.put(hecdss.PairedData.create(x_values=zs_all.astype(float), y_values=q.reshape(-1, 1).astype(float), x_units="M", x_type="Linear", y_units="M3/S", y_type="Linear", path=f"//{tq}/STAGE-FLOW///TABLE/"))
    for tname, ttype, yu, cpart in [(ta, "Elevation-Area", "M2", "ELEVATION-AREA"), (tq, "Stage-Flow", "M3/S", "STAGE-FLOW")]:
        pdata = pdata.rstrip("\n") + f"\n\nTable: {tname}\n     Table Type: {ttype}\n     Last Modified Date: {DATE}\n     Last Modified Time: {TIME}\n     X-Units: M\n     Y-Units: {yu}\n     Use External DSS File: NO\n     DSS File: HEC_HMS_Block_04.dss\n     Pathname: //{tname}/{cpart}///TABLE/\n     Interpolation: Linear Interpolation\nEnd:\n"
    print("tables added for", dam, "| Q at crest", round(float(np.interp(crest_el, zs_all, q))), "m3/s")
dss.close(); open(ST / "HEC_HMS_Block_04.pdata", "w", encoding="utf-8", newline="\n").write(pdata)
# ---------------------------------------------------------------- project, runs, analyses, met
hms = open(ST / "HEC_HMS_Block_04.hms", encoding="utf-8").read()
if "Basin: Basin 4\n" not in hms:
    b3 = re.search(r'^Basin: Basin 3\r?\n.*?^End:\n', hms, re.S | re.M).group(0)
    hms = hms.replace(b3, b3 + f"\nBasin: Basin 4\n     Filename: Basin_4.basin\n     Description: Basin 1 + the nine dam reservoirs (Shafan 08 included)\n     Last Modified Date: {DATE}\n     Last Modified Time: {TIME[:5]}\nEnd:\n")
open(ST / "HEC_HMS_Block_04.hms", "w", encoding="utf-8", newline="\n").write(hms)
run = open(ST / "HEC_HMS_Block_04.run", encoding="utf-8").read()
els4 = bf.parse(ST / "Basin_4.basin"); points = [n for n, e in els4.items() if e["type"] in ("Subbasin", "Junction", "Reach", "Reservoir")]
for rp in RPS:
    if f"Run: FM {rp} B4\n" in run: continue
    blk = re.search(r'^Run: FM ' + rp + r' B3\r?\n.*?^End:\n', run, re.S | re.M).group(0)
    new = blk.replace(f"Run: FM {rp} B3", f"Run: FM {rp} B4").replace(f"FM_{rp}_B3", f"FM_{rp}_B4").replace("Basin: Basin 3", "Basin: Basin 4")
    new = re.sub(r'^(\s*Last Modified Date: ).*$', r'\g<1>' + DATE, new, flags=re.M); new = re.sub(r'^(\s*Last Modified Time: ).*$', r'\g<1>' + TIME, new, flags=re.M)
    run = run.rstrip("\n") + "\n\n" + new
open(ST / "HEC_HMS_Block_04.run", "w", encoding="utf-8", newline="\n").write(run)
nals = open(ST / "HEC_HMS_Block_04.nals", encoding="utf-8").read()
for rp in RPS:
    if f"Analysis: DA {rp} B4\n" in nals: continue
    blk = re.search(r'^Analysis: DA ' + rp + r' B3\r?\n.*?^End:\n', nals, re.S | re.M).group(0)
    head = blk.split("     Analysis Point:")[0]; tail = "     Time-Series Output: Save All\n     Time Series Results Manager Start:\n     Time Series Results Manager End:\nEnd:\n"
    head = head.replace(f"Analysis: DA {rp} B3", f"Analysis: DA {rp} B4").replace(f"DA_{rp}_B3.dss", f"DA_{rp}_B4.dss").replace("Basin Model Name: Basin 3", "Basin Model Name: Basin 4")
    head = re.sub(r'^\s*Last Execution (Date|Time): .*\n', '', head, flags=re.M)
    nals = nals.rstrip("\n") + "\n\n" + head + "".join(f"     Analysis Point: {p}\n" for p in points) + tail
open(ST / "HEC_HMS_Block_04.nals", "w", encoding="utf-8", newline="\n").write(nals)
for rp in RPS:
    p = ST / f"FM_{rp}.met"; m = open(p, encoding="utf-8").read()
    if "Use Basin Model: Basin 4" not in m: m = m.replace("     Use Basin Model: Basin 3\n", "     Use Basin Model: Basin 3\n     Use Basin Model: Basin 4\n", 1); open(p, "w", encoding="utf-8", newline="\n").write(m)
print(pd.DataFrame(added).to_string(index=False)); print("Basin 4 elements:", {t: sum(1 for e in els4.values() if e["type"] == t) for t in ("Subbasin", "Junction", "Reach", "Reservoir")}, "| analysis points:", len(points))
subprocess.run([sys.executable, str(Path(__file__).resolve().parents[2] / "scripts" / "validate_basin.py"), str(ST / "Basin_4.basin")], check=False)
if INSTALL:
    if any(p.name.lower().startswith("hec-hms") for p in Path("C:/").glob("*")): pass
    bk = HMS / f"_backup_before_basin4_{now:%Y%m%d_%H%M%S}"; bk.mkdir(exist_ok=True)
    for f in FILES: shutil.copy2(HMS / f, bk / f)
    for f in ["HEC_HMS_Block_04.hms", "HEC_HMS_Block_04.run", "HEC_HMS_Block_04.nals", "HEC_HMS_Block_04.pdata", "HEC_HMS_Block_04.dss", "Basin_4.basin", "Basin_4.sqlite"] + [f"FM_{rp}.met" for rp in RPS]: shutil.copy2(ST / f, HMS / f)
    print("installed into", HMS, "| previous files in", bk)
