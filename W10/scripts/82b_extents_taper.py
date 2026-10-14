"""Step 82b (W10) - the channel extents per return period with the width tapered along the channel (his comment of 2026-10-14 on
the KMZ: the reach-by-reach buffers of step 82 gave steps at the reach limits and wedge gaps on the outer side of bends).

For every channel the bed width equals the designed span at each reach midpoint and varies linearly between consecutive midpoints
(constant beyond the first and last midpoint); the corridor adds 15.5 m each side. The outline is the union of the round-capped buffers of the
5 m centreline segments at the local half-width, so bends close without gaps and the taper is continuous. Writes W10/gis/extents/extent_<rp>yr.shp
(kind bed / corridor, the schema of step 82) and leaves the dyke extent (constant 15.5 m) as it is.
    python 82b_extents_taper.py [--step 5]"""
import os, sys, math
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union, linemerge
from shapely import make_valid
HERE = os.path.dirname(os.path.abspath(__file__)); W10 = os.path.dirname(HERE)
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
STEP = float(opt("--step", 5.0)); EXTRA = 15.5; RPS = ["2", "5", "10", "25", "50", "100", "200", "500"]
seg = gpd.read_file(os.path.join(W10, "gis", "segments_all_rp.gpkg"))
OUT = os.path.join(W10, "gis", "extents"); os.makedirs(OUT, exist_ok=True)

def channel_samples(ch):
    """Centreline samples of one channel at STEP spacing, reaches in order: station, x, y and the unit tangent."""
    pts = []
    for _, r in ch.sort_values("Seg").iterrows():
        ln = r.geometry
        if ln.geom_type == "MultiLineString": ln = linemerge(ln)
        n = max(int(math.ceil(ln.length / STEP)), 1)
        for i in range(n + 1):
            d = min(i * STEP, ln.length); p = ln.interpolate(d)
            if pts and abs(pts[-1][1] - p.x) < 1e-6 and abs(pts[-1][2] - p.y) < 1e-6: continue
            pts.append((float(r["FromSta"]) + d, p.x, p.y))
    P = np.array(pts)
    dx = np.gradient(P[:, 1]); dy = np.gradient(P[:, 2]); L = np.hypot(dx, dy); L[L == 0] = 1.0
    return P[:, 0], P[:, 1], P[:, 2], dx / L, dy / L

def width_profile(ch, k, sta):
    """Bed width at every sample: the designed span at the reach midpoints, linear between consecutive midpoints, constant beyond."""
    ch = ch.sort_values("Seg")
    mids = ((ch["FromSta"].astype(float) + ch["ToSta"].astype(float)) / 2.0).values; spans = ch[f"span_{k}"].astype(float).values
    order = np.argsort(mids)
    return np.interp(sta, mids[order], spans[order])

def ribbon(x, y, tx, ty, half):
    """The ribbon of half-width 'half' (one value per sample) about the sampled centreline: the union of the round-capped buffers
    of the 5 m segments, each at the mean half-width of its two ends. Round caps close the outer side of every bend and a hairpin
    folds onto itself without bow-ties (the quads of the first version left an artefact at the 137-degree bend of SAK-CH5-SS)."""
    pieces = []
    for i in range(len(x) - 1):
        h = 0.5 * (half[i] + half[i + 1])
        if h <= 0: continue
        pieces.append(LineString([(x[i], y[i]), (x[i + 1], y[i + 1])]).buffer(h, quad_segs=8))
    return unary_union(pieces)

for k in RPS:
    beds, cors = [], []
    for name, ch in seg.groupby("Channel"):
        sta, x, y, tx, ty = channel_samples(ch); w = width_profile(ch, k, sta)
        beds.append(ribbon(x, y, tx, ty, w / 2.0)); cors.append(ribbon(x, y, tx, ty, w / 2.0 + EXTRA))
    bed = unary_union(beds); cor = unary_union(cors)
    g = gpd.GeoDataFrame({"kind": ["bed", "corridor"], "rp_years": [int(k), int(k)],
                          "note": [f"designed bed width, {k}-year flow, tapered between the reach midpoints", f"bed + {EXTRA} m each side (embankment and access road), tapered"]},
                         geometry=[bed, cor], crs=seg.crs)
    g.to_file(os.path.join(OUT, f"extent_{k}yr.shp"))
    nb = len(getattr(bed, "geoms", [bed])); nc = len(getattr(cor, "geoms", [cor]))
    print(f"extent_{k}yr: bed {bed.area / 1e4:.0f} ha ({nb} parts), corridor {cor.area / 1e4:.0f} ha ({nc} parts)")
