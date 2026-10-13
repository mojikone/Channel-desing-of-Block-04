"""Step 25 - ground design profiles (GDP) for the channels: the existing-ground profile of each alignment, read from
the drawing every 1 m, is simplified by the Ramer-Douglas-Peucker rule with a VERTICAL tolerance (the engineer's
method: connect the ends, add the point of largest departure from the ground, repeat until the departure is small):
the result is a polyline through ground points whose grade breaks mark the trend changes. For each channel a layout
profile "GDP <name>" is created in the drawing (cs/31_create_gdp.cs), the breaks are marked on the alignment, and the
SewerGEMS inputs are written: gdp/Block4_channel_breaks.shp (points) and gdp/Block4_channel_segments.shp (the
centreline split at the breaks, with the ground elevation and slope of every segment), plus CSV summaries.
    python 25_gdp.py --calibrate [SAK-CH3-SM]      # compare the engineer's sample GDP with the ground, test tolerances
    python 25_gdp.py [--tol 0.75] [--window 201] [--min-seg 0] [--min-slope 0] [names...] [--no-mark] [--no-save]
No reverse slope: a segment that climbs in the flow direction is merged with a neighbour (engineer, 2026-10-07).
Calibration (2026-10-07, SAK-CH3-SM): the engineer's 5-PVI sample departs 0.87 m from the 201 m trend, so tolerance
0.75 m on that trend reproduces his density (6 breaks on 6.5 km, one at 3 321 m next to his 3 357 m).
"""
import os, sys, json, csv, math, time
HERE = os.path.dirname(os.path.abspath(__file__)); W5 = os.path.dirname(HERE); W4 = os.path.join(os.path.dirname(W5), "W4")
sys.path.insert(0, HERE)
from c3d_mcp import McpSession, load_cs
GDP = os.path.join(W5, "gdp"); os.makedirs(GDP, exist_ok=True); LOG = os.path.join(W5, "log", "25_gdp.log")
SPEC_PATH = os.path.join(W5, "civil3d", "build_spec_w5.json"); SPEC = json.load(open(SPEC_PATH))
STYLES = json.load(open(os.path.join(W5, "civil3d", "styles.json")))
GDP_STYLE = STYLES.get("gdp", {}).get("profile", "ARJV_Design Profile"); GDP_LABELS = STYLES.get("gdp", {}).get("profileLabelSet", "_No Labels")


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + "  " + msg; print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")


# ---------------------------------------------------------------- the simplification
def rdp(sta, z, tol):
    """Indices of the kept points: recursive largest vertical departure from the chord, until every departure <= tol."""
    keep = {0, len(sta) - 1}; stack = [(0, len(sta) - 1)]
    while stack:
        a, b = stack.pop()
        if b - a < 2: continue
        za, zb = z[a], z[b]; sa, sb = sta[a], sta[b]; best, bi = 0.0, -1
        for i in range(a + 1, b):
            d = abs(z[i] - (za + (zb - za) * (sta[i] - sa) / (sb - sa)))
            if d > best: best, bi = d, i
        if best > tol: keep.add(bi); stack.append((a, bi)); stack.append((bi, b))
    return sorted(keep)


def enforce_min_seg(idx, sta, z, tol, min_seg):
    """Drop interior breaks closer than min_seg to their predecessor, unless that would push the departure past 2*tol."""
    if not min_seg: return idx
    out = [idx[0]]
    for k in range(1, len(idx) - 1):
        i = idx[k]
        if sta[i] - sta[out[-1]] >= min_seg: out.append(i); continue
        a, b = out[-1], idx[k + 1]; za, zb, sa, sb = z[a], z[b], sta[a], sta[b]
        worst = max(abs(z[j] - (za + (zb - za) * (sta[j] - sa) / (sb - sa))) for j in range(a + 1, b))
        if worst > 2 * tol: out.append(i)
    out.append(idx[-1]); return out


def enforce_monotone(idx, sta, zpvi, zs, min_slope=0.0):
    """A channel invert cannot rise downstream (engineer, 2026-10-07): remove interior breaks that make a segment climb in
    the flow direction (or fall less than `min_slope`, m/m). The adverse segment is merged with a neighbour by dropping the
    one of its two breaks whose removal keeps the trend closest to the merged chord; repeated until every segment complies.
    `zpvi` maps a sample index to the elevation the PVI will get. Returns (indices, breaks dropped, ends-adverse flag)."""
    idx = list(idx); dropped = 0
    while True:
        bad = [k for k in range(len(idx) - 1) if zpvi[idx[k + 1]] > zpvi[idx[k]] - min_slope * (sta[idx[k + 1]] - sta[idx[k]]) + 1e-6]
        if not bad: return idx, dropped, False
        k = bad[0]; cands = []
        for drop in (k, k + 1):
            if drop == 0 or drop == len(idx) - 1: continue
            a, b = idx[drop - 1], idx[drop + 1]
            dev = max(abs(zs[j] - (zpvi[a] + (zpvi[b] - zpvi[a]) * (sta[j] - sta[a]) / (sta[b] - sta[a]))) for j in range(a + 1, b))
            cands.append((dev, drop))
        if not cands: return idx, dropped, True          # only the two ends are left and the end is higher than the start
        idx.pop(min(cands)[1]); dropped += 1


def departures(sta, z, bsta, bz):
    """Vertical departure of the ground from the polyline through the breaks, at every sample."""
    out = []; k = 0
    for s, zz in zip(sta, z):
        while k < len(bsta) - 2 and s > bsta[k + 1]: k += 1
        sa, sb, za, zb = bsta[k], bsta[k + 1], bz[k], bz[k + 1]
        out.append(zz - (za + (zb - za) * (s - sa) / (sb - sa)) if sb > sa else 0.0)
    return out


def read_eg(s, name, step=1.0):
    r = s.query(load_cs(os.path.join(W5, "cs", "30_read_profiles.cs"), NAME=name, STEP=step)); r = r.get("result", r) if isinstance(r, dict) else r
    z = [float(v) for v in r["eg"]["samples"].split(",")]; sta = [r["eg"]["start"] + i * step for i in range(len(z))]; sta[-1] = min(sta[-1], r["eg"]["end"])
    for i in [i for i, v in enumerate(z) if math.isnan(v)]:                       # a few cells without ground (gaps between corridor cells): carry the last value
        z[i] = next((z[j] for j in range(i - 1, -1, -1) if not math.isnan(z[j])), next(v for v in z if not math.isnan(v)))
    return r, sta, z


def smooth(z, window, mean_window=51):
    """The trend of the ground: a rolling median over `window` samples (kills crossings, bunds and single-cell spikes)
    followed by a short rolling mean (removes the median's steps)."""
    import statistics
    def rolling(v, w, fn):
        h = w // 2; return [fn(v[max(0, i - h): i + h + 1]) for i in range(len(v))]
    return rolling(rolling(z, window, statistics.median), mean_window, statistics.fmean)


def stitch(i, sta, z, zs, reach=30):
    """Ground elevation for a break found on the smoothed trend at sample i: the raw ground there, unless it sits on a
    spike (more than 0.3 m off the trend), in which case the nearest sample within `reach` m whose ground is closest to
    the trend is taken instead."""
    if abs(z[i] - zs[i]) <= 0.3: return i
    lo, hi = max(0, i - reach), min(len(z) - 1, i + reach)
    return min(range(lo, hi + 1), key=lambda j: (abs(z[j] - zs[j]), abs(j - i)))


# ---------------------------------------------------------------- geometry along the centreline
def polyline_interp(verts, station):
    """Point on the 2D polyline at a cumulative length (clamped)."""
    acc = 0.0
    for i in range(1, len(verts)):
        seg = math.hypot(verts[i]["x"] - verts[i - 1]["x"], verts[i]["y"] - verts[i - 1]["y"])
        if acc + seg >= station - 1e-9 and seg > 0:
            t = max(0.0, min(1.0, (station - acc) / seg)); return (verts[i - 1]["x"] + t * (verts[i]["x"] - verts[i - 1]["x"]), verts[i - 1]["y"] + t * (verts[i]["y"] - verts[i - 1]["y"]))
        acc += seg
    return (verts[-1]["x"], verts[-1]["y"])


def split_polyline(verts, stations):
    """The polyline cut at the given cumulative lengths: a list of vertex lists."""
    parts = []; cur = [(verts[0]["x"], verts[0]["y"])]; acc = 0.0; cuts = list(stations[1:-1]); ci = 0
    for i in range(1, len(verts)):
        p, q = verts[i - 1], verts[i]; seg = math.hypot(q["x"] - p["x"], q["y"] - p["y"])
        while ci < len(cuts) and acc + seg >= cuts[ci] - 1e-9:
            t = (cuts[ci] - acc) / seg if seg > 0 else 0.0; x = p["x"] + t * (q["x"] - p["x"]); y = p["y"] + t * (q["y"] - p["y"])
            cur.append((x, y)); parts.append(cur); cur = [(x, y)]; ci += 1
        cur.append((q["x"], q["y"])); acc += seg
    parts.append(cur); return parts


# ---------------------------------------------------------------- modes
def calibrate(s, name):
    r, sta, z = read_eg(s, name); gdp = next((p for p in r["profiles"] if p["name"].endswith(" GDP")), None)
    if not gdp: sys.exit("no sample profile '<name> GDP' on " + name)
    bsta = [q["sta"] for q in gdp["pvis"]]; bz = [q["elev"] for q in gdp["pvis"]]
    dep = departures(sta, z, bsta, bz); amax = max(abs(d) for d in dep); rms = math.sqrt(sum(d * d for d in dep) / len(dep))
    print("sample %s GDP: %d PVIs at %s" % (name, len(bsta), ["%.0f/%.2f" % (a, b) for a, b in zip(bsta, bz)]))
    print("  ground departs from it by at most %.2f m (RMS %.2f m); PVI elevations vs ground at the PVI stations: %s" % (amax, rms, ["%.2f" % (bz[i] - z[min(range(len(sta)), key=lambda j: abs(sta[j] - bsta[i]))]) for i in range(len(bsta))]))
    print("  tolerance -> breaks of the algorithm on the same ground:")
    for tol in (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0):
        idx = rdp(sta, z, tol); print("    tol %4.2f m -> %2d PVIs at %s" % (tol, len(idx), ["%.0f" % sta[i] for i in idx]))


def run(s, names, tol, min_seg, mark, save, window, min_slope=0.0):
    breaks = []; segments = []; summary = []
    for f in [f for f in SPEC if f["name"] in names]:
        name = f["name"]; verts = list(reversed(f["alignment"])) if f["reverse"] else f["alignment"]
        r, sta, z = read_eg(s, name); zs = smooth(z, window)
        idx = enforce_min_seg(rdp(sta, zs, tol), sta, zs, tol, min_seg)
        idx = [idx[0]] + sorted({stitch(i, sta, z, zs) for i in idx[1:-1]} - {idx[0], idx[-1]}) + [idx[-1]]
        # the two ends must stay at the alignment ends: if the raw ground there is a spike (more than 0.3 m off the trend), the trend elevation is used
        end_notes = []; zpvi = {i: z[i] for i in idx}
        for k, i in ((0, idx[0]), (len(idx) - 1, idx[-1])):
            if abs(z[i] - zs[i]) > 0.3: end_notes.append("%s end: ground %.2f is %.2f m off the trend, trend %.2f used" % ("start" if k == 0 else "end", z[i], z[i] - zs[i], zs[i])); zpvi[i] = zs[i]
        # no reverse slope in the flow direction
        idx, dropped, ends_adverse = enforce_monotone(idx, sta, zpvi, zs, min_slope)
        if dropped: end_notes.append("%d break(s) dropped for reverse slope" % dropped)
        if ends_adverse: end_notes.append("END HIGHER THAN START by %.2f m: no compliant line exists, chord kept" % (zpvi[idx[-1]] - zpvi[idx[0]]))
        bsta = [round(sta[i], 3) for i in idx]; bz = [round(zpvi[i], 3) for i in idx]
        flat = sum(1 for i in range(len(bsta) - 1) if (bz[i] - bz[i + 1]) / (bsta[i + 1] - bsta[i]) < 0.0005)
        dep = departures(sta, z, bsta, bz); amax = max(abs(d) for d in dep); rms = math.sqrt(sum(d * d for d in dep) / len(dep))
        deps = departures(sta, zs, bsta, bz); smax = max(abs(d) for d in deps); smax_sta = sta[max(range(len(deps)), key=lambda j: abs(deps[j]))]
        out = s.execute(load_cs(os.path.join(W5, "cs", "31_create_gdp.cs"), NAME=name, STA=", ".join("%.3f" % v for v in bsta), ELEV=", ".join("%.3f" % v for v in bz), STYLE=GDP_STYLE, LABELSET=GDP_LABELS, TEXT_H=STYLES["leader"]["textHeight"] * 0.5, MARK="true" if mark else "false"), description="GDP " + name)
        res = out.get("result", out) if isinstance(out, dict) else out
        bad = [c for c in res["check"] if abs(c["got"] - c["want"]) > 0.005]
        log("%s: %d breaks (tol %.2f m on the %d m trend, min seg %s): trend departs %.2f m at %.0f, raw ground %.2f m (RMS %.2f), segments %s m; %s%s%s" % (name, len(idx), tol, window, min_seg, smax, smax_sta, amax, rms, [int(round(bsta[i + 1] - bsta[i])) for i in range(len(bsta) - 1)], res["log"][-1], "; " + "; ".join(end_notes) if end_notes else "", "; PVI CHECK FAILED %s" % bad if bad else ""))
        pts = res["points"] if res["points"] else [{"i": i, "sta": bsta[i], "elev": bz[i], "x": polyline_interp(verts, bsta[i])[0], "y": polyline_interp(verts, bsta[i])[1]} for i in range(len(bsta))]
        for i, p in enumerate(pts):
            gin = (bz[i] - bz[i - 1]) / (bsta[i] - bsta[i - 1]) if i > 0 else None; gout = (bz[i + 1] - bz[i]) / (bsta[i + 1] - bsta[i]) if i < len(bsta) - 1 else None
            breaks.append({"Label": "%s GB%d" % (name, i), "Channel": name, "GB": i, "Station": p["sta"], "Z_m": p["elev"], "X": p["x"], "Y": p["y"], "GradeIn": None if gin is None else round(gin, 5), "GradeOut": None if gout is None else round(gout, 5)})
        for k, part in enumerate(split_polyline(verts, bsta)):
            L = bsta[k + 1] - bsta[k]
            segments.append({"Label": "%s-%d" % (name, k + 1), "Channel": name, "Seg": k + 1, "StaFrom": bsta[k], "StaTo": bsta[k + 1], "Length_m": round(L, 2), "ZFrom": bz[k], "ZTo": bz[k + 1], "Slope": round((bz[k] - bz[k + 1]) / L, 5) if L > 0 else None, "geometry": part})
        summary.append({"Channel": name, "Length_m": round(sta[-1], 1), "Breaks": len(idx), "Segments": len(idx) - 1, "MinSeg_m": round(min(bsta[i + 1] - bsta[i] for i in range(len(bsta) - 1)), 1), "MaxSeg_m": round(max(bsta[i + 1] - bsta[i] for i in range(len(bsta) - 1)), 1), "TrendDep_m": round(smax, 2), "TrendDepSta": round(smax_sta), "MaxDep_m": round(amax, 2), "RMS_m": round(rms, 2), "ZStart": bz[0], "ZEnd": bz[-1], "MeanSlope": round((bz[0] - bz[-1]) / sta[-1], 5), "AdverseFixed": dropped, "FlatSegments": flat, "Notes": "; ".join(end_notes)})
    if save: s.execute("return Database.Filename;", save=True); log("drawing saved")
    # outputs
    import geopandas as gpd
    from shapely.geometry import Point, LineString
    gb = gpd.GeoDataFrame([{k: v for k, v in b.items()} for b in breaks], geometry=[Point(b["X"], b["Y"]) for b in breaks], crs="EPSG:32640")
    gb.to_file(os.path.join(GDP, "Block4_channel_breaks.shp")); gb.drop(columns="geometry").to_csv(os.path.join(GDP, "Block4_channel_breaks.csv"), index=False)
    gs = gpd.GeoDataFrame([{k: v for k, v in sg.items() if k != "geometry"} for sg in segments], geometry=[LineString(sg["geometry"]) for sg in segments], crs="EPSG:32640")
    gs.to_file(os.path.join(GDP, "Block4_channel_segments.shp")); gs.drop(columns="geometry").to_csv(os.path.join(GDP, "Block4_channel_segments.csv"), index=False)
    with open(os.path.join(GDP, "gdp_summary.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0].keys())); w.writeheader(); w.writerows(summary)
    json.dump({"method": "ground profile read every 1 m from the drawing; trend = rolling median over `smoothing_window_m` + rolling mean over 51 m; Ramer-Douglas-Peucker on the trend with the vertical `tolerance_m`; each break stitched to the raw ground (moved up to 30 m to a sample within 0.3 m of the trend); segments shorter than `min_segment_m` merged; no reverse slope in the flow direction (breaks of a climbing segment dropped, `min_slope_m_per_m` is the smallest fall allowed)", "tolerance_m": tol, "smoothing_window_m": window, "min_segment_m": min_seg, "min_slope_m_per_m": min_slope, "style": GDP_STYLE, "labelSet": GDP_LABELS, "channels": len(summary), "breaks": len(breaks), "segments": len(segments), "calibration": "engineer's sample SAK-CH3-SM GDP (5 PVIs): 0.87 m from the 201 m trend, 2.25 m from the raw ground"}, open(os.path.join(GDP, "gdp_parameters.json"), "w"), indent=1)
    log("%d channels: %d breaks, %d segments -> %s" % (len(summary), len(breaks), len(segments), GDP))


if __name__ == "__main__":
    flags = sys.argv[1:]; valued = ("--tol", "--min-seg", "--window", "--min-slope")
    args = [a for i, a in enumerate(flags) if not a.startswith("--") and not (i > 0 and flags[i - 1] in valued)]   # feature names only: option values are skipped
    tol = float(flags[flags.index("--tol") + 1]) if "--tol" in flags else 0.75; min_seg = float(flags[flags.index("--min-seg") + 1]) if "--min-seg" in flags else 0.0
    window = int(flags[flags.index("--window") + 1]) if "--window" in flags else 201
    min_slope = float(flags[flags.index("--min-slope") + 1]) if "--min-slope" in flags else 0.0
    s = McpSession(command_timeout_ms=900000); log("drawing: %s" % s.identity()["filename"])
    if "--calibrate" in flags: calibrate(s, args[0] if args else "SAK-CH3-SM")
    else:
        names = args or [f["name"] for f in SPEC if f["kind"] == "channel"]
        if not names or not any(f["name"] in names for f in SPEC): sys.exit("no feature selected: " + str(names))
        run(s, names, tol, min_seg, "--no-mark" not in flags, "--no-save" not in flags, window, min_slope)
    s.close()
