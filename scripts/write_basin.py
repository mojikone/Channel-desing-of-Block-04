"""Build Basin 2 = Basin 1 elements verbatim + delineated channel network below the dams.
usage: python write_basin.py <grid_folder> <hms_project_folder> [--install]
Writes Basin_2.basin, Basin_2.sqlite into <grid_folder>/out/hms/ and, with --install, copies them into the HMS project and registers Basin 2 in the .hms file.
"""
import re, sys, os, shutil, sqlite3, datetime, json
import numpy as np, pandas as pd, geopandas as gpd
from shapely import wkb
from shapely.geometry import Point
from pyproj import Transformer
N = sys.argv[1].rstrip("/\\") + "/"; HMS = sys.argv[2].rstrip("/\\") + "/"; INSTALL = "--install" in sys.argv
OUT = N + "out/hms/"; os.makedirs(OUT, exist_ok=True)
P = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydrology\SHP\temp\CH WALL for HMS channels"
now = datetime.datetime.now(); DATE = now.strftime("%d %B %Y").lstrip("0"); TIME = now.strftime("%H:%M:%S")
to_ll = Transformer.from_crs("EPSG:32640", "EPSG:4326", always_xy=True)

# ---------- Basin 1 ----------
txt = open(HMS + "Basin_1.basin", encoding="utf-8", errors="replace").read()
blocks = re.findall(r'^((Subbasin|Junction|Reach): (.+?)\n.*?^End:\n)', txt, re.S | re.M)
b1 = {name: (kind, body) for body, kind, name in blocks}
b1_junctions = {n for n, (k, b) in b1.items() if k == "Junction"}
def field(body, key):
    m = re.search(r'^\s*' + re.escape(key) + r': (.*)$', body, re.M); return m.group(1).strip() if m else None
SHAFAN08_SET = {"S22", "S23", "J17", "J18", "R15", "R16", "Shafan 08"}   # removed dam: replaced by the new delineation
b1 = {n: v for n, v in b1.items() if n not in SHAFAN08_SET}
b1_junctions = {n for n, (k, b) in b1.items() if k == "Junction"}
terminals = {n for n, (k, b) in b1.items() if k == "Junction" and (field(b, "Downstream") in (None, "", "None") or field(b, "Downstream") in SHAFAN08_SET)}
print("Basin 1 elements carried over:", len(b1), "| terminal junctions:", sorted(terminals))

# ---------- new links ----------
df = pd.read_csv(N + "out/links.csv"); df["reach"] = df.reach.fillna(""); df["head_junction"] = df.head_junction.fillna(""); df["ch_type"] = df.ch_type.fillna("")
B1N = b1_junctions
# a link is "inside Basin 1" if its water reaches a retained Basin 1 junction downstream (walk the link graph by names)
next_link = {r.head_junction: r.junction for r in df.itertuples() if r.head_junction}
def drains_to_b1(j):
    seen = set()
    while j and j not in seen:
        if j in B1N: return True
        seen.add(j); j = next_link.get(j)
    return False
inside = df.junction.map(drains_to_b1)
stub = (~inside) & (df.head_junction == "") & (df.area_km2 < 0.05)
print(f"headwater stubs < 0.05 km2 dropped: {stub.sum()} ({df[stub].area_km2.sum():.3f} km2)")
df = df[~stub].reset_index(drop=True); inside = df.junction.map(drains_to_b1)
print(f"links inside Basin 1 network dropped: {inside.sum()} ({df[inside].area_km2.sum():.1f} km2); channel-network links kept: {(~inside).sum()} ({df[~inside].area_km2.sum():.1f} km2)")
new = df[~inside].sort_values("area_km2", ascending=False).reset_index(drop=True)
# names: S101.., R101.., J101.. (junction names already J101+ from delineate), outlets keep names
new["S"] = [f"S{101+i}" for i in range(len(new))]
rk = 101; R = []
for r in new.itertuples():
    R.append(f"R{rk}" if r.head_junction else ""); rk += 1 if r.head_junction else 0
new["R"] = R
gp = gpd.read_file(N + "out/review.gpkg", layer="subbasins")[["label", "geometry"]]
new = new.merge(gp, on="label", how="left"); new = gpd.GeoDataFrame(new, geometry="geometry", crs="EPSG:32640")
from shapely.ops import unary_union
_c = sqlite3.connect(HMS + "Basin_1.sqlite")
b1_union = unary_union([wkb.loads(g).buffer(0) for g, n in _c.execute("select GEOMETRY, name from subbasin2d") if n in b1]); _c.close()
new["geometry"] = new.geometry.make_valid()
ov = new.geometry.intersection(b1_union).area / 1e6
new["geometry"] = new.geometry.difference(b1_union); new["area_km2"] = new.area_km2 - ov
print(f"overlap with retained Basin 1 polygons removed from new subbasins: {ov.sum():.2f} km2 on {(ov > 0.01).sum()} subbasins (max {ov.max():.2f})")
cxy = new.geometry.centroid
new["cx"] = [float(cxy.x.iloc[i]) if ov.iloc[i] > 0.01 else float(new["cx"].iloc[i]) for i in range(len(new))]
new["cy"] = [float(cxy.y.iloc[i]) if ov.iloc[i] > 0.01 else float(new["cy"].iloc[i]) for i in range(len(new))]
print(f"Basin 1 area carried over: {b1_union.area/1e6:.1f} km2 | new channel-network subbasins: {new.area_km2.sum():.1f} km2 | total: {b1_union.area/1e6 + new.area_km2.sum():.1f} km2")
nodes = json.load(open(N + "out/nodes.json")); W = nodes["W"]
import rasterio
with rasterio.open(N + "d8.tif") as s: tr = s.transform
cell_xy = lambda c: (tr.c + (c % W + 0.5) * tr.a, tr.f + (c // W + 0.5) * tr.e)
jcell = {v: int(k) for k, v in nodes["node_name"].items() if not k.startswith("(")}


# reach parameters by type (PLACEHOLDERS for channel sections — to be replaced by the design sections)
def reach_params(ch_type):
    if ch_type.startswith("FP"): return dict(n=0.035, b=15.0, z=2.0)
    if ch_type.startswith("Sw M"): return dict(n=0.035, b=8.0, z=2.0)
    if ch_type.startswith("Sw S"): return dict(n=0.035, b=4.0, z=2.0)
    return dict(n=0.1, b=100.0, z=5.0)  # natural wadi on the plain, Basin 1 style

# ---------- element blocks ----------
def sub_block(name, x, y, area, down, cn, ia, lag):
    lon, lat = to_ll.transform(x, y)
    return (f"Subbasin: {name}\n     Last Modified Date: {DATE}\n     Last Modified Time: {TIME}\n     Latitude Degrees:  {lat}\n     Longitude Degrees: {lon}\n"
            f"     Canvas X: {x}\n     Canvas Y: {y}\n     Area: {area:.3f}\n     Downstream: {down}\n\n     Discretization: None\n     File: Basin_2.sqlite\n\n"
            f"     Canopy: None\n     Allow Simultaneous Precip Et: No\n     Plant Uptake Method: None\n\n     Surface: None\n\n     LossRate: SCS\n     Percent Impervious Area: 0.0\n"
            f"     Curve Number: {cn:.1f}\n     Initial Abstraction: {ia:.2f}\n\n     Transform: SCS\n     Lag: {lag:.1f}\n     Unitgraph Type: STANDARD\n\n     Baseflow: None\nEnd:\n")
def junc_block(name, x, y, down):
    ds = "     Downstream: " + down + chr(10) if down else ""
    return "Junction: " + name + chr(10) + "     Last Modified Date: " + DATE + chr(10) + "     Last Modified Time: " + TIME + chr(10) + "     Canvas X: " + str(x) + chr(10) + "     Canvas Y: " + str(y) + chr(10) + ds + "End:" + chr(10)
def reach_block(name, x, y, fx, fy, down, length, slope, p):
    return (f"Reach: {name}\n     Last Modified Date: {DATE}\n     Last Modified Time: {TIME}\n     Canvas X: {x}\n     Canvas Y: {y}\n     From Canvas X: {fx}\n     From Canvas Y: {fy}\n     Downstream: {down}\n\n"
            f"     Route: Muskingum Cunge\n     Channel: Trapezoid\n     Length: {length:.2f}\n     Energy Slope: {slope:.5f}\n     Mannings n: {p['n']}\n     Bottom Width: {p['b']}\n     Side Slope: {p['z']}\n"
            f"     Initial Variable: Combined Inflow\n     Space-Time Method: Automatic DX and DT\n     Index Parameter Type: Index Celerity\n     Index Celerity: 1.524\n     Number Subreaches: 1\n"
            f"     Maximum Depth Iterations: 20\n     Maximum Route Step Iterations: 30\n     Channel Loss: None\nEnd:\n")

# RULE (2026-10-05): inside a wall-closed compartment, very small subbasins are merged into the compartment's main one.
# Compartment = links connected through junctions that are neither culverts, Basin 1 junctions nor sea outlets.
SMALL_KM2 = 0.5
culv = set(nodes.get("culvert_junctions", [])); term = set(new.junction[new.is_outlet]) | B1N
new = new.reset_index(drop=True)
parent = list(range(len(new))); 
def find(i):
    while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
    return i
by_head = {r.head_junction: i for i, r in new.iterrows() if r.head_junction}
for i, r in new.iterrows():
    j = r.junction
    if j in culv or j in term: continue
    if j in by_head: parent[find(i)] = find(by_head[j])          # downstream link through a plain confluence junction
    for k in new.index[new.junction == j]: parent[find(k)] = find(i)   # siblings at the same confluence
new["comp"] = [find(i) for i in range(len(new))]
merged = 0; log_m = []
for comp, grp in new.groupby("comp"):
    if len(grp) < 2: continue
    host = grp.area_km2.idxmax()
    for i, r in grp.iterrows():
        if i == host or r.area_km2 >= SMALL_KM2: continue
        h = new.loc[host]; a = h.area_km2 + r.area_km2
        new.loc[host, "CN"] = (h.CN * h.area_km2 + r.CN * r.area_km2) / a
        new.loc[host, "geometry"] = h.geometry.union(r.geometry); new.loc[host, "area_km2"] = a
        new.loc[i, "area_km2"] = 0.0; merged += 1; log_m.append((r.label, h.label))
new["Ia_mm"] = 0.2 * 25.4 * (1000 / new.CN - 10)
print(f"small subbasins (<{SMALL_KM2} km2) merged into their compartment's main subbasin: {merged}")
new["write_sub"] = new.area_km2 >= 0.001
# ---------- merge regions: closed red loops from the engineer's screenshots + his HMS merges (2026-10-05) ----------
REG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "georef", "merge_regions.gpkg")
s16_add = None
if os.path.exists(REG):
    regions = gpd.read_file(REG)
    next_link = {r.head_junction: r.junction for r in new.itertuples() if r.head_junction}
    def downstream_of(j, k):   # is junction k downstream of j?
        seen = set(); x = next_link.get(j)
        while x and x not in seen:
            if x == k: return True
            seen.add(x); x = next_link.get(x)
        return False
    written_union = unary_union(list(new[new.write_sub].geometry))
    nreg = 0
    for reg in regions.itertuples():
        inter = new.geometry.intersection(reg.geometry).area
        mem = new.index[(inter / new.geometry.area.replace(0, np.nan) >= 0.5) & new.write_sub].tolist()
        if reg.kind == "merge into Basin 1 S16":
            if mem:
                s16_add = dict(area=float(new.loc[mem, "area_km2"].sum()), cn=float((new.loc[mem, "CN"] * new.loc[mem, "area_km2"]).sum() / new.loc[mem, "area_km2"].sum()), geom=unary_union(list(new.loc[mem, "geometry"])), members=[int(m) for m in mem])
                new.loc[mem, "area_km2"] = 0.0; new.loc[mem, "write_sub"] = False
                print(f"region {reg.src} {reg.face}: {len(mem)} subbasins ({s16_add['area']:.2f} km2) merged into Basin 1 S16")
            continue
        if not mem: print(f"region {reg.src} {reg.face}: no member subbasin found"); continue
        # group members by exit: the member junction that is downstream of (or equal to) the others
        js = sorted(set(new.loc[mem, "junction"]))
        sinks = [j for j in js if not any(downstream_of(j, k) for k in js if k != j)]
        groups = {}
        for m in mem:
            jm = new.loc[m, "junction"]; sink = next((s_ for s_ in sinks if s_ == jm or downstream_of(jm, s_)), jm)
            groups.setdefault(sink, []).append(m)
        FORCE_OUTLET = {("img7", "1"): "J176", ("img7", "2"): "J176"}   # engineer 2026-10-05: S239 and S106 confluence at J176
        forced = FORCE_OUTLET.get((reg.src, str(reg.face)))
        if forced and forced in set(new.junction) | set(new.head_junction): groups = {forced: sum(groups.values(), [])}
        for sink, members in groups.items():
            host = max(members, key=lambda m: new.loc[m, "area_km2"])
            longest = max(members, key=lambda m: new.loc[m, "Lfp_m"])
            for col in ["Lfp_m", "L1085_m", "z10", "z85", "S1085", "S_used", "Lag_min"]: new.loc[host, col] = new.loc[longest, col]
            geom = unary_union(list(new.loc[members, "geometry"])); area = float(new.loc[members, "area_km2"].sum())
            cn = float((new.loc[members, "CN"] * new.loc[members, "area_km2"]).sum() / area)
            # unassigned ground inside the loop (white in HMS) joins the merged subbasin
            left = reg.geometry.difference(written_union).difference(b1_union)
            left = left.intersection(reg.geometry); extra = left.area / 1e6 if left.area / 1e6 > 0.01 and len(groups) == 1 else 0.0
            if extra: geom = unary_union([geom, left]); area += extra
            for m in members:
                if m != host: new.loc[m, "area_km2"] = 0.0; new.loc[m, "write_sub"] = False
            new.loc[host, "geometry"] = geom; new.loc[host, "area_km2"] = area; new.loc[host, "CN"] = cn; new.loc[host, "junction"] = sink
            nreg += 1
            print(f"region {reg.src} {reg.face}: {len(members)} subbasins -> one ({area:.2f} km2, +{extra:.2f} km2 unassigned) draining to {sink}")
    new["Ia_mm"] = 0.2 * 25.4 * (1000 / new.CN - 10)
    print("regions applied:", nreg)
# ---------- no gaps: slivers of the delineation that ended in no written subbasin join the adjacent new subbasin ----------
allp = gpd.read_file(N + "out/review.gpkg", layer="subbasins").geometry.buffer(0)
cover = unary_union(list(new[new.write_sub].geometry.buffer(0)) + [b1_union])
gaps = unary_union(list(allp)).difference(cover)
pieces = [g for g in (gaps.geoms if gaps.geom_type == "MultiPolygon" else [gaps]) if 1e3 < g.area < 2e6]
filled = 0; filled_area = 0.0
wn = new[new.write_sub]
for g in pieces:
    cand = wn[wn.geometry.buffer(0).intersects(g.buffer(12))]
    if len(cand) == 0: continue
    shared = cand.geometry.buffer(0).apply(lambda p: p.buffer(12).intersection(g).area)
    k = int(shared.idxmax()); new.loc[k, "geometry"] = unary_union([new.loc[k, "geometry"], g]); new.loc[k, "area_km2"] += g.area / 1e6
    filled += 1; filled_area += g.area / 1e6
print(f"gap slivers joined to the neighbouring subbasin: {filled} ({filled_area:.2f} km2)")
# ---------- holes inside a subbasin that no other polygon covers are filled; final polygons made single-part ----------
from shapely.geometry import Polygon as _Poly, MultiPolygon as _MPoly
wn_idx = list(new.index[new.write_sub]); nh = 0; np_ = 0
others_union = lambda i: unary_union([new.loc[k, "geometry"].buffer(0) for k in wn_idx if k != i] + [b1_union])
for i in wn_idx:
    g = new.loc[i, "geometry"].buffer(0); parts = list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
    holes = [ _Poly(r) for p in parts for r in p.interiors if _Poly(r).area < 2e6 ]
    if holes:
        ou = others_union(i)
        for h in holes:
            if h.intersection(ou).area < 0.1 * h.area:
                new.loc[i, "geometry"] = unary_union([new.loc[i, "geometry"], h]); new.loc[i, "area_km2"] += h.area / 1e6; nh += 1
for i in wn_idx:
    g = new.loc[i, "geometry"].buffer(0)
    if g.geom_type != "MultiPolygon" or len(g.geoms) < 2: continue
    parts = sorted(g.geoms, key=lambda p: -p.area); keep = parts[0]
    for p in parts[1:]:
        best = None
        for k in wn_idx:
            if k == i: continue
            sh = new.loc[k, "geometry"].buffer(0).buffer(12).intersection(p).area
            if sh > 0 and (best is None or sh > best[0]): best = (sh, k)
        if best:
            k = best[1]; new.loc[k, "geometry"] = unary_union([new.loc[k, "geometry"], p]); new.loc[k, "area_km2"] += p.area / 1e6
            new.loc[i, "area_km2"] -= p.area / 1e6; np_ += 1
        else: keep = unary_union([keep, p])
    new.loc[i, "geometry"] = keep
print(f"holes filled: {nh} | detached parts moved to the neighbour: {np_}")
multi = [new.loc[i, "S"] for i in wn_idx if new.loc[i, "geometry"].geom_type == "MultiPolygon" and len(new.loc[i, "geometry"].geoms) > 1]
print("still multi-part:", multi)
new["Ia_mm"] = 0.2 * 25.4 * (1000 / new.CN - 10)
bad = new[new.write_sub & (new.Lfp_m < 0.3 * np.sqrt(new.area_km2 * 1e6))]
if len(bad): print("WARNING flow path too short for area:", bad[["S", "area_km2", "Lfp_m", "Lag_min"]].round(1).to_dict("records"))
# ---------- name persistence: keep the names of the engineer-edited model where the polygon is the same ----------
UE = os.path.join(HMS.replace("Hydrology/HEC_HMS_Block_04/", ""), "Claude Block 04", "W2", "output", "hms", "user_edited_20261005d")
if os.path.exists(UE + "/Basin_2.sqlite"):
    _cu = sqlite3.connect(UE + "/Basin_2.sqlite"); ue = {n: wkb.loads(g).buffer(0) for g, n in _cu.execute("select GEOMETRY, name from subbasin2d")}; _cu.close()
    ue_txt = open(UE + "/Basin_2.basin", encoding="utf-8", errors="replace").read()
    ue_subs = set(re.findall(r'^Subbasin: (.+?)$', ue_txt, re.M)); ue = {n: g for n, g in ue.items() if n in ue_subs and n not in b1}
    prev_el = pd.read_csv(UE.replace("user_edited_20261005d", "") + "/Basin_2_new_elements.csv") if os.path.exists(UE.replace("user_edited_20261005d", "") + "/Basin_2_new_elements.csv") else None
    taken = set(); cand = []
    for i, r in new[new.write_sub].iterrows():
        g = r.geometry.buffer(0); best = None
        for n, ug in ue.items():
            ia = g.intersection(ug).area; f = ia / max(g.area, ug.area)
            if f >= 0.5 and (best is None or f > best[0]): best = (f, n)
        if best: cand.append((best[0], i, best[1]))
    names = {}
    for f, i, n in sorted(cand, reverse=True):
        if n not in taken and i not in names: names[i] = n; taken.add(n)
    snums = [int(n[1:]) for n in ue_subs if n[1:].isdigit()]; nxt_s = max(snums + [100]) + 1
    for i in new.index[new.write_sub]:
        if i not in names: names[i] = f"S{nxt_s}"; nxt_s += 1
    new["S"] = [names.get(i, f"S{i}") for i in new.index]
    print(f"subbasin names kept from the engineer's model: {len(taken)} of {int(new.write_sub.sum())}")
    if prev_el is not None:
        prev_r = {(r.head_junction, r.junction): r.R for r in prev_el.dropna(subset=["R"]).itertuples() if isinstance(r.R, str) and r.R}
        rnums = [int(v[1:]) for v in prev_r.values() if v[1:].isdigit()]; nxt_r = max(rnums + [100]) + 1; R2 = []
        for r in new.itertuples():
            if not r.head_junction: R2.append(""); continue
            key = (r.head_junction, r.junction)
            if key in prev_r and prev_r[key] not in R2: R2.append(prev_r[key])
            else: R2.append(f"R{nxt_r}"); nxt_r += 1
        new["R"] = R2
print(f"subbasins with <0.001 km2 after clipping (reach kept, subbasin omitted): {(~new.write_sub).sum()}")
# ---------- islands: a small subbasin almost entirely surrounded by one other new subbasin joins it ----------
isl = 0
wn = new[new.write_sub]
for i, r in wn.iterrows():
    if r.area_km2 >= 1.0: continue
    ring = r.geometry.buffer(15).difference(r.geometry.buffer(0)); best = None
    for k, q in wn.iterrows():
        if k == i: continue
        f = ring.intersection(q.geometry.buffer(0)).area / ring.area
        if f >= 0.6 and (best is None or f > best[0]): best = (f, k)
    if best:
        k = best[1]; a = new.loc[k, "area_km2"] + r.area_km2
        new.loc[k, "CN"] = (new.loc[k, "CN"] * new.loc[k, "area_km2"] + r.CN * r.area_km2) / a
        new.loc[k, "geometry"] = unary_union([new.loc[k, "geometry"], r.geometry]); new.loc[k, "area_km2"] = a
        new.loc[i, "area_km2"] = 0.0; new.loc[i, "write_sub"] = False; isl += 1
        print(f"island {r.S} ({r.area_km2:.2f} km2) merged into {new.loc[k, 'S']}")
new["Ia_mm"] = 0.2 * 25.4 * (1000 / new.CN - 10)
# ---------- the engineer's structural edits made in HMS (2026-10-05 10:46), re-applied by name on every rebuild ----------
USER_EDITS = dict(
    # reaches the engineer deleted in HMS, as (upstream junction, downstream junction) pairs
    delete_links=[("J128", "J150"), ("J210", "Outlet 9 FP CH 16"), ("J150", "Outlet 13 Sw M CH 15"), ("J115", "Outlet 11")],
    redirect_junction={"J210": "Outlet 9 FP CH 16"},          # everything that drained to J210 now goes straight to Outlet 9
    delete_junctions=["J210", "Outlet 13 Sw M CH 15", "Outlet 11"],
    delete_subbasins=["S238"])
def merge_into_neighbour(i, prefer_same_junction=True):
    """merge subbasin row i into the written neighbour sharing the longest boundary (same junction preferred)"""
    g = new.loc[i, "geometry"].buffer(0); best = None
    for k in new.index[new.write_sub]:
        if k == i: continue
        sh = new.loc[k, "geometry"].buffer(0).buffer(12).intersection(g).area
        if sh <= 0: continue
        score = sh * (3 if (prefer_same_junction and new.loc[k, "junction"] == new.loc[i, "junction"]) else 1)
        if best is None or score > best[0]: best = (score, k)
    if best is None: return None
    k = best[1]; a = new.loc[k, "area_km2"] + new.loc[i, "area_km2"]
    new.loc[k, "CN"] = (new.loc[k, "CN"] * new.loc[k, "area_km2"] + new.loc[i, "CN"] * new.loc[i, "area_km2"]) / a
    new.loc[k, "geometry"] = unary_union([new.loc[k, "geometry"], g]); new.loc[k, "area_km2"] = a
    new.loc[i, "area_km2"] = 0.0; new.loc[i, "write_sub"] = False
    return new.loc[k, "S"]
for sn in USER_EDITS["delete_subbasins"]:
    for i in new.index[(new.S == sn) & new.write_sub]: print("user edit: subbasin", sn, "removed, its ground joins", merge_into_neighbour(i))
for h, j in USER_EDITS["delete_links"]:
    idx_ = new.index[(new.head_junction == h) & (new.junction == j)]
    if len(idx_): new.loc[idx_, "head_junction"] = ""; new.loc[idx_, "R"] = ""; print(f"user edit: reach {h} -> {j} removed")
for old_j, new_j_ in USER_EDITS["redirect_junction"].items():
    idx_ = new.index[new.junction == old_j]
    if len(idx_): new.loc[idx_, "junction"] = new_j_; print(f"user edit: {len(idx_)} link(s) into {old_j} now drain to {new_j_}")
for jn in USER_EDITS["delete_junctions"]:
    idx_ = new.index[new.head_junction == jn]
    if len(idx_): new.loc[idx_, "head_junction"] = ""; new.loc[idx_, "R"] = ""
    left = new.index[(new.junction == jn) & new.write_sub]
    for i in left: print(f"user edit: subbasin {new.loc[i, 'S']} still drained to deleted {jn}; joined to", merge_into_neighbour(i))
    print("user edit: junction", jn, "removed")
# ---------- rule (engineer 2026-10-05): no catchment below SMALL_FINAL km2, none enclosed by another ----------
SMALL_FINAL = 1.0
for _ in range(20):
    wn_idx = list(new.index[new.write_sub]); done = True
    for i in wn_idx:
        if not new.loc[i, "write_sub"]: continue
        r = new.loc[i]; g = r.geometry.buffer(0)
        enclosed = False
        if r.area_km2 < 30:
            ring = g.buffer(15).difference(g)
            for k in wn_idx:
                if k != i and new.loc[k, "write_sub"] and ring.intersection(new.loc[k, "geometry"].buffer(0)).area >= 0.9 * ring.area: enclosed = True; break
        if r.area_km2 < SMALL_FINAL or enclosed:
            host = merge_into_neighbour(i)
            if host: print(f"{'enclosed' if enclosed else 'small'} subbasin {r.S} ({r.area_km2:.2f} km2) merged into {host}"); done = False
    if done: break
new["Ia_mm"] = 0.2 * 25.4 * (1000 / new.CN - 10)
# prune junctions left without any inflow by the merges (their outgoing reach carries nothing)
for _ in range(10):
    inflow = {}
    for r in new.itertuples():
        if r.write_sub: inflow[r.junction] = inflow.get(r.junction, 0) + 1
        if r.head_junction: inflow[r.junction] = inflow.get(r.junction, 0) + 1
    dead = [j for j in set(new.head_junction) if j and j not in B1N and inflow.get(j, 0) == 0]
    if not dead: break
    for j in dead:
        idx_ = new.index[new.head_junction == j]
        new.loc[idx_, "head_junction"] = ""; new.loc[idx_, "R"] = ""
    print("junctions pruned (no inflow after merging):", dead)
# ---------- renaming (engineer 2026-10-05): outfalls O1.. west to east; other elements <GCA>-S/R/J<n> by global catchment ----------
GCA = "W:/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/06-WORKING/04-Hydraulic/05 Small Tasks/18 Channel Design/Hydraulic/Block 6/Report/Hydraulic Design of Stormwater Channels/Data/GCA RENN.shp"
DAMS_KEEP = {"Hawasinah 02", "Hawasinah 11", "Hawasinah EX", "Shafan 02", "Shafan 08", "Shafan 08 site", "Sarami 03", "Sarami 05", "Sakhin 04", "Sakhin 08"}
gca = gpd.read_file(GCA).to_crs("EPSG:32640"); gca = gca[gca.J_CA.notna() & (gca.J_CA != "N/A")].reset_index(drop=True)
gca["geometry"] = gca.geometry.buffer(0)
def prefix(name):
    n = re.sub(r"^(al|the)\s+", "", name.strip(), flags=re.I); return re.sub(r"[^A-Za-z]", "", n)[:3].upper()
gca["pre"] = gca.J_CA.map(prefix)
PREFIX_OVERRIDE = {"MAS": "HAW"}     # engineer 2026-10-05: the east-edge elements that the shapefile puts in Mashin belong to Al Hawasinah
gca["pre"] = gca.pre.map(lambda p: PREFIX_OVERRIDE.get(p, p))
def gca_of_point(x, y):
    p = Point(x, y); hit = gca[gca.contains(p)]
    if len(hit): return hit.iloc[0].pre
    return gca.iloc[int(gca.distance(p).idxmin())].pre
def gca_of_poly(g):
    inter = gca.geometry.intersection(g.buffer(0)).area
    return gca.loc[int(inter.idxmax()), "pre"] if inter.max() > 0 else gca_of_point(g.centroid.x, g.centroid.y)
b1_junc_xy = {n: (float(field(b, "Canvas X")), float(field(b, "Canvas Y"))) for n, (k, b) in b1.items() if k == "Junction"}
b1_sub_xy = {n: (float(field(b, "Canvas X")), float(field(b, "Canvas Y"))) for n, (k, b) in b1.items() if k == "Subbasin"}
b1_reach_ds = {n: field(b, "Downstream") for n, (k, b) in b1.items() if k == "Reach"}
b1_junc_ds = {n: field(b, "Downstream") for n, (k, b) in b1.items() if k == "Junction"}
wn = new[new.write_sub]
junc_xy = dict(b1_junc_xy)
for jn in set(new.junction) | set(new.head_junction):
    if not jn or jn in junc_xy: continue
    if jn in jcell: junc_xy[jn] = cell_xy(jcell[jn])
    else:
        rr = new[new.junction == jn]
        if len(rr): junc_xy[jn] = (float(rr.iloc[0].outlet_x), float(rr.iloc[0].outlet_y))
jnext = {}
for jn, dn in b1_junc_ds.items():
    if dn in b1_reach_ds: jnext[jn] = b1_reach_ds[dn]
    elif dn and dn != "None": jnext[jn] = dn
for r in new.itertuples():
    if r.head_junction: jnext[r.head_junction] = r.junction
live = set(b1_junc_xy) | set(new.junction[new.write_sub]) | set(new.head_junction[new.head_junction != ""]) | set(new.junction[new.head_junction != ""])
all_j = {j for j in (live | {jnext[j] for j in live if j in jnext}) if j and j != "None"} - set(USER_EDITS["delete_junctions"])
terminal_j = sorted([j for j in all_j if j not in jnext and j not in DAMS_KEEP], key=lambda j: junc_xy.get(j, (0, 0))[0])
rank = {}
def jrank(j, depth=0):
    if j in rank: return rank[j]
    ups = [u for u, d in jnext.items() if d == j]
    rank[j] = 0 if (not ups or depth > 500) else 1 + max(jrank(u, depth + 1) for u in ups)
    return rank[j]
for j in all_j: jrank(j)
gca_j = {j: gca_of_point(*junc_xy[j]) for j in all_j if j in junc_xy}
rename = {}
counters = {}
def nxt(pre, kind):
    counters[(pre, kind)] = counters.get((pre, kind), 0) + 1; return f"{pre}-{kind}{counters[(pre, kind)]}"
for j in terminal_j: rename[j] = nxt(gca_j.get(j, "OTH"), "O")      # outfalls: <GCA>-O<n>, numbered west to east within the catchment
for j in sorted([j for j in all_j if j not in rename and j not in DAMS_KEEP], key=lambda j: (gca_j.get(j, "OTH"), rank[j], junc_xy.get(j, (0, 0))[0])):
    rename[j] = nxt(gca_j.get(j, "OTH"), "J")
sub_items = [(n, gca_of_point(*b1_sub_xy[n]), rank.get(field(b1[n][1], "Downstream"), 0), float(field(b1[n][1], "Area"))) for n in b1_sub_xy]
sub_items += [(r.S, gca_of_poly(r.geometry), rank.get(r.junction, 0), r.area_km2) for r in wn.itertuples()]
for n, pre, rk, a in sorted(sub_items, key=lambda t: (t[1], t[2], -t[3])): rename[n] = nxt(pre, "S")
reach_items = [(n, gca_j.get(b1_reach_ds[n], "OTH"), rank.get(b1_reach_ds[n], 0)) for n in b1_reach_ds if b1_reach_ds[n]]
reach_items += [(r.R, gca_j.get(r.junction, "OTH"), rank.get(r.head_junction, 0)) for r in new.itertuples() if r.head_junction and r.R]
for n, pre, rk in sorted(reach_items, key=lambda t: (t[1], t[2])): rename[n] = nxt(pre, "R")
ren = lambda n: rename.get(n, n)
pd.DataFrame([dict(old=k, new=v) for k, v in rename.items()]).to_csv(OUT + "Basin_2_rename_map.csv", index=False)
print(f"renamed: {len(rename)} elements | outfalls: {len(terminal_j)} | prefixes used: {sorted(set(v.split('-')[0] for v in rename.values() if '-' in v))}")
new["S"] = new.S.map(ren); new["R"] = new.R.map(lambda x: ren(x) if x else x)
new["junction"] = new.junction.map(ren); new["head_junction"] = new.head_junction.map(lambda x: ren(x) if x else x)
jcell = {ren(k): v for k, v in jcell.items()}
b1r = {}
for n, (kind, body) in b1.items():
    body2 = re.sub(r"^(" + kind + r": ).*$", lambda m: m.group(1) + ren(n), body, count=1, flags=re.M)
    body2 = re.sub(r"^(\s*Downstream: )(.*)$", lambda m: m.group(1) + ren(m.group(2).strip()), body2, flags=re.M)
    b1r[ren(n)] = (kind, body2)
b1 = b1r; b1_junctions = {ren(j) for j in b1_junctions}; B1N = {ren(j) for j in B1N}; terminals = {ren(j) for j in terminals}
# downstream of each junction = the reach whose head is that junction
head_reach = {r.head_junction: r.R for r in new.itertuples() if r.head_junction}
out = []
# Basin 1 blocks verbatim, except: sqlite file name, terminal junctions now flow into the new reaches
for name, (kind, body) in b1.items():
    b = body.replace("Basin_1.sqlite", "Basin_2.sqlite")
    if name == rename.get("S16", "S16") and s16_add:
        a0 = float(field(b, "Area")); cn0 = float(field(b, "Curve Number")); a1 = a0 + s16_add["area"]; cn1 = (cn0 * a0 + s16_add["cn"] * s16_add["area"]) / a1
        b = re.sub(r'^(\s*Area: ).*$', lambda m: m.group(1) + f"{a1:.3f}", b, flags=re.M)
        b = re.sub(r'^(\s*Curve Number: ).*$', lambda m: m.group(1) + f"{cn1:.1f}", b, flags=re.M)
        b = re.sub(r'^(\s*Initial Abstraction: ).*$', lambda m: m.group(1) + f"{0.2*25.4*(1000/cn1-10):.2f}", b, flags=re.M)
        print(f"S16: area {a0:.3f} -> {a1:.3f} km2, CN {cn0:.1f} -> {cn1:.1f}")
    if kind == "Junction" and name in terminals and name in head_reach:
        if re.search(r'^\s*Downstream: ', b, re.M):
            b = re.sub(r'^(\s*Downstream: ).*$', lambda m: m.group(1) + head_reach[name], b, flags=re.M)
        else:
            b = b.replace("End:", "     Downstream: " + head_reach[name] + chr(10) + "End:")
    out.append(b)
# new junctions
new_j = sorted(({r.junction for r in new.itertuples() if r.write_sub or r.head_junction} | {r.head_junction for r in new.itertuples() if r.head_junction}) - B1N - set(USER_EDITS["delete_junctions"]))
for jn in new_j:
    c = jcell.get(jn)
    if c is None:  # outlet junction: at the link's outlet cell
        rr = new[new.junction == jn].iloc[0]; x, y = rr.outlet_x, rr.outlet_y
    else: x, y = cell_xy(c)
    out.append(junc_block(jn, x, y, head_reach.get(jn)))
# new subbasins + reaches
rows_sql = []
for r in new.itertuples():
    if r.write_sub: out.append(sub_block(r.S, r.cx, r.cy, r.area_km2, r.junction, r.CN, r.Ia_mm, r.Lag_min))
    if r.head_junction:
        hx, hy = cell_xy(jcell[r.head_junction]); dx, dy = (cell_xy(jcell[r.junction]) if r.junction in jcell else (r.outlet_x, r.outlet_y))
        slope = r.reach_slope if (np.isfinite(r.reach_slope) and r.reach_slope > 0.0005) else 0.0005
        out.append(reach_block(r.R, dx, dy, hx, hy, r.junction, r.reach_len_m, slope, reach_params(r.ch_type)))

# header + tail from Basin 1
header = re.search(r'^Basin: Basin 1\n.*?^End:\n', txt, re.S | re.M).group(0).replace("Basin: Basin 1", "Basin: Basin 2")
header = re.sub(r'Last Modified Date: .*', f"Last Modified Date: {DATE}", header); header = re.sub(r'Last Modified Time: .*', f"Last Modified Time: {TIME}", header)
tail = txt[txt.index("Basin Layer Properties:"):]
tail = tail[:tail.index("Computation Point:")] if "Computation Point:" in tail else tail
tail = tail.replace("Basin_1.sqlite", "Basin_2.sqlite")
tail = tail.replace(r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydrology\SHP\for HMS\1\Wall.shp", P + r"\WALL.shp").replace("Display name: Wall.shp", "Display name: WALL.shp")
tail = tail.replace(r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydrology\SHP\for HMS\1\Burn.shp", P + r"\CH.shp").replace("Display name: Burn.shp", "Display name: CH.shp")
tail = re.sub(r'Properties Filename: maps\\[^\n]*\n', '', tail)  # drop display-property files that belong to Basin 1
basin_txt = header + "\n" + "\n".join(out) + "\n" + tail
open(OUT + "Basin_2.basin", "w", encoding="utf-8", newline="\n").write(basin_txt)
print("Basin_2.basin written:", len(out), "element blocks (", len(b1), "from Basin 1 +", len(out) - len(b1), "new )")

# ---------- Basin_2.sqlite: copy Basin 1 and add new subbasin polygons / stats ----------
dst = OUT + "Basin_2.sqlite"; shutil.copyfile(HMS + "Basin_1.sqlite", dst)
c = sqlite3.connect(dst)
for tbl, col in [("subbasin2d", "name"), ("outlet", "name"), ("longest_flowpath", "subbasin"), ("centroid", "subbasin"), ("centroidal_flowpath", "subbasin"), ("teneightyfive_flowpath", "subbasin"), ("subbasin_statistics", "subbasin_name"), ("reach2d", "name"), ("reach_statistics", "reach_name")]:
    for old_n, new_n in rename.items():
        c.execute(f"update {tbl} set {col}=? where {col}=?", (new_n, old_n))
if s16_add:
    from shapely.geometry import MultiPolygon as _MP
    g16 = wkb.loads(c.execute("select GEOMETRY from subbasin2d where name=?", (rename.get("S16", "S16"),)).fetchone()[0]).buffer(0)
    g16 = unary_union([g16, s16_add["geom"]]); g16 = g16 if g16.geom_type == "MultiPolygon" else _MP([g16])
    c.execute("update subbasin2d set GEOMETRY=?, area_sqkm=? where name=?", (wkb.dumps(g16), round(g16.area / 1e6, 4), rename.get("S16", "S16")))
lfp = gpd.read_file(N + "out/review.gpkg", layer="longest_flowpath").set_index("sub")
for r in new.itertuples():
    if not r.write_sub: continue
    geom = r.geometry
    from shapely.geometry import MultiPolygon
    mp = geom if geom.geom_type == "MultiPolygon" else MultiPolygon([geom])
    lon, lat = to_ll.transform(r.cx, r.cy)
    c.execute("insert into subbasin2d (GEOMETRY,name,centroid_x,centroid_y,area_sqkm,latitude,longitude,basinid) values (?,?,?,?,?,?,?,?)", (wkb.dumps(mp), r.S, r.cx, r.cy, round(r.area_km2, 4), lat, lon, 2))
    c.execute("insert into centroid (GEOMETRY,subbasin) values (?,?)", (wkb.dumps(Point(r.cx, r.cy, 0.0)), r.S))
    c.execute("insert into outlet (GEOMETRY,name) values (?,?)", (wkb.dumps(Point(r.outlet_x, r.outlet_y, 0.0)), r.S))
    # original link label -> flowpath layer keyed by delineate's sub name
    key = df.loc[df.label == r.label, "sub"].iloc[0]
    if key in lfp.index:
        c.execute("insert into longest_flowpath (GEOMETRY,subbasin) values (?,?)", (wkb.dumps(lfp.loc[key, "geometry"]), r.S))
    c.execute("insert into subbasin_statistics (subbasin_name,longest_length,longest_slope,centroidal_length,centroidal_slope,[10_85_length],[10_85_slope],basin_slope,basin_relief,elongation_ratio,relief_ratio,drainage_density,length_units) values (?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (r.S, str(r.Lfp_m), "", "", "", str(r.L1085_m), str(r.S1085), "", "", "", "", "", "m"))
c.commit(); c.close(); print("Basin_2.sqlite written with", len(new), "new subbasins")
new.drop(columns="geometry").to_csv(OUT + "Basin_2_new_elements.csv", index=False)
rev = OUT + "Basin_2_review.gpkg"
cols = ["S", "R", "head_junction", "junction", "area_km2", "CN", "Ia_mm", "Lag_min", "Lfp_m", "L1085_m", "S1085", "reach_len_m", "reach_slope", "ch_type", "ch_feat", "is_outlet", "write_sub"]
new[new.write_sub][cols + ["geometry"]].to_file(rev, layer="subbasins_new", driver="GPKG")
lk = gpd.read_file(N + "out/review.gpkg", layer="links")[["sub", "geometry"]].merge(df[["sub", "label"]], on="sub").merge(new[["label"] + cols], on="label")
lk[lk.R != ""][["S", "R", "head_junction", "junction", "reach_len_m", "reach_slope", "ch_type", "ch_feat", "geometry"]].to_file(rev, layer="reaches_new", driver="GPKG")
lk[["S", "junction", "ch_type", "ch_feat", "geometry"]].to_file(rev, layer="stream_links_new", driver="GPKG")
jpts = [dict(name=jn, geometry=Point(*cell_xy(jcell[jn])), kind="junction") for jn in new_j if jn in jcell]
jpts += [dict(name=jn, geometry=Point(new[new.junction == jn].iloc[0].outlet_x, new[new.junction == jn].iloc[0].outlet_y), kind="sea outlet") for jn in new_j if jn not in jcell]
jpts += [dict(name=n, geometry=Point(float(field(b, "Canvas X")), float(field(b, "Canvas Y"))), kind="Basin 1 junction") for n, (k, b) in b1.items() if k == "Junction"]
if jpts: gpd.GeoDataFrame(jpts, geometry="geometry", crs="EPSG:32640").to_file(rev, layer="junctions", driver="GPKG")
else: print("WARNING: no junction points for the review layer")
_c = sqlite3.connect(HMS + "Basin_1.sqlite")
b1poly = gpd.GeoDataFrame([dict(name=ren(n), geometry=wkb.loads(g)) for g, n in _c.execute("select GEOMETRY, name from subbasin2d") if ren(n) in b1], geometry="geometry", crs="EPSG:32640"); _c.close()
b1poly.to_file(rev, layer="subbasins_basin1_carried_over", driver="GPKG")
print("review GeoPackage:", rev)

if INSTALL:
    bk = HMS + f"_backup_before_basin2_{now:%Y%m%d_%H%M%S}/"; os.makedirs(bk, exist_ok=True)
    for f in ["HEC_HMS_Block_04.hms"]: shutil.copy2(HMS + f, bk)
    for f in ["Basin_2.basin", "Basin_2.sqlite"]: shutil.copy2(OUT + f, HMS + f)
    hms = open(HMS + "HEC_HMS_Block_04.hms", encoding="utf-8").read()
    if "Basin: Basin 2" not in hms:
        blk = f"Basin: Basin 2\n     Filename: Basin_2.basin\n     Description: Basin 1 dam catchments + Block 4 channel network (CH/WALL reconditioning)\n     Last Modified Date: {DATE}\n     Last Modified Time: {TIME}\nEnd:\n\n"
        i = hms.index("Control: Control 1"); hms = hms[:i] + blk + hms[i:]
        open(HMS + "HEC_HMS_Block_04.hms", "w", encoding="utf-8", newline="\n").write(hms)
    print("installed into HMS project; .hms backup in", bk)
