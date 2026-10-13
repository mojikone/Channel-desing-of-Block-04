"""Step 62 (W7) - the design flows refreshed from Basin 6 (Shafan 08 included, step 60/61), everything else untouched:
  * the engineer's flow file Hydraulic/SHP/tmp/Qp Vol Block 04.shp is READ ONLY; its W7 copy inputs/Qp Vol Block 04.shp gets the
    Q<rp> (m3/s) and V<rp> (Mm3) of every row whose name is a Basin 6 element whose PEAK moved (the Shafan line below the dam; rows
    whose peaks are unchanged keep his values, their volumes differ from the new export by rounding only; SHA-S51 is Basin 5);
  * the final point layer of W6 (final/Block4_design_points.shp by step 37: geometry, GDP, raise and SewerGEMS names unchanged) is
    read and written to W7/final with the same 26 fields refreshed by name (repeatable: W6 stays the source);
  * inputs/62_flow_changes.csv lists every value that moved (file row or design point, return period, old, new, difference).
    python 62_update_flows.py"""
import os, shutil, pandas as pd, geopandas as gpd
HERE = os.path.dirname(os.path.abspath(__file__)); W7 = os.path.dirname(HERE); CB = os.path.dirname(W7)
QP = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydraulic\SHP\tmp\Qp Vol Block 04.shp"
RPS = ["2", "5", "10", "25", "50", "100", "200", "500", "1000", "2000", "5000", "10000", "PMP"]
b6 = pd.read_csv(os.path.join(CB, "results", "basin6_peak_flow_volume_long.csv"))
b6["rp"] = b6.rp.str.replace("yr", ""); q = b6.pivot(index="element", columns="rp", values="peak_m3s"); v = b6.pivot(index="element", columns="rp", values="vol_Mm3")
changes = []
def refresh(df, where, key="name"):
    hit = 0
    for i, r in df.iterrows():
        n = str(r[key]).strip()
        if n not in q.index: continue
        if not any(abs(round(float(q.loc[n, rp]), 3) - float(r["Q" + rp])) > 0.0005 for rp in RPS if pd.notna(r["Q" + rp])): continue   # no peak moved: the row stays his (volumes differ by rounding only)
        hit += 1
        for rp in RPS:
            for fld, src in (("Q" + rp, q), ("V" + rp, v)):
                old = float(r[fld]) if pd.notna(r[fld]) else float("nan"); new = round(float(src.loc[n, rp]), 3)
                if pd.isna(old) or abs(new - old) > 0.0005:
                    df.at[i, fld] = new
                    changes.append(dict(where=where, row=str(r.get("SGLabel", r.get("Label", ""))) or n, name=n, field=fld, old=old, new=new, diff=round(new - old, 3) if pd.notna(old) else None))
    return hit
# the flow file -> W7 copy
g = gpd.read_file(QP); n0 = len(g); hit = refresh(g, "flow file")
out = os.path.join(W7, "inputs", "Qp Vol Block 04.shp"); os.makedirs(os.path.dirname(out), exist_ok=True); g.to_file(out)
print("flow file: %d rows, %d named Basin 6 elements refreshed -> %s" % (n0, hit, out))
# the final point layer (W7 copy of W6's) -> same fields by name
pts_shp = os.path.join(W7, "final", "Block4_design_points.shp")
p = gpd.read_file(os.path.join(CB, "W6", "final", "Block4_design_points.shp")); hitp = refresh(p, "design points")   # from the W6 original, so the run is repeatable
p.to_file(pts_shp); p.drop(columns="geometry").to_csv(os.path.join(W7, "final", "Block4_design_points.csv"), index=False)
print("design points: %d, %d named Basin 6 elements refreshed" % (len(p), hitp))
ch = pd.DataFrame(changes); ch.to_csv(os.path.join(W7, "inputs", "62_flow_changes.csv"), index=False)
pt = ch[(ch["where"] == "design points") & (ch.field == "Q200")]
print("values moved: %d (flow file %d, design points %d); design points with a new Q200:" % (len(ch), (ch["where"] == "flow file").sum(), (ch["where"] == "design points").sum()))
print(pt[["row", "name", "old", "new", "diff"]].to_string(index=False) if len(pt) else "  none")
