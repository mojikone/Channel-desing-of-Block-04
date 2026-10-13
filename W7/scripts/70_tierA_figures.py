"""Step 70 (W7) - the figures and tables that bring report R4 to the Block 6 layout (engineer, 2026-10-12, "Tier A" and "Tier C"):
  charts  -> W7/report/img: C11_width_hist (bed widths, length-weighted, 50 m bins), C12_lengths_by_class (channels and dykes),
             C13_flow_vs_width (200-yr design flow against bed width by class), C14_arf_curve (the area reduction factor),
             F10_process (the design-process flowchart, seven stages in two bands)
  images  -> W7/report/img: F11_section_fill.png, F12_section_cut.png (the project's typical sections, as in the Block 6 report)
  tables  -> W7/report/data: size_inventory.csv (size x length), reach_table.csv (every reach at 200 yr), drawings.csv (the
             plan-profile set), outfalls.csv (the 15 model outfalls: flow, width, invert, ground, depth, MHHW margin)
All from the SewerGEMS run named in --run (200 yr), the final segment layer, the alignment shapefile and the set's contents file.
    python 70_tierA_figures.py [--run run_20261012_1758]"""
import os, sys, re, shutil, json
import numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
HERE = os.path.dirname(os.path.abspath(__file__)); W7 = os.path.dirname(HERE); CB = os.path.dirname(W7); B4 = os.path.dirname(CB)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(CB, "W3", "scripts")); sys.path.insert(0, os.path.join(W7, "report"))
import figstyle as FS
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
RUN = opt("--run", "run_20261012_1758")
IMG = os.path.join(W7, "report", "img"); DATA = os.path.join(W7, "report", "data"); os.makedirs(IMG, exist_ok=True); os.makedirs(DATA, exist_ok=True)
MHHW = 0.70
def save(fig, name):
    p = os.path.join(IMG, name + ".png"); fig.savefig(p, dpi=200, bbox_inches="tight"); plt.close(fig); print("  ", name)
exp = pd.read_csv(os.path.join(W7, "sewergems", "results", RUN, "bridge_exports", "conduits_200yr.csv")).set_index("label")
nodes = pd.read_csv(os.path.join(W7, "sewergems", "results", RUN, "bridge_exports", "nodes_200yr.csv")).set_index("label")
seg = gpd.read_file(os.path.join(W7, "final", "Block4_design_segments.shp"))
seg = seg.merge(exp[["length_m", "slope", "flow", "velocity", "rise_m", "span_m", "percentfull", "depthtorise", "depthout", "stop"]], left_on="SGLabel", right_index=True, how="left")
CLS = {"FP": "Flood protection", "SM": "Stormwater main", "SS": "Stormwater secondary"}; COL = {"FP": FS.BLUE, "SM": FS.ORANGE, "SS": "#7F7F7F"}
# ---- C11 width distribution, length-weighted
fig, ax = plt.subplots(figsize=(7.6, 3.4)); bins = np.arange(0, seg.span_m.max() + 50, 50)
for k, c in COL.items():
    s = seg[seg.Class == k]; ax.hist(s.span_m, bins=bins, weights=s.Length / 1000, color=c, alpha=0.85, label=CLS[k], edgecolor="white", linewidth=0.5, histtype="bar", stacked=False)
h, _ = np.histogram(seg.span_m, bins=bins, weights=seg.Length / 1000)
for x0, v in zip(bins[:-1], h):
    if v > 0: ax.text(x0 + 25, v + 0.3, f"{v:,.1f}", ha="center", fontsize=6.5, color=FS.MUTED)
ax.set_xlabel("designed bed width, m (50 m bins)"); ax.set_ylabel("length of reaches, km"); ax.legend(fontsize=7.5); FS.finish(ax); fig.tight_layout(); save(fig, "C11_width_hist")
# ---- C12 lengths by class, channels and dykes
g = gpd.read_file(os.path.join(B4, "Hydrology", "SHP", "temp", "Channels and Dykes 04102026.shp")); g = g[g["Block"] == 4]; g["km"] = g.geometry.length / 1000
order = [("FP CH", "Flood protection channel"), ("Sw M CH", "Stormwater main channel"), ("Sw S CH", "Stormwater secondary channel"), ("FP D", "Flood protection dyke"), ("Sw M D", "Stormwater main dyke"), ("Sw S D", "Stormwater secondary dyke")]
vals = [float(g[g.CHtt == k].km.sum()) for k, _ in order]
fig, ax = plt.subplots(figsize=(7.6, 3.2)); cols = [FS.BLUE, FS.BLUE, FS.BLUE, "#9DC3E6", "#9DC3E6", "#9DC3E6"]
b = ax.barh(range(len(order)), vals, color=cols); ax.set_yticks(range(len(order))); ax.set_yticklabels([n for _, n in order], fontsize=8); ax.invert_yaxis()
for i, v in enumerate(vals): ax.text(v + 1, i, f"{v:,.1f} km", va="center", fontsize=8, color=FS.INK)
ax.set_xlabel("length, km"); ax.set_xlim(0, max(vals) * 1.25); FS.finish(ax); fig.tight_layout(); save(fig, "C12_lengths_by_class")
# ---- C13 flow against width by class
fig, ax = plt.subplots(figsize=(7.6, 4.0))
for k, c in COL.items():
    s = seg[(seg.Class == k) & (seg.flow > 0)]; ax.scatter(s.flow, s.span_m, s=14, color=c, label=CLS[k], alpha=0.85, edgecolor="white", linewidth=0.4)
ax.set_xlabel("200-year design flow of the reach, m³/s"); ax.set_ylabel("designed bed width, m"); ax.legend(fontsize=7.5); FS.finish(ax); fig.tight_layout(); save(fig, "C13_flow_vs_width")
# ---- C14 ARF curve
import data_facts as DF
arf = DF.arf(); fig, ax = plt.subplots(figsize=(7.0, 3.2)); ax.plot([a for a, f in arf], [f for a, f in arf], color=FS.BLUE, lw=1.6, marker="o", ms=3.5)
ax.set_xscale("log"); ax.set_xlabel("catchment area, km²"); ax.set_ylabel("area reduction factor"); ax.set_ylim(0.5, 1.02); FS.finish(ax); fig.tight_layout(); save(fig, "C14_arf_curve")
# ---- F10 the design-process flowchart (the seven stages of the report's table, in two bands)
stages = [("1", "Project input", ["Design rainfall", "Topography", "Land use", "Dam characteristics"]), ("2", "Catchment analysis", ["HEC-HMS subbasins", "ARF, SCS curve number", "Lag time", "Reservoir and reach routing"]),
          ("3", "Rainfall-runoff simulation", ["HEC-HMS model", "200-year peak flow", "Inflow and outflow hydrographs"]), ("4", "Channel alignment", ["HEC-RAS 2D results", "Wadi geometry", "Site visits", "Client and authority input"]),
          ("5", "Hydraulic channel design", ["Manning equation", "Depth, slope, velocity", "Freeboard", "Culvert sizing"]), ("6", "Performance assessment", ["Dyke heights", "Culvert and bridge capacity", "Outfalls and system check", "200-year protection"]),
          ("7", "Outputs", ["Channel dimensions", "Dyke heights", "Culvert capacities", "Solutions for bottlenecks"])]
fig, ax = plt.subplots(figsize=(11, 5.6)); ax.set_xlim(0, 11); ax.set_ylim(0, 5.6); ax.axis("off")
pos = {0: (0.35, 3.1), 1: (3.05, 3.1), 2: (5.75, 3.1), 3: (8.45, 3.1), 4: (1.7, 0.3), 5: (4.4, 0.3), 6: (7.1, 0.3)}; W, H = 2.45, 2.2
for i, (n, title, items) in enumerate(stages):
    x, y = pos[i]; ax.add_patch(FancyBboxPatch((x, y), W, H, boxstyle="round,pad=0.02,rounding_size=0.25", facecolor="#1F3B63", edgecolor="none"))
    ax.add_patch(plt.Circle((x + 0.3, y + H - 0.3), 0.19, color="#4FA3E3")); ax.text(x + 0.3, y + H - 0.3, n, ha="center", va="center", fontsize=9, color="white", fontweight="bold")
    ax.text(x + 0.58, y + H - 0.3, title, ha="left", va="center", fontsize=8.3, color="#9FD0FF", fontweight="bold")
    ax.plot([x + 0.15, x + W - 0.15], [y + H - 0.58, y + H - 0.58], color="#3C5A85", lw=0.8)
    for j, it in enumerate(items): ax.text(x + 0.2, y + H - 0.9 - 0.33 * j, "• " + it, ha="left", va="center", fontsize=8.6, color="white")
for i in range(6):
    (x1, y1), (x2, y2) = pos[i], pos[i + 1]
    if i == 3:   # the band changes: a stub leaves stage 4 to the right and a stub enters stage 5 from the left, as the project's own figure
        ax.add_patch(FancyArrowPatch((x1 + W + 0.02, y1 + H / 2), (x1 + W + 0.32, y1 + H / 2), arrowstyle="-|>", mutation_scale=14, color="#4FA3E3", lw=1.6))
        ax.add_patch(FancyArrowPatch((x2 - 0.32, y2 + H / 2), (x2 - 0.02, y2 + H / 2), arrowstyle="-|>", mutation_scale=14, color="#4FA3E3", lw=1.6))
    else: ax.add_patch(FancyArrowPatch((x1 + W + 0.02, y1 + H / 2), (x2 - 0.02, y2 + H / 2), arrowstyle="-|>", mutation_scale=14, color="#4FA3E3", lw=1.6))
ax.text(0.05, 4.2, "Input and analysis", rotation=90, ha="center", va="center", fontsize=9, color="#4FA3E3"); ax.text(0.05, 1.4, "Design and verification", rotation=90, ha="center", va="center", fontsize=9, color="#4FA3E3")
fig.tight_layout(); save(fig, "F10_process")
# ---- the typical sections of the project (the images of the Block 6 report, the same standard details)
src = r"C:\Users\mojtaba\AppData\Local\Temp\claude\D--Mojtaba-Renardet-2224-WS11-Batinah-Block-4\72a3ff20-809e-4d71-bf42-7b9f694d69ff\scratchpad\b6_img"
for a, b in (("img21.png", "F11_section_fill.png"), ("img22.png", "F12_section_cut.png")):
    if os.path.exists(os.path.join(src, a)): shutil.copy2(os.path.join(src, a), os.path.join(IMG, b)); print("  ", b)
# ---- tables
inv = seg.copy(); inv["size"] = inv.apply(lambda r: "%.1f x %s" % (r.rise_m, ("%.1f" % r.span_m).replace(".0", "")), axis=1)
si = inv.groupby(["rise_m", "span_m", "size"])["Length"].sum().reset_index().sort_values(["rise_m", "span_m"]); si["Length"] = si.Length.round(1); si.to_csv(os.path.join(DATA, "size_inventory.csv"), index=False)
rt = seg[["SGLabel", "Channel", "Class", "Length", "slope", "velocity", "percentfull", "depthtorise", "rise_m", "span_m", "flow"]].copy()
rt["n"] = 0.03; rt["size"] = inv["size"]; rt = rt.rename(columns={"SGLabel": "label", "Channel": "channel", "Length": "length_m"})
def ok(n):
    m = re.match(r"^(HAW|SHA|SAR|SAK)CH(\d+)-C(\d+)", n); return ({"HAW": 0, "SHA": 1, "SAR": 2, "SAK": 3}[m.group(1)], int(m.group(2)), int(m.group(3))) if m else (9, 0, 0)
rt["k"] = rt.label.map(ok); rt = rt.sort_values("k").drop(columns="k"); rt.to_csv(os.path.join(DATA, "reach_table.csv"), index=False)
cont = os.path.join(W7, "sewergems", "sheets", "scripts", "PDF", "Set", "2224-PD-HY-PP-B4_Plan_and_Profile_Drawings_200yr_R9_contents.csv")
if os.path.exists(cont): shutil.copy2(cont, os.path.join(DATA, "drawings.csv")); print("   drawings.csv", len(pd.read_csv(cont)), "rows")
last = seg.groupby("Channel").apply(lambda s: s.sort_values("Seg").iloc[-1]); rows = []
for lab, n in nodes[nodes["type"] == "OF"].iterrows() if "type" in nodes.columns else []:
    pass
of = nodes[nodes.index.str.contains(r"-O\d+$")]
for lab, n in of.iterrows():
    up = seg[seg.stop == lab]
    q = float(up.flow.max()) if len(up) else float("nan"); w = float(up.span_m.max()) if len(up) else float("nan"); dep = float(up.depthout.max()) if len(up) else float("nan"); ch = up.Channel.iloc[0] if len(up) else ""
    rows.append(dict(outfall=lab, channel=ch, Q200=round(q, 1), width_m=w, invert_m=round(float(n["invert"]), 2), ground_m=round(float(n["ground"]), 2), depth_m=round(dep, 2), invert_minus_MHHW=round(float(n["invert"]) - MHHW, 2)))
pd.DataFrame(rows).sort_values("outfall").to_csv(os.path.join(DATA, "outfalls.csv"), index=False); print("   outfalls.csv", len(rows), "| size_inventory", len(si), "| reach_table", len(rt))
