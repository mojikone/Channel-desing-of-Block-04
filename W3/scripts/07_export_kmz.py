"""Step 07 - KMZ files for Google Earth, as the Block 6 set (28 files), from the step-06 shapefiles.

  All_Layers.kmz      subbasins + reaches + points (named)
  Basins_Reach.kmz    subbasins + reaches; every polygon and reach opens the same table as the points (Q and V, 13 RPs)
  Q_<rp>.kmz          points labelled with the integer peak flow of that return period (13 files)
  V_<rp>.kmz          points labelled with the volume of that return period (13 files)
Styling as Block 6: basins orange outline, reaches blue, points white circle; popups = HTML tables.
usage: python 07_export_kmz.py [B3|B2]   (default B3)   -> W3/elements/kmz/B<b>/
"""
import sys, io, zipfile
from pathlib import Path
import geopandas as gpd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import RPS, RP_LABEL, W3, ensure

B = next((a for a in sys.argv[1:] if a in ("B2", "B3")), "B3"); SHP = W3 / "elements" / "shp" / B; OUT = ensure(W3 / "elements" / "kmz" / B)
def rpf(p, rp): return f"{p}{rp.replace('yr', '')}"
def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
def kml(r, g, b, a=255): return f"{a:02x}{b:02x}{g:02x}{r:02x}"
STYLES = (f'<Style id="basin"><LineStyle><color>{kml(255,102,0)}</color><width>1.2</width></LineStyle><PolyStyle><color>00000000</color><fill>0</fill><outline>1</outline></PolyStyle>'
          '<BalloonStyle><text>$[description]</text></BalloonStyle></Style>\n'
          f'<Style id="reach"><LineStyle><color>{kml(1,98,255)}</color><width>2.0</width></LineStyle><BalloonStyle><text>$[description]</text></BalloonStyle></Style>\n'
          f'<Style id="point"><IconStyle><color>ffffffff</color><scale>0.8</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon></IconStyle>'
          '<LabelStyle><color>ffffffff</color><scale>0.9</scale></LabelStyle><BalloonStyle><text>$[description]</text></BalloonStyle></Style>\n')

def table(rec, extra):
    rows = "".join(f"<tr><td>{RP_LABEL[rp]}</td><td align='right'>{rec[rpf('Q', rp)]:,.1f}</td><td align='right'>{rec[rpf('V', rp)]:,.2f}</td></tr>" for rp in RPS if rec.get(rpf("Q", rp)) is not None)
    info = "".join(f"<tr><td><b>{k}</b></td><td colspan='2'>{esc(v)}</td></tr>" for k, v in extra if v not in (None, "", "nan"))
    return ("<![CDATA[" f"<h3>{esc(rec['name'])}</h3><table border='1' cellpadding='3' cellspacing='0' style='font-family:Arial;font-size:12px'>{info}"
            "<tr><th>Return period</th><th>Peak flow (m³/s)</th><th>Volume (Mm³)</th></tr>" + rows + "</table>"
            f"<p style='font-size:10px;color:#666'>HEC-HMS Block 04, Basin {B[1]}, depth-area analyses, own analysis point</p>]]>")

def coords(seq): return " ".join(f"{x:.6f},{y:.6f},0" for x, y in seq)
def poly_pm(name, desc, geom):
    polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]; body = ""
    for p in polys:
        inner = "".join(f"<innerBoundaryIs><LinearRing><coordinates>{coords(r.coords)}</coordinates></LinearRing></innerBoundaryIs>" for r in p.interiors)
        body += f"<Polygon><outerBoundaryIs><LinearRing><coordinates>{coords(p.exterior.coords)}</coordinates></LinearRing></outerBoundaryIs>{inner}</Polygon>"
    if len(polys) > 1: body = f"<MultiGeometry>{body}</MultiGeometry>"
    return f"<Placemark><name>{esc(name)}</name><description>{desc}</description><styleUrl>#basin</styleUrl>{body}</Placemark>\n"
def line_pm(name, desc, geom):
    lines = geom.geoms if geom.geom_type == "MultiLineString" else [geom]
    body = "".join(f"<LineString><coordinates>{coords(l.coords)}</coordinates></LineString>" for l in lines)
    if len(lines) > 1: body = f"<MultiGeometry>{body}</MultiGeometry>"
    return f"<Placemark><name>{esc(name)}</name><description>{desc}</description><styleUrl>#reach</styleUrl>{body}</Placemark>\n"
def point_pm(label, desc, geom): return f"<Placemark><name>{esc(label)}</name><description>{desc}</description><styleUrl>#point</styleUrl><Point><coordinates>{geom.x:.6f},{geom.y:.6f},0</coordinates></Point></Placemark>\n"
def doc(name, body): return f'<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>{esc(name)}</name>\n{STYLES}{body}</Document></kml>\n'
def write(name, text):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z: z.writestr("doc.kml", text.encode("utf-8"))
    (OUT / name).write_bytes(buf.getvalue())

sub = gpd.read_file(SHP / f"Subbasins_{B}.shp").to_crs(4326); rch = gpd.read_file(SHP / f"Reaches_{B}.shp").to_crs(4326); pts = gpd.read_file(SHP / f"Points_{B}.shp").to_crs(4326)
f_sub = "<Folder><name>Subbasins</name>\n" + "".join(poly_pm(r["name"], table(r, [("Type", "Subbasin"), ("Area (km²)", f"{r['area_km2']:.2f}"), ("Curve number", f"{r['cn']:.1f}"), ("Lag (min)", f"{r['lag_min']:.1f}"), ("Downstream", r["downstream"])]), r.geometry) for _, r in sub.iterrows()) + "</Folder>\n"
f_rch = "<Folder><name>Reaches</name>\n" + "".join(line_pm(r["name"], table(r, [("Type", "Reach"), ("Length (m)", f"{r['length_m']:.0f}"), ("Slope", f"{r['slope']:.5f}"), ("Bottom width (m)", f"{r['bottom_w']:.1f}"), ("Side slope (H:V)", f"{r['side_slope']:.1f}"), ("Manning n", f"{r['manning_n']:.3f}"), ("Downstream", r["downstream"])]), r.geometry) for _, r in rch.iterrows()) + "</Folder>\n"
def f_pts(label_field, folder):
    out = [f"<Folder><name>{esc(folder)}</name>\n"]
    for _, r in pts.iterrows():
        desc = table(r, [("Type", r["type"]), ("Downstream", r["downstream"])])
        label = r["name"] if label_field == "name" else (f"{r[label_field]:,.0f}" if label_field.startswith("Q") else f"{r[label_field]:,.1f}")
        out.append(point_pm(label, desc, r.geometry))
    return "".join(out) + "</Folder>\n"
write("All_Layers.kmz", doc(f"Block 04 {B} - all layers", f_sub + f_rch + f_pts("name", "Points")))
write("Basins_Reach.kmz", doc(f"Block 04 {B} - subbasins and reaches", f_sub + f_rch))
for rp in RPS:
    write(f"Q_{rp}.kmz", doc(f"Peak flow {RP_LABEL[rp]} (m³/s)", f_pts(rpf("Q", rp), f"Q peak - {RP_LABEL[rp]}")))
    write(f"V_{rp}.kmz", doc(f"Volume {RP_LABEL[rp]} (Mm³)", f_pts(rpf("V", rp), f"Volume - {RP_LABEL[rp]}")))
print(B, "->", OUT, "| files:", len(list(OUT.glob("*.kmz"))), "| subbasins", len(sub), "reaches", len(rch), "points", len(pts))
