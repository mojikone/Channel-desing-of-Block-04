"""Step 90 (W9, engineer 2026-10-14) - the submission folder updated in place: reports R7 and stormwater R2, the GIS products of W9
(reach sizes for all return periods, extents per return period, dyke extent, the culverts with the bypass, his point and reach
styles), the second-generation KMZ files with the HEC-HMS model, the tables (dam hydrographs, dams and reservoirs, BOQ and cost
estimate, the culvert tables), the maps of both reports, the channel terrain on the 0.5 m ground, and the bypass road design
package (09). Client-facing names only. Copies are skipped when the target has the same size and date; files that changed are
replaced. Run after 73, 71, 80, 82, 84, 85, 87 and the report builds; step 91 then rebuilds the QGIS project.
    python 90_submission.py [--dry] [--out "<folder>"]"""
import os, sys, shutil, re, glob, json, time
import pandas as pd, geopandas as gpd
HERE = os.path.dirname(os.path.abspath(__file__)); W9 = os.path.dirname(HERE); CB = os.path.dirname(W9); B4 = os.path.dirname(CB); W9P = os.path.join(CB, "W9")
W3, W6, W7, W8 = (os.path.join(CB, w) for w in ("W3", "W6", "W7", "W8"))
W = "W:/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/06-WORKING/"
SHARE = r"C:\Users\mojtaba\Desktop\Win10 shared folder"
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
DRY = "--dry" in A
OUT = opt("--out", os.path.join(B4, "Deliverables", "2 Submission 13102026"))
SHEETS = os.path.join(W8, "sewergems", "sheets", "scripts")
log = []
def cp(src, dst, must=True):
    if not os.path.exists(src):
        msg = "MISSING " + src; print("  " + msg); log.append(msg)
        if must: raise SystemExit(msg)
        return
    if os.path.isdir(src):
        for root, _, files in os.walk(src):
            for f in files: cp(os.path.join(root, f), os.path.join(dst, os.path.relpath(os.path.join(root, f), src)))
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(src) and abs(os.path.getmtime(dst) - os.path.getmtime(src)) < 2: return
    if not DRY: shutil.copy2(src, dst)
    log.append("%s  <-  %s" % (os.path.relpath(dst, OUT), src))
def cp_shp(src_shp, dst_shp, must=True):
    base, _ = os.path.splitext(src_shp); dbase, _ = os.path.splitext(dst_shp)
    for ext in (".shp", ".shx", ".dbf", ".prj", ".cpg", ".qpj", ".sbn", ".sbx"):
        if os.path.exists(base + ext): cp(base + ext, dbase + ext, must=False)
    if must and not os.path.exists(src_shp): raise SystemExit("MISSING " + src_shp)
def cp_csv_drop(src, dst, drop):
    """Client copy of a CSV without the internal columns."""
    import pandas as pd
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    df = pd.read_csv(src, dtype=str, keep_default_na=False)
    df = df.drop(columns=[c for c in drop if c in df.columns])
    if not DRY: df.to_csv(dst, index=False)
    log.append(os.path.relpath(dst, OUT) + "  (written without %s)" % ", ".join(drop))
def cp_gpkg_drop(src, dst, drop):
    """Client copy of a GeoPackage, every layer, without the internal fields."""
    import geopandas as gpd, fiona
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst) and not DRY: os.remove(dst)
    for i, lyr in enumerate(fiona.listlayers(src)):
        g = gpd.read_file(src, layer=lyr)
        g = g.drop(columns=[c for c in drop if c in g.columns])
        if not DRY: g.to_file(dst, driver="GPKG", layer=lyr, mode=("w" if i == 0 else "a"))
    log.append(os.path.relpath(dst, OUT) + "  (written without %s)" % ", ".join(drop))
def to_shp(gdf, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if DRY: return
    g = gdf.copy()
    for c in g.columns:
        if c != "geometry" and g[c].dtype == object: g[c] = g[c].map(lambda v: str(v) if isinstance(v, (dict, list)) else v)
    g.to_file(dst, driver="ESRI Shapefile"); log.append(os.path.relpath(dst, OUT) + "  (written)")
def rm(path):
    if os.path.exists(path) and not DRY: os.remove(path); log.append("removed " + os.path.relpath(path, OUT))

# ------------------------------------------------------------------ 01 reports
R = os.path.join(OUT, "01 Reports")
cp(os.path.join(W9, "report", "R7", "Block04_Report_R7.pdf"), os.path.join(R, "Block 04 - Channels Feasibility and Hydrological Report.pdf"))
cp(os.path.join(W9, "report", "R7", "Block04_Report_R7.docx"), os.path.join(R, "Block 04 - Channels Feasibility and Hydrological Report.docx"))
cp(os.path.join(W9, "report", "SW_R2", "Block04_Stormwater_Channels_R2.pdf"), os.path.join(R, "Block 04 - Hydraulic Design of Stormwater Channels.pdf"))
cp(os.path.join(W9, "report", "SW_R2", "Block04_Stormwater_Channels_R2.docx"), os.path.join(R, "Block 04 - Hydraulic Design of Stormwater Channels.docx"))
# ------------------------------------------------------------------ 02 drawings (the sets of W8 stand)
DW = os.path.join(OUT, "02 Drawings")
cp(os.path.join(SHEETS, "PDF", "Set", "2224-PD-HY-PP-B4_Plan_and_Profile_Drawings_200yr_R9.pdf"), os.path.join(DW, "2224-PD-HY-PP-B4 - Plan and Profile Drawings of the Flood Protection Channels (200-year).pdf"))
cp(os.path.join(SHEETS, "PDF", "Set", "2224-PD-HY-PP-B4_Stormwater_Channels_Plan_and_Profile_Drawings_200yr_R9.pdf"), os.path.join(DW, "2224-PD-HY-PP-B4 - Plan and Profile Drawings of the Stormwater Channels (200-year).pdf"))
cp(os.path.join(W6, "civil3d", "Block04_Channels_W6.dwg"), os.path.join(DW, "Civil 3D", "Block 04 - Channels and Dykes.dwg"))
# ------------------------------------------------------------------ 03 GIS
G = os.path.join(OUT, "03 GIS")
chs = os.path.join(B4, "Hydrology", "SHP", "temp", "Channels and Dykes 04102026.shp")
g = gpd.read_file(chs); g = g[g["Block"] == 4]; to_shp(g, os.path.join(G, "Channels and dykes", "Channels and dykes.shp"))
cp(os.path.join(W3, "maps", "styles", "channels_dykes.qml"), os.path.join(G, "Channels and dykes", "Channels and dykes.qml"))
cp_shp(os.path.join(SHEETS, "Data", "SHP", "Buffers", "Channel Bed Buffer.shp"), os.path.join(G, "Channel extents", "Channel bed (designed, 200-year).shp"))
cp_shp(os.path.join(SHEETS, "Data", "SHP", "Buffers", "Channels Buffer.shp"), os.path.join(G, "Channel extents", "Channel corridor (bed, embankments and access roads).shp"))
cp_shp(os.path.join(W9, "gis", "dyke_extent.shp"), os.path.join(G, "Channel extents", "Dyke extent (15.5 m each side).shp"))
for k in ("2", "5", "10", "25", "50", "100", "200", "500"):
    cp_shp(os.path.join(W9, "gis", "extents", f"extent_{k}yr.shp"), os.path.join(G, "Channel extents", "By return period", f"Channel extent {k}-year (bed and corridor).shp"))
cp_shp(os.path.join(W6, "final", "Block4_design_points.shp"), os.path.join(G, "Design points and segments", "Design points.shp"))
cp_shp(os.path.join(W6, "final", "Block4_design_segments.shp"), os.path.join(G, "Design points and segments", "Design segments.shp"))
cp(os.path.join(W6, "final", "Block4_design_points.csv"), os.path.join(G, "Design points and segments", "Design points.csv"))
cp(os.path.join(W6, "final", "Block4_design_segments.csv"), os.path.join(G, "Design points and segments", "Design segments.csv"))
cp(os.path.join(W9, "gis", "qml", "design_points_his.qml"), os.path.join(G, "Design points and segments", "Design points.qml"))
cp(os.path.join(W8, "gis", "stations.gpkg"), os.path.join(G, "Stations", "Stations every 500 m and 1000 m.gpkg"))
H = os.path.join(G, "Hydraulic model (200-year design)")
cp(os.path.join(W8, "gis", "sewergems_200yr_R9.gpkg"), os.path.join(H, "Channel reaches, nodes, outfalls, bed and corridor.gpkg"))
cp(os.path.join(W9, "gis", "segments_all_rp.gpkg"), os.path.join(H, "Channel reaches - sizes for all return periods.gpkg")); cp_shp(os.path.join(W9, "gis", "segments_all_rp.shp"), os.path.join(H, "Channel reaches - sizes for all return periods.shp"))
cp(os.path.join(W9, "gis", "qml", "segments_his.qml"), os.path.join(H, "Channel reaches.qml"))
cp(os.path.join(W7, "gis", "outfalls_levels.gpkg"), os.path.join(H, "Outfalls - invert and existing level.gpkg"))
cp(os.path.join(W7, "dykes", "dykes.gpkg"), os.path.join(G, "Dykes", "Dykes - height and cost.gpkg"))
cp_gpkg_drop(os.path.join(W9, "culverts", "crossings.gpkg"), os.path.join(G, "Culverts", "Road crossings and proposed box culverts.gpkg"), ["extended", "start_short", "end_short_m", "start_short_m", "existing_dist_m", "note"])
ex = gpd.read_file(W + "04-Hydraulic/05 Small Tasks/18 Channel Design/Master Plan Map/Data for Master Plan/SHP/Culverts/Existing Culverts Batinah/Culverts_2_4.shp").to_crs(32640)
env = g.total_bounds; pad = 5000; ex = ex.cx[env[0] - pad: env[2] + pad, env[1] - pad: env[3] + pad]; to_shp(ex, os.path.join(G, "Culverts", "Existing culverts (inventory, Block 04 plain).shp"))
cp_shp(os.path.join(B4, "Hydrology", "SHP", "Block 4 Dams", "Dams updated.shp"), os.path.join(G, "Dams", "Dam axes.shp"))
cp_shp(W + "04-Hydraulic/05 Small Tasks/18 Channel Design/SHP/Block 04 Dams/Polygon_FSL.shp", os.path.join(G, "Dams", "Reservoirs at full supply level.shp"))
cp_shp(W + "04-Hydraulic/05 Small Tasks/18 Channel Design/SHP/Block 04 Dams/Ppygon_Crest_Level.shp", os.path.join(G, "Dams", "Reservoirs at crest level.shp"))
cp(os.path.join(W8, "gis", "GCA_RENN.gpkg"), os.path.join(G, "Catchments", "Global catchments.gpkg"))
for f, nm in (("Subbasins_B6.shp", "subbasins"), ("Subbasins_B6_dam.shp", "subbasins with dam flag"), ("Reaches_B6.shp", "reaches"), ("Points_B6.shp", "junctions and outfalls")):
    cp_shp(os.path.join(W7, "elements", "shp", "B6", f), os.path.join(G, "Catchments", "HEC-HMS " + nm + ".shp"), must=False)
cp_shp(W + "13-Study and Design/01-FS and PD/00-General/02-Land Use/ALL_MOH_CLEANED/LandUSE_block4.shp", os.path.join(G, "Land use", "Land use (cadastre).shp"))
for key, name in (("03-Hydrology/01 GIS DATA/SHP/Bathinah Highway CL.shp", "Batinah Highway.shp"), ("03-Hydrology/01 GIS DATA/SHP/Batinah Coastal RD CL.shp", "Batinah Coastal Road.shp"), ("03-Hydrology/01 GIS DATA/SHP/Muscat Expressway CL.shp", "Batinah Expressway.shp"),
                  ("04-Hydraulic/000 Correspond/02 Sent/2026.01.12 PDO pipeline/SHP/North/Pipelines.shp", "OQ pipelines (north).shp"), ("04-Hydraulic/000 Correspond/02 Sent/2026.01.12 PDO pipeline/SHP/South/Pipeline.shp", "OQ pipelines (south).shp")):
    cp_shp(W + key, os.path.join(G, "Roads and utilities", name), must=False)
cp_shp(os.path.join(B4, "Hydrology", "SHP", "Bypass road alignment", "North Batina Bypass.shp"), os.path.join(G, "Roads and utilities", "North Batinah Bypass (planned).shp"), must=False)
RS = os.path.join(G, "Rasters")
cp(os.path.join(W3, "maps", "data", "depth_200yr_plain.tif"), os.path.join(RS, "Flood depth 200-year without the scheme (m).tif"))
cp(os.path.join(B4, "Hydrology", "HEC_HMS_Block_04", "Hydrology Data", "CN_Include_Hill_Area.tif"), os.path.join(RS, "SCS curve number grid.tif"), must=False)
cp(os.path.join(W3, "maps", "data", "hillshade.tif"), os.path.join(RS, "Hillshade 10 m.tif"), must=False)
cp(os.path.join(B4, "Hydrology", "Terrain", "NSA_Batinah_5m_Block_04.tif"), os.path.join(RS, "Terrain model 5 m - Block 04.tif"))
cp(os.path.join(B4, "Hydrology", "Terrain", "NSA_Batinah_5m_Block_04_resample10m.tif"), os.path.join(RS, "Terrain model 10 m - Block 04.tif"))
for q in glob.glob(os.path.join(W3, "maps", "styles", "*.qml")): cp(q, os.path.join(G, "Styles", os.path.basename(q)))
cp(os.path.join(W9, "gis", "qml", "design_points_his.qml"), os.path.join(G, "Styles", "design_points.qml")); cp(os.path.join(W9, "gis", "qml", "segments_his.qml"), os.path.join(G, "Styles", "channel_reaches.qml"))
# ------------------------------------------------------------------ 04 KMZ (the second generation replaces the first)
K = os.path.join(OUT, "04 KMZ")
for old in glob.glob(os.path.join(K, "*.kmz")): rm(old)
NAMES = {"channels_dykes": "Channels and dykes", "channel_reaches": "Channel reaches and sizes", "extents": "Channel and dyke extents", "design_points": "Design points", "dams": "Dams", "culverts": "Culverts", "HEC-HMS_model": "HEC-HMS model", "all": "All layers"}
for f in glob.glob(os.path.join(W9, "kmz", "*.kmz")):
    key = os.path.basename(f)[len("Block04_"):-4]; cp(f, os.path.join(K, "Block 04 - %s.kmz" % NAMES.get(key, key.replace("_", " "))))
# ------------------------------------------------------------------ 05 tables
T = os.path.join(OUT, "05 Tables"); os.makedirs(T, exist_ok=True)
cp(os.path.join(W9, "tables", "Block 04 - Channel design tables (200-year).xlsx"), os.path.join(T, "Block 04 - Channel design tables (200-year).xlsx"))   # W10: built by 93_design_tables.py with live formulas
cp(os.path.join(W9, "tables", "Block 04 - BOQ and cost estimate.xlsx"), os.path.join(T, "Block 04 - BOQ and cost estimate.xlsx"))
cp(os.path.join(W3, "dams", "hydrographs", "Block04_Dam_Hydrographs - with 200yr hydrographs.xlsx"), os.path.join(T, "Block 04 - Dam hydrographs (all return periods, with the 200-year sheet).xlsx"))
cp(os.path.join(W3, "dams", "hydrographs", "dams_reservoirs.xlsx"), os.path.join(T, "Block 04 - Dams and reservoirs (hydrographs, peaks, volumes, levels).xlsx"))
for f in glob.glob(os.path.join(W7, "elements", "xlsx", "*.xlsx")): cp(f, os.path.join(T, "HEC-HMS " + os.path.basename(f).replace("_", " ")))
cp_csv_drop(os.path.join(W9, "culverts", "culverts_proposed.csv"), os.path.join(T, "Proposed culverts.csv"), ["end_short_m", "start_short_m", "existing_dist_m", "note"]); cp(os.path.join(W9, "culverts", "culverts_existing.csv"), os.path.join(T, "Existing culverts at the crossings.csv"))
cp(os.path.join(W9P, "volumes", "channel_quantities.csv"), os.path.join(T, "Channel quantities.csv")); cp(os.path.join(W7, "dykes", "dykes.csv"), os.path.join(T, "Dykes.csv"))
# ------------------------------------------------------------------ 06 maps
for sub, src in (("Channels feasibility and hydrological report", os.path.join(W9, "maps", "png_r6")), ("Hydraulic design of stormwater channels", os.path.join(W9, "maps", "png_sw_r1"))):
    for f in glob.glob(os.path.join(src, "M*.png")): cp(f, os.path.join(OUT, "06 Maps", sub, re.sub(r"^M\d+_", "", os.path.basename(f)).replace("_", " ")))
rm(os.path.join(OUT, "06 Maps", "Channels feasibility and hydrological report", "reach labels.png"))
# ------------------------------------------------------------------ 07 models
M = os.path.join(OUT, "07 Models")
HMS = os.path.join(B4, "Hydrology", "HEC_HMS_Block_04")
def copy_hms(dst):
    for root, dirs, files in os.walk(HMS):
        dirs[:] = [d_ for d_ in dirs if not d_.startswith("_backup")]
        for f in files:
            if re.match(r"^(DA|FM)_.*_B[2345]\.", f) or re.match(r"^(DA|FM)_[^_]+\.(dss|out|log)$", f) or f.endswith(".lock"): continue
            cp(os.path.join(root, f), os.path.join(dst, os.path.relpath(os.path.join(root, f), HMS)))
copy_hms(os.path.join(M, "HEC-HMS"))
SG = os.path.join(SHARE, "SewerGEMS Block 04 11102026")
for f in glob.glob(os.path.join(SG, "SewerGEMS Block 04_R9.*")):
    if ".bak" in f: continue
    cp(f, os.path.join(M, "SewerGEMS", os.path.basename(f).replace("_R9", "")))
if os.path.isdir(os.path.join(SG, "SHP")): cp(os.path.join(SG, "SHP"), os.path.join(M, "SewerGEMS", "SHP"))
CT = os.path.join(M, "Channel terrain")
rm(os.path.join(CT, "Block 04 - Channel terrain (2 m).zip")); rm(os.path.join(CT, "Channel terrain - contents.txt"))
cp(os.path.join(W9P, "terrain", "Block04_channel_surfaces_2m.tif"), os.path.join(CT, "Block 04 - Channel surfaces (designed, 2 m).tif"))
cp(os.path.join(W9P, "terrain", "Block04_terrain_with_channels_2m.tif"), os.path.join(CT, "Block 04 - Terrain with the channels cut in (2 m, 0.5 m ground).tif"))
cp(os.path.join(W9P, "terrain", "README.txt"), os.path.join(CT, "Channel terrain - contents.txt"))
for ch in sorted(os.listdir(os.path.join(W9P, "volumes"))):
    d_ = os.path.join(W9P, "volumes", ch)
    if os.path.isdir(d_):
        cp(os.path.join(d_, "channel_terrain.tif"), os.path.join(CT, "Per channel", ch, "Designed surface (2 m).tif")); cp(os.path.join(d_, "ground_2m.tif"), os.path.join(CT, "Per channel", ch, "Ground (0.5 m terrain at 2 m).tif"))
# ------------------------------------------------------------------ 09 the bypass road design package
BP = os.path.join(OUT, "09 Bypass road design package")
copy_hms(os.path.join(BP, "HEC-HMS model"))
to_shp(g, os.path.join(BP, "GIS", "Channels and dykes.shp")); cp(os.path.join(W3, "maps", "styles", "channels_dykes.qml"), os.path.join(BP, "GIS", "Channels and dykes.qml"))
cp_shp(os.path.join(W9, "gis", "segments_all_rp.shp"), os.path.join(BP, "GIS", "Channel reaches - 200-year design and the sizes of all return periods.shp")); cp(os.path.join(W9, "gis", "qml", "segments_his.qml"), os.path.join(BP, "GIS", "Channel reaches - 200-year design and the sizes of all return periods.qml"))
cp_shp(os.path.join(W9, "gis", "extents", "extent_200yr.shp"), os.path.join(BP, "GIS", "Channel extent 200-year (bed and corridor).shp"))
cp_shp(os.path.join(W9, "gis", "dyke_extent.shp"), os.path.join(BP, "GIS", "Dyke extent.shp"))
cp_shp(os.path.join(W6, "final", "Block4_design_points.shp"), os.path.join(BP, "GIS", "Design points.shp")); cp(os.path.join(W9, "gis", "qml", "design_points_his.qml"), os.path.join(BP, "GIS", "Design points.qml"))
cp_shp(os.path.join(B4, "Hydrology", "SHP", "Bypass road alignment", "North Batina Bypass.shp"), os.path.join(BP, "GIS", "North Batinah Bypass alignment (planned).shp"), must=False)
# W10 (his request, 2026-10-14): the culverts under the bypass as a layer, the two roads, and the package's own QGIS project (step 92)
_cro = gpd.read_file(os.path.join(W9, "culverts", "crossings.gpkg"), layer="crossings"); _cro = _cro[_cro.road == "North Batinah Bypass"]
_cro = _cro.drop(columns=[c for c in ("extended", "start_short", "end_short_m", "start_short_m", "existing_dist_m", "note") if c in _cro.columns])
to_shp(_cro, os.path.join(BP, "GIS", "Proposed box culverts under the bypass.shp"))
for _rd in ("Batinah Highway", "Batinah Coastal Road"): cp_shp(os.path.join(G, "Roads and utilities", _rd + ".shp"), os.path.join(BP, "GIS", _rd + ".shp"), must=False)
cp(os.path.join(W9, "bypass", "Block 04 - Flows and hydrographs at the bypass crossings.xlsx"), os.path.join(BP, "Block 04 - Flows and hydrographs at the bypass crossings.xlsx"))
cp(os.path.join(W9, "bypass", "Block 04 - Culverts at the bypass crossings.xlsx"), os.path.join(BP, "Block 04 - Culverts at the bypass crossings.xlsx"))
cp(os.path.join(W9P, "bypass", "civil3d", "Block04_Channel_Profiles_Bypass.dwg"), os.path.join(BP, "Civil 3D", "Block 04 - Channel profiles for the bypass design.dwg"), must=False)
if not DRY:
    os.makedirs(BP, exist_ok=True)
    open(os.path.join(BP, "Contents.txt"), "w", encoding="utf-8").write("""Block 04 - package for the design of the North Batinah Bypass

HEC-HMS model          The hydrological model of Block 04 (dams in place): catchments, reaches, junctions, reservoirs; the depth-area analyses of the 13 return periods
GIS                    Channels and dykes (with style), channel reaches of the 200-year design with the designed size of every return period (with style), channel extent 200-year (bed and corridor), dyke extent, design points (with style), the bypass alignment, the proposed box culverts under the bypass, the Batinah Highway and the Coastal Road
QGIS project           Block 04 - Bypass road design package.qgz: every layer of the GIS folder, styled and labelled (relative paths; open it from this folder) used
Civil 3D               Profile views of every channel: existing ground, channel invert with the grade in percent, channel crown, and the design point annotations
Flows and hydrographs  Peak flow and volume of all return periods and the 48-hour hydrographs at the channel crossings of the bypass (one sheet and chart per crossing)
Culverts               The proposed box culverts under the bypass with the channel data at each crossing

Coordinate system: WGS 84 / UTM zone 40N (EPSG:32640). Stations from the channel start.
""")
# ------------------------------------------------------------------ the contents note
README = """Block 04 - Flood Protection Scheme in North and South Al Batinah
Submission of %s (updated %s)

01 Reports      Channels Feasibility and Hydrological Report; Hydraulic Design of Stormwater Channels (PDF and Word)
02 Drawings     Plan and profile drawings of the flood protection channels and of the stormwater channels (200-year design), the Civil 3D drawing of the channels and dykes, the tables of drawings
03 GIS          Channels and dykes with their style, channel and dyke extents (200-year and every return period), design points and segments (styled), stations, the hydraulic model layers with the reach sizes of all return periods, dykes, culverts (proposed and the existing inventory), dams, catchments, land use, roads and utilities, rasters (flood depth, curve number, terrain)
04 KMZ          Google Earth files: channels and dykes, channel reaches and sizes, extents, design points, dams, culverts, the HEC-HMS model, and all in one; labels appear when zoomed in, click a feature for its data
05 Tables       Design tables (sections, reaches, outfalls, culverts, dykes, quantities and cost), the BOQ and cost estimate workbook, the dam hydrographs and reservoirs workbooks, the HEC-HMS peak flows
06 Maps         The maps of the two reports
07 Models       HEC-HMS project, SewerGEMS model (200-year design and the other return periods), the channel terrain on the 0.5 m ground (designed surfaces, terrain with the channels cut in, per channel)
08 QGIS         The QGIS project with a group for each report map and the supporting layers
09 Bypass road  The package for the design of the North Batinah Bypass (HEC-HMS model, layers, Civil 3D profiles, flows and hydrographs and culverts at the crossings)

Coordinate system of the GIS data: WGS 84 / UTM zone 40N (EPSG:32640).
""" % ("13 October 2026", time.strftime("%d %B %Y"))
if not DRY:
    os.makedirs(OUT, exist_ok=True); open(os.path.join(OUT, "Contents.txt"), "w", encoding="utf-8").write(README)
    open(os.path.join(W9, "submission_log.txt"), "w", encoding="utf-8").write("\n".join(log))
tot = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(OUT) for f in fs) if os.path.exists(OUT) else 0
print("%d files copied, written or removed; folder %s: %.2f GB" % (len(log), OUT, tot / 1e9))
