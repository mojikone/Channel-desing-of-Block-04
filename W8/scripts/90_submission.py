"""Step 90 (W8) - the clean submission folder (engineer, 2026-10-13): one folder with everything final — the two reports, the two
plan-profile drawing sets and the Civil 3D drawing, the GIS layers with their styles, the KMZ files, the tables, the report maps,
the models of record (HEC-HMS Basin 6, SewerGEMS R9, the channel terrain) and the QGIS project (built by step 91). Client-facing
names only: no iteration or revision tags, no internal names. Copies are skipped when the target has the same size and date.
    python 90_submission.py [--dry] [--out "<folder>"]"""
import os, sys, shutil, re, glob, json, zipfile, time
import pandas as pd, geopandas as gpd
HERE = os.path.dirname(os.path.abspath(__file__)); W8 = os.path.dirname(HERE); CB = os.path.dirname(W8); B4 = os.path.dirname(CB)
W3, W6, W7 = (os.path.join(CB, w) for w in ("W3", "W6", "W7"))
W = "W:/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/06-WORKING/"
SHARE = r"C:\Users\mojtaba\Desktop\Win10 shared folder"
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
DRY = "--dry" in A
OUT = opt("--out", os.path.join(B4, "Deliverables", "2 Submission 13102026"))
SHEETS = os.path.join(W8, "sewergems", "sheets", "scripts")
log = []

def cp(src, dst, must=True):
    """copy one file (or a whole folder when src is a directory) if missing or changed"""
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

def to_shp(gdf, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if DRY: return
    g = gdf.copy()
    for c in g.columns:
        if c != "geometry" and g[c].dtype == object: g[c] = g[c].map(lambda v: str(v) if isinstance(v, (dict, list)) else v)
    g.to_file(dst, driver="ESRI Shapefile"); log.append(os.path.relpath(dst, OUT) + "  (written)")

# ------------------------------------------------------------------ 01 reports
R = os.path.join(OUT, "01 Reports")
cp(os.path.join(W8, "report", "R5", "Block04_Report_R5.pdf"), os.path.join(R, "Block 04 - Channels Feasibility and Hydrological Report.pdf"))
cp(os.path.join(W8, "report", "R5", "Block04_Report_R5.docx"), os.path.join(R, "Block 04 - Channels Feasibility and Hydrological Report.docx"))
cp(os.path.join(W8, "report", "SW_R0", "Block04_Stormwater_Channels_R0.pdf"), os.path.join(R, "Block 04 - Hydraulic Design of Stormwater Channels.pdf"), must=False)
cp(os.path.join(W8, "report", "SW_R0", "Block04_Stormwater_Channels_R0.docx"), os.path.join(R, "Block 04 - Hydraulic Design of Stormwater Channels.docx"), must=False)

# ------------------------------------------------------------------ 02 drawings
DW = os.path.join(OUT, "02 Drawings")
cp(os.path.join(SHEETS, "PDF", "Set", "2224-PD-HY-PP-B4_Plan_and_Profile_Drawings_200yr_R9.pdf"), os.path.join(DW, "2224-PD-HY-PP-B4 - Plan and Profile Drawings of the Flood Protection Channels (200-year).pdf"))
cp(os.path.join(SHEETS, "PDF", "Set", "2224-PD-HY-PP-B4_Stormwater_Channels_Plan_and_Profile_Drawings_200yr_R9.pdf"), os.path.join(DW, "2224-PD-HY-PP-B4 - Plan and Profile Drawings of the Stormwater Channels (200-year).pdf"))
cp(os.path.join(W6, "civil3d", "Block04_Channels_W6.dwg"), os.path.join(DW, "Civil 3D", "Block 04 - Channels and Dykes.dwg"))
for key, name in (("2224-PD-HY-PP-B4_Plan_and_Profile_Drawings_200yr_R9_contents.csv", "Table of drawings - flood protection channels.csv"), ("2224-PD-HY-PP-B4_Stormwater_Channels_Plan_and_Profile_Drawings_200yr_R9_contents.csv", "Table of drawings - stormwater channels.csv")):
    p = os.path.join(SHEETS, "PDF", "Set", key)
    if os.path.exists(p) and not DRY:
        t = pd.read_csv(p); t.columns = ["Drawing No.", "Catchment", "Channel", "Drawing", "Station from", "Station to", "Page"]; os.makedirs(DW, exist_ok=True); t.to_csv(os.path.join(DW, name), index=False); log.append(name + "  (written)")

# ------------------------------------------------------------------ 03 GIS
G = os.path.join(OUT, "03 GIS")
chs = os.path.join(B4, "Hydrology", "SHP", "temp", "Channels and Dykes 04102026.shp")
g = gpd.read_file(chs); g = g[g["Block"] == 4]; to_shp(g, os.path.join(G, "Channels and dykes", "Channels and dykes.shp"))
cp(os.path.join(W3, "maps", "styles", "channels_dykes.qml"), os.path.join(G, "Channels and dykes", "Channels and dykes.qml"))
cp_shp(os.path.join(SHEETS, "Data", "SHP", "Buffers", "Channel Bed Buffer.shp"), os.path.join(G, "Channel extents", "Channel bed (designed, 200-year).shp"))
cp_shp(os.path.join(SHEETS, "Data", "SHP", "Buffers", "Channels Buffer.shp"), os.path.join(G, "Channel extents", "Channel corridor (bed, embankments and access roads).shp"))
cp_shp(os.path.join(W6, "final", "Block4_design_points.shp"), os.path.join(G, "Design points and segments", "Design points.shp"))
cp_shp(os.path.join(W6, "final", "Block4_design_segments.shp"), os.path.join(G, "Design points and segments", "Design segments.shp"))
cp(os.path.join(W6, "final", "Block4_design_points.csv"), os.path.join(G, "Design points and segments", "Design points.csv"))
cp(os.path.join(W6, "final", "Block4_design_segments.csv"), os.path.join(G, "Design points and segments", "Design segments.csv"))
cp(os.path.join(W8, "gis", "stations.gpkg"), os.path.join(G, "Stations", "Stations every 500 m and 1000 m.gpkg"))
cp(os.path.join(W8, "gis", "sewergems_200yr_R9.gpkg"), os.path.join(G, "Hydraulic model (200-year design)", "Channel reaches, nodes, outfalls, bed and corridor.gpkg"))
cp(os.path.join(W7, "gis", "outfalls_levels.gpkg"), os.path.join(G, "Hydraulic model (200-year design)", "Outfalls - invert and existing level.gpkg"))
cp(os.path.join(W7, "dykes", "dykes.gpkg"), os.path.join(G, "Dykes", "Dykes - height and cost.gpkg"))
cp(os.path.join(W8, "culverts", "crossings.gpkg"), os.path.join(G, "Culverts", "Road crossings and proposed box culverts.gpkg"))
ex = gpd.read_file(W + "04-Hydraulic/05 Small Tasks/18 Channel Design/Master Plan Map/Data for Master Plan/SHP/Culverts/Existing Culverts Batinah/Culverts_2_4.shp").to_crs(32640)
env = g.total_bounds; pad = 5000; ex = ex.cx[env[0] - pad: env[2] + pad, env[1] - pad: env[3] + pad]; to_shp(ex, os.path.join(G, "Culverts", "Existing culverts (inventory, Block 04 plain).shp"))
cp_shp(os.path.join(B4, "Hydrology", "SHP", "Block 4 Dams", "Dams updated.shp"), os.path.join(G, "Dams", "Dam axes.shp"))
cp_shp(W + "04-Hydraulic/05 Small Tasks/18 Channel Design/SHP/Block 04 Dams/Polygon_FSL.shp", os.path.join(G, "Dams", "Reservoirs at full supply level.shp"))
cp_shp(W + "04-Hydraulic/05 Small Tasks/18 Channel Design/SHP/Block 04 Dams/Ppygon_Crest_Level.shp", os.path.join(G, "Dams", "Reservoirs at crest level.shp"))
cp(os.path.join(W8, "gis", "GCA_RENN.gpkg"), os.path.join(G, "Catchments", "Global catchments.gpkg"))
for f in ("Subbasins_B6.shp", "Subbasins_B6_dam.shp", "Reaches_B6.shp", "Points_B6.shp"):
    cp_shp(os.path.join(W7, "elements", "shp", "B6", f), os.path.join(G, "Catchments", "HEC-HMS " + {"Subbasins_B6.shp": "subbasins", "Subbasins_B6_dam.shp": "subbasins with dam flag", "Reaches_B6.shp": "reaches", "Points_B6.shp": "junctions and outfalls"}[f] + ".shp"), must=False)
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

# ------------------------------------------------------------------ 04 KMZ
for f in glob.glob(os.path.join(W8, "kmz", "*.kmz")): cp(f, os.path.join(OUT, "04 KMZ", os.path.basename(f).replace("Block04_", "Block 04 - ").replace("_", " ")))

# ------------------------------------------------------------------ 05 tables
T = os.path.join(OUT, "05 Tables"); os.makedirs(T, exist_ok=True)
if not DRY:
    sys.path.insert(0, os.path.join(W8, "report")); sys.path.insert(0, os.path.join(W8, "report", "lib")); os.environ.pop("REPORT_ONLY", None)
    import data_facts as DF
    with pd.ExcelWriter(os.path.join(T, "Block 04 - Channel design tables (200-year).xlsx")) as xw:
        DF.channel_sections("200yr").to_excel(xw, sheet_name="Channel sections", index=False); DF.reach_table().to_excel(xw, sheet_name="Reaches", index=False); DF.size_inventory().to_excel(xw, sheet_name="Size inventory", index=False)
        DF.outfalls_table().to_excel(xw, sheet_name="Outfalls", index=False); DF.culverts().to_excel(xw, sheet_name="Proposed culverts", index=False); DF.dykes().to_excel(xw, sheet_name="Dykes", index=False)
        q = DF.channel_quantities(); q["land_take_ha"] = q.land_take_ha.map(json.dumps); q.to_excel(xw, sheet_name="Channel quantities and cost", index=False)
        DF.land_take_by_class().to_excel(xw, sheet_name="Land take by class", index=False); DF.cost_by_catchment().to_excel(xw, sheet_name="Cost by catchment", index=False)
        pd.DataFrame([DF.cost_totals()]).to_excel(xw, sheet_name="Cost totals (million OMR)", index=False)
    log.append("05 Tables/Block 04 - Channel design tables (200-year).xlsx  (written)")
for f in glob.glob(os.path.join(W7, "elements", "xlsx", "*.xlsx")): cp(f, os.path.join(T, "HEC-HMS " + os.path.basename(f).replace("_", " ")))
cp(os.path.join(W8, "culverts", "culverts_proposed.csv"), os.path.join(T, "Proposed culverts.csv")); cp(os.path.join(W8, "culverts", "culverts_existing.csv"), os.path.join(T, "Existing culverts at the crossings.csv"))
cp(os.path.join(W7, "volumes", "channel_quantities.csv"), os.path.join(T, "Channel quantities.csv")); cp(os.path.join(W7, "dykes", "dykes.csv"), os.path.join(T, "Dykes.csv"))

# ------------------------------------------------------------------ 06 maps
for sub, src in (("Channels feasibility and hydrological report", os.path.join(W8, "maps", "png_r5")), ("Hydraulic design of stormwater channels", os.path.join(W8, "maps", "png_sw"))):
    for f in glob.glob(os.path.join(src, "M*.png")): cp(f, os.path.join(OUT, "06 Maps", sub, re.sub(r"^M\d+_", "", os.path.basename(f)).replace("_", " ")))

# ------------------------------------------------------------------ 07 models
M = os.path.join(OUT, "07 Models")
HMS = os.path.join(B4, "Hydrology", "HEC_HMS_Block_04")
for root, dirs, files in os.walk(HMS):
    dirs[:] = [d_ for d_ in dirs if not d_.startswith("_backup")]
    for f in files:
        if re.match(r"^(DA|FM)_.*_B[2345]\.", f) or re.match(r"^(DA|FM)_[^_]+\.(dss|out|log)$", f): continue   # results of the superseded basins; Basin 6 is the hydrology of record
        if f.endswith(".lock"): continue
        cp(os.path.join(root, f), os.path.join(M, "HEC-HMS", os.path.relpath(os.path.join(root, f), HMS)))
SG = os.path.join(SHARE, "SewerGEMS Block 04 11102026")
for f in glob.glob(os.path.join(SG, "SewerGEMS Block 04_R9.*")):
    if ".bak" in f: continue
    cp(f, os.path.join(M, "SewerGEMS", os.path.basename(f).replace("_R9", "")))
if os.path.isdir(os.path.join(SG, "SHP")): cp(os.path.join(SG, "SHP"), os.path.join(M, "SewerGEMS", "SHP"))
cp(os.path.join(W7, "volumes", "Block04_channel_terrain_R9_2m.zip"), os.path.join(M, "Channel terrain", "Block 04 - Channel terrain (2 m).zip"))
cp(os.path.join(W7, "volumes", "README_channel_terrain.txt"), os.path.join(M, "Channel terrain", "Channel terrain - contents.txt"), must=False)

# ------------------------------------------------------------------ the contents note
README = """Block 04 - Flood Protection Scheme in North and South Al Batinah
Submission of %s

01 Reports      Channels Feasibility and Hydrological Report; Hydraulic Design of Stormwater Channels (PDF and Word)
02 Drawings     Plan and profile drawings of the flood protection channels and of the stormwater channels (200-year design), the Civil 3D drawing of the channels and dykes, the tables of drawings
03 GIS          Channels and dykes with their style, channel extents, design points and segments, stations, the hydraulic model layers, dykes, culverts, dams, catchments, land use, roads and utilities, rasters (flood depth, curve number, terrain)
04 KMZ          Google Earth files: channels and dykes, extents, design points, dams, culverts, and all in one
05 Tables       The design tables (sections, reaches, outfalls, culverts, dykes, quantities and cost) and the HEC-HMS peak flows
06 Maps         The maps of the two reports
07 Models       HEC-HMS project, SewerGEMS model (200-year design and the other return periods), channel terrain surfaces
08 QGIS         The QGIS project with a group for each report map and the supporting layers

Coordinate system of the GIS data: WGS 84 / UTM zone 40N (EPSG:32640).
""" % time.strftime("%d %B %Y")
if not DRY:
    os.makedirs(OUT, exist_ok=True); open(os.path.join(OUT, "Contents.txt"), "w", encoding="utf-8").write(README)
    open(os.path.join(W8, "submission_log.txt"), "w", encoding="utf-8").write("\n".join(log))
tot = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(OUT) for f in fs) if os.path.exists(OUT) else 0
print("%d files copied or written; folder %s: %.2f GB" % (len(log), OUT, tot / 1e9))
