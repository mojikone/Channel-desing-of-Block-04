"""Step 04 - where each profile view goes in the Civil 3D drawing: civil3d/profile_views.csv (name, kind, insertX, insertY,
width, height, distance to its alignment) + a QA sketch civil3d/profile_view_layout.png and .dxf.

Rule (engineer, 2026-10-07): channel profile views as close as possible to their own alignment, organised; dyke profile
views in a separate stack. Placement: a channel view starts under the west end of its alignment's extent and slides
south (then east) until it overlaps neither an alignment corridor nor a placed view; the dyke views form one column
east of the block, sorted by name. The view footprint is the alignment length by the elevation range at the vertical
exaggeration of the profile view style plus the band space; Civil 3D places the view's lower-left at the insertion point.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import box
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_w4 import LINES, POINTS, C3D

VE = 10.0            # vertical exaggeration of the profile view style used in the drawing
BAND_M = 40.0        # model-space height of the data bands and titles under the grid (at VE 10: 4 m of elevation)
MARGIN_Z = 2.0       # metres of elevation above and below the ground line
GAP = 150.0          # clearance between a view and anything else, m
STEP = 100.0         # slide step, m

def main():
    lines = gpd.read_file(LINES / "Block4_lines.gpkg").sort_values("order"); summ = pd.read_csv(POINTS / "points_summary.csv").set_index("name")
    obstacles = [g.buffer(120.0) for g in lines.geometry]                      # the corridor of every alignment (not its bounding box)
    placed = []; rows = []
    ch = lines[lines.kind == "channel"].copy(); ch["ymin"] = ch.geometry.bounds.miny; ch = ch.sort_values("ymin", ascending=False)   # north first
    def free(rect): return not any(rect.intersects(o) for o in obstacles) and not any(rect.intersects(p) for p in placed)
    for r in ch.itertuples():
        w = r.length_m; h = (summ.loc[r.name, "z_max"] - summ.loc[r.name, "z_min"] + 2 * MARGIN_Z) * VE + BAND_M
        xmin, ymin, xmax, ymax = r.geometry.bounds; cx = (xmin + xmax) / 2
        starts = [(xmin, ymin - GAP - h, 0, -STEP), (xmin, ymax + GAP, 0, STEP), (xmax + GAP, ymin, STEP, 0), (xmin - GAP - w, ymin, -STEP, 0),            # below, above, right, left of the extent
                  (cx - w / 2, ymin - GAP - h, 0, -STEP), (cx - w / 2, ymax + GAP, 0, STEP)]
        best = None
        for x0, y0, dx, dy_ in starts:
            x, y = x0, y0
            for k in range(80):
                rect = box(x, y, x + w, y + h)
                if free(rect):
                    d = r.geometry.distance(rect)
                    if best is None or d < best[0]: best = (d, x, y, k)
                    break
                x += dx; y += dy_
        if best is None: x, y, k = xmin, ymin - GAP - h - 8000.0, 999
        else: _, x, y, k = best
        placed.append(box(x, y, x + w, y + h).buffer(GAP / 2)); dist = float(r.geometry.distance(box(x, y, x + w, y + h)))
        rows.append(dict(name=r.name, kind="channel", insertX=round(x, 2), insertY=round(y, 2), width_m=round(w, 1), height_m=round(h, 1), distance_to_alignment_m=round(dist, 0), slides=k))
    dy = lines[lines.kind == "dyke"].sort_values("name"); x0 = float(lines.total_bounds[2]) + 2000.0; y = float(lines.total_bounds[3])
    for r in dy.itertuples():
        w = r.length_m; h = (summ.loc[r.name, "z_max"] - summ.loc[r.name, "z_min"] + 2 * MARGIN_Z) * VE + BAND_M; y -= h
        rows.append(dict(name=r.name, kind="dyke", insertX=round(x0, 2), insertY=round(y, 2), width_m=round(w, 1), height_m=round(h, 1), distance_to_alignment_m=round(float(r.geometry.distance(box(x0, y, x0 + w, y + h))), 0), slides=0)); y -= GAP
    pv = pd.DataFrame(rows); pv.to_csv(C3D / "profile_views.csv", index=False)
    # QA sketch
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(12, 12))
    for r in lines.itertuples(): ax.plot(*r.geometry.xy, color="#C00000" if r.kind == "channel" else "#7030A0", lw=0.8)
    for r in pv.itertuples():
        ax.add_patch(plt.Rectangle((r.insertX, r.insertY), r.width_m, r.height_m, fill=True, alpha=0.25, color="#1F3B63" if r.kind == "channel" else "#7F6000")); ax.text(r.insertX, r.insertY + r.height_m, r.name, fontsize=4.5, va="bottom")
    ax.set_aspect("equal"); ax.set_title("Profile view footprints (blue: channels, near their alignments; brown: the dyke stack)"); fig.savefig(C3D / "profile_view_layout.png", dpi=150, bbox_inches="tight")
    L = ["0", "SECTION", "2", "ENTITIES"]
    for r in pv.itertuples():
        lay = "PV_CH" if r.kind == "channel" else "PV_D"; x0_, y0_, x1_, y1_ = r.insertX, r.insertY, r.insertX + r.width_m, r.insertY + r.height_m
        L += ["0", "POLYLINE", "8", lay, "66", "1", "70", "1"]
        for px, py in ((x0_, y0_), (x1_, y0_), (x1_, y1_), (x0_, y1_)): L += ["0", "VERTEX", "8", lay, "10", f"{px:.2f}", "20", f"{py:.2f}", "30", "0"]
        L += ["0", "SEQEND", "8", lay, "0", "TEXT", "8", lay, "10", f"{x0_:.2f}", "20", f"{y1_ + 20:.2f}", "30", "0", "40", "60", "1", r.name]
    L += ["0", "ENDSEC", "0", "EOF"]; (C3D / "profile_view_layout.dxf").write_text("\n".join(L) + "\n", encoding="ascii")
    print(pv.groupby("kind")[["distance_to_alignment_m", "slides"]].describe().round(0).to_string()); print("->", C3D / "profile_views.csv")

if __name__ == "__main__":
    main()
