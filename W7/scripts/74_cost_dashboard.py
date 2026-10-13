"""Step 74 (W7) - the costs dashboard of report R4, the layout of the Block 6 report's Appendix 1 (engineer, 2026-10-12): page 1, three
horizontal bar charts (channel, dyke and culvert cost by global catchment; the Block 6 third chart was by existing structure type,
his instruction of 11:05 makes all three by catchment) over the total
cost by infrastructure type with the grand total in the title; page 2, the cost of every channel, dyke and culvert. Data from the
W7 estimate through the report's data_facts (channel_quantities, dykes, culverts). Writes report/img/D1_dashboard.png and
D2_dashboard_items.png (A4 landscape pages at 200 dpi).
    python 74_cost_dashboard.py"""
import os, sys, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
HERE = os.path.dirname(os.path.abspath(__file__)); W7 = os.path.dirname(HERE); CB = os.path.dirname(W7)
sys.path.insert(0, os.path.join(W7, "report")); sys.path.insert(0, os.path.join(W7, "report", "lib")); sys.path.insert(0, HERE)
import data_facts as A
IMG = os.path.join(W7, "report", "img"); BLUE, ORANGE, GREY, INK = "#1F5F8B", "#E8743B", "#D9D9D9", "#1F1F1F"
plt.rcParams.update({"font.family": "Arial", "font.size": 9})
q = A.channel_quantities(); dk = A.dykes(); cv = A.culverts(); tot = A.cost_totals(); cc = A.cost_by_catchment()
def frame(ax, title):
    ax.set_title(title, fontsize=10, color="#404040", pad=10)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#BFBFBF"); ax.spines["bottom"].set_color("#BFBFBF"); ax.grid(axis="x", color="#E6E6E6", lw=0.8); ax.set_axisbelow(True); ax.tick_params(colors="#404040")
def hbar(ax, labels, values, title, xlabel="Cost (million OMR)", color=BLUE, fmt="{:,.2f}"):
    y = np.arange(len(labels)); b = ax.barh(y, values, 0.55, color=color); ax.set_yticks(y); ax.set_yticklabels(labels)
    for bb, v in zip(b, values): ax.text(v + max(values) * 0.02, bb.get_y() + bb.get_height() / 2, fmt.format(v), va="center", fontsize=8.5, color=INK)
    ax.set_xlim(0, max(values) * 1.22); ax.set_xlabel(xlabel, fontsize=9); frame(ax, title)
# ---- page 1
fig = plt.figure(figsize=(11.69, 8.27)); gs = GridSpec(2, 3, height_ratios=[1.35, 1.0], figure=fig, hspace=0.6, wspace=0.75)
ax1 = fig.add_subplot(gs[0, 0]); hbar(ax1, cc.gca, cc.channels, "Channel cost by catchment\n(million OMR)")
ax1.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=BLUE)], labels=["Construction"], loc="lower right", fontsize=8, frameon=False)
ax2 = fig.add_subplot(gs[0, 1]); hbar(ax2, cc.gca, cc.dykes, "Dyke construction cost by\ncatchment (million OMR)")
ax3 = fig.add_subplot(gs[0, 2]); hbar(ax3, cc.gca, cc.culverts, "Culvert cost by catchment\n(million OMR)")   # by global catchment, like the other two (engineer, 2026-10-12 11:05)
ax4 = fig.add_subplot(gs[1, :]); names = ["Channels", "Dykes", "Culverts"]; vals = [tot["channels"], tot["dykes"], tot["culverts"]]
b = ax4.bar(names, vals, 0.45, color=BLUE)
for bb, v in zip(b, vals): ax4.text(bb.get_x() + bb.get_width() / 2, v + max(vals) * 0.02, f"{v:,.2f}", ha="center", fontsize=10, color=INK)
ax4.set_ylim(0, max(vals) * 1.2); ax4.set_ylabel("Cost (million OMR)"); frame(ax4, "Total cost by infrastructure type (million OMR), total %.1f million OMR" % tot["total"]); ax4.grid(axis="y", color="#E6E6E6", lw=0.8); ax4.grid(axis="x", visible=False)
fig.savefig(os.path.join(IMG, "D1_dashboard.png"), dpi=200, bbox_inches="tight"); plt.close(fig); print("   D1_dashboard")
# ---- page 2: every channel, dyke and culvert
fig = plt.figure(figsize=(11.69, 8.27)); gs = GridSpec(1, 3, width_ratios=[1.2, 1.1, 1.0], figure=fig, wspace=0.75)
qq = q.sort_values("cost_mOMR", ascending=True); ax = fig.add_subplot(gs[0, 0]); hbar(ax, qq.channel, qq.cost_mOMR.values, "Channel cost, all channels (million OMR)"); ax.tick_params(axis="y", labelsize=7)
dd = dk.sort_values("cost_mOMR", ascending=True); ax = fig.add_subplot(gs[0, 1]); hbar(ax, dd.name, dd.cost_mOMR.values, "Dyke cost, all dykes (million OMR)"); ax.tick_params(axis="y", labelsize=7)
cs = cv.sort_values("cost_mOMR", ascending=True); ax = fig.add_subplot(gs[0, 2]); hbar(ax, [f"{r.id}  {r.channel}" for r in cs.itertuples()], cs.cost_mOMR.values, "Culvert cost, all structures (million OMR)"); ax.tick_params(axis="y", labelsize=7)
fig.savefig(os.path.join(IMG, "D2_dashboard_items.png"), dpi=200, bbox_inches="tight"); plt.close(fig); print("   D2_dashboard_items")
