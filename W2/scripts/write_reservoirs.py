"""Add the 8 dam reservoirs to Basin 2 (HMS project files), just downstream of each dam junction.
Storage: Elevation-Area table from reservoirs/EAV_<dam>.csv (10 m DEM, crest polygon).
Outflow: Elevation-Discharge table = broad-crested spillway Q = C L H^1.5 above FSL (C, L from 'Dams updated.shp')
         + overtopping over the dam crest (C 1.7, crest length) above crest level, tabulated to crest + 5 m.
Syntax as the Qashab HMS model (Modified Puls, Elevation-Area-Outflow). usage: python write_reservoirs.py <HMS folder> [--install]
"""
import sys, os, re, shutil, sqlite3, datetime, numpy as np, pandas as pd, geopandas as gpd, hecdss
from shapely import wkb
from shapely.geometry import Point
HMS = sys.argv[1].rstrip("/\\") + "/"; INSTALL = "--install" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "reservoirs") + "/"
S = "W:/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/06-WORKING/04-Hydraulic/05 Small Tasks/18 Channel Design/SHP/Block 04 Dams/"
dams = gpd.read_file(S + "Dams updated.shp"); dams = dams[dams["Dam Name"] != "Shafan 08"]
now = datetime.datetime.now(); DATE = now.strftime("%d %B %Y").lstrip("0"); TIME = now.strftime("%H:%M:%S")
OUT = HERE + "/reservoirs/hms/"; os.makedirs(OUT, exist_ok=True)
for f in ["Basin_2.basin", "Basin_2.sqlite", "HEC_HMS_Block_04.pdata", "HEC_HMS_Block_04.dss", "HEC_HMS_Block_04.nals"]: shutil.copy2(HMS + f, OUT + f)
basin = open(OUT + "Basin_2.basin", encoding="utf-8").read(); pdata = open(OUT + "HEC_HMS_Block_04.pdata", encoding="utf-8").read(); nals = open(OUT + "HEC_HMS_Block_04.nals", encoding="utf-8").read()
g = lambda s, k: (re.search(r'^\s*' + re.escape(k) + r': (.*)$', s, re.M) or [None, None])[1]
dss = hecdss.HecDss(OUT + "HEC_HMS_Block_04.dss")
con = sqlite3.connect(OUT + "Basin_2.sqlite")
reach_geom = {n: wkb.loads(gg) for gg, n in con.execute("select GEOMETRY, name from reach2d")}
added = []
for d in dams.itertuples():
    name = d[1]; crest_el = float(d[2]); fsl = float(d[3]); C = float(d[7]); L = float(d[8]); Lcrest = float(d.geometry.length)
    res = f"{name} Reservoir"; ta = f"Elev-Area {name}"; tq = f"Elev-Dis {name}"
    eav = pd.read_csv(RES + f"EAV_{name.replace(' ', '_')}.csv")
    # --- extend tables above crest (dam overtopping) so HMS never extrapolates
    zs = eav.elevation_m.values; areas = eav.area_km2.values * 1e6
    ext = np.arange(zs[-1] + 0.5, crest_el + 5.01, 0.5); slope = (areas[-1] - areas[-4]) / (zs[-1] - zs[-4]) if len(zs) > 4 else 0
    zs_all = np.r_[zs, ext]; a_all = np.r_[areas, areas[-1] + slope * (ext - zs[-1])]
    q = np.where(zs_all > fsl, C * L * np.clip(zs_all - fsl, 0, None) ** 1.5, 0.0) + np.where(zs_all > crest_el, 1.7 * Lcrest * np.clip(zs_all - crest_el, 0, None) ** 1.5, 0.0)
    # --- DSS paired data
    pa = hecdss.PairedData.create(x_values=zs_all.astype(float), y_values=a_all.reshape(-1, 1).astype(float), x_units="M", x_type="Linear", y_units="M2", y_type="Linear", path=f"//{ta}/ELEVATION-AREA///TABLE/")
    pq = hecdss.PairedData.create(x_values=zs_all.astype(float), y_values=q.reshape(-1, 1).astype(float), x_units="M", x_type="Linear", y_units="M3/S", y_type="Linear", path=f"//{tq}/STAGE-FLOW///TABLE/")
    dss.put(pa); dss.put(pq)
    # --- pdata entries
    for tname, ttype, yu, cpart in [(ta, "Elevation-Area", "M2", "ELEVATION-AREA"), (tq, "Stage-Flow", "M3/S", "STAGE-FLOW")]:
        if f"Table: {tname}\n" not in pdata:
            pdata = pdata.rstrip("\n") + f"\n\nTable: {tname}\n     Table Type: {ttype}\n     Last Modified Date: {DATE}\n     Last Modified Time: {TIME}\n     X-Units: M\n     Y-Units: {yu}\n     Use External DSS File: NO\n     DSS File: HEC_HMS_Block_04.dss\n     Pathname: //{tname}/{cpart}///TABLE/\n     Interpolation: Linear Interpolation\nEnd:\n"
    # --- basin: junction -> reservoir -> old downstream reach
    jb = re.search(r'^Junction: ' + re.escape(name) + r'\n.*?^End:', basin, re.S | re.M).group(0)
    down = g(jb, "Downstream"); jx, jy = float(g(jb, "Canvas X")), float(g(jb, "Canvas Y"))
    if down and down.endswith("Reservoir"): print(name, "already has a reservoir"); continue
    # position 150 m along the downstream reach geometry (or 150 m east if no geometry)
    pt = reach_geom[down].interpolate(150.0) if down in reach_geom else Point(jx + 150, jy)
    rx, ry = float(pt.x), float(pt.y)
    jb2 = re.sub(r'^(\s*Downstream: ).*$', lambda m: m.group(1) + res, jb, flags=re.M); basin = basin.replace(jb, jb2)
    blk = (f"Reservoir: {res}\n     Last Modified Date: {DATE}\n     Last Modified Time: {TIME}\n     Canvas X: {rx}\n     Canvas Y: {ry}\n     From Canvas X: {rx}\n     From Canvas Y: {ry}\n     Downstream: {down}\n\n"
           f"     Route: Modified Puls\n     Routing Curve: Elevation-Area-Outflow\n     Initial Elevation: {zs[0]:.1f}\n     Elevation-Area Table: {ta}\n     Elevation-Outflow Table: {tq}\n     Primary Table: Elevation-Area\nEnd:\n")
    basin = basin.replace(jb2, jb2 + "\n" + blk)
    con.execute("insert into reservoir (GEOMETRY, name) values (?,?)", (wkb.dumps(Point(rx, ry, 0.0)), res))
    # --- analysis points in the 13 Basin 2 depth-area analyses
    nals = re.sub(r'(^Analysis: DA [^\n]* B2\n.*?)(^End:)', lambda m: m.group(1) + (f"     Analysis Point: {res}\n" if f"Analysis Point: {res}\n" not in m.group(1) else "") + m.group(2), nals, flags=re.S | re.M)
    added.append(dict(reservoir=res, after=name, downstream=down, x=round(rx), y=round(ry), bed=zs[0], fsl=fsl, crest=crest_el, spill_L=L, C=C, Q_at_crest=round(float(np.interp(crest_el, zs_all, q))), Q_crest_plus2=round(float(np.interp(crest_el + 2, zs_all, q))), table_rows=len(zs_all)))
dss.close(); con.commit(); con.close()
open(OUT + "Basin_2.basin", "w", encoding="utf-8", newline="\n").write(basin); open(OUT + "HEC_HMS_Block_04.pdata", "w", encoding="utf-8", newline="\n").write(pdata); open(OUT + "HEC_HMS_Block_04.nals", "w", encoding="utf-8", newline="\n").write(nals)
df = pd.DataFrame(added); pd.set_option("display.width", 250); print(df.to_string(index=False)); df.to_csv(RES + "reservoirs_added.csv", index=False)
if INSTALL:
    bk = HMS + f"_backup_before_reservoirs_{now:%Y%m%d_%H%M%S}/"; os.makedirs(bk, exist_ok=True)
    for f in ["Basin_2.basin", "Basin_2.sqlite", "HEC_HMS_Block_04.pdata", "HEC_HMS_Block_04.dss", "HEC_HMS_Block_04.nals"]: shutil.copy2(HMS + f, bk + f); shutil.copy2(OUT + f, HMS + f)
    print("installed; previous files in", bk)
