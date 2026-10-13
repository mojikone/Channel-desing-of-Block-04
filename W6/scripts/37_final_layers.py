"""Step 37 - the final layers for SewerGEMS (engineer, 2026-10-10 afternoon): ONE point layer with every design point and ONE
segment layer between consecutive points, both in W6/final/.

Points (final/Block4_design_points.shp): the GDP grade breaks, the flow points, the fix points, the 500 m downstream points and
the channel ends on a receiving channel, merged where they share a location: a non-GDP point joins the nearest GDP break within
MERGE_M (10 m; the data has 142 gaps under 4 m, one of 8 m and none between 8 and 60 m), the remaining points are grouped within
MERGE_M among themselves and the group sits at the channel end, else the fix point, the flow point, the downstream point.
A tributary's own end point is not a point: it is the point that splits the receiving channel at the junction, and a flow or fix
point on the tributary's last MERGE_M metres belongs to that junction point (its Q/V go there). Stations within
2 m of a channel end are snapped to the end. Fields: Label (<channel>-N<nn>, numbered from upstream), Channel, Class, Station,
StaLbl, X, Y, Ground (the drawing's EG profile), GdpZ (the GDP of the channel the point is on), the five kind fields Flow / Fix /
Fix500 / GDP / CHend (filled with the matched identity, empty otherwise), FixType, name and the 26 Q*/V* fields of the flow layer,
Members (every merged member), Flag, SGLabel (the SewerGEMS point name, engineer 2026-10-10: <GCA><CH n>-<nn>, e.g. HAWCH7-1),
WadiDepth / WadiClass / BankZ / Raise from wadi/wadi_results.csv (39_wadi_depth.py; empty where not yet run; WadiDepth sets the
SewerGEMS library depth, Raise = lower bank top - GDP is the ground raise at the point, 0 where there is no wadi), GDP-Raised
(= GdpZ + Raise, the SewerGEMS node ground, the GDP-raised profile of the drawing) and Outfall ("Y" at the end of every channel
that joins no other channel: the model outfalls; engineer, 2026-10-11).
Segments (final/Block4_design_segments.shp): <channel>-C<nn> between consecutive points; geometry = the centreline between the two
stations with its end vertices set to the point coordinates exactly; a tributary's last segment runs to the receiver's junction
point. Fields: Label, Channel, Class, Seg, FromNode, ToNode, ToChannel, FromSta, ToSta, Length, USInv, DSInv (the channel's own
GDP at the two ends), Slope, Flag, SGLabel (<GCA><CH n>-C<nn>, e.g. HAWCH7-C1), SGFrom, SGTo (the SewerGEMS names of its two points).
final/final_markers.json carries every point for the drawing (38_sg_labels_markers.py puts the SewerGEMS names into the profile views).
Also written: final/merges.csv (every merged group), final/final_summary.json (counts, checks), a frozen copy final/frozen_<stamp>/
of everything (never overwritten), gis/design_points_final.qml and gis/design_segments_final.qml (written when missing, labels off).
Ground comes from the drawing's EG profiles through the MCP (W5/cs/30_read_profiles.cs, 1 m) and is cached in output/eg_samples.json
because the surfaces do not change; --no-ground uses the cache only.
    python 37_final_layers.py [--merge-tol 10] [--no-ground]"""
import os, sys, re, csv, json, math, time, shutil
import pandas as pd, geopandas as gpd
from shapely.geometry import LineString, Point
from shapely.ops import substring

HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE); CB = os.path.dirname(W6); W5 = os.path.join(CB, "W5")
sys.path.insert(0, os.path.join(W5, "scripts"))
OUT = os.path.join(W6, "output"); FINAL = os.path.join(W6, "final"); GIS = os.path.join(W6, "gis"); LOG = os.path.join(W6, "log", "37_final_layers.log")
GPKG = os.path.join(OUT, "design_points.gpkg"); EG_CACHE = os.path.join(OUT, "eg_samples.json"); PVIS_JSON = os.path.join(W6, "gdp", "gdp_reviewed_pvis.json")
SPEC = json.load(open(os.path.join(W5, "civil3d", "build_spec_w5.json"))); CRS = "EPSG:32640"
ARGS = sys.argv[1:]
MERGE_M = float(ARGS[ARGS.index("--merge-tol") + 1]) if "--merge-tol" in ARGS else 10.0   # points closer than this along a channel are one point
END_SNAP_M = 2.0                                                                          # a station this close to a channel end is the end
PRIORITY = {"CHend": 0, "fix": 1, "flow": 2, "fix500": 3}                                # who gives the location when no GDP break is in the group
STAMP = time.strftime("%Y%m%d_%H%M")
for d in (FINAL, os.path.dirname(LOG)): os.makedirs(d, exist_ok=True)


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + "  " + msg; print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")


def fmt(sta): k = int(round(sta)); return "%d+%03d" % (k // 1000, k % 1000)
def short(n): return re.sub(r"^([A-Z]+)-CH(\d+)-(FP|SM|SS)$", r"\1CH\2", n)   # SewerGEMS channel code (engineer, 2026-10-10): HAW-CH7-SS -> HAWCH7; unique over the 37 channels
def join(a, b): return b if not a else a + "; " + b


# ---------------------------------------------------------------- channels (oriented centrelines) and the live GDP
chan = {}
for f in SPEC:
    if f["kind"] != "channel": continue
    v = list(reversed(f["alignment"])) if f["reverse"] else f["alignment"]
    ln = LineString([(p["x"], p["y"]) for p in v]); chan[f["name"]] = {"line": ln, "length": ln.length, "cls": f["name"].rsplit("-", 1)[-1]}
pv_doc = json.load(open(PVIS_JSON)); GDP = {p["alignment"]: sorted(p["pvis"], key=lambda q: q["sta"]) for p in pv_doc["profiles"]}
log("37 final layers | %d channels, GDP for %d (%s, saved=%s) | merge tolerance %.1f m" % (len(chan), len(GDP), os.path.basename(PVIS_JSON), pv_doc.get("saved"), MERGE_M))


def gdp_at(name, sta):
    pv = GDP.get(name)
    if not pv: return None
    if sta <= pv[0]["sta"]: return pv[0]["elev"]
    if sta >= pv[-1]["sta"]: return pv[-1]["elev"]
    for a, b in zip(pv, pv[1:]):
        if a["sta"] <= sta <= b["sta"]: return a["elev"] + (b["elev"] - a["elev"]) * (sta - a["sta"]) / (b["sta"] - a["sta"]) if b["sta"] > a["sta"] else a["elev"]
    return None


# ---------------------------------------------------------------- ground: the drawing's EG profiles, cached
EG = json.load(open(EG_CACHE)) if os.path.exists(EG_CACHE) else {}
missing = [n for n in chan if n not in EG]
if missing and "--no-ground" not in ARGS:
    from c3d_mcp import McpSession, load_cs
    s = McpSession(command_timeout_ms=900000); ident = s.identity(); log("reading EG samples from %s for %d channels" % (ident["filename"], len(missing)))
    for name in missing:
        r = s.query(load_cs(os.path.join(W5, "cs", "30_read_profiles.cs"), NAME=name, STEP=1.0)); r = r.get("result", r) if isinstance(r, dict) else r
        z = [float(v) for v in r["eg"]["samples"].split(",")]
        for i in [i for i, v in enumerate(z) if math.isnan(v)]: z[i] = next((z[j] for j in range(i - 1, -1, -1) if not math.isnan(z[j])), next(v for v in z if not math.isnan(v)))
        EG[name] = {"start": r["eg"]["start"], "end": r["eg"]["end"], "step": r["eg"]["step"], "z": z}
    s.close(); json.dump({"_source": ident["filename"], "_read": time.strftime("%Y-%m-%d %H:%M"), **{k: v for k, v in EG.items() if not k.startswith("_")}}, open(EG_CACHE, "w")); log("EG samples cached in %s" % EG_CACHE)
elif missing: log("WARNING no EG samples for %d channels (cache only): ground left empty there" % len(missing))


def ground_at(name, sta):
    s = EG.get(name)
    if not s: return None
    sta = max(s["start"], min(sta, s["end"])); i = (sta - s["start"]) / s["step"]; k = int(i); t = i - k; z = s["z"]
    return round(z[k] + (z[min(k + 1, len(z) - 1)] - z[k]) * t, 2)


# ---------------------------------------------------------------- the design points of 31 (the engineer's edited layers)
flow = gpd.read_file(GPKG, layer="flow_points"); fix = gpd.read_file(GPKG, layer="fix_points"); ds = gpd.read_file(GPKG, layer="fix_downstream"); junc = gpd.read_file(GPKG, layer="junction_points")
REMOVED = json.load(open(os.path.join(W6, "inputs", "fix_removed.json")))["removed"] if os.path.exists(os.path.join(W6, "inputs", "fix_removed.json")) else {}
if REMOVED:                                                                                         # engineer, 2026-10-12: fixes withdrawn
    _ids = ("FIX" + fix["Fix"].astype(str).str.strip().str.replace(".0", "", regex=False)) if "Fix" in fix.columns else fix["Label"].astype(str).str.extract(r"^(FIX" + r"\d+)")[0]
    _n = len(fix); fix = fix[~_ids.isin(REMOVED)].copy(); log("fix points withdrawn by inputs/fix_removed.json: %d of %d" % (_n - len(fix), _n))
QV = [c for c in flow.columns if re.fullmatch(r"[QV](\d+|PMP)", c)]
recv_of = {r["Tributary"]: (r["Receiver"], float(r["RecvSta"])) for _, r in junc.iterrows()}
cands = {n: [] for n in chan}; skipped = []
for n, pv in GDP.items():
    if n not in chan: continue
    L = chan[n]["length"]
    for k, q in enumerate(pv):
        if k == len(pv) - 1 and n in recv_of: continue                   # a tributary's end is the junction point on its receiver
        sta = q["sta"]; sta = 0.0 if sta < END_SNAP_M else (L if L - sta < END_SNAP_M else sta)
        cands[n].append({"kind": "GDP", "sta": sta, "id": "GB%d" % k})
for _, r in flow.iterrows():
    if pd.isna(r["Channel"]) or pd.isna(r["Station"]): skipped.append("flow %s (no geometry / no channel)" % r["name"]); continue
    cands[r["Channel"]].append({"kind": "flow", "sta": float(r["Station"]), "id": str(r["name"]), "qv": {c: (None if pd.isna(r[c]) else float(r[c])) for c in QV}})
for _, r in fix.iterrows():
    if pd.isna(r["Channel"]) or pd.isna(r["Station"]): skipped.append("fix FIX%s (no channel)" % r["Fix"]); continue
    cands[r["Channel"]].append({"kind": "fix", "sta": float(r["Station"]), "id": "FIX%d" % int(r["Fix"]), "type": str(r["Type"])})
for _, r in ds.iterrows():
    if pd.isna(r["Channel"]) or pd.isna(r["Station"]): skipped.append("fix500 FIX%s+500 (no channel)" % r["Fix"]); continue
    cands[r["Channel"]].append({"kind": "fix500", "sta": float(r["Station"]), "id": "FIX%d+500" % int(r["Fix"])})
for _, r in junc.iterrows():
    cands[r["Receiver"]].append({"kind": "CHend", "sta": float(r["RecvSta"]), "id": str(r["Tributary"]), "tribEndZ": None if pd.isna(r["TribEndZ"]) else float(r["TribEndZ"])})
# a point on a tributary's last MERGE_M metres (its flow point, a fix point) belongs to the receiver's junction point, not to a point of its own
moved = []
for n, (recv, rsta) in recv_of.items():
    L = chan[n]["length"]; keep = []
    for c in cands[n]:
        if c["kind"] != "GDP" and c["sta"] >= L - MERGE_M: c2 = dict(c, sta=rsta, note="end of %s" % n); cands[recv].append(c2); moved.append("%s:%s %s -> %s" % (c["kind"], c["id"], n, recv))
        else: keep.append(c)
    cands[n] = keep
for s_ in skipped: log("skipped: " + s_)
log("points at a tributary's end moved to the receiver's junction point: %d (%s)" % (len(moved), "; ".join(moved)))
log("candidates: %d GDP breaks, %d flow, %d fix, %d fix500, %d channel ends" % tuple(sum(1 for cl in cands.values() for c in cl if c["kind"] == k) for k in ("GDP", "flow", "fix", "fix500", "CHend")))

# ---------------------------------------------------------------- merge into points
nodes = {}; merges = []; close_pairs = []
for n, cl in cands.items():
    groups = [[g] for g in sorted((c for c in cl if c["kind"] == "GDP"), key=lambda c: c["sta"])]
    loose = []
    for c in sorted((c for c in cl if c["kind"] != "GDP"), key=lambda c: (c["sta"], PRIORITY[c["kind"]])):
        best = min(groups, key=lambda g: abs(g[0]["sta"] - c["sta"])) if groups else None
        if best is not None and abs(best[0]["sta"] - c["sta"]) <= MERGE_M: best.append(c)
        else: loose.append(c)
    cur = []
    for c in loose:
        if cur and c["sta"] - cur[0]["sta"] <= MERGE_M: cur.append(c)
        else:
            if cur: groups.append(cur)
            cur = [c]
    if cur: groups.append(cur)
    lst = []; L = chan[n]["length"]; line = chan[n]["line"]
    for g in groups:
        anchor = g[0] if g[0]["kind"] == "GDP" else sorted(g, key=lambda c: (PRIORITY[c["kind"]], c["sta"]))[0]
        sta = anchor["sta"]; sta = 0.0 if sta < END_SNAP_M else (L if L - sta < END_SNAP_M else sta)
        p = line.interpolate(sta); z = gdp_at(n, sta)
        node = {"Channel": n, "Class": chan[n]["cls"], "sta": sta, "Station": round(sta, 3), "StaLbl": fmt(sta), "X": p.x, "Y": p.y, "Ground": ground_at(n, sta), "GdpZ": None if z is None else round(z, 3),
                "Flow": None, "Fix": None, "FixType": None, "Fix500": None, "GDP": None, "CHend": None, "name": None, **{c: None for c in QV},
                "Members": "; ".join("%s:%s%s" % (c["kind"], c["id"], " [%s]" % c["note"] if c.get("note") else "") for c in g), "Flag": ""}
        for c in g:
            if c["kind"] == "GDP": node["GDP"] = join(node["GDP"], c["id"])
            elif c["kind"] == "flow":
                node["Flow"] = join(node["Flow"], c["id"])
                if node["name"] is None: node["name"] = c["id"]; node.update(c["qv"])
                else: node["Flag"] = join(node["Flag"], "two flow points on one point: Q/V of %s kept" % node["name"])
            elif c["kind"] == "fix": node["Fix"] = join(node["Fix"], c["id"]); node["FixType"] = join(node["FixType"], c["type"])
            elif c["kind"] == "fix500": node["Fix500"] = join(node["Fix500"], c["id"])
            elif c["kind"] == "CHend": node["CHend"] = join(node["CHend"], c["id"])
        spread = max(c["sta"] for c in g) - min(c["sta"] for c in g)
        if len(g) > 1: merges.append({"Channel": n, "Station": node["Station"], "StaLbl": node["StaLbl"], "Members": node["Members"], "Spread_m": round(spread, 2), "LocationFrom": anchor["kind"] + ":" + anchor["id"]})
        if spread > 1.0: node["Flag"] = join(node["Flag"], "merged over %.1f m, placed at %s" % (spread, anchor["kind"]))
        lst.append(node)
    lst.sort(key=lambda d: d["sta"])
    for i, d in enumerate(lst): d["Label"] = "%s-N%02d" % (n, i + 1); d["SGLabel"] = "%s-%d" % (short(n), i + 1)
    for a_, b_ in zip(lst, lst[1:]):
        if b_["sta"] - a_["sta"] < MERGE_M: close_pairs.append((a_["Label"], b_["Label"], round(b_["sta"] - a_["sta"], 1)))
    nodes[n] = lst
for m in merges:
    m["Label"] = next(d["Label"] for d in nodes[m["Channel"]] if d["Station"] == m["Station"])
log("points: %d on %d channels; %d merged groups (%d of them spread over more than 1 m); %d consecutive points closer than %.0f m: %s" % (sum(len(l) for l in nodes.values()), len(nodes), len(merges), sum(1 for m in merges if m["Spread_m"] > 1), len(close_pairs), MERGE_M, close_pairs))

# ---------------------------------------------------------------- segments between consecutive points
segs = []; jogs = []
def seg(n, k, a_, b_, geom, to_sta, to_channel, flag=""):
    us, dsz = gdp_at(n, a_["sta"]), gdp_at(n, to_sta); Lg = geom.length; slope = None if (us is None or dsz is None or Lg <= 0) else (us - dsz) / Lg
    if slope is not None and slope < 0: flag = join(flag, "REVERSE slope")
    elif slope is not None and slope < 0.0005: flag = join(flag, "flat (< 0.05 %)")
    return {"Label": "%s-C%02d" % (n, k), "Channel": n, "Class": chan[n]["cls"], "Seg": k, "FromNode": a_["Label"], "ToNode": b_["Label"], "ToChannel": to_channel, "FromSta": round(a_["sta"], 3), "ToSta": round(to_sta, 3),
            "Length": round(Lg, 2), "USInv": None if us is None else round(us, 3), "DSInv": None if dsz is None else round(dsz, 3), "Slope": None if slope is None else round(slope, 5), "Flag": flag,
            "SGLabel": "%s-C%d" % (short(n), k), "SGFrom": a_["SGLabel"], "SGTo": b_["SGLabel"], "geometry": geom}
for n, lst in nodes.items():
    line = chan[n]["line"]; L = chan[n]["length"]
    for i in range(len(lst) - 1):
        a_, b_ = lst[i], lst[i + 1]
        if b_["sta"] <= a_["sta"]: log("WARNING %s: zero-length segment %s -> %s skipped" % (n, a_["Label"], b_["Label"])); continue
        g = substring(line, a_["sta"], b_["sta"]); coords = list(g.coords); coords[0] = (a_["X"], a_["Y"]); coords[-1] = (b_["X"], b_["Y"])
        segs.append(seg(n, i + 1, a_, b_, LineString(coords), b_["sta"], n))
    if n in recv_of:                                                      # the last segment of a tributary ends on the receiver's junction point
        recv, _ = recv_of[n]; jn = next((d for d in nodes[recv] if d["CHend"] and n in d["CHend"].split("; ")), None)
        if jn is None: log("PROBLEM %s: junction point on %s not found" % (n, recv)); continue
        last = lst[-1]
        if L > last["sta"] + 0.01: g = substring(line, last["sta"], L); coords = list(g.coords)
        else: coords = [(last["X"], last["Y"]), (last["X"], last["Y"])]
        coords[0] = (last["X"], last["Y"]); jog = Point(coords[-1]).distance(Point(jn["X"], jn["Y"]))
        if jog <= 0.5 or len(coords) < 2: coords[-1] = (jn["X"], jn["Y"])
        else: coords.append((jn["X"], jn["Y"]))
        jogs.append((n, round(jog, 1)))
        flag = "" if jog <= 1 else "end moved %.1f m onto the receiver's point" % jog
        s_ = seg(n, len(lst), last, jn, LineString(coords), L, recv, flag)
        if jn["GdpZ"] is not None and s_["DSInv"] is not None and abs(jn["GdpZ"] - s_["DSInv"]) > 0.005: s_["Flag"] = join(s_["Flag"], "tributary end %.3f vs receiver point GDP %.3f" % (s_["DSInv"], jn["GdpZ"]))
        segs.append(s_)
log("segments: %d; tributary ends moved onto the receiver's point: max %.1f m (%s)" % (len(segs), max(j for _, j in jogs) if jogs else 0, [j for j in jogs if j[1] > 1]))

# ---------------------------------------------------------------- checks
byname = {d["Label"]: d for l in nodes.values() for d in l}; bad = 0
for s_ in segs:
    c0, c1 = s_["geometry"].coords[0], s_["geometry"].coords[-1]; A, B = byname[s_["FromNode"]], byname[s_["ToNode"]]
    if c0 != (A["X"], A["Y"]) or c1 != (B["X"], B["Y"]): bad += 1
cont = [abs(s2["USInv"] - s1["DSInv"]) for n in nodes for s1, s2 in zip([s for s in segs if s["Channel"] == n], [s for s in segs if s["Channel"] == n][1:]) if s1["DSInv"] is not None and s2["USInv"] is not None]
log("checks: segment ends equal to their points: %s (%d mismatches); invert continuity along channels max %.4f m; flags on segments: %d; flags on points: %d" % ("OK" if bad == 0 else "FAILED", bad, max(cont) if cont else 0, sum(1 for s in segs if s["Flag"]), sum(1 for l in nodes.values() for d in l if d["Flag"])))
for s_ in segs:
    if s_["Flag"]: log("  segment %-16s %s" % (s_["Label"], s_["Flag"]))

# ---------------------------------------------------------------- write
PCOLS = ["Label", "Channel", "Class", "Station", "StaLbl", "X", "Y", "Ground", "GdpZ", "Flow", "Fix", "FixType", "Fix500", "GDP", "CHend", "name"] + QV + ["Members", "Flag", "SGLabel"]
SCOLS = ["Label", "Channel", "Class", "Seg", "FromNode", "ToNode", "ToChannel", "FromSta", "ToSta", "Length", "USInv", "DSInv", "Slope", "Flag", "SGLabel", "SGFrom", "SGTo"]
prows = [d for l in nodes.values() for d in l]
WADI = os.path.join(W6, "wadi", "wadi_results.csv")        # 39_wadi_depth.py: WadiDepth (0 where no wadi), WadiClass, BankZ (lower bank top), Raise = bank - GDP
wd = pd.read_csv(WADI).drop_duplicates("SGLabel", keep="last").set_index("SGLabel") if os.path.exists(WADI) else None
for d in prows:
    r = wd.loc[d["SGLabel"]] if wd is not None and d["SGLabel"] in wd.index else None
    d["WadiDepth"] = None if r is None or pd.isna(r["WadiDepth"]) else float(r["WadiDepth"]); d["WadiClass"] = None if r is None or pd.isna(r["WadiClass"]) else str(r["WadiClass"])
    d["BankZ"] = None if r is None or pd.isna(r["BankZ"]) else float(r["BankZ"]); d["Raise"] = None if r is None or pd.isna(r["Raise"]) else float(r["Raise"])
PCOLS += ["WadiDepth", "WadiClass", "BankZ", "Raise"]
log("wadi fields joined for %d of %d points%s" % (sum(1 for d in prows if d["WadiClass"]), len(prows), "" if wd is not None else " (no wadi_results.csv yet)"))
for n, lst in nodes.items():                                           # engineer, 2026-10-11: outfall flag = the end of a channel that joins no other channel
    for d in lst: d["Outfall"] = ""
    if n not in recv_of: lst[-1]["Outfall"] = "Y"
for d in prows: d["GDP-Raised"] = None if d["GdpZ"] is None else round(d["GdpZ"] + (d["Raise"] or 0.0), 3)   # the SewerGEMS node ground = the GDP-raised profile
PCOLS += ["GDP-Raised", "Outfall"]
log("GDP-Raised (GdpZ + Raise) written; outfall flag on %d channel ends" % sum(1 for d in prows if d["Outfall"] == "Y"))
pts = gpd.GeoDataFrame([{c: d[c] for c in PCOLS} for d in prows], geometry=[Point(d["X"], d["Y"]) for d in prows], crs=CRS)
sg = gpd.GeoDataFrame([{c: s_[c] for c in SCOLS} for s_ in segs], geometry=[s_["geometry"] for s_ in segs], crs=CRS)
for frame, base in ((pts, "Block4_design_points"), (sg, "Block4_design_segments")):
    try: frame.to_file(os.path.join(FINAL, base + ".shp"))
    except Exception as ex: sys.exit("%s.shp not written (%s): remove the final layers from QGIS and run again" % (base, ex))
    frame.drop(columns="geometry").to_csv(os.path.join(FINAL, base + ".csv"), index=False)
with open(os.path.join(FINAL, "merges.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["Label", "Channel", "Station", "StaLbl", "Members", "Spread_m", "LocationFrom"]); w.writeheader(); w.writerows(sorted(merges, key=lambda m: -m["Spread_m"]))
summary = {"written": time.strftime("%Y-%m-%d %H:%M"), "merge_tolerance_m": MERGE_M, "end_snap_m": END_SNAP_M, "location_priority_without_gdp": list(PRIORITY), "gdp_source": {"file": PVIS_JSON, "saved_flag": pv_doc.get("saved"), "mtime": time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(PVIS_JSON)))},
           "points_source": {"file": GPKG, "mtime": time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(GPKG)))}, "channels": len(nodes), "points": len(prows), "segments": len(segs),
           "points_by_kind": {k: sum(1 for d in prows if d[k]) for k in ("Flow", "Fix", "Fix500", "GDP", "CHend")}, "points_gdp_only": sum(1 for d in prows if d["GDP"] and not (d["Flow"] or d["Fix"] or d["Fix500"] or d["CHend"])),
           "merged_groups": len(merges), "merged_over_1m": [m for m in merges if m["Spread_m"] > 1], "consecutive_points_closer_than_tolerance": close_pairs, "tributary_end_jogs_over_1m": [j for j in jogs if j[1] > 1],
           "points_moved_from_tributary_ends": moved, "segment_end_mismatches": bad, "invert_continuity_max_m": round(max(cont), 4) if cont else 0, "segments_flagged": [(s_["Label"], s_["Flag"]) for s_ in segs if s_["Flag"]], "skipped_inputs": skipped}
json.dump(summary, open(os.path.join(FINAL, "final_summary.json"), "w"), indent=1)
json.dump([{"alignment": d["Channel"], "station": d["sta"], "elevation": d["GdpZ"], "kind": "sglabel", "label": "%s  D %s  R %s" % (d["SGLabel"], "-" if d["WadiDepth"] is None else "%.2f" % d["WadiDepth"], "-" if d["Raise"] is None else "%.2f" % d["Raise"]), "x": d["X"], "y": d["Y"]} for d in prows], open(os.path.join(FINAL, "final_markers.json"), "w"), indent=1)   # for 38_sg_labels_markers.py
frozen = os.path.join(FINAL, "frozen_" + STAMP); os.makedirs(frozen, exist_ok=True)
for fn in os.listdir(FINAL):
    if os.path.isfile(os.path.join(FINAL, fn)): shutil.copy2(os.path.join(FINAL, fn), os.path.join(frozen, fn))
log("written %s: Block4_design_points (%d) and Block4_design_segments (%d), merges.csv, final_summary.json; frozen copy %s" % (FINAL, len(prows), len(segs), frozen))

# ---------------------------------------------------------------- QGIS styles (written only when missing: the engineer's later edits in QGIS stay)
def marker(idx, fill, outline, size, ow):
    return ('<symbol type="marker" name="%d" alpha="1" clip_to_extent="1" force_rhr="0"><layer class="SimpleMarker" enabled="1" pass="0" locked="0"><Option type="Map"><Option name="name" type="QString" value="circle"/>'
            '<Option name="color" type="QString" value="%s"/><Option name="outline_color" type="QString" value="%s"/><Option name="outline_style" type="QString" value="solid"/><Option name="outline_width" type="QString" value="%s"/>'
            '<Option name="outline_width_unit" type="QString" value="MM"/><Option name="size" type="QString" value="%s"/><Option name="size_unit" type="QString" value="MM"/></Option></layer></symbol>') % (idx, fill, outline, ow, size)
RULES = [("Flow", "Flow point (HMS)", "0,0,0,0", "0,60,200,255", 7.0, "0.9"), ("CHend", "Channel end joining here", "230,30,30,255", "140,0,0,255", 5.0, "0.4"), ("Fix", "Fix point", "255,220,0,255", "140,110,0,255", 4.0, "0.4"),
         ("Fix500", "500 m downstream of a fix point", "255,140,0,255", "170,80,0,255", 3.0, "0.4"), ("GDP", "GDP grade break", "60,60,60,255", "0,0,0,255", 2.0, "0.3")]
LABEL = ('<labeling type="simple"><settings calloutType="simple"><text-style fontSize="%s" fontFamily="Arial" fontWeight="75" textColor="%s" fieldName="%s" isExpression="1" namedStyle="Bold"><text-buffer bufferDraw="1" bufferSize="0.8" bufferColor="255,255,255,255"/></text-style>'
         '<placement placement="%d" dist="%s" quadOffset="%d"/><rendering scaleVisibility="1" scaleMin="1" scaleMax="100000"/></settings></labeling>')
pts_qml = ('<!DOCTYPE qgis PUBLIC \'http://mrcc.com/qgis.dtd\' \'SYSTEM\'>\n<qgis version="3.44" styleCategories="Symbology|Labeling" labelsEnabled="1">\n <renderer-v2 type="RuleRenderer" symbollevels="0" forceraster="0" enableorderby="0"><rules key="{w6-final-points}">'
           + "".join('<rule key="{rule-%s}" symbol="%d" label="%s" filter="coalesce(&quot;%s&quot;, \'\') &lt;&gt; \'\'"/>' % (f, i, lab, f) for i, (f, lab, *_) in enumerate(RULES)) + "</rules><symbols>"
           + "".join(marker(i, fill, outline, size, ow) for i, (f, lab, fill, outline, size, ow) in enumerate(RULES)) + "</symbols></renderer-v2>\n "
           + LABEL % ("7.5", "30,30,30,255", "&quot;SGLabel&quot; || '\\n' || 'D: ' || coalesce(format_number(&quot;WadiDepth&quot;, 2), '-') || '\\n' || 'R: ' || coalesce(format_number(&quot;Raise&quot;, 2), '-')", 6, "4.5", 2) + "\n</qgis>\n")   # engineer 2026-10-11: stacked label name / D: wadi depth / R: raise, labels ON for this layer
def lsym(idx, color, width):
    return ('<symbol type="line" name="%d" alpha="1" clip_to_extent="1" force_rhr="0"><layer class="SimpleLine" enabled="1" pass="0" locked="0"><Option type="Map"><Option name="line_color" type="QString" value="%s"/><Option name="line_style" type="QString" value="solid"/>'
            '<Option name="line_width" type="QString" value="%s"/><Option name="line_width_unit" type="QString" value="MM"/><Option name="capstyle" type="QString" value="round"/><Option name="joinstyle" type="QString" value="round"/></Option></layer></symbol>') % (idx, color, width)
CLASSES = [("FP", "FP flood protection channel", "0,70,160,255", "1.1"), ("SM", "SM main swale", "0,130,90,255", "0.8"), ("SS", "SS secondary swale", "110,110,110,255", "0.5")]
seg_qml = ('<!DOCTYPE qgis PUBLIC \'http://mrcc.com/qgis.dtd\' \'SYSTEM\'>\n<qgis version="3.44" styleCategories="Symbology|Labeling" labelsEnabled="0">\n <renderer-v2 type="categorizedSymbol" attr="Class" symbollevels="0" forceraster="0" enableorderby="0"><categories>'
           + "".join('<category value="%s" symbol="%d" label="%s" render="true" type="string"/>' % (c, i, lab) for i, (c, lab, *_) in enumerate(CLASSES)) + "</categories><symbols>" + "".join(lsym(i, col, w) for i, (c, lab, col, w) in enumerate(CLASSES)) + "</symbols></renderer-v2>\n "
           + LABEL % ("7", "0,80,60,255", "&quot;SGLabel&quot; || '  ' || &quot;SGFrom&quot; || ' > ' || &quot;SGTo&quot; || '  ' || round(&quot;Slope&quot; * 100, 2) || ' %'", 2, "1.5", 0) + "\n</qgis>\n")
for name, text in (("design_points_final.qml", pts_qml), ("design_segments_final.qml", seg_qml)):
    p = os.path.join(GIS, name)
    if not os.path.exists(p): open(p, "w", encoding="utf-8").write(text); log("style written: " + p)
log("done")
