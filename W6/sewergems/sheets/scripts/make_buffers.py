"""Build the two buffer shapefiles the sheet pipeline draws on the plan (Data/SHP/Buffers/Channel Bed Buffer.shp and
Channels Buffer.shp) as ONE dissolved outline each, so adjacent segment buffers never show crossing ends at the joints
(engineer, 2026-10-11: "the channel buffer extents to be dissolved, so the overlapping ends will not be there").

Width source (placeholder until the real bed and corridor are set): the designed width of each segment in the chosen scenario,
read from the bridge export conduits_<scenario>.csv (size_label "depth x width"), mapped by SGLabel onto W6/final/
Block4_design_segments.shp. Every segment is buffered by half its width with FLAT ends; at every inner point (a point that starts
a segment and is also reached by one, i.e. not a channel start, not a channel end or outfall) a disc sized by the wider adjacent
segment rounds the joint; the union of all parts is written as a single MultiPolygon feature.
Corridor = bed + EXTRA m each side; EXTRA = 15.5 m is the engineer's definition (2026-10-12): an embankment on both sides of every
channel, 2.5 m high with 1.5H:1V slopes and a 4 m crest, bottom width 2 x (2.5 x 1.5) + 4 = 11.5 m, plus a 4 m access road.
    python make_buffers.py [--scenario 200yr] [--run run_20261012_0031] [--extra 15.5]
"""
import os, sys
import geopandas as gpd, pandas as pd
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
W6 = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
A = sys.argv[1:]
def opt(k, d): return A[A.index(k) + 1] if k in A else d
SC = opt("--scenario", "200yr"); RUN = opt("--run", "run_20261011_1721"); EXTRA = float(opt("--extra", "15.5"))   # embankment bottom 11.5 m + access road 4 m, each side
S = os.path.join(HERE, "Data", "SHP", "Buffers"); os.makedirs(S, exist_ok=True)

seg = gpd.read_file(os.path.join(W6, "final", "Block4_design_segments.shp"))
pts = gpd.read_file(os.path.join(W6, "final", "Block4_design_points.shp")).set_index("Label")
c = pd.read_csv(os.path.join(W6, "sewergems", "results", RUN, "bridge_exports", "conduits_%s.csv" % SC))
w = dict(zip(c["label"], c["size_label"].str.extract(r"x\s*([\d.]+)")[0].astype(float)))      # "2.5 x 29" -> 29.0 m
seg["Width_m"] = seg["SGLabel"].map(w)
missing = seg[seg["Width_m"].isna()]["SGLabel"].tolist()
if missing: sys.exit("no designed width for %d segments: %s" % (len(missing), ", ".join(missing[:10])))
starts = set(seg.groupby("Channel")["FromNode"].first()); tos = set(seg["ToNode"]); froms = set(seg["FromNode"])


def dissolved(extra):
    parts = [s.geometry.buffer(s["Width_m"] / 2 + extra, cap_style=2) for _, s in seg.iterrows()]     # flat ends
    for lab in froms | tos:                                                                            # round joints at inner points
        if lab in starts and lab not in tos: continue                                                  # a channel start: keep the flat end
        if lab not in froms: continue                                                                  # a channel end or outfall: flat
        wmax = seg[(seg["FromNode"] == lab) | (seg["ToNode"] == lab)]["Width_m"].max() / 2 + extra
        parts.append(pts.loc[lab].geometry.buffer(wmax))
    return unary_union(parts)


bed = dissolved(0.0); cor = dissolved(EXTRA)
crs = seg.crs or "EPSG:32640"
gpd.GeoDataFrame({"Layer": ["bed = designed span, %s, dissolved" % SC]}, geometry=[bed], crs=crs).to_file(os.path.join(S, "Channel Bed Buffer.shp"))
gpd.GeoDataFrame({"Layer": ["corridor = span + %g m each side (embankment 11.5 + road 4), dissolved" % EXTRA]}, geometry=[cor], crs=crs).to_file(os.path.join(S, "Channels Buffer.shp"))
def n(g): return len(getattr(g, "geoms", [g]))
print("bed: %s, %d parts, %.2f km2 | corridor: %s, %d parts, %.2f km2 -> %s" % (bed.geom_type, n(bed), bed.area / 1e6, cor.geom_type, n(cor), cor.area / 1e6, S))
