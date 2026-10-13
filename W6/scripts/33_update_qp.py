"""Step 33 - fill the three new points of the engineer's flow file Hydraulic/SHP/tmp/Qp Vol Block 04.shp with the peak
flow (Q<rp>, m3/s) and volume (V<rp>, Mm3) of the 13 return periods, depth-area results at the element's own analysis point
as every other row of the file:
  * SAR-S11 and HAW-S14: the Basin 3 subbasins of the same name (results/basin3_peak_flow_volume_long.csv)
  * "SHA-CH13-SS GB0": renamed to the new Basin 5 subbasin (hms/basin5_peak_flow_volume_long.csv from 30/34), type Subbasin
The file is rewritten in place; the original is copied to '<name>_before_<stamp>.*' beside it and the result also to output/.
    python 33_update_qp.py [--new-name SHA-S51]"""
import os, sys, shutil, time, glob
import geopandas as gpd, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE); CB = os.path.dirname(W6)
QP = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydraulic\SHP\tmp\Qp Vol Block 04.shp"
RPS = ["2", "5", "10", "25", "50", "100", "200", "500", "1000", "2000", "5000", "10000", "PMP"]
NEW = sys.argv[sys.argv.index("--new-name") + 1] if "--new-name" in sys.argv else "SHA-S51"
LOG = os.path.join(W6, "log", "33_update_qp.log")


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + "  " + msg; print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")


def table(csv_path):
    df = pd.read_csv(csv_path); df["rp"] = df["rp"].str.replace("yr", ""); return df


b3 = table(os.path.join(CB, "results", "basin3_peak_flow_volume_long.csv"))
b5p = os.path.join(W6, "hms", "basin5_peak_flow_volume_long.csv"); b5 = table(b5p) if os.path.exists(b5p) else None
g = gpd.read_file(QP); stamp = time.strftime("%Y%m%d_%H%M")
for f in glob.glob(QP[:-4] + ".*"): shutil.copy2(f, f.replace("Qp Vol Block 04", "Qp Vol Block 04_before_%s" % stamp))
log("backup copies: Qp Vol Block 04_before_%s.*" % stamp)


def fill(idx, element, src, downstream=None):
    rows = src[src.element == element]
    if rows.empty: log("NO RESULTS for %s" % element); return False
    for _, r in rows.iterrows():
        g.loc[idx, "Q" + r["rp"]] = round(float(r["peak_m3s"]), 3); g.loc[idx, "V" + r["rp"]] = round(float(r["vol_Mm3"]), 4)
    g.loc[idx, "type"] = rows.iloc[0]["type"]; g.loc[idx, "x"] = round(g.loc[idx, "geometry"].x, 1); g.loc[idx, "y"] = round(g.loc[idx, "geometry"].y, 1)
    if downstream: g.loc[idx, "downstream"] = downstream
    log("%s filled: Q200 %.1f m3/s, QPMP %.1f m3/s, %d return periods" % (g.loc[idx, "name"], g.loc[idx, "Q200"], g.loc[idx, "QPMP"], len(rows))); return True


import re
b3txt = open(r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydrology\HEC_HMS_Block_04\Basin_3.basin", encoding="utf-8").read()
def downstream_of(name):
    m = re.search(r"^Subbasin: " + re.escape(name) + r"\r?\n.*?^\s*Downstream: (.*?)\r?$", b3txt, re.S | re.M); return m.group(1).strip() if m else None
done = []
for name in ("SAR-S11", "HAW-S14"):
    idx = g.index[g["name"] == name]
    if len(idx) != 1: log("point %s not found once in the file (%d)" % (name, len(idx))); continue
    if fill(idx[0], name, b3, downstream_of(name)): done.append(name)
idx = g.index[g["name"].isin(["SHA-CH13-SS GB0", NEW])]
if len(idx) == 1 and b5 is not None:
    g.loc[idx[0], "name"] = NEW
    if fill(idx[0], NEW, b5, "SHA-J52"): done.append(NEW)
elif len(idx) == 1: log("Basin 5 results not available yet (%s missing): %s left unfilled" % (b5p, g.loc[idx[0], "name"]))
else: log("point SHA-CH13-SS GB0 / %s not found once (%d)" % (NEW, len(idx)))
os.makedirs(os.path.join(W6, "output"), exist_ok=True); g.to_file(os.path.join(W6, "output", "Qp Vol Block 04.shp")); g.drop(columns="geometry").to_csv(os.path.join(W6, "output", "Qp Vol Block 04.csv"), index=False)
log("written W6/output/Qp Vol Block 04.shp (%d points; filled now: %s)" % (len(g), done))
try: g.to_file(QP); log("engineer's file updated in place: %s" % QP)
except PermissionError as ex: log("engineer's file is locked (open in QGIS?): %s -- not updated; the W6/output copy is current" % ex)
