"""Step 27 - after the engineer's review of the ground design profiles in Civil 3D: read every "GDP <name>" profile's
PVIs back from the drawing (cs/33_read_gdp.cs), redraw the plan markers on W5-GDP-BREAKS from them (cs/34_mark_breaks.cs),
rewrite gdp/Block4_channel_breaks.* and gdp/Block4_channel_segments.* and gdp/gdp_summary.csv from the reviewed points,
save the drawing. The rule-based run (25_gdp.py) is NOT re-applied: the engineer's PVIs are the source from here on.
    python 27_gdp_from_drawing.py [--no-save] [--no-mark]"""
import os, sys, json, csv, time, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import importlib; gdp = importlib.import_module("25_gdp")
from c3d_mcp import McpSession, load_cs
W5 = gdp.W5; SPEC = gdp.SPEC; LOG = os.path.join(W5, "log", "27_gdp_from_drawing.log")
GDP = os.path.join(os.path.dirname(W5), "W6", "gdp") if os.path.isdir(os.path.join(os.path.dirname(W5), "W6", "gdp")) else gdp.GDP   # the live GDP files moved to W6/gdp on 2026-10-10; W5/gdp is frozen


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + "  " + msg; print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")


if __name__ == "__main__":
    s = McpSession(command_timeout_ms=900000); ident = s.identity(); log("drawing: %s" % ident["filename"])
    if not ident["filename"].endswith(("Block04_Channels_W5.dwg", "Block04_Channels_W6.dwg")): sys.exit("the active drawing is not the W5 drawing: nothing done")
    r = s.query(load_cs(os.path.join(W5, "cs", "33_read_gdp.cs"))); r = r.get("result", r) if isinstance(r, dict) else r
    json.dump(r, open(os.path.join(GDP, "gdp_reviewed_pvis.json"), "w"), indent=1)
    profs = {p["alignment"]: p for p in r["profiles"]}; log("%d GDP profiles read (drawing %s)" % (len(profs), "saved" if r["saved"] else "with unsaved edits"))
    breaks = []; segments = []; summary = []; warn = []
    for f in [f for f in SPEC if f["kind"] == "channel"]:
        name = f["name"]
        if name not in profs: warn.append("%s: no GDP profile in the drawing" % name); continue
        p = profs[name]; pv = sorted(p["pvis"], key=lambda q: q["sta"])
        if len(pv) < 2: warn.append("%s: fewer than 2 PVIs" % name); continue
        verts = list(reversed(f["alignment"])) if f["reverse"] else f["alignment"]
        bsta = [q["sta"] for q in pv]; bz = [q["elev"] for q in pv]
        # the reviewed end PVIs sit up to ~1.5 m inside the alignment ends: the files cover the whole centreline, so those two stations are snapped to the ends (elevations kept)
        if 0 < abs(bsta[0] - p["alStart"]) <= 2.0: bsta[0] = p["alStart"]
        if 0 < abs(bsta[-1] - p["alEnd"]) <= 2.0: bsta[-1] = p["alEnd"]
        if abs(bsta[0] - p["alStart"]) > 0.5 or abs(bsta[-1] - p["alEnd"]) > 0.5: warn.append("%s: GDP spans %.1f-%.1f, alignment %.1f-%.1f" % (name, bsta[0], bsta[-1], p["alStart"], p["alEnd"]))
        if any(t["type"] not in ("?", "Tangent", "Tangent ") and "Parab" in t["type"] or "Arc" in t["type"] for t in pv): warn.append("%s: vertical curve PVIs present; treated as grade breaks" % name)
        for i, q in enumerate(pv):
            gin = (bz[i] - bz[i - 1]) / (bsta[i] - bsta[i - 1]) if i > 0 and bsta[i] > bsta[i - 1] else None
            gout = (bz[i + 1] - bz[i]) / (bsta[i + 1] - bsta[i]) if i < len(pv) - 1 and bsta[i + 1] > bsta[i] else None
            x, y = (q["x"], q["y"]) if q["x"] or q["y"] else gdp.polyline_interp(verts, q["sta"])
            breaks.append({"Label": "%s GB%d" % (name, i), "Channel": name, "GB": i, "Station": q["sta"], "Z_m": q["elev"], "X": x, "Y": y, "GradeIn": None if gin is None else round(gin, 5), "GradeOut": None if gout is None else round(gout, 5)})
        parts = gdp.split_polyline(verts, bsta)
        for k, part in enumerate(parts):
            L = bsta[k + 1] - bsta[k]
            segments.append({"Label": "%s-%d" % (name, k + 1), "Channel": name, "Seg": k + 1, "StaFrom": bsta[k], "StaTo": bsta[k + 1], "Length_m": round(L, 2), "ZFrom": bz[k], "ZTo": bz[k + 1], "Slope": round((bz[k] - bz[k + 1]) / L, 5) if L > 0 else None, "geometry": part})
        slopes = [(bz[k] - bz[k + 1]) / (bsta[k + 1] - bsta[k]) for k in range(len(bsta) - 1) if bsta[k + 1] > bsta[k]]
        adverse = sum(1 for v in slopes if v < -1e-9); flat = sum(1 for v in slopes if -1e-9 <= v < 0.0005)
        summary.append({"Channel": name, "Length_m": round(p["alEnd"] - p["alStart"], 1), "Breaks": len(pv), "Segments": len(pv) - 1, "MinSeg_m": round(min(bsta[k + 1] - bsta[k] for k in range(len(bsta) - 1)), 1), "MaxSeg_m": round(max(bsta[k + 1] - bsta[k] for k in range(len(bsta) - 1)), 1), "ZStart": bz[0], "ZEnd": bz[-1], "MeanSlope": round((bz[0] - bz[-1]) / (bsta[-1] - bsta[0]), 5), "ReverseSegments": adverse, "FlatSegments": flat, "Source": "engineer's reviewed GDP (drawing)"})
        if adverse: warn.append("%s: %d segment(s) with reverse slope" % (name, adverse))
    # markers in the drawing
    if "--no-mark" not in sys.argv:
        spec = ";".join("%s|%.3f|%.3f" % (b["Channel"], b["Station"], b["Z_m"]) for b in breaks)
        m = s.execute(load_cs(os.path.join(W5, "cs", "34_mark_breaks.cs"), BREAKS=spec, TEXT_H=gdp.STYLES["leader"]["textHeight"] * 0.5), description="W5 GDP markers from the reviewed profiles")
        log("markers: %s" % (m.get("result", m) if isinstance(m, dict) else m))
    if "--no-save" not in sys.argv: s.execute("return Database.Filename;", save=True); log("drawing saved")
    s.close()
    # files
    import geopandas as gpd
    from shapely.geometry import Point, LineString
    gb = gpd.GeoDataFrame([{k: v for k, v in b.items()} for b in breaks], geometry=[Point(b["X"], b["Y"]) for b in breaks], crs="EPSG:32640")
    gs = gpd.GeoDataFrame([{k: v for k, v in sg.items() if k != "geometry"} for sg in segments], geometry=[LineString(sg["geometry"]) for sg in segments], crs="EPSG:32640")
    for frame, base in ((gb, "Block4_channel_breaks"), (gs, "Block4_channel_segments")):
        try: frame.to_file(os.path.join(GDP, base + ".shp"))
        except Exception as ex: log("%s.shp not written (%s): writing %s_reviewed.shp instead" % (base, ex, base)); frame.to_file(os.path.join(GDP, base + "_reviewed.shp"))
        frame.drop(columns="geometry").to_csv(os.path.join(GDP, base + ".csv"), index=False)
    with open(os.path.join(GDP, "gdp_summary.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0].keys())); w.writeheader(); w.writerows(summary)
    par = json.load(open(os.path.join(GDP, "gdp_parameters.json"))); par.update({"source": "engineer's reviewed GDP profiles read from the drawing on " + time.strftime("%Y-%m-%d %H:%M"), "channels": len(summary), "breaks": len(breaks), "segments": len(segments)}); json.dump(par, open(os.path.join(GDP, "gdp_parameters.json"), "w"), indent=1)
    for wmsg in warn: log("WARNING " + wmsg)
    log("%d channels: %d breaks, %d segments from the reviewed profiles -> %s" % (len(summary), len(breaks), len(segments), GDP))
