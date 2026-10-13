import ast
w = open("write_basin.py").read()
w = w.replace('"user_edited_20261005c"', '"user_edited_20261005d"')
old = '''USER_EDITS = dict(delete_reaches=["R151", "R170", "R199"], delete_junctions=["J210", "Outlet 13 Sw M CH 15"], redirect={"R169": "Outlet 9 FP CH 16"})'''
new = '''USER_EDITS = dict(delete_reaches=["R151", "R170", "R199", "R196"], delete_junctions=["J210", "Outlet 13 Sw M CH 15", "Outlet 11"], redirect={"R169": "Outlet 9 FP CH 16"}, delete_subbasins=["S238"])
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
    idx_ = new.index[(new.S == sn) & new.write_sub]
    for i in idx_: print("user edit: subbasin", sn, "removed, its ground joins", merge_into_neighbour(i))'''
assert old in w; w = w.replace(old, new, 1)

old = '''# prune junctions left without any inflow by the merges (their outgoing reach carries nothing)'''
new = r'''# ---------- rule (engineer 2026-10-05): no catchment below SMALL_FINAL km2, none enclosed by another ----------
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
# ---------- renaming (engineer 2026-10-05): outfalls O1.. west to east; other elements <GCA>-S/R/J<n> by global catchment ----------
GCA = "W:/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/06-WORKING/04-Hydraulic/05 Small Tasks/18 Channel Design/Hydraulic/Block 6/Report/Hydraulic Design of Stormwater Channels/Data/GCA RENN.shp"
DAMS_KEEP = {"Hawasinah 02", "Hawasinah 11", "Hawasinah EX", "Shafan 02", "Shafan 08", "Shafan 08 site", "Sarami 03", "Sarami 05", "Sakhin 04", "Sakhin 08"}
gca = gpd.read_file(GCA).to_crs("EPSG:32640"); gca = gca[gca.J_CA.notna() & (gca.J_CA != "N/A")].reset_index(drop=True)
gca["geometry"] = gca.geometry.buffer(0)
def prefix(name):
    n = re.sub(r"^(al|the)\s+", "", name.strip(), flags=re.I); return re.sub(r"[^A-Za-z]", "", n)[:3].upper()
gca["pre"] = gca.J_CA.map(prefix)
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
for jn, rn in b1_junc_ds.items():
    if rn and rn in b1_reach_ds: jnext[jn] = b1_reach_ds[rn]
for r in new.itertuples():
    if r.head_junction: jnext[r.head_junction] = r.junction
all_j = {j for j in (set(junc_xy) | set(jnext) | set(jnext.values())) if j and j != "None"}
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
for n, j in enumerate(terminal_j, 1): rename[j] = f"O{n}"
counters = {}
def nxt(pre, kind):
    counters[(pre, kind)] = counters.get((pre, kind), 0) + 1; return f"{pre}-{kind}{counters[(pre, kind)]}"
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
USER_EDITS = {k: ([ren(x) for x in v] if isinstance(v, list) else {ren(a): ren(b) for a, b in v.items()}) for k, v in USER_EDITS.items()}
# prune junctions left without any inflow by the merges (their outgoing reach carries nothing)'''
assert old in w; w = w.replace(old, new, 1)
w = w.replace('''    if name == "S16" and s16_add:''', '''    if name == rename.get("S16", "S16") and s16_add:''')
old2 = '''c = sqlite3.connect(dst)
if s16_add:'''
new2 = '''c = sqlite3.connect(dst)
for tbl, col in [("subbasin2d", "name"), ("outlet", "name"), ("longest_flowpath", "subbasin"), ("centroid", "subbasin"), ("centroidal_flowpath", "subbasin"), ("teneightyfive_flowpath", "subbasin"), ("subbasin_statistics", "subbasin_name"), ("reach2d", "name"), ("reach_statistics", "reach_name")]:
    for old_n, new_n in rename.items():
        c.execute(f"update {tbl} set {col}=? where {col}=?", (new_n, old_n))
if s16_add:'''
assert old2 in w; w = w.replace(old2, new2, 1)
w = w.replace('''    c.execute("update subbasin2d set GEOMETRY=?, area_sqkm=? where name='S16'", (wkb.dumps(g16), round(g16.area / 1e6, 4)))''',
              '''    c.execute("update subbasin2d set GEOMETRY=?, area_sqkm=? where name=?", (wkb.dumps(g16), round(g16.area / 1e6, 4), rename.get("S16", "S16")))''')
w = w.replace('''    g16 = wkb.loads(c.execute("select GEOMETRY from subbasin2d where name='S16'").fetchone()[0]).buffer(0)''',
              '''    g16 = wkb.loads(c.execute("select GEOMETRY from subbasin2d where name=?", (rename.get("S16", "S16"),)).fetchone()[0]).buffer(0)''')
open("write_basin.py", "w").write(w); ast.parse(w); print("write_basin patched")
