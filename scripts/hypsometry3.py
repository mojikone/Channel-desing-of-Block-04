"""Reservoir elevation-area-volume (10 m DEM): pond at level z = cells with ground < z, 4-connected to the dam axis,
inside MASK = D8 catchment of the dam junction UNION the crest-contour polygon (contour closed by the dam axis) where it polygonizes."""
import sys, json, numpy as np, rasterio, rasterio.mask as rm, geopandas as gpd, pandas as pd
from rasterio.features import rasterize
from scipy import ndimage as ndi
from shapely.ops import unary_union, polygonize, linemerge, nearest_points
from shapely.geometry import LineString, Point
sys.path.insert(0, '.'); from d8lib import downstream_index, upstream_csr, watershed
T = "D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/HEC_HMS_Block_04/terrain/NSA_5m_B04_Res10m/00/elevation.tif"
S = "W:/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/06-WORKING/04-Hydraulic/05 Small Tasks/18 Channel Design/SHP/Block 04 Dams/"
dams = gpd.read_file(S + "Dams updated.shp"); crest = gpd.read_file(S + "Crest_Level.shp")
sheet = pd.read_excel("W:/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/06-WORKING/04-Hydraulic/00 Data/Dams/Block 04/Block 4 Dams/Block 4 Dams Details.xlsx").set_index("Dam Name")
with rasterio.open(T) as s: el = s.read(1); tr = s.transform; H, W = el.shape
with rasterio.open("new/d8.tif") as s: w = s.read(1)
fd = np.full((H, W), -32768, np.int16)
for k, v in {1: 2, 2: 1, 4: 8, 8: 7, 16: 6, 32: 5, 64: 4, 128: 3}.items(): fd[w == k] = v
ds = downstream_index(fd, -32768); cnt, up = upstream_csr(ds); bp = json.load(open("new/out/nodes.json"))["bp"]
def crest_faces(axis, level):
    cand = crest[((crest.Contour - level).abs() <= 1) & (crest.geometry.distance(axis) < 3000)]; parts = []
    for g in cand.geometry:
        g = linemerge(g) if g.geom_type == "MultiLineString" else g
        for gg in (g.geoms if g.geom_type == "MultiLineString" else [g]):
            parts.append(gg)
            for pt in (Point(gg.coords[0]), Point(gg.coords[-1])):
                q = nearest_points(pt, axis)[1]
                if 0 < pt.distance(q) < 2500: parts.append(LineString([pt, q]))
    return [f for f in polygonize(unary_union(parts + [axis])) if f.area > 1e5]
STEP = 0.5; out = []; polys = []
for d in dams.itertuples():
    name = d[1]
    if name == "Shafan 08" or name not in bp: continue
    crest_el = float(d[2]); fsl = float(d[3]); axis = d.geometry
    label = np.zeros(H * W, np.int8); n = watershed(int(bp[name]), cnt, up, label, 1); catch = label.reshape(H, W).astype(bool)
    faces = crest_faces(axis, crest_el); facemask = np.zeros((H, W), bool)
    good = []
    for f in faces:   # keep faces that are mostly below crest (the impounded side)
        arr, trf = rm.mask(rasterio.open(T), [f], crop=True, nodata=np.nan); z = arr[0]; z = z[np.isfinite(z) & (z < 1e30)]
        if z.size and (z < crest_el).mean() > 0.6: good.append(f)
    if good: facemask = rasterize([(f, 1) for f in good], out_shape=(H, W), transform=tr, dtype=np.uint8).astype(bool); polys.append(dict(dam=name, geometry=unary_union(good)))
    maskall = catch | facemask
    ax = rasterize([(axis.buffer(15), 1)], out_shape=(H, W), transform=tr, dtype=np.uint8).astype(bool)
    rows_, cols_ = np.where((maskall & (el < crest_el) & (el < 1e30)) | ax); r0, r1, c0, c1 = rows_.min(), rows_.max() + 1, cols_.min(), cols_.max() + 1
    z = el[r0:r1, c0:c1]; mk = maskall[r0:r1, c0:c1]; am = ax[r0:r1, c0:c1]; seed = ndi.binary_dilation(am, iterations=3) & catch[r0:r1, c0:c1] | (ndi.binary_dilation(am, iterations=3) & facemask[r0:r1, c0:c1])
    levels = np.arange(np.floor(z[mk & (z < 1e30)].min()) + STEP, crest_el + STEP / 2, STEP); A = []; V = []
    for lv in levels:
        wet = mk & (z < lv) & (z < 1e30); lab, nl = ndi.label(wet); ids = np.unique(lab[seed & wet]); ids = ids[ids > 0]
        pond = np.isin(lab, ids) if len(ids) else np.zeros_like(wet)
        A.append(pond.sum() * 100 / 1e6); V.append(np.clip(lv - z[pond], 0, None).sum() * 100 / 1e6)
    A = np.array(A); V = np.array(V); k0 = int(np.argmax(A > 0)); levels, A, V = levels[k0:], A[k0:], V[k0:]
    pd.DataFrame(dict(elevation_m=levels.round(2), area_km2=A.round(4), volume_Mm3=V.round(4))).to_csv(f"reservoirs/EAV_{name.replace(' ', '_')}.csv", index=False)
    vf = float(np.interp(fsl, levels, V)); af = float(np.interp(fsl, levels, A))
    out.append(dict(dam=name, crest=crest_el, fsl=fsl, crest_faces=len(good), bed_m=round(float(levels[0] - STEP), 1), A_fsl_km2=round(af, 2), V_fsl_Mm3=round(vf, 2),
                    sheet_Mm3=float(sheet.loc[name if name != "Hawasinah EX" else "Hawasinah UP", "Reservoir Capacity (MCM)"]), A_crest_km2=round(float(A[-1]), 2), V_crest_Mm3=round(float(V[-1]), 2),
                    spillway_L=float(d[8]), C=float(d[7]), axis_len_m=round(axis.length)))
df = pd.DataFrame(out); df["diff_%"] = ((df.V_fsl_Mm3 / df.sheet_Mm3 - 1) * 100).round(1); pd.set_option("display.width", 250); print(df.to_string(index=False)); df.to_csv("reservoirs/summary.csv", index=False)
if polys: gpd.GeoDataFrame(polys, crs="EPSG:32640").to_file("reservoirs/crest_polygons.gpkg", driver="GPKG")
