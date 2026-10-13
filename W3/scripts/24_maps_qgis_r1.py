"""Step 24 - map figures for report R1 (engineer's comments of 2026-10-06), standalone PyQGIS on the Ibri W17 layout:
legend inside the frame, data box and key table of one width, long scale bar, no 'WS11', tighter zoom, dam axes in their
own colour on top, the engineer's symbology (QML exported by step 15) for channels, dams, roads, utilities, land use,
flood depth; Google satellite background where useful. One A3 sheet with the five RUSLE factor maps and the yield.
run:  "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" 24_maps_qgis_r1.py [keys]   -> maps/png_r1/<key>.png, maps/Block04_R1_maps.qgz
"""
import os, sys, json
from qgis.core import (QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsPrintLayout, QgsReadWriteContext, QgsLayoutItemLabel, QgsLayoutItemMap, QgsLayoutItemLegend,
                       QgsLayoutItemScaleBar, QgsLayoutFrame, QgsLayoutItemManualTable, QgsLayoutItemHtml, QgsLayoutExporter, QgsRectangle, QgsCoordinateReferenceSystem, QgsFillSymbol, QgsLineSymbol,
                       QgsMarkerSymbol, QgsSingleSymbolRenderer, QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsGraduatedSymbolRenderer, QgsRendererRange, QgsPalLayerSettings,
                       QgsVectorLayerSimpleLabeling, QgsTextFormat, QgsTextBufferSettings, QgsSingleBandPseudoColorRenderer, QgsColorRampShader, QgsRasterShader, QgsSingleBandGrayRenderer,
                       QgsContrastEnhancement, QgsMapLayerLegendUtils, QgsTableCell, QgsLayoutSize, QgsLayoutPoint, QgsUnitTypes, QgsLegendStyle, QgsLayoutMeasurement, QgsLayoutItemPage, QgsLayoutItemShape, QgsLayoutItem, QgsLayoutTable, QgsFeatureRequest, Qgis)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtXml import QDomDocument
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", r"C:\Program Files\QGIS 3.44.8\apps\qgis-ltr"), True)
app = QgsApplication([], False); app.initQgis()

HERE = os.path.dirname(os.path.abspath(__file__)); W3 = os.path.dirname(HERE); CB04 = os.path.dirname(W3); B4 = os.path.dirname(CB04)
DATA = os.path.join(W3, "maps", "data"); STY = os.path.join(W3, "maps", "styles"); PNG = os.path.join(W3, "maps", "png_r1"); os.makedirs(PNG, exist_ok=True)
TEMPLATE_XML = os.path.join(W3, "maps", "template", "ibri_W17_S1_zones_layout.xml")
SUBTITLE = "Flood Protection Scheme in North and South Al Batinah — Block 04"; CREDIT = {True: "Background: Google satellite image and the hillshade of the 10 m terrain model", False: "Background: hillshade of the 10 m terrain model"}
UTM = QgsCoordinateReferenceSystem("EPSG:32640"); MM = QgsUnitTypes.LayoutMillimeters
ext = json.load(open(os.path.join(DATA, "extent.json"))); RS = ext["raster_stats"]
DAMS9 = ["Hawasinah 02", "Hawasinah 11", "Hawasinah EX", "Shafan 02", "Shafan 08", "Sarami 03", "Sarami 05", "Sakhin 04", "Sakhin 08"]
LABEL = {"Hawasinah EX": "Hawasinah UP", "Sakhin 08": "Sakhin 08 (Mehmum)"}; lab = lambda d: LABEL.get(d, d)
W = "W:/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/06-WORKING/"
SRC = {"channels": os.path.join(B4, "Hydrology", "SHP", "temp", "Channels and Dykes 04102026.shp"), "dam_axis": os.path.join(B4, "Hydrology", "SHP", "Block 4 Dams", "Dams updated.shp"), "dam_dikes": os.path.join(B4, "Hydrology", "SHP", "Block 4 Dams", "Dikes.shp"),
       "fsl_polygon": W + "04-Hydraulic/05 Small Tasks/18 Channel Design/SHP/Block 04 Dams/Polygon_FSL.shp", "crest_polygon": W + "04-Hydraulic/05 Small Tasks/18 Channel Design/SHP/Block 04 Dams/Ppygon_Crest_Level.shp",
       "depth_200yr": W + "04-Hydraulic/00 Data/Layers/Flood Maps/Depth/Rasters OK/B4 Depth Rasters/Block4_200Yr.tif", "landuse": W + "13-Study and Design/01-FS and PD/00-General/02-Land Use/ALL_MOH_CLEANED/LandUSE_block4.shp",
       "highway": W + "03-Hydrology/01 GIS DATA/SHP/Bathinah Highway CL.shp", "coastal_road": W + "03-Hydrology/01 GIS DATA/SHP/Batinah Coastal RD CL.shp", "expressway": W + "03-Hydrology/01 GIS DATA/SHP/Muscat Expressway CL.shp",
       "bypass": os.path.join(B4, "Hydrology", "SHP", "Bypass road alignment", "North Batina Bypass.shp"), "pipeline_south": W + "04-Hydraulic/000 Correspond/02 Sent/2026.01.12 PDO pipeline/SHP/South/Pipeline.shp",
       "pipeline_north": W + "04-Hydraulic/000 Correspond/02 Sent/2026.01.12 PDO pipeline/SHP/North/Pipelines.shp", "culverts": "W:/2425 Supervision of Sultan Taymur Bin Faysal Road_MOTC&IT/06-WORKING/03-Hydrology/05_Shape Files/Culverts_RDs.shp"}
proj = QgsProject.instance(); proj.setCrs(UTM)

def label_layer(layer, field, size=7.5, colour="#1F3B63", bold=True, buffer=0.9, expression=False):
    pal = QgsPalLayerSettings(); pal.fieldName = field; pal.isExpression = expression; pal.enabled = True
    tf = QgsTextFormat(); f = QFont("Arial"); f.setBold(bold); tf.setFont(f); tf.setSize(size); tf.setColor(QColor(colour))
    b = QgsTextBufferSettings(); b.setEnabled(True); b.setSize(buffer); b.setColor(QColor("#FFFFFF")); tf.setBuffer(b); pal.setFormat(tf); layer.setLabelsEnabled(True); layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
def vec(path, name, layer=None, qml=None):
    l = QgsVectorLayer(path if layer is None else f"{path}|layername={layer}", name, "ogr"); assert l.isValid(), path
    if qml and os.path.exists(os.path.join(STY, qml + ".qml")): l.loadNamedStyle(os.path.join(STY, qml + ".qml")); l.setLabelsEnabled(False)
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

# ------------------------------------------------------------------ layers
hs = QgsRasterLayer(os.path.join(DATA, "hillshade.tif"), "Terrain hillshade"); gr = QgsSingleBandGrayRenderer(hs.dataProvider(), 1); ce = QgsContrastEnhancement(hs.dataProvider().dataType(1)); ce.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum); ce.setMinimumValue(60); ce.setMaximumValue(255); gr.setContrastEnhancement(ce); hs.setRenderer(gr); hs.setOpacity(0.5); proj.addMapLayer(hs, False)
google = QgsRasterLayer("type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=18&zmin=0", "Google satellite", "wms"); sat = google if google.isValid() else None
if sat: sat.setOpacity(0.85); proj.addMapLayer(sat, False)
cat = vec(os.path.join(DATA, "dam_catchments_results.gpkg"), "Dam catchment", "catchments"); fill(cat, "0,0,0,0", "#F2F2F2", 0.9); label_layer(cat, "name", 8.0, "#FFFFFF", True, 1.0)
cat.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": "#FFD966", "outline_width": "0.75", "outline_width_unit": "MM"})))
label_layer(cat, '"label_s"', 8.0, "#FFD966", True, 1.0, expression=True)
cat_nolab = vec(os.path.join(DATA, "dam_catchments_results.gpkg"), "Dam catchment", "catchments"); cat_nolab.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": "#FFD966", "outline_width": "0.75", "outline_width_unit": "MM"}))); cat_nolab.setLabelsEnabled(False)
axes_l = vec(SRC["dam_axis"], "Dam axis", qml="dam_axis"); line(axes_l, "#FF00FF", 1.3)
dikes = vec(SRC["dam_dikes"], "Dam dyke", qml="dam_dikes"); line(dikes, "#FF00FF", 0.9, "dash")
fslp = vec(SRC["fsl_polygon"], "Reservoir at full supply level", qml="fsl_polygon"); crp = vec(SRC["crest_polygon"], "Reservoir at crest level", qml="crest_polygon")
ch = vec(SRC["channels"], "Channels and dykes", qml="channels_dykes"); ch.setSubsetString('"Block" = 4')
CHNAMES = {"FP CH": "Flood protection channel", "Sw M CH": "Stormwater main channel", "Sw S CH": "Stormwater secondary channel", "FP D": "Flood protection dyke", "Sw M D": "Stormwater main dyke", "Sw S D": "Stormwater secondary dyke"}
_r = ch.renderer()
if _r is not None and _r.type() == "categorizedSymbol":
    for _i, _c in enumerate(_r.categories()): _r.updateCategoryLabel(_i, CHNAMES.get(str(_c.value()), str(_c.label())))
chc = vec(SRC["channels"], "Channel category"); chc.setSubsetString('"Block" = 4'); cats = []
for key, lab_, col, wd in (("FP CH", "Flood protection channel", "#C00000", 0.7), ("Sw M CH", "Stormwater main channel", "#0070C0", 0.5), ("Sw S CH", "Stormwater secondary channel", "#00B0F0", 0.35), ("FP D", "Flood protection dyke", "#7030A0", 0.7), ("Sw M D", "Stormwater main dyke", "#8E44AD", 0.5), ("Sw S D", "Stormwater secondary dyke", "#B07CC6", 0.35)):
    cats.append(QgsRendererCategory(key, QgsLineSymbol.createSimple({"color": col, "width": str(wd), "width_unit": "MM", "capstyle": "round", "line_style": "dash" if key.endswith(" D") else "solid"}), lab_))
chc.setRenderer(QgsCategorizedSymbolRenderer("CHtt", cats))
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
sub = vec(os.path.join(W3, "elements", "shp", "B3", "Subbasins_B3.shp"), "HEC-HMS subbasin"); fill(sub, "0,0,0,0", "#E97132", 0.25)
rch = vec(os.path.join(W3, "elements", "shp", "B3", "Reaches_B3.shp"), "HEC-HMS reach"); line(rch, "#0162FF", 0.5)
pts = vec(os.path.join(W3, "elements", "shp", "B3", "Points_B3.shp"), "HEC-HMS node"); pcats = []
for key, lab_, props in (("Junction", "Junction", {"name": "circle", "color": "#FFFFFF", "outline_color": "#1F1F1F", "outline_width": "0.25", "size": "1.4"}), ("Outfall", "Outfall to the sea", {"name": "triangle", "color": "#00B050", "outline_color": "#1F1F1F", "outline_width": "0.25", "size": "2.4"}),
                        ("Dam junction", "Dam site", {"name": "diamond", "color": "#C00000", "outline_color": "#FFFFFF", "outline_width": "0.3", "size": "3.0"}), ("Reservoir", "Reservoir element", {"name": "square", "color": "#2E75B6", "outline_color": "#FFFFFF", "outline_width": "0.3", "size": "2.2"})):
    pcats.append(QgsRendererCategory(key, QgsMarkerSymbol.createSimple(props), lab_))
pts.setRenderer(QgsCategorizedSymbolRenderer("type", pcats)); pts.setSubsetString("\"type\" IN ('Junction', 'Outfall')")
q2 = vec(os.path.join(W3, "elements", "shp", "B3", "Points_B3.shp"), "Junction: 200-year peak flow (m³/s)"); q2.setSubsetString("\"type\" IN ('Junction', 'Outfall', 'Dam junction')")
q2.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "circle", "color": "#1F4FD8", "outline_color": "#FFFFFF", "outline_width": "0.25", "size": "1.9"})))
label_layer(q2, 'format_number("Q200", 0)', 6.8, "#1F1F1F", True, 0.9, expression=True)
try:
    _q = q2.labeling().settings(); _q.placement = Qgis.LabelPlacement.OrderedPositionsAroundPoint; _q.placementSettings().setOverlapHandling(Qgis.LabelOverlapHandling.AllowOverlapIfRequired)
    _tf = _q.format(); _f = _tf.font(); _f.setItalic(True); _tf.setFont(_f); _q.setFormat(_tf); q2.setLabeling(QgsVectorLayerSimpleLabeling(_q))
except Exception as _e: print("q200 labels:", _e)
sub_o = vec(os.path.join(W3, "elements", "shp", "B3", "Subbasins_B3.shp"), "HEC-HMS subbasin"); fill(sub_o, "0,0,0,0", "#E97132", 0.3)
rch_o = vec(os.path.join(W3, "elements", "shp", "B3", "Reaches_B3.shp"), "HEC-HMS reach"); line(rch_o, "#00B0F0", 0.55)
cat_k = vec(os.path.join(DATA, "dam_catchments_results.gpkg"), "Dam catchment", "catchments"); cat_k.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": "#1F1F1F", "outline_width": "0.6", "outline_width_unit": "MM"}))); cat_k.setLabelsEnabled(False)
BLUES = ["#F7FBFF", "#C6DBEF", "#6BAED6", "#2171B5", "#08306B"]; BROWNS = ["#FFF7EC", "#FDD49E", "#FC8D59", "#D7301F", "#7F0000"]; PURPLES = ["#FCFBFD", "#DADAEB", "#9E9AC8", "#6A51A3", "#3F007D"]; GREENS = ["#F7FCF5", "#C7E9C0", "#74C476", "#238B45", "#00441B"]; ORANGES = ["#FFF5EB", "#FDD0A2", "#FD8D3C", "#D94801", "#7F2704"]
RF = {k: ramp_raster(os.path.join(DATA, f"{k}_catchments.tif"), nm, RS[k]["p2"], RS[k]["p98"], cols, dec) for k, nm, cols, dec in (("R", "R factor, MJ mm/(ha h yr)", BLUES, 0), ("K", "K factor, t ha h/(ha MJ mm)", BROWNS, 3), ("LS", "LS factor", PURPLES, 0), ("C", "C factor", GREENS, 3), ("SoilLoss", "Soil loss, t/ha/yr", ORANGES, 0))}
cy = vec(os.path.join(DATA, "dam_catchments_results.gpkg"), "Sediment yield, m³/km²/yr", "catchments_excl")
rngs = [(0, 100, "90 (floor) to 100", "#FEE8C8"), (100, 140, "100 to 140", "#FDBB84"), (140, 170, "140 to 170", "#E34A33"), (170, 300, "over 170", "#7F0000")]
cy.setRenderer(QgsGraduatedSymbolRenderer("yield_m3km2", [QgsRendererRange(lo, hi, QgsFillSymbol.createSimple({"color": c, "outline_color": "#FFFFFF", "outline_width": "0.3", "outline_width_unit": "MM"}), lab_) for lo, hi, lab_, c in rngs]))
label_layer(cy, '"label_s" || \'\\n\' || format_number("yield_m3km2", 0) || \' m³/km²/yr\' || \'\\n\' || format_number("loss50_pct", 1) || \' % in 50 yr\'', 6.8, "#1F1F1F", True, 0.9, expression=True)
try:
    _ps = cy.labeling().settings(); _ps.placementSettings().setOverlapHandling(Qgis.LabelOverlapHandling.AllowOverlapIfRequired); cy.setLabeling(QgsVectorLayerSimpleLabeling(_ps))
except Exception as _e: print("label overlap setting:", _e)
try:
    _ob = QgsFeatureRequest.OrderBy([QgsFeatureRequest.OrderByClause("area_km2", False)]); cy.renderer().setOrderBy(_ob); cy.renderer().setOrderByEnabled(True)
except Exception as _e: print("order by:", _e)
# ------------------------------------------------------------------ extents and figures
def rect(b, s): r = QgsRectangle(b[0], b[1], b[2], b[3]); r.scale(s); return r
E_ALL = rect(ext["all"], 1.04); E_CAT = rect(ext["catchments"], 1.05); E_PLAIN = rect(ext["channels_dams"], 1.06)
E_PLAIN_Q = rect([ext["channels_dams"][0], ext["channels_dams"][1] - 6000, ext["channels_dams"][2], ext["channels_dams"][3]], 1.04)
def per_dam(field, fmt): vals = {f["name"]: float(f[field]) for f in cat.getFeatures()}; return [(lab(d), fmt(vals[d])) for d in DAMS9 if d in vals]
FIGS = {
 "M01_dams": ("Dams and their catchments", [axes_l, dikes, crp, fslp, cat, ch], E_ALL, True, [("Dams", "9"), ("Catchment area controlled", f"{ext['controlled_km2']:,.0f} km²"), ("Channels and dykes", f"{sum(f.geometry().length() for f in ch.getFeatures()) / 1000:,.0f} km")], per_dam("area_km2", lambda v: f"{v:,.0f} km²"), "Catchment area"),
 "M02_channel_category": ("Channel category classification", [chc, axes_l], E_PLAIN, True, [("Flood protection channels", f"{sum(f.geometry().length() for f in ch.getFeatures() if f['CHtt'] == 'FP CH') / 1000:,.0f} km"), ("Stormwater main channels", f"{sum(f.geometry().length() for f in ch.getFeatures() if f['CHtt'] == 'Sw M CH') / 1000:,.0f} km"), ("Stormwater secondary channels", f"{sum(f.geometry().length() for f in ch.getFeatures() if f['CHtt'] == 'Sw S CH') / 1000:,.0f} km"), ("Dykes", f"{sum(f.geometry().length() for f in ch.getFeatures() if str(f['CHtt']).endswith(' D')) / 1000:,.0f} km")], [], None),
 "M03_alignments_flood": ("Channel alignments to control the 200-year flood", [chc, axes_l, depth], E_PLAIN, False, [("Flood depth", "200-year, no scheme"), ("Channels", "flood protection, stormwater"), ("Dams", "9")], [], None),
 "M04_routes": ("Channel and dyke routes", [ch, axes_l, dikes, fslp], E_PLAIN, True, [("Channels and dykes", f"{sum(f.geometry().length() for f in ch.getFeatures()) / 1000:,.0f} km"), ("Dams", "9")], [], None),
 "M05_roads_utilities": ("Roads and utilities", roads + pipes + [culv, chc], E_PLAIN, True, [("Batinah Expressway", "existing"), ("Batinah Highway", "existing"), ("Batinah Coastal Road", "existing"), ("North Batinah Bypass", "planned"), ("OQ pipelines", "shallow, to be verified")], [], None),
 "M06_landuse": ("Land use", [lu, chc, axes_l], E_PLAIN, False, [("Source", "MoHUP cadastre"), ("Channels", "flood protection, stormwater"), ("Dams", "9")], [], None),
 "M08_hms": ("The HEC-HMS model: subbasins, reaches, junctions and dams", [sub, rch, pts, axes_l, cat], E_ALL, True, [("Subbasins", str(sub.featureCount())), ("Reaches", str(rch.featureCount())), ("Junctions and outfalls", str(pts.featureCount())), ("Dams", "9")], [], None),
 "M10_q200": ("200-year peak flow (m³/s) at the junctions of the HEC-HMS model", [sub_o, rch_o, q2, cat_k, axes_l], E_ALL, True, [("Junctions and outfalls", str(q2.featureCount())), ("Design event", "200-year, dams in place"), ("Dams", "9")], [], None),
 "M11_q200_plain": ("200-year peak flow (m³/s) at the junctions: the coastal plain", [sub_o, rch_o, q2, cat_k, axes_l], E_PLAIN_Q, True, [("Junctions and outfalls", str(q2.featureCount())), ("Design event", "200-year, dams in place"), ("Dams", "9")], [], None),
 "M09_yield": ("Sediment yield per dam and the storage lost in 50 years", [cy, axes_l], E_CAT, True, [("Yield", "RUSLE, Williams SDR"), ("Floors", "SDR 0.2; 90 m³/km²/yr"), ("Storage lost, 50 yr", f"{min(float(f['loss50_pct']) for f in cat.getFeatures()):.0f} – {max(float(f['loss50_pct']) for f in cat.getFeatures()):.0f} % of capacity")], per_dam("loss50_pct", lambda v: f"{v:.1f} % (50 yr)"), "Storage lost at FSL"),
}
def load_template():
    lay = QgsPrintLayout(proj); doc = QDomDocument(); doc.setContent(open(TEMPLATE_XML, encoding="utf-8").read()); lay.loadFromTemplate(doc, QgsReadWriteContext(), True); return lay
TABLE_H = [20.0]
def furnish(lay, title, m, stack, table_rows, box_rows, box_title, legend_layers=None, with_sat=True):
    items = sorted(lay.items(), key=lambda i: 0 if (isinstance(i, QgsLayoutFrame) and isinstance(i.multiFrame(), QgsLayoutItemManualTable)) else 1)   # the table first: the box sits on it
    for it in items:
        if isinstance(it, QgsLayoutItemLabel):
            t = it.text()
            if t.startswith("Ibri Sewer"): it.setText(SUBTITLE); it.attemptResize(QgsLayoutSize(260, 4.5, MM))
            elif t.startswith("Satellite image") or t.startswith("Background"): it.setText(CREDIT[with_sat]); it.attemptResize(QgsLayoutSize(120, 3.5, MM))
            elif t and not t.startswith("N"): it.setText(title); it.attemptResize(QgsLayoutSize(185, 6.5, MM)); tf = it.textFormat(); tf.setSize(13); it.setTextFormat(tf)
        elif isinstance(it, QgsLayoutItemScaleBar):
            it.setLinkedMap(m); it.setUnits(Qgis.DistanceUnit.Meters); it.setSegmentSizeMode(Qgis.ScaleBarSegmentSizeMode.Fixed); it.setStyle("Single Box"); it.setNumberOfSegments(4); it.setUnitsPerSegment(5000); it.setNumberOfSegmentsLeft(0); it.setMapUnitsPerScaleBarUnit(1000); it.setUnitLabel("km"); it.setHeight(2.0); it.setLabelBarSpace(1.0)
            tfs = it.textFormat(); tfs.setSize(8); tfs.setFont(QFont("Arial")); it.setTextFormat(tfs); it.setReferencePoint(QgsLayoutItem.UpperLeft); it.attemptMove(QgsLayoutPoint(170.0, 5.0, MM)); it.attemptResize(QgsLayoutSize(60, 8, MM))
        elif isinstance(it, QgsLayoutItemLegend):
            it.setLinkedMap(m); it.setAutoUpdateModel(False); grp = it.model().rootGroup()
            for c in list(grp.children()): grp.removeChildNode(c)
            for l in (legend_layers or stack):
                if l.name().endswith("(south)"): continue
                node = grp.addLayer(l); r = getattr(l, "renderer", lambda: None)()
                if r is not None and r.type() in ("categorizedSymbol", "graduatedSymbol"): node.setCustomProperty("legend/title-style", "visible")
                if isinstance(l, QgsRasterLayer):
                    it.model().refreshLayerLegend(node); kids = it.model().layerLegendNodes(node); keep = [i for i, k in enumerate(kids) if type(k).__name__ != "QgsSimpleLegendNode"]
                    if keep and len(keep) < len(kids): QgsMapLayerLegendUtils.setLegendNodeOrder(node, keep); it.model().refreshLayerLegend(node)
            it.setTitle(""); it.setBackgroundEnabled(True); it.setBackgroundColor(QColor(255, 255, 255, 235)); it.setResizeToContents(True)
            for sty in (QgsLegendStyle.Subgroup, QgsLegendStyle.SymbolLabel):
                f = QFont("Arial"); f.setPointSizeF(6.5 if sty == QgsLegendStyle.SymbolLabel else 7.0); f.setBold(sty == QgsLegendStyle.Subgroup); it.rstyle(sty).setFont(f)
            it.setWrapString(""); nrows = sum(1 + len(it.model().layerLegendNodes(it.model().rootGroup().findLayer(l.id()))) for l in (legend_layers or stack) if it.model().rootGroup().findLayer(l.id()) is not None)
            it.setColumnCount(2 if nrows > 14 else 1); it.setSplitLayer(True); it.setEqualColumnWidth(False); it.setFrameEnabled(True); it.setFrameStrokeWidth(QgsLayoutMeasurement(0.2, MM))
            mp, ms = m.positionWithUnits(), m.sizeWithUnits(); it.setReferencePoint(QgsLayoutItem.LowerLeft); it.attemptMove(QgsLayoutPoint(mp.x() + 2.5, mp.y() + ms.height() - 2.5, MM), True); it.adjustBoxSize()
        elif isinstance(it, QgsLayoutFrame):
            mf = it.multiFrame()
            if isinstance(mf, QgsLayoutItemManualTable):
                mf.setTableContents([[QgsTableCell(a), QgsTableCell(b)] for a, b in table_rows]); mf.setGridStrokeWidth(0.15); mf.setGridColor(QColor("#9DA9B8"))
                tfc = mf.contentTextFormat(); tfc.setSize(7.5); tfc.setFont(QFont("Arial")); tfc.setColor(QColor("#1F3B63")); mf.setContentTextFormat(tfc); mf.setWrapBehavior(QgsLayoutTable.WrapText)
                cols = mf.columns()
                if len(cols) >= 2: cols[0].setWidth(38.0); cols[1].setWidth(34.0); mf.setColumns(cols)
                mf.refreshAttributes(); h = max(4.3 * len(table_rows) + 1.5, mf.totalHeight() + 1.0); it.attemptResize(QgsLayoutSize(72.0, h, MM)); it.attemptMove(QgsLayoutPoint(216.0, 201.5 - h, MM)); TABLE_H[0] = h
            elif isinstance(mf, QgsLayoutItemHtml):
                if box_rows:
                    rows = "".join(f"<tr><td style='padding:1px 4px'>{a}</td><td align='right' style='padding:1px 4px'>{b}</td></tr>" for a, b in box_rows)
                    mf.setContentMode(QgsLayoutItemHtml.ManualHtml); mf.setHtml(f"<html><body style='margin:0;font-family:Arial;font-size:7pt;color:#1F3B63'><div style='background:#FFFFFF;border:0.3px solid #1F3B63;padding:3px'><b>{box_title}</b><table style='font-size:7pt;border-collapse:collapse;margin-top:2px'>{rows}</table></div></body></html>"); mf.loadHtml()
                    hbox = 7 + 3.9 * len(box_rows); it.attemptResize(QgsLayoutSize(72.0, hbox, MM)); it.attemptMove(QgsLayoutPoint(216.0, 201.5 - TABLE_H[0] - 2.0 - hbox, MM))
                else: lay.removeLayoutItem(it)
def build(keys=None, dpi=200):
    made = []; mgr = proj.layoutManager()
    for key, (title, stack, extent, with_sat, table_rows, box_rows, box_title) in FIGS.items():
        if keys and key not in keys: continue
        lay = load_template(); lay.setName(key); layers = list(stack) + [hs] + ([sat] if (sat is not None and with_sat) else [])
        m = [i for i in lay.items() if isinstance(i, QgsLayoutItemMap)][0]; m.setCrs(UTM); m.setLayers(layers); m.setKeepLayerSet(True); m.zoomToExtent(extent); m.setBackgroundColor(QColor("#FFFFFF"))
        furnish(lay, title, m, stack, table_rows, box_rows, box_title, with_sat=with_sat)
        old = mgr.layoutByName(key)
        if old: mgr.removeLayout(old)
        mgr.addLayout(lay); path = os.path.join(PNG, f"{key}.png"); exp = QgsLayoutExporter(lay); st = QgsLayoutExporter.ImageExportSettings(); st.dpi = dpi
        rc = exp.exportToImage(path, st); made.append((key, rc == QgsLayoutExporter.Success)); print(key, "ok" if rc == QgsLayoutExporter.Success else f"FAILED {rc}")
    # the RUSLE sheet: six panels on one A3 landscape page, each with its own legend, Google satellite behind
    if not keys or "M07_rusle" in keys:
        lay = QgsPrintLayout(proj); lay.initializeDefaults(); lay.setName("M07_rusle"); pc = lay.pageCollection(); pg = pc.page(0); pg.setPageSize("A3", QgsLayoutItemPage.Landscape)
        t = QgsLayoutItemLabel(lay); t.setText("RUSLE factors and soil loss over the dam catchments, and the sediment yield per dam"); tf = QgsTextFormat(); f = QFont("Arial"); f.setBold(True); tf.setFont(f); tf.setSize(14); t.setTextFormat(tf); lay.addLayoutItem(t); t.attemptMove(QgsLayoutPoint(8, 4, MM)); t.attemptResize(QgsLayoutSize(300, 8, MM))
        s = QgsLayoutItemLabel(lay); s.setText(SUBTITLE + " | " + "R rainfall erosivity, K soil erodibility, LS slope, C cover; P = 1; A = R K LS C P; yield by Williams (1977) with the 0.2 and 90 m³/km²/yr floors"); tf2 = QgsTextFormat(); tf2.setFont(QFont("Arial")); tf2.setSize(8); s.setTextFormat(tf2); lay.addLayoutItem(s); s.attemptMove(QgsLayoutPoint(8, 12, MM)); s.attemptResize(QgsLayoutSize(400, 5, MM))
        panels = [("R", RF["R"], "Rainfall erosivity R"), ("K", RF["K"], "Soil erodibility K"), ("LS", RF["LS"], "Slope length and steepness LS"), ("C", RF["C"], "Cover management C"), ("SoilLoss", RF["SoilLoss"], "Soil loss A = R K LS C P"), ("yield", cy, "Sediment yield and storage lost in 50 years")]
        pw, ph = 131.0, 128.0; x0, y0 = 8.0, 19.0
        for i, (key, layer, ttl) in enumerate(panels):
            px, py = x0 + (i % 3) * (pw + 6.0), y0 + (i // 3) * (ph + 10.0)
            m = QgsLayoutItemMap(lay); lay.addLayoutItem(m); m.attemptMove(QgsLayoutPoint(px, py + 6, MM)); m.attemptResize(QgsLayoutSize(pw, ph - 6, MM)); m.setCrs(UTM); m.setFrameEnabled(True); m.setFrameStrokeWidth(QgsLayoutMeasurement(0.3, MM))
            m.setLayers([axes_l, cat_nolab if key == "yield" else cat, layer] + ([sat] if sat else [hs])); m.setKeepLayerSet(True); m.zoomToExtent(E_CAT)
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
    proj.write(os.path.join(W3, "maps", "Block04_R1_maps.qgz")); return made
if __name__ == "__main__":
    keys = [a for a in sys.argv[1:] if a in FIGS or a == "M07_rusle"] or None
    print(build(keys)); app.exitQgis()
