"""Step 80 (W9, engineer 2026-10-14) - the KMZ files for Google Earth, legible for the client: every label sits in a Region so it
appears only when zoomed in (channel and dyke names along the alignments, smaller; reach sizes; dam names in white; culvert sizes);
the bed as a fill only and the corridor as an outline only; the dyke extent; the design points as very small dots without a label;
the existing culverts as lines; the proposed culverts as small circles; the HEC-HMS model (step 84) with its popups. One KMZ per
theme and the all-in-one Block04_all.kmz. Plain KML, WGS 84, the agreed colours from the project QML."""
import os, io, re, zipfile, math
import geopandas as gpd, pandas as pd
from shapely.ops import transform
from pyproj import Transformer
from xml.sax.saxutils import escape
HERE = os.path.dirname(os.path.abspath(__file__)); W9 = os.path.dirname(HERE); CB = os.path.dirname(W9); B4 = os.path.dirname(CB); W3 = os.path.join(CB, "W3"); W6 = os.path.join(CB, "W6"); W7 = os.path.join(CB, "W7")
W = "W:/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/06-WORKING/"
SRC = {"channels": os.path.join(B4, "Hydrology", "SHP", "temp", "Channels and Dykes 04102026.shp"), "qml": os.path.join(W3, "maps", "styles", "channels_dykes.qml"),
       "segments": os.path.join(W9, "gis", "segments_all_rp.gpkg"), "extent200": os.path.join(W9, "gis", "extents", "extent_200yr.shp"), "dyke_extent": os.path.join(W9, "gis", "dyke_extent.shp"),
       "points": os.path.join(W6, "final", "Block4_design_points.shp"), "dam_axis": os.path.join(B4, "Hydrology", "SHP", "Block 4 Dams", "Dams updated.shp"),
       "fsl": W + "04-Hydraulic/05 Small Tasks/18 Channel Design/SHP/Block 04 Dams/Polygon_FSL.shp", "crest": W + "04-Hydraulic/05 Small Tasks/18 Channel Design/SHP/Block 04 Dams/Ppygon_Crest_Level.shp",
       "culv_exist": W + "04-Hydraulic/05 Small Tasks/18 Channel Design/Master Plan Map/Data for Master Plan/SHP/Culverts/Existing Culverts Batinah/Culverts_2_4.shp", "crossings": os.path.join(W9, "culverts", "crossings.gpkg")}
OUT = os.path.join(W9, "kmz"); os.makedirs(OUT, exist_ok=True)
T = Transformer.from_crs("EPSG:32640", "EPSG:4326", always_xy=True); to_wgs = lambda g: transform(T.transform, g)
CHNAMES = {"FP CH": "Flood protection channel", "Sw M CH": "Stormwater main channel", "Sw S CH": "Stormwater secondary channel", "FP D": "Flood protection dyke", "Sw M D": "Stormwater main dyke", "Sw S D": "Stormwater secondary dyke"}
DAM_LABEL = {"Hawasinah EX": "Hawasinah UP", "Sakhin 08": "Sakhin 08 (Mehmum)"}
# label visibility: a label placemark carries a Region of ±HALF degrees around its anchor and shows once that box spans MIN_PX pixels
LOD = {"name": (0.004, 110), "reach": (0.003, 220), "culvert": (0.003, 160), "dam": (0.006, 90)}

def agreed_colours():
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
def coords(geom): return " ".join("%.7f,%.7f,0" % (x, y) for x, y in geom.coords)
def geom_kml(g):
    g = to_wgs(g)
    if g.geom_type == "Point": return "<Point><coordinates>%s</coordinates></Point>" % coords(g)
    if g.geom_type == "LineString": return "<LineString><tessellate>1</tessellate><coordinates>%s</coordinates></LineString>" % coords(g)
    if g.geom_type == "MultiLineString": return "<MultiGeometry>%s</MultiGeometry>" % "".join("<LineString><tessellate>1</tessellate><coordinates>%s</coordinates></LineString>" % coords(p) for p in g.geoms)
    if g.geom_type == "Polygon": return _poly(g)
    if g.geom_type == "MultiPolygon": return "<MultiGeometry>%s</MultiGeometry>" % "".join(_poly(p) for p in g.geoms)
    raise ValueError(g.geom_type)
def _poly(p):
    inner = "".join("<innerBoundaryIs><LinearRing><coordinates>%s</coordinates></LinearRing></innerBoundaryIs>" % coords(r) for r in p.interiors)
    return "<Polygon><tessellate>1</tessellate><outerBoundaryIs><LinearRing><coordinates>%s</coordinates></LinearRing></outerBoundaryIs>%s</Polygon>" % (coords(p.exterior), inner)
def table(rows): return "<![CDATA[<table border='0' cellpadding='2'>%s</table>]]>" % "".join("<tr><td><b>%s</b></td><td>%s</td></tr>" % (escape(str(k)), escape(str(v))) for k, v in rows if v is not None and str(v) not in ("", "nan", "None"))
def placemark(name, style, g, desc_rows=(), show_name=True):
    return "<Placemark><name>%s</name><styleUrl>#%s</styleUrl>%s%s</Placemark>" % (escape(str(name)), style, ("<description>%s</description>" % table(desc_rows)) if desc_rows else "", geom_kml(g)) if show_name else \
           "<Placemark><styleUrl>#%s</styleUrl>%s%s</Placemark>" % (style, ("<description>%s</description>" % table(desc_rows)) if desc_rows else "", geom_kml(g))
def region(pt_wgs, kind):
    half, px = LOD[kind]; x, y = pt_wgs.x, pt_wgs.y
    return "<Region><LatLonAltBox><north>%.5f</north><south>%.5f</south><east>%.5f</east><west>%.5f</west></LatLonAltBox><Lod><minLodPixels>%d</minLodPixels><maxLodPixels>-1</maxLodPixels></Lod></Region>" % (y + half, y - half, x + half, x - half, px)
def label_mark(name, g, style, kind):
    mid = g.interpolate(0.5, normalized=True) if g.geom_type == "LineString" else (max(g.geoms, key=lambda p: p.length).interpolate(0.5, normalized=True) if g.geom_type == "MultiLineString" else g.representative_point())
    mw = to_wgs(mid)
    return "<Placemark><name>%s</name>%s<styleUrl>#%s</styleUrl><Point><coordinates>%.7f,%.7f,0</coordinates></Point></Placemark>" % (escape(str(name)), region(mw, kind), style, mw.x, mw.y)
def line_style(sid, colour, width): return "<Style id='%s'><LineStyle><color>%s</color><width>%s</width></LineStyle><LabelStyle><scale>0</scale></LabelStyle></Style>" % (sid, colour, width)
def poly_style(sid, fill, outline, width=1.5, filled=True, outlined=True): return "<Style id='%s'><LineStyle><color>%s</color><width>%s</width></LineStyle><PolyStyle><color>%s</color><fill>%d</fill><outline>%d</outline></PolyStyle></Style>" % (sid, outline, width, fill, 1 if filled else 0, 1 if outlined else 0)
def point_style(sid, colour, scale=0.9, icon="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png", label_scale=0.0): return "<Style id='%s'><IconStyle><color>%s</color><scale>%s</scale><Icon><href>%s</href></Icon></IconStyle><LabelStyle><scale>%s</scale></LabelStyle></Style>" % (sid, colour, scale, icon, label_scale)
def label_style(sid, colour="ffffffff", scale=0.75): return "<Style id='%s'><IconStyle><scale>0</scale></IconStyle><LabelStyle><color>%s</color><scale>%s</scale></LabelStyle></Style>" % (sid, colour, scale)
def folder(name, items, open_=0): return "<Folder><name>%s</name><open>%d</open>%s</Folder>" % (escape(name), open_, "".join(items))
def document(name, styles, folders, desc=""):
    return ('<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>%s</name><open>1</open>%s%s%s</Document></kml>'
            % (escape(name), ("<description>%s</description>" % escape(desc)) if desc else "", "".join(styles), "".join(folders)))
def write_kmz(path, kml):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z: z.writestr("doc.kml", kml)
    print("  %s  %.2f MB" % (os.path.basename(path), os.path.getsize(path) / 1e6))

# ------------------------------------------------------------------ themes: each returns (styles, folders, count)
def theme_channels():
    g = gpd.read_file(SRC["channels"]); g = g[g["Block"] == 4].copy(); cols = agreed_colours(); styles = [label_style("lbl_ch", "ffffffff", 0.7)]; folders = []
    for cls, (rgba, w) in cols.items(): styles.append(line_style("c_" + re.sub(r"\W", "_", cls), kml_colour(rgba), max(2, round(w * 3))))
    for cls in ("FP CH", "Sw M CH", "Sw S CH", "FP D", "Sw M D", "Sw S D"):
        sub = g[g["CHtt"] == cls]
        if sub.empty: continue
        items = [placemark(r["Name"], "c_" + re.sub(r"\W", "_", cls), r.geometry, [("Name", r["Name"]), ("Class", CHNAMES[cls]), ("Length", "%.0f m" % r.geometry.length)]) for _, r in sub.iterrows()]
        labels = [label_mark(r["Name"], r.geometry, "lbl_ch", "name") for _, r in sub.iterrows()]
        folders.append(folder(CHNAMES[cls] + "s (%d)" % len(sub), items + [folder("Names (visible when zoomed in)", labels)]))
    return styles, folders, len(g)
def theme_segments():
    s = gpd.read_file(SRC["segments"], layer="segments"); styles = [line_style("seg", kml_colour([0, 60, 160]), 3), label_style("lbl_seg", "ffffffff", 0.65)]
    items = [placemark(r["SGLabel"], "seg", r.geometry, [("Reach", r["SGLabel"]), ("Channel", r["Channel"]), ("Station", "%.0f to %.0f m" % (r["FromSta"], r["ToSta"])), ("Length", "%.0f m" % r["Length"]),
             ("Size 200-year (W x D)", r["size_200"]), ("Flow 200-year", "%.1f m³/s" % r["Q_200"]), ("Slope", "%.4f" % r["slope_200"]),
             ("Size 2 / 5 / 10 / 25-year", "%s; %s; %s; %s" % (r["size_2"], r["size_5"], r["size_10"], r["size_25"])), ("Size 50 / 100 / 500-year", "%s; %s; %s" % (r["size_50"], r["size_100"], r["size_500"]))], show_name=False) for _, r in s.iterrows()]
    labels = [label_mark("%s  %s" % (r["SGLabel"], r["size_200"]), r.geometry, "lbl_seg", "reach") for _, r in s.iterrows()]
    return styles, [folder("Channel reaches, 200-year design (%d)" % len(s), items + [folder("Reach and size (visible when zoomed in)", labels)])], len(s)
def theme_extents():
    e = gpd.read_file(SRC["extent200"]); d = gpd.read_file(SRC["dyke_extent"])
    styles = [poly_style("bed", kml_colour([255, 215, 0], 120), kml_colour([255, 215, 0], 0), 0.5, filled=True, outlined=False), poly_style("cor", kml_colour([139, 69, 19], 0), kml_colour([139, 69, 19]), 2.0, filled=False, outlined=True),
              poly_style("dyk", kml_colour([0, 176, 80], 0), kml_colour([0, 176, 80]), 2.0, filled=False, outlined=True)]
    f1 = folder("Designed bed (200-year), fill only", [placemark("Channel bed", "bed", r.geometry, [("Extent", r["note"])], show_name=False) for _, r in e[e.kind == "bed"].iterrows()])
    f2 = folder("Corridor (bed, embankments and access roads), outline only", [placemark("Channel corridor", "cor", r.geometry, [("Extent", r["note"])], show_name=False) for _, r in e[e.kind == "corridor"].iterrows()])
    f3 = folder("Dyke extent (15.5 m each side), outline only", [placemark(r["Name"], "dyk", r.geometry, [("Dyke", r["Name"]), ("Extent", "%.0f m" % r["extent_m"])], show_name=False) for _, r in d.iterrows()])
    return styles, [f1, f2, f3], len(e) + len(d)
def theme_points():
    p = gpd.read_file(SRC["points"]); styles = [point_style("pt", kml_colour([0, 229, 160]), 0.35), point_style("pt_out", kml_colour([255, 80, 80]), 0.4)]
    def rows(r):
        return [("Label", r["SGLabel"]), ("Channel", r["Channel"]), ("Station", r["StaLbl"]), ("Ground level", "%.2f m" % r["Ground"] if pd.notna(r["Ground"]) else None), ("Design point", r["GDP"]), ("Inflow element", r["Flow"]),
                ("Q200", "%.1f m³/s" % r["Q200"] if pd.notna(r["Q200"]) else None), ("Q100", "%.1f m³/s" % r["Q100"] if pd.notna(r["Q100"]) else None), ("Fix", r["Fix"]), ("Fix type", r["FixType"]), ("Outfall", r["Outfall"]), ("Raise", r["Raise"])]
    items = [placemark(r["SGLabel"], "pt_out" if str(r.get("Outfall", "")) not in ("", "nan", "None") else "pt", r.geometry, rows(r), show_name=False) for _, r in p.iterrows()]
    return styles, [folder("Design points (%d), click for the data" % len(p), items)], len(p)
def theme_dams():
    ax = gpd.read_file(SRC["dam_axis"]); fsl = gpd.read_file(SRC["fsl"]); cr = gpd.read_file(SRC["crest"])
    styles = [line_style("axis", kml_colour([255, 0, 255]), 5), poly_style("fsl", kml_colour([0, 112, 192], 100), kml_colour([0, 112, 192]), 1.5), poly_style("crest", kml_colour([192, 0, 0], 0), kml_colour([192, 0, 0]), 2.0, filled=False), label_style("lbl_dam", "ffffffff", 0.9)]
    nm = lambda r: DAM_LABEL.get(r.get("Dam Name", r.get("Dam_Name")), r.get("Dam Name", r.get("Dam_Name")))
    rows = lambda r: [("Dam", nm(r)), ("Crest level", "%s m" % r.get("Crest El", r.get("Crest_El"))), ("Full supply level", "%s m" % r["FSL"]), ("Reservoir at FSL", "%s Mm³" % r["Reservoir"]), ("Maximum height", "%s m" % r["Hmax"]), ("Spillway length", "%s m" % r.get("Spillway L", r.get("Spillway_L")))]
    f1 = folder("Dam axes", [placemark(nm(r), "axis", r.geometry, rows(r), show_name=False) for _, r in ax.iterrows()] + [folder("Names (visible when zoomed in)", [label_mark(nm(r), r.geometry, "lbl_dam", "dam") for _, r in ax.iterrows()])])
    f2 = folder("Reservoir at full supply level", [placemark("%s - FSL %s m" % (nm(r), r["FSL"]), "fsl", r.geometry, rows(r), show_name=False) for _, r in fsl.iterrows()])
    f3 = folder("Reservoir at crest level", [placemark("%s - crest %s m" % (nm(r), r.get("Crest El", r.get("Crest_El"))), "crest", r.geometry, rows(r), show_name=False) for _, r in cr.iterrows()])
    return styles, [f1, f2, f3], len(ax) + len(fsl) + len(cr)
def theme_culverts():
    cr = gpd.read_file(SRC["crossings"], layer="crossings"); ex = gpd.read_file(SRC["culv_exist"]).to_crs(32640)
    ch = gpd.read_file(SRC["channels"]); ch = ch[ch["Block"] == 4]; env = ch.total_bounds; pad = 5000; ex = ex.cx[env[0] - pad: env[2] + pad, env[1] - pad: env[3] + pad]
    styles = [point_style("prop", kml_colour([255, 128, 0]), 0.6), label_style("lbl_cul", "ffffffff", 0.75), line_style("exist", kml_colour([0, 176, 240]), 3)]
    items = [placemark("%s - %s" % (r["channel"], r["road"]), "prop", r.geometry,
             [("Road", r["road"]), ("Channel", r["channel"]), ("Reach", r["reach"]), ("Station", "%.0f m" % r["station_m"]), ("Q200", "%.0f m³/s" % r["Q200"] if pd.notna(r["Q200"]) else None), ("Channel width x depth", "%s x %s m" % (r["channel_width_m"], r["channel_depth_m"])),
              ("Cells", "%s x %s x %s m" % (r["cells"], r["cell_width_m"], r["cell_height_m"])), ("Overall width", "%s m" % r["overall_width_m"]), ("Length", "%s m" % r["length_m"]), ("Slope", r["slope"]), ("Headwater / height", r["HW_over_D"]),
              ("Existing structure within 10 m", r["existing_type"]), ("Existing size", r["existing_size"]), ("Cost", "%.2f million OMR" % r["cost_mOMR"] if pd.notna(r["cost_mOMR"]) else None)], show_name=False) for _, r in cr.iterrows()]
    labels = [label_mark(r["size"], r.geometry, "lbl_cul", "culvert") for _, r in cr.iterrows()]
    f1 = folder("Proposed box culverts (%d), click for the data" % len(cr), items + [folder("Cells x width x height (visible when zoomed in)", labels)])
    f2 = folder("Existing culverts of the inventory (%d barrels)" % len(ex), [placemark(str(r.get("Code", "")) or "culvert", "exist", r.geometry, [(c, r[c]) for c in ("Num", "W", "H", "Size", "Code", "L") if c in ex.columns], show_name=False) for _, r in ex.iterrows()])
    return styles, [f1, f2], len(cr) + len(ex)
def theme_hms():
    import importlib.util
    spec = importlib.util.spec_from_file_location("hms84", os.path.join(HERE, "84_hms_kmz.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    styles, folder_xml, n = m.hms_folders(); return [styles], [folder_xml], sum(n)

if __name__ == "__main__":
    all_styles, all_folders = [], []
    for key, title, fn in (("channels_dykes", "Channels and dykes", theme_channels), ("channel_reaches", "Channel reaches and sizes", theme_segments), ("extents", "Channel and dyke extents", theme_extents),
                           ("design_points", "Design points", theme_points), ("dams", "Dams", theme_dams), ("culverts", "Culverts", theme_culverts), ("HEC-HMS_model", "HEC-HMS model", theme_hms)):
        styles, folders, n = fn(); print(key, n, "features")
        write_kmz(os.path.join(OUT, "Block04_%s.kmz" % key), document("Block 04 - " + title, styles, folders))
        for st in styles:
            if st not in all_styles: all_styles.append(st)
        all_folders.append(folder(title, folders, 0))
    write_kmz(os.path.join(OUT, "Block04_all.kmz"), document("Block 04 - channel scheme", all_styles, all_folders, "Flood protection and stormwater channels of Block 04: names, reaches and sizes, extents, design points, dams, culverts and the HEC-HMS model. Labels appear when zoomed in; click a feature for its data."))
    print("done ->", OUT)
