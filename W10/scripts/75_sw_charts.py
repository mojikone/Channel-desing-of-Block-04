"""Step 75 (W8) - the channel charts of the stormwater channels report: C11 (bed widths, length-weighted, 50 m bins), C12 (lengths
by class) and C13 (200-year design flow against bed width) restricted to the stormwater main and secondary channels and dykes,
written as report/img/C11_width_hist_sw.png, C12_lengths_by_class_sw.png, C13_flow_vs_width_sw.png (the W7 step 70 code on the
same data, filtered).
    python 75_sw_charts.py [--run run_20261012_1758]"""
import os, sys
import numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); W8 = os.path.dirname(HERE); CB = os.path.dirname(W8); B4 = os.path.dirname(CB); W7 = os.path.join(CB, "W7")
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(CB, "W3", "scripts")); sys.path.insert(0, os.path.join(W8, "report"))
import figstyle as FS
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
RUN = opt("--run", "run_20261012_1758"); SUF = "_sw"; KEEP = {"SM", "SS"}
IMG = os.path.join(W8, "report", "img"); os.makedirs(IMG, exist_ok=True)
def save(fig, name):
    p = os.path.join(IMG, name + SUF + ".png"); fig.savefig(p, dpi=200, bbox_inches="tight"); plt.close(fig); print("  ", name + SUF)
exp = pd.read_csv(os.path.join(W7, "sewergems", "results", RUN, "bridge_exports", "conduits_200yr.csv")).set_index("label")
seg = gpd.read_file(os.path.join(W7, "final", "Block4_design_segments.shp"))
seg = seg.merge(exp[["length_m", "slope", "flow", "velocity", "rise_m", "span_m", "percentfull", "depthtorise", "depthout", "stop"]], left_on="SGLabel", right_index=True, how="left")
seg = seg[seg.Class.isin(KEEP)]
CLS = {"SM": "Stormwater main", "SS": "Stormwater secondary"}; COL = {"SM": FS.ORANGE, "SS": "#7F7F7F"}
# ---- C11 width distribution, length-weighted
fig, ax = plt.subplots(figsize=(7.6, 3.4)); bins = np.arange(0, seg.span_m.max() + 50, 50)
for k, c in COL.items():
    s = seg[seg.Class == k]; ax.hist(s.span_m, bins=bins, weights=s.Length / 1000, color=c, alpha=0.85, label=CLS[k], edgecolor="white", linewidth=0.5, histtype="bar", stacked=False)
h, _ = np.histogram(seg.span_m, bins=bins, weights=seg.Length / 1000)
for x0, v in zip(bins[:-1], h):
    if v > 0: ax.text(x0 + 25, v + 0.3, f"{v:,.1f}", ha="center", fontsize=6.5, color=FS.MUTED)
ax.set_xlabel("designed bed width, m (50 m bins)"); ax.set_ylabel("length of reaches, km"); ax.legend(fontsize=7.5); FS.finish(ax); fig.tight_layout(); save(fig, "C11_width_hist")
# ---- C12 lengths by class, the stormwater channels and dykes
g = gpd.read_file(os.path.join(B4, "Hydrology", "SHP", "temp", "Channels and Dykes 04102026.shp")); g = g[g["Block"] == 4]; g["km"] = g.geometry.length / 1000
order = [("Sw M CH", "Stormwater main channel"), ("Sw S CH", "Stormwater secondary channel"), ("Sw M D", "Stormwater main dyke"), ("Sw S D", "Stormwater secondary dyke")]
vals = [float(g[g.CHtt == k].km.sum()) for k, _ in order]
fig, ax = plt.subplots(figsize=(7.6, 2.6)); cols = [FS.BLUE, FS.BLUE, "#9DC3E6", "#9DC3E6"]
b = ax.barh(range(len(order)), vals, color=cols); ax.set_yticks(range(len(order))); ax.set_yticklabels([n for _, n in order], fontsize=8); ax.invert_yaxis()
for i, v in enumerate(vals): ax.text(v + 1, i, f"{v:,.1f} km", va="center", fontsize=8, color=FS.INK)
ax.set_xlabel("length, km"); ax.set_xlim(0, max(vals) * 1.25); FS.finish(ax); fig.tight_layout(); save(fig, "C12_lengths_by_class")
# ---- C13 flow against width by class
fig, ax = plt.subplots(figsize=(7.6, 4.0))
for k, c in COL.items():
    s = seg[(seg.Class == k) & (seg.flow > 0)]; ax.scatter(s.flow, s.span_m, s=14, color=c, label=CLS[k], alpha=0.85, edgecolor="white", linewidth=0.4)
ax.set_xlabel("200-year design flow of the reach, m³/s"); ax.set_ylabel("designed bed width, m"); ax.legend(fontsize=7.5); FS.finish(ax); fig.tight_layout(); save(fig, "C13_flow_vs_width")
print("done")
