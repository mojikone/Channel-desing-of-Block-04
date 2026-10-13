"""Step 03 - LandXML 1.2 for Civil 3D: one TIN surface per feature (the triangulated 1 m corridor, triangles outside the
corridor removed, so no interpolation between channels and no sliver across bends), one alignment per feature (named),
and the existing-ground profile of each alignment sampled every 0.5 m from the corridor cells.

  landxml/Block4_channels.xml   37 channel surfaces + alignments (the Civil 3D build creates the dynamic surface profiles)
  landxml/Block4_dykes.xml      36 dyke surfaces + alignments
  landxml/*_with_EG_profiles.xml  the same plus the static existing-ground profiles: the fallback when Civil 3D is driven by hand
  landxml/surfaces_summary.csv  points, triangles, elevation range per surface

Names: surface  "EG <name>", alignment "<name>", profile "EG <name>". Civil 3D: Insert > LandXML, both files; the
surfaces and alignments import by name, the profiles as existing-ground profiles of their alignments.
"""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
from scipy.spatial import Delaunay
import shapely
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_w4 import LINES, POINTS, LANDXML, BUFFER_M

STEP = 0.5      # profile sampling along the centreline, m

def tin(pts, corridor):
    """Delaunay on E,N; keep the triangles whose centroid lies in the corridor polygon"""
    if len(pts) < 3: return np.zeros((0, 3), int)
    tri = Delaunay(pts[:, :2]).simplices; c = pts[tri].mean(axis=1)
    keep = shapely.contains_xy(corridor, c[:, 0], c[:, 1]); return tri[keep]

def profile(line, pts, step=STEP):
    """station, elevation every `step` m: the elevation of the corridor cell nearest to the station point"""
    from scipy.spatial import cKDTree
    st = np.arange(0.0, line.length, step); st = np.append(st, line.length)
    xy = np.array([line.interpolate(s).coords[0] for s in st]); d, i = cKDTree(pts[:, :2]).query(xy)
    return st, pts[i, 2], float(d.max())

def xml_escape(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def write(group, feats, buffers, out, with_profiles=True):
    t0 = time.time(); L = ['<?xml version="1.0" encoding="UTF-8"?>', '<LandXML xmlns="http://www.landxml.org/schema/LandXML-1.2" version="1.2" date="2026-10-07" time="00:00:00" readOnly="false" language="English">',
         '<Units><Metric areaUnit="squareMeter" linearUnit="meter" volumeUnit="cubicMeter" temperatureUnit="celsius" pressureUnit="HPA" angularUnit="decimal degrees" directionUnit="decimal degrees"/></Units>',
         f'<Project name="Block 04 {group}"/><Application name="W4 scripts" desc="Block 04 channel and dyke corridors, 0.5 m DEM" manufacturer="Renardet" version="1" manufacturerURL=""/>', '<CoordinateSystem name="UTM 40N" epsgCode="32640" horizontalDatum="WGS84"/>', "<Surfaces>"]
    rows = []; profs = []
    for r in feats.itertuples():
        pts = pd.read_csv(POINTS / "csv" / f"{r.name}.csv", header=None, names=["P", "E", "N", "Z", "D"])[["E", "N", "Z"]].to_numpy(float)
        tri = tin(pts, buffers[r.name]); st, z, dmax = profile(r.geometry, pts)
        L.append(f'<Surface name="{xml_escape("EG " + r.name)}" desc="{xml_escape(r.kind + " " + r.name + ", 1 m corridor on the 0.5 m DEM")}"><Definition surfType="TIN"><Pnts>')
        L.append("\n".join(f'<P id="{i + 1}">{p[1]:.3f} {p[0]:.3f} {p[2]:.3f}</P>' for i, p in enumerate(pts)))          # LandXML points are N E Z
        L.append("</Pnts><Faces>"); L.append("\n".join(f"<F>{a + 1} {b + 1} {c + 1}</F>" for a, b, c in tri)); L.append("</Faces></Definition></Surface>")
        profs.append((r, st, z)); rows.append(dict(name=r.name, kind=r.kind, points=len(pts), triangles=len(tri), z_min=round(float(pts[:, 2].min()), 2), z_max=round(float(pts[:, 2].max()), 2), profile_samples=len(st), max_cell_distance_m=round(dmax, 2)))
    L.append("</Surfaces><Alignments>")
    for r, st, z in profs:
        c = [q for i, q in enumerate(r.geometry.coords) if i == 0 or abs(q[0] - r.geometry.coords[i - 1][0]) > 0.001 or abs(q[1] - r.geometry.coords[i - 1][1]) > 0.001]   # no zero-length lines (the shapefile repeats vertices)
        L.append(f'<Alignment name="{xml_escape(r.name)}" length="{r.geometry.length:.3f}" staStart="0" desc="{xml_escape(r.kind + " " + r.cls + ", " + r.gca)}"><CoordGeom>')
        L.append("".join(f"<Line><Start>{c[i][1]:.3f} {c[i][0]:.3f}</Start><End>{c[i + 1][1]:.3f} {c[i + 1][0]:.3f}</End></Line>" for i in range(len(c) - 1)))
        if with_profiles:
            L.append(f'</CoordGeom><Profile name="{xml_escape("EG " + r.name)}" staStart="0"><ProfSurf name="{xml_escape("EG " + r.name)}" surfRef="{xml_escape("EG " + r.name)}">')
            L.append(" ".join(f"{s:.2f} {e:.3f}" for s, e in zip(st, z))); L.append("</ProfSurf></Profile></Alignment>")
        else: L.append("</CoordGeom></Alignment>")
    L.append("</Alignments></LandXML>"); Path(out).write_text("\n".join(L), encoding="utf-8")
    print(f"{group}: {len(feats)} surfaces/alignments/profiles -> {out} ({Path(out).stat().st_size / 1e6:.0f} MB) [{time.time() - t0:.0f}s]"); return rows

def main():
    lines = gpd.read_file(LINES / "Block4_lines.gpkg").sort_values("order"); buf = gpd.read_file(POINTS / "Block4_buffers_0.5m.gpkg"); buffers = dict(zip(buf.name, buf.geometry))
    rows = write("channels", lines[lines.kind == "channel"], buffers, LANDXML / "Block4_channels.xml", with_profiles=False) + write("dykes", lines[lines.kind == "dyke"], buffers, LANDXML / "Block4_dykes.xml", with_profiles=False)
    write("channels", lines[lines.kind == "channel"], buffers, LANDXML / "Block4_channels_with_EG_profiles.xml"); write("dykes", lines[lines.kind == "dyke"], buffers, LANDXML / "Block4_dykes_with_EG_profiles.xml")   # the self-contained fallback: static ground profiles included
    pd.DataFrame(rows).to_csv(LANDXML / "surfaces_summary.csv", index=False); print(pd.DataFrame(rows)[["points", "triangles", "max_cell_distance_m"]].describe().round(2).loc[["min", "50%", "max"]])

if __name__ == "__main__":
    main()
