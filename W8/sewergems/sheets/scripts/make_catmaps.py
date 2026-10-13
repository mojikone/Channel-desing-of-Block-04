"""Key plan of each global catchment for the plan-profile set (W8, engineer 2026-10-13): after each catchment divider one A1 page
with the channels and dykes in the agreed symbology and their names, their extents (designed bed and corridor), the stations every
500 m (1 000 m where the 500 m labels would collide), the dam axes, on the satellite image. Built with PyQGIS and exported as a
one-page PDF per catchment into PDF/Set/_catmap_<CODE>.pdf, which make_set.py places after the divider.
    "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" make_catmaps.py [HAW SHA SAR SAK] [--dim-fp] [--png] [--step 500|1000|auto]
--dim-fp: the stormwater set, the flood-protection channels and dykes in grey without stations (they are not in that set).
"""
import os, sys, math, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from qgis.core import (QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemLegend,
                       QgsLayoutItemScaleBar, QgsLayoutItemShape, QgsLayoutExporter, QgsLayoutSize, QgsLayoutPoint, QgsUnitTypes, QgsRectangle, QgsCoordinateReferenceSystem,
                       QgsLineSymbol, QgsFillSymbol, QgsMarkerSymbol, QgsSingleSymbolRenderer, QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings,
                       QgsVectorLayerSimpleLabeling, QgsProperty, QgsLayoutItemPage, QgsLegendStyle, QgsLayoutMeasurement, QgsFeature, QgsGeometry, QgsPointXY,
                       QgsLayerTreeGroup, QgsLayerTreeLayer, Qgis, QgsFeatureRequest)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import Qt
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", r"C:\Program Files\QGIS 3.44.8\apps\qgis-ltr"), True)
app = QgsApplication([], False); app.initQgis()
from config import DOC_NO_PREFIX, OUT_PDF, SHP_BUF_BED, SHP_BUF_CH, CATCHMENT_ORDER
from shapely.geometry import Polygon as ShPolygon
from shapely import affinity as sh_aff
from shapely.strtree import STRtree

A = sys.argv[1:]
DIM_FP = "--dim-fp" in A; PNG = "--png" in A
STEP_OPT = A[A.index("--step") + 1] if "--step" in A else "auto"
CODES = [a for a in A if a in ("HAW", "SHA", "SAR", "SAK")] or list(CATCHMENT_ORDER)
CATCHMENT = {"HAW": "Al Hawasinah", "SAK": "Sakhin", "SAR": "Sarami", "SHA": "Shafan"}
W8 = os.path.dirname(os.path.dirname(os.path.dirname(HERE))); CB04 = os.path.dirname(W8); B4 = os.path.dirname(CB04); W3 = os.path.join(CB04, "W3")
SRC_CH = os.path.join(B4, "Hydrology", "SHP", "temp", "Channels and Dykes 04102026.shp")
QML_CH = os.path.join(W3, "maps", "styles", "channels_dykes.qml")
STATIONS = os.path.join(W8, "gis", "stations.gpkg")
DAMS = os.path.join(B4, "Hydrology", "SHP", "Block 4 Dams", "Dams updated.shp")
OUT_DIR = os.path.join(OUT_PDF, "Set"); os.makedirs(OUT_DIR, exist_ok=True)
REV = "1"; DATE = datetime.date.today().strftime("%d.%m.%Y")
UTM = QgsCoordinateReferenceSystem("EPSG:32640"); MM = QgsUnitTypes.LayoutMillimeters
PAGE_W, PAGE_H = 841.0, 594.0
MAP_X, MAP_Y, MAP_W, MAP_H = 15.0, 52.0, 811.0, 522.0          # inside the 10 mm frame, under the title band
CHNAMES = {"FP CH": "Flood protection channel", "Sw M CH": "Stormwater main channel", "Sw S CH": "Stormwater secondary channel",
           "FP D": "Flood protection dyke", "Sw M D": "Stormwater main dyke", "Sw S D": "Stormwater secondary dyke"}
proj = QgsProject.instance(); proj.setCrs(UTM)

# ------------------------------------------------------------------ layers
def vec(path, name, layer=None, subset=None):
    l = QgsVectorLayer(path + ("|layername=" + layer if layer else ""), name, "ogr")
    if not l.isValid(): sys.exit("layer not valid: " + path)
    if subset: l.setSubsetString(subset)
    proj.addMapLayer(l, False); return l

ch = vec(SRC_CH, "Channels and dykes", subset='"Block" = 4'); ch.loadNamedStyle(QML_CH)
r = ch.renderer()
if r is not None and r.type() == "categorizedSymbol":
    for i, c in enumerate(r.categories()):
        lab = CHNAMES.get(str(c.value()), str(c.label())); r.updateCategoryLabel(i, lab + (" (not in this set)" if DIM_FP and str(c.value()).startswith("FP") else ""))
        if DIM_FP and str(c.value()).startswith("FP"):
            s = c.symbol().clone(); s.setColor(QColor("#A6A6A6")); r.updateCategorySymbol(i, s)
    for i in sorted([i for i, c in enumerate(r.categories()) if c.value() in (None, "") or str(c.value()).strip() in ("", "NULL")], reverse=True): r.deleteCategory(i)
# names along the lines, placed first
pal = QgsPalLayerSettings(); pal.fieldName = "Name"; pal.isExpression = False; pal.enabled = True
tf = QgsTextFormat(); f = QFont("Arial"); f.setBold(True); tf.setFont(f); tf.setSize(13.0); tf.setColor(QColor("#1F1F1F"))
b = QgsTextBufferSettings(); b.setEnabled(True); b.setSize(1.3); b.setColor(QColor("#FFFFFF")); tf.setBuffer(b); pal.setFormat(tf)
pal.placement = Qgis.LabelPlacement.Line; ls = pal.lineSettings(); ls.setPlacementFlags(Qgis.LabelLinePlacementFlag.AboveLine | Qgis.LabelLinePlacementFlag.BelowLine | Qgis.LabelLinePlacementFlag.MapOrientation); ls.setMergeLines(False)
pal.placementSettings().setOverlapHandling(Qgis.LabelOverlapHandling.AllowOverlapIfRequired); pal.dist = 0.8; pal.priority = 10
if DIM_FP: pal.dataDefinedProperties().setProperty(QgsPalLayerSettings.Property.Color, QgsProperty.fromExpression("CASE WHEN \"CHtt\" LIKE 'FP%' THEN '#8C8C8C' ELSE '#1F1F1F' END"))
ch.setLabelsEnabled(True); ch.setLabeling(QgsVectorLayerSimpleLabeling(pal))

bed = vec(SHP_BUF_BED, "Channel extent: designed bed"); bed.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({"color": "255,255,0,70", "outline_color": "#FFD700", "outline_width": "0.25", "outline_width_unit": "MM"})))
cor = vec(SHP_BUF_CH, "Channel extent: corridor (embankments and access roads)"); cor.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": "#8B4513", "outline_width": "0.45", "outline_width_unit": "MM"})))
dams = vec(DAMS, "Dam axis"); dams.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple({"color": "#FF00FF", "width": "1.4", "width_unit": "MM"})))
pd_ = QgsPalLayerSettings(); pd_.fieldName = """CASE WHEN "Dam Name" = 'Hawasinah EX' THEN 'Hawasinah UP' WHEN "Dam Name" = 'Sakhin 08' THEN 'Sakhin 08 (Mehmum)' ELSE "Dam Name" END"""; pd_.isExpression = True; pd_.enabled = True; tfd = QgsTextFormat(); fd = QFont("Arial"); fd.setBold(True); tfd.setFont(fd); tfd.setSize(11.5); tfd.setColor(QColor("#1F1F1F"))
bd = QgsTextBufferSettings(); bd.setEnabled(True); bd.setSize(0.9); bd.setColor(QColor("#FFFFFF")); tfd.setBuffer(bd); pd_.setFormat(tfd); pd_.placement = Qgis.LabelPlacement.Line; pd_.priority = 9
dams.setLabelsEnabled(True); dams.setLabeling(QgsVectorLayerSimpleLabeling(pd_))
google = QgsRasterLayer("type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=18&zmin=0", "Google satellite", "wms")
if not google.isValid(): sys.exit("satellite layer not valid")
proj.addMapLayer(google, False)

def feats(layer, cond=lambda f: True): return [f for f in layer.getFeatures() if cond(f)]
def cat_extent(code, s=1.06):
    r = QgsRectangle()
    for f in ch.getFeatures():
        if str(f["Name"]).upper().startswith(code):
            bb = f.geometry().boundingBox(); r = QgsRectangle(bb) if r.isNull() else (r.combineExtentWith(bb) or r)
    r.scale(s); return r

# ------------------------------------------------------------------ stations: ticks and labels in a memory layer per catchment
def station_layers(code, step, mm_per_m):
    """Ticks (lines) and label anchors (points) for the channels and dykes of the catchment at the given step; the label is
    perpendicular to the line on its left side, centred beyond the tick, rotated to read along the tick. Returns the two layers
    and the count of colliding label pairs at this scale (shapely, paper mm)."""
    src = vec(STATIONS, "stations %d" % step, "stations_%d" % step)
    tick_len = 4.0 / mm_per_m; gap = 1.5 / mm_per_m; h_mm = 3.0   # 8.5 pt labels (engineer, 2026-10-13: larger, legible)
    ticks = QgsVectorLayer("LineString?crs=EPSG:32640&field=label:string(12)", "Station every %d m" % step, "memory"); tp = ticks.dataProvider()
    labs = QgsVectorLayer("Point?crs=EPSG:32640&field=label:string(12)&field=rot:double", "Station label", "memory"); lp = labs.dataProvider()
    tf_, lf_, polys = [], [], []
    for f in src.getFeatures():
        nm = str(f["name"]).upper()
        if not nm.startswith(code): continue
        if DIM_FP and nm.endswith("-FP"): continue
        p = f.geometry().asPoint(); a = math.radians(float(f["angle"])); n = (-math.sin(a), math.cos(a))
        t = QgsFeature(ticks.fields()); t.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(p.x() - n[0] * tick_len / 2, p.y() - n[1] * tick_len / 2), QgsPointXY(p.x() + n[0] * tick_len / 2, p.y() + n[1] * tick_len / 2)])); t.setAttributes([f["label"]]); tf_.append(t)
        lab = str(f["label"]); span_mm = len(lab) * h_mm * 0.62; off = tick_len / 2 + gap + (span_mm / 2) / mm_per_m
        ax, ay = p.x() + n[0] * off, p.y() + n[1] * off
        rot = math.degrees(a) + 90.0
        while rot > 90: rot -= 180
        while rot <= -90: rot += 180
        l = QgsFeature(labs.fields()); l.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(ax, ay))); l.setAttributes([lab, rot]); lf_.append(l)
        # paper-space rectangle for the collision count
        px, py = ax * mm_per_m, ay * mm_per_m; rect = ShPolygon([(px - span_mm / 2, py - h_mm / 2), (px + span_mm / 2, py - h_mm / 2), (px + span_mm / 2, py + h_mm / 2), (px - span_mm / 2, py + h_mm / 2)])
        polys.append(sh_aff.rotate(rect, rot, origin=(px, py)))
    tp.addFeatures(tf_); lp.addFeatures(lf_); ticks.updateExtents(); labs.updateExtents()
    pairs = 0
    if polys:
        tree = STRtree(polys)
        for i, pg in enumerate(polys):
            for j in tree.query(pg):
                if j > i and polys[j].intersects(pg) and polys[j].intersection(pg).area > 0.3: pairs += 1
    ticks.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple({"color": "#1F1F1F", "width": "0.5", "width_unit": "MM"})))
    labs.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "circle", "color": "0,0,0,0", "outline_style": "no", "size": "0.1"})))
    ps = QgsPalLayerSettings(); ps.fieldName = "label"; ps.enabled = True
    tfs = QgsTextFormat(); fs = QFont("Arial"); fs.setBold(True); tfs.setFont(fs); tfs.setSize(8.5); tfs.setColor(QColor("#1F1F1F"))
    bs = QgsTextBufferSettings(); bs.setEnabled(True); bs.setSize(1.0); bs.setColor(QColor("#FFFFFF")); tfs.setBuffer(bs); ps.setFormat(tfs)
    ps.placement = Qgis.LabelPlacement.OverPoint; ps.quadOffset = Qgis.LabelQuadrantPosition.Over; ps.priority = 5
    ps.placementSettings().setOverlapHandling(Qgis.LabelOverlapHandling.PreventOverlap)
    ps.dataDefinedProperties().setProperty(QgsPalLayerSettings.Property.LabelRotation, QgsProperty.fromExpression(ROT_EXPR))
    labs.setLabelsEnabled(True); labs.setLabeling(QgsVectorLayerSimpleLabeling(ps))
    proj.addMapLayer(ticks, False); proj.addMapLayer(labs, False); return ticks, labs, pairs, len(lf_)
ROT_EXPR = os.environ.get("CATMAP_ROT_EXPR", '-"rot"')   # QGIS label rotation is clockwise: the counter-clockwise angle negated

# ------------------------------------------------------------------ the page
def fitted_scale(extent):
    """mm of paper per metre once the extent is fitted into the map item (the map keeps the aspect by widening the extent)."""
    return min(MAP_W / extent.width(), MAP_H / extent.height())

def label(lay, text, x, y, w, h, size, bold=False, align=Qt.AlignLeft, color="#1F1F1F"):
    it = QgsLayoutItemLabel(lay); it.setText(text); tf = QgsTextFormat(); f = QFont("Arial"); f.setBold(bold); tf.setFont(f); tf.setSize(size); tf.setColor(QColor(color)); it.setTextFormat(tf)
    it.setHAlign(align); lay.addLayoutItem(it); it.attemptMove(QgsLayoutPoint(x, y, MM)); it.attemptResize(QgsLayoutSize(w, h, MM)); return it

def build(code):
    name = CATCHMENT[code]; ext = cat_extent(code); mm_per_m = fitted_scale(ext)
    if STEP_OPT == "auto":
        t5, l5, pairs5, n5 = station_layers(code, 500, mm_per_m)
        if n5 and pairs5 / n5 > 0.06:
            proj.removeMapLayer(t5.id()); proj.removeMapLayer(l5.id()); ticks, labs, pairs, n = station_layers(code, 1000, mm_per_m); step = 1000
        else: ticks, labs, pairs, n, step = t5, l5, pairs5, n5, 500
    else:
        step = int(STEP_OPT); ticks, labs, pairs, n = station_layers(code, step, mm_per_m)
    print("%s: scale 1:%.0f, stations every %d m: %d labels, %d colliding pairs" % (code, 1000 / mm_per_m, step, n, pairs))
    lay = QgsPrintLayout(proj); lay.initializeDefaults(); lay.setName("catmap_" + code); pg = lay.pageCollection().page(0); pg.setPageSize(QgsLayoutSize(PAGE_W, PAGE_H, MM))
    frame = QgsLayoutItemShape(lay); frame.setShapeType(QgsLayoutItemShape.Rectangle); sym = QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": "#000000", "outline_width": "0.4", "outline_width_unit": "MM"}); frame.setSymbol(sym)
    lay.addLayoutItem(frame); frame.attemptMove(QgsLayoutPoint(10, 10, MM)); frame.attemptResize(QgsLayoutSize(PAGE_W - 20, PAGE_H - 20, MM))
    label(lay, "%s CATCHMENT — KEY PLAN" % name.upper(), 15, 13, 600, 15, 30, bold=True)
    sub = "Channels and dykes with their names, their extents (designed bed in yellow, corridor with the embankments and access roads in brown) and the stations every %d m; dam axes in magenta" % step
    if DIM_FP: sub += "; the flood protection channels and dykes in grey are not part of this set"
    label(lay, sub, 15, 30, 760, 8, 13)
    label(lay, "%s    Revision %s    %s" % (DOC_NO_PREFIX, REV, DATE), 15, 40, 400, 7, 12)
    label(lay, "Plan and profile drawings of the flood protection channels — %s catchment" % name, 420, 40, 406, 7, 12, align=Qt.AlignRight)
    m = QgsLayoutItemMap(lay); lay.addLayoutItem(m); m.attemptMove(QgsLayoutPoint(MAP_X, MAP_Y, MM)); m.attemptResize(QgsLayoutSize(MAP_W, MAP_H, MM))
    m.setCrs(UTM); m.setFrameEnabled(True); m.setFrameStrokeWidth(QgsLayoutMeasurement(0.4, MM)); m.setBackgroundColor(QColor("#FFFFFF"))
    layers = [labs, ticks, dams, ch, bed, cor, google]; m.setLayers(layers); m.setKeepLayerSet(True); m.zoomToExtent(ext)
    # legend, bottom left inside the map, white box
    lg = QgsLayoutItemLegend(lay); lay.addLayoutItem(lg); lg.setLinkedMap(m); lg.setAutoUpdateModel(False); lg.setTitle(""); root = lg.model().rootGroup()
    for child in list(root.children()): root.removeChildNode(child)
    g1 = root.addGroup("Channels and dykes"); g1.addLayer(ch); g2 = root.addGroup("Extents"); g2.addLayer(bed); g2.addLayer(cor); g3 = root.addGroup("Stations and dams"); g3.addLayer(ticks); g3.addLayer(dams)
    for node in (g1.findLayer(ch.id()), g2.findLayer(bed.id()), g2.findLayer(cor.id()), g3.findLayer(ticks.id()), g3.findLayer(dams.id())):
        if node is not None and node.layer() is ch: node.setCustomProperty("legend/title-style", "hidden")
    for sty, size, bold in ((QgsLegendStyle.Group, 12.0, True), (QgsLegendStyle.Subgroup, 11.0, True), (QgsLegendStyle.SymbolLabel, 10.0, False)):
        f = QFont("Arial"); f.setPointSizeF(size); f.setBold(bold); lg.rstyle(sty).setFont(f)
    lg.setSymbolWidth(13.0); lg.setSymbolHeight(5.0); lg.setBackgroundEnabled(True); lg.setBackgroundColor(QColor(255, 255, 255, 235)); lg.setFrameEnabled(True); lg.setFrameStrokeWidth(QgsLayoutMeasurement(0.3, MM))
    LG_W, LG_H = 128.0, 108.0   # a fixed box: resize-to-contents reported a stale size and the box ran below the map
    lg.setResizeToContents(False); lg.setLegendFilterByMapEnabled(False); lg.attemptResize(QgsLayoutSize(LG_W, LG_H, MM)); lg.attemptMove(QgsLayoutPoint(MAP_X + 4, MAP_Y + MAP_H - 4 - LG_H, MM)); lg.refresh()
    # scale bar and north
    sb = QgsLayoutItemScaleBar(lay); lay.addLayoutItem(sb); sb.setLinkedMap(m); sb.setStyle("Single Box"); sb.setUnits(Qgis.DistanceUnit.Meters); sb.setSegmentSizeMode(Qgis.ScaleBarSegmentSizeMode.Fixed)
    seg = 1000 if mm_per_m > 0.04 else (2000 if mm_per_m > 0.02 else 5000); sb.setNumberOfSegments(4); sb.setUnitsPerSegment(seg); sb.setNumberOfSegmentsLeft(0); sb.setMapUnitsPerScaleBarUnit(1000); sb.setUnitLabel("km")
    sb.setBackgroundEnabled(True); sb.setBackgroundColor(QColor(255, 255, 255, 220)); sb.attemptMove(QgsLayoutPoint(MAP_X + MAP_W - 4 - 4 * seg * mm_per_m - 24, MAP_Y + MAP_H - 16, MM))
    n_ = label(lay, "N\n▲", MAP_X + MAP_W - 24, MAP_Y + 6, 18, 16, 16, bold=True, align=Qt.AlignHCenter); n_.setBackgroundEnabled(True); n_.setBackgroundColor(QColor(255, 255, 255, 200))
    label(lay, "Scale 1:%s (A1)    Background: Google satellite image    Coordinates: WGS 84 / UTM zone 40N" % "{:,}".format(int(round(1000 / mm_per_m, -2))).replace(",", " "), MAP_X + 4, MAP_Y + MAP_H + 3, 500, 7, 10)
    proj.layoutManager().addLayout(lay)
    exp = QgsLayoutExporter(lay)
    if PNG:
        path = os.path.join(OUT_DIR, "_catmap_%s%s.png" % (code, "_sw" if DIM_FP else "")); st = QgsLayoutExporter.ImageExportSettings(); st.dpi = 150; rc = exp.exportToImage(path, st)
    else:
        path = os.path.join(OUT_DIR, "_catmap_%s%s.pdf" % (code, "_sw" if DIM_FP else "")); st = QgsLayoutExporter.PdfExportSettings(); st.dpi = 200; st.forceVectorOutput = True; st.rasterizeWholeImage = False
        try: st.textRenderFormat = Qgis.TextRenderFormat.AlwaysText
        except Exception: pass
        rc = exp.exportToPdf(path, st)
    print(code, "ok" if rc == QgsLayoutExporter.Success else "FAILED %s" % rc, path, "%.1f MB" % (os.path.getsize(path) / 1e6) if os.path.exists(path) else "")
    return rc == QgsLayoutExporter.Success

ok = all([build(c) for c in CODES]); app.exitQgis(); sys.exit(0 if ok else 1)
