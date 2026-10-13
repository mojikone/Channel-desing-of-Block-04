"""Step 13 - data for the QGIS map figures (plain Python: geopandas / rasterio), read by 24_maps_qgis_r1.py.
R1 (2026-10-06): the NINE dams of Basin 4 (Shafan 08 included), report labels, exclusive catchment polygons.

maps/data/dam_catchments_results.gpkg : layer 'catchments' = the nine catchments with the step-20/21/11 results as attributes
                                        (area, CN, yield, loss %, 200-yr peaks ...); layer 'catchments_excl' = the same minus the
                                        upstream dams' catchments (Hawasinah UP without 02 and 11, Shafan 08 without Shafan 02),
                                        for fills and labels that must not overlap
maps/data/dams.gpkg                   : dam axes (lines) and dam points with FSL/crest/capacity
maps/data/<factor>_catchments.tif     : R, K, LS, C, P, SoilLoss clipped to the nine catchments (NaN outside)
maps/data/hillshade.tif               : hillshade of the HMS 10 m terrain, resampled to 30 m (the map background)
maps/data/extent.json                 : map extents (all; catchments only; channels and dams)
"""
import sys, json, os
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio import mask as rmask
from rasterio.enums import Resampling
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DAMS9, HMS, CB04, DAMS_SHP, W3, CRS, ensure, label, BLOCK4

OUT = ensure(W3 / "maps" / "data"); SED = W3 / "sediment"
cat = gpd.read_file(SED / "catchments" / "Dam_catchments9.gpkg").set_index("name")
y = pd.read_csv(SED / "sediment_yield.csv").set_index("name"); s = pd.read_csv(SED / "reservoir_sedimentation_summary.csv")
s50 = s[s.horizon_yr == 50].set_index("dam"); s100 = s[s.horizon_yr == 100].set_index("dam"); summ = pd.read_csv(W3 / "dams" / "data" / "dam_summary_B4.csv")
q200 = summ[summ.rp == "200yr"].set_index("dam"); pmp = summ[summ.rp == "PMP"].set_index("dam")
dams = gpd.read_file(DAMS_SHP).set_index("Dam Name")
UPSTREAM = {"Hawasinah EX": ["Hawasinah 02", "Hawasinah 11"], "Shafan 08": ["Shafan 02"]}
rows = []
for dam in DAMS9:
    rows.append(dict(name=dam, label=label(dam), label_s=label(dam, short=True), area_km2=float(cat.loc[dam, "area_km2"]), cn=float(cat.loc[dam, "cn_w"]), fsl_m=float(dams.loc[dam, "FSL"]), crest_m=float(dams.loc[dam, "Crest El"]),
                     capacity_Mm3=float(dams.loc[dam, "Reservoir"]), spill_L=float(dams.loc[dam, "Spillway L"]), soil_loss=float(y.loc[dam, "soil_loss_t_ha_yr"]), R=float(y.loc[dam, "R"]), K=float(y.loc[dam, "K"]),
                     LS=float(y.loc[dam, "LS"]), C=float(y.loc[dam, "C"]), P=float(y.loc[dam, "P"]), sdr=float(y.loc[dam, "sdr_used"]), yield_m3km2=float(y.loc[dam, "yield_m3_km2_yr"]), yield_m3yr=float(y.loc[dam, "yield_m3_yr"]), sed50_Mcm=float(y.loc[dam, "sed50_Mcm"]), sed100_Mcm=float(y.loc[dam, "sed100_Mcm"]),
                     loss50_pct=float(s50.loc[dam, "loss_pct"]), loss100_pct=float(s100.loc[dam, "loss_pct"]), dep50_Mm3=float(s50.loc[dam, "deposited_Mm3"]), q200_in=float(q200.loc[dam, "peak_inflow_m3s"]),
                     q200_out=float(q200.loc[dam, "peak_outflow_m3s"]), qpmp_in=float(pmp.loc[dam, "peak_inflow_m3s"]), lvl_pmp=float(pmp.loc[dam, "peak_level_m"]), geometry=cat.loc[dam, "geometry"]))
g = gpd.GeoDataFrame(rows, crs=cat.crs); g.to_file(OUT / "dam_catchments_results.gpkg", layer="catchments", driver="GPKG")
ex = g.copy()
for dam, ups in UPSTREAM.items():
    i = ex.index[ex.name == dam][0]; u = gpd.GeoSeries([cat.loc[d, "geometry"] for d in ups], crs=cat.crs); uu = u.union_all() if hasattr(u, "union_all") else u.unary_union
    ex.loc[i, "geometry"] = ex.loc[i, "geometry"].difference(uu.buffer(5))
ex["area_excl_km2"] = ex.geometry.area / 1e6; ex.to_file(OUT / "dam_catchments_results.gpkg", layer="catchments_excl", driver="GPKG")
# dams: axes and points
ax = dams.reset_index()[["Dam Name", "FSL", "Crest El", "Reservoir", "Spillway L", "geometry"]].rename(columns={"Dam Name": "name", "FSL": "fsl_m", "Crest El": "crest_m", "Reservoir": "capacity_Mm3", "Spillway L": "spill_L"})
ax["label"] = [label(n) for n in ax.name]; ax["label_s"] = [label(n, short=True) for n in ax.name]
ax.to_file(OUT / "dams.gpkg", layer="dam_axes", driver="GPKG")
pts = ax.copy(); pts["geometry"] = pts.geometry.interpolate(0.5, normalized=True); pts.to_file(OUT / "dams.gpkg", layer="dam_points", driver="GPKG")
# rasters clipped to the catchments
union = [cat.geometry.union_all()] if hasattr(cat.geometry, "union_all") else [cat.geometry.unary_union]
stats = {}
for f in ("R", "K", "LS", "C", "P", "SoilLoss"):
    with rasterio.open(SED / "rusle" / "Output" / "Rasters" / f"{f}.tif") as src:
        geom = gpd.GeoSeries(union, crs=cat.crs).to_crs(src.crs); arr, tr = rmask.mask(src, [geom.iloc[0]], crop=True, nodata=np.nan, filled=True); a = arr[0].astype("float32")
        a[~np.isfinite(a)] = np.nan; meta = src.meta.copy(); meta.update(driver="GTiff", height=a.shape[0], width=a.shape[1], transform=tr, dtype="float32", nodata=-9999.0, compress="lzw", count=1)
        out = np.where(np.isfinite(a), a, -9999.0).astype("float32")
        with rasterio.open(OUT / f"{f}_catchments.tif", "w", **meta) as dst: dst.write(out, 1)
        v = a[np.isfinite(a)]; stats[f] = dict(p2=float(np.percentile(v, 2)), p98=float(np.percentile(v, 98)), min=float(v.min()), max=float(v.max()), mean=float(v.mean()))
# hillshade of the HMS terrain at 30 m
with rasterio.open(HMS / "terrain" / "NSA_5m_B04_Res10m" / "00" / "elevation.tif") as src:
    sc = 3; h, w = src.height // sc, src.width // sc; z = src.read(1, out_shape=(h, w), resampling=Resampling.average).astype("float64"); tr = src.transform * src.transform.scale(src.width / w, src.height / h)
    nod = src.nodata; z[(z == nod) | (z > 1e30) | (z < -1e4)] = np.nan
    dx = tr.a; dzdx = np.gradient(z, dx, axis=1); dzdy = -np.gradient(z, dx, axis=0)
    az, alt = np.deg2rad(315), np.deg2rad(45); slope = np.arctan(np.hypot(dzdx, dzdy)); aspect = np.arctan2(-dzdx, dzdy)
    hs = 255 * (np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)); hs = np.clip(hs, 0, 255); hs[np.isnan(z)] = 0
    meta = src.meta.copy(); meta.update(height=h, width=w, transform=tr, dtype="uint8", nodata=0, compress="lzw", count=1)
    with rasterio.open(OUT / "hillshade.tif", "w", **meta) as dst: dst.write(hs.astype("uint8"), 1)
    terrain_bounds = list(rasterio.transform.array_bounds(h, w, tr))
ch = gpd.read_file(BLOCK4 / "Hydrology" / "SHP" / "temp" / "Channels and Dykes 04102026.shp").to_crs(cat.crs); ch = ch[ch["Block"] == 4]   # the file holds Blocks 2, 4 and 6
b_cat = list(cat.total_bounds); b_all = list(gpd.GeoSeries(list(cat.geometry) + list(ch.geometry), crs=cat.crs).total_bounds); b_chd = list(gpd.GeoSeries(list(ch.geometry) + list(dams.geometry), crs=cat.crs).total_bounds)
controlled = float((union[0].area) / 1e6)
# the plain: the dams and every HMS point outside the dam catchments (the elements downstream of the dams), for the zoomed Q200 map
pts = gpd.read_file(W3 / "elements" / "shp" / "B3" / "Points_B3.shp").to_crs(cat.crs); inside = pts.geometry.within(union[0].buffer(-50))
down = gpd.GeoSeries(list(pts[~inside].geometry) + list(dams.geometry) + list(ch.geometry), crs=cat.crs); b_down = list(down.total_bounds); print("points downstream of the dams:", int((~inside).sum()), "of", len(pts))
# the 200-year flood depth of the plain: the server raster is 820 MB; the clip to the channel-and-dam window with a 12 % margin
# (LZW) is the map input, so that the map figures and the deliverables project read nothing outside the project folders
DEPTH = "W:/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/06-WORKING/04-Hydraulic/00 Data/Layers/Flood Maps/Depth/Rasters OK/B4 Depth Rasters/Block4_200Yr.tif"
if os.path.exists(DEPTH):
    from rasterio.windows import from_bounds
    with rasterio.open(DEPTH) as src:
        x0, y0, x1, y1 = b_chd; dx, dy = (x1 - x0) * 0.12, (y1 - y0) * 0.12
        win = from_bounds(max(x0 - dx, src.bounds.left), max(y0 - dy, src.bounds.bottom), min(x1 + dx, src.bounds.right), min(y1 + dy, src.bounds.top), src.transform).round_offsets().round_lengths()
        arr = src.read(1, window=win); tr = src.window_transform(win); meta = src.meta.copy(); meta.update(driver="GTiff", height=arr.shape[0], width=arr.shape[1], transform=tr, compress="lzw", predictor=2, tiled=True)
        with rasterio.open(OUT / "depth_200yr_plain.tif", "w", **meta) as dst: dst.write(arr, 1)
        print("depth clip:", arr.shape, f"{os.path.getsize(OUT / 'depth_200yr_plain.tif') / 1e6:.0f} MB")
else: print("depth raster not reachable; the previous clip is kept")
json.dump(dict(catchments=b_cat, all=b_all, channels_dams=b_chd, downstream=b_down, terrain=terrain_bounds, raster_stats=stats, controlled_km2=controlled), open(OUT / "extent.json", "w"), indent=1)
print("written", OUT, "| rasters:", {k: (round(v["p2"], 3), round(v["p98"], 3)) for k, v in stats.items()}, "| controlled km2:", round(controlled), "| extents:", [round(x) for x in b_all])
