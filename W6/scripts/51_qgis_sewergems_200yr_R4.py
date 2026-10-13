"""Step 51 - the 200 yr design on revision R4 as GIS layers for the engineer's QGIS project (his request of 2026-10-12), in one
GeoPackage W6/gis/sewergems_200yr_R4.gpkg:
  segments     the SewerGEMS conduits on the final segment geometry: SGLabel, designed width (span), slope, inverts, flow, velocity
  manholes     the model's manholes from the nodes export (x, y are the model coordinates, UTM 40N): ground, invert
  outfalls     the model's outfalls, same fields
  channels     the 37 oriented channel alignments (the sheet pipeline's Channels.shp)
  bed          the designed span, dissolved (the sheet pipeline's Channel Bed Buffer)
  corridor     span + 15.5 m each side, dissolved (Channels Buffer)
  chk_inverts  TEMPORARY: nodes whose invert moved between the R3 and the R4 run (> 1 cm): inv_r3, inv_r4, d_inv
  chk_conduits TEMPORARY: conduits whose size, slope or an invert changed between R3 and R4: span/slope old and new, d_slope
    python 51_qgis_sewergems_200yr_R4.py [--new run_20261012_0850] [--old run_20261012_0031] [--scenario 200yr] [--rev R4]
"""
import os, sys
import pandas as pd, geopandas as gpd
from shapely.geometry import Point
HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE)
A = sys.argv[1:]
def opt(k, d): return A[A.index(k) + 1] if k in A else d
NEW = opt("--new", "run_20261012_0850"); OLD = opt("--old", "run_20261012_0031"); SC = opt("--scenario", "200yr"); REV = opt("--rev", "R4")
SHEETS = os.path.join(W6, "sewergems", "sheets", "scripts"); OUT = os.path.join(W6, "gis", "sewergems_%s_%s.gpkg" % (SC, REV))
CRS = "EPSG:32640"
def exp(run, kind): return pd.read_csv(os.path.join(W6, "sewergems", "results", run, "bridge_exports", "%s_%s.csv" % (kind, SC)))

cn, co = exp(NEW, "conduits"), exp(OLD, "conduits"); nn, no = exp(NEW, "nodes"), exp(OLD, "nodes")
seg = gpd.read_file(os.path.join(W6, "final", "Block4_design_segments.shp"))[["SGLabel", "Channel", "Label", "FromNode", "ToNode", "Length", "geometry"]]
if os.path.exists(OUT): os.remove(OUT)

# segments with the R4 design
keep = ["label", "size_label", "span_m", "rise_m", "material", "slope", "start_inv", "stop_inv", "flow", "velocity", "depthin", "depthout", "start", "stop"]
s = seg.merge(cn[keep].rename(columns={"label": "SGLabel", "start": "SGFrom", "stop": "SGTo"}), on="SGLabel", how="left")
s["width_m"] = s["span_m"]; s["slope_pct"] = (s["slope"] * 100).round(3)
s.to_file(OUT, layer="segments", driver="GPKG"); print("segments", len(s), "| without a conduit:", int(s["span_m"].isna().sum()))

# nodes
nodes = gpd.GeoDataFrame(nn, geometry=[Point(x, y) for x, y in zip(nn["x"], nn["y"])], crs=CRS)
for typ, name in (("MH", "manholes"), ("OF", "outfalls")):
    g = nodes[nodes["type"] == typ][["label", "type", "ground", "invert", "geometry"]].copy(); g["depth_m"] = (g["ground"] - g["invert"]).round(2)
    g.to_file(OUT, layer=name, driver="GPKG"); print(name, len(g))

# channels, bed, corridor from the sheet pipeline (already the R4 200-yr widths)
gpd.read_file(os.path.join(SHEETS, "Data", "SHP", "Channels.shp")).to_file(OUT, layer="channels", driver="GPKG")
gpd.read_file(os.path.join(SHEETS, "Data", "SHP", "Buffers", "Channel Bed Buffer.shp")).to_file(OUT, layer="bed", driver="GPKG")
gpd.read_file(os.path.join(SHEETS, "Data", "SHP", "Buffers", "Channels Buffer.shp")).to_file(OUT, layer="corridor", driver="GPKG")

# TEMPORARY check layers: R3 -> R4
j = nn.merge(no[["label", "invert", "ground"]], on="label", how="inner", suffixes=("", "_r3"))
j["inv_r3"] = j["invert_r3"].round(3); j["inv_r4"] = j["invert"].round(3); j["d_inv"] = (j["inv_r4"] - j["inv_r3"]).round(3)
chk = j[j["d_inv"].abs() > 0.01][["label", "type", "ground", "inv_r3", "inv_r4", "d_inv", "x", "y"]]
chk = gpd.GeoDataFrame(chk, geometry=[Point(x, y) for x, y in zip(chk["x"], chk["y"])], crs=CRS).drop(columns=["x", "y"])
chk.to_file(OUT, layer="chk_inverts", driver="GPKG"); print("chk_inverts", len(chk), "| raised", int((chk["d_inv"] > 0).sum()), "lowered", int((chk["d_inv"] < 0).sum()))
c = cn.merge(co[["label", "size", "span_m", "slope", "start_inv", "stop_inv"]], on="label", suffixes=("", "_r3"))
c["span_r3"] = c["span_m_r3"]; c["span_r4"] = c["span_m"]; c["slope_r3"] = c["slope_r3"]; c["slope_r4"] = c["slope"]
c["d_slope"] = (c["slope_r4"] - c["slope_r3"]).round(6); c["d_span"] = (c["span_r4"] - c["span_r3"]).round(1)
c["d_start_inv"] = (c["start_inv"] - c["start_inv_r3"]).round(3); c["d_stop_inv"] = (c["stop_inv"] - c["stop_inv_r3"]).round(3)
changed = c[(c["size"] != c["size_r3"]) | (c["d_slope"].abs() > 1e-6) | (c["d_start_inv"].abs() > 0.01) | (c["d_stop_inv"].abs() > 0.01)]
cc = seg[["SGLabel", "Channel", "geometry"]].merge(changed[["label", "span_r3", "span_r4", "d_span", "slope_r3", "slope_r4", "d_slope", "start_inv", "stop_inv", "d_start_inv", "d_stop_inv", "flow"]].rename(columns={"label": "SGLabel"}), on="SGLabel", how="inner")
cc.to_file(OUT, layer="chk_conduits", driver="GPKG"); print("chk_conduits", len(cc), "| slope up", int((cc["d_slope"] > 1e-6).sum()), "down", int((cc["d_slope"] < -1e-6).sum()), "unchanged slope", int((cc["d_slope"].abs() <= 1e-6).sum()))
print("->", OUT)
