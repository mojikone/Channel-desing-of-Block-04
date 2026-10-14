"""Step 82b (W10) - the channel extents per return period: every reach at its designed width over its whole length (as the
W9 polygons of step 82), and a short transition at each joint between reaches instead of a step (his rule, 2026-10-14, after
the first W10 version had interpolated the width between the reach midpoints, which contradicts the design: a reach is one section).

Transition at a joint: length = 3 x the change of bed width, capped at a third of the shorter adjacent reach, never under 20 m,
centred on the joint (half in each reach); the width runs linearly from one reach's width to the other's along the centreline
through the joint. The transition ribbon is the union of round-capped buffers of 2 m centreline segments, so it also closes the
wedge that two flat-ended reach buffers leave on the outer side of a bend (where the widths are equal the 20 m piece is a round
join). The constant parts are the reach lines trimmed by half the transition at each joint, flat-capped as before. The corridor
adds 15.5 m each side. Writes W10/gis/extents/extent_<rp>yr.shp (kind bed / corridor, the schema of step 82); the dyke extent
(constant 15.5 m) is untouched.
    python 82b_extents_taper.py [--ratio 3] [--cap 3] [--min 20]"""
import os, sys, math
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import LineString
from shapely.ops import unary_union, linemerge, substring
HERE = os.path.dirname(os.path.abspath(__file__)); W10 = os.path.dirname(HERE)
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
RATIO = float(opt("--ratio", 3.0)); CAP = float(opt("--cap", 3.0)); LMIN = float(opt("--min", 20.0)); STEP = 2.0
EXTRA = 15.5; RPS = ["2", "5", "10", "25", "50", "100", "200", "500"]
seg = gpd.read_file(os.path.join(W10, "gis", "segments_all_rp.gpkg"))
OUT = os.path.join(W10, "gis", "extents"); os.makedirs(OUT, exist_ok=True)

def line_of(g):
    return linemerge(g) if g.geom_type == "MultiLineString" else g

def transition_length(dw, L1, L2):
    """Length of the transition at a joint: RATIO x the width change, capped at 1/CAP of the shorter reach, at least LMIN, never longer than the shorter reach."""
    lt = max(LMIN, min(RATIO * abs(dw), min(L1, L2) / CAP))
    return min(lt, min(L1, L2))

def ribbon(path, h0, h1):
    """The transition ribbon along 'path' (LineString): half-width from h0 at its start to h1 at its end, as the union of round-capped buffers of STEP m segments."""
    n = max(int(math.ceil(path.length / STEP)), 1); ds = [min(i * STEP, path.length) for i in range(n + 1)]
    pts = [path.interpolate(d) for d in ds]; pieces = []
    for i in range(n):
        ha = h0 + (h1 - h0) * ds[i] / path.length; hb = h0 + (h1 - h0) * ds[i + 1] / path.length; h = 0.5 * (ha + hb)
        if h <= 0: continue
        pieces.append(LineString([pts[i].coords[0], pts[i + 1].coords[0]]).buffer(h, quad_segs=8))
    return unary_union(pieces)

def channel_extent(ch, half):
    """Polygon of one channel for the half-widths 'half' (one per reach, in Seg order): constant parts plus the joint transitions."""
    lines = [line_of(g) for g in ch.geometry]; L = [ln.length for ln in lines]; n = len(lines); parts = []
    trim_start = [0.0] * n; trim_end = [0.0] * n
    for i in range(n - 1):
        lt = transition_length(2 * (half[i + 1] - half[i]), L[i], L[i + 1]); trim_end[i] = lt / 2.0; trim_start[i + 1] = lt / 2.0
        a = substring(lines[i], max(L[i] - lt / 2.0, 0.0), L[i]); b = substring(lines[i + 1], 0.0, min(lt / 2.0, L[i + 1]))
        coords = list(a.coords) + list(b.coords)[1:]
        if len(coords) >= 2: parts.append(ribbon(LineString(coords), half[i], half[i + 1]))
    for i in range(n):
        a, b = trim_start[i], L[i] - trim_end[i]
        if b - a > 0.5: parts.append(substring(lines[i], a, b).buffer(half[i], cap_style=2))
    return unary_union(parts)

for k in RPS:
    beds, cors = [], []
    for name, ch in seg.groupby("Channel"):
        ch = ch.sort_values("Seg"); w = ch[f"span_{k}"].astype(float).fillna(0.0).values
        beds.append(channel_extent(ch, w / 2.0)); cors.append(channel_extent(ch, w / 2.0 + EXTRA))
    bed = unary_union(beds); cor = unary_union(cors)
    g = gpd.GeoDataFrame({"kind": ["bed", "corridor"], "rp_years": [int(k), int(k)],
                          "note": [f"designed bed width, {k}-year flow; transitions at the reach joints", f"bed + {EXTRA} m each side (embankment and access road); transitions at the reach joints"]},
                         geometry=[bed, cor], crs=seg.crs)
    g.to_file(os.path.join(OUT, f"extent_{k}yr.shp"))
    nb = len(getattr(bed, "geoms", [bed])); nc = len(getattr(cor, "geoms", [cor]))
    print(f"extent_{k}yr: bed {bed.area / 1e4:.0f} ha ({nb} parts), corridor {cor.area / 1e4:.0f} ha ({nc} parts)")
