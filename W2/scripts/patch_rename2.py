import ast, re
w = open("write_basin.py").read()
lines = w.split("\n")
# --- 1. replace the USER_EDITS block (from its definition up to the small-catchment rule) with a structural version
i0 = next(i for i, l in enumerate(lines) if l.startswith("USER_EDITS = dict("))
i1 = next(i for i, l in enumerate(lines) if l.startswith("# ---------- rule (engineer 2026-10-05): no catchment below"))
block = '''USER_EDITS = dict(
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
    print("user edit: junction", jn, "removed")'''
lines[i0:i1] = block.split("\n")
w = "\n".join(lines)
# --- 2. move the prune loop before the renaming block, drop the post-rename USER_EDITS remap
m = re.search(r"# prune junctions left without any inflow by the merges.*?print\(\"junctions pruned \(no inflow after merging\):\", dead\)\n", w, re.S)
prune = m.group(0); w = w.replace(prune, "", 1)
w = w.replace('''USER_EDITS = {k: ([ren(x) for x in v] if isinstance(v, list) else {ren(a): ren(b) for a, b in v.items()}) for k, v in USER_EDITS.items()}\n''', "")
w = w.replace("# ---------- renaming (engineer 2026-10-05): outfalls O1.. west to east; other elements <GCA>-S/R/J<n> by global catchment ----------",
              prune + "# ---------- renaming (engineer 2026-10-05): outfalls O1.. west to east; other elements <GCA>-S/R/J<n> by global catchment ----------", 1)
# --- 3. junction graph: direct junction->junction links in Basin 1, only live elements
old = '''jnext = {}
for jn, rn in b1_junc_ds.items():
    if rn and rn in b1_reach_ds: jnext[jn] = b1_reach_ds[rn]
for r in new.itertuples():
    if r.head_junction: jnext[r.head_junction] = r.junction
all_j = {j for j in (set(junc_xy) | set(jnext) | set(jnext.values())) if j and j != "None"}'''
new = '''jnext = {}
for jn, dn in b1_junc_ds.items():
    if dn in b1_reach_ds: jnext[jn] = b1_reach_ds[dn]
    elif dn and dn != "None": jnext[jn] = dn
for r in new.itertuples():
    if r.head_junction: jnext[r.head_junction] = r.junction
live = set(b1_junc_xy) | set(new.junction[new.write_sub]) | set(new.head_junction[new.head_junction != ""]) | set(new.junction[new.head_junction != ""])
all_j = {j for j in (live | {jnext[j] for j in live if j in jnext}) if j and j != "None"} - set(USER_EDITS["delete_junctions"])'''
assert old in w; w = w.replace(old, new, 1)
# --- 4. review export: guard empty junction list
w = w.replace('''gpd.GeoDataFrame(jpts, crs="EPSG:32640").to_file(rev, layer="junctions", driver="GPKG")''',
              '''if jpts: gpd.GeoDataFrame(jpts, geometry="geometry", crs="EPSG:32640").to_file(rev, layer="junctions", driver="GPKG")
else: print("WARNING: no junction points for the review layer")''')
open("write_basin.py", "w").write(w); ast.parse(w); print("write_basin patched (structural user edits, prune before rename, live junction graph)")
