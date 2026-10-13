"""Step 23 - take the engineer's edited centrelines from the shapefile (Block = 4) and write the W5 build spec:
the W4 spec (corridor boundaries, point files, view insertions) with the NEW centreline vertices (deduplicated at 1 mm)
and, per feature, the `reverse` flag that keeps the approved direction (W4 order, reversed for corrections.json's list):
the new line is reversed when its first vertex is nearer the approved END than the approved START.
Outputs: civil3d/build_spec_w5.json, lines/Block4_lines_w5.csv (+ .gpkg), civil3d/qa/line_changes.csv (what changed).
A feature of the W4 spec missing from the file (or a new name) stops the script: nothing is deleted silently."""
import os, sys, json, csv, math
import geopandas as gpd
HERE = os.path.dirname(os.path.abspath(__file__)); W5 = os.path.dirname(HERE); W4 = os.path.join(os.path.dirname(W5), "W4")
sys.path.insert(0, os.path.join(W4, "scripts")); from config_w4 import LINES_SHP, kind_of, cls_of, gca_of
SPEC4 = json.load(open(os.path.join(W4, "civil3d", "build_spec.json")))
REVERSED = set(json.load(open(os.path.join(W5, "civil3d", "corrections.json")))["reversed"])
os.makedirs(os.path.join(W5, "lines"), exist_ok=True); os.makedirs(os.path.join(W5, "civil3d", "qa"), exist_ok=True)


def dedupe(pts, tol=0.001):
    out = [pts[0]]
    for q in pts[1:]:
        if abs(q["x"] - out[-1]["x"]) > tol or abs(q["y"] - out[-1]["y"]) > tol: out.append(q)
    return out


def dist(a, b): return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


g = gpd.read_file(LINES_SHP); b = g[g["Block"] == 4].copy()
assert b.crs.to_epsg() == 32640 and (b.geom_type == "LineString").all() and b["Name"].is_unique, "Block 4 lines: unique names, single-part lines, UTM 40N expected"
new = {r.Name: [{"x": round(x, 3), "y": round(y, 3)} for x, y in r.geometry.coords] for r in b.itertuples()}
old_names = [f["name"] for f in SPEC4]; missing = [n for n in old_names if n not in new]; added = [n for n in new if n not in old_names]
if missing or added: sys.exit("names differ from the W4 spec: missing %s, new %s -> nothing written" % (missing, added))
rows = []; spec = []
for f in SPEC4:
    name = f["name"]; old = f["alignment"]; pts = dedupe(new[name])
    appr_start, appr_end = (old[-1], old[0]) if name in REVERSED else (old[0], old[-1])          # the approved direction
    reverse = dist(pts[0], appr_start) > dist(pts[-1], appr_start)
    oriented = list(reversed(pts)) if reverse else pts
    length = sum(dist(oriented[i], oriented[i + 1]) for i in range(len(oriented) - 1))
    old_len = f["length_m"]
    changed = len(pts) != len(old) or any(dist(p, q) > 0.001 for p, q in zip(pts, old))
    rows.append({"name": name, "kind": f["kind"], "changed": changed, "reverse": reverse, "old_length_m": old_len, "new_length_m": round(length, 2), "d_length_m": round(length - old_len, 2),
                 "old_vertices": len(old), "new_vertices": len(pts), "start_moved_m": round(dist(oriented[0], appr_start), 2), "end_moved_m": round(dist(oriented[-1], appr_end), 2)})
    f2 = dict(f); f2["alignment"] = pts; f2["reverse"] = reverse; f2["length_m"] = round(length, 2); spec.append(f2)
json.dump(spec, open(os.path.join(W5, "civil3d", "build_spec_w5.json"), "w"), indent=0)
with open(os.path.join(W5, "civil3d", "qa", "line_changes.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
b = b.rename(columns={"Name": "name"}); b["kind"] = b["name"].map(kind_of); b["cls"] = b["name"].map(cls_of); b["gca"] = b["name"].map(gca_of); b["length_m"] = b.geometry.length.round(2)
b["reverse"] = b["name"].map({r["name"]: r["reverse"] for r in rows}); b["changed"] = b["name"].map({r["name"]: r["changed"] for r in rows})
b[["name", "kind", "cls", "gca", "length_m", "reverse", "changed", "geometry"]].to_file(os.path.join(W5, "lines", "Block4_lines_w5.gpkg"), layer="lines", driver="GPKG")
b.drop(columns="geometry")[["name", "kind", "cls", "gca", "length_m", "reverse", "changed"]].to_csv(os.path.join(W5, "lines", "Block4_lines_w5.csv"), index=False)
ch = [r for r in rows if r["changed"]]
print("%d features, %d changed, %d built reversed; shapefile %s" % (len(rows), len(ch), sum(r["reverse"] for r in rows), os.path.getmtime(LINES_SHP)))
for r in ch: print("  %-12s %-7s len %9.1f -> %9.1f (%+7.1f m)  vertices %3d -> %3d  start moved %6.1f m  end moved %6.1f m  reverse %s" % (r["name"], r["kind"], r["old_length_m"], r["new_length_m"], r["d_length_m"], r["old_vertices"], r["new_vertices"], r["start_moved_m"], r["end_moved_m"], r["reverse"]))
print("reverse flags:", sorted(r["name"] for r in rows if r["reverse"]))
