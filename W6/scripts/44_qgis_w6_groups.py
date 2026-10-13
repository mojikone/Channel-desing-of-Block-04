"""Step 44 - restore the W6 groups in the engineer's QGIS project (written after the crash of 2026-10-11 04:01, when the Block 04
instance died with its unsaved layer tree). Runs INSIDE QGIS (the MCP execute_code tool or the Python console); project API only.
Adds, styles and groups, replacing layers of the same name:
  "W6 design points": Flow points (HMS, W6) | Channel ends on receiving channel (W6) [unchecked] | Fix points (W6) |
                      500 m downstream of fix points (W6) | GDP grade breaks (W6, live) | Design points, all kinds (W6, final) |
                      Design segments between points (W6, final)
  "W6 wadi depth":    Wadi sections / Wadi depth at points for HAW, SAK, SAR, SHA and the calibration pair of SHACH1-12
and re-applies the channel symbology W3/maps/styles/channels_dykes.qml to "Channels and Dykes 04102026" (its saved renderer is
"No Symbols"). The project is NOT saved: that stays the engineer's decision."""
from qgis.core import QgsProject, QgsVectorLayer
CB = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Claude Block 04"
W6 = CB + r"\W6"; GIS = W6 + r"\gis"; GPKG = W6 + r"\output\design_points.gpkg"
LAYERS = [  # (group, name, source, qml, checked)
    ("W6 design points", "Flow points (HMS, W6)", GPKG + "|layername=flow_points", GIS + r"\flow_points.qml", True),
    ("W6 design points", "Channel ends on receiving channel (W6)", GPKG + "|layername=junction_points", GIS + r"\junction_points.qml", False),
    ("W6 design points", "Fix points (W6)", GPKG + "|layername=fix_points", GIS + r"\fix_points.qml", True),
    ("W6 design points", "500 m downstream of fix points (W6)", GPKG + "|layername=fix_downstream", GIS + r"\fix_downstream.qml", True),
    ("W6 design points", "GDP grade breaks (W6, live)", W6 + r"\gdp\Block4_channel_breaks.shp", CB + r"\W5\gis\Block4_channel_breaks.qml", True),
    ("W6 design points", "Design points, all kinds (W6, final)", W6 + r"\final\Block4_design_points.shp", GIS + r"\design_points_final.qml", True),
    ("W6 design points", "Design segments between points (W6, final)", W6 + r"\final\Block4_design_segments.shp", GIS + r"\design_segments_final.qml", True),
]
for g in ("HAW", "SAK", "SAR", "SHA"):
    LAYERS.append(("W6 wadi depth", "Wadi sections, %s (W6)" % g, W6 + r"\wadi\%s_wadi_sections.shp" % g, GIS + r"\wadi_sections.qml", True))
    LAYERS.append(("W6 wadi depth", "Wadi depth at points, %s (W6)" % g, W6 + r"\wadi\%s_wadi_points.shp" % g, GIS + r"\wadi_points.qml", True))
LAYERS.append(("W6 wadi depth", "Wadi section, calibration SHACH1-12 (W6)", W6 + r"\wadi\calibration_SHACH1-12_wadi_sections.shp", GIS + r"\wadi_sections.qml", True))
LAYERS.append(("W6 wadi depth", "Wadi depth, calibration SHACH1-12 (W6)", W6 + r"\wadi\calibration_SHACH1-12_wadi_points.shp", GIS + r"\wadi_points.qml", True))

proj = QgsProject.instance(); root = proj.layerTreeRoot(); done = []
for gname in ("W6 wadi depth", "W6 design points"):
    if root.findGroup(gname) is None: root.insertGroup(0, gname)
for gname, name, src, qml, checked in LAYERS:
    for old in proj.mapLayersByName(name): proj.removeMapLayer(old.id())
    lyr = QgsVectorLayer(src, name, "ogr")
    if not lyr.isValid(): done.append("INVALID " + name + " <- " + src); continue
    proj.addMapLayer(lyr, False); node = root.findGroup(gname).addLayer(lyr); node.setItemVisibilityChecked(checked)
    msg, ok = lyr.loadNamedStyle(qml); lyr.triggerRepaint(); done.append("%s: %d features%s" % (name, lyr.featureCount(), "" if ok else "  STYLE FAILED: " + str(msg)))   # PyQGIS returns (message, success)
for lyr in proj.mapLayersByName("Channels and Dykes 04102026"):
    msg, ok = lyr.loadNamedStyle(CB + r"\W3\maps\styles\channels_dykes.qml"); lyr.triggerRepaint(); done.append("Channels and Dykes 04102026: symbology %s" % ("re-applied" if ok else str(msg)))
print("\n".join(done))
