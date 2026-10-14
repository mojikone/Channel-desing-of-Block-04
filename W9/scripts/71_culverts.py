"""Step 71 (W8, R5) - road crossings of the channels, the existing culverts, and the proposed box culverts. R5 changes (his comments of
2026-10-13): the clear height of the culvert is the full channel depth (2.5 or 3.0 m, the road embankment above it); existing structures
counted within 10 m of the crossing only; the culvert slope is the channel slope at the crossing. Original header of W7 step 71:
(engineer,
2026-10-12: "wherever the channels are crossing a road (Batinah Highway, Batinah Coastal Road, Muscat Expressway) we need a
culvert ... culverts will be the same width as the channels, just set the number of cells; 2.5 and 3 m deep channels, 0.5 m
embankment, so 2 and 2.5 m clear height"). Method of the Block 6 channel design report and cost sheet:
  * crossing = intersection of a channel alignment (final segment layer, W7) with a road centreline; the reach there gives the
    200-yr design flow, bed width, depth, slope and velocity of the SewerGEMS run named in --run;
  * existing structure: the barrels of the Batinah culvert inventory (Culverts_2_4.shp: Num cells x W x H, Code, length) within
    150 m of the crossing, the nearest structure code; photos are not on file and stay blank;
  * proposed: box cells of the Oman Highway Design Standard 2017 (Table 12.5.3.1), clear width 4.0 m, clear height = channel
    depth - 0.5 m (2.0 or 2.5 m); cells = ceil(bed width / 4.0); then the FHWA HDS-5 headwater check of the engineer's tool
    (inlet control form 1, outlet control, Ke 0.4, n 0.015, allowable HW = 1.2 D; the tailwater is the normal depth of the
    downstream channel); cells are added until the check passes;
  * cost: the Block 6 build-up (structural works: concrete per m of length N((B+0.25)(D+0.6)-BD)+0.8 m3/m, rebar 0.12 t/m3 at
    417.1 OMR/t, concrete 106.9 OMR/m3, blinding, waterproofing; road works: pavement, ABC, BBC, WBC, TC, marking, guard rails,
    posts; CNG; dismantling of the existing structure), the crossing length taken as the road corridor width (Batinah Highway
    45 m, Batinah Coastal Road 32 m, an assumption until measured).
Writes W7/culverts/: crossings.csv, culverts_proposed.csv, culverts_existing.csv, crossings.gpkg (points, existing barrels near),
culverts.md.
    python 71_culverts.py [--run run_20261012_1758]"""
import os, sys, math, re, json
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import Point, MultiPoint
from shapely.ops import nearest_points
HERE = os.path.dirname(os.path.abspath(__file__)); W8 = os.path.dirname(HERE); CB = os.path.dirname(W8); B4 = os.path.dirname(CB); W7 = os.path.join(CB, "W7")   # W8 here is the W9 folder (the script sits in W9/scripts)   # W8 writes its own culverts/; the design data stay in W7
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
RUN = opt("--run", "run_20261012_1758"); SC = "200yr"
OUT = os.path.join(W8, "culverts"); os.makedirs(OUT, exist_ok=True); RADIUS = float(opt("--radius", 10.0))
Wd = "W:/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/06-WORKING/"
ROADS = {"Batinah Highway": (Wd + "03-Hydrology/01 GIS DATA/SHP/Bathinah Highway CL.shp", 45.0), "Batinah Coastal Road": (Wd + "03-Hydrology/01 GIS DATA/SHP/Batinah Coastal RD CL.shp", 32.0),
         "Muscat Expressway": (Wd + "03-Hydrology/01 GIS DATA/SHP/Muscat Expressway CL.shp", 50.0),
         "North Batinah Bypass": (os.path.join(B4, "Hydrology", "SHP", "Bypass road alignment", "North Batina Bypass.shp"), 45.0)}   # W9: the planned bypass, corridor as the Highway's
END_RADIUS = 150.0   # W9: an outfall channel that stops within this distance of the Coastal Road without crossing it gets its culvert there
CULV = Wd + "04-Hydraulic/05 Small Tasks/18 Channel Design/Master Plan Map/Data for Master Plan/SHP/Culverts/Existing Culverts Batinah/Culverts_2_4.shp"
# ---- the design (sizes resolved by class) and the segment geometry
exp = os.path.join(W7, "sewergems", "results", RUN, "bridge_exports", "conduits_%s.csv" % SC)
if not os.path.exists(exp): exp = os.path.join(r"D:\VBOX\bridge\out\b4", RUN, "conduits_%s.csv" % SC)
c = pd.read_csv(exp).set_index("label")
seg = gpd.read_file(os.path.join(W7, "final", "Block4_design_segments.shp"))
seg = seg.merge(c[["flow", "velocity", "slope", "rise_m", "span_m", "depthin", "depthout"]], left_on="SGLabel", right_index=True, how="left")
# ---- crossings
rows = []
for road, (path, corridor) in ROADS.items():
    r = gpd.read_file(path).to_crs("EPSG:32640"); rline = r.geometry.union_all()
    for _, s in seg.iterrows():
        x = s.geometry.intersection(rline)
        if x.is_empty: continue
        pts = [x] if isinstance(x, Point) else [g for g in getattr(x, "geoms", []) if isinstance(g, Point)]
        for p in pts:
            d_along = s.geometry.project(p); sta = float(s["FromSta"]) + d_along
            # skew: angle between the channel tangent and the road tangent (0 = perpendicular crossing)
            eps = 5.0; a = s.geometry.interpolate(max(d_along - eps, 0)); b = s.geometry.interpolate(min(d_along + eps, s.geometry.length)); tch = math.atan2(b.y - a.y, b.x - a.x)
            near = nearest_points(rline, p)[0]; dr = rline.project(near) if hasattr(rline, "project") else None
            try:
                ra = rline.interpolate(max(dr - eps, 0)); rb = rline.interpolate(dr + eps); trd = math.atan2(rb.y - ra.y, rb.x - ra.x)
                skew = abs((math.degrees(tch - trd) + 90) % 180 - 90); skew = abs(90 - skew) if skew > 45 else skew
            except Exception: skew = float("nan")
            rows.append(dict(road=road, corridor_m=corridor, channel=s["Channel"], cls=s["Class"], reach=s["SGLabel"], station_m=round(sta, 1), x=round(p.x, 1), y=round(p.y, 1), skew_deg=round(skew, 1),
                             Q200=round(float(s["flow"]), 1), span_m=float(s["span_m"]), rise_m=float(s["rise_m"]), slope=float(s["slope"]), velocity=round(float(s["velocity"]), 2), depth_m=round(float(np.nanmax([s["depthin"], s["depthout"]])), 2)))
# W9: the outfall channels that end just short of the Coastal Road (HAW-CH7-SS, SHA-CH3-SM, SAK-CH3-SM, SAK-CH5-SS): the crossing is
# the nearest point of the road to the channel end, with the width, slope and flow of the last reach
_outf = pd.read_csv(os.path.join(W8, "report", "data", "outfalls.csv")); _cr_line = gpd.read_file(ROADS["Batinah Coastal Road"][0]).to_crs("EPSG:32640").geometry.union_all()
_crossed = {r["channel"] for r in rows if r["road"] == "Batinah Coastal Road"}
for chn in _outf.channel:
    if chn in _crossed: continue
    s_ch = seg[seg.Channel == chn].sort_values("Seg")
    if not len(s_ch): continue
    last = s_ch.iloc[-1]; end = Point(last.geometry.coords[-1]); d_end = end.distance(_cr_line)
    if d_end > END_RADIUS: continue
    p = nearest_points(_cr_line, end)[0]; eps = 5.0; a = last.geometry.interpolate(max(last.geometry.length - eps, 0)); tch = math.atan2(end.y - a.y, end.x - a.x)
    dr = _cr_line.project(p); ra = _cr_line.interpolate(max(dr - eps, 0)); rb = _cr_line.interpolate(dr + eps); trd = math.atan2(rb.y - ra.y, rb.x - ra.x)
    skew = abs((math.degrees(tch - trd) + 90) % 180 - 90); skew = abs(90 - skew) if skew > 45 else skew
    rows.append(dict(road="Batinah Coastal Road", corridor_m=ROADS["Batinah Coastal Road"][1], channel=chn, cls=last["Class"], reach=last["SGLabel"], station_m=round(float(last["FromSta"]) + float(last.geometry.length), 1), x=round(p.x, 1), y=round(p.y, 1), skew_deg=round(skew, 1),
                     Q200=round(float(last["flow"]), 1), span_m=float(last["span_m"]), rise_m=float(last["rise_m"]), slope=float(last["slope"]), velocity=round(float(last["velocity"]), 2), depth_m=round(float(np.nanmax([last["depthin"], last["depthout"]])), 2), extended=round(d_end, 1)))
    print("  end-of-channel crossing added: %s, %.0f m short of the Coastal Road" % (chn, d_end))
# W9 (his list, 2026-10-14): the channels that START just downstream of the bypass take their runoff from across the road: a culvert
# under the bypass at the channel start, sized on the first reach (its width, depth, slope and flow)
START_AT_BYPASS = ["SHA-CH20-SS", "SAK-CH4-SS", "SHA-CH14-SS", "SAK-CH3-SM", "SHA-CH8-SS", "SHA-CH6-SM", "SAR-CH2-SM", "SHA-CH10-SS", "SHA-CH9-SS"]
_by_line = gpd.read_file(ROADS["North Batinah Bypass"][0]).to_crs("EPSG:32640").geometry.union_all()
_crossed_by = {r["channel"] for r in rows if r["road"] == "North Batinah Bypass"}
for chn in START_AT_BYPASS:
    s_ch = seg[seg.Channel == chn].sort_values("Seg")
    if not len(s_ch): print("  start-at-bypass channel not in the design:", chn); continue
    first = s_ch.iloc[0]; start = Point(first.geometry.coords[0]); d_start = start.distance(_by_line)
    if chn in _crossed_by: print("  %s already crosses the bypass; start culvert skipped" % chn); continue
    p = nearest_points(_by_line, start)[0]; eps = 5.0; b = first.geometry.interpolate(min(eps, first.geometry.length)); tch = math.atan2(b.y - start.y, b.x - start.x)
    dr = _by_line.project(p); ra = _by_line.interpolate(max(dr - eps, 0)); rb = _by_line.interpolate(dr + eps); trd = math.atan2(rb.y - ra.y, rb.x - ra.x)
    skew = abs((math.degrees(tch - trd) + 90) % 180 - 90); skew = abs(90 - skew) if skew > 45 else skew
    rows.append(dict(road="North Batinah Bypass", corridor_m=ROADS["North Batinah Bypass"][1], channel=chn, cls=first["Class"], reach=first["SGLabel"], station_m=round(float(first["FromSta"]), 1), x=round(p.x, 1), y=round(p.y, 1), skew_deg=round(skew, 1),
                     Q200=round(float(first["flow"]), 1), span_m=float(first["span_m"]), rise_m=float(first["rise_m"]), slope=float(first["slope"]), velocity=round(float(first["velocity"]), 2), depth_m=round(float(np.nanmax([first["depthin"], first["depthout"]])), 2), start_short=round(d_start, 1)))
    print("  start-of-channel crossing added under the bypass: %s, start %.0f m from the bypass, first reach %s %.0f m3/s %.1f m wide" % (chn, d_start, first["SGLabel"], first["flow"], first["span_m"]))
cr = pd.DataFrame(rows)
if "extended" not in cr.columns: cr["extended"] = np.nan
if "start_short" not in cr.columns: cr["start_short"] = np.nan
def chkey(n):
    m = re.match(r"^(HAW|SHA|SAR|SAK)-CH(\d+)", n); return ({"HAW": 0, "SHA": 1, "SAR": 2, "SAK": 3}[m.group(1)], int(m.group(2))) if m else (9, 0)
cr["k"] = cr.channel.map(chkey); cr = cr.sort_values(["k", "road", "station_m"]).drop(columns="k").reset_index(drop=True); cr.insert(0, "id", range(1, len(cr) + 1))
print("crossings:", len(cr), cr.groupby("road").size().to_dict())
# ---- existing structures within 150 m (barrels grouped by structure code)
cu = gpd.read_file(CULV).to_crs("EPSG:32640"); cu["mid"] = cu.geometry.interpolate(0.5, normalized=True)
ex_rows = []; ex_near = []
for _, k in cr.iterrows():
    p = Point(k.x, k.y); d = cu.mid.distance(p); near = cu[d < RADIUS].copy(); near["dist_m"] = d[d < RADIUS].round(1)
    if len(near) == 0: ex_rows.append(dict(id=k.id, existing_type="None", existing_code="", existing_size="", barrels=0, barrel_len_m=None, dist_m=None)); continue
    near["code"] = near["Code"].astype(str).str.replace(r"_\d+$", "", regex=True)
    g = near.sort_values("dist_m").groupby("code").agg(n=("Size", "size"), size=("Size", lambda s: ", ".join(sorted(set(map(str, s))))), L=("L", "mean"), dist=("dist_m", "min"), cells=("Num", "max"), W=("W", "max"), H=("H", "max")).sort_values("dist")
    best = g.iloc[0]; code = g.index[0]
    ex_rows.append(dict(id=k.id, existing_type="Culvert", existing_code=code, existing_size=best["size"], barrels=int(best["n"]), barrel_len_m=round(float(best["L"]), 1), dist_m=float(best["dist"]), cells=int(best["cells"]), W=float(best["W"]), H=float(best["H"])))
    for _, b in near.iterrows(): ex_near.append(dict(id=k.id, code=b["code"], size=b["Size"], num=b["Num"], W=b["W"], H=b["H"], L=b["L"], dist_m=b["dist_m"], geometry=b.geometry))
ex = pd.DataFrame(ex_rows)
# ---- the proposed box culverts: OHDS cells, HDS-5 headwater check, Block 6 cost build-up
K_ic, M_ic, c_ic, Y_ic, Ke, N_CULV, WALL = 0.026, 1.0, 0.0496, 0.53, 0.4, 0.015, 0.25
def normal_depth(Q, b, S, n=0.03):
    y = max((Q * n / (b * max(S, 1e-4) ** 0.5)) ** 0.6, 0.01)
    for _ in range(200):
        Aa = b * y; P = b + 2 * y; R = Aa / P; Qc = Aa * R ** (2 / 3) * max(S, 1e-4) ** 0.5 / n
        dQ = (max(S, 1e-4) ** 0.5 / n) * (b * R ** (2 / 3) + Aa * (2 / 3) * R ** (-1 / 3) * (b ** 2 / P ** 2))
        if abs(Qc - Q) < 1e-4: break
        y = max(y - (Qc - Q) / dQ, 1e-4)
    return y
def hw_ic(Q, B, D, N, S):
    Qb = Q / N; ratio = Qb / (B * D ** 1.5); yc = (Qb ** 2 / (9.81 * B ** 2)) ** (1 / 3); Hc = yc + (Qb / (B * yc)) ** 2 / 19.62
    return max(max(Hc / D + K_ic * ratio ** M_ic - 0.5 * S, c_ic * ratio ** 2 + Y_ic - 0.5 * S) * D, 0.0)
def hw_oc(Q, B, D, N, TW, L, S):
    Ab = B * D; Qb = Q / N; V = Qb / Ab; hv = V ** 2 / 19.62; R = Ab / (2 * (B + D)); hf = N_CULV ** 2 * V ** 2 * L / R ** (4 / 3)
    yc = (Qb ** 2 / (9.81 * B ** 2)) ** (1 / 3); Ho = max(TW, (yc + D) / 2); return max(Ho + hf + Ke * hv - S * L, 0.0)
RATES = dict(rebar=417.1, conc=106.9, blind=45.0, wp=2.0, abc=6.5, bbc=45.0, wbc=47.0, pc=0.45, tc=0.35, mark=4.0, rail=53.0, post=3.0, cng=0.2, removal=4.0)
def cost(N, B, D, L, G, existing):
    conc_m = N * ((B + WALL) * (D + 0.6) - B * D) + 0.8; conc = conc_m * L; rebar = 0.12 * conc
    items = dict(rebar=rebar * RATES["rebar"], concrete=conc * RATES["conc"], blinding=G * L * 0.1 * 1.1 * RATES["blind"], waterproofing=(2 * D * L + B * L) * RATES["wp"])
    PC = G * L * 1.1
    items.update(abc=PC * 0.1 * RATES["abc"], bbc=PC * 0.05 * RATES["bbc"], wbc=PC * 0.05 * RATES["wbc"], pavement=PC * RATES["pc"], tc=2 * PC * RATES["tc"], marking=G * 0.1 * 1.1 * RATES["mark"],
                 guardrail=2 * G * 1.1 * RATES["rail"], posts=math.ceil(2 * G * 1.1 / 4) * RATES["post"], cng=(L + 3) * G * 1.1 * RATES["cng"], removal=(G * L * (D + 0.5) * 1.1 * RATES["removal"]) if existing else 0.0)
    return sum(items.values()), conc, rebar, items
prop = []
for _, k in cr.iterrows():
    B = 4.0; D = float(k.rise_m); Q = k.Q200; L = k.corridor_m; S = max(k.slope, 0.0005)   # clear height = the full channel depth (R5)
    N = max(int(math.ceil(k.span_m / B)), 1); TW = normal_depth(Q, k.span_m, S) if Q > 0 else 0.0
    note = ""
    for _ in range(400):
        ic = hw_ic(Q, B, D, N, S) if Q > 0 else 0.0; oc = hw_oc(Q, B, D, N, TW, L, S) if Q > 0 else 0.0; hw = max(ic, oc)
        if hw <= 1.2 * D: break
        N += 1; note = "cells added for the headwater check"
    G = N * B + (N + 1) * WALL; e = ex[ex.id == k.id].iloc[0]; existing = e.existing_type != "None"
    total, conc, rebar, items = cost(N, B, D, L, G, existing)
    prop.append(dict(id=k.id, road=k.road, channel=k.channel, reach=k.reach, station_m=k.station_m, Q200=Q, channel_width_m=k.span_m, channel_depth_m=k.rise_m, cells=N, cell_width_m=B, cell_height_m=D,
                     overall_width_m=round(G, 1), length_m=L, slope=round(float(k.slope), 4), skew_deg=k.skew_deg, HW_m=round(hw, 2), HW_over_D=round(hw / D, 2), control="inlet" if ic >= oc else "outlet", tailwater_m=round(TW, 2), size="%d x %.0f x %.1f" % (N, B, D),
                     concrete_m3=round(conc), rebar_t=round(rebar, 1), cost_OMR=round(total), cost_mOMR=round(total / 1e6, 3), existing_type=e.existing_type, existing_size=e.existing_size, existing_barrels=e.barrels, existing_dist_m=e.dist_m, note=note,
                     end_short_m=(k.extended if "extended" in cr.columns and not pd.isna(k.extended) else ""), start_short_m=(k.start_short if "start_short" in cr.columns and not pd.isna(k.start_short) else "")))
pr = pd.DataFrame(prop)
cr.to_csv(os.path.join(OUT, "crossings.csv"), index=False); pr.to_csv(os.path.join(OUT, "culverts_proposed.csv"), index=False); ex.to_csv(os.path.join(OUT, "culverts_existing.csv"), index=False)
gp = os.path.join(OUT, "crossings.gpkg")
if os.path.exists(gp): os.remove(gp)
gpd.GeoDataFrame(pr.drop(columns=[]), geometry=[Point(x, y) for x, y in zip(cr.x, cr.y)], crs="EPSG:32640").to_file(gp, layer="crossings", driver="GPKG")
if ex_near: gpd.GeoDataFrame(pd.DataFrame(ex_near), crs="EPSG:32640").to_file(gp, layer="existing_barrels_near", driver="GPKG")
md = ["# Road crossings and box culverts (200-yr design %s)" % RUN, "", "crossings: %d (%s)" % (len(cr), ", ".join("%s %d" % kv for kv in cr.groupby("road").size().items())),
      "existing culverts within %.0f m: %d; proposed culverts: %d, cells %d, total cost %.1f mOMR" % (RADIUS, (ex.existing_type != "None").sum(), len(pr), pr.cells.sum(), pr.cost_OMR.sum() / 1e6), "",
      "| id | road | channel | reach | station | Q200 | channel W x D | proposed N x B x D | overall width | HW/D | existing (size, barrels, distance) | cost mOMR |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for _, p in pr.iterrows():
    md.append("| %d | %s | %s | %s | %.0f | %.0f | %.1f x %.1f | %s | %.1f | %.2f %s | %s | %.3f |" % (p.id, p.road, p.channel, p.reach, p.station_m, p.Q200, p.channel_width_m, p.channel_depth_m, p["size"], p.overall_width_m, p.HW_over_D, p.control, ("%s, %d barrels, %.0f m" % (p.existing_size, p.existing_barrels, p.existing_dist_m)) if p.existing_type != "None" else "none", p.cost_mOMR))
open(os.path.join(OUT, "culverts.md"), "w", encoding="utf-8").write("\n".join(md)); print("\n".join(md[:6])); print(pr[["id", "road", "channel", "Q200", "channel_width_m", "size", "HW_over_D", "existing_size", "cost_mOMR"]].to_string(index=False))
print("total proposed culvert cost: %.2f mOMR; notes: %s" % (pr.cost_OMR.sum() / 1e6, pr.note[pr.note != ""].count()))
