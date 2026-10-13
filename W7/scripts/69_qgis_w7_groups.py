"""Step 69 (W7) - the R9 review groups in the engineer's open QGIS project (run INSIDE QGIS through the MCP execute_code tool; the
project is never saved by us). From W7/gis/sewergems_200yr_R9.gpkg (step 51 with --rev R9) and the QML styles of W6 (gis/qml):
  "W7 SewerGEMS 200 yr R9":        segments (SGLabel, width, slope stacked), manholes, outfalls, channels, bed (span), corridor
  "W7 check R8 to R9 (temporary)": chk_inverts (points whose invert moved, old/new, blue up / red down), chk_conduits (conduits
                                   whose size, slope or invert changed, old values in brackets, colour by the slope change)
Layers of the same name are replaced; nothing is removed while a modal dialog of his is open (the crash of 2026-10-11)."""
from qgis.core import QgsProject, QgsVectorLayer
from qgis.PyQt.QtWidgets import QApplication
CB = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Claude Block 04"
W7 = CB + r"\W7"; GPKG = W7 + r"\gis\sewergems_200yr_R9.gpkg"; QML = W7 + r"\gis\qml"
G1, G2 = "W7 SewerGEMS 200 yr R9", "W7 check R8 to R9 (temporary)"
LAYERS = [  # (group, name, gpkg layer, qml, checked)
    (G1, "Corridor, span + 15.5 m (W7, R9 200 yr)", "corridor", "r4_corridor.qml", True),
    (G1, "Channel bed, designed span (W7, R9 200 yr)", "bed", "r4_bed.qml", True),
    (G1, "Channels (W7)", "channels", "r4_channels.qml", True),
    (G1, "SewerGEMS segments: width and slope (W7, R9 200 yr)", "segments", "r4_segments.qml", True),
    (G1, "Manholes (W7, R9)", "manholes", "r4_manholes.qml", True),
    (G1, "Outfalls (W7, R9)", "outfalls", "r4_outfalls.qml", True),
    (G2, "Check: inverts changed R8 to R9 (temporary)", "chk_inverts", "chk_inverts.qml", True),
    (G2, "Check: conduits changed R8 to R9 (temporary)", "chk_conduits", "chk_conduits.qml", True),
]
if QApplication.activeModalWidget() is not None: raise SystemExit("a modal dialog is open in QGIS: nothing removed, run again later")
proj = QgsProject.instance(); root = proj.layerTreeRoot(); done = []
for gname in (G2, G1):
    if root.findGroup(gname) is None: root.insertGroup(0, gname)
for gname, name, layer, qml, checked in LAYERS:
    for old in proj.mapLayersByName(name): proj.removeMapLayer(old.id())
    lyr = QgsVectorLayer(GPKG + "|layername=" + layer, name, "ogr")
    if not lyr.isValid(): done.append("INVALID " + name); continue
    proj.addMapLayer(lyr, False); node = root.findGroup(gname).addLayer(lyr); node.setItemVisibilityChecked(checked)
    msg, ok = lyr.loadNamedStyle(QML + "\\" + qml); lyr.triggerRepaint(); done.append("%s: %d features%s" % (name, lyr.featureCount(), "" if ok else "  STYLE FAILED: " + str(msg)))
# the earlier revision groups stay, collapsed and unchecked
for g in root.findGroups():
    if g.name().startswith("W6 SewerGEMS") or g.name().startswith("W6 check"): g.setExpanded(False); g.setItemVisibilityChecked(False)
print("\n".join(done))
