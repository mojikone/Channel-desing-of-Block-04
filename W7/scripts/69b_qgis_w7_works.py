"""Step 69b (W7) - the culverts, dykes and widths of the R4 report in the engineer's open QGIS project, for his check (run INSIDE
QGIS through the MCP execute_code tool; the project is never saved by us). Group "W7 culverts, dykes, widths (R9 200 yr)":
  proposed box culverts at the road crossings (labelled cells x width x height), the existing barrels on file within 150 m,
  the dykes by adopted height (labelled), the designed bed (span) polygons with the width labels of the reaches."""
from qgis.core import (QgsProject, QgsVectorLayer, QgsSingleSymbolRenderer, QgsMarkerSymbol, QgsLineSymbol, QgsFillSymbol, QgsGraduatedSymbolRenderer, QgsRendererRange,
                       QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsTextFormat, QgsTextBufferSettings, Qgis)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtWidgets import QApplication
CB = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Claude Block 04"; W7 = CB + r"\W7"
G = "W7 culverts, dykes, widths (R9 200 yr)"
def labels(layer, expr, size=7.5, line=False):
    pal = QgsPalLayerSettings(); pal.fieldName = expr; pal.isExpression = True; pal.enabled = True
    tf = QgsTextFormat(); f = QFont("Arial"); f.setBold(True); tf.setFont(f); tf.setSize(size); tf.setColor(QColor("#1F1F1F"))
    b = QgsTextBufferSettings(); b.setEnabled(True); b.setSize(0.9); b.setColor(QColor("#FFFFFF")); tf.setBuffer(b); pal.setFormat(tf)
    if line: pal.placement = Qgis.LabelPlacement.Line
    layer.setLabelsEnabled(True); layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
if QApplication.activeModalWidget() is not None: raise SystemExit("a modal dialog is open in QGIS: nothing removed, run again later")
proj = QgsProject.instance(); root = proj.layerTreeRoot(); done = []
if root.findGroup(G) is None: root.insertGroup(0, G)
grp = root.findGroup(G)
def add(name, src, renderer, label=None, line=False, checked=True):
    for old in proj.mapLayersByName(name): proj.removeMapLayer(old.id())
    l = QgsVectorLayer(src, name, "ogr")
    if not l.isValid(): done.append("INVALID " + name); return None
    l.setRenderer(renderer)
    if label: labels(l, label, line=line)
    proj.addMapLayer(l, False); node = grp.addLayer(l); node.setItemVisibilityChecked(checked); done.append("%s: %d features" % (name, l.featureCount())); return l
GP = W7 + r"\gis\sewergems_200yr_R9.gpkg"
add("Proposed box culverts (cells x width x height, m)", W7 + r"\culverts\crossings.gpkg|layername=crossings", QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "square", "color": "#FFC000", "outline_color": "#1F1F1F", "outline_width": "0.3", "size": "3.4"})), '"size"')
add("Existing culvert barrels on file within 150 m", W7 + r"\culverts\crossings.gpkg|layername=existing_barrels_near", QgsSingleSymbolRenderer(QgsLineSymbol.createSimple({"color": "#7030A0", "width": "0.9", "width_unit": "MM"})), '"size"', line=True)
dk = add("Dykes by adopted height (m)", W7 + r"\dykes\dykes.gpkg|layername=dykes", QgsGraduatedSymbolRenderer("H_m", [QgsRendererRange(lo, hi, QgsLineSymbol.createSimple({"color": c, "width": "1.3", "width_unit": "MM"}), lab) for lo, hi, lab, c in (
    (0, 2.0, "1.0 to 2.0", "#A9D18E"), (2.0, 2.5, "2.0 to 2.5", "#70AD47"), (2.5, 3.5, "2.5 to 3.5", "#C55A11"), (3.5, 10, "3.5 to 4.5", "#C00000"))]), 'format_number("H_m", 1) || \' m\'', line=True)
add("Designed bed, 200 yr (R9)", GP + "|layername=bed", QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({"color": "233,113,50,150", "outline_color": "#A0522D", "outline_width": "0.2", "outline_width_unit": "MM"})))
add("Reaches: bed width (m)", GP + "|layername=segments", QgsSingleSymbolRenderer(QgsLineSymbol.createSimple({"color": "#1F3B63", "width": "0.3", "width_unit": "MM"})), 'format_number("span_m", 1)', line=True, checked=False)
print("\n".join(done))
