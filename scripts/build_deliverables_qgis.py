"""Build the root QGIS project of the latest deliverables snapshot:  <snapshot>/Block04_Deliverables.qgz

One project, next to the snapshot's README, with every relevant layer of the folder in groups and subgroups, every map
layout of the report saved inside it, and every path relative and INSIDE the snapshot (the only online layer is the
Google satellite background). Run with QGIS's Python after the sync:

    "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" build_deliverables_qgis.py

Method: the map project written by W3/scripts/26_maps_qgis_r2.py (all layouts, layers styled for the figures) is loaded;
its layers are arranged into the groups below, the other relevant files of the snapshot are added as layers, the
project is saved into the snapshot with relative paths, and then every data source in the saved XML is re-pointed to
the snapshot's copy of that file through MANIFEST.csv (source path -> copy). The result is reopened and verified: every
layer valid, every layout present, no path outside the snapshot.
"""
import os, sys, re, csv, zipfile, shutil, io
from pathlib import Path
import xml.etree.ElementTree as ET
from qgis.core import (QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsSingleSymbolRenderer, QgsFillSymbol, QgsLineSymbol, QgsMarkerSymbol, QgsCoordinateReferenceSystem, QgsDataProvider, QgsLayoutItemLegend, QgsLayoutExporter)
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", r"C:\Program Files\QGIS 3.44.8\apps\qgis-ltr"), True)
app = QgsApplication([], False); app.initQgis()
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import sync_deliverables as SD

SNAP = SD.latest_version(create=False); assert SNAP, "no snapshot: run sync_deliverables.py first"
SD.set_dest(SNAP); MAN = SD.load_manifest(); OUT = SNAP / SD.PROJECT_FILE
MAPS_QGZ = SD.W3 / "maps" / "Block04_R2_maps.qgz"
def norm(p): return os.path.normcase(os.path.normpath(os.path.abspath(str(p))))
SRC2DEST = {norm(r["source"]): r["dest"] for r in MAN.values() if r["kind"] != "pointer"}
def copy_of(path):
    """snapshot copy (relative posix) of a source-of-record file, or None"""
    return SRC2DEST.get(norm(path))
def in_snapshot(path):
    try: return Path(path).resolve().relative_to(SNAP.resolve()).as_posix()
    except ValueError: return None

# ---------------------------------------------------------------- 1. the map project with its layouts and styled layers
proj = QgsProject.instance(); ok = proj.read(str(MAPS_QGZ)); assert ok, MAPS_QGZ
layouts = [l.name() for l in proj.layoutManager().layouts()]; print("layouts in the map project:", layouts)
root = proj.layerTreeRoot(); layers = list(proj.mapLayers().values()); print("layers:", len(layers))

def role(l):
    """tell the figure layers apart: (name, renderer type, key colour / size, labels)"""
    n = l.name(); r = l.renderer() if hasattr(l, "renderer") else None
    if isinstance(l, QgsVectorLayer):
        rt = r.type() if r else ""; sym = r.symbol() if (r and rt == "singleSymbol") else None
        col = sym.symbolLayers()[0].properties().get("outline_color", sym.color().name()) if sym else ""; size = sym.symbolLayers()[0].properties().get("size", "") if sym else ""
        col = str(col)
        if not col.startswith("#") and col.count(",") >= 2:                       # QGIS 3.44 stores "r,g,b,a,rgb:…": compare as hex
            try: r_, g_, b_ = [int(float(v)) for v in col.split(",")[:3]]; col = f"#{r_:02X}{g_:02X}{b_:02X}"
            except ValueError: pass
        return n, rt, col.upper(), str(size), l.labelsEnabled()
    return n, "raster", "", "", False
def is_(l, name, rt=None, col=None, size=None, labels=None):
    n, t, c, s_, lab = role(l)
    return n == name and (rt is None or t == rt) and (col is None or c.startswith(col.upper()) or c == col) and (size is None or s_ == size) and (labels is None or lab == labels)

# the arrangement: group -> [(node label, matcher)] ; subgroups as nested dicts
NAMES = {}      # layer id -> node label (the layer itself keeps its name, so the layout legends do not change)
def pick(label, **kw):
    for l in layers:
        if l.id() not in NAMES and is_(l, **kw): NAMES[l.id()] = label; return l
    print("   not found:", label, kw); return None
TREE = [
 ("Background", [
    pick("Terrain hillshade (10 m terrain, 50 %)", name="Terrain hillshade"),
    pick("Terrain hillshade (dimmed)", name="Terrain hillshade (dimmed)"),
    pick("Google satellite (online)", name="Google satellite")]),
 ("Dams", [
    pick("Dam axis", name="Dam axis"), pick("Dam dyke", name="Dam dyke"),
    pick("Reservoir at full supply level", name="Reservoir at full supply level"), pick("Reservoir at crest level", name="Reservoir at crest level"),
    pick("Dam catchment (outline)", name="Dam catchment", col="#1F1F1F")]),
 ("Channels and dykes", [
    pick("Channels and dykes (categories, Block 4)", name="Channels and dykes", rt="categorizedSymbol", labels=False),
    pick("Channels and dykes (named)", name="Channels and dykes", rt="categorizedSymbol", labels=True),
    pick("Channels and dykes (one colour)", name="Channels and dykes", rt="RuleRenderer"),
    ("Roads and utilities", [pick("Batinah Expressway", name="Batinah Expressway"), pick("Batinah Highway", name="Batinah Highway"), pick("Batinah Coastal Road", name="Batinah Coastal Road"),
                            pick("North Batinah Bypass (planned)", name="North Batinah Bypass (planned)"), pick("OQ pipelines", name="OQ pipelines"), pick("OQ pipelines (south)", name="OQ pipelines (south)"), pick("Existing culvert / bridge", name="Existing culvert / bridge")]),
    ("Constraints", [pick("Land use (MoHUP cadastre)", name="Land use"), pick("Flood depth 200-year (m), without the scheme", name="Flood depth 200-year (m)")])]),
 ("HEC-HMS model", [
    pick("HEC-HMS model view (georeferenced screenshot)", name="HEC-HMS model view"),
    ("Basin 3 (channels with the eight reservoirs)", [pick("Subbasins", name="HEC-HMS subbasin"), pick("Reaches", name="HEC-HMS reach"), pick("Junctions and outfalls: 200-year peak flow", name="Junction: 200-year peak flow (m³/s)", size="1.9")])]),
 ("Sediment", [
    pick("R factor, MJ mm/(ha h yr)", name="R factor, MJ mm/(ha h yr)"), pick("K factor, t ha h/(ha MJ mm)", name="K factor, t ha h/(ha MJ mm)"), pick("LS factor", name="LS factor"), pick("C factor", name="C factor"), pick("Soil loss, t/ha/yr", name="Soil loss, t/ha/yr"),
    pick("Sediment yield, m³/km²/yr (per dam)", name="Sediment yield, m³/km²/yr"), pick("Sediment delivered in 50 years, Mcm (per dam)", name="Sediment delivered in 50 years, Mcm")]),
 ("Map figure layers (duplicates the layouts use)", [
    pick("Dam catchment (yellow outline, figures)", name="Dam catchment", col="#FFD966"),
    pick("Dam names (label layer)", name="_Dam names"), pick("Dam names, small (label layer)", name="_Dam names (small)"),
    pick("Junctions: 200-year peak flow (zoomed figure)", name="Junction: 200-year peak flow (m³/s)", size="2.1")]),
]
left = [l for l in layers if l.id() not in NAMES]
if left: print("   layers not placed (appended to 'Map figure layers'):", [l.name() for l in left]); TREE[-1][1].extend(left)

# ---------------------------------------------------------------- 2. the other relevant files of the snapshot, added as layers
def shp(rel, name, style=None): return (rel, name, "ogr", style)
def gpkg(rel, layer, name, style=None): return (f"{rel}|layername={layer}", name, "ogr", style)
def tif(rel, name, style=None): return (rel, name, "gdal", style)
S = lambda rel: str(SNAP / rel)
EL = "04 Channel network elements/tables, shapefiles, KMZ (Basin 3 with dams, Basin 2 without)/shp"
HS = "08 GIS layers/Hydrology SHP"; CI = "08 GIS layers/Claude inputs (channels and walls for HMS, dams, global catchments, review screenshots)"; CG = "08 GIS layers/Claude gis (Basin 2 review, reconditioned terrain, red lines, result overlays)"
HM = "02 HMS model/HEC_HMS_Block_04 (project files, terrain, gis)"; MD = "07 Maps/figures and QGIS projects/data"; SR = "05 Sediment/catchments, yield, reservoir sedimentation"; RL = "10 References/Shared layers (W server)"
NEW = [
 ("Dams", None, [gpkg(f"{MD}/dam_catchments_results.gpkg", "catchments", "Dam catchments with results (area, CN, yield, loss, Q200)"), shp(f"{SR}/catchments/Dam_catchments9.shp", "Dam catchments (nine, physiography)"),
                 gpkg(f"{MD}/dams.gpkg", "dam_points", "Dam points (FSL, crest, capacity)"), shp(f"{RL}/GCA RENN.shp", "Global catchments (HAW, SHA, SAR, SAK)")]),
 ("HEC-HMS model", "Basin 3 (channels with the eight reservoirs)", [shp(f"{EL}/B3/Points_B3.shp", "Points (all, Q and V for 13 return periods)")]),
 ("HEC-HMS model", "Basin 2 (channels without reservoirs)", [shp(f"{EL}/B2/Subbasins_B2.shp", "Subbasins"), shp(f"{EL}/B2/Reaches_B2.shp", "Reaches"), shp(f"{EL}/B2/Points_B2.shp", "Points (Q and V for 13 return periods)")]),
 ("HEC-HMS model", "Basin 2 delineation review", [("ALL", f"{CG}/Basin_2_review.gpkg", "Review: ", "ogr", None), gpkg(f"{CG}/red_lines.gpkg", None, "Engineer's red lines"), gpkg(f"{CG}/merge_regions.gpkg", None, "Merge regions")]),
 ("HEC-HMS model", "HMS exports (Hydrology SHP)", [("ALL", f"{HS}/HMS Output/**/*.shp", "HMS Output: ", "ogr", None), ("ALL", f"{HS}/from HMS/**/*.shp", "from HMS: ", "ogr", None)]),
 ("HEC-HMS model", "Model inputs", [shp(f"{CI}/CH.shp", "Channels burnt into the terrain (CH)"), shp(f"{CI}/WALL.shp", "Walls raised on the terrain (WALL)"), shp(f"{HS}/for HMS/1/Burn.shp", "Burn lines (HMS)"), shp(f"{HS}/for HMS/1/Wall.shp", "Wall lines (HMS)"),
                                    shp(f"{HS}/Gage stations/*.shp", "Gauge stations"), shp(f"{HS}/Streams NSA 5m Batinah/*.shp", "Streams (NSA 5 m terrain)"),
                                    tif(f"{HM}/Hydrology Data/CN_Include_Hill_Area.tif", "Curve number grid"), tif(f"{HM}/terrain/NSA_5m_B04_Res10m/00/elevation.tif", "HMS terrain, 10 m"), tif(f"{CG}/reconditioned_CH_WALL_10m.tif", "Reconditioned terrain (channels burnt, walls raised)")]),
 ("Sediment", "RUSLE rasters (full extent)", [tif(f"{SR}/rusle/Output/Rasters/{k}.tif", f"{k} (full extent)") for k in ("R", "K", "LS", "C", "P", "SoilLoss")]),
]
def resolve(rel):
    """a path pattern inside the snapshot -> the first match (shapefile folders are listed, not guessed)"""
    base, _, opt = rel.partition("|"); p = SNAP / base
    if "*" in base:
        import glob; hits = sorted(glob.glob(str(SNAP / base)))
        if not hits: return None
        p = Path(hits[0])
    return (str(p) + ("|" + opt if opt else "")) if p.exists() else None
def add_new(group_name, sub_name, items):
    g = root.findGroup(group_name) or root.addGroup(group_name)
    tgt = g if sub_name is None else (g.findGroup(sub_name) or g.addGroup(sub_name))
    expanded = []
    for it in items:
        if it[0] == "ALL":                                    # every sublayer of a GeoPackage, or every shapefile of a folder
            _, rel, prefix, prov, style = it
            if "*" in rel:
                import glob
                for f in sorted(glob.glob(str(SNAP / rel), recursive=True)): expanded.append((str(Path(f).relative_to(SNAP).as_posix()), prefix + Path(f).stem, prov, style))
            else:
                probe = QgsVectorLayer(str(SNAP / rel), "probe", "ogr")
                for sl in probe.dataProvider().subLayers():
                    lname = sl.split(QgsDataProvider.sublayerSeparator())[1] if hasattr(QgsDataProvider, "sublayerSeparator") else sl.split("!!::!!")[1]
                    expanded.append((f"{rel}|layername={lname}", prefix + lname, prov, style))
        else: expanded.append(it)
    for rel, name, prov, style in expanded:
        src = resolve(rel)
        if src is None: print("   missing in the snapshot:", rel); continue
        if prov == "ogr" and "|layername=None" in src: src = src.replace("|layername=None", "")
        l = QgsVectorLayer(src, name, "ogr") if prov == "ogr" else QgsRasterLayer(src, name)
        if not l.isValid(): print("   invalid:", rel); continue
        if prov == "ogr" and l.geometryType() in (1,): l.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple({"color": "#1F3B63", "width": "0.35", "width_unit": "MM"})))
        if prov == "ogr" and l.geometryType() in (2,): l.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": "#7F7F7F", "outline_width": "0.3", "outline_width_unit": "MM"})))
        proj.addMapLayer(l, False); node = tgt.addLayer(l); node.setItemVisibilityChecked(False)

# ---------------------------------------------------------------- 3. arrange the tree
ORIG = {}
for l in layers:
    label = NAMES.get(l.id())
    if label and label != l.name(): ORIG[l.id()] = l.name(); l.setName(label)      # the project shows the role; the legends keep the figure wording (below)
for lay in proj.layoutManager().layouts():
    for it in lay.items():
        if isinstance(it, QgsLayoutItemLegend):
            for node in it.model().rootGroup().findLayers():
                lid = node.layerId()
                if lid in ORIG: node.setCustomProperty("legend/title-label", ORIG[lid])
            it.refresh()
for n in list(root.children()): root.removeChildNode(n)          # the map script appended every layer flat; rebuild
ON = {"Terrain hillshade (10 m terrain, 50 %)", "Google satellite (online)", "Dam axis", "Reservoir at full supply level", "Reservoir at crest level", "Dam catchment (outline)", "Channels and dykes (categories, Block 4)"}
def place(parent, items):
    for it in items:
        if it is None: continue
        if isinstance(it, tuple): sub = parent.addGroup(it[0]); place(sub, it[1]); sub.setExpanded(False); continue
        node = parent.addLayer(it); node.setItemVisibilityChecked(it.name() in ON)
for gname, items in TREE:
    g = root.addGroup(gname); place(g, items); g.setExpanded(gname in ("Dams", "Channels and dykes"))
for gname, sub, items in NEW: add_new(gname, sub, items)
# order: Background last (bottom of the drawing order)
bg = root.findGroup("Background"); clone = bg.clone(); root.insertChildNode(-1, clone); root.removeChildNode(bg)
proj.setCrs(QgsCoordinateReferenceSystem("EPSG:32640")); proj.setTitle("Block 04 deliverables: dams, channels, HEC-HMS model, sediment, maps")
proj.writeEntry("Paths", "/Absolute", False)
ok = proj.write(str(OUT)); assert ok, OUT; print("saved", OUT)

# ---------------------------------------------------------------- 4. re-point every data source to the snapshot copy (through the manifest), relative
def fix_source(src):
    if not src or "type=xyz" in src or src.startswith(("http", "crs=", "url=")): return src, None
    path, _, opt = src.partition("|")
    ap = path if os.path.isabs(path) else os.path.normpath(os.path.join(str(SNAP), path))
    rel = in_snapshot(ap)
    if rel is None: rel = copy_of(ap)
    if rel is None: return src, ap
    return "./" + rel + ("|" + opt if opt else ""), None
qgz = zipfile.ZipFile(OUT); names = qgz.namelist(); qgs_name = [n for n in names if n.endswith(".qgs")][0]; members = {n: qgz.read(n) for n in names}; qgz.close()
tree = ET.fromstring(members[qgs_name].decode("utf-8")); outside = []; fixed = 0
for ds in tree.iter("datasource"):
    new, bad = fix_source(ds.text or "")
    if bad: outside.append(bad)
    elif new != (ds.text or ""): ds.text = new; fixed += 1
for lt in tree.iter("layer-tree-layer"):
    new, bad = fix_source(lt.get("source", ""))
    if new != lt.get("source", ""): lt.set("source", new)
members[qgs_name] = ET.tostring(tree, encoding="utf-8", xml_declaration=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for n, b in members.items(): z.writestr(n, b)
print(f"re-pointed {fixed} data sources;", ("ALL INSIDE the snapshot" if not outside else f"{len(outside)} OUTSIDE: " + "; ".join(sorted(set(outside))[:8])))

# ---------------------------------------------------------------- 5. verify by reopening
p2 = QgsProject(); assert p2.read(str(OUT)); bad = [l.name() for l in p2.mapLayers().values() if not l.isValid()]
print("reopened:", len(p2.mapLayers()), "layers,", len(bad), "invalid", bad[:10]); print("layouts:", [l.name() for l in p2.layoutManager().layouts()])
abs_left = [ds.text for ds in tree.iter("datasource") if ds.text and re.match(r"^[A-Za-z]:[\\/]|^\\\\", ds.text)]
print("absolute paths left in the project:", len(abs_left), abs_left[:5])
def show(node, depth=0):
    for c in node.children():
        print("   " * depth + ("[" + c.name() + "]" if isinstance(c, QgsLayerTreeGroup) else ("x " if c.itemVisibilityChecked() else "  ") + c.name()))
        if isinstance(c, QgsLayerTreeGroup): show(c, depth + 1)
show(p2.layerTreeRoot())
if "--export-check" in sys.argv:
    outdir = Path(os.environ.get("CHECK_DIR", str(SNAP))); outdir.mkdir(exist_ok=True)
    for name in ("M01_dams", "M10_q200", "M05_roads_utilities"):
        lay = p2.layoutManager().layoutByName(name); st = QgsLayoutExporter.ImageExportSettings(); st.dpi = 110
        rc = QgsLayoutExporter(lay).exportToImage(str(outdir / f"check_{name}.png"), st); print("export check", name, "ok" if rc == QgsLayoutExporter.Success else rc)
sys.exit(1 if (bad or outside or abs_left or len(p2.layoutManager().layouts()) < 10) else 0)
