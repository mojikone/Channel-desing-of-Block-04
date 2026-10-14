"""Step 80 (W8) - KMZ files for Google Earth (engineer, 2026-10-13): the channels and dykes in the agreed colours with their names,
their extents (designed bed, corridor), the design points, the dam axes with the FSL and crest reservoir polygons, the existing
culverts of the Batinah inventory on the plain and the proposed box culverts at the road crossings. One KMZ per theme and one
with everything, in W8/kmz/. Plain KML written here (no library), EPSG:32640 -> WGS 84 with pyproj, geometries clamped to ground.
Lines carry no label in Google Earth, so every channel, dyke and dam axis also gets an invisible placemark at its midpoint that
shows the name."""
import os, io, re, zipfile, math
import geopandas as gpd, pandas as pd
from shapely.geometry import LineString, MultiLineString, Polygon, MultiPolygon, Point
from shapely.ops import transform
from pyproj import Transformer
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__)); W8 = os.path.dirname(HERE); CB04 = os.path.dirname(W8); B4 = os.path.dirname(CB04); W3 = os.path.join(CB04, "W3"); W6 = os.path.join(CB04, "W6"); W7 = os.path.join(CB04, "W7")
W = "W:/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/06-WORKING/"
SRC = {"channels": os.path.join(B4, "Hydrology", "SHP", "temp", "Channels and Dykes 04102026.shp"),
       "qml": os.path.join(W3, "maps", "styles", "channels_dykes.qml"),
       "bed": os.path.join(W8, "sewergems", "sheets", "scripts", "Data", "SHP", "Buffers", "Channel Bed Buffer.shp"),
       "corridor": os.path.join(W8, "sewergems", "sheets", "scripts", "Data", "SHP", "Buffers", "Channels Buffer.shp"),
       "points": os.path.join(W6, "final", "Block4_design_points.shp"),
       "dam_axis": os.path.join(B4, "Hydrology", "SHP", "Block 4 Dams", "Dams updated.shp"),
       "fsl": W + "04-Hydraulic/05 Small Tasks/18 Channel Design/SHP/Block 04 Dams/Polygon_FSL.shp",
       "crest": W + "04-Hydraulic/05 Small Tasks/18 Channel Design/SHP/Block 04 Dams/Ppygon_Crest_Level.shp",
       "culv_exist": W + "04-Hydraulic/05 Small Tasks/18 Channel Design/Master Plan Map/Data for Master Plan/SHP/Culverts/Existing Culverts Batinah/Culverts_2_4.shp",
       "crossings": os.path.join(W8, "culverts", "crossings.gpkg")}
OUT = os.path.join(W8, "kmz"); os.makedirs(OUT, exist_ok=True)
T = Transformer.from_crs("EPSG:32640", "EPSG:4326", always_xy=True)
to_wgs = lambda g: transform(T.transform, g)
CHNAMES = {"FP CH": "Flood protection channel", "Sw M CH": "Stormwater main channel", "Sw S CH": "Stormwater secondary channel", "FP D": "Flood protection dyke", "Sw M D": "Stormwater main dyke", "Sw S D": "Stormwater secondary dyke"}

# ------------------------------------------------------------------ the agreed colours from the QML (symbol index -> line colour, width)
def agreed_colours():
    """category value -> (rgba, width mm) from the QML's categorized renderer (ElementTree: the symbol's first line layer)."""
    import xml.etree.ElementTree as ET
    root = ET.parse(SRC["qml"]).getroot(); cats = {c.get("symbol"): c.get("value") for c in root.iter("category")}; out = {}
    for sym in root.find("renderer-v2").find("symbols").findall("symbol"):
        val = cats.get(sym.get("name"))
        if val in (None, "", "NULL"): continue
        opts = {o.get("name"): o.get("value") for o in sym.find("layer").iter("Option") if o.get("name") in ("line_color", "line_width")}
        rgba = [int(float(v)) for v in opts.get("line_color", "0,0,0,255").split(",")[:4]]; out[val] = (rgba, float(opts.get("line_width", "0.5")))
    return out
def kml_colour(rgba, alpha=None):
    r, g, b = rgba[:3]; a = 255 if alpha is None else alpha; return "%02x%02x%02x%02x" % (a, b, g, r)

# ------------------------------------------------------------------ KML pieces
def coords(geom):
    return " ".join("%.7f,%.7f,0" % (x, y) for x, y in geom.coords)
def geom_kml(g):
    g = to_wgs(g)
    if g.geom_type == "Point": return "<Point><coordinates>%s</coordinates></Point>" % coords(g)
    if g.geom_type == "LineString": return "<LineString><tessellate>1</tessellate><coordinates>%s</coordinates></LineString>" % coords(g)
    if g.geom_type == "MultiLineString": return "<MultiGeometry>%s</MultiGeometry>" % "".join("<LineString><tessellate>1</tessellate><coordinates>%s</coordinates></LineString>" % coords(p) for p in g.geoms)
    if g.geom_type == "Polygon":
        inner = "".join("<innerBoundaryIs><LinearRing><coordinates>%s</coordinates></LinearRing></innerBoundaryIs>" % coords(r) for r in g.interiors)
        return "<Polygon><tessellate>1</tessellate><outerBoundaryIs><LinearRing><coordinates>%s</coordinates></LinearRing></outerBoundaryIs>%s</Polygon>" % (coords(g.exterior), inner)
    if g.geom_type == "MultiPolygon": return "<MultiGeometry>%s</MultiGeometry>" % "".join(geom_kml_wgs(p) for p in g.geoms)
    raise ValueError(g.geom_type)
def geom_kml_wgs(g):   # already in WGS 84 (parts of a multipolygon)
    inner = "".join("<innerBoundaryIs><LinearRing><coordinates>%s</coordinates></LinearRing></innerBoundaryIs>" % coords(r) for r in g.interiors)
    return "<Polygon><tessellate>1</tessellate><outerBoundaryIs><LinearRing><coordinates>%s</coordinates></LinearRing></outerBoundaryIs>%s</Polygon>" % (coords(g.exterior), inner)
def table(rows): return "<![CDATA[<table border='0' cellpadding='2'>%s</table>]]>" % "".join("<tr><td><b>%s</b></td><td>%s</td></tr>" % (escape(str(k)), escape(str(v))) for k, v in rows if v is not None and str(v) not in ("", "nan", "None"))
def placemark(name, style, g, desc_rows=(), visible=True):
    return "<Placemark><name>%s</name>%s<styleUrl>#%s</styleUrl>%s%s</Placemark>" % (escape(str(name)), "" if visible else "<visibility>0</visibility>", style, ("<description>%s</description>" % table(desc_rows)) if desc_rows else "", geom_kml(g))
def label_mark(name, g, style="lbl"):
    mid = g.interpolate(0.5, normalized=True) if g.geom_type == "LineString" else (max(g.geoms, key=lambda p: p.length).interpolate(0.5, normalized=True) if g.geom_type == "MultiLineString" else g.representative_point())
    return "<Placemark><name>%s</name><styleUrl>#%s</styleUrl>%s</Placemark>" % (escape(str(name)), style, geom_kml(mid))
def line_style(sid, colour, width): return "<Style id='%s'><LineStyle><color>%s</color><width>%s</width></LineStyle><LabelStyle><scale>0.8</scale></LabelStyle></Style>" % (sid, colour, width)
def poly_style(sid, fill, outline, width=1.5, filled=True): return "<Style id='%s'><LineStyle><color>%s</color><width>%s</width></LineStyle><PolyStyle><color>%s</color><fill>%d</fill><outline>1</outline></PolyStyle></Style>" % (sid, outline, width, fill, 1 if filled else 0)
def point_style(sid, colour, scale=0.9, icon="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png", label_scale=0.8): return "<Style id='%s'><IconStyle><color>%s</color><scale>%s</scale><Icon><href>%s</href></Icon></IconStyle><LabelStyle><scale>%s</scale></LabelStyle></Style>" % (sid, colour, scale, icon, label_scale)
LABEL_STYLE = "<Style id='lbl'><IconStyle><scale>0</scale></IconStyle><LabelStyle><color>ffffffff</color><scale>0.9</scale></LabelStyle></Style><Style id='lbl_dam'><IconStyle><scale>0</scale></IconStyle><LabelStyle><color>ffff00ff</color><scale>1.0</scale></LabelStyle></Style>"
def folder(name, items, open_=1): return "<Folder><name>%s</name><open>%d</open>%s</Folder>" % (escape(name), open_, "".join(items))
def document(name, styles, folders, desc=""):
    return ('<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>%s</name><open>1</open>%s%s%s</Document></kml>'
            % (escape(name), ("<description>%s</description>" % escape(desc)) if desc else "", "".join(styles), "".join(folders)))
def write_kmz(path, kml):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z: z.writestr("doc.kml", kml)
    print("  %s  %.2f MB" % (os.path.basename(path), os.path.getsize(path) / 1e6))

# ------------------------------------------------------------------ themes
def theme_channels():
    g = gpd.read_file(SRC["channels"]); g = g[g["Block"] == 4].copy(); cols = agreed_colours(); styles = [LABEL_STYLE]; folders = []
    for cls, (rgba, w) in cols.items(): styles.append(line_style("c_" + re.sub(r"\W", "_", cls), kml_colour(rgba), max(2, round(w * 3))))
    for cls in ("FP CH", "Sw M CH", "Sw S CH", "FP D", "Sw M D", "Sw S D"):
        sub = g[g["CHtt"] == cls]
        if sub.empty: continue
        items = [placemark(r["Name"], "c_" + re.sub(r"\W", "_", cls), r.geometry, [("Name", r["Name"]), ("Class", CHNAMES[cls]), ("Length", "%.0f m" % r.geometry.length)]) for _, r in sub.iterrows()]
        labels = [label_mark(r["Name"], r.geometry) for _, r in sub.iterrows()]
        folders.append(folder(CHNAMES[cls] + "s (%d)" % len(sub), items + [folder("Names", labels, 0)]))
    return document("Block 04 — channels and dykes", styles, folders, "Flood protection channels and dykes, stormwater main and secondary channels and dykes; the agreed colours of the project maps"), len(g)
def theme_extents():
    bed = gpd.read_file(SRC["bed"]); cor = gpd.read_file(SRC["corridor"])
    styles = [poly_style("bed", kml_colour([255, 215, 0], 110), kml_colour([255, 215, 0]), 1.0), poly_style("cor", kml_colour([139, 69, 19], 40), kml_colour([139, 69, 19]), 2.0)]
    f1 = folder("Designed bed (200-year flow)", [placemark("Channel bed", "bed", r.geometry, [("Extent", "designed bed width, 200-year flow")]) for _, r in bed.iterrows()])
    f2 = folder("Corridor (bed, embankments and access roads)", [placemark("Channel corridor", "cor", r.geometry, [("Extent", "bed + 15.5 m each side: embankment 11.5 m and access road 4 m")]) for _, r in cor.iterrows()])
    return document("Block 04 — channel extents", styles, [f1, f2]), len(bed) + len(cor)
def theme_points():
    p = gpd.read_file(SRC["points"]); styles = [point_style("pt", kml_colour([0, 229, 160])), point_style("pt_out", kml_colour([255, 80, 80]))]
    def rows(r):
        return [("Label", r["Label"]), ("Channel", r["Channel"]), ("Class", r["Class"]), ("Station", r["StaLbl"]), ("Ground level", "%.2f m" % r["Ground"] if pd.notna(r["Ground"]) else None), ("Design point", r["GDP"]),
                ("Inflow (HEC-HMS element)", r["Flow"]), ("Q200", "%.1f m³/s" % r["Q200"] if pd.notna(r["Q200"]) else None), ("Q100", "%.1f m³/s" % r["Q100"] if pd.notna(r["Q100"]) else None),
                ("Fix", r["Fix"]), ("Fix type", r["FixType"]), ("Outfall", r["Outfall"]), ("Model label", r["SGLabel"]), ("Raise", r["Raise"])]
    items = [placemark(r["Label"], "pt_out" if str(r.get("Outfall", "")) not in ("", "nan", "None") else "pt", r.geometry, rows(r)) for _, r in p.iterrows()]
    return document("Block 04 — design points", styles, [folder("Design points (%d)" % len(p), items)], "The design points of the channels: inflow points, junctions, outfalls, with the design flows"), len(p)
def theme_dams():
    ax = gpd.read_file(SRC["dam_axis"]); fsl = gpd.read_file(SRC["fsl"]); cr = gpd.read_file(SRC["crest"])
    styles = [LABEL_STYLE, line_style("axis", kml_colour([255, 0, 255]), 5), poly_style("fsl", kml_colour([0, 112, 192], 100), kml_colour([0, 112, 192]), 1.5), poly_style("crest", kml_colour([192, 0, 0], 0), kml_colour([192, 0, 0]), 2.0, filled=False)]
    DAM_LABEL = {"Hawasinah EX": "Hawasinah UP", "Sakhin 08": "Sakhin 08 (Mehmum)"}
    nm = lambda r: DAM_LABEL.get(r.get("Dam Name", r.get("Dam_Name")), r.get("Dam Name", r.get("Dam_Name")))
    rows = lambda r: [("Dam", nm(r)), ("Crest level", "%s m" % r.get("Crest El", r.get("Crest_El"))), ("Full supply level", "%s m" % r["FSL"]), ("Reservoir at FSL", "%s Mm³" % r["Reservoir"]), ("Maximum height", "%s m" % r["Hmax"]), ("Spillway length", "%s m" % r.get("Spillway L", r.get("Spillway_L")))]
    f1 = folder("Dam axes", [placemark(nm(r), "axis", r.geometry, rows(r)) for _, r in ax.iterrows()] + [folder("Names", [label_mark(nm(r), r.geometry, "lbl_dam") for _, r in ax.iterrows()], 0)])
    f2 = folder("Reservoir at full supply level", [placemark("%s — FSL %s m" % (nm(r), r["FSL"]), "fsl", r.geometry, rows(r)) for _, r in fsl.iterrows()])
    f3 = folder("Reservoir at crest level", [placemark("%s — crest %s m" % (nm(r), r.get("Crest El", r.get("Crest_El"))), "crest", r.geometry, rows(r)) for _, r in cr.iterrows()])
    return document("Block 04 — dams", styles, [f1, f2, f3]), len(ax) + len(fsl) + len(cr)
def theme_culverts():
    cr = gpd.read_file(SRC["crossings"], layer="crossings"); ex = gpd.read_file(SRC["culv_exist"]).to_crs(32640)
    ch = gpd.read_file(SRC["channels"]); ch = ch[ch["Block"] == 4]; env = ch.total_bounds; pad = 5000
    ex = ex.cx[env[0] - pad: env[2] + pad, env[1] - pad: env[3] + pad]
    styles = [point_style("prop", kml_colour([255, 128, 0]), 1.1, "http://maps.google.com/mapfiles/kml/shapes/square.png"), point_style("exist", kml_colour([0, 176, 240]), 0.7, label_scale=0.0)]
    f1 = folder("Proposed box culverts at the road crossings (%d)" % len(cr), [placemark("%s — %s" % (r["channel"], r["road"]), "prop", r.geometry,
          [("Road", r["road"]), ("Channel", r["channel"]), ("Station", "%.0f m" % r["station_m"]), ("Q200", "%.0f m³/s" % r["Q200"] if pd.notna(r["Q200"]) else None), ("Channel width x depth", "%s x %s m" % (r["channel_width_m"], r["channel_depth_m"])),
           ("Cells", "%s x %s x %s m" % (r["cells"], r["cell_width_m"], r["cell_height_m"])), ("Overall width", "%s m" % r["overall_width_m"]), ("Length", "%s m" % r["length_m"]), ("Slope", r["slope"]), ("Headwater / height", r["HW_over_D"]), ("Existing structure within 10 m", r["existing_type"]), ("Existing size", r["existing_size"]), ("Cost", "%.2f million OMR" % r["cost_mOMR"] if pd.notna(r["cost_mOMR"]) else None)]) for _, r in cr.iterrows()])
    f2 = folder("Existing culverts of the Batinah inventory (%d barrels)" % len(ex), [placemark(str(r.get("Code", "")) or "culvert", "exist", r.geometry, [(c, r[c]) for c in ("Num", "W", "H", "Size", "Code", "L") if c in ex.columns]) for _, r in ex.iterrows()], 0)
    return document("Block 04 — culverts", styles, [f1, f2], "Proposed box culverts of the channel scheme at the Batinah Highway and Coastal Road crossings; the existing culvert inventory on the plain"), len(cr) + len(ex)

if __name__ == "__main__":
    docs = {}
    for key, fn in (("channels_dykes", theme_channels), ("extents", theme_extents), ("design_points", theme_points), ("dams", theme_dams), ("culverts", theme_culverts)):
        kml, n = fn(); print(key, n, "features"); docs[key] = kml; write_kmz(os.path.join(OUT, "Block04_%s.kmz" % key), kml)
    # everything in one file: the documents' folders and styles merged
    styles, folders = [], []
    for key, kml in docs.items():
        body = kml.split("<Document>", 1)[1].rsplit("</Document>", 1)[0]; name = re.search(r"<name>(.*?)</name>", body).group(1)
        st = "".join(re.findall(r"<Style id='[^']*'>.*?</Style>", body)); fo = re.sub(r"<Style id='[^']*'>.*?</Style>", "", body); fo = re.sub(r"^<name>.*?</name><open>1</open>(<description>.*?</description>)?", "", fo)
        if st not in styles: styles.append(st)
        folders.append(folder(name.replace("Block 04 — ", ""), [fo]))
    write_kmz(os.path.join(OUT, "Block04_all.kmz"), document("Block 04 — channel scheme", styles, folders))
    print("done ->", OUT)
