"""Step 06 - the build specification for the Civil 3D drawing (civil3d/build_spec.json): per feature the surface name and
strip, the corridor ring as the surface's outer boundary, the alignment vertices and site, the profile and profile view
names and the view insertion point (from step 04). The Civil 3D build (MCP plugin calls) reads this file."""
import sys, json
from pathlib import Path
import geopandas as gpd, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_w4 import LINES, POINTS, C3D
lines = gpd.read_file(LINES / "Block4_lines.gpkg").sort_values("order"); buf = gpd.read_file(POINTS / "Block4_buffers_0.5m.gpkg").set_index("name"); pv = pd.read_csv(C3D / "profile_views.csv").set_index("name")
def dedupe(pts, tol=0.001):
    """drop consecutive duplicate vertices: the channel shapefile repeats vertices, and a zero-length fixed line is rejected by Civil 3D"""
    out = [pts[0]]
    for q in pts[1:]:
        if abs(q["x"] - out[-1]["x"]) > tol or abs(q["y"] - out[-1]["y"]) > tol: out.append(q)
    return out
spec = []
for r in lines.itertuples():
    ring = list(buf.loc[r.name, "geometry"].simplify(0.02).exterior.coords)[:-1]
    spec.append(dict(name=r.name, kind=r.kind, cls=r.cls, gca=r.gca, length_m=r.length_m, surface=f"EG {r.name}", strip=str(POINTS / "strips" / f"{r.name}.tif"),
                     boundary=[dict(x=round(x, 3), y=round(y, 3)) for x, y in ring], site="Channels" if r.kind == "channel" else "Dykes",
                     alignment=dedupe([dict(x=round(x, 3), y=round(y, 3)) for x, y in r.geometry.coords]), profile=f"EG {r.name}", view=f"PV {r.name}",
                     insertX=float(pv.loc[r.name, "insertX"]), insertY=float(pv.loc[r.name, "insertY"])))
json.dump(spec, open(C3D / "build_spec.json", "w"), indent=0)
print(len(spec), "features; boundary points", min(len(s["boundary"]) for s in spec), "-", max(len(s["boundary"]) for s in spec), "; alignment vertices", min(len(s["alignment"]) for s in spec), "-", max(len(s["alignment"]) for s in spec))
