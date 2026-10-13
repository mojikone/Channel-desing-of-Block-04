"""Step 14 - map figures on the Ibri W17 layout template (A4 landscape: title, subtitle, map, legend, scale bar, north,
key-number table, data box), exported as PNG for the report, plus a QGIS project with every layout for hand adjustment.
run:  "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" 14_maps_qgis.py [figure keys]
Inputs: maps/data/* (step 13), maps/template/ibri_W17_S1_zones_layout.xml, elements/shp/B3, inputs/CH.shp + WALL.shp
Writes: maps/png/M<nn>_<key>.png (200 dpi), maps/Block04_W3_maps.qgz
"""
import os, sys, json
from qgis.core import (QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsPrintLayout, QgsReadWriteContext, QgsLayoutItemLabel, QgsLayoutItemMap, QgsLayoutItemLegend,
                       QgsLayoutItemScaleBar, QgsLayoutFrame, QgsLayoutItemManualTable, QgsLayoutItemHtml, QgsLayoutExporter, QgsRectangle, QgsCoordinateReferenceSystem, QgsFillSymbol, QgsLineSymbol,
                       QgsMarkerSymbol, QgsSingleSymbolRenderer, QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsGraduatedSymbolRenderer, QgsRendererRange, QgsPalLayerSettings,
                       QgsVectorLayerSimpleLabeling, QgsTextFormat, QgsTextBufferSettings, QgsSingleBandPseudoColorRenderer, QgsColorRampShader, QgsRasterShader, QgsSingleBandGrayRenderer,
                       QgsContrastEnhancement, QgsMapLayerLegendUtils, QgsTableCell, QgsLayoutSize, QgsLayoutPoint, QgsUnitTypes, QgsLegendStyle, QgsLayoutItemPage, QgsLayoutMeasurement)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtXml import QDomDocument
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", r"C:\Program Files\QGIS 3.44.8\apps\qgis-ltr"), True)
app = QgsApplication([], False); app.initQgis()

HERE = os.path.dirname(os.path.abspath(__file__)); W3 = os.path.dirname(HERE); CB04 = os.path.dirname(W3)
DATA = os.path.join(W3, "maps", "data"); PNG = os.path.join(W3, "maps", "png"); os.makedirs(PNG, exist_ok=True)
TEMPLATE_XML = os.path.join(W3, "maps", "template", "ibri_W17_S1_zones_layout.xml")
SUBTITLE = "Flood Protection Scheme in North & South Batinah (MAFWWR) — Block 04: hydrology, dams and channels | Renardet 2224 WS11"
CREDIT = "Background: hillshade of the 10 m NSA terrain model; Esri World Imagery where shown"
UTM = QgsCoordinateReferenceSystem("EPSG:32640"); MM = QgsUnitTypes.LayoutMillimeters
ext = json.load(open(os.path.join(DATA, "extent.json"))); RS = ext["raster_stats"]
DAMS = ["Hawasinah 02", "Shafan 02", "Hawasinah EX", "Hawasinah 11", "Sarami 03", "Sarami 05", "Sakhin 08", "Sakhin 04"]
proj = QgsProject.instance(); proj.setCrs(UTM)
ACC = "1F4E79"

def label(layer, field, size=7.5, colour="#1F3B63", bold=True, buffer=0.9, expression=False, placement=None):
    pal = QgsPalLayerSettings(); pal.fieldName = field; pal.isExpression = expression; pal.enabled = True
    tf = QgsTextFormat(); f = QFont("Arial"); f.setBold(bold); tf.setFont(f); tf.setSize(size); tf.setColor(QColor(colour))
    b = QgsTextBufferSettings(); b.setEnabled(True); b.setSize(buffer); b.setColor(QColor("#FFFFFF")); tf.setBuffer(b); pal.setFormat(tf)
    if placement is not None: pal.placement = placement
    layer.setLabelsEnabled(True); layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))

def vec(path, name, layer=None):
    src = path if layer is None else f"{path}|layername={layer}"
    l = QgsVectorLayer(src, name, "ogr"); assert l.isValid(), src; proj.addMapLayer(l, False); return l

def fill(l, color="0,0,0,0", outline="#C00000", width=0.5, style=None):
    props = {"color": color, "outline_color": outline, "outline_width": str(width), "outline_width_unit": "MM"}
    if style: props["style"] = style
    if outline is None: props["outline_style"] = "no"
    l.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(props)))

def line(l, color, width=0.4, dash=None):
    props = {"color": color, "width": str(width), "width_unit": "MM", "capstyle": "round", "joinstyle": "round"}
    if dash: props["line_style"] = dash
    l.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple(props)))

def ramp_raster(path, name, lo, hi, colours, decimals=1, unit=""):
    r = QgsRasterLayer(path, name); assert r.isValid(), path
    sh = QgsColorRampShader(lo, hi, None, QgsColorRampShader.Interpolated, QgsColorRampShader.Continuous)
    n = len(colours); items = []
    for i, c in enumerate(colours):
        v = lo + (hi - lo) * i / (n - 1); items.append(QgsColorRampShader.ColorRampItem(v, QColor(c), f"{v:.{decimals}f}"))
    sh.setColorRampItemList(items); sh.setClip(False)
    rs = QgsRasterShader(); rs.setRasterShaderFunction(sh)
    rend = QgsSingleBandPseudoColorRenderer(r.dataProvider(), 1, rs); rend.setClassificationMin(lo); rend.setClassificationMax(hi); r.setRenderer(rend)
    from qgis.core import QgsColorRampLegendNodeSettings, QgsBasicNumericFormat
    st = QgsColorRampLegendNodeSettings(); fmt = QgsBasicNumericFormat(); fmt.setNumberDecimalPlaces(decimals); fmt.setShowTrailingZeros(False); st.setNumericFormat(fmt)
    st.setMinimumLabel(f"{lo:.{decimals}f} {unit}".strip()); st.setMaximumLabel(f"{hi:.{decimals}f} {unit}".strip()); sh.setLegendSettings(st)
    r.setOpacity(0.88); proj.addMapLayer(r, False); return r

# ------------------------------------------------------------------ layers
hs = QgsRasterLayer(os.path.join(DATA, "hillshade.tif"), "Terrain hillshade"); assert hs.isValid()
gr = QgsSingleBandGrayRenderer(hs.dataProvider(), 1); ce = QgsContrastEnhancement(hs.dataProvider().dataType(1)); ce.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum); ce.setMinimumValue(60); ce.setMaximumValue(255); gr.setContrastEnhancement(ce)
hs.setRenderer(gr); hs.setOpacity(0.55); proj.addMapLayer(hs, False)
sat = QgsRasterLayer("type=xyz&url=https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=18&zmin=0", "Esri World Imagery", "wms")
if sat.isValid(): sat.setOpacity(0.45); proj.addMapLayer(sat, False)
else: sat = None; print("satellite basemap not available")
cat = vec(os.path.join(DATA, "dam_catchments_results.gpkg"), "Dam catchment", "catchments"); fill(cat, "0,0,0,0", "#C00000", 0.55); label(cat, "name", 8.5, "#7F0000")
axes = vec(os.path.join(DATA, "dams.gpkg"), "Dam axis", "dam_axes"); line(axes, "#C00000", 1.1)
res = vec(os.path.join(DATA, "dams.gpkg"), "Reservoir at crest level", "reservoirs"); fill(res, "46,117,182,170", None)
ch = vec(os.path.join(CB04, "inputs", "CH.shp"), "Channel alignment"); line(ch, "#1F77B4", 0.3)
wall = vec(os.path.join(CB04, "inputs", "WALL.shp"), "Dyke or road"); line(wall, "#6E6E6E", 0.28, "dash")
sub = vec(os.path.join(W3, "elements", "shp", "B3", "Subbasins_B3.shp"), "HEC-HMS subbasin"); fill(sub, "0,0,0,0", "#E97132", 0.22); label(sub, "name", 5.2, "#9C4A14", bold=False, buffer=0.6)
rch = vec(os.path.join(W3, "elements", "shp", "B3", "Reaches_B3.shp"), "HEC-HMS reach"); line(rch, "#0162FF", 0.45)
pts = vec(os.path.join(W3, "elements", "shp", "B3", "Points_B3.shp"), "HEC-HMS node")
cats = []
for key, lab, props in (("Junction", "Junction", {"name": "circle", "color": "#FFFFFF", "outline_color": "#1F1F1F", "outline_width": "0.25", "size": "1.4"}),
                        ("Outfall", "Outfall to the sea", {"name": "triangle", "color": "#00B050", "outline_color": "#1F1F1F", "outline_width": "0.25", "size": "2.4"}),
                        ("Dam junction", "Dam site", {"name": "diamond", "color": "#C00000", "outline_color": "#FFFFFF", "outline_width": "0.3", "size": "3.0"}),
                        ("Reservoir", "Reservoir element", {"name": "square", "color": "#2E75B6", "outline_color": "#FFFFFF", "outline_width": "0.3", "size": "2.2"})):
    cats.append(QgsRendererCategory(key, QgsMarkerSymbol.createSimple(props), lab))
pts.setRenderer(QgsCategorizedSymbolRenderer("type", cats))
dpts = vec(os.path.join(DATA, "dams.gpkg"), "Dam", "dam_points"); dpts.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "diamond", "color": "#C00000", "outline_color": "#FFFFFF", "outline_width": "0.3", "size": "3.2"})))
# RUSLE rasters: one hue each, light -> dark (sequential), range 2-98 percentile of the catchment cells
BLUES = ["#F7FBFF", "#C6DBEF", "#6BAED6", "#2171B5", "#08306B"]; BROWNS = ["#FFF7EC", "#FDD49E", "#FC8D59", "#D7301F", "#7F0000"]; PURPLES = ["#FCFBFD", "#DADAEB", "#9E9AC8", "#6A51A3", "#3F007D"]
GREENS = ["#F7FCF5", "#C7E9C0", "#74C476", "#238B45", "#00441B"]; GREYS = ["#FFFFFF", "#D9D9D9", "#969696", "#525252", "#000000"]; ORANGES = ["#FFF5EB", "#FDD0A2", "#FD8D3C", "#D94801", "#7F2704"]
RF = {}
for key, name, colours, dec, unit in (("R", "R factor, MJ mm/(ha h yr)", BLUES, 0, ""), ("K", "K factor, t ha h/(ha MJ mm)", BROWNS, 3, ""),
                                       ("LS", "LS factor", PURPLES, 0, ""), ("C", "C factor", GREENS, 3, ""),
                                       ("P", "P factor", GREYS, 2, ""), ("SoilLoss", "Soil loss, t/ha/yr", ORANGES, 0, "")):
    st = RS[key]; lo, hi = (st["p2"], st["p98"]) if key != "P" else (0.5, 1.0)
    RF[key] = ramp_raster(os.path.join(DATA, f"{key}_catchments.tif"), name, lo, hi, colours, dec, unit)
# sediment yield choropleth on the catchments
cy = vec(os.path.join(DATA, "dam_catchments_results.gpkg"), "Sediment yield, m³/km²/yr", "catchments")
rngs = [(0, 50, "under 50", "#FEE8C8"), (50, 70, "50 to 70", "#FDBB84"), (70, 85, "70 to 85", "#E34A33"), (85, 200, "over 85", "#7F0000")]
cy.setRenderer(QgsGraduatedSymbolRenderer("yield_m3km2", [QgsRendererRange(lo, hi, QgsFillSymbol.createSimple({"color": c, "outline_color": "#7F0000", "outline_width": "0.35", "outline_width_unit": "MM"}), lab) for lo, hi, lab, c in rngs]))
cy.renderer().setUsingSymbolLevels(False)
label(cy, '"name" || \'\\n\' || format_number("yield_m3km2", 0) || \' m³/km²/yr\' || \'\\n\' || format_number("loss50_pct", 1) || \' % in 50 yr\'', 7.0, "#1F1F1F", True, 0.9, expression=True)

# ------------------------------------------------------------------ figures
def rect(b, scale):
    r = QgsRectangle(b[0], b[1], b[2], b[3]); r.scale(scale); return r
E_ALL = rect(ext["all"], 1.10); E_CAT = rect(ext["catchments"], 1.12)
def dam_rows(fmt, field):
    return [(d, fmt(float(cat.getFeature(fid)[field]))) for d, fid in [(f["name"], f.id()) for f in cat.getFeatures()] if d in DAMS]
def per_dam(field, fmt=lambda v: f"{v:,.0f}"):
    vals = {f["name"]: float(f[field]) for f in cat.getFeatures()}; return [(d, fmt(vals[d])) for d in DAMS]
FIGS = {
 "M01_dams": ("The eight dams of Block 04 and their catchments", [cat, axes, res, ch, wall], E_ALL, True,
              [("Dams", "8"), ("Catchments", f"{sum(float(f['area_km2']) for f in cat.getFeatures()):,.0f} km²"), ("Reservoir capacity", f"{sum(float(f['capacity_Mm3']) for f in cat.getFeatures()):,.0f} Mm³ at FSL"), ("Channel alignments", "CH, WALL layers")],
              per_dam("area_km2", lambda v: f"{v:,.0f} km²"), "Catchment area"),
 "M02_R": ("Rainfall erosivity, the R factor of RUSLE", [cat, RF["R"]], E_CAT, False, [("Source", "SM2RAIN 1 km climatology"), ("Formula", "Renard et al. 1997"), ("Range (2–98 %)", f"{RS['R']['p2']:.0f} – {RS['R']['p98']:.0f}"), ("Mean", f"{RS['R']['mean']:.0f}")], per_dam("R", lambda v: f"{v:.1f}"), "Catchment mean R"),
 "M03_K": ("Soil erodibility, the K factor (SoilGrids texture)", [cat, RF["K"]], E_CAT, False, [("Source", "ISRIC SoilGrids 0–5 cm"), ("Formula", "Williams 1995"), ("Range (2–98 %)", f"{RS['K']['p2']:.3f} – {RS['K']['p98']:.3f}"), ("Mean", f"{RS['K']['mean']:.3f}")], per_dam("K", lambda v: f"{v:.3f}"), "Catchment mean K"),
 "M04_LS": ("Slope length and steepness, the LS factor", [cat, RF["LS"]], E_CAT, False, [("Source", "Copernicus GLO-30, D8 flow accumulation"), ("Formula", "Moore & Burch 1986"), ("Range (2–98 %)", f"{RS['LS']['p2']:.0f} – {RS['LS']['p98']:.0f}"), ("Mean", f"{RS['LS']['mean']:.1f}")], per_dam("LS", lambda v: f"{v:.1f}"), "Catchment mean LS"),
 "M05_C": ("Cover management, the C factor (Landsat 8 NDVI)", [cat, RF["C"]], E_CAT, False, [("Source", "Landsat 8, 2017 mosaic, NDVI"), ("Formula", "Durigon et al. 2014"), ("Range (2–98 %)", f"{RS['C']['p2']:.3f} – {RS['C']['p98']:.3f}"), ("Mean", f"{RS['C']['mean']:.3f}")], per_dam("C", lambda v: f"{v:.4f}"), "Catchment mean C"),
 "M06_P": ("Support practice, the P factor (ESA WorldCover)", [cat, RF["P"]], E_CAT, False, [("Source", "ESA WorldCover 2020"), ("Rule", "cropland and vegetation below 1"), ("Range", f"{RS['P']['min']:.2f} – {RS['P']['max']:.2f}"), ("Mean", f"{RS['P']['mean']:.3f}")], per_dam("P", lambda v: f"{v:.3f}"), "Catchment mean P"),
 "M07_soilloss": ("Annual soil loss A = R K LS C P", [cat, RF["SoilLoss"]], E_CAT, False, [("Unit", "t ha⁻¹ yr⁻¹, 250 m cells"), ("Range (2–98 %)", f"{RS['SoilLoss']['p2']:.0f} – {RS['SoilLoss']['p98']:.0f}"), ("Mean", f"{RS['SoilLoss']['mean']:.1f}"), ("Sediment delivery", "Williams 1977 SDR")], per_dam("soil_loss", lambda v: f"{v:.1f} t/ha/yr"), "Catchment mean soil loss"),
 "M08_yield": ("Sediment yield per dam and the storage lost in 50 years", [cy, axes], E_CAT, True, [("Yield", "RUSLE × Williams SDR, 1.5 t/m³"), ("Range", "40 – 98 m³/km²/yr"), ("Storage lost, 50 yr", "1 – 16 % of capacity"), ("Method", "USBR 2.6, operation 3")], per_dam("loss50_pct", lambda v: f"{v:.1f} % (50 yr)"), "Storage lost at FSL"),
 "M09_hms": ("The HEC-HMS model: subbasins, reaches, junctions and reservoirs", [sub, rch, pts, cat], E_ALL, True, [("Subbasins", str(sub.featureCount())), ("Reaches", str(rch.featureCount())), ("Junctions and outfalls", str(sum(1 for f in pts.getFeatures() if f['type'] in ('Junction', 'Outfall', 'Dam junction')))), ("Reservoirs", "8")], per_dam("q200_out", lambda v: f"{v:,.0f} m³/s"), "200-yr routed outflow"),
}
def load_template():
    lay = QgsPrintLayout(proj); doc = QDomDocument(); doc.setContent(open(TEMPLATE_XML, encoding="utf-8").read()); lay.loadFromTemplate(doc, QgsReadWriteContext(), True); return lay

def build(keys=None, dpi=200):
    made = []; mgr = proj.layoutManager()
    for n, (key, (title, stack, extent, with_sat, table_rows, box_rows, box_title)) in enumerate(FIGS.items(), 1):
        if keys and key not in keys: continue
        lay = load_template(); lay.setName(key)
        layers = list(stack) + [hs] + ([sat] if (sat is not None and with_sat) else [])
        m = [i for i in lay.items() if isinstance(i, QgsLayoutItemMap)][0]; m.setCrs(UTM); m.setLayers(layers); m.setKeepLayerSet(True); m.zoomToExtent(extent); m.setBackgroundColor(QColor("#FFFFFF"))
        for it in lay.items():
            if isinstance(it, QgsLayoutItemLabel):
                t = it.text()
                if t.startswith("Ibri Sewer"): it.setText(SUBTITLE); it.attemptResize(QgsLayoutSize(260, 4.5, MM))
                elif t.startswith("Satellite image"): it.setText(CREDIT); it.attemptResize(QgsLayoutSize(110, 3.5, MM))
                elif t and not t.startswith("N"):
                    it.setText(title); it.attemptResize(QgsLayoutSize(185, 6.5, MM)); tf = it.textFormat(); tf.setSize(13); it.setTextFormat(tf)
            elif isinstance(it, QgsLayoutItemScaleBar): it.setLinkedMap(m)
            elif isinstance(it, QgsLayoutItemLegend):
                it.setLinkedMap(m); it.setAutoUpdateModel(False); grp = it.model().rootGroup()
                for c in list(grp.children()): grp.removeChildNode(c)
                for l in stack:
                    node = grp.addLayer(l)
                    r = getattr(l, "renderer", lambda: None)()
                    if r is not None and r.type() in ("categorizedSymbol", "graduatedSymbol"): node.setCustomProperty("legend/title-style", "visible")
                    if isinstance(l, QgsRasterLayer):
                        it.model().refreshLayerLegend(node); kids = it.model().layerLegendNodes(node); keep = [i for i, k in enumerate(kids) if type(k).__name__ != "QgsSimpleLegendNode"]
                        if keep and len(keep) < len(kids): QgsMapLayerLegendUtils.setLegendNodeOrder(node, keep); it.model().refreshLayerLegend(node)
                it.setTitle(""); it.setBackgroundEnabled(True); it.setBackgroundColor(QColor(255, 255, 255, 235)); it.setResizeToContents(True); it.adjustBoxSize()
                for sty in (QgsLegendStyle.Subgroup, QgsLegendStyle.SymbolLabel):
                    f = QFont("Arial"); f.setPointSizeF(6.5 if sty == QgsLegendStyle.SymbolLabel else 7.0); f.setBold(sty == QgsLegendStyle.Subgroup); it.rstyle(sty).setFont(f)
                it.setWrapString(""); it.adjustBoxSize(); it.attemptMove(QgsLayoutPoint(11.0, min(163.0, 202.0 - it.sizeWithUnits().height()), MM))
            elif isinstance(it, QgsLayoutFrame):
                mf = it.multiFrame()
                if isinstance(mf, QgsLayoutItemManualTable):
                    mf.setTableContents([[QgsTableCell(a), QgsTableCell(b)] for a, b in table_rows]); mf.setGridStrokeWidth(0.15); mf.setGridColor(QColor("#9DA9B8"))
                    tfc = mf.contentTextFormat(); tfc.setSize(7.5); tfc.setFont(QFont("Arial")); tfc.setColor(QColor("#1F3B63")); mf.setContentTextFormat(tfc)
                    it.attemptResize(QgsLayoutSize(74.5, 4.3 * len(table_rows) + 1.5, MM)); it.attemptMove(QgsLayoutPoint(214.3, 202.0 - (4.3 * len(table_rows) + 1.5), MM))
                elif isinstance(mf, QgsLayoutItemHtml):
                    rows = "".join(f"<tr><td style='padding:1px 4px'>{a}</td><td align='right' style='padding:1px 4px'>{b}</td></tr>" for a, b in box_rows)
                    mf.setContentMode(QgsLayoutItemHtml.ManualHtml)
                    mf.setHtml(f"<html><body style='margin:0;font-family:Arial;font-size:7pt;color:#1F3B63'><div style='background:#FFFFFF;border:0.3px solid #1F3B63;padding:3px'><b>{box_title}</b><table style='font-size:7pt;border-collapse:collapse;margin-top:2px'>{rows}</table></div></body></html>")
                    mf.loadHtml(); hbox = 7 + 3.9 * len(box_rows); it.attemptResize(QgsLayoutSize(62.0, hbox, MM)); it.attemptMove(QgsLayoutPoint(226.8, 202.0 - (4.3 * len(table_rows) + 1.5) - 2.0 - hbox, MM))
        old = mgr.layoutByName(key)
        if old: mgr.removeLayout(old)
        mgr.addLayout(lay)
        path = os.path.join(PNG, f"{key}.png"); exp = QgsLayoutExporter(lay); st = QgsLayoutExporter.ImageExportSettings(); st.dpi = dpi
        rc = exp.exportToImage(path, st); made.append((key, rc == QgsLayoutExporter.Success)); print(key, "ok" if rc == QgsLayoutExporter.Success else f"FAILED {rc}")
    for l in (cat, axes, res, ch, wall, sub, rch, pts, dpts, cy, hs) + tuple(RF.values()) + ((sat,) if sat else ()):
        if proj.layerTreeRoot().findLayer(l.id()) is None: proj.layerTreeRoot().addLayer(l)
    proj.write(os.path.join(W3, "maps", "Block04_W3_maps.qgz")); return made

if __name__ == "__main__":
    keys = [a for a in sys.argv[1:] if a in FIGS] or None
    print(build(keys)); app.exitQgis()
