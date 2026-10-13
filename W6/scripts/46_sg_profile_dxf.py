"""Step 46 - a SewerGEMS-identical profile DXF without the GUI (engineer, 2026-10-11 night, trial on HAW-CH1-FP): the file is built
exactly like SewerGEMS's own "Export to DXF" of a profile, measured on the Block 6 export OUTPUT\\DXF\\1\\Ais-CH1-FP.dxf of the Rustaq
model (W6/README.md, "Profiles inside SewerGEMS"): DXF R12, x = station in m, y = elevation x 10, layers Grid (254) / Grid_Text /
Ground_Elevation (3) / Crown / Invert / Structure / Hydraulic_Grade (5) / Energy_Grade (1) / Annotation / Tap / Tap_Drop_Pipe /
Annotation_Table (254), 2D POLYLINE + TEXT entities, text style Standard, heights 4.1667 and 2.0833, the grid every 25 m and 2 m,
elevation labels at x = -32.7, station labels "k+mm" at y = -7.7, the axis title "Elevation (m)" rotated at x = -58, node annotation
label / "Rim: x m" / "Invert: y m" at station + 2.44 with the leader and its arrowhead, conduit annotation "label: length @ slope"
and "Box - span x rise m material" rotated along the conduit, the table of nine rows below the chart (conduit rows at the conduit
middle, node rows at the node station, column lines from the table bottom to the top of the grid).
Data: the conduit and node exports of the design run (W6/sewergems/results/<run>/bridge_exports), the profile path of
W6/sewergems/profiles/profile_paths.csv, the class-resolved sizes of the corrected exports (span, rise, material; step 48), the
ground from the EG samples of the drawing (output/eg_samples.json, the DTM along the alignment). Known difference from the GUI
export: the HGL inside a conduit is a straight line between its two ends (the GVF profile points are not exported by the API).
    python 46_sg_profile_dxf.py --channel HAW-CH1-FP [--scenario 200yr] [--run run_20261011_1721]"""
import os, sys, re, json, math
import pandas as pd, ezdxf
HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE)
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
CH = opt("--channel", "HAW-CH1-FP"); SC = opt("--scenario", "200yr"); RUN = opt("--run", "run_20261011_1721")
OUT = os.path.join(W6, "sewergems", "dxf", RUN, SC); os.makedirs(OUT, exist_ok=True)
FT = 0.3048; TH = 4.16666671550657; TH2 = TH / 2; RISE_DEFAULT = 2.5

# ---------------------------------------------------------------- data
cond = pd.read_csv(os.path.join(W6, "sewergems", "results", RUN, "bridge_exports", "conduits_%s.csv" % SC)).set_index("label")
nodes = pd.read_csv(os.path.join(W6, "sewergems", "results", RUN, "bridge_exports", "nodes_%s.csv" % SC)).set_index("label")
path = pd.read_csv(os.path.join(W6, "sewergems", "profiles", "profile_paths.csv")).set_index("profile").loc[CH, "elements"].split(" > ")
for col in ("rise_m", "span_m", "material", "class_label"):                 # class-resolved sizes written by 48_fix_size_labels.py (a size is class + GUID)
    if col not in cond.columns: sys.exit("conduits_%s.csv has no %s column: run 48_fix_size_labels.py first" % (SC, col))
eg = json.load(open(os.path.join(W6, "output", "eg_samples.json")))[CH]

# ---------------------------------------------------------------- the path: nodes with stations, conduits
N, C = [], []; sta = 0.0
for k, el in enumerate(path):
    if k % 2 == 0:
        n = nodes.loc[el]; N.append({"label": el, "sta": sta, "rim": float(n["ground"]), "inv": float(n["invert"]), "type": n["type"]})
    else:
        c = cond.loc[el]; rise = float(c["rise_m"]) if pd.notna(c["rise_m"]) else RISE_DEFAULT; span = float(c["span_m"]) if pd.notna(c["span_m"]) else float("nan")
        C.append({"label": el, "sta0": sta, "sta1": sta + float(c["length_m"]), "L": float(c["length_m"]), "inv0": float(c["start_inv"]), "inv1": float(c["stop_inv"]),
                  "rise": rise, "span": span, "material": "" if pd.isna(c["material"]) else str(c["material"]), "flow": float(c["flow"]), "d0": float(c["depthin"]), "d1": float(c["depthout"])})
        sta += float(c["length_m"])
for k, n in enumerate(N): n["rise"] = C[min(k, len(C) - 1)]["rise"]
L = N[-1]["sta"]
zmax = max(max(n["rim"] for n in N), max(eg["z"])); zmin = min(min(n["inv"] for n in N), min(c["inv1"] for c in C))
Y0 = math.floor(zmin * 10 / 20) * 20; Y1 = math.ceil(zmax * 10 / 20) * 20; X0 = -25.0; X1 = math.ceil(L / 25) * 25
def kmm(s): v = int(round(abs(s))); return ("-" if s < 0 else "") + "%d+%02d" % (v // 100, v % 100)
def num(v, d=1): return format(v, ",.%df" % d)

# ---------------------------------------------------------------- the drawing
doc = ezdxf.new("R12"); msp = doc.modelspace()
for name, color in [("Grid", 254), ("Grid_Text", 7), ("Crown", 7), ("Invert", 7), ("Structure", 7), ("Hydraulic_Grade", 5), ("Energy_Grade", 1), ("Ground_Elevation", 3), ("Annotation", 7), ("Tap", 7), ("Tap_Drop_Pipe", 7), ("Annotation_Table", 254)]:
    doc.layers.add(name, color=color)
def pl(pts, layer, color, closed=False):
    e = msp.add_polyline2d(pts, dxfattribs={"layer": layer, "color": color}); e.close(closed); return e
def tx(text, x, y, layer, h, halign, valign, rot=0.0):
    e = msp.add_text(text, dxfattribs={"layer": layer, "height": h, "rotation": rot, "color": 0, "style": "Standard"})
    e.dxf.halign = halign; e.dxf.valign = valign; e.dxf.insert = (x, y); e.dxf.align_point = (x, y); return e
# grid: horizontal lines with elevation labels, then vertical lines with station labels, then the axis title
y = Y0
while y <= Y1 + 1e-6:
    pl([(X0, y), (X1, y)], "Grid", 254); tx("%.2f" % (y / 10), -32.7, y, "Grid_Text", TH, 2, 2); y += 20
x = X0
while x <= X1 + 1e-6:
    pl([(x, Y0), (x, Y1)], "Grid", 254); tx(kmm(x), x, Y0 - 7.7, "Grid_Text", TH, 1, 3); x += 25
tx("Elevation (m)", -58.0, (Y0 + Y1) / 2, "Grid_Text", TH, 1, 1, rot=90.0)
tx("Station (m)", X1 / 2, Y0 - 15.24, "Grid_Text", TH, 1, 3)
# ground: the DTM along the alignment
step = eg["step"]; z = eg["z"]; ground = []
for i, zi in enumerate(z):
    s = eg["start"] + i * step
    if s > L + 1e-6: break
    ground.append((s, zi * 10))
if ground[-1][0] < L: ground.append((L, z[min(len(z) - 1, int(round((L - eg["start"]) / step)))] * 10))
pl(ground, "Ground_Elevation", 3)
# crown, invert, structure, hydraulic grade: node, conduit, node ...
for k, n in enumerate(N):
    pl([(n["sta"], (n["inv"] + n["rise"]) * 10)] * 2, "Crown", 0); pl([(n["sta"], n["inv"] * 10)] * 2, "Invert", 0)
    for _ in range(2): pl([(n["sta"], n["rim"] * 10), (n["sta"], n["inv"] * 10)], "Structure", 0)
    if k < len(C):
        c = C[k]
        pl([(c["sta0"], (c["inv0"] + c["rise"]) * 10), (c["sta1"], (c["inv1"] + c["rise"]) * 10)], "Crown", 0)
        pl([(c["sta0"], c["inv0"] * 10), (c["sta1"], c["inv1"] * 10)], "Invert", 0)
for k, n in enumerate(N):
    hgl = (C[k]["inv0"] + C[k]["d0"]) * 10 if k < len(C) else (C[-1]["inv1"] + C[-1]["d1"]) * 10
    if k < len(C):
        c = C[k]
        if math.isnan(c["d0"]) or math.isnan(c["d1"]): continue            # a conduit without results (not computed) gets no hydraulic grade
        pl([(c["sta0"], (c["inv0"] + c["d0"]) * 10), (c["sta1"], (c["inv1"] + c["d1"]) * 10)], "Hydraulic_Grade", 5)
        pl([(N[k + 1]["sta"], (c["inv1"] + c["d1"]) * 10)] * (3 if k + 1 == len(C) else 2), "Hydraulic_Grade", 5)
# annotation: nodes (label, rim, invert, leader with arrowhead), conduits (two rotated lines)
for n in N:
    x = n["sta"]; r = n["rim"] * 10
    tx(n["label"], x + 2.44, r + 13.87, "Annotation", TH, 0, 2); tx("Rim: %.2f m" % n["rim"], x + 2.44, r + 7.62, "Annotation", TH, 0, 2); tx("Invert: %.2f m" % n["inv"], x + 2.44, r + 1.37, "Annotation", TH, 0, 2)
    if n["type"] == "OF": tx("", x + 2.44, r - 4.88, "Annotation", TH, 0, 2)
    pl([(x + 2.44, r + 7.62), (x + 1.7, r + 7.62), (x, r)], "Annotation", 0); pl([(x, r), (x - 0.2, r + 0.98), (x + 0.59, r + 0.8)], "Annotation", 0, closed=True)
for c in C:
    mx = (c["sta0"] + c["sta1"]) / 2; cm = ((c["inv0"] + c["inv1"]) / 2 + c["rise"]) * 10
    ang = math.degrees(math.atan2((c["inv1"] - c["inv0"]) * 10, c["L"])) % 360
    desc = "Box - %.1f x %.1f m" % (c["span"], c["rise"]); c["desc"] = desc; c["slope"] = (c["inv0"] - c["inv1"]) / c["L"]
    tx("%s: %s m @ %.4f m/m" % (c["label"], num(c["L"]), c["slope"]), mx, cm - 7.86, "Annotation", TH, 1, 2, rot=ang)
    tx(("%s %s" % (desc, c["material"])).strip(), mx, cm - 14.11, "Annotation", TH, 1, 2, rot=ang)
# the table
XR = X1 - 0.05; rows = [-36.576 - 12.192 * k for k in range(9)]; lines = [-30.48 - 12.192 * k for k in range(10)]
for n in N: pl([(n["sta"], lines[-1]), (n["sta"], Y1)], "Annotation_Table", 254)
for yl in lines: pl([(X0, yl), (XR, yl)], "Annotation_Table", 254)
pl([(X0, lines[0]), (X0, lines[-1])], "Annotation_Table", 254); pl([(XR, lines[0]), (XR, lines[-1])], "Annotation_Table", 254)
for yr, label in zip(rows, ["Label", "Length (Unified) (m)", "Conduit Description", "Flow (m\\U+00B3/s)", "Slope (Calculated) (m/m)", "Label", "Elevation (Ground) (m)", "Elevation (Invert) (m)", "Station (m)"]):
    tx(label, -26.52, yr, "Annotation_Table", TH2, 2, 2)
for c in C:
    mx = (c["sta0"] + c["sta1"]) / 2
    for yr, val in zip(rows[:5], [c["label"], num(c["L"]), c["desc"], "" if math.isnan(c["flow"]) else num(c["flow"]), "%.4f" % c["slope"]]): tx(val, mx, yr, "Annotation_Table", TH2, 1, 2)
for n in N:
    for yr, val in zip(rows[5:], [n["label"], "%.2f" % n["rim"], "%.2f" % n["inv"], kmm(n["sta"])]): tx(val, n["sta"], yr, "Annotation_Table", TH2, 1, 2)
out = os.path.join(OUT, CH + ".dxf"); doc.saveas(out)
print("written %s | %d nodes, %d conduits, L %.2f m, grid x %s..%s y %s..%s, ground %d vertices" % (out, len(N), len(C), L, X0, X1, Y0, Y1, len(ground)))
for c in C: print("  %-10s %9.1f m  %s  %s  Q %.1f  slope %.4f" % (c["label"], c["L"], c["desc"], c["material"], c["flow"], c["slope"]))
