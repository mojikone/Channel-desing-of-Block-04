"""Step 91 (W9, engineer 2026-10-14) - the QGIS project of the submission folder, second generation: station ticks perpendicular to
the alignment, the existing culverts as lines, the dyke extent, his own styles and labels for the design points and the channel
reaches (SGLabel, width and slope), the outfalls with the invert below the existing level in red, the reach sizes of all return
periods and the extents per return period, the bypass and its culverts. Relative paths into "03 GIS"; a group per report map
plus the standing groups. Run after 90_submission.py.
    "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" 91_submission_qgis.py [--out "<submission folder>"]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); W9 = os.path.dirname(HERE); CB = os.path.dirname(W9); B4 = os.path.dirname(CB)
from qgis.core import (QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem, QgsLineSymbol, QgsFillSymbol, QgsMarkerSymbol,
                       QgsSingleSymbolRenderer, QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsGraduatedSymbolRenderer, QgsRendererRange, QgsRuleBasedRenderer,
                       QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling, QgsLayerTreeGroup, Qgis, QgsSimpleLineCallout, QgsUnitTypes,
                       QgsRasterShader, QgsColorRampShader, QgsSingleBandPseudoColorRenderer, QgsHillshadeRenderer, QgsProperty, QgsSymbolLayer)
from qgis.PyQt.QtGui import QColor, QFont
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", r"C:\Program Files\QGIS 3.44.8\apps\qgis-ltr"), True)
app = QgsApplication([], False); app.initQgis()
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
OUT = opt("--out", os.path.join(B4, "Deliverables", "2 Submission 13102026")); G = os.path.join(OUT, "03 GIS"); Q = os.path.join(OUT, "08 QGIS"); os.makedirs(Q, exist_ok=True)
UTM = QgsCoordinateReferenceSystem("EPSG:32640")
proj = QgsProject.instance(); proj.setCrs(UTM); proj.setTitle("Block 04 - Flood protection scheme: channels and dykes"); proj.writeEntry("Paths", "/Absolute", False)
root = proj.layerTreeRoot(); made = []
RPS = ["2", "5", "10", "25", "50", "100", "200", "500"]
SEG = "Hydraulic model (200-year design)/Channel reaches, nodes, outfalls, bed and corridor.gpkg"; SEG_RP = "Hydraulic model (200-year design)/Channel reaches - sizes for all return periods.gpkg"

def vec(rel, name, layer=None, subset=None, qml=None):
    path = os.path.join(G, rel); l = QgsVectorLayer(path + ("|layername=" + layer if layer else ""), name, "ogr")
    if not l.isValid(): print("  not valid:", rel, layer); return None
    if subset: l.setSubsetString(subset)
    if qml: l.loadNamedStyle(os.path.join(G, "Styles", qml + ".qml"))
    proj.addMapLayer(l, False); made.append(l); return l
def ras(rel, name, qml=None):
    l = QgsRasterLayer(os.path.join(G, rel), name)
    if not l.isValid(): print("  not valid:", rel); return None
    if qml: l.loadNamedStyle(os.path.join(G, "Styles", qml + ".qml"))
    proj.addMapLayer(l, False); made.append(l); return l
def line(l, color, width=0.5, dash=None):
    if l is None: return
    p = {"color": color, "width": str(width), "width_unit": "MM"}
    if dash: p["line_style"] = dash
    l.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple(p)))
def fill(l, color="0,0,0,0", outline="#C00000", width=0.5):
    if l is None: return
    l.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({"color": color, "outline_color": outline, "outline_width": str(width), "outline_width_unit": "MM"})))
def marker(l, color, shape="circle", size=2.0, outline="#1F1F1F"):
    if l is None: return
    l.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": shape, "color": color, "outline_color": outline, "outline_width": "0.3", "size": str(size)})))
def label(l, expr, size=8.0, colour="#1F1F1F", bold=True, on_line=False, around=False, callout=False, buffer=0.9, colour_expr=None):
    if l is None: return
    pal = QgsPalLayerSettings(); pal.fieldName = expr; pal.isExpression = True; pal.enabled = True
    tf = QgsTextFormat(); f = QFont("Arial"); f.setBold(bold); tf.setFont(f); tf.setSize(size); tf.setColor(QColor(colour))
    b = QgsTextBufferSettings(); b.setEnabled(True); b.setSize(buffer); b.setColor(QColor("#FFFFFF")); tf.setBuffer(b); pal.setFormat(tf)
    if on_line: pal.placement = Qgis.LabelPlacement.Line; pal.lineSettings().setPlacementFlags(Qgis.LabelLinePlacementFlag.AboveLine | Qgis.LabelLinePlacementFlag.MapOrientation)
    if around: pal.placement = Qgis.LabelPlacement.OrderedPositionsAroundPoint; pal.dist = 1.5
    if callout:
        co = QgsSimpleLineCallout(); co.setEnabled(True); co.setMinimumLength(1.0); pal.setCallout(co)
    if colour_expr: pal.dataDefinedProperties().setProperty(QgsPalLayerSettings.Property.Color, QgsProperty.fromExpression(colour_expr))
    l.setLabelsEnabled(True); l.setLabeling(QgsVectorLayerSimpleLabeling(pal))
def group(parent, name, layers, visible=True, expanded=False):
    g = parent.addGroup(name)
    for l in layers:
        if l is not None: g.addLayer(l)
    g.setItemVisibilityChecked(visible); g.setExpanded(expanded); return g
CHNAMES = {"FP CH": "Flood protection channel", "Sw M CH": "Stormwater main channel", "Sw S CH": "Stormwater secondary channel", "FP D": "Flood protection dyke", "Sw M D": "Stormwater main dyke", "Sw S D": "Stormwater secondary dyke"}
def channels_styled(name="Channels and dykes", names=False):
    l = vec("Channels and dykes/Channels and dykes.shp", name, qml="channels_dykes"); r = l.renderer() if l else None
    if r is not None and r.type() == "categorizedSymbol":
        for i, c in enumerate(r.categories()): r.updateCategoryLabel(i, CHNAMES.get(str(c.value()), str(c.label())))
        for i in sorted([i for i, c in enumerate(r.categories()) if c.value() in (None, "") or str(c.value()).strip() in ("", "NULL")], reverse=True): r.deleteCategory(i)
    if names: label(l, '"Name"', 7.5, on_line=True)
    return l
def channels_plain(name="Channels and dykes"):
    l = vec("Channels and dykes/Channels and dykes.shp", name)
    if l is None: return None
    rt = QgsRuleBasedRenderer.Rule(None)
    rt.appendChild(QgsRuleBasedRenderer.Rule(QgsLineSymbol.createSimple({"color": "#1F3B63", "width": "0.55", "width_unit": "MM"}), 0, 0, "\"CHtt\" LIKE '% CH'", "Channel"))
    rt.appendChild(QgsRuleBasedRenderer.Rule(QgsLineSymbol.createSimple({"color": "#1F3B63", "width": "0.55", "width_unit": "MM", "line_style": "dash"}), 0, 0, "\"CHtt\" LIKE '% D'", "Dyke"))
    l.setRenderer(QgsRuleBasedRenderer(rt)); return l
def dam_axes(name="Dam axis"):
    l = vec("Dams/Dam axes.shp", name); line(l, "#FF00FF", 1.4)
    label(l, '''CASE WHEN "Dam Name" = 'Hawasinah EX' THEN 'Hawasinah UP' WHEN "Dam Name" = 'Sakhin 08' THEN 'Sakhin 08 (Mehmum)' ELSE "Dam Name" END''', 8.5, on_line=True); return l
def reaches_his(name, rp="200"):
    """his reach style and labels (SGLabel, width, slope) on the layer with the sizes of all return periods"""
    l = vec(SEG_RP, name, "segments")
    if l is None: return None
    l.loadNamedStyle(os.path.join(G, "Styles", "channel_reaches.qml"))
    label(l, f'''"SGLabel" || '\\n' || 'W: ' || format_number("span_{rp}", 1) || ' m' || '\\n' || 'S: ' || format_number("slope_{rp}", 4)''', 7.5, "#003ca0", bold=False, on_line=True)
    return l
def outfalls_red(name="Outfall: invert, existing level, difference (m)"):
    l = vec("Hydraulic model (200-year design)/Outfalls - invert and existing level.gpkg", name, "outfalls")
    if l is None: return None
    rt = QgsRuleBasedRenderer.Rule(None)
    rt.appendChild(QgsRuleBasedRenderer.Rule(QgsMarkerSymbol.createSimple({"name": "circle", "color": "#00E5A0", "outline_color": "#1F1F1F", "outline_width": "0.3", "size": "3.0"}), 0, 0, '"diff" <= 0.05', "Invert at or above the existing level"))
    rt.appendChild(QgsRuleBasedRenderer.Rule(QgsMarkerSymbol.createSimple({"name": "circle", "color": "#00E5A0", "outline_color": "#C00000", "outline_width": "0.9", "size": "3.4"}), 0, 0, '"diff" > 0.05', "Invert below the existing level"))
    l.setRenderer(QgsRuleBasedRenderer(rt))
    label(l, '''"label" || '\\n' || 'I: ' || format_number("invert", 2) || '\\n' || 'Fix: ' || format_number("fix", 2) || '\\n' || 'Δ: ' || format_number("diff", 2)''', 7.0, around=True, colour_expr='''CASE WHEN "diff" > 0.05 THEN '#C00000' ELSE '#1F1F1F' END''')
    return l
def stations(name, layer):
    l = vec("Stations/Stations every 500 m and 1000 m.gpkg", name, layer)
    if l is None: return None
    sym = QgsMarkerSymbol.createSimple({"name": "line", "color": "#1F1F1F", "outline_color": "#1F1F1F", "outline_width": "0.4", "size": "3.0"})
    sym.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.Property.Angle, QgsProperty.fromExpression('180 - "angle"'))   # perpendicular to the alignment (marker angles are clockwise)
    l.setRenderer(QgsSingleSymbolRenderer(sym)); label(l, '"label"', 6.5, around=True, bold=False); return l
roads_spec = (("Roads and utilities/Batinah Highway.shp", "Batinah Highway", "#1F1F1F", 0.9, None), ("Roads and utilities/Batinah Coastal Road.shp", "Batinah Coastal Road", "#5A5A5A", 0.7, None), ("Roads and utilities/Batinah Expressway.shp", "Batinah Expressway", "#000000", 0.9, None),
              ("Roads and utilities/North Batinah Bypass (planned).shp", "North Batinah Bypass (planned)", "#7F6000", 0.8, "dash"), ("Roads and utilities/OQ pipelines (north).shp", "OQ pipelines", "#FF8C00", 0.8, "dash dot"), ("Roads and utilities/OQ pipelines (south).shp", "OQ pipelines (south)", "#FF8C00", 0.8, "dash dot"))
def roads():
    out = []
    for rel, nm, col, wd, dash in roads_spec:
        l = vec(rel, nm); line(l, col, wd, dash); out.append(l)
    return out
def existing_culverts(name="Existing culverts (inventory)"):
    l = vec("Culverts/Existing culverts (inventory, Block 04 plain).shp", name); line(l, "#00B0F0", 1.2); return l

# ------------------------------------------------------------------ the report maps
maps = root.addGroup("Report maps"); maps.setExpanded(True)
g = vec("Catchments/Global catchments.gpkg", "Global catchments of Block 04", "gca")
if g is not None:
    g.setRenderer(QgsCategorizedSymbolRenderer("G_NAME", [QgsRendererCategory(nm, QgsFillSymbol.createSimple({"color": col, "outline_color": "#1F1F1F", "outline_width": "0.4", "outline_width_unit": "MM"}), nm) for nm, col in (("Al Hawasinah", "255,192,0,110"), ("Shafan", "0,176,240,110"), ("Sarami", "146,208,80,110"), ("Sakhin", "255,102,0,110"), ("Mehmum", "255,153,102,110"))]))
    label(g, '''replace("G_NAME", '_', ' ') || '\\n' || format_number("area_km2", 0) || ' km²' ''', 9.0)
group(maps, "Global catchments", [dam_axes(), channels_plain(), g])
dep = ras("Rasters/Flood depth 200-year without the scheme (m).tif", "Flood depth 200-year, no scheme (m)", qml="depth_200yr")
group(maps, "Channel alignments on the 200-year flood depth", [dam_axes(), channels_styled("Channels and dykes by class"), dep])
fsl = vec("Dams/Reservoirs at full supply level.shp", "Reservoir at full supply level", qml="fsl_polygon")
group(maps, "Channel and dyke routes by category", [dam_axes(), channels_styled("Channels and dykes by class", names=True), fsl])
group(maps, "Roads and utilities", [existing_culverts()] + roads() + [channels_plain()])
lu = vec("Land use/Land use (cadastre).shp", "Land use (cadastre)", qml="landuse")
group(maps, "Land use", [channels_plain(), lu])
sub = vec("Catchments/HEC-HMS subbasins.shp", "HEC-HMS subbasin"); fill(sub, "0,0,0,0", "#E97132", 0.3); label(sub, '"name"', 7.0, "#C55A11", False)
rch = vec("Catchments/HEC-HMS reaches.shp", "HEC-HMS reach"); line(rch, "#00B0F0", 0.6)
pts = vec("Catchments/HEC-HMS junctions and outfalls.shp", "HEC-HMS junction, outfall and reservoir"); marker(pts, "#1F4FD8", "circle", 1.8, "#FFFFFF"); label(pts, '"name"', 7.0, around=True)
group(maps, "HEC-HMS model", [pts, rch, sub, dam_axes()])
q2 = vec("Catchments/HEC-HMS junctions and outfalls.shp", "200-year peak flow at the junctions (m³/s)"); marker(q2, "#1F4FD8", "circle", 1.9, "#FFFFFF"); label(q2, 'format_number("Q200", 0)', 7.5, around=True)
group(maps, "200-year peak flow at the junctions", [q2, rch, channels_plain(), dam_axes()])
inter = vec("Catchments/HEC-HMS subbasins with dam flag.shp", "Intermediate catchments (no dam upstream)")
if inter is not None: inter.setRenderer(QgsCategorizedSymbolRenderer("inter", [QgsRendererCategory(1, QgsFillSymbol.createSimple({"color": "255,192,0,120", "outline_color": "#7F6000", "outline_width": "0.3", "outline_width_unit": "MM"}), "No dam upstream"), QgsRendererCategory(0, QgsFillSymbol.createSimple({"color": "189,215,238,90", "outline_color": "#5A5A5A", "outline_width": "0.2", "outline_width_unit": "MM"}), "Dam upstream")]))
group(maps, "Intermediate catchments", [channels_plain(), rch, inter, dam_axes()])
cn = ras("Rasters/SCS curve number grid.tif", "SCS curve number")
if cn is not None:
    sh = QgsColorRampShader(55, 100, None, QgsColorRampShader.Interpolated, QgsColorRampShader.Continuous); cols = ["#1A9850", "#A6D96A", "#FFFFBF", "#FDAE61", "#D73027"]
    sh.setColorRampItemList([QgsColorRampShader.ColorRampItem(55 + 45 * i / 4, QColor(c), str(round(55 + 45 * i / 4))) for i, c in enumerate(cols)]); rs = QgsRasterShader(); rs.setRasterShaderFunction(sh)
    cn.setRenderer(QgsSingleBandPseudoColorRenderer(cn.dataProvider(), 1, rs))
group(maps, "SCS curve number", [channels_plain(), dam_axes(), cn])
bed = vec(SEG, "Designed channel bed (200-year)", "bed"); fill(bed, "#E97132", "#A0522D", 0.2)
dyk = vec("Dykes/Dykes - height and cost.gpkg", "Dyke", "dykes"); line(dyk, "#00B050", 1.1)
group(maps, "Designed bed width", [reaches_his("Channel reaches: label, width, slope (200-year)"), bed, dyk, dam_axes()])
segd = vec(SEG, "Channel depth (m)", "segments")
if segd is not None: segd.setRenderer(QgsCategorizedSymbolRenderer("rise_m", [QgsRendererCategory(2.5, QgsLineSymbol.createSimple({"color": "#1F4FD8", "width": "0.9", "width_unit": "MM"}), "2.5 m"), QgsRendererCategory(3.0, QgsLineSymbol.createSimple({"color": "#C00000", "width": "1.2", "width_unit": "MM"}), "3.0 m")]))
group(maps, "Channel depth", [segd, dyk, dam_axes()])
segl = vec(SEG, "Reach label", "segments"); line(segl, "0,0,0,0", 0.1); label(segl, '"SGLabel"', 6.0, on_line=True)
group(maps, "Channel names and reach labels", [segl, channels_styled("Channels and dykes by class", names=True), dam_axes()])
segq = vec(SEG, "200-year design flow of the reach (m³/s)", "segments")
if segq is not None:
    segq.setRenderer(QgsGraduatedSymbolRenderer("flow", [QgsRendererRange(lo, hi, QgsLineSymbol.createSimple({"color": c, "width": w, "width_unit": "MM"}), lab_) for lo, hi, lab_, c, w in (
        (0, 50, "0 to 50", "#9DC3E6", "0.5"), (50, 150, "50 to 150", "#5B9BD5", "0.7"), (150, 400, "150 to 400", "#2F5597", "0.9"), (400, 1000, "400 to 1 000", "#C55A11", "1.2"), (1000, 3000, "1 000 to 1 500", "#C00000", "1.5"))]))
    label(segq, '''CASE WHEN "flow" > 0.5 THEN format_number("flow", 0) ELSE '' END''', 7.0, on_line=True, bold=False)
group(maps, "200-year design flow along the channels", [segq, dyk, dam_axes()])
group(maps, "Outfalls", [outfalls_red(), channels_plain(), dam_axes()])
cro = vec("Culverts/Road crossings and proposed box culverts.gpkg", "Proposed box culvert (cells x width x height, m)", "crossings"); marker(cro, "#FFC000", "square", 3.0); label(cro, '"size"', 7.0, around=True, callout=True)
group(maps, "Road crossings and culverts", [cro, existing_culverts(), channels_plain()] + roads()[:4] + [dam_axes()])
dykh = vec("Dykes/Dykes - height and cost.gpkg", "Dyke height (m)", "dykes")
if dykh is not None:
    dykh.setRenderer(QgsGraduatedSymbolRenderer("H_m", [QgsRendererRange(lo, hi, QgsLineSymbol.createSimple({"color": c, "width": "1.3", "width_unit": "MM"}), lab_) for lo, hi, lab_, c in ((0, 2.0, "1.0 to 2.0", "#A9D18E"), (2.0, 2.5, "2.0 to 2.5", "#70AD47"), (2.5, 3.5, "2.5 to 3.5", "#C55A11"), (3.5, 10, "3.5 to 4.5", "#C00000"))]))
    label(dykh, 'format_number("H_m", 1)', 7.5, on_line=True)
group(maps, "Dyke heights", [dykh, channels_plain(), dam_axes()])

# ------------------------------------------------------------------ the standing groups
dp = vec("Design points and segments/Design points.shp", "Design points (all kinds)", qml="design_points")   # his style and labels (SGLabel, wadi depth, raise)
ds = vec("Design points and segments/Design segments.shp", "Design segments"); line(ds, "#1F3B63", 0.6); label(ds, '"SGLabel"', 6.5, on_line=True, bold=False)
group(root, "Design points and segments", [dp, ds], visible=False)
hm = root.addGroup("Channel reaches: sizes for every return period"); hm.setItemVisibilityChecked(False); hm.setExpanded(False)
for rp in RPS:
    l = reaches_his(f"Reaches {rp}-year: label, width, slope", rp)
    if l is not None: hm.addLayer(l)
group(root, "Channel and dyke stations", [stations("Stations every 1000 m", "stations_1000"), stations("Stations every 500 m", "stations_500")], visible=False)
ex = root.addGroup("Channel and dyke extents"); ex.setItemVisibilityChecked(False); ex.setExpanded(False)
bedx = vec("Channel extents/Channel bed (designed, 200-year).shp", "Channel bed (designed, 200-year)"); fill(bedx, "255,215,0,90", "#FFD700", 0.3)
cor = vec("Channel extents/Channel corridor (bed, embankments and access roads).shp", "Channel corridor (bed, embankments and access roads)"); fill(cor, "0,0,0,0", "#8B4513", 0.6)
dye = vec("Channel extents/Dyke extent (15.5 m each side).shp", "Dyke extent (15.5 m each side)"); fill(dye, "0,0,0,0", "#00B050", 0.6)
for l in (bedx, cor, dye):
    if l is not None: ex.addLayer(l)
exr = ex.addGroup("By return period (bed and corridor)"); exr.setItemVisibilityChecked(False); exr.setExpanded(False)
for rp in RPS:
    l = vec(f"Channel extents/By return period/Channel extent {rp}-year (bed and corridor).shp", f"Channel extent {rp}-year")
    if l is not None:
        l.setRenderer(QgsCategorizedSymbolRenderer("kind", [QgsRendererCategory("bed", QgsFillSymbol.createSimple({"color": "255,215,0,110", "outline_style": "no"}), "Bed"), QgsRendererCategory("corridor", QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": "#8B4513", "outline_width": "0.5", "outline_width_unit": "MM"}), "Corridor")]))
        exr.addLayer(l)
group(root, "Channels and dykes", [channels_styled("Channels and dykes by class", names=True)], visible=True)
cr = vec("Dams/Reservoirs at crest level.shp", "Reservoir at crest level", qml="crest_polygon")
group(root, "Dams", [dam_axes(), vec("Dams/Reservoirs at full supply level.shp", "Reservoir at full supply level", qml="fsl_polygon"), cr], visible=False)
cro2 = vec("Culverts/Road crossings and proposed box culverts.gpkg", "Proposed box culverts (highway, coastal road, bypass)", "crossings"); marker(cro2, "#FFC000", "square", 3.0); label(cro2, '"size"', 7.0, around=True, callout=True)
group(root, "Roads, utilities and culverts", roads() + [existing_culverts(), cro2], visible=False)
group(root, "Land use", [vec("Land use/Land use (cadastre).shp", "Land use (cadastre)", qml="landuse")], visible=False)
dem5 = ras("Rasters/Terrain model 5 m - Block 04.tif", "Terrain model 5 m"); dem10 = ras("Rasters/Terrain model 10 m - Block 04.tif", "Terrain model 10 m"); hs = ras("Rasters/Hillshade 10 m.tif", "Hillshade 10 m")
if hs is not None and hs.bandCount() == 1:
    try: hs.setRenderer(QgsHillshadeRenderer(hs.dataProvider(), 1, 315, 45))
    except Exception: pass
ct1 = QgsRasterLayer(os.path.join(OUT, "07 Models", "Channel terrain", "Block 04 - Terrain with the channels cut in (2 m, 0.5 m ground).tif"), "Terrain with the channels cut in (2 m)")
if ct1.isValid(): proj.addMapLayer(ct1, False); made.append(ct1)
group(root, "Terrain", [ct1 if ct1.isValid() else None, hs, dem10, dem5], visible=False)
google = QgsRasterLayer("type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=18&zmin=0", "Google satellite", "wms")
if google.isValid(): proj.addMapLayer(google, False); group(root, "Background", [google], visible=True)
for i, g_ in enumerate(maps.children()):
    if isinstance(g_, QgsLayerTreeGroup): g_.setItemVisibilityChecked(i == 2); g_.setExpanded(False)
path = os.path.join(Q, "Block 04 - Channel scheme.qgz"); ok = proj.write(path); print("project:", path, "written" if ok else "FAILED", "| layers:", len(made))
app.exitQgis(); sys.exit(0 if ok else 1)
