"""Step 05 - one small GeoTIFF per feature: the 0.5 m DEM cells of its 1 m corridor, nodata elsewhere (points/strips/<name>.tif).
The alternative surface source for Civil 3D (surface from DEM file + the corridor as outer boundary) when the LandXML
import cannot be driven; the data are the same cells as the point files."""
import sys
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio.transform import from_origin
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_w4 import LINES, POINTS, CRS

out = POINTS / "strips"; out.mkdir(exist_ok=True); lines = gpd.read_file(LINES / "Block4_lines.gpkg"); n = 0
for r in lines.itertuples():
    p = pd.read_csv(POINTS / "csv" / f"{r.name}.csv", header=None, names=["P", "E", "N", "Z", "D"])
    x0 = np.floor(p.E.min()) - 1; y1 = np.ceil(p.N.max()) + 1; cols = ((p.E - x0) / 0.5).round().astype(int); rows = ((y1 - p.N) / 0.5).round().astype(int)
    a = np.full((rows.max() + 1, cols.max() + 1), -9999.0, "float32"); a[rows, cols] = p.Z.astype("float32")
    with rasterio.open(out / f"{r.name}.tif", "w", driver="GTiff", height=a.shape[0], width=a.shape[1], count=1, dtype="float32", crs=CRS, transform=from_origin(x0, y1, 0.5, 0.5), nodata=-9999.0, compress="lzw", tiled=True) as dst: dst.write(a, 1)
    n += 1
print(n, "strips ->", out, f"({sum(f.stat().st_size for f in out.glob('*.tif')) / 1e6:.0f} MB)")
