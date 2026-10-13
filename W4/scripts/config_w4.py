"""W4 - Civil 3D surfaces and ground profiles for the Block 4 channels and dykes. Paths and parameters."""
from pathlib import Path
W4 = Path(__file__).resolve().parents[1]; CB04 = W4.parent; BLOCK4 = CB04.parent
LINES_SHP = BLOCK4 / "Hydrology" / "SHP" / "temp" / "Channels and Dykes 04102026.shp"     # all blocks; Block = 4 is used
TERRAIN = "//FILESERVER-/Works/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/10-DATABASE/01 DEM/Prosessed_DEM/OUTPUT/GGC4_DTM_GMAP_NSA.tif"   # 0.5 m DEM (the shortcut in Hydrology/DWG/Claude for CAD Points/Data/Terrain); forward slashes: GDAL rejects the backslash UNC form
CRS = "EPSG:32640"
BUFFER_M = 0.5            # each side of the centreline (1 m corridor), the engineer's instruction of 2026-10-07
ND_LIMIT = 1e30           # DEM nodata is 3.4e38
TILE_PX = 2048            # DEM read window (1 024 m); N_WORKERS network-bound
N_WORKERS = 16
LINES = W4 / "lines"; POINTS = W4 / "points"; LANDXML = W4 / "landxml"; C3D = W4 / "civil3d"; LOG = W4 / "log"
for p in (LINES, POINTS, LANDXML, C3D, LOG): p.mkdir(parents=True, exist_ok=True)
def kind_of(name): return "channel" if "-CH" in name else "dyke"
def cls_of(name): return name.rsplit("-", 1)[-1]          # FP, SM, SS
def gca_of(name): return name.split("-", 1)[0]            # HAW, SHA, SAR, SAK
def sort_key(name):
    """HAW-CH1-FP -> (kind, catchment, class order, number)"""
    import re
    m = re.match(r"([A-Z]+)-(CH|D)(\d+)-(FP|SM|SS)$", name); order = {"FP": 0, "SM": 1, "SS": 2}
    return (0 if m.group(2) == "CH" else 1, m.group(1), order[m.group(4)], int(m.group(3))) if m else (9, name, 9, 0)
