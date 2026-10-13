"""Standalone PyQGIS: load one Ibri W17 layout from its XML and list the items by class, position, size and content.
run:  "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" qgis_inspect_template.py
"""
import os, sys
from qgis.core import QgsApplication, QgsProject, QgsPrintLayout, QgsReadWriteContext, QgsLayoutItemLabel, QgsLayoutItemMap, QgsLayoutItemLegend, QgsLayoutItemScaleBar, QgsLayoutItemPicture, QgsLayoutItemShape, QgsLayoutFrame, QgsLayoutItemTextTable, QgsLayoutItemManualTable, QgsLayoutItemHtml
from qgis.PyQt.QtXml import QDomDocument
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", r"C:\Program Files\QGIS 3.44.8\apps\qgis-ltr"), True)
app = QgsApplication([], False); app.initQgis()
HERE = os.path.dirname(os.path.abspath(__file__)); xml_path = os.path.join(HERE, "..", "maps", "template", "ibri_W17_S1_zones_layout.xml")
proj = QgsProject.instance(); lay = QgsPrintLayout(proj); doc = QDomDocument(); doc.setContent(open(xml_path, encoding="utf-8").read())
ok = lay.loadFromTemplate(doc, QgsReadWriteContext()); print("loaded:", bool(ok), "| items:", len(lay.items()))
for it in lay.items():
    cls = type(it).__name__
    if cls in ("QgsLayoutItemPage",): continue
    try:
        pos = it.positionWithUnits(); size = it.sizeWithUnits(); info = f"{cls:24s} pos=({pos.x():.1f},{pos.y():.1f}) size=({size.width():.1f}x{size.height():.1f}) z={it.zValue():.0f} id={it.id()!r}"
    except Exception as e:
        info = f"{cls} ?"
    if isinstance(it, QgsLayoutItemLabel): info += f" text={it.text()[:90]!r} font={it.textFormat().font().family()} {it.textFormat().size()}pt"
    if isinstance(it, QgsLayoutItemPicture): info += f" picture={it.picturePath()!r}"
    if isinstance(it, QgsLayoutItemLegend): info += f" title={it.title()!r} cols={it.columnCount()} symbolW={it.symbolWidth()} symbolH={it.symbolHeight()} bg={it.backgroundColor().name()} frame={it.frameEnabled()}"
    if isinstance(it, QgsLayoutItemMap): info += f" map crs={it.crs().authid()} extent={it.extent().toString(0)} frame={it.frameEnabled()} grids={it.grids().size() if hasattr(it.grids(),'size') else '?'}"
    if isinstance(it, QgsLayoutItemScaleBar): info += f" scalebar style={it.style()} units={it.unitLabel()!r} segments={it.numberOfSegments()} width={it.unitsPerSegment()}"
    if isinstance(it, QgsLayoutFrame):
        mf = it.multiFrame(); info += f" frame of {type(mf).__name__}"
        if isinstance(mf, QgsLayoutItemManualTable): info += f" manual table {mf.tableContents() if hasattr(mf,'tableContents') else ''}"[:300]
        if isinstance(mf, QgsLayoutItemHtml): info += f" html={mf.html()[:200]!r}"
        if isinstance(mf, QgsLayoutItemTextTable): info += " text table"
    if isinstance(it, QgsLayoutItemShape): info += f" shape={it.shapeType()} fill={it.symbol().color().name() if it.symbol() else None}"
    print(info)
app.exitQgis()
