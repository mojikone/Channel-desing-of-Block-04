"""Step 66 (W8) - map figures for report R5: the reach map redrawn (channels in the agreed colours with their names, reach numbers
along the line) and the global-catchment map added; the rest as W7. Original W7 header:
Step 66 (W7) - map figures for report R4: the Q200 junction maps and the HEC-HMS model figure from the Basin 6 elements
(Shafan 08 and its full catchment in the channel hydrology), the model figure drawn from the element layers instead of the
screenshot; everything else as step 26 of W3 (R2/R3). Output W7/maps/png_r4 (the unchanged maps were copied from W3 png_r3).
Original header of step 26:
R2 changes against step 24 (R1): channel category map dropped (the routes map with the engineer's own symbology carries the
colours; maps where the categories do not matter draw channels and dykes in one colour); dam names labelled in black with
a thin white halo instead of catchment names; scale bar left where the template puts it (the frame line through the bar)
with a segment length chosen from the map scale; key table and data box kept 3 mm inside the frame; the flood-alignment and
land-use maps on the Google image with a dimmed hillshade; the HEC-HMS figure is the engineer's screenshot georeferenced
(step 25) in the layout; the zoomed Q200 map covers the dams and every element downstream of them; the sediment map is
coloured by the sediment delivered in 50 years (Mcm).
run:  "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" 26_maps_qgis_r2.py [keys]   -> maps/png_r2/<key>.png, maps/Block04_R2_maps.qgz
"""
import os, sys, json
from qgis.core import (QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsPrintLayout, QgsReadWriteContext, QgsLayoutItemLabel, QgsLayoutItemMap, QgsLayoutItemLegend,
                       QgsLayoutItemScaleBar, QgsLayoutFrame, QgsLayoutItemManualTable, QgsLayoutItemHtml, QgsLayoutExporter, QgsRectangle, QgsCoordinateReferenceSystem, QgsFillSymbol, QgsLineSymbol,
                       QgsMarkerSymbol, QgsSingleSymbolRenderer, QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsGraduatedSymbolRenderer, QgsRendererRange, QgsPalLayerSettings,
                       QgsVectorLayerSimpleLabeling, QgsTextFormat, QgsTextBufferSettings, QgsSingleBandPseudoColorRenderer, QgsColorRampShader, QgsRasterShader, QgsSingleBandGrayRenderer,
                       QgsContrastEnhancement, QgsMapLayerLegendUtils, QgsTableCell, QgsLayoutSize, QgsLayoutPoint, QgsUnitTypes, QgsLegendStyle, QgsLayoutMeasurement, QgsLayoutItemPage,
                       QgsLayoutItem, QgsLayoutTable, QgsFeatureRequest, Qgis)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtXml import QDomDocument
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", r"C:\Program Files\QGIS 3.44.8\apps\qgis-ltr"), True)
app = QgsApplication([], False); app.initQgis()

HERE = os.path.dirname(os.path.abspath(__file__)); W8 = os.path.dirname(HERE); CB04 = os.path.dirname(W8); B4 = os.path.dirname(CB04); W3 = os.path.join(CB04, "W3"); W7 = os.path.join(CB04, "W7")   # W3: map data, styles, template; W7: the Basin 6 elements, the R9 design, dykes; W8: culverts, GCA, the output
DATA = os.path.join(W3, "maps", "data"); STY = os.path.join(W3, "maps", "styles"); PNG = os.path.join(W8, "maps", os.environ.get("MAPS_OUT", "png_r7")); os.makedirs(PNG, exist_ok=True)   # R3: MAPS_OUT=png_r3
TEMPLATE_XML = os.path.join(W3, "maps", "template", "ibri_W17_S1_zones_layout.xml")
# the stormwater report (W8): MAPS_DIM_FP=1 draws the flood protection channels and dykes in grey and leaves their designed
# reaches, beds, outfalls, culverts and dykes out of the maps (MAPS_OUT=png_sw)
DIM_FP = bool(os.environ.get("MAPS_DIM_FP")); NOFP_SEG = "NOT (\"Channel\" LIKE '%-FP')"
def _dim_fp(renderer):
    """categorised channel renderer: the FP categories in grey, labelled as outside this report"""
    if renderer is None or renderer.type() != "categorizedSymbol": return
    for i, c in enumerate(renderer.categories()):
        if str(c.value()).startswith("FP"):
            sym = c.symbol().clone(); sym.setColor(QColor("#A6A6A6")); renderer.updateCategorySymbol(i, sym); renderer.updateCategoryLabel(i, str(c.label()) + " (not in this report)")
SUBTITLE = "Flood Protection Scheme in North and South Al Batinah — Block 04"
CREDIT = {True: "Background: Google satellite image and the hillshade of the 10 m terrain model", False: "Background: hillshade of the 10 m terrain model"}
UTM = QgsCoordinateReferenceSystem("EPSG:32640"); MM = QgsUnitTypes.LayoutMillimeters
ext = json.load(open(os.path.join(DATA, "extent.json"))); RS = ext["raster_stats"]
DAMS9 = ["Hawasinah 02", "Hawasinah 11", "Hawasinah EX", "Shafan 02", "Shafan 08", "Sarami 03", "Sarami 05", "Sakhin 04", "Sakhin 08"]
LABEL = {"Hawasinah EX": "Hawasinah UP", "Sakhin 08": "Sakhin 08 (Mehmum)"}; lab = lambda d: LABEL.get(d, d)
W = "W:/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/06-WORKING/"
# depth_200yr = the clip of the 820 MB server raster made by step 13 (R3): nothing is read outside the project folders
SRC = {"channels": os.path.join(B4, "Hydrology", "SHP", "temp", "Channels and Dykes 04102026.shp"), "dam_axis": os.path.join(B4, "Hydrology", "SHP", "Block 4 Dams", "Dams updated.shp"), "dam_dikes": os.path.join(B4, "Hydrology", "SHP", "Block 4 Dams", "Dikes.shp"),
       "fsl_polygon": W + "04-Hydraulic/05 Small Tasks/18 Channel Design/SHP/Block 04 Dams/Polygon_FSL.shp", "crest_polygon": W + "04-Hydraulic/05 Small Tasks/18 Channel Design/SHP/Block 04 Dams/Ppygon_Crest_Level.shp",
       "depth_200yr": os.path.join(W3, "maps", "data", "depth_200yr_plain.tif"), "landuse": W + "13-Study and Design/01-FS and PD/00-General/02-Land Use/ALL_MOH_CLEANED/LandUSE_block4.shp",
       "highway": W + "03-Hydrology/01 GIS DATA/SHP/Bathinah Highway CL.shp", "coastal_road": W + "03-Hydrology/01 GIS DATA/SHP/Batinah Coastal RD CL.shp", "expressway": W + "03-Hydrology/01 GIS DATA/SHP/Muscat Expressway CL.shp",
       "bypass": os.path.join(B4, "Hydrology", "SHP", "Bypass road alignment", "North Batina Bypass.shp"), "pipeline_south": W + "04-Hydraulic/000 Correspond/02 Sent/2026.01.12 PDO pipeline/SHP/South/Pipeline.shp",
       "pipeline_north": W + "04-Hydraulic/000 Correspond/02 Sent/2026.01.12 PDO pipeline/SHP/North/Pipelines.shp", "culverts": "W:/2425 Supervision of Sultan Taymur Bin Faysal Road_MOTC&IT/06-WORKING/03-Hydrology/05_Shape Files/Culverts_RDs.shp"}
proj = QgsProject.instance(); proj.setCrs(UTM)

# ------------------------------------------------------------------ helpers
def label_layer(layer, field, size=7.5, colour="#1F3B63", bold=True, buffer=0.9, expression=False, italic=False, around_point=False, overlap=False, offset_mm=None):
    pal = QgsPalLayerSettings(); pal.fieldName = field; pal.isExpression = expression; pal.enabled = True
    tf = QgsTextFormat(); f = QFont("Arial"); f.setBold(bold); f.setItalic(italic); tf.setFont(f); tf.setSize(size); tf.setColor(QColor(colour))
    b = QgsTextBufferSettings(); b.setEnabled(True); b.setSize(buffer); b.setColor(QColor("#FFFFFF")); tf.setBuffer(b); pal.setFormat(tf)
    if around_point: pal.placement = Qgis.LabelPlacement.OrderedPositionsAroundPoint
    if offset_mm is not None: pal.dist = offset_mm
    if overlap:
        try: pal.placementSettings().setOverlapHandling(Qgis.LabelOverlapHandling.AllowOverlapIfRequired)
        except Exception as e: print("overlap setting:", e)
    layer.setLabelsEnabled(True); layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
def vec(path, name, layer=None, qml=None, subset=None):
    l = QgsVectorLayer(path if layer is None else f"{path}|layername={layer}", name, "ogr"); assert l.isValid(), path
    if qml and os.path.exists(os.path.join(STY, qml + ".qml")): l.loadNamedStyle(os.path.join(STY, qml + ".qml")); l.setLabelsEnabled(False)
    if subset: l.setSubsetString(subset)
    proj.addMapLayer(l, False); return l
def ras(path, name, qml=None, opacity=None):
    r = QgsRasterLayer(path, name); assert r.isValid(), path
    if qml and os.path.exists(os.path.join(STY, qml + ".qml")): r.loadNamedStyle(os.path.join(STY, qml + ".qml"))
    if opacity is not None: r.setOpacity(opacity)
    proj.addMapLayer(r, False); return r
def fill(l, color="0,0,0,0", outline="#C00000", width=0.5): l.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({"color": color, "outline_color": outline, "outline_width": str(width), "outline_width_unit": "MM"} if outline else {"color": color, "outline_style": "no"})))
def line(l, color, width=0.4, dash=None):
    props = {"color": color, "width": str(width), "width_unit": "MM", "capstyle": "round", "joinstyle": "round"}
    if dash: props["line_style"] = dash
    l.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple(props)))
def ramp_raster(path, name, lo, hi, colours, decimals=1):
    r = QgsRasterLayer(path, name); assert r.isValid(), path
    sh = QgsColorRampShader(lo, hi, None, QgsColorRampShader.Interpolated, QgsColorRampShader.Continuous); n = len(colours)
    sh.setColorRampItemList([QgsColorRampShader.ColorRampItem(lo + (hi - lo) * i / (n - 1), QColor(c), f"{lo + (hi - lo) * i / (n - 1):.{decimals}f}") for i, c in enumerate(colours)]); sh.setClip(False)
    rs = QgsRasterShader(); rs.setRasterShaderFunction(sh); rend = QgsSingleBandPseudoColorRenderer(r.dataProvider(), 1, rs); rend.setClassificationMin(lo); rend.setClassificationMax(hi); r.setRenderer(rend)
    from qgis.core import QgsColorRampLegendNodeSettings, QgsBasicNumericFormat
    st = QgsColorRampLegendNodeSettings(); fmt = QgsBasicNumericFormat(); fmt.setNumberDecimalPlaces(decimals); fmt.setShowTrailingZeros(False); st.setNumericFormat(fmt); sh.setLegendSettings(st)
    r.setOpacity(0.9); proj.addMapLayer(r, False); return r
def hillshade(opacity, name):
    hs_ = QgsRasterLayer(os.path.join(DATA, "hillshade.tif"), name); gr = QgsSingleBandGrayRenderer(hs_.dataProvider(), 1); ce = QgsContrastEnhancement(hs_.dataProvider().dataType(1))
    ce.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum); ce.setMinimumValue(60); ce.setMaximumValue(255); gr.setContrastEnhancement(ce); hs_.setRenderer(gr); hs_.setOpacity(opacity); proj.addMapLayer(hs_, False); return hs_

# ------------------------------------------------------------------ layers
hs = hillshade(0.5, "Terrain hillshade"); hs_dim = hillshade(0.28, "Terrain hillshade (dimmed)")
google = QgsRasterLayer("type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=18&zmin=0", "Google satellite", "wms"); sat = google if google.isValid() else None
if sat: sat.setOpacity(0.85); proj.addMapLayer(sat, False)
YELLOW_OUTLINE = {"color": "0,0,0,0", "outline_color": "#FFD966", "outline_width": "0.75", "outline_width_unit": "MM"}
cat_nolab = vec(os.path.join(DATA, "dam_catchments_results.gpkg"), "Dam catchment", "catchments"); cat_nolab.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(YELLOW_OUTLINE))); cat_nolab.setLabelsEnabled(False)
cat_k = vec(os.path.join(DATA, "dam_catchments_results.gpkg"), "Dam catchment", "catchments"); cat_k.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": "#1F1F1F", "outline_width": "0.6", "outline_width_unit": "MM"}))); cat_k.setLabelsEnabled(False)
# the dams: axes in magenta on top everywhere; names from an invisible point layer, black with a thin white halo (engineer, R2)
axes_l = vec(SRC["dam_axis"], "Dam axis", qml="dam_axis"); line(axes_l, "#FF00FF", 1.3)
dikes = vec(SRC["dam_dikes"], "Dam dyke", qml="dam_dikes"); line(dikes, "#FF00FF", 0.9, "dash")
def dam_labels(name, size=8.5, buffer=0.7):
    l = vec(os.path.join(DATA, "dams.gpkg"), name, "dam_points"); l.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "circle", "size": "0.1", "color": "0,0,0,0", "outline_style": "no"})))
    label_layer(l, '"label"', size, "#1F1F1F", True, buffer, expression=True, around_point=True, overlap=True, offset_mm=1.2); return l
dam_pts = dam_labels("_Dam names"); dam_pts_small = dam_labels("_Dam names (small)", 7.0, 0.6)
fslp = vec(SRC["fsl_polygon"], "Reservoir at full supply level", qml="fsl_polygon"); crp = vec(SRC["crest_polygon"], "Reservoir at crest level", qml="crest_polygon")
try:
    for _sl in crp.renderer().symbol().symbolLayers(): _sl.setStrokeWidth(0.22)   # the engineer's yellow outline, thinned so the FSL polygon shows (R3)
except Exception as _e: print("crest outline:", _e)
# channels: the engineer's own symbology (with readable class names) where the categories matter, one colour elsewhere
ch = vec(SRC["channels"], "Channels and dykes", qml="channels_dykes", subset='"Block" = 4')
CHNAMES = {"FP CH": "Flood protection channel", "Sw M CH": "Stormwater main channel", "Sw S CH": "Stormwater secondary channel", "FP D": "Flood protection dyke", "Sw M D": "Stormwater main dyke", "Sw S D": "Stormwater secondary dyke"}
_r = ch.renderer()
if _r is not None and _r.type() == "categorizedSymbol":
    for _i, _c in enumerate(_r.categories()): _r.updateCategoryLabel(_i, CHNAMES.get(str(_c.value()), str(_c.label())))
    for _i in sorted([_i for _i, _c in enumerate(_r.categories()) if _c.value() in (None, "") or str(_c.value()).strip() in ("", "NULL")], reverse=True): _r.deleteCategory(_i)
    if DIM_FP: _dim_fp(_r)
ch_names = vec(SRC["channels"], "Channels and dykes", qml="channels_dykes", subset='"Block" = 4')
_rn = ch_names.renderer()
if _rn is not None and _rn.type() == "categorizedSymbol":
    for _i, _c in enumerate(_rn.categories()): _rn.updateCategoryLabel(_i, CHNAMES.get(str(_c.value()), str(_c.label())))
    for _i in sorted([_i for _i, _c in enumerate(_rn.categories()) if _c.value() in (None, "") or str(_c.value()).strip() in ("", "NULL")], reverse=True): _rn.deleteCategory(_i)
    if DIM_FP: _dim_fp(_rn)
def line_labels(layer, field, size=6.6, buffer=0.8):
    """names along the lines, as the Block 6 channel-name figure: bold black, white halo, above the line, every name placed"""
    pal = QgsPalLayerSettings(); pal.fieldName = field; pal.isExpression = False; pal.enabled = True
    tf = QgsTextFormat(); f = QFont("Arial"); f.setBold(True); tf.setFont(f); tf.setSize(size); tf.setColor(QColor("#1F1F1F"))
    b = QgsTextBufferSettings(); b.setEnabled(True); b.setSize(buffer); b.setColor(QColor("#FFFFFF")); tf.setBuffer(b); pal.setFormat(tf)
    pal.placement = Qgis.LabelPlacement.Line
    try: ls = pal.lineSettings(); ls.setPlacementFlags(Qgis.LabelLinePlacementFlag.AboveLine | Qgis.LabelLinePlacementFlag.MapOrientation); ls.setMergeLines(False)
    except Exception as e: print("line settings:", e)
    try: pal.placementSettings().setOverlapHandling(Qgis.LabelOverlapHandling.AllowOverlapIfRequired)
    except Exception as e: print("overlap:", e)
    pal.dist = 0.6; pal.priority = 8; layer.setLabelsEnabled(True); layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
line_labels(ch_names, "Name")
ch1 = vec(SRC["channels"], "Channels and dykes", subset='"Block" = 4')
from qgis.core import QgsRuleBasedRenderer
_root = QgsRuleBasedRenderer.Rule(None)
_r1 = QgsRuleBasedRenderer.Rule(QgsLineSymbol.createSimple({"color": "#1F3B63", "width": "0.55", "width_unit": "MM", "capstyle": "round"}), 0, 0, "\"CHtt\" LIKE '% CH'", "Channel"); _root.appendChild(_r1)
_r2 = QgsRuleBasedRenderer.Rule(QgsLineSymbol.createSimple({"color": "#1F3B63", "width": "0.55", "width_unit": "MM", "capstyle": "round", "line_style": "dash"}), 0, 0, "\"CHtt\" LIKE '% D'", "Dyke"); _root.appendChild(_r2)
if DIM_FP:
    _r1.setFilterExpression("\"CHtt\" LIKE '% CH' AND NOT \"CHtt\" LIKE 'FP%'"); _r2.setFilterExpression("\"CHtt\" LIKE '% D' AND NOT \"CHtt\" LIKE 'FP%'")
    _root.appendChild(QgsRuleBasedRenderer.Rule(QgsLineSymbol.createSimple({"color": "#A6A6A6", "width": "0.5", "width_unit": "MM", "capstyle": "round"}), 0, 0, "\"CHtt\" = 'FP CH'", "Flood protection channel (not in this report)"))
    _root.appendChild(QgsRuleBasedRenderer.Rule(QgsLineSymbol.createSimple({"color": "#A6A6A6", "width": "0.5", "width_unit": "MM", "capstyle": "round", "line_style": "dash"}), 0, 0, "\"CHtt\" = 'FP D'", "Flood protection dyke (not in this report)"))
ch1.setRenderer(QgsRuleBasedRenderer(_root))   # the Type field is empty for the Block 4 rows; the class code CHtt tells channel from dyke
depth = ras(SRC["depth_200yr"], "Flood depth 200-year (m)", qml="depth_200yr", opacity=0.75)
lu = vec(SRC["landuse"], "Land use"); lucats = []
for key, col in (("Resedential", "#F4E04D"), ("Residential Commercial", "#F5A742"), ("Commercial", "#E03C31"), ("Government", "#3498DB"), ("Agricultural", "#4CAF50"), ("Industrial", "#9B59B6"), ("Tourism", "#1ABC9C"), ("Future Plans", "#BDC3C7"), ("Proposed", "#95A5A6"), ("Other", "#D5DBDB"), ("Not Classified", "#EAEDED")):
    lucats.append(QgsRendererCategory(key, QgsFillSymbol.createSimple({"color": col, "outline_style": "no"}), "Residential" if key == "Resedential" else key))
lu.setRenderer(QgsCategorizedSymbolRenderer("ParcelLand", lucats))
roads = []
for key, name, col, wd in (("highway", "Batinah Highway", "#1F1F1F", 0.9), ("coastal_road", "Batinah Coastal Road", "#5A5A5A", 0.7), ("expressway", "Batinah Expressway", "#000000", 0.9), ("bypass", "North Batinah Bypass (planned)", "#7F6000", 0.8)):
    l = vec(SRC[key], name); line(l, col, wd, "dash" if key == "bypass" else None); roads.append(l)
pipes = []
for key, name in (("pipeline_north", "OQ pipelines"),):
    l = vec(SRC[key], name); line(l, "#FF8C00", 0.8, "dash dot"); pipes.append(l)
try:
    l = vec(SRC["pipeline_south"], "OQ pipelines (south)"); line(l, "#FF8C00", 0.8, "dash dot"); pipes.append(l)
except Exception: pass
culv = vec(SRC["culverts"], "Existing culvert / bridge"); culv.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "square", "color": "#FFFFFF", "outline_color": "#1F1F1F", "outline_width": "0.3", "size": "1.8"})))
# the HEC-HMS model: the engineer's screenshot, georeferenced (step 25)
shot = ras(os.path.join(DATA, "hms_model_georef.tif"), "HEC-HMS model view"); E_SHOT = shot.extent()
# Q200 at the junctions (Block 6 Figure 12 a/b)
q2 = vec(os.path.join(W7, "elements", "shp", "B6", "Points_B6.shp"), "Junction: 200-year peak flow (m³/s)", subset="\"type\" IN ('Junction', 'Outfall', 'Dam junction')")
q2.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "circle", "color": "#1F4FD8", "outline_color": "#FFFFFF", "outline_width": "0.25", "size": "1.9"})))
label_layer(q2, 'format_number("Q200", 0)', 6.8, "#1F1F1F", True, 0.9, expression=True, italic=True, around_point=True, overlap=True)
q2z = vec(os.path.join(W7, "elements", "shp", "B6", "Points_B6.shp"), "Junction: 200-year peak flow (m³/s)", subset="\"type\" IN ('Junction', 'Outfall', 'Dam junction')")
q2z.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "circle", "color": "#1F4FD8", "outline_color": "#FFFFFF", "outline_width": "0.25", "size": "2.1"})))
label_layer(q2z, 'format_number("Q200", 0)', 7.2, "#1F1F1F", True, 0.9, expression=True, italic=True, around_point=True, overlap=True)
sub_o = vec(os.path.join(W7, "elements", "shp", "B6", "Subbasins_B6.shp"), "HEC-HMS subbasin"); fill(sub_o, "0,0,0,0", "#E97132", 0.3)
mdl_pts = vec(os.path.join(W7, "elements", "shp", "B6", "Points_B6.shp"), "HEC-HMS junction / outfall", subset="\"type\" IN ('Junction', 'Outfall', 'Dam junction')")
mdl_pts.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "circle", "color": "#1F4FD8", "outline_color": "#FFFFFF", "outline_width": "0.25", "size": "1.6"}))); mdl_pts.setLabelsEnabled(False)
res_pts = vec(os.path.join(W7, "elements", "shp", "B6", "Points_B6.shp"), "HEC-HMS reservoir", subset="\"type\" = 'Reservoir'")
res_pts.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "triangle", "color": "#C00000", "outline_color": "#FFFFFF", "outline_width": "0.3", "size": "3.0"}))); res_pts.setLabelsEnabled(False)
# ---- R4 (W7): the designed channels of the 200-yr run (R9), the crossings and culverts, the dykes, the plain catchments, the CN grid
GP = os.path.join(W7, "gis", "sewergems_200yr_R9.gpkg")
if DIM_FP:   # the bed of the stormwater channels only: a buffer of each designed reach by half its bed width (the stored bed is one dissolved polygon)
    from qgis.core import QgsGeometryGeneratorSymbolLayer
    bed_w = vec(GP, "Designed channel bed (200-year)", "segments", subset=NOFP_SEG)
    _gg = QgsGeometryGeneratorSymbolLayer.create({"geometryModifier": 'buffer($geometry, "span_m" / 2)', "SymbolType": "Fill"})
    _gg.setSubSymbol(QgsFillSymbol.createSimple({"color": "#E97132", "outline_color": "#A0522D", "outline_width": "0.2", "outline_width_unit": "MM"}))
    _bs = QgsLineSymbol(); _bs.changeSymbolLayer(0, _gg); bed_w.setRenderer(QgsSingleSymbolRenderer(_bs))
else:
    bed_w = vec(GP, "Designed channel bed (200-year)", "bed"); bed_w.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({"color": "#E97132", "outline_color": "#A0522D", "outline_width": "0.2", "outline_width_unit": "MM"})))
seg_w = vec(GP, "Bed width (m)", "segments", subset=NOFP_SEG if DIM_FP else None); seg_w.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple({"color": "#1F3B63", "width": "0.3", "width_unit": "MM"})))
label_layer(seg_w, 'format_number("span_m", 0)', 6.8, "#1F1F1F", True, 0.9, expression=True, italic=True, overlap=True)
try: pal = seg_w.labeling().settings(); pal.placement = Qgis.LabelPlacement.Line; seg_w.setLabeling(QgsVectorLayerSimpleLabeling(pal))
except Exception as _e: print("seg_w labels:", _e)
seg_d = vec(GP, "Channel depth", "segments", subset=NOFP_SEG if DIM_FP else None)
seg_d.setRenderer(QgsCategorizedSymbolRenderer("rise_m", [QgsRendererCategory(2.5, QgsLineSymbol.createSimple({"color": "#1F4FD8", "width": "0.9", "width_unit": "MM"}), "2.5 m"), QgsRendererCategory(3.0, QgsLineSymbol.createSimple({"color": "#C00000", "width": "1.2", "width_unit": "MM"}), "3.0 m, the wadi is deeper")]))
seg_q = vec(GP, "200-year design flow of the reach (m³/s)", "segments", subset=NOFP_SEG if DIM_FP else None)
seg_q.setRenderer(QgsGraduatedSymbolRenderer("flow", [QgsRendererRange(lo, hi, QgsLineSymbol.createSimple({"color": c, "width": w, "width_unit": "MM"}), lab_) for lo, hi, lab_, c, w in (
    (0, 50, "0 to 50", "#9DC3E6", "0.5"), (50, 150, "50 to 150", "#5B9BD5", "0.7"), (150, 400, "150 to 400", "#2F5597", "0.9"), (400, 1000, "400 to 1 000", "#C55A11", "1.2"), (1000, 3000, "1 000 to 1 500", "#C00000", "1.5"))]))
label_layer(seg_q, 'CASE WHEN "flow" > 0.5 THEN format_number("flow", 0) ELSE \'\' END', 6.4, "#1F1F1F", True, 0.9, expression=True, italic=True, overlap=True)
try: pal = seg_q.labeling().settings(); pal.placement = Qgis.LabelPlacement.Line; seg_q.setLabeling(QgsVectorLayerSimpleLabeling(pal))
except Exception as _e: print("seg_q labels:", _e)
seg_lab = vec(GP, "Reach number", "segments", subset=NOFP_SEG if DIM_FP else None); seg_lab.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple({"color": "0,0,0,0", "width": "0.1", "width_unit": "MM"})))   # invisible line, labels only
label_layer(seg_lab, 'regexp_replace("SGLabel", \'^.*-C\', \'C\')', 5.2, "#1F1F1F", True, 0.8, expression=True, overlap=True)
try:
    pal = seg_lab.labeling().settings(); pal.placement = Qgis.LabelPlacement.Line; pal.displayAll = True; pal.priority = 10
    try: pal.placementSettings().setOverlapHandling(Qgis.LabelOverlapHandling.AllowOverlapIfRequired); pal.placementSettings().setAllowDegradedPlacement(True)
    except Exception as _e2: print("seg_lab overlap:", _e2)
    seg_lab.setLabeling(QgsVectorLayerSimpleLabeling(pal))
except Exception as _e: print("seg_lab labels:", _e)
# R5 (his comment on the reach map: names and reach numbers overlapping): one A3 panel per catchment; the names along the lines placed first
# (priority 10, either side of the line), the reach numbers as labels around the reach midpoint with a leader, placed only where they fit
import re as _re
from qgis.core import QgsFeature as _QgsFeature, QgsSimpleLineCallout as _QgsSimpleLineCallout
reach_pts = QgsVectorLayer("Point?crs=EPSG:32640&field=lab:string(20)&field=ch:string(40)", "Reach number (at the reach midpoint)", "memory"); _pr = reach_pts.dataProvider(); _fts = []
for _f in seg_lab.getFeatures():
    _g = _f.geometry()
    if _g is None or _g.isEmpty(): continue
    _ft = _QgsFeature(reach_pts.fields()); _ft.setGeometry(_g.interpolate(_g.length() / 2.0)); _lab = str(_f["SGLabel"]); _ft.setAttributes([_lab, _lab.rsplit("-C", 1)[0]]); _fts.append(_ft)   # W9: the full SGLabel (his instruction)
_pr.addFeatures(_fts); reach_pts.updateExtents(); print("reach midpoints:", reach_pts.featureCount())
reach_pts.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "circle", "color": "#1F1F1F", "outline_style": "no", "size": "0.9", "size_unit": "MM"})))
label_layer(reach_pts, '"lab"', 5.2, "#1F1F1F", True, 0.7, expression=True, around_point=True, offset_mm=1.0)
try:
    _pal = reach_pts.labeling().settings(); _pal.priority = 3; _pal.displayAll = False
    _pal.placementSettings().setOverlapHandling(Qgis.LabelOverlapHandling.PreventOverlap); _pal.placementSettings().setAllowDegradedPlacement(False)
    _co = _QgsSimpleLineCallout(); _co.setEnabled(True); _co.setLineSymbol(QgsLineSymbol.createSimple({"color": "#1F1F1F", "width": "0.18", "width_unit": "MM"})); _co.setMinimumLength(0.6); _co.setMinimumLengthUnit(QgsUnitTypes.RenderMillimeters)
    _pal.setCallout(_co); reach_pts.setLabeling(QgsVectorLayerSimpleLabeling(_pal))
except Exception as _e: print("reach_pts labels:", _e)
ch_names_p = vec(SRC["channels"], "Channels and dykes", qml="channels_dykes", subset='"Block" = 4')
_rp = ch_names_p.renderer()
if _rp is not None and _rp.type() == "categorizedSymbol":
    for _i, _c in enumerate(_rp.categories()): _rp.updateCategoryLabel(_i, CHNAMES.get(str(_c.value()), str(_c.label())))
    for _i in sorted([_i for _i, _c in enumerate(_rp.categories()) if _c.value() in (None, "") or str(_c.value()).strip() in ("", "NULL")], reverse=True): _rp.deleteCategory(_i)
    if DIM_FP: _dim_fp(_rp)
line_labels(ch_names_p, "Name", size=7.4, buffer=0.9)
try:
    _pal = ch_names_p.labeling().settings(); _pal.priority = 10
    _ls = _pal.lineSettings(); _ls.setPlacementFlags(Qgis.LabelLinePlacementFlag.AboveLine | Qgis.LabelLinePlacementFlag.BelowLine | Qgis.LabelLinePlacementFlag.MapOrientation); _ls.setMergeLines(False)
    ch_names_p.setLabeling(QgsVectorLayerSimpleLabeling(_pal))
except Exception as _e: print("ch_names_p labels:", _e)
def cat_extent(code, s=1.12):
    r = QgsRectangle()
    for f in ch.getFeatures():
        if str(f["Name"]).upper().startswith(code):
            b = f.geometry().boundingBox()
            if r.isNull(): r = QgsRectangle(b)
            else: r.combineExtentWith(b)
    r.scale(s); return r
def cat_counts(code):
    names = [str(f["Name"]) for f in ch.getFeatures() if str(f["Name"]).upper().startswith(code)]
    return len([n for n in names if "-CH" in n.upper()]), len([n for n in names if "-D" in n.upper()]), len([f for f in reach_pts.getFeatures() if str(f["ch"]).upper().startswith(code)])
OL = os.path.join(W7, "gis", "outfalls_levels.gpkg"); OEXPR = '"label" || \'\\n\' || \'I: \' || format_number("invert", 2) || \'\\n\' || \'Fix: \' || format_number("fix", 2) || \'\\n\' || \'Δ: \' || format_number("diff", 2)'
if DIM_FP:
    import pandas as _pd
    _ot = _pd.read_csv(os.path.join(W8, "report", "data", "outfalls.csv")); _sw = [o for o, c in zip(_ot.outfall, _ot.channel) if not str(c).upper().endswith("-FP")]
    _OSUB = " AND \"label\" IN (" + ", ".join("'%s'" % o for o in _sw) + ")"
else: _OSUB = ""
outf_pts = vec(OL, "Outfall: designed invert I, existing level Fix, difference Δ (m)", "outfalls", subset='"diff" <= 0.05' + _OSUB); outf_pts.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "circle", "color": "#00E5A0", "outline_color": "#1F1F1F", "outline_width": "0.25", "size": "2.6"})))
label_layer(outf_pts, OEXPR, 6.6, "#1F1F1F", True, 0.9, expression=True, around_point=True, overlap=True)
outf_red = vec(OL, "Outfall with the invert below the existing level", "outfalls", subset='"diff" > 0.05' + _OSUB); outf_red.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "circle", "color": "#00E5A0", "outline_color": "#C00000", "outline_width": "0.5", "size": "2.6"})))
label_layer(outf_red, OEXPR, 6.6, "#C00000", True, 0.9, expression=True, around_point=True, overlap=True)
for _l in (outf_pts, outf_red):
    try: _pal = _l.labeling().settings(); _pal.displayAll = True; _pal.multilineAlign = Qgis.LabelMultiLineAlignment.Left; _pal.dist = 1.6; _l.setLabeling(QgsVectorLayerSimpleLabeling(_pal))
    except Exception as _e: print("outfall labels:", _e)
DY = os.path.join(W7, "dykes", "dykes.gpkg")
dyke_l = vec(DY, "Dyke", "dykes", subset="NOT (\"name\" LIKE '%-FP')" if DIM_FP else None); line(dyke_l, "#00B050", 1.1)
dyke_h = vec(DY, "Dyke height (m)", "dykes", subset="NOT (\"name\" LIKE '%-FP')" if DIM_FP else None)
dyke_h.setRenderer(QgsGraduatedSymbolRenderer("H_m", [QgsRendererRange(lo, hi, QgsLineSymbol.createSimple({"color": c, "width": "1.3", "width_unit": "MM"}), lab_) for lo, hi, lab_, c in (
    (0, 2.0, "1.0 to 2.0", "#A9D18E"), (2.0, 2.5, "2.0 to 2.5", "#70AD47"), (2.5, 3.5, "2.5 to 3.5", "#C55A11"), (3.5, 10, "3.5 to 4.5", "#C00000"))]))
label_layer(dyke_h, 'format_number("H_m", 1)', 7.0, "#1F1F1F", True, 0.9, expression=True, overlap=True)
try: pal = dyke_h.labeling().settings(); pal.placement = Qgis.LabelPlacement.Line; dyke_h.setLabeling(QgsVectorLayerSimpleLabeling(pal))
except Exception as _e: print("dyke labels:", _e)
CV = os.path.join(W8, "culverts", "crossings.gpkg")
culv_pts = vec(CV, "Proposed box culvert (cells x width x height, m)", "crossings", subset="NOT (\"channel\" LIKE '%-FP')" if DIM_FP else None); culv_pts.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "square", "color": "#FFC000", "outline_color": "#1F1F1F", "outline_width": "0.3", "size": "3.0"})))
label_layer(culv_pts, '"size"', 6.4, "#1F1F1F", True, 0.9, expression=True, around_point=True, overlap=False)
try:
    from qgis.core import QgsSimpleLineCallout
    _pal = culv_pts.labeling().settings(); _pal.placement = Qgis.LabelPlacement.OrderedPositionsAroundPoint; _pal.dist = 3.0; _pal.displayAll = True; _pal.priority = 10
    _pal.placementSettings().setOverlapHandling(Qgis.LabelOverlapHandling.PreventOverlap); _pal.placementSettings().setAllowDegradedPlacement(True)
    _co = QgsSimpleLineCallout(); _co.setEnabled(True); _co.setMinimumLength(1.0)
    try: _co.lineSymbol().setWidth(0.25); _co.lineSymbol().setColor(QColor("#1F1F1F"))
    except Exception as _e3: print("callout symbol:", _e3)
    _pal.setCallout(_co); culv_pts.setLabeling(QgsVectorLayerSimpleLabeling(_pal))
except Exception as _e: print("culvert callouts:", _e)
sub_dam = vec(os.path.join(W7, "elements", "shp", "B6", "Subbasins_B6_dam.shp"), "Catchment")
sub_dam.setRenderer(QgsCategorizedSymbolRenderer("inter", [QgsRendererCategory(0, QgsFillSymbol.createSimple({"color": "255,255,255,0", "outline_color": "#7F7F7F", "outline_width": "0.25", "outline_width_unit": "MM"}), "catchment of a dam, or receiving a dam outflow"),
                                                            QgsRendererCategory(1, QgsFillSymbol.createSimple({"color": "0,229,200,150", "outline_color": "#007A66", "outline_width": "0.3", "outline_width_unit": "MM"}), "intermediate catchment: no dam in its upstream network")]))
cn_ras = ramp_raster(os.path.join(B4, "Hydrology", "HEC_HMS_Block_04", "Hydrology Data", "CN_Include_Hill_Area.tif"), "SCS curve number", 55, 100, ["#1A9850", "#A6D96A", "#FFFFBF", "#FDAE61", "#D73027"], 0)
GCA = os.path.join(W8, "gis", "GCA_RENN.gpkg")
gca_all = vec(GCA, "Global catchments of the study area", "gca", subset='"block4" = 0'); gca_all.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({"color": "230,230,230,90", "outline_color": "#7F7F7F", "outline_width": "0.3", "outline_width_unit": "MM"})))
label_layer(gca_all, 'replace("G_NAME", \'_\', \' \')', 6.5, "#5A5A5A", False, 0.8, expression=True, italic=True, overlap=True)
gca_b4 = vec(GCA, "Global catchments of Block 04", "gca", subset='"block4" = 1')
gca_b4.setRenderer(QgsCategorizedSymbolRenderer("G_NAME", [QgsRendererCategory(nm, QgsFillSymbol.createSimple({"color": col, "outline_color": "#1F1F1F", "outline_width": "0.5", "outline_width_unit": "MM"}), nm) for nm, col in (("Al Hawasinah", "255,192,0,110"), ("Shafan", "0,176,240,110"), ("Sarami", "146,208,80,110"), ("Sakhin", "255,102,0,110"), ("Mehmum", "255,153,102,110"))]))
label_layer(gca_b4, '"G_NAME" || \'\\n\' || format_number("area_km2", 0) || \' km²\'', 9.0, "#1F1F1F", True, 1.0, expression=True, overlap=True)
E_GCA = gca_b4.extent(); E_GCA.scale(1.25)
roads_bg = []
for key, name, col, wd in (("highway", "Batinah Highway", "#1F1F1F", 0.9), ("coastal_road", "Batinah Coastal Road", "#5A5A5A", 0.7), ("bypass", "North Batinah Bypass (planned)", "#7F6000", 0.8)):
    l = vec(SRC[key], name); line(l, col, wd, "dash" if key == "bypass" else None); roads_bg.append(l)

rch_o = vec(os.path.join(W7, "elements", "shp", "B6", "Reaches_B6.shp"), "HEC-HMS reach"); line(rch_o, "#00B0F0", 0.55)
# RUSLE rasters and the sediment layers
BLUES = ["#F7FBFF", "#C6DBEF", "#6BAED6", "#2171B5", "#08306B"]; BROWNS = ["#FFF7EC", "#FDD49E", "#FC8D59", "#D7301F", "#7F0000"]; PURPLES = ["#FCFBFD", "#DADAEB", "#9E9AC8", "#6A51A3", "#3F007D"]; GREENS = ["#F7FCF5", "#C7E9C0", "#74C476", "#238B45", "#00441B"]; ORANGES = ["#FFF5EB", "#FDD0A2", "#FD8D3C", "#D94801", "#7F2704"]
RF = {k: ramp_raster(os.path.join(DATA, f"{k}_catchments.tif"), nm, RS[k]["p2"], RS[k]["p98"], cols, dec) for k, nm, cols, dec in (("R", "R factor, MJ mm/(ha h yr)", BLUES, 0), ("K", "K factor, t ha h/(ha MJ mm)", BROWNS, 3), ("LS", "LS factor", PURPLES, 0), ("C", "C factor", GREENS, 3), ("SoilLoss", "Soil loss, t/ha/yr", ORANGES, 0))}
def excl_layer(name, field, ranges, label_expr, size=6.8):
    l = vec(os.path.join(DATA, "dam_catchments_results.gpkg"), name, "catchments_excl")
    l.setRenderer(QgsGraduatedSymbolRenderer(field, [QgsRendererRange(lo, hi, QgsFillSymbol.createSimple({"color": c, "outline_color": "#FFFFFF", "outline_width": "0.3", "outline_width_unit": "MM"}), lab_) for lo, hi, lab_, c in ranges]))
    label_layer(l, label_expr, size, "#1F1F1F", True, 0.9, expression=True, overlap=True)
    try: _ob = QgsFeatureRequest.OrderBy([QgsFeatureRequest.OrderByClause("area_km2", False)]); l.renderer().setOrderBy(_ob); l.renderer().setOrderByEnabled(True)
    except Exception as e: print("order by:", e)
    return l
cy = excl_layer("Sediment yield, m³/km²/yr", "yield_m3km2", [(0, 100, "90 (floor) to 100", "#FEE8C8"), (100, 140, "100 to 140", "#FDBB84"), (140, 170, "140 to 170", "#E34A33"), (170, 300, "over 170", "#7F0000")],
                '"label_s" || \'\\n\' || format_number("yield_m3km2", 0) || \' m³/km²/yr\' || \'\\n\' || format_number("loss50_pct", 1) || \' % in 50 yr\'')
cv = excl_layer("Sediment delivered in 50 years, Mcm", "sed50_Mcm", [(0, 0.5, "up to 0.5", "#FEF0D9"), (0.5, 1.0, "0.5 to 1", "#FDCC8A"), (1.0, 2.5, "1 to 2.5", "#FC8D59"), (2.5, 4.0, "2.5 to 4", "#E34A33"), (4.0, 20, "over 4", "#B30000")],
                '"label_s" || \'\\n\' || format_number("sed50_Mcm", 2) || \' Mcm in 50 yr\' || \'\\n\' || format_number("loss50_pct", 1) || \' % of FSL storage\'', 7.2)
# the counts of the data boxes, from the layers (the stormwater report leaves the flood protection channels out)
def _names(): return [str(f["Name"]) for f in ch.getFeatures() if not (DIM_FP and str(f["Name"]).upper().endswith("-FP"))]
N_CH = len([n for n in _names() if "-CH" in n.upper()]); N_DY = len([n for n in _names() if "-D" in n.upper()])
_spans = [float(f["span_m"]) for f in seg_w.getFeatures() if f["span_m"] is not None]; W_MIN, W_MAX = (min(_spans), max(_spans)) if _spans else (0.0, 0.0)
N_REACH = seg_w.featureCount()
_dk = [(float(f["H_m"]), float(f["L_m"])) for f in dyke_h.getFeatures()]; DK_KM = sum(l for h, l in _dk) / 1000; H_MIN, H_MAX = (min(h for h, l in _dk), max(h for h, l in _dk)) if _dk else (0.0, 0.0)
N_HWY = len([f for f in culv_pts.getFeatures() if f["road"] == "Batinah Highway"]); N_CST = len([f for f in culv_pts.getFeatures() if f["road"] == "Batinah Coastal Road"]); N_BYP = len([f for f in culv_pts.getFeatures() if f["road"] == "North Batinah Bypass"])
# ------------------------------------------------------------------ extents and figures
def rect(b, s): r = QgsRectangle(b[0], b[1], b[2], b[3]); r.scale(s); return r
E_ALL = rect(ext["all"], 1.04); E_CAT = rect(ext["catchments"], 1.05); E_PLAIN = rect(ext["channels_dams"], 1.06); E_DOWN = rect(ext["downstream"], 1.04)
def per_dam(field, fmt): vals = {f["name"]: float(f[field]) for f in cat_nolab.getFeatures()}; return [(lab(d), fmt(vals[d])) for d in DAMS9 if d in vals]
def klen(cond=lambda f: True): return sum(f.geometry().length() for f in ch.getFeatures() if cond(f)) / 1000
F = lambda title, stack, extent, sat_=True, hs_=hs, table=(), box=(), box_title=None, legend=None, credit=None, a3=False: dict(title=title, stack=stack, extent=extent, sat=sat_, hs=hs_, table=list(table), box=list(box), box_title=box_title, legend=legend, credit=credit, a3=a3)
FIGS = {
 "M01_dams": F("Dams and their catchments", [axes_l, dikes, fslp, crp, cat_nolab, ch, dam_pts], E_ALL, True, hs, [("Dams", "9"), ("Catchment area controlled", f"{ext['controlled_km2']:,.0f} km²"), ("Channels and dykes", f"{klen():,.0f} km")], per_dam("area_km2", lambda v: f"{v:,.0f} km²"), "Catchment area"),
 "M03_alignments_flood": F("Channel alignments to control the 200-year flood", [ch, axes_l, dam_pts, depth], E_PLAIN, True, hs_dim, [("Flood depth", "200-year, no scheme"), ("Channels and dykes", f"{klen():,.0f} km"), ("Dams", "9")]),
 "M04_routes": F("Channel and dyke routes", [ch_names, axes_l, dikes, fslp, dam_pts], E_PLAIN, True, hs, ([] if DIM_FP else [("Flood protection channels", f"{klen(lambda f: f['CHtt'] == 'FP CH'):,.0f} km")]) + [("Stormwater main channels", f"{klen(lambda f: f['CHtt'] == 'Sw M CH'):,.0f} km"), ("Stormwater secondary channels", f"{klen(lambda f: f['CHtt'] == 'Sw S CH'):,.0f} km"), ("Dykes", f"{klen(lambda f: str(f['CHtt']).endswith(' D') and not (DIM_FP and f['CHtt'] == 'FP D')):,.0f} km"), ("Dams", "9")]),
 "M05_roads_utilities": F("Roads and utilities", roads + pipes + [culv, ch1, axes_l], E_PLAIN, True, hs, [("Batinah Expressway", "existing"), ("Batinah Highway", "existing"), ("Batinah Coastal Road", "existing"), ("North Batinah Bypass", "planned"), ("OQ pipelines", "shallow, to be verified")]),
 "M06_landuse": F("Land use", [lu, ch1, axes_l], E_PLAIN, True, hs_dim, [("Source", "MoHUP cadastre"), ("Channels and dykes", f"{klen():,.0f} km"), ("Dams", "9")]),
 "M08_hms": F("HEC-HMS model for Block 04", [sub_o, rch_o, mdl_pts, res_pts, axes_l, dam_pts_small], E_ALL, False, hs, [("Subbasins", str(sub_o.featureCount())), ("Reaches", str(rch_o.featureCount())), ("Junctions and outfalls", str(q2.featureCount())), ("Reservoirs", str(res_pts.featureCount())), ("Dams", "9")], credit="HEC-HMS model elements on the hillshade of the 10 m terrain model"),
 "M10_q200": F("200-year peak flow (m³/s) at the junctions of the HEC-HMS model", [sub_o, rch_o, q2, cat_k, axes_l, dam_pts_small], E_ALL, True, hs, [("Junctions and outfalls", str(q2.featureCount())), ("Design event", "200-year, dams in place"), ("Dams", "9")]),
 "M11_q200_plain": F("200-year peak flow (m³/s) at the junctions: the dams and the plain", [sub_o, rch_o, q2z, cat_k, axes_l, dam_pts], E_DOWN, True, hs, [("Junctions and outfalls", str(q2.featureCount())), ("Design event", "200-year, dams in place"), ("Dams", "9")], a3=True),
 "M21_gca": F("Global catchments of Block 04", [gca_all, gca_b4, ch1, axes_l, dam_pts_small], E_GCA, False, hs, [("Global catchments", "Al Hawasinah, Shafan, Sarami, Sakhin"), ("Area", "%s km²" % "{:,.0f}".format(sum(float(f["area_km2"]) for f in gca_b4.getFeatures())))]),
 "M12_width": F("Designed bed width of the channels for the 200-year flow (m)", [bed_w, seg_w, dyke_l, axes_l, dam_pts_small], E_PLAIN, True, hs, [("Channels", f"{N_CH}, bed width to scale"), ("Bed width", f"{W_MIN:.0f} to {W_MAX:.0f} m"), ("Dykes", str(N_DY))]),
 "M13_depth": F("Channel depth: 2.5 m, or 3 m where the wadi is deeper", [seg_d, dyke_l, axes_l, dam_pts_small], E_PLAIN, True, hs, [("Channels 2.5 m deep", "the plain"), ("Channels 3 m deep", "the deeper wadis"), ("Dykes", str(N_DY))]),
 "M14_reach_labels": F("Channels by class with their names and the reach numbers of the hydraulic model", [ch_names, seg_lab, axes_l, dam_pts_small], E_PLAIN, True, hs, [("Channels", "37, named"), ("Reaches", "212, numbered C1 … from upstream"), ("Dykes", "36")], a3=True),
 "M15_outfalls": F("Outfalls of the channel system: designed invert I, existing level Fix, difference", [ch1, outf_pts, outf_red, axes_l, dam_pts_small], E_PLAIN, True, hs, [("Outfalls", str(len(list(outf_pts.getFeatures())) + len(list(outf_red.getFeatures())))), ("Invert below the existing level", str(len(list(outf_red.getFeatures()))) + ", in red"), ("Design event", "200-year, dams in place")]),
 "M16_plain_catchments": F("Intermediate catchments with no dam in their upstream network", [sub_dam, rch_o, ch1, axes_l, dam_pts_small], E_ALL, False, hs, [("Intermediate catchments", "44, 258 km²"), ("With a dam upstream", "66, 2 205 km²")]),
 "M17_cn": F("SCS curve number grid", [cn_ras, cat_k, axes_l, dam_pts_small], E_ALL, False, None, [("Source", "ESA WorldCover 2020, ISRIC SoilGrids"), ("Resolution", "10 m")]),
 "M18_q200_channels": F("200-year design flow along the channels (m³/s)", [seg_q, dyke_l, axes_l, dam_pts_small], E_PLAIN, True, hs, [("Reaches", str(N_REACH)), ("Design event", "200-year, dams in place")], a3=True),
 "M19_culverts": F("Road crossings and the proposed box culverts", roads_bg + [ch1, culv_pts, axes_l, dam_pts_small], E_PLAIN, True, hs, [("Crossings", str(culv_pts.featureCount())), ("Batinah Highway", str(N_HWY)), ("Batinah Coastal Road", str(N_CST)), ("North Batinah Bypass (planned)", str(N_BYP)), ("Cells", "4.0 m wide, 2.5 or 3.0 m high")]),
 "M20_dykes": F("Dyke heights (m)", [ch1, dyke_h, axes_l, dam_pts_small], E_PLAIN, True, hs, [("Dykes", f"{N_DY}, {DK_KM:.1f} km"), ("Height", f"{H_MIN:.1f} to {H_MAX:.1f} m"), ("Basis", "200-year depth + 0.5 m + 0.6 m freeboard")]),
 "M09_sediment50": F("Sediment delivered to each dam in 50 years and the storage lost", [cv, axes_l], E_CAT, True, hs, [("Sediment in 50 yr", "RUSLE × Williams SDR"), ("Floors", "SDR 0.2; 90 m³/km²/yr"), ("Range", f"{min(float(f['sed50_Mcm']) for f in cat_nolab.getFeatures()):.2f} – {max(float(f['sed50_Mcm']) for f in cat_nolab.getFeatures()):.2f} Mcm")], per_dam("sed50_Mcm", lambda v: f"{v:.2f} Mcm"), "Sediment in 50 years"),
}
def load_template(a3=False):
    lay = QgsPrintLayout(proj); doc = QDomDocument(); doc.setContent(open(TEMPLATE_XML, encoding="utf-8").read()); lay.loadFromTemplate(doc, QgsReadWriteContext(), True)
    if a3:   # the A4 landscape template scaled to A3 landscape; the scale bar is re-seated so the frame line runs through the bar
        k = 420.0 / 297.0; pg = lay.pageCollection().page(0); pg.setPageSize("A3", QgsLayoutItemPage.Landscape)
        for it in lay.items():
            if isinstance(it, (QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemScaleBar, QgsLayoutItemLegend, QgsLayoutFrame)):
                pos, sz = it.positionWithUnits(), it.sizeWithUnits(); it.attemptMove(QgsLayoutPoint(pos.x() * k, pos.y() * k, MM)); it.attemptResize(QgsLayoutSize(sz.width() * k, sz.height() * k, MM))
        m = [i for i in lay.items() if isinstance(i, QgsLayoutItemMap)][0]
        for it in lay.items():
            if isinstance(it, QgsLayoutItemScaleBar): it.attemptMove(QgsLayoutPoint(it.positionWithUnits().x(), m.positionWithUnits().y() - 7.3, MM))
    return lay
def segment_m(m):
    """scale bar segment so that four segments span 50 to 80 mm at the map's scale"""
    mm_per_km = 1e6 / max(m.scale(), 1.0); fit = [km for km in (1, 2, 2.5, 5, 10, 20) if 4 * km * mm_per_km <= 80]
    return (max(fit) if fit else 1) * 1000
def furnish(lay, spec, m):
    mp, ms = m.positionWithUnits(), m.sizeWithUnits(); right, bottom = mp.x() + ms.width(), mp.y() + ms.height(); table_h = [20.0]
    items = sorted(lay.items(), key=lambda i: 0 if (isinstance(i, QgsLayoutFrame) and isinstance(i.multiFrame(), QgsLayoutItemManualTable)) else 1)   # the table first: the box sits on it
    for it in items:
        if isinstance(it, QgsLayoutItemLabel):
            t = it.text()
            if t.startswith("Ibri Sewer"): it.setText(SUBTITLE); it.attemptResize(QgsLayoutSize(260, 4.5, MM))
            elif t.startswith("Satellite image") or t.startswith("Background"): it.setText(spec["credit"] or CREDIT[spec["sat"]]); it.attemptResize(QgsLayoutSize(140, 3.5, MM))
            elif t and not t.startswith("N"): kk = 420.0 / 297.0 if spec.get("a3") else 1.0; it.setText(spec["title"]); it.attemptResize(QgsLayoutSize(185 * kk, 6.5 * kk, MM)); tf = it.textFormat(); tf.setSize(16 if spec.get("a3") else 13); it.setTextFormat(tf)
        elif isinstance(it, QgsLayoutItemScaleBar):
            # the template's own place and spacing (the frame line runs through the bar); only the units and the segment length are set
            it.setLinkedMap(m); it.setUnits(Qgis.DistanceUnit.Meters); it.setSegmentSizeMode(Qgis.ScaleBarSegmentSizeMode.Fixed); it.setStyle("Single Box"); it.setNumberOfSegments(4); it.setNumberOfSegmentsLeft(0)
            seg = segment_m(m); it.setUnitsPerSegment(seg); it.setMapUnitsPerScaleBarUnit(1000); it.setUnitLabel("km"); it.setHeight(2.5); it.setLabelBarSpace(3.0)
            tfs = it.textFormat(); tfs.setSize(8); tfs.setFont(QFont("Arial")); it.setTextFormat(tfs)
            it.attemptMove(QgsLayoutPoint(it.positionWithUnits().x(), mp.y() - (7.8 if spec.get("a3") else 7.75), MM))   # bar centre on the frame line (measured on the export: label 3.5 mm + gap 3 mm + half the 2.5 mm bar), as in the engineer's layouts
        elif isinstance(it, QgsLayoutItemLegend):
            legend_layers = spec["legend"] if spec["legend"] is not None else [l for l in spec["stack"] if not l.name().startswith("_") and not l.name().endswith("(south)")]
            if not legend_layers: lay.removeLayoutItem(it); continue
            it.setLinkedMap(m); it.setAutoUpdateModel(False); grp = it.model().rootGroup()
            for c in list(grp.children()): grp.removeChildNode(c)
            for l in legend_layers:
                node = grp.addLayer(l); r = getattr(l, "renderer", lambda: None)()
                if r is not None and r.type() in ("categorizedSymbol", "graduatedSymbol"): node.setCustomProperty("legend/title-style", "visible")
                if isinstance(l, QgsRasterLayer):
                    it.model().refreshLayerLegend(node); kids = it.model().layerLegendNodes(node); keep = [i for i, k in enumerate(kids) if type(k).__name__ != "QgsSimpleLegendNode"]
                    if keep and len(keep) < len(kids): QgsMapLayerLegendUtils.setLegendNodeOrder(node, keep); it.model().refreshLayerLegend(node)
            it.setTitle(""); it.setBackgroundEnabled(True); it.setBackgroundColor(QColor(255, 255, 255, 235)); it.setResizeToContents(True)
            for sty in (QgsLegendStyle.Subgroup, QgsLegendStyle.SymbolLabel):
                f = QFont("Arial"); f.setPointSizeF(6.5 if sty == QgsLegendStyle.SymbolLabel else 7.0); f.setBold(sty == QgsLegendStyle.Subgroup); it.rstyle(sty).setFont(f)
            nrows = sum(1 + len(it.model().layerLegendNodes(grp.findLayer(l.id()))) for l in legend_layers if grp.findLayer(l.id()) is not None)
            it.setWrapString(""); it.setColumnCount(2 if nrows > 14 else 1); it.setSplitLayer(True); it.setEqualColumnWidth(False); it.setFrameEnabled(True); it.setFrameStrokeWidth(QgsLayoutMeasurement(0.2, MM))
            it.setReferencePoint(QgsLayoutItem.LowerLeft); it.attemptMove(QgsLayoutPoint(mp.x() + 2.5, bottom - 2.5, MM), True); it.adjustBoxSize()
        elif isinstance(it, QgsLayoutFrame):
            mf = it.multiFrame()
            if isinstance(mf, QgsLayoutItemManualTable):
                mf.setTableContents([[QgsTableCell(a), QgsTableCell(b)] for a, b in spec["table"]]); mf.setGridStrokeWidth(0.15); mf.setGridColor(QColor("#9DA9B8"))
                tfc = mf.contentTextFormat(); tfc.setSize(7.5); tfc.setFont(QFont("Arial")); tfc.setColor(QColor("#1F3B63")); mf.setContentTextFormat(tfc); mf.setWrapBehavior(QgsLayoutTable.WrapText)
                cols = mf.columns()
                if len(cols) >= 2: cols[0].setWidth(36.0); cols[1].setWidth(32.0); mf.setColumns(cols)
                mf.refreshAttributes(); h = max(4.3 * len(spec["table"]) + 1.5, mf.totalHeight() + 1.0); table_h[0] = h
                it.attemptResize(QgsLayoutSize(70.0, h, MM)); it.attemptMove(QgsLayoutPoint(right - 3.0 - 70.0, bottom - 3.0 - h, MM))
            elif isinstance(mf, QgsLayoutItemHtml):
                if spec["box"]:
                    rows = "".join(f"<tr><td style='padding:1px 4px'>{a}</td><td align='right' style='padding:1px 4px'>{b}</td></tr>" for a, b in spec["box"])
                    mf.setContentMode(QgsLayoutItemHtml.ManualHtml); mf.setHtml(f"<html><body style='margin:0;font-family:Arial;font-size:7pt;color:#1F3B63'><div style='background:#FFFFFF;border:0.3px solid #1F3B63;padding:3px'><b>{spec['box_title']}</b><table style='font-size:7pt;border-collapse:collapse;margin-top:2px'>{rows}</table></div></body></html>"); mf.loadHtml()
                    hbox = 7 + 3.9 * len(spec["box"]); it.attemptResize(QgsLayoutSize(70.0, hbox, MM)); it.attemptMove(QgsLayoutPoint(right - 3.0 - 70.0, bottom - 3.0 - table_h[0] - 2.0 - hbox, MM))
                else: lay.removeLayoutItem(it)
for _code, _nm in (("HAW", "Al Hawasinah"), ("SHA", "Shafan"), ("SAR", "Sarami"), ("SAK", "Sakhin")):
    _nc, _nd, _nr = cat_counts(_code)
    FIGS[f"M14_reach_{_code}"] = F(f"Channels and reach numbers: {_nm} catchment ({_nc} channels, {_nr} reaches)", [ch_names_p, reach_pts, axes_l, dam_pts_small], cat_extent(_code), True, hs, [], a3=True)
def build(keys=None, dpi=200):
    made = []; mgr = proj.layoutManager()
    for key, spec in FIGS.items():
        if keys and key not in keys: continue
        lay = load_template(spec.get("a3", False)); lay.setName(key); layers = list(spec["stack"]) + ([spec["hs"]] if spec["hs"] is not None else []) + ([sat] if (sat is not None and spec["sat"]) else [])
        m = [i for i in lay.items() if isinstance(i, QgsLayoutItemMap)][0]; m.setCrs(UTM); m.setLayers(layers); m.setKeepLayerSet(True); m.zoomToExtent(spec["extent"]); m.setBackgroundColor(QColor("#FFFFFF"))
        furnish(lay, spec, m)
        old = mgr.layoutByName(key)
        if old: mgr.removeLayout(old)
        mgr.addLayout(lay); path = os.path.join(PNG, f"{key}.png"); exp = QgsLayoutExporter(lay); st = QgsLayoutExporter.ImageExportSettings(); st.dpi = dpi
        rc = exp.exportToImage(path, st); made.append((key, rc == QgsLayoutExporter.Success)); print(key, "ok" if rc == QgsLayoutExporter.Success else f"FAILED {rc}")
    # the RUSLE sheet: six panels on one A3 landscape page, each with its own legend, Google satellite behind, dam names in black
    if not keys or "M07_rusle" in keys:
        lay = QgsPrintLayout(proj); lay.initializeDefaults(); lay.setName("M07_rusle"); pc = lay.pageCollection(); pg = pc.page(0); pg.setPageSize("A3", QgsLayoutItemPage.Landscape)
        t = QgsLayoutItemLabel(lay); t.setText("RUSLE factors and soil loss over the dam catchments, and the sediment yield per dam"); tf = QgsTextFormat(); f = QFont("Arial"); f.setBold(True); tf.setFont(f); tf.setSize(14); t.setTextFormat(tf); lay.addLayoutItem(t); t.attemptMove(QgsLayoutPoint(8, 4, MM)); t.attemptResize(QgsLayoutSize(300, 8, MM))
        s = QgsLayoutItemLabel(lay); s.setText(SUBTITLE + " | " + "R rainfall erosivity, K soil erodibility, LS slope, C cover; P = 1; A = R K LS C P; yield by Williams (1977) with the 0.2 and 90 m³/km²/yr floors"); tf2 = QgsTextFormat(); tf2.setFont(QFont("Arial")); tf2.setSize(8); s.setTextFormat(tf2); lay.addLayoutItem(s); s.attemptMove(QgsLayoutPoint(8, 12, MM)); s.attemptResize(QgsLayoutSize(400, 5, MM))
        panels = [("R", RF["R"], "Rainfall erosivity R"), ("K", RF["K"], "Soil erodibility K"), ("LS", RF["LS"], "Slope length and steepness LS"), ("C", RF["C"], "Cover management C"), ("SoilLoss", RF["SoilLoss"], "Soil loss A = R K LS C P"), ("yield", cy, "Sediment yield and storage lost in 50 years")]
        pw, ph = 131.0, 128.0; x0, y0 = 8.0, 19.0
        for i, (key, layer, ttl) in enumerate(panels):
            px, py = x0 + (i % 3) * (pw + 6.0), y0 + (i // 3) * (ph + 10.0)
            m = QgsLayoutItemMap(lay); lay.addLayoutItem(m); m.attemptMove(QgsLayoutPoint(px, py + 6, MM)); m.attemptResize(QgsLayoutSize(pw, ph - 6, MM)); m.setCrs(UTM); m.setFrameEnabled(True); m.setFrameStrokeWidth(QgsLayoutMeasurement(0.3, MM))
            m.setLayers(([dam_pts_small] if key != "yield" else []) + [axes_l, cat_nolab, layer] + ([sat] if sat else [hs])); m.setKeepLayerSet(True); m.zoomToExtent(E_CAT)
            lb = QgsLayoutItemLabel(lay); lb.setText(ttl); tf3 = QgsTextFormat(); f3 = QFont("Arial"); f3.setBold(True); tf3.setFont(f3); tf3.setSize(10); lb.setTextFormat(tf3); lay.addLayoutItem(lb); lb.attemptMove(QgsLayoutPoint(px, py, MM)); lb.attemptResize(QgsLayoutSize(pw, 6, MM))
            lg = QgsLayoutItemLegend(lay); lay.addLayoutItem(lg); lg.setLinkedMap(m); lg.setAutoUpdateModel(False); grp = lg.model().rootGroup()
            for c in list(grp.children()): grp.removeChildNode(c)
            node = grp.addLayer(layer)
            if isinstance(layer, QgsRasterLayer):
                lg.model().refreshLayerLegend(node); kids = lg.model().layerLegendNodes(node); keep = [k for k, kk in enumerate(kids) if type(kk).__name__ != "QgsSimpleLegendNode"]
                if keep and len(keep) < len(kids): QgsMapLayerLegendUtils.setLegendNodeOrder(node, keep); lg.model().refreshLayerLegend(node)
            lg.setTitle(""); lg.setBackgroundEnabled(True); lg.setBackgroundColor(QColor(255, 255, 255, 230)); lg.setFrameEnabled(True); lg.setFrameStrokeWidth(QgsLayoutMeasurement(0.2, MM))
            for sty in (QgsLegendStyle.Subgroup, QgsLegendStyle.SymbolLabel):
                fl = QFont("Arial"); fl.setPointSizeF(6.5 if sty == QgsLegendStyle.SymbolLabel else 7.0); fl.setBold(sty == QgsLegendStyle.Subgroup); lg.rstyle(sty).setFont(fl)
            lg.setResizeToContents(True); lg.setReferencePoint(QgsLayoutItem.LowerLeft); lg.attemptMove(QgsLayoutPoint(px + 2, py + ph - 2, MM), True); lg.adjustBoxSize()
        n = QgsLayoutItemLabel(lay); n.setText("N\n▲"); tfn = QgsTextFormat(); tfn.setFont(QFont("Arial")); tfn.setSize(12); n.setTextFormat(tfn); lay.addLayoutItem(n); n.attemptMove(QgsLayoutPoint(405, 4, MM)); n.attemptResize(QgsLayoutSize(12, 12, MM))
        sb = QgsLayoutItemScaleBar(lay); lay.addLayoutItem(sb); sb.setLinkedMap([i for i in lay.items() if isinstance(i, QgsLayoutItemMap)][0]); sb.setStyle("Single Box"); sb.setUnits(Qgis.DistanceUnit.Meters); sb.setSegmentSizeMode(Qgis.ScaleBarSegmentSizeMode.Fixed); sb.setNumberOfSegments(4); sb.setUnitsPerSegment(5000); sb.setNumberOfSegmentsLeft(0); sb.setMapUnitsPerScaleBarUnit(1000); sb.setUnitLabel("km"); sb.attemptMove(QgsLayoutPoint(330, 6, MM))
        cr = QgsLayoutItemLabel(lay); cr.setText("Background: Google satellite image. Grid: 250 m (RUSLE), catchments from the hydrology study."); tfc = QgsTextFormat(); tfc.setFont(QFont("Arial")); tfc.setSize(6); cr.setTextFormat(tfc); lay.addLayoutItem(cr); cr.attemptMove(QgsLayoutPoint(8, 291, MM)); cr.attemptResize(QgsLayoutSize(200, 4, MM))
        old = mgr.layoutByName("M07_rusle")
        if old: mgr.removeLayout(old)
        mgr.addLayout(lay); path = os.path.join(PNG, "M07_rusle.png"); exp = QgsLayoutExporter(lay); st = QgsLayoutExporter.ImageExportSettings(); st.dpi = dpi; rc = exp.exportToImage(path, st); print("M07_rusle", "ok" if rc == QgsLayoutExporter.Success else f"FAILED {rc}")
    for l in list(proj.mapLayers().values()):
        if proj.layerTreeRoot().findLayer(l.id()) is None: proj.layerTreeRoot().addLayer(l)
    proj.write(os.path.join(W8, "maps", "Block04_SW_R2_maps.qgz" if DIM_FP else "Block04_R7_maps.qgz")); return made
if __name__ == "__main__":
    keys = [a for a in sys.argv[1:] if a in FIGS or a == "M07_rusle"] or None
    print(build(keys)); app.exitQgis()
