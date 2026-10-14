"""Step 84 (W9, engineer 2026-10-14) - the HEC-HMS model of record (Basin 6) for Google Earth, as the earlier element KMZ: the
subbasins (orange outline), the reaches (blue), the junctions and outfalls (white circles) labelled with the 200-year peak flow;
every element opens a table with its data and the peak flow and volume of all return periods. The junction labels sit in a
Region so they appear only when zoomed in (legibility). Writes W9/kmz/Block04_HEC-HMS_model.kmz and returns the folder XML for
the all-in-one file through hms_folders()."""
import os, io, zipfile
import geopandas as gpd
from xml.sax.saxutils import escape as esc
HERE = os.path.dirname(os.path.abspath(__file__)); W9 = os.path.dirname(HERE); CB = os.path.dirname(W9); W7 = os.path.join(CB, "W7")
SHP = os.path.join(W7, "elements", "shp", "B6"); OUT = os.path.join(W9, "kmz"); os.makedirs(OUT, exist_ok=True)
RPS = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr", "1000yr", "2000yr", "5000yr", "10000yr", "PMP"]
LAB = {rp: (rp.replace("yr", "-year") if rp != "PMP" else "PMP") for rp in RPS}
def kml(r, g, b, a=255): return f"{a:02x}{b:02x}{g:02x}{r:02x}"
STYLES = (f'<Style id="basin"><LineStyle><color>{kml(255,102,0)}</color><width>1.2</width></LineStyle><PolyStyle><color>00000000</color><fill>0</fill><outline>1</outline></PolyStyle><BalloonStyle><text>$[description]</text></BalloonStyle></Style>'
          f'<Style id="reach"><LineStyle><color>{kml(1,98,255)}</color><width>2.0</width></LineStyle><BalloonStyle><text>$[description]</text></BalloonStyle></Style>'
          f'<Style id="jct"><IconStyle><color>ffffffff</color><scale>0.6</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon></IconStyle><LabelStyle><scale>0</scale></LabelStyle><BalloonStyle><text>$[description]</text></BalloonStyle></Style>'
          f'<Style id="jctlab"><IconStyle><scale>0</scale></IconStyle><LabelStyle><color>ffffffff</color><scale>0.8</scale></LabelStyle></Style>'
          f'<Style id="res"><IconStyle><color>{kml(255,0,255)}</color><scale>0.9</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/triangle.png</href></Icon></IconStyle><LabelStyle><scale>0</scale></LabelStyle><BalloonStyle><text>$[description]</text></BalloonStyle></Style>')
def table(rec, extra):
    rows = "".join(f"<tr><td>{LAB[rp]}</td><td align='right'>{float(rec['Q' + rp.replace('yr', '')]):,.1f}</td><td align='right'>{float(rec['V' + rp.replace('yr', '')]):,.2f}</td></tr>"
                   for rp in RPS if ("Q" + rp.replace("yr", "")) in rec and ("V" + rp.replace("yr", "")) in rec and rec["Q" + rp.replace("yr", "")] is not None)
    info = "".join(f"<tr><td><b>{esc(str(k))}</b></td><td colspan='2'>{esc(str(v))}</td></tr>" for k, v in extra if v not in (None, "", "nan"))
    return ("<![CDATA[" f"<h3>{esc(str(rec['name']))}</h3><table border='1' cellpadding='3' cellspacing='0' style='font-family:Arial;font-size:12px'>{info}"
            "<tr><th>Return period</th><th>Peak flow (m³/s)</th><th>Volume (Mm³)</th></tr>" + rows + "</table>"
            "<p style='font-size:10px;color:#666'>HEC-HMS model of Block 04, dams in place, depth-area analyses</p>]]>")
def coords(seq): return " ".join(f"{x:.6f},{y:.6f},0" for x, y in seq)
def region(x, y, half=0.004, min_px=140):   # label visible once the ±half-degree box spans min_px pixels
    return f"<Region><LatLonAltBox><north>{y + half:.5f}</north><south>{y - half:.5f}</south><east>{x + half:.5f}</east><west>{x - half:.5f}</west></LatLonAltBox><Lod><minLodPixels>{min_px}</minLodPixels><maxLodPixels>-1</maxLodPixels></Lod></Region>"
def poly_pm(name, desc, geom):
    polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]; body = ""
    for p in polys:
        inner = "".join(f"<innerBoundaryIs><LinearRing><coordinates>{coords(r.coords)}</coordinates></LinearRing></innerBoundaryIs>" for r in p.interiors)
        body += f"<Polygon><outerBoundaryIs><LinearRing><coordinates>{coords(p.exterior.coords)}</coordinates></LinearRing></outerBoundaryIs>{inner}</Polygon>"
    if len(polys) > 1: body = f"<MultiGeometry>{body}</MultiGeometry>"
    return f"<Placemark><name>{esc(name)}</name><description>{desc}</description><styleUrl>#basin</styleUrl>{body}</Placemark>\n"
def line_pm(name, desc, geom):
    lines = geom.geoms if geom.geom_type == "MultiLineString" else [geom]
    body = "".join(f"<LineString><tessellate>1</tessellate><coordinates>{coords(l.coords)}</coordinates></LineString>" for l in lines)
    if len(lines) > 1: body = f"<MultiGeometry>{body}</MultiGeometry>"
    return f"<Placemark><name>{esc(name)}</name><description>{desc}</description><styleUrl>#reach</styleUrl>{body}</Placemark>\n"
def hms_folders():
    sub = gpd.read_file(os.path.join(SHP, "Subbasins_B6.shp")).to_crs(4326); rch = gpd.read_file(os.path.join(SHP, "Reaches_B6.shp")).to_crs(4326); pts = gpd.read_file(os.path.join(SHP, "Points_B6.shp")).to_crs(4326)
    f_sub = "<Folder><name>Subbasins</name><open>0</open>" + "".join(poly_pm(r["name"], table(r, [("Type", "Subbasin"), ("Area (km²)", f"{float(r['area_km2']):.2f}"), ("Curve number", f"{float(r['cn']):.1f}"), ("Lag (min)", f"{float(r['lag_min']):.1f}"), ("Downstream", r["downstream"])]), r.geometry) for _, r in sub.iterrows()) + "</Folder>"
    f_rch = "<Folder><name>Reaches</name><open>0</open>" + "".join(line_pm(r["name"], table(r, [("Type", "Reach"), ("Length (m)", f"{float(r['length_m']):.0f}"), ("Slope", f"{float(r['slope']):.5f}"), ("Bottom width (m)", f"{float(r['bottom_w']):.1f}"), ("Side slope (H:V)", f"{float(r['side_slope']):.1f}"), ("Manning n", f"{float(r['manning_n']):.3f}"), ("Downstream", r["downstream"])]), r.geometry) for _, r in rch.iterrows()) + "</Folder>"
    jp, jl = [], []
    for _, r in pts.iterrows():
        sty = "res" if str(r["type"]).lower().startswith("reserv") else "jct"; desc = table(r, [("Type", r["type"]), ("Downstream", r["downstream"])])
        jp.append(f"<Placemark><name>{esc(str(r['name']))}</name><description>{desc}</description><styleUrl>#{sty}</styleUrl><Point><coordinates>{r.geometry.x:.6f},{r.geometry.y:.6f},0</coordinates></Point></Placemark>")
        q = r["Q200"]
        if q is not None and str(q) != "nan":
            jl.append(f"<Placemark><name>{float(q):,.0f}</name>{region(r.geometry.x, r.geometry.y)}<styleUrl>#jctlab</styleUrl><Point><coordinates>{r.geometry.x:.6f},{r.geometry.y:.6f},0</coordinates></Point></Placemark>")
    f_pts = "<Folder><name>Junctions, outfalls and reservoirs (click for the flows and volumes)</name><open>0</open>" + "".join(jp) + "</Folder>"
    f_lab = "<Folder><name>200-year peak flow at the junctions (m³/s), visible when zoomed in</name><open>0</open>" + "".join(jl) + "</Folder>"
    return STYLES, f"<Folder><name>HEC-HMS model (dams in place)</name><open>0</open>{f_sub}{f_rch}{f_pts}{f_lab}</Folder>", (len(sub), len(rch), len(pts))
if __name__ == "__main__":
    styles, folder, n = hms_folders()
    doc = f'<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Block 04 - HEC-HMS model</name><open>1</open>{styles}{folder}</Document></kml>'
    with zipfile.ZipFile(os.path.join(OUT, "Block04_HEC-HMS_model.kmz"), "w", zipfile.ZIP_DEFLATED) as z: z.writestr("doc.kml", doc)
    print("HEC-HMS kmz: subbasins %d, reaches %d, points %d ->" % n, OUT)
