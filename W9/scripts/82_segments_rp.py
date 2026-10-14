"""Step 82 (W9, engineer 2026-10-14) - three GIS products from the SewerGEMS R9 design:
  * the channel segment layer with the designed size of every reach for all eight return periods (2 to 500 years): span, rise,
    size text and flow per return period, from the class-resolved exports of the R9 run -> W9/gis/segments_all_rp.gpkg + .shp
  * the channel extents per return period, bed and corridor in one shapefile each (field kind): bed = the reach buffered by half
    its designed bed width, corridor = bed + 15.5 m each side (embankment 11.5 m + access road 4 m, as the 200-year corridor of W7)
    -> W9/gis/extents/extent_<rp>.shp
  * the dyke extent: the fill-channel allowance of 15.5 m each side of the dyke line ("consider same as fill channel")
    -> W9/gis/dyke_extent.shp
    python 82_segments_rp.py [--run run_20261012_1758]"""
import os, sys
import pandas as pd, geopandas as gpd
from shapely.ops import unary_union
HERE = os.path.dirname(os.path.abspath(__file__)); W9 = os.path.dirname(HERE); CB = os.path.dirname(W9); B4 = os.path.dirname(CB); W7 = os.path.join(CB, "W7")
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
RUN = opt("--run", "run_20261012_1758"); RPS = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr"]; EXTRA = 15.5
OUT = os.path.join(W9, "gis"); os.makedirs(os.path.join(OUT, "extents"), exist_ok=True)
seg = gpd.read_file(os.path.join(W7, "final", "Block4_design_segments.shp"))[["SGLabel", "Channel", "Class", "Seg", "FromSta", "ToSta", "Length", "SGFrom", "SGTo", "geometry"]]
for rp in RPS:
    c = pd.read_csv(os.path.join(W7, "sewergems", "results", RUN, "bridge_exports", f"conduits_{rp}.csv")).set_index("label")
    k = rp.replace("yr", "")
    seg[f"span_{k}"] = seg.SGLabel.map(c["span_m"]).astype(float).round(1); seg[f"rise_{k}"] = seg.SGLabel.map(c["rise_m"]).astype(float).round(1)
    seg[f"Q_{k}"] = seg.SGLabel.map(c["flow"]).astype(float).round(1); seg[f"size_{k}"] = [f"{a:.1f} x {b:.1f} m" for a, b in zip(seg[f"span_{k}"], seg[f"rise_{k}"])]
    seg[f"slope_{k}"] = seg.SGLabel.map(c["slope"]).astype(float).round(5)
print("segments", len(seg), "| columns", len(seg.columns))
gp = os.path.join(OUT, "segments_all_rp.gpkg")
if os.path.exists(gp): os.remove(gp)
seg.to_file(gp, layer="segments", driver="GPKG"); seg.to_file(os.path.join(OUT, "segments_all_rp.shp"))
# extents per return period
for rp in RPS:
    k = rp.replace("yr", "")
    bed = unary_union([ln.buffer(sp / 2.0, cap_style=2) for ln, sp in zip(seg.geometry, seg[f"span_{k}"])])
    cor = unary_union([ln.buffer(sp / 2.0 + EXTRA, cap_style=2) for ln, sp in zip(seg.geometry, seg[f"span_{k}"])])
    g = gpd.GeoDataFrame({"kind": ["bed", "corridor"], "rp_years": [int(k), int(k)], "note": [f"designed bed width, {k}-year flow", f"bed + {EXTRA} m each side (embankment and access road)"]}, geometry=[bed, cor], crs=seg.crs)
    g.to_file(os.path.join(OUT, "extents", f"extent_{k}yr.shp")); print(f"extent_{k}yr: bed {bed.area / 1e4:.0f} ha, corridor {cor.area / 1e4:.0f} ha")
# dyke extent
dy = gpd.read_file(os.path.join(B4, "Hydrology", "SHP", "temp", "Channels and Dykes 04102026.shp")); dy = dy[(dy["Block"] == 4) & dy["CHtt"].astype(str).str.endswith(" D")].copy()
dy["extent_m"] = 2 * EXTRA; dy["geometry"] = dy.geometry.buffer(EXTRA, cap_style=2)
dy[["Name", "CHtt", "extent_m", "geometry"]].to_file(os.path.join(OUT, "dyke_extent.shp")); print("dyke extents", len(dy), "%.0f ha" % (dy.area.sum() / 1e4))
print("done ->", OUT)
