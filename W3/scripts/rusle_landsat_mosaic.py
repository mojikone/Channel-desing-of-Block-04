"""Replace the RUSLE pipeline's single Landsat 8 scene by a mosaic of the least-cloudy 2017 scene of EVERY path/row that
covers the study bbox (the pipeline takes one scene, which here misses most of the dam catchments -> C factor NaN).
Run with the RUSLE venv python from the rusle folder:  python ../../scripts/rusle_landsat_mosaic.py
Writes Data/Landsat8/landsat8_2017_B4B5.tif (2 bands: red, nir08 surface reflectance 0-1; -9999 nodata), previous file kept as *_single_scene.tif
"""
import os, sys, shutil
import numpy as np, rasterio, geopandas as gpd
from rasterio import mask as rmask
from rasterio.merge import merge
from shapely.geometry import box as shapely_box
import pystac_client, planetary_computer
sys.path.insert(0, os.path.join(os.getcwd(), "Scripts")); import config
from config import BBOX, DIRS, DATE_START, DATE_END, catchments

out_dir = DIRS["landsat8"]; out_path = os.path.join(out_dir, "landsat8_2017_B4B5.tif")
if os.path.exists(out_path) and not os.path.exists(out_path.replace(".tif", "_single_scene.tif")): shutil.move(out_path, out_path.replace(".tif", "_single_scene.tif"))
cat_b = catchments.to_crs("EPSG:4326").total_bounds; m = 0.1; search_bbox = [cat_b[0] - m, cat_b[1] - m, cat_b[2] + m, cat_b[3] + m]
catalog = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=planetary_computer.sign_inplace)
items = list(catalog.search(collections=["landsat-c2-l2"], bbox=search_bbox, datetime=f"{DATE_START}/{DATE_END}", query={"eo:cloud_cover": {"lt": 30}, "platform": {"in": ["landsat-8"]}}).items())
best = {}
for it in items:
    key = (it.properties.get("landsat:wrs_path"), it.properties.get("landsat:wrs_row")); cc = it.properties.get("eo:cloud_cover", 100)
    if key not in best or cc < best[key].properties.get("eo:cloud_cover", 100): best[key] = it
print("scenes found:", len(items), "| path/rows:", {k: (v.id, v.properties.get("eo:cloud_cover")) for k, v in best.items()})
west, south, east, north = BBOX; tmp = []
for key, it in best.items():
    hrefs = [it.assets[k].href for k in ("red", "nir08")]
    with rasterio.open(hrefs[0]) as src: crs = src.crs
    geom = [g.__geo_interface__ for g in gpd.GeoDataFrame(geometry=[shapely_box(west, south, east, north)], crs="EPSG:4326").to_crs(crs).geometry]
    bands = []; meta = None
    for href in hrefs:
        with rasterio.open(href) as src:
            arr, tr = rmask.mask(src, geom, crop=True, nodata=0, filled=True); a = arr[0].astype(np.float32)
            refl = np.where(a > 0, np.clip(a * 2.75e-5 - 0.2, 0, 1), -9999.0).astype(np.float32); bands.append(refl)
            meta = src.meta.copy(); meta.update(count=2, dtype="float32", nodata=-9999, compress="lzw", height=refl.shape[0], width=refl.shape[1], transform=tr, crs=crs)
    p = os.path.join(out_dir, f"scene_{key[0]}_{key[1]}.tif")
    with rasterio.open(p, "w", **meta) as dst: dst.write(bands[0], 1); dst.write(bands[1], 2)
    tmp.append(p); print("  read", it.id, refl.shape, "valid share", round(float((bands[0] > -1).mean()), 3))
srcs = [rasterio.open(p) for p in tmp]; mosaic, tr = merge(srcs, nodata=-9999, method="first"); meta = srcs[0].meta.copy(); [s.close() for s in srcs]
meta.update(height=mosaic.shape[1], width=mosaic.shape[2], transform=tr, count=2, dtype="float32", nodata=-9999, compress="lzw")
with rasterio.open(out_path, "w", **meta) as dst: dst.write(mosaic.astype(np.float32))
for p in tmp: os.remove(p)
valid = (mosaic[0] > -1).mean(); print("mosaic written", out_path, mosaic.shape, "| valid share of bbox", round(float(valid), 3))
