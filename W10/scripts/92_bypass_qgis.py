"""Step 92 (W10, his request 2026-10-14) - the QGIS project of the bypass road design package: every layer of the package's GIS
folder, styled and labelled as in the main project, relative paths, WGS 84 / UTM 40N. Run after 90_submission.py:
    "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" 92_bypass_qgis.py [--out "<submission folder>"]"""
import os, sys
from qgis.core import (QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem, QgsLineSymbol, QgsFillSymbol, QgsMarkerSymbol,
                       QgsSingleSymbolRenderer, QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling, Qgis, QgsSimpleLineCallout)
from qgis.PyQt.QtGui import QFont, QColor
HERE = os.path.dirname(os.path.abspath(__file__)); W10 = os.path.dirname(HERE); CB = os.path.dirname(W10); B4 = os.path.dirname(CB)
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
OUT = opt("--out", os.path.join(B4, "Deliverables", "2 Submission 13102026")); BP = os.path.join(OUT, "09 Bypass road design package"); G = os.path.join(BP, "GIS")
app = QgsApplication([], False); app.initQgis()
UTM = QgsCoordinateReferenceSystem("EPSG:32640")
proj = QgsProject.instance(); proj.setCrs(UTM); proj.setTitle("Block 04 - Bypass road design package"); proj.writeEntry("Paths", "/Absolute", False)
root = proj.layerTreeRoot(); made = []

def vec(fn, name, subset=None, sidecar_qml=True):
    path = os.path.join(G, fn); l = QgsVectorLayer(path, name, "ogr")
    if not l.isValid(): print("  not valid:", fn); return None
    if subset: l.setSubsetString(subset)
    qml = os.path.splitext(path)[0] + ".qml"
    if sidecar_qml and os.path.exists(qml): l.loadNamedStyle(qml)
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
def label(l, expr, size=8.0, colour="#1F1F1F", bold=True, on_line=False, around=False, callout=False, buffer=0.9):
    if l is None: return
    pal = QgsPalLayerSettings(); pal.fieldName = expr; pal.isExpression = True; pal.enabled = True
    tf = QgsTextFormat(); f = QFont("Arial"); f.setBold(bold); tf.setFont(f); tf.setSize(size); tf.setColor(QColor(colour))
    b = QgsTextBufferSettings(); b.setEnabled(True); b.setSize(buffer); b.setColor(QColor("#FFFFFF")); tf.setBuffer(b); pal.setFormat(tf)
    if on_line: pal.placement = Qgis.LabelPlacement.Line; pal.lineSettings().setPlacementFlags(Qgis.LabelLinePlacementFlag.AboveLine | Qgis.LabelLinePlacementFlag.MapOrientation)
    if around: pal.placement = Qgis.LabelPlacement.OrderedPositionsAroundPoint; pal.dist = 1.5
    if callout:
        co = QgsSimpleLineCallout(); co.setEnabled(True); co.setMinimumLength(1.0); pal.setCallout(co)
    l.setLabelsEnabled(True); l.setLabeling(QgsVectorLayerSimpleLabeling(pal))
def relabel(l, expr):
    """Keep his style, point the label expression at the fields of this layer."""
    if l is None or l.labeling() is None: label(l, expr, 7.5, "#003CA0"); return
    pal = l.labeling().settings(); pal.fieldName = expr; pal.isExpression = True; pal.enabled = True; l.setLabeling(QgsVectorLayerSimpleLabeling(pal)); l.setLabelsEnabled(True)
def group(parent, name, layers, visible=True, expanded=False):
    g = parent.addGroup(name)
    for l in layers:
        if l is not None: g.addLayer(l)
    g.setItemVisibilityChecked(visible); g.setExpanded(expanded); return g

# ---- the bypass and its culverts
byp = vec("North Batinah Bypass alignment (planned).shp", "North Batinah Bypass (planned alignment)", sidecar_qml=False); line(byp, "#7F6000", 1.1, "dash")
cul = vec("Proposed box culverts under the bypass.shp", "Proposed box culverts under the bypass (cells x width x height, m)", sidecar_qml=False)
marker(cul, "#FFC000", "square", 3.2); label(cul, '"size"', 8.0, around=True, callout=True)
hw = vec("Batinah Highway.shp", "Batinah Highway", sidecar_qml=False); line(hw, "#1F1F1F", 0.9)
crd = vec("Batinah Coastal Road.shp", "Batinah Coastal Road", sidecar_qml=False); line(crd, "#5A5A5A", 0.7)
group(root, "Bypass and culverts", [cul, byp], visible=True, expanded=True)
group(root, "Roads", [hw, crd], visible=True)
# ---- the channels, reaches and design points (his styles beside the files)
ch = vec("Channels and dykes.shp", "Channels and dykes")
rc = vec("Channel reaches - 200-year design and the sizes of all return periods.shp", "Channel reaches: 200-year size (W bed width, S slope); every return period in the table")
relabel(rc, '"SGLabel" || \'\\n\' || \'W: \' || format_number("span_200", 1) || \' m\' || \'\\n\' || \'S: \' || format_number("slope_200", 4)')
pts = vec("Design points.shp", "Design points (SewerGEMS nodes: D wadi depth, R raise)")
group(root, "Channels and design", [pts, rc, ch], visible=True, expanded=True)
# ---- the extents
bed = vec("Channel extent 200-year (bed and corridor).shp", "Channel bed (200-year)", subset="\"kind\" = 'bed'", sidecar_qml=False); fill(bed, "157,195,230,140", "#2E75B6", 0.3)
cor = vec("Channel extent 200-year (bed and corridor).shp", "Channel corridor (200-year, bed + embankments + access road)", subset="\"kind\" = 'corridor'", sidecar_qml=False); fill(cor, "0,0,0,0", "#C00000", 0.5)
dyk = vec("Dyke extent.shp", "Dyke extent (15.5 m each side)", sidecar_qml=False); fill(dyk, "0,0,0,0", "#7030A0", 0.5)
group(root, "Extents (200-year)", [cor, bed, dyk], visible=True)
# ---- background
google = QgsRasterLayer("type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=18&zmin=0", "Google satellite", "wms")
if google.isValid(): proj.addMapLayer(google, False); group(root, "Background", [google], visible=True)
path = os.path.join(BP, "Block 04 - Bypass road design package.qgz"); ok = proj.write(path); print("project:", path, "written" if ok else "FAILED", "| layers:", len(made))
app.exitQgis(); sys.exit(0 if ok else 1)
