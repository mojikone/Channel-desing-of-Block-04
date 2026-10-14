"""88_hecras_conduits.py - the SewerGEMS R9 conduit export with the designed sizes resolved, for the HEC-RAS check.

His GUI export (SHP/from SewerGEMS/Channels.shp in the model share) carries SPAN = 10 for every conduit (the conduit's stored
span, which SewerGEMS never updates for catalogue conduits: the design assigns a catalogue item) and SIZE = that item's GUID.
The designed sizes live behind the catalogue reference and were resolved by class + GUID in W7 (gis/sewergems_200yr_R9.gpkg,
layer segments, 200-year) and for every return period in W9 (gis/segments_all_rp.gpkg). This script joins them onto his
geometry by the conduit label and writes a NEW shapefile next to his export (his file is never touched) plus a copy in W9.
"""
import os, geopandas as gpd, pandas as pd
W = "D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Claude Block 04"
SRC = "C:/Users/mojtaba/Desktop/Win10 shared folder/SewerGEMS Block 04 11102026/SHP/from SewerGEMS/Channels.shp"
OUT_SHARE = os.path.dirname(SRC) + "/Channels_R9_designed_sizes.shp"
OUT_W9 = W + "/W9/gis/hecras/Channels_R9_designed_sizes.shp"
RPS = [2, 5, 10, 25, 50, 100, 200, 500]
his = gpd.read_file(SRC)
seg = gpd.read_file(W + "/W7/gis/sewergems_200yr_R9.gpkg", layer="segments")
rp = gpd.read_file(W + "/W9/gis/segments_all_rp.gpkg")
print("his export:", len(his), "conduits; crs", his.crs, "; bounds", [round(v) for v in his.total_bounds])
print("R9 segments:", len(seg), "crs", seg.crs, "; all-RP:", len(rp))
m = his.merge(seg.drop(columns="geometry"), left_on="LABEL", right_on="SGLabel", how="left", validate="one_to_one")
miss = m[m.SGLabel.isna()].LABEL.tolist(); print("unmatched labels:", len(miss), miss[:10])
m = m.merge(rp.drop(columns="geometry")[["SGLabel", "Class", "Seg"] + [f"{k}_{r}" for r in RPS for k in ("span", "rise", "Q", "slope")]], on="SGLabel", how="left")
for a, b in [("INV_STRT", "start_inv"), ("INV_STP", "stop_inv"), ("S", "slope"), ("RISE", "rise_m"), ("LENGTH_(SC", "Length")]:
    d = (m[a].astype(float) - m[b].astype(float)).abs(); print(f"check his {a} vs resolved {b}: max |diff| = {d.max():.3f}, mean = {d.mean():.4f}")
print("his SPAN values:", sorted(m.SPAN.unique()), "; resolved width range:", m.span_m.min(), "-", m.span_m.max(), "; size_label e.g.", m.size_label.iloc[0])
print("W9 span_200 vs W7 span_m: max |diff| =", (m.span_200.astype(float) - m.span_m.astype(float)).abs().max())
crs = his.crs or seg.crs
out = gpd.GeoDataFrame({
    "LABEL": m.LABEL, "CHANNEL": m.Channel, "CLASS": m.Class, "FROM_NODE": m.START_NODE, "TO_NODE": m.STOP_NOD2,
    "LENGTH_M": m["LENGTH_(SC"].astype(float).round(1), "INV_UP_M": m.INV_STRT.astype(float).round(3), "INV_DN_M": m.INV_STP.astype(float).round(3),
    "SLOPE": m.S.astype(float).round(5), "SHAPE": m.COND_SHAPE, "CLASS_SG": m.SECT_SIZE, "WIDTH_M": m.span_m.astype(float).round(1),
    "DEPTH_M": m.rise_m.astype(float).round(1), "SIZE": m.size_label, "MANN_N": m.MANN_N.astype(float), "Q200_M3S": m.flow.astype(float).round(1),
    "V200_MS": m.velocity.astype(float).round(2), "Y200_IN_M": m.depthin.astype(float).round(2), "Y200_OUT_M": m.depthout.astype(float).round(2)},
    geometry=m.geometry, crs=crs)
for r in RPS:
    out[f"W_{r}"] = m[f"span_{r}"].astype(float).round(1); out[f"D_{r}"] = m[f"rise_{r}"].astype(float).round(1)
    out[f"Q_{r}"] = m[f"Q_{r}"].astype(float).round(1); out[f"S_{r}"] = m[f"slope_{r}"].astype(float).round(5)
assert all(len(c) <= 10 for c in out.columns), [c for c in out.columns if len(c) > 10]
assert out.WIDTH_M.notna().all() and out.LABEL.is_unique
for p in (OUT_SHARE, OUT_W9):
    os.makedirs(os.path.dirname(p), exist_ok=True); out.to_file(p, driver="ESRI Shapefile"); print("written", p, len(out), "crs", out.crs)
    with open(os.path.splitext(p)[0] + "_README.txt", "w", encoding="utf-8") as fh:
        print("Block 04 - conduits of the SewerGEMS hydraulic design, revision R9, with the designed sizes (for the HEC-RAS check)", file=fh)
        print("", file=fh)
        print("Geometry: the 212 conduits as exported from SewerGEMS (same lines and node labels as Channels.shp / Nodes.shp). CRS: WGS 84 / UTM zone 40N (EPSG:32640).", file=fh)
        print("Do not use SPAN or SIZE of Channels.shp: SPAN there is the conduit's stored value (10 m for all, never updated for catalogue conduits) and SIZE is the catalogue item identifier. The designed sizes are in this file.", file=fh)
        print("", file=fh)
        print("Section: rectangular (SewerGEMS catalogue class 'Rect- Natural', Manning n 0.030), WIDTH_M = designed bed width at 200 years, DEPTH_M = clear depth of the class (2.5 m, 3.0 m where deeper).", file=fh)
        print("Fields: LABEL conduit; CHANNEL, CLASS channel and class (FP flood protection, Sw M stormwater main, Sw S stormwater secondary); FROM_NODE, TO_NODE node labels;", file=fh)
        print("  LENGTH_M; INV_UP_M, INV_DN_M upstream and downstream inverts (m, 200-year scenario); SLOPE (m/m); SHAPE, CLASS_SG SewerGEMS shape and class; SIZE as text 'depth x width';", file=fh)
        print("  Q200_M3S design flow 200-year (m3/s); V200_MS velocity; Y200_IN_M, Y200_OUT_M flow depth at the upstream and downstream ends (200-year, GVF).", file=fh)
        print("  W_<rp>, D_<rp>, Q_<rp>, S_<rp>: designed width, depth, flow and slope of the scenario of each return period (2, 5, 10, 25, 50, 100, 200, 500 years); the inverts of those scenarios differ from the 200-year ones where the slope differs.", file=fh)
        print("", file=fh)
        print("Source: SewerGEMS Block 04 R9 (all eight scenarios designed), sizes resolved per conduit from the catalogue class and item.", file=fh)
print(out.drop(columns="geometry").head(3).T.to_string())
