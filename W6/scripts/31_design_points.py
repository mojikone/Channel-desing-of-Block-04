"""Step 31 - the channel design points (engineer's method, 2026-10-10), from the W5 geometry, the reviewed GDP profiles
and the ground profiles of the drawing:
  * flow points   - the HMS points of Hydraulic/SHP/tmp/Qp Vol Block 04.shp snapped to the channels (station, GDP and ground elevation)
  * junctions     - a channel's end on a receiving channel (higher class first: FP > SM > SS): the receiver's station,
                    its GDP and ground elevation there, the tributary's GDP end elevation, the nearest GDP break of the receiver
  * fix points    - Hydraulic/SHP/tmp/fix points.shp snapped to the channels (station, ground, GDP), bed = ground there
  * fix downstream- 500 m downstream of every Road-OQ fix point along its channel (none for outfalls)
Outputs: output/design_points.gpkg (four layers) + CSVs, gis/*.qml (nested circle sizes: flow 7 mm hollow blue, junction
5 mm red, fix 4 mm yellow, downstream 3 mm orange), and output/profile_markers.json for the Civil 3D markers (32_markers.py).
Ground elevations come from the EG profiles of the drawing (W5/cs/30_read_profiles.cs, 1 m samples) through the MCP.
    python 31_design_points.py [--no-ground]   (--no-ground skips the drawing and leaves ground elevations empty)"""
import os, sys, json, csv, math, time
import geopandas as gpd, pandas as pd
from shapely.geometry import Point, LineString
HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE); CB = os.path.dirname(W6); W5 = os.path.join(CB, "W5")
sys.path.insert(0, os.path.join(W5, "scripts"))
OUT = os.path.join(W6, "output"); GIS = os.path.join(W6, "gis"); LOG = os.path.join(W6, "log", "31_design_points.log")
for d in (OUT, GIS, os.path.dirname(LOG)): os.makedirs(d, exist_ok=True)
TMP = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydraulic\SHP\tmp"            # the engineer's source point files (the Q values were written into the flow file by 33)
QP_SHP = os.path.join(TMP, "Qp Vol Block 04.shp"); FIX_SHP = os.path.join(TMP, "fix points.shp")
# THE W6 LAYERS ARE THE MASTER (engineer, 2026-10-10): he edits the flow and fix points on the QGIS layers of output/design_points.gpkg.
# When that file exists its flow_points / fix_points layers are read as the input (geometry and his attributes), the source shapefiles only
# when it does not. The file is never deleted before it has been read; a dated copy of what was read goes to inputs/as_read_<stamp>/.
import shutil, glob
GPKG = os.path.join(OUT, "design_points.gpkg"); FROM_GPKG = os.path.exists(GPKG)
_arch = os.path.join(W6, "inputs", "as_read_" + time.strftime("%Y%m%d_%H%M")); os.makedirs(_arch, exist_ok=True)
if FROM_GPKG: shutil.copy2(GPKG, os.path.join(_arch, "design_points.gpkg"))
else:
    for _p in glob.glob(QP_SHP[:-4] + ".*") + glob.glob(FIX_SHP[:-4] + ".*"): shutil.copy2(_p, _arch)
SPEC = json.load(open(os.path.join(W5, "civil3d", "build_spec_w5.json")))
PVIS_JSON = os.path.join(W6, "gdp", "gdp_reviewed_pvis.json") if os.path.exists(os.path.join(W6, "gdp", "gdp_reviewed_pvis.json")) else os.path.join(W5, "gdp", "gdp_reviewed_pvis.json")   # the live PVIs (W6/gdp since 2026-10-10)
GDP = {p["alignment"]: sorted(p["pvis"], key=lambda q: q["sta"]) for p in json.load(open(PVIS_JSON))["profiles"]}
CLASS_RANK = {"FP": 3, "SM": 2, "SS": 1}
SNAP_END_M, SNAP_POINT_M, DOWNSTREAM_M = 15.0, 60.0, 500.0


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + "  " + msg; print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")


def fmt(sta): return "%d+%03d" % (int(sta // 1000), int(round(sta % 1000)))


# ---------------------------------------------------------------- channels: oriented lines, classes, GDP interpolation
chan = {}
for f in SPEC:
    if f["kind"] != "channel": continue
    v = list(reversed(f["alignment"])) if f["reverse"] else f["alignment"]
    chan[f["name"]] = {"line": LineString([(p["x"], p["y"]) for p in v]), "cls": f["name"].rsplit("-", 1)[-1], "rank": CLASS_RANK[f["name"].rsplit("-", 1)[-1]], "length": f["length_m"]}


def gdp_at(name, sta):
    pv = GDP.get(name)
    if not pv: return None
    if sta <= pv[0]["sta"]: return pv[0]["elev"]
    if sta >= pv[-1]["sta"]: return pv[-1]["elev"]
    for a, b in zip(pv, pv[1:]):
        if a["sta"] <= sta <= b["sta"]: return a["elev"] + (b["elev"] - a["elev"]) * (sta - a["sta"]) / (b["sta"] - a["sta"]) if b["sta"] > a["sta"] else a["elev"]
    return None


def nearest_break(name, sta):
    pv = GDP.get(name)
    if not pv: return None
    k = min(range(len(pv)), key=lambda i: abs(pv[i]["sta"] - sta)); return {"gb": k, "sta": pv[k]["sta"], "elev": pv[k]["elev"], "dist": round(abs(pv[k]["sta"] - sta), 1)}


# ---------------------------------------------------------------- ground elevations from the drawing's EG profiles
EG = {}
def ground_at(name, sta):
    s = EG.get(name)
    if not s: return None
    sta = max(s["start"], min(sta, s["end"])); i = (sta - s["start"]) / s["step"]; k = int(i); t = i - k
    z = s["z"]; return round(z[k] + (z[min(k + 1, len(z) - 1)] - z[k]) * t, 2)


if "--no-ground" not in sys.argv:
    from c3d_mcp import McpSession, load_cs
    s = McpSession(command_timeout_ms=900000); ident = s.identity(); log("drawing: %s" % ident["filename"])
    for name in chan:
        r = s.query(load_cs(os.path.join(W5, "cs", "30_read_profiles.cs"), NAME=name, STEP=1.0)); r = r.get("result", r) if isinstance(r, dict) else r
        z = [float(v) for v in r["eg"]["samples"].split(",")]
        for i in [i for i, v in enumerate(z) if math.isnan(v)]: z[i] = next((z[j] for j in range(i - 1, -1, -1) if not math.isnan(z[j])), next(v for v in z if not math.isnan(v)))
        EG[name] = {"start": r["eg"]["start"], "end": r["eg"]["end"], "step": r["eg"]["step"], "z": z}
    s.close(); log("ground profiles read for %d channels" % len(EG))


def snap(pt, exclude=None, tol=SNAP_POINT_M):
    """Nearest channel (within tol) to a point; among channels within tol the highest class wins, then the nearest."""
    cands = []
    for n, c in chan.items():
        if n == exclude: continue
        d = c["line"].distance(pt)
        if d <= tol: cands.append((-c["rank"], d, n))
    if not cands: return None
    cands.sort(); n = cands[0][2]; return {"channel": n, "dist": round(cands[0][1], 2), "station": round(chan[n]["line"].project(pt), 2)}


markers = []   # for the Civil 3D profile views: alignment, station, elevation, kind, label
# ---------------------------------------------------------------- 1. junctions: channel ends on a receiving channel
junc = []
for name, c in chan.items():
    end = Point(c["line"].coords[-1]); hit = snap(end, exclude=name, tol=SNAP_END_M)
    if not hit: continue
    B = hit["channel"]; sta = hit["station"]; zB = gdp_at(B, sta); zA = GDP[name][-1]["elev"] if name in GDP else None; nb = nearest_break(B, sta)
    gB = ground_at(B, sta); gA = ground_at(name, c["length"])
    row = {"Label": "%s -> %s" % (name, B), "Tributary": name, "TribClass": c["cls"], "Receiver": B, "RecvClass": chan[B]["cls"], "RecvSta": sta, "RecvStaLbl": fmt(sta), "RecvLen": round(chan[B]["length"], 1),
           "TribEndZ": zA, "RecvGdpZ": None if zB is None else round(zB, 2), "DiffZ": None if (zA is None or zB is None) else round(zA - zB, 2), "RecvGround": gB, "TribGround": gA,
           "NearGB": nb["gb"] if nb else None, "NearGBSta": nb["sta"] if nb else None, "NearGBZ": nb["elev"] if nb else None, "NearGBDist": nb["dist"] if nb else None, "SnapDist": hit["dist"],
           "Flag": ("LOW: tributary bed %.2f m below the receiver's GDP" % (zB - zA)) if (zA is not None and zB is not None and zA < zB - 0.05) else ("merge with GB%d (%s, %.0f m away)" % (nb["gb"], fmt(nb["sta"]), nb["dist"]) if nb and nb["dist"] <= 60 else "new point on the receiver"),
           "X": end.x, "Y": end.y}
    junc.append(row)
    markers.append({"alignment": B, "station": sta, "elevation": zA if zA is not None else zB, "kind": "junction", "label": "%s ends  z=%s  (GDP here %s)" % (name, zA, row["RecvGdpZ"]), "x": end.x, "y": end.y})
    markers.append({"alignment": name, "station": c["length"], "elevation": zA if zA is not None else gA, "kind": "junction", "label": "-> %s %s  GDP there %s" % (B, fmt(sta), row["RecvGdpZ"]), "x": end.x, "y": end.y})
log("junctions: %d channel ends on a receiving channel; %d flagged LOW; %d can merge with a break within 60 m" % (len(junc), sum(1 for r in junc if r["Flag"].startswith("LOW")), sum(1 for r in junc if r["Flag"].startswith("merge"))))
unsnapped = [n for n, c in chan.items() if not snap(Point(c["line"].coords[-1]), exclude=n, tol=SNAP_END_M)]
log("channel ends not on another channel (outfalls or free ends): %s" % unsnapped)

# ---------------------------------------------------------------- 2. fix points and 500 m downstream
fix = gpd.read_file(GPKG, layer="fix_points") if FROM_GPKG else gpd.read_file(FIX_SHP); fixrows = []; dsrows = []
if FROM_GPKG: fix = fix.rename(columns={"Type": "type"}); log("fix points read from the W6 layer (the engineer's edits), %d features" % len(fix))
else: log("fix points read from %s" % FIX_SHP)
REMOVED = json.load(open(os.path.join(W6, "inputs", "fix_removed.json")))["removed"] if os.path.exists(os.path.join(W6, "inputs", "fix_removed.json")) else {}
if REMOVED:                                                                                         # engineer, 2026-10-12: fixes withdrawn
    _ids = ("FIX" + fix["Fix"].astype(str).str.strip().str.replace(".0", "", regex=False)) if "Fix" in fix.columns else fix["Label"].astype(str).str.extract(r"^(FIX" + r"\d+)")[0]
    _n = len(fix); fix = fix[~_ids.isin(REMOVED)].copy(); log("fix points withdrawn by inputs/fix_removed.json: %d of %d" % (_n - len(fix), _n))
for i, r in fix.iterrows():
    if "Fix" in fix.columns and pd.notna(r.get("Fix")): i = int(r["Fix"])          # the stable fix number of the W6 layer (survives reordering); new points get the row index
    hit = snap(r.geometry)
    if not hit: fixrows.append({"Label": "FIX%d %s" % (i, r["type"]), "Fix": i, "Type": r["type"], "Channel": None, "Station": None, "StaLbl": None, "Ground": None, "GdpZ": None, "SnapDist": None, "X": r.geometry.x, "Y": r.geometry.y, "Flag": "no channel within %d m" % SNAP_POINT_M}); continue
    n, sta = hit["channel"], hit["station"]; g = ground_at(n, sta); z = gdp_at(n, sta)
    fixrows.append({"Label": "FIX%d %s %s %s" % (i, r["type"], n, fmt(sta)), "Fix": i, "Type": r["type"], "Channel": n, "Station": sta, "StaLbl": fmt(sta), "Ground": g, "GdpZ": None if z is None else round(z, 2), "SnapDist": hit["dist"], "X": r.geometry.x, "Y": r.geometry.y, "Flag": ""})
    markers.append({"alignment": n, "station": sta, "elevation": g if g is not None else z, "kind": "fix", "label": "FIX%d %s  bed = ground %s  (GDP %s)" % (i, r["type"], g, None if z is None else round(z, 2)), "x": r.geometry.x, "y": r.geometry.y})
    if r["type"] != "Outfall":
        s2 = min(sta + DOWNSTREAM_M, chan[n]["length"]); p2 = chan[n]["line"].interpolate(s2); g2 = ground_at(n, s2); z2 = gdp_at(n, s2)
        dsrows.append({"Label": "FIX%d+500 %s %s" % (i, n, fmt(s2)), "Fix": i, "Channel": n, "Station": round(s2, 2), "StaLbl": fmt(s2), "Ground": g2, "GdpZ": None if z2 is None else round(z2, 2), "DistDown": round(s2 - sta, 1), "X": p2.x, "Y": p2.y, "Flag": "" if s2 - sta >= DOWNSTREAM_M - 0.01 else "channel ends %.0f m after the fix point" % (s2 - sta)})
        markers.append({"alignment": n, "station": s2, "elevation": g2 if g2 is not None else z2, "kind": "fix500", "label": "FIX%d +%.0f m  ground %s  GDP %s" % (i, s2 - sta, g2, None if z2 is None else round(z2, 2)), "x": p2.x, "y": p2.y})
# downstream points the engineer declared redundant (inputs/downstream_exclusions.json): dropped from the layer and the markers
excl = json.load(open(os.path.join(W6, "inputs", "downstream_exclusions.json")))["exclude"]; dropped = []
for e in excl:
    hit = [r for r in dsrows if r["Fix"] == e["fix"] and r["Channel"] == e["channel"]]
    if not hit: log("EXCLUSION NOT FOUND: FIX%d+500 on %s" % (e["fix"], e["channel"])); continue
    r = hit[0]
    if r["StaLbl"] != e["station"]: log("EXCLUSION STATION DIFFERS: FIX%d+500 %s is at %s, the engineer quoted %s (dropped anyway)" % (e["fix"], e["channel"], r["StaLbl"], e["station"]))
    dsrows.remove(r); markers[:] = [m for m in markers if not (m["kind"] == "fix500" and m["alignment"] == e["channel"] and abs(m["station"] - r["Station"]) < 0.01)]; dropped.append(r["Label"])
log("fix points: %d, snapped %d; downstream points %d after dropping %d redundant ones: %s" % (len(fixrows), sum(1 for r in fixrows if r["Channel"]), len(dsrows), len(dropped), dropped))

# ---------------------------------------------------------------- 3. flow points (the HMS points of the engineer's file)
qp = gpd.read_file(GPKG, layer="flow_points") if FROM_GPKG else gpd.read_file(QP_SHP); flowrows = []
if FROM_GPKG: qp = qp.drop(columns=[c for c in ("Channel", "Station", "StaLbl", "Ground", "GdpZ", "SnapDist", "Flag") if c in qp.columns]); log("flow points read from the W6 layer (the engineer's edits), %d features" % len(qp))
else: log("flow points read from %s" % QP_SHP)
for i, r in qp.iterrows():
    if r.geometry is None or r.geometry.is_empty: continue
    hit = snap(r.geometry)
    n, sta = (hit["channel"], hit["station"]) if hit else (None, None); g = ground_at(n, sta) if hit else None; z = gdp_at(n, sta) if hit else None
    row = {k: (None if pd.isna(v) else v) for k, v in r.items() if k != "geometry"}          # the engineer's attribute table, every field as in Qp Vol Block 04.shp
    row.update({"Channel": n, "Station": sta, "StaLbl": fmt(sta) if hit else None, "Ground": g, "GdpZ": None if z is None else round(z, 2), "SnapDist": hit["dist"] if hit else None, "X": r.geometry.x, "Y": r.geometry.y, "Flag": "" if hit else "no channel within %d m" % SNAP_POINT_M})
    flowrows.append(row)
    if hit: markers.append({"alignment": n, "station": sta, "elevation": z if z is not None else g, "kind": "flow", "label": "%s  Q200 %s m3/s" % (r["name"], ("%.0f" % r["Q200"]) if pd.notna(r.get("Q200")) else "?"), "x": r.geometry.x, "y": r.geometry.y})
log("flow points: %d, on a channel %d" % (len(flowrows), sum(1 for r in flowrows if r["Channel"])))

# ---------------------------------------------------------------- outputs
if os.path.exists(GPKG): os.remove(GPKG)          # everything was read above; rewritten now from the recomputed rows
for lyr, rows in (("flow_points", flowrows), ("junction_points", junc), ("fix_points", fixrows), ("fix_downstream", dsrows)):
    attrs = [{k: v for k, v in r.items() if not (lyr == "flow_points" and k in ("X", "Y"))} for r in rows]   # the flow layer keeps the file's own x/y fields (GeoPackage field names are case-insensitive)
    gdf = gpd.GeoDataFrame(attrs, geometry=[Point(r["X"], r["Y"]) for r in rows], crs="EPSG:32640")
    gdf.to_file(GPKG, layer=lyr, driver="GPKG"); gdf.drop(columns="geometry").to_csv(os.path.join(OUT, lyr + ".csv"), index=False)
json.dump(markers, open(os.path.join(OUT, "profile_markers.json"), "w"), indent=1)
log("written %s (4 layers), CSVs and profile_markers.json (%d markers)" % (GPKG, len(markers)))

# ---------------------------------------------------------------- QML styles: nested circles so that overlapping points stay visible
def qml(fill, outline, size, label_expr, color_text, placement_quad, hollow=False, font=7.5):
    return """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.44" styleCategories="Symbology|Labeling">
 <renderer-v2 type="singleSymbol"><symbols><symbol type="marker" name="0" alpha="1"><layer class="SimpleMarker"><Option type="Map"><Option name="name" type="QString" value="circle"/><Option name="color" type="QString" value="%s"/><Option name="outline_color" type="QString" value="%s"/><Option name="outline_width" type="QString" value="%s"/><Option name="size" type="QString" value="%s"/><Option name="size_unit" type="QString" value="MM"/></Option></layer></symbol></symbols></renderer-v2>
 <labeling type="simple"><settings calloutType="simple"><text-style fontSize="%s" fontFamily="Arial" fontWeight="75" textColor="%s" fieldName="%s" isExpression="1" namedStyle="Bold"><text-buffer bufferDraw="1" bufferSize="0.8" bufferColor="255,255,255,255"/></text-style><placement placement="6" dist="%s" quadOffset="%d"/><rendering scaleVisibility="1" scaleMin="1" scaleMax="100000"/></settings></labeling>
</qgis>
""" % ("0,0,0,0" if hollow else fill, outline, "0.9" if hollow else "0.4", size, font, color_text, label_expr.replace('"', "&quot;"), size / 2 + 1, placement_quad)
def write_qml(name, text):
    """A QML is written only when missing: the files in gis/ are the live styles (labels switched off by the engineer, 2026-10-10)."""
    p = os.path.join(GIS, name)
    if not os.path.exists(p): open(p, "w", encoding="utf-8").write(text)
write_qml("flow_points.qml", qml("0,90,220,255", "0,60,200,255", 7.0, '"name" || CASE WHEN "Q200" IS NOT NULL THEN \'  Q200 \' || round("Q200") || \' mÂ³/s\' ELSE \'\' END', "0,50,180,255", 0, hollow=True))
write_qml("junction_points.qml", qml("230,30,30,255", "140,0,0,255", 5.0, "'END ' || \"Tributary\" || ' on ' || \"Receiver\" || ' ' || \"RecvStaLbl\" || '  z ' || \"TribEndZ\" || ' / GDP ' || \"RecvGdpZ\"", "170,0,0,255", 8))
write_qml("fix_points.qml", qml("255,220,0,255", "140,110,0,255", 4.0, "'FIX' || \"Fix\" || ' ' || \"Type\" || '  ' || coalesce(\"StaLbl\", '') || '  gnd ' || coalesce(\"Ground\", '')", "120,90,0,255", 2))
write_qml("fix_downstream.qml", qml("255,140,0,255", "170,80,0,255", 3.0, "'+500 FIX' || \"Fix\" || '  ' || \"StaLbl\" || '  gnd ' || coalesce(\"Ground\", '')", "180,80,0,255", 6, font=6.5))
log("styles in %s (existing QML files kept)" % GIS)
for r in junc: print("  %-24s recv sta %s  trib z %s  recv GDP %s  diff %s  near GB%s %s m  %s" % (r["Label"], r["RecvStaLbl"], r["TribEndZ"], r["RecvGdpZ"], r["DiffZ"], r["NearGB"], r["NearGBDist"], r["Flag"]))
