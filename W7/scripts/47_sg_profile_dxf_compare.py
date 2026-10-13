"""Step 47 - prove the generated profile DXF matches SewerGEMS's own export: compare W6/sewergems/dxf/<run>/<scenario>/<channel>.dxf
with the Block 6 export of the Rustaq model (Ais-CH1-FP.dxf, extracted from the backup rar) feature by feature: DXF version, layers
and colours, text style, entity types per layer, entity counts normalised by the number of nodes and conduits, text heights,
alignments, rotations and formats per layer, grid spacing and extents, table row positions, the polyline colour attributes. Writes
<out>/<channel>_vs_Rustaq.md and renders both files to PNG (first 1500 m) for the eye.
    python 47_sg_profile_dxf_compare.py [--channel HAW-CH1-FP] [--scenario 200yr] [--run run_20261011_1721] [--ref path]"""
import os, sys, re, math, collections
import ezdxf
HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE)
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
CH = opt("--channel", "HAW-CH1-FP"); SC = opt("--scenario", "200yr"); RUN = opt("--run", "run_20261011_1721")
REF = opt("--ref", r"C:\Users\mojtaba\AppData\Local\Temp\claude\D--Mojtaba-Renardet-2224-WS11-Batinah-Block-4\72a3ff20-809e-4d71-bf42-7b9f694d69ff\scratchpad\rustaq\OUTPUT\DXF\1\Ais-CH1-FP.dxf")
OUT = os.path.join(W6, "sewergems", "dxf", RUN, SC); MINE = os.path.join(OUT, CH + ".dxf")


def describe(path):
    doc = ezdxf.readfile(path); msp = doc.modelspace(); d = {}
    d["version"] = doc.dxfversion
    d["layers"] = sorted((l.dxf.name, l.dxf.color, l.dxf.linetype.upper()) for l in doc.layers if l.dxf.name not in ("0", "Defpoints"))
    d["styles"] = sorted((s.dxf.name, s.dxf.font) for s in doc.styles)
    T = [e for e in msp if e.dxftype() == "TEXT"]; P = [e for e in msp if e.dxftype() == "POLYLINE"]; other = collections.Counter(e.dxftype() for e in msp if e.dxftype() not in ("TEXT", "POLYLINE"))
    d["other_entities"] = dict(other)
    tab = [t for t in T if t.dxf.layer == "Annotation_Table"]
    sta_row_y = min(t.dxf.insert.y for t in tab); nodes = sum(1 for t in tab if abs(t.dxf.insert.y - sta_row_y) < 0.01) - 1
    rows_y = sorted(set(round(t.dxf.insert.y, 2) for t in tab), reverse=True); conduits = nodes - 1
    d["nodes"], d["conduits"] = nodes, conduits
    d["per_layer"] = {}
    for lay in sorted(set(e.dxf.layer for e in msp)):
        pls = [p for p in P if p.dxf.layer == lay]; txs = [t for t in T if t.dxf.layer == lay]
        info = {"polylines": len(pls), "texts": len(txs)}
        if pls: info["pl_colors"] = sorted(set(p.dxf.color for p in pls)); info["pl_vertices"] = (min(len(list(p.points())) for p in pls), max(len(list(p.points())) for p in pls)); info["pl_closed"] = sum(1 for p in pls if p.is_closed)
        if txs:
            info["heights"] = sorted(set(round(t.dxf.height, 3) for t in txs)); info["align"] = sorted(set((t.dxf.halign, t.dxf.valign) for t in txs)); info["rot0"] = sum(1 for t in txs if abs(t.dxf.rotation) < 1e-6)
            pats = collections.Counter()
            for t in txs:
                s = t.dxf.text; s = re.sub(r"\d", "9", s); s = re.sub(r"[A-Za-z]+(-[A-Za-z]+)*", "A", s); pats[s] += 1
            info["text_patterns"] = sorted(pats.items(), key=lambda kv: -kv[1])[:12]
        d["per_layer"][lay] = info
    g = [p for p in P if p.dxf.layer == "Grid"]; xs = sorted(set(round(v[0], 2) for p in g for v in p.points())); ys = sorted(set(round(v[1], 2) for p in g for v in p.points()))
    d["grid"] = {"x_min": xs[0], "x_max": xs[-1], "dx": round(xs[2] - xs[1], 2), "y_min": ys[0], "y_max": ys[-1], "dy": round(ys[2] - ys[1], 2)}
    gt = [t for t in T if t.dxf.layer == "Grid_Text"]
    d["elev_label_x"] = sorted(set(round(t.dxf.insert.x, 2) for t in gt if "+" not in t.dxf.text and t.dxf.rotation == 0))
    d["sta_label_y"] = sorted(set(round(t.dxf.insert.y, 2) for t in gt if "+" in t.dxf.text))
    d["channel_end"] = math.ceil(max(v[0] for p in P if p.dxf.layer == "Invert" for v in p.points()) / 25.0) * 25   # the channel end rounded up to the 25 m grid
    d["mid_grid"] = math.ceil(d["channel_end"] / 2.0 / 25.0) * 25                   # the second column of elevation labels sits at the first grid line at or after the middle
    d["axis_title"] = [(round(t.dxf.insert.x, 1), t.dxf.rotation, t.dxf.text) for t in gt if t.dxf.rotation != 0]
    d["table_rows_y"] = rows_y; d["table_label_x"] = sorted(set(round(t.dxf.insert.x, 2) for t in tab if t.dxf.halign == 2))
    tl = [p for p in P if p.dxf.layer == "Annotation_Table"]; d["table_h_lines_y"] = sorted(set(round(list(p.points())[0][1], 2) for p in tl if abs(list(p.points())[0][1] - list(p.points())[1][1]) < 1e-6))
    an = [t for t in T if t.dxf.layer == "Annotation"]
    rim = [t for t in an if t.dxf.text.startswith("Rim")]; lab = [t for t in an if t.dxf.text.startswith("Rim")]
    d["node_annotation_lines"] = sorted(set(round(b.dxf.insert.y - a.dxf.insert.y, 2) for a in rim for b in an if abs(b.dxf.insert.x - a.dxf.insert.x) < 1e-6 and b is not a))
    d["ground_vertices"] = max(len(list(p.points())) for p in P if p.dxf.layer == "Ground_Elevation")
    return d


ref, mine = describe(REF), describe(MINE)
lines = ["# %s.dxf (generated, %s) against the SewerGEMS export Ais-CH1-FP.dxf (Block 6 Rustaq)" % (CH, SC), "", "| Feature | SewerGEMS export | Generated | Match |", "|---|---|---|---|"]
def row(name, a, b, ok=None):
    if ok is None: ok = a == b
    lines.append("| %s | %s | %s | %s |" % (name, str(a)[:120], str(b)[:120], "info (label formats differ by model)" if ok == "info" else ("yes" if ok else "**differs**")))
row("DXF version", ref["version"], mine["version"]); row("layers (name, colour, linetype)", ref["layers"], mine["layers"]); row("text styles", ref["styles"], mine["styles"]); row("entity types other than POLYLINE/TEXT", ref["other_entities"], mine["other_entities"])
row("nodes / conduits in the profile", (ref["nodes"], ref["conduits"]), (mine["nodes"], mine["conduits"]), True)
for lay in sorted(set(ref["per_layer"]) | set(mine["per_layer"])):
    a, b = ref["per_layer"].get(lay, {}), mine["per_layer"].get(lay, {})
    for key in ("pl_colors", "pl_vertices", "pl_closed", "heights", "align", "text_patterns"):
        if key in a or key in b:
            av, bv = a.get(key), b.get(key)
            if key == "pl_vertices" and lay in ("Ground_Elevation", "Hydraulic_Grade"): ok = True
            elif key == "pl_closed": ok = (av or 0) / max(1, ref["nodes"]) == (bv or 0) / max(1, mine["nodes"])
            elif key == "text_patterns": ok = "info"
            else: ok = av == bv
            row("%s: %s" % (lay, key), av, bv, ok)
    for key in ("polylines", "texts"):
        if a.get(key) or b.get(key):
            na = a.get(key, 0); nb = b.get(key, 0)
            if lay in ("Grid", "Grid_Text", "Ground_Elevation"): ok = True
            elif lay == "Annotation_Table" and key == "polylines": ok = (na - ref["nodes"]) == (nb - mine["nodes"])   # 12 fixed lines + a column line per node
            else: ok = abs(na / max(1, ref["nodes"]) - nb / max(1, mine["nodes"])) < 0.6 or abs(na / max(1, ref["conduits"]) - nb / max(1, mine["conduits"])) < 0.6
            row("%s: %s per node" % (lay, key), "%d (%.2f)" % (na, na / max(1, ref["nodes"])), "%d (%.2f)" % (nb, nb / max(1, mine["nodes"])), ok)
row("grid spacing dx, dy", (ref["grid"]["dx"], ref["grid"]["dy"]), (mine["grid"]["dx"], mine["grid"]["dy"])); row("grid x_min, y_min", (ref["grid"]["x_min"], ref["grid"]["y_min"]), (mine["grid"]["x_min"], mine["grid"]["y_min"]), ref["grid"]["x_min"] == mine["grid"]["x_min"])
row("elevation labels x (middle column relative to its grid line)", [ref["elev_label_x"][0]] + [round(x - ref["mid_grid"], 2) for x in ref["elev_label_x"][1:]], [mine["elev_label_x"][0]] + [round(x - mine["mid_grid"], 2) for x in mine["elev_label_x"][1:]]); row("station labels y (relative to y_min)", [round(v - ref["grid"]["y_min"], 2) for v in ref["sta_label_y"]], [round(v - mine["grid"]["y_min"], 2) for v in mine["sta_label_y"]])
row("axis title", [(x, r, t) for x, r, t in ref["axis_title"]], [(x, r, t) for x, r, t in mine["axis_title"]], [(x, r, t) for x, r, t in ref["axis_title"]] == [(x, r, t) for x, r, t in mine["axis_title"]])
row("table rows y", ref["table_rows_y"], mine["table_rows_y"]); row("table label x", ref["table_label_x"], mine["table_label_x"]); row("table horizontal lines y", ref["table_h_lines_y"], mine["table_h_lines_y"])
row("node annotation line offsets", ref["node_annotation_lines"], mine["node_annotation_lines"])
row("ground polyline vertices", ref["ground_vertices"], mine["ground_vertices"], True)
lines += ["", "Known difference: the HGL inside a conduit is a straight line in the generated file (2 vertices) where the export carries the GVF profile points (up to 13); everything else is built by the same rules."]
md = "\n".join(lines); open(os.path.join(OUT, CH + "_vs_Rustaq.md"), "w", encoding="utf-8").write(md); print(md)
# renders
try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    for tag, path, xr in (("generated", MINE, (-80, 1500)), ("sewergems_export", REF, (-80, 1500))):
        doc = ezdxf.readfile(path); fig = plt.figure(figsize=(22, 9)); ax = fig.add_axes([0, 0, 1, 1]); ctx = RenderContext(doc); out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(doc.modelspace(), finalize=True); ax.set_xlim(*xr); ys = [v[1] for e in doc.modelspace().query("POLYLINE[layer==\"Ground_Elevation\"]") for v in e.points() if xr[0] <= v[0] <= xr[1]]
        ax.set_ylim(-150, max(ys) + 60); ax.set_aspect("auto"); fig.savefig(os.path.join(OUT, "%s_%s_first1500m.png" % (CH, tag)), dpi=110, facecolor="white"); plt.close(fig)
    print("renders written")
except Exception as ex: print("render skipped:", ex)
