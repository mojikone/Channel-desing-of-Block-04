"""Step 39 - wadi depth at the design points (engineer, 2026-10-11): at every point of final/Block4_design_points.shp a cross
section perpendicular to the channel is cut from the design terrain GGC_4_MERGE_HDSM (0.5 m hybrid DSM on the W: server, read
only), the wadi bed and the two bank tops are found and the wadi depth = lower bank top - bed is reported with flags, so that the
design ground can be raised to the bank where a point lies in a wadi bed (bank elevation as ground, conduit depth = wadi depth).

Rules agreed 2026-10-11: half-width per class FP 300 m (HAWCH1-8 is ~200 m wide, SAKCH2-8 ~300 m), SM 100 m, SS 60 m; the bed is
the lowest ground within 30 m of the centreline; a wadi needs 0.5 m of depth. Walls, roofs, trees and other objects of the DSM are
removed by a 30 m grey opening of the profile (anything narrower than 30 m and more than 1.5 m above the opened surface is dropped
and bridged by a straight line); the plot layer LandUSE_block4.shp the engineer offered as a building mask is a cadastral grid
(82 206 residential parcels over the whole block: 516 of the 600 m of the calibration section fell inside "existing" plots), so it
is only counted (PlotsM = metres of the section inside existing plots, every ParcelLand except "Future Plans" and "Proposed").
Bank top, per side, walking outward from the bed on the 5 m-median profile: the first place where the ground has risen
>= 0.5 m above the bed and then either drops >= 0.2 m within 5 m (a crest) or flattens (mean slope over the next 20 m < 2 % with
no rise over 0.3 m); without one, the side's maximum (flagged). The lower of the two bank tops is the bankfull level, as the
engineer measured at SHACH1-12 (3.2 m). Left and right are seen looking downstream; on the panels left is on the left.

Outputs in wadi/: <tag>_wadi_points.shp/.csv (the points with BedZ, BankLZ, BankRZ, BankZ = lower, BankSide, WadiDepth, GroundPt
= DSM at the point, BankMinusGdp, flags), <tag>_wadi_sections.shp (the section lines, left end first), <tag>_sections.png (one
panel per point: raw and processed profile, masked spans, bed, bank tops, GDP), wadi_parameters.json.
    python 39_wadi_depth.py --gca HAW | --channel HAW-CH1-FP[,SHA-CH1-FP] | --points SHACH1-12[,...] | --all   [--tag name]
Classes (engineer, 2026-10-11, after the HAW-CH1-FP prototype: HAWCH1-1 to -4 lie in a plain and are no wadi): none = depth under
0.5 m, or under 1.0 m with a second low beyond both banks or the bed at the edge of the 30 m window (undulating plain; WadiDepth
and Raise are 0 and the Civil 3D ground stands); shallow = 0.5 to 1.0 m with one low; clear = 1.0 m and more; braided = 1.0 m and
more with a second low beyond a bank. Raise = lower bank top - GDP at the point (floored at 0); at a fix point the bed stays on the
GDP and Raise is the library (embankment) depth above it from inputs/fix_raise.json (engineer, 2026-10-11: 2.5 m as standard,
3.0 m at SHACH1-13 because only the segment from SHACH1-12 can take a deeper library; WadiDepth is kept). wadi/wadi_results.csv accumulates
every run by SGLabel and 37_final_layers.py joins WadiDepth / WadiClass / BankZ / Raise into the final point layer."""
import os, sys, json, math, time
import numpy as np, pandas as pd, geopandas as gpd, rasterio, rasterio.windows as rw
from scipy.ndimage import map_coordinates, median_filter, minimum_filter1d, maximum_filter1d
from shapely.geometry import LineString, Point
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE); CB = os.path.dirname(W6); W5 = os.path.join(CB, "W5")
OUT = os.path.join(W6, "wadi"); LOG = os.path.join(W6, "log", "39_wadi_depth.log"); os.makedirs(OUT, exist_ok=True); os.makedirs(os.path.dirname(LOG), exist_ok=True)
RASTERS = {"dtm": r"W:\2224 Flood Protection Scheme in North & South Batinah_MAFWWR\10-DATABASE\01 DEM\Prosessed_DEM\OUTPUT\GGC4_DTM_GMAP_NSA.tif",     # the Civil 3D ground (W4 strips, EG profiles, GDP): the design surface
           "hdsm": r"W:\2224 Flood Protection Scheme in North & South Batinah_MAFWWR\10-DATABASE\01 DEM\Prosessed_DEM\OUTPUT\GGC_4_MERGE_HDSM.tif"}   # hybrid DSM with buildings, used for the 2026-10-11 prototype
LANDUSE = r"W:\2224 Flood Protection Scheme in North & South Batinah_MAFWWR\06-WORKING\13-Study and Design\01-FS and PD\00-General\02-Land Use\ALL_MOH_CLEANED\LandUSE_block4.shp"
POINTS = os.path.join(W6, "final", "Block4_design_points.shp"); SPEC = json.load(open(os.path.join(W5, "civil3d", "build_spec_w5.json")))
HALF_W = {"FP": 300.0, "SM": 100.0, "SS": 60.0}; W_MAX = 300.0; BED_WIN = 30.0; MIN_DEPTH = 0.5; STEP = 0.5; MEDIAN_M = 5.0   # W_MAX: the search goes on to here when no bank top lies within the class half-width
CREST_DROP, CREST_M = 0.2, 5.0; FLAT_M, FLAT_SLOPE, FLAT_RISE = 20.0, 0.02, 0.3; PLANNED = {"Future Plans", "Proposed"}
OPEN_M, OBJ_H = 30.0, 1.5                       # objects narrower than OPEN_M and higher than OBJ_H above the opened profile are removed
FIXR = json.load(open(os.path.join(W6, "inputs", "fix_raise.json")))   # raise at fix points = library depth: default 2.5 m, per-point overrides (SHACH1-13: 3.0)
BENCH_MAX, LOOK_M, STEEP_RISE, STEEP_M = 1.5, 50.0, 1.0, 15.0   # a bank-top candidate less than BENCH_MAX above the bed is a bench (not the bank) when a steeper rise (STEEP_RISE within STEEP_M) follows within LOOK_M


def base(p): return {"SGLabel": p["SGLabel"], "Label": p["Label"], "Channel": p["Channel"], "Class": p["Class"], "StaLbl": p["StaLbl"], "Station": round(float(p["Station"]), 2), "X": p["X"], "Y": p["Y"]}
A = sys.argv[1:]
def opt(k, default=None): return A[A.index(k) + 1] if k in A else default
RASTER_KEY = (opt("--raster") or "dtm").lower(); RASTER = RASTERS[RASTER_KEY]   # --raster dtm (default, the design surface) | hdsm


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + "  " + msg; print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")


# ---------------------------------------------------------------- the points to do
pts = gpd.read_file(POINTS)
if "--all" in A: sel = pts
elif opt("--points"): sel = pts[pts["SGLabel"].isin(opt("--points").split(","))]
elif opt("--channel"): sel = pts[pts["Channel"].isin(opt("--channel").split(","))]
elif opt("--gca"): sel = pts[pts["Channel"].str.startswith(opt("--gca").upper() + "-")]
else: sys.exit("give --gca HAW, --channel NAME[,NAME], --points SGLABEL[,...] or --all")
tag = opt("--tag") or (opt("--gca") or opt("--channel") or opt("--points") or "all").replace(",", "+").upper() if opt("--gca") else (opt("--tag") or (opt("--channel") or opt("--points") or "all").replace(",", "+"))
STAMP = time.strftime("%Y%m%d_%H%M")
if RASTER_KEY != "dtm" and not opt("--tag"): tag += "_" + RASTER_KEY.upper()
if sel.empty: sys.exit("no point selected")
log("39 wadi depth | %d points, tag %s, raster %s" % (len(sel), tag, RASTER_KEY))

# ---------------------------------------------------------------- channel geometry: oriented centrelines, tangent at a station
chan = {}
for f in SPEC:
    if f["kind"] != "channel": continue
    v = list(reversed(f["alignment"])) if f["reverse"] else f["alignment"]
    xy = np.array([(p["x"], p["y"]) for p in v]); seg = np.diff(xy, axis=0); L = np.hypot(seg[:, 0], seg[:, 1]); cum = np.concatenate([[0], np.cumsum(L)])
    chan[f["name"]] = {"xy": xy, "seg": seg / L[:, None], "cum": cum, "length": cum[-1]}


def tangent(name, s):
    c = chan[name]; cum, d = c["cum"], c["seg"]; k = int(np.searchsorted(cum, s, side="right") - 1); k = max(0, min(k, len(d) - 1))
    if abs(s - cum[k]) < 1e-6 and 0 < k: v = d[k - 1] + d[k]          # at a vertex: mean of the two directions
    else: v = d[k]
    return v / np.hypot(*v)


# ---------------------------------------------------------------- terrain and plots
ds = rasterio.open(RASTER); nodata = ds.nodata
LU = {"frame": None, "bounds": None}
def plots_near(line):
    """Existing plots (ParcelLand not planned) crossing the section line; the plots are read once per 2 km neighbourhood."""
    b = line.bounds; cb = LU["bounds"]
    if cb is None or not (cb[0] <= b[0] and cb[1] <= b[1] and cb[2] >= b[2] and cb[3] >= b[3]):
        pad = 2000.0; LU["bounds"] = (b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad)
        fr = gpd.read_file(LANDUSE, bbox=LU["bounds"]); LU["frame"] = fr[~fr["ParcelLand"].isin(PLANNED)]
    fr = LU["frame"]
    return fr[fr.intersects(line)] if len(fr) else fr


def sample(xs, ys):
    """Bilinear DSM values at the points (nodata -> NaN) from one window read."""
    pad = 2.0; w = rw.from_bounds(xs.min() - pad, ys.min() - pad, xs.max() + pad, ys.max() + pad, ds.transform); w = w.round_offsets().round_lengths()
    a = ds.read(1, window=w).astype("float64"); a[a == nodata] = np.nan; a[a > 1e30] = np.nan
    tr = ds.window_transform(w); cols, rows = (~tr) * (xs, ys)
    return map_coordinates(a, [np.asarray(rows) - 0.5, np.asarray(cols) - 0.5], order=1, mode="nearest")


def fill_nan(g):
    ok = ~np.isnan(g)
    if ok.sum() == 0: return g
    return np.interp(np.arange(len(g)), np.flatnonzero(ok), g[ok])


def bank_top(side, limit):
    """side[0] = bed, outward; candidates up to index limit (the ground beyond is still used to look ahead).
    Returns (index, z, how, benches) with how in crest / flat / max; benches = candidates skipped as benches."""
    z_bed = side[0]; n = len(side); kc = int(round(CREST_M / STEP)); kf = int(round(FLAT_M / STEP)); kl = int(round(LOOK_M / STEP)); ks = int(round(STEEP_M / STEP)); benches = 0
    for i in range(1, min(limit, n - 1)):
        if side[i] - z_bed < MIN_DEPTH or side[i] < side[i - 1]: continue
        ahead_c = side[i + 1: i + 1 + kc]; ahead_f = side[i + 1: i + 1 + kf]
        crest = len(ahead_c) > 0 and side[i] - ahead_c.min() >= CREST_DROP
        flat = len(ahead_f) == kf and (ahead_f[-1] - side[i]) / FLAT_M < FLAT_SLOPE and ahead_f.max() - side[i] < FLAT_RISE
        if not (crest or flat): continue
        if side[i] - z_bed < BENCH_MAX:                                   # low candidate: a bench if the ground climbs steeply again soon after
            look = side[i: i + 1 + kl]
            if any(look[j + ks] - look[j] >= STEEP_RISE for j in range(0, len(look) - ks)): benches += 1; continue
        return i, side[i], "crest" if crest else "flat", benches
    i = int(np.nanargmax(side[:max(limit, 2)])); return i, side[i], "max", benches


# ---------------------------------------------------------------- the sections
rows, lines, panels = [], [], []
for _, p in sel.sort_values(["Channel", "Station"]).iterrows():
    name, s = p["Channel"], float(p["Station"]); W = HALF_W[p["Class"]]
    d = tangent(name, s); nL = np.array([-d[1], d[0]])                       # left normal, looking downstream
    t = np.arange(-W_MAX, W_MAX + STEP / 2, STEP); xs = p["X"] - t * nL[0]; ys = p["Y"] - t * nL[1]   # t < 0 is the left side; sampled to W_MAX, searched within W first
    line = LineString([(xs[0], ys[0]), (xs[-1], ys[-1])])
    raw = sample(xs, ys); flags = []
    if np.isnan(raw).all(): rows.append({**base(p), "Flag": "no terrain"}); continue
    if np.isnan(raw).any(): flags.append("%d m outside the terrain" % (np.isnan(raw).sum() * STEP))
    plots = plots_near(line); inplots = np.zeros(len(t), bool)
    if len(plots):
        from shapely import contains_xy
        geom = plots.geometry.union_all() if hasattr(plots.geometry, "union_all") else plots.geometry.unary_union
        inplots = contains_xy(geom, xs, ys)
    filled = fill_nan(raw.copy()); k_open = int(round(OPEN_M / STEP)) | 1
    opened = maximum_filter1d(minimum_filter1d(filled, k_open, mode="nearest"), k_open, mode="nearest")   # grey opening: bumps narrower than OPEN_M go
    masked = (filled - opened) > OBJ_H                                                                     # walls, roofs, trees, narrow bunds
    g = filled.copy(); g[masked] = np.nan; g = fill_nan(g); g = median_filter(g, size=int(round(MEDIAN_M / STEP)) | 1, mode="nearest")
    if masked.any(): flags.append("objects removed over %d m" % (masked.sum() * STEP))
    ib = np.flatnonzero(np.abs(t) <= BED_WIN); i_bed = ib[int(np.nanargmin(g[ib]))]; z_bed = g[i_bed]; t_bed = t[i_bed]
    if abs(abs(t_bed) - BED_WIN) < STEP: flags.append("bed at the edge of the 30 m window")
    left = g[i_bed::-1]; right = g[i_bed:]
    limL = i_bed - int(np.argmin(np.abs(t + W))) + 1; limR = int(np.argmin(np.abs(t - W))) - i_bed + 1   # samples from the bed to the class half-width
    def find(side, lim, label):
        i, z, how, b = bank_top(side, min(lim, len(side)))
        if how == "max" and len(side) > lim:                                  # nothing within W: look on to W_MAX
            i2, z2, how2, b2 = bank_top(side, len(side))
            if how2 != "max": flags.append("%s bank top beyond the %d m half-width, at %d m" % (label, W, STEP * i2)); return i2, z2, how2 + " beyond W", b2, len(side)
            flags.append("no %s bank top within %d m (max within %d m used)" % (label, W_MAX, W))
        elif how == "max": flags.append("no %s bank top within %d m (max used)" % (label, W))
        return i, z, how, b, lim
    iL, zL, howL, bL, limL = find(left, limL, "left"); iR, zR, howR, bR, limR = find(right, limR, "right")
    tL = t[i_bed - iL]; tR = t[i_bed + iR]
    if bL or bR: flags.append("benches skipped: %d left, %d right" % (bL, bR))
    side = "L" if zL <= zR else "R"; z_bank = min(zL, zR); depth = z_bank - z_bed
    segL, segR = left[iL:max(limL, iL + 1)], right[iR:max(limR, iR + 1)]
    outL, outR = float(np.nanmax(segL)), float(np.nanmax(segR))
    second = []
    if depth >= MIN_DEPTH:
        if np.nanmin(segL) < z_bed + 0.5 * depth: second.append("left")
        if np.nanmin(segR) < z_bed + 0.5 * depth: second.append("right")
    if second: flags.append("second low beyond the %s bank" % " and ".join(second))
    g0 = float(raw[np.argmin(np.abs(t))]); gdp = None if pd.isna(p["GdpZ"]) else float(p["GdpZ"])
    if not pd.isna(p["Ground"]) and abs(g0 - float(p["Ground"])) > 0.5: flags.append("DSM at the point %.2f vs EG %.2f" % (g0, p["Ground"]))
    bed_edge = abs(abs(t_bed) - BED_WIN) < STEP
    if depth < MIN_DEPTH: wclass, why = "none", "depth < %.1f m" % MIN_DEPTH
    elif depth < 1.0 and len(second) == 2: wclass, why = "none", "undulating ground, a second low beyond both banks"
    elif depth < 1.0 and bed_edge: wclass, why = "none", "no low at the centreline"
    elif depth < 1.0: wclass, why = "shallow", ""
    else: wclass, why = ("braided" if second else "clear"), ""
    if wclass == "none": flags.insert(0, "no wadi: " + why)
    depth_out = 0.0 if wclass == "none" else float(depth)
    raise_ = None if gdp is None else (0.0 if wclass == "none" else max(0.0, float(z_bank) - gdp))
    if gdp is not None and wclass != "none" and z_bank < gdp: flags.append("GDP already %.2f m above the lower bank" % (gdp - z_bank))
    is_fix = not pd.isna(p.get("Fix")) and str(p.get("Fix")).strip() != ""     # engineer, 2026-10-11: at a fix point the bed stays on the GDP and the raise is the library depth (inputs/fix_raise.json)
    if is_fix:
        bank_above = None if gdp is None else float(z_bank) - gdp
        raise_ = float(FIXR["points"].get(str(p["SGLabel"]), FIXR["default"]))
        flags.append("fix point %s: raise = library depth %.1f m above the GDP bed%s" % (p["Fix"], raise_, "" if bank_above is None else " (bank %+.2f m vs GDP)" % bank_above))
    row = {"SGLabel": p["SGLabel"], "Label": p["Label"], "Channel": name, "Class": p["Class"], "StaLbl": p["StaLbl"], "Station": round(s, 2), "HalfW": W,
           "GroundPt": round(g0, 2), "Ground": p["Ground"], "GdpZ": gdp, "BedZ": round(float(z_bed), 2), "BedOff": round(float(t_bed), 1),
           "BankLZ": round(float(zL), 2), "BankLOff": round(float(tL), 1), "BankLHow": howL, "BankRZ": round(float(zR), 2), "BankROff": round(float(tR), 1), "BankRHow": howR,
           "BankZ": round(float(z_bank), 2), "BankSide": side, "WadiDepth": round(depth_out, 2), "DepthRaw": round(float(depth), 2), "WadiClass": wclass, "Raise": None if raise_ is None else round(raise_, 2), "BankMinGdp": None if gdp is None else round(float(z_bank) - gdp, 2),
           "OuterLZ": round(outL, 2), "OuterRZ": round(outR, 2), "MaskedM": round(float(masked.sum() * STEP), 1), "PlotsM": round(float(inplots.sum() * STEP), 1), "Flag": "; ".join(flags), "X": p["X"], "Y": p["Y"]}
    rows.append(row); lines.append({"SGLabel": p["SGLabel"], "Channel": name, "StaLbl": p["StaLbl"], "HalfW": W, "WadiDepth": row["WadiDepth"], "geometry": line})
    panels.append((row, t, raw, g, masked, i_bed, (tL, zL), (tR, zR), gdp))
    log("%-10s %-11s %s  bed %6.2f at %+6.1f  banks L %6.2f (%s, %+6.1f) R %6.2f (%s, %+6.1f)  depth %5.2f (%s)  %s" % (p["SGLabel"], name, p["StaLbl"], z_bed, t_bed, zL, howL, tL, zR, howR, tR, depth, side, "; ".join(flags)))


# ---------------------------------------------------------------- outputs
COLS = ["SGLabel", "Label", "Channel", "Class", "StaLbl", "Station", "HalfW", "GroundPt", "Ground", "GdpZ", "BedZ", "BedOff", "BankLZ", "BankLOff", "BankLHow", "BankRZ", "BankROff", "BankRHow", "BankZ", "BankSide", "WadiDepth", "DepthRaw", "WadiClass", "Raise", "BankMinGdp", "OuterLZ", "OuterRZ", "MaskedM", "PlotsM", "Flag"]
df = pd.DataFrame(rows); df = df.reindex(columns=COLS + ["X", "Y"])
if "--no-results" not in A and RASTER_KEY == "dtm":                       # only the design-surface run feeds the final layer
    RES = os.path.join(OUT, "wadi_results.csv"); res = df[COLS].copy(); res["Run"] = STAMP; res["Raster"] = RASTER_KEY
    if os.path.exists(RES):
        old = pd.read_csv(RES); old = old[~old["SGLabel"].isin(res["SGLabel"])]; res = pd.concat([old, res], ignore_index=True)
    res.sort_values(["Channel", "Station"]).to_csv(RES, index=False); log("wadi_results.csv carries %d points (37_final_layers.py joins them into the final layer)" % len(res))
gpts = gpd.GeoDataFrame(df[COLS], geometry=[Point(r["X"], r["Y"]) for r in rows], crs="EPSG:32640")
gpts.to_file(os.path.join(OUT, tag + "_wadi_points.shp")); df[COLS].to_csv(os.path.join(OUT, tag + "_wadi_points.csv"), index=False)
if lines: gpd.GeoDataFrame(lines, crs="EPSG:32640").to_file(os.path.join(OUT, tag + "_wadi_sections.shp"))
json.dump({"half_width_m": HALF_W, "bed_window_m": BED_WIN, "min_depth_m": MIN_DEPTH, "step_m": STEP, "median_m": MEDIAN_M, "crest_drop_m": CREST_DROP, "crest_within_m": CREST_M, "flat_over_m": FLAT_M, "flat_slope": FLAT_SLOPE, "flat_max_rise_m": FLAT_RISE,
           "planned_plot_classes_not_masked": sorted(PLANNED), "w_max_m": W_MAX, "bench_max_m": BENCH_MAX, "look_m": LOOK_M, "steep_rise_m": STEEP_RISE, "steep_within_m": STEEP_M,
           "raster_key": RASTER_KEY, "raster": RASTER, "rasters": RASTERS, "landuse": LANDUSE, "points": POINTS}, open(os.path.join(OUT, "wadi_parameters.json"), "w"), indent=1)
# panels: one PNG per channel
channels = sorted(set(pn[0]["Channel"] for pn in panels)); pngs = []
from matplotlib.backends.backend_pdf import PdfPages; pdf = PdfPages(os.path.join(OUT, tag + "_sections.pdf"))   # all channels of the run, one page each
for ch in channels:
    sub = [pn for pn in panels if pn[0]["Channel"] == ch]
    n = len(sub); ncol = 2 if n > 1 else 1; nrow = max(1, math.ceil(n / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(9.0 * ncol, 3.0 * nrow), squeeze=False)
    for ax in axes.flat: ax.set_visible(False)
    for k, (row, t, raw, g, masked, i_bed, (tL, zL), (tR, zR), gdp) in enumerate(sub):
        ax = axes.flat[k]; ax.set_visible(True)
        on = np.flatnonzero(np.diff(np.concatenate([[0], masked.astype(int), [0]])))
        for a, b in zip(on[0::2], on[1::2]): ax.axvspan(t[a], t[min(b, len(t) - 1)], color="#f4c7c3", alpha=0.6, lw=0)
        ax.plot(t, raw, color="#9a9a9a", lw=0.6, label="DSM raw"); ax.plot(t, g, color="black", lw=1.0, label="objects removed + 5 m median")
        ax.axhline(row["BankZ"], color="#c62828", lw=0.8, ls="--" if row["WadiClass"] != "none" else ":"); ax.axvline(0, color="#1565c0", lw=0.6, ls=":")
        ax.plot(t[i_bed], row["BedZ"], "o", color="#1565c0", ms=5, zorder=5); ax.plot([tL, tR], [zL, zR], "v", color="#c62828", ms=6, zorder=5)
        ax.annotate("L %.2f" % zL, (tL, zL), textcoords="offset points", xytext=(-4, 6), fontsize=7, color="#c62828", ha="right")
        ax.annotate("R %.2f" % zR, (tR, zR), textcoords="offset points", xytext=(4, 6), fontsize=7, color="#c62828", ha="left")
        ax.annotate("bed %.2f" % row["BedZ"], (t[i_bed], row["BedZ"]), textcoords="offset points", xytext=(0, -11), fontsize=7, color="#1565c0", ha="center")
        if gdp is not None: ax.plot(0, gdp, "s", color="#2e7d32", ms=5, zorder=6); ax.annotate("GDP %.2f" % gdp, (0, gdp), textcoords="offset points", xytext=(5, -10), fontsize=7, color="#2e7d32")
        rz = "-" if row["Raise"] is None else "%.2f" % row["Raise"]
        ax.set_title("%s   %s %s   wadi depth %.2f m, %s, raise %s m (%s bank %.2f, bed %.2f)%s" % (row["SGLabel"], row["Channel"], row["StaLbl"], row["WadiDepth"], row["WadiClass"], rz, row["BankSide"], row["BankZ"], row["BedZ"], "\n" + row["Flag"] if row["Flag"] else ""), fontsize=8, loc="left")
        xr = max(row["HalfW"], abs(tL) + 20, abs(tR) + 20); ax.set_xlim(-xr, xr); ax.set_xlabel("offset from the centreline, m   (left bank <- 0 -> right bank, looking downstream)", fontsize=7); ax.set_ylabel("m", fontsize=7); ax.tick_params(labelsize=7); ax.grid(True, lw=0.3, alpha=0.5)
        if k == 0: ax.legend(fontsize=7, loc="upper right")
    fig.suptitle("Wadi depth at the design points - %s  (%s; objects narrower than %.0f m removed, pink; bank top = end of the first rise >= %.1f m, benches skipped; lower bank dashed, dotted where no wadi)" % (ch, os.path.basename(RASTER), OPEN_M, MIN_DEPTH), fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.97)); png = os.path.join(OUT, (tag + "_sections.png") if len(channels) == 1 else (tag + "_sections_" + ch + ".png")); fig.savefig(png, dpi=130); pdf.savefig(fig); plt.close(fig); pngs.append(os.path.basename(png))
pdf.close(); log("written %s: %d points -> %s_wadi_points.shp/.csv, %s_wadi_sections.shp, %s_sections.pdf, %s" % (OUT, len(rows), tag, tag, tag, ", ".join(pngs)))
ds.close()
