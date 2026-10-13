"""Elevation-area-volume curve of Shafan 08 (the dam re-enters the report): pond at each 0.5 m level = cells of the 10 m
HMS terrain below the level, inside the dam's crest-level polygon (Ppygon_Crest_Level.shp), connected to the dam axis.
Same method as the other eight curves (W2 hypsometry3), with the ready crest polygon instead of the polygonised contour.
Writes ../reservoirs/EAV_Shafan_08.csv and prints the volume at FSL against the dams sheet."""
import sys, numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio import mask as rmask
from rasterio.features import rasterize
from scipy import ndimage as ndi
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from config import HMS, CB04
S = "W:/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/06-WORKING/04-Hydraulic/05 Small Tasks/18 Channel Design/SHP/Block 04 Dams/"
T = HMS / "terrain" / "NSA_5m_B04_Res10m" / "00" / "elevation.tif"
dams = gpd.read_file(S + "Dams updated.shp").set_index("Dam Name"); poly = gpd.read_file(S + "Ppygon_Crest_Level.shp").set_index("Dam_Name")
def curve(name, step=0.5):
    axis = dams.loc[name, "geometry"]; crest_el = float(dams.loc[name, "Crest El"]); fsl = float(dams.loc[name, "FSL"]); pg = poly.loc[name, "geometry"]
    with rasterio.open(T) as src:
        arr, tr = rmask.mask(src, [pg.buffer(50)], crop=True, nodata=np.nan); z = arr[0].astype(float); z[(z > 1e30) | (z < -1e4)] = np.nan
        inside = rasterize([(pg, 1)], out_shape=z.shape, transform=tr, dtype=np.uint8).astype(bool)
        ax = rasterize([(axis.buffer(15), 1)], out_shape=z.shape, transform=tr, dtype=np.uint8).astype(bool)
    seed = ndi.binary_dilation(ax, iterations=3) & inside
    bed = np.nanmin(z[inside & ~ax]) if np.isfinite(z[inside]).any() else np.nan
    levels = np.arange(np.floor(bed) + step, crest_el + step / 2, step); A = []; V = []
    for lv in levels:
        wet = inside & (z < lv) & np.isfinite(z); lab, n = ndi.label(wet); ids = np.unique(lab[seed & wet]); ids = ids[ids > 0]
        pond = np.isin(lab, ids) if len(ids) else np.zeros_like(wet)
        A.append(pond.sum() * 100 / 1e6); V.append(np.clip(lv - z[pond], 0, None).sum() * 100 / 1e6)
    A, V = np.array(A), np.array(V); k0 = int(np.argmax(A > 0)); levels, A, V = levels[k0:], A[k0:], V[k0:]
    return pd.DataFrame(dict(elevation_m=levels.round(2), area_km2=A.round(4), volume_Mm3=V.round(4))), fsl, crest_el
df, fsl, crest = curve("Shafan 08"); out = CB04 / "reservoirs" / "EAV_Shafan_08.csv"; df.to_csv(out, index=False)
a = df.area_km2.values * 1e6; z = df.elevation_m.values; v = np.zeros_like(z)
for i in range(1, len(z)): v[i] = v[i - 1] + (z[i] - z[i - 1]) / 3 * (a[i - 1] + a[i] + np.sqrt(a[i - 1] * a[i]))
print("Shafan 08: bed", z[0], "| rows", len(df), "| at FSL", fsl, ": area", round(float(np.interp(fsl, z, a)) / 1e6, 2), "km2, conic volume", round(float(np.interp(fsl, z, v)) / 1e6, 2), "Mm3 (DEM-integrated", round(float(np.interp(fsl, z, df.volume_Mm3)), 2), ") vs sheet", float(dams.loc["Shafan 08", "Reservoir"]), "| at crest", crest, ":", round(float(v[-1]) / 1e6, 2), "Mm3 | written", out)
# cross-check the method on a dam already computed with the W2 script
d2, f2, c2 = curve("Sarami 03"); old = pd.read_csv(CB04 / "reservoirs" / "EAV_Sarami_03.csv")
print("check Sarami 03: polygon method V at FSL", round(float(np.interp(f2, d2.elevation_m, d2.volume_Mm3)), 2), "| W2 method", round(float(np.interp(f2, old.elevation_m, old.volume_Mm3)), 2), "Mm3")
