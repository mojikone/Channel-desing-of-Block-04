"""Georeference the HMS screenshots (north-up similarity transform) from labelled element icons and extract the red
hand-drawn lines as UTM polylines.  Output: red_lines.gpkg (one layer per image) + overlay PNGs for checking."""
import re, sys, os, numpy as np, pandas as pd, geopandas as gpd
from PIL import Image
from scipy import ndimage as ndi
from skimage.morphology import skeletonize, binary_closing, disk
from shapely.geometry import LineString, Point
IMG = "C:/Users/mojtaba/AppData/Local/Temp/claude/D--Mojtaba-Renardet-2224-WS11-Batinah-Block-4/72a3ff20-809e-4d71-bf42-7b9f694d69ff/images/"
BASIN = "D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/HEC_HMS_Block_04/Basin_2.basin"
OUT = "georef/"; os.makedirs(OUT, exist_ok=True)
txt = open(BASIN, encoding="utf-8", errors="replace").read()
EL = {n: (float(x), float(y)) for n, x, y in re.findall(r'^(?:Subbasin|Junction|Reach): (.+?)\n.*?Canvas X: (\S+)\n\s*Canvas Y: (\S+)', txt, re.S | re.M)}
# rough pixel positions of labelled icons read off each screenshot (x, y); refined by snapping to icon blobs
SEEDS = {
 1: {"J105": (155, 318), "J104": (360, 490), "Outlet 8 FP CH 31": (590, 195), "J113": (108, 88), "Outlet 4 Sw M CH 20": (385, 50), "J102": (35, 218), "J112": (100, 268)},
 2: {"Outlet 12 Sw M CH 34": (470, 225), "J154": (405, 250), "J113": (415, 520), "J119": (555, 610), "Outlet 6 Sw S CH 19": (672, 402), "J147": (178, 567), "J111": (255, 628), "J153": (45, 155), "J135": (68, 357), "J125": (50, 452)},
 3: {"Outlet 1 Sw M CH 24": (288, 92), "J148": (97, 278), "Outlet 9 FP CH 16": (440, 282), "J106": (220, 355), "J207": (238, 378), "J208": (280, 338), "J209": (290, 445), "J206": (165, 435)},
 4: {"J150": (305, 172), "J128": (325, 225), "J145": (55, 290), "J107": (100, 418), "J205": (55, 45), "Outlet 1 Sw M CH 24": (523, 514)},
 5: {"J148": (285, 138), "J144": (165, 230), "J106": (352, 187), "J201": (195, 275), "J200": (165, 322), "J103": (315, 385), "J129": (355, 410), "J122": (470, 312), "J126": (527, 270), "J137": (45, 75), "Outlet 1 Sw M CH 24": (390, 37)},
 6: {"J144": (765, 40), "J200": (790, 115), "J157": (845, 118), "J195": (700, 200), "J193": (403, 555), "J178": (470, 78), "J176": (490, 170), "J174": (285, 78), "J26": (210, 170), "Sakhin 04": (190, 235), "Sakhin 08": (285, 445), "Sarami 05": (315, 668), "J28": (18, 598), "J166": (455, 292), "J163": (418, 352), "J103": (905, 172), "J129": (945, 197), "J116": (1050, 298), "J147": (1145, 380), "J111": (1080, 412)},
 7: {"J102": (907, 70), "J202": (877, 92), "J137": (838, 232), "J107": (897, 180), "Outlet 1 Sw M CH 24": (1050, 210), "J174": (530, 357), "J26": (420, 428), "Sakhin 04": (490, 470), "J25": (345, 490), "J24": (290, 572), "J28": (375, 732), "Sakhin 08": (560, 622), "Sarami 05": (580, 783), "J193": (645, 700), "J178": (690, 355), "J176": (715, 422), "J181": (655, 230), "J103": (610, 262), "J144": (910, 330), "J157": (952, 381), "J115": (565, 352), "J125": (1120, 528), "J147": (1178, 578), "J111": (1222, 590)},
 10: {"Outlet 5 FP CH 26": (740, 68), "J205": (695, 100), "J202": (648, 130), "J145": (688, 200), "J107": (712, 245), "J137": (598, 318), "J182": (427, 315), "J181": (362, 315), "J103": (335, 355), "J174": (205, 480), "J178": (420, 475), "J176": (437, 558), "J144": (684, 440), "J201": (725, 487), "J200": (700, 513), "J157": (762, 515), "J195": (628, 585), "J166": (393, 672), "J165": (357, 690), "J163": (342, 725), "Sakhin 04": (153, 623), "J26": (138, 565), "J150": (785, 153), "J128": (816, 172), "J148": (795, 370), "J106": (848, 407), "J206": (823, 440), "J210": (929, 375)},
 8: {"Hawasinah 02": (280, 568), "J12": (360, 370), "J11": (175, 482), "J4": (318, 695), "J9": (95, 692), "J198": (68, 232), "J117": (375, 197), "J118": (428, 197), "J114": (528, 262), "J221": (535, 160), "J220": (560, 228), "J212": (350, 118)},
}
def icon_blobs(im):
    r, g, b = [im[..., i].astype(int) for i in range(3)]
    m = ((r == 0) & (g == 0) & (b == 204)) | ((r == 51) & (g == 102) & (b == 255)) | ((r == 102) & (g == 51) & (b == 0)) | ((r == 0) & (g == 51) & (b == 153))
    lab, n = ndi.label(ndi.binary_dilation(m, iterations=2))
    cents = ndi.center_of_mass(m, lab, range(1, n + 1)); sizes = ndi.sum(m, lab, range(1, n + 1))
    return np.array([(c[1], c[0]) for c, s in zip(cents, sizes) if s >= 12])
def fit(px, utm):
    # similarity: utm = s*R*px + t  (y axis flipped) -> solve linear least squares for [a,b,tx,ty]: X = a*px - b*py + tx ; Y = b*px + a*py + ty  (with py negated)
    A = []; B = []
    for (x, y), (X, Y) in zip(px, utm):
        A.append([x, -(-y), 1, 0]); B.append(X); A.append([-y, x, 0, 1]); B.append(Y)   # use p=(x,-y)
    sol, *_ = np.linalg.lstsq(np.array(A, float), np.array(B, float), rcond=None); return sol
def apply(sol, px):
    a, b, tx, ty = sol; x = px[:, 0]; y = -px[:, 1]
    return np.c_[a * x - b * y + tx, b * x + a * y + ty]
def trace_skeleton(sk):
    H, W = sk.shape; pts = set(zip(*np.nonzero(sk))); nb = lambda p: [(p[0] + i, p[1] + j) for i in (-1, 0, 1) for j in (-1, 0, 1) if (i or j) and (p[0] + i, p[1] + j) in pts]
    deg = {p: len(nb(p)) for p in pts}; nodes = {p for p in pts if deg[p] != 2}; visited = set(); paths = []
    def walk(start, first):
        path = [start, first]; visited.add((start, first)); visited.add((first, start)); cur, prev = first, start
        while cur not in nodes:
            nxt = [q for q in nb(cur) if q != prev]
            if not nxt: break
            q = nxt[0]
            if (cur, q) in visited: break
            visited.add((cur, q)); visited.add((q, cur)); path.append(q); prev, cur = cur, q
            if cur == start: break
        return path
    for n in nodes:
        for q in nb(n):
            if (n, q) not in visited: paths.append(walk(n, q))
    for p in pts:   # pure cycles without nodes
        if deg[p] == 2 and not any((p, q) in visited for q in nb(p)): paths.append(walk(p, nb(p)[0]))
    return [p for p in paths if len(p) >= 4]
rows = []; report = []
ONLY = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else None
for k, seeds in SEEDS.items():
    if ONLY and k not in ONLY: continue
    im = np.array(Image.open(IMG + f"{k}.png").convert("RGB")); blobs = icon_blobs(im)
    px, utm, names = [], [], []
    for n, (x, y) in seeds.items():
        if n not in EL: report.append(f"img{k}: {n} not in basin"); continue
        d = np.hypot(blobs[:, 0] - x, blobs[:, 1] - y); j = int(d.argmin())
        if d[j] > 18: report.append(f"img{k}: {n} no icon blob within 18 px (nearest {d[j]:.0f})"); continue
        px.append(blobs[j]); utm.append(EL[n]); names.append(n)
    px = np.array(px); utm = np.array(utm)
    for it in range(3):
        sol = fit(px, utm); res = np.hypot(*(apply(sol, px) - utm).T); keep = res < max(3 * np.median(res), 60)
        if keep.all(): break
        report.append(f"img{k}: dropped {[names[i] for i in np.where(~keep)[0]]} residual {res[~keep].round(0)}"); px, utm, names = px[keep], utm[keep], [n for n, kp in zip(names, keep) if kp]
    scale = np.hypot(sol[0], sol[1]); res = np.hypot(*(apply(sol, px) - utm).T)
    report.append(f"img{k}: {len(px)} control points, {scale:.1f} m/px, rms {np.sqrt((res**2).mean()):.0f} m, max {res.max():.0f} m")
    r, g, b = [im[..., i].astype(int) for i in range(3)]
    red = (r > 200) & (g < 140) & (b < 90)
    if red.sum() < 200: continue
    sk = skeletonize(binary_closing(red, disk(2)))
    for path in trace_skeleton(sk):
        pts = apply(sol, np.array([(c, rr) for rr, c in path], float))
        rows.append(dict(img=k, geometry=LineString(pts).simplify(scale * 0.7), length_m=LineString(pts).length))
print("\n".join(report))
gdf = gpd.GeoDataFrame(rows, crs="EPSG:32640"); gdf = gdf[gdf.length_m > 150]
if ONLY and os.path.exists(OUT + "red_lines.gpkg"):
    old = gpd.read_file(OUT + "red_lines.gpkg", layer="red_lines"); old = old[~old.img.isin(ONLY)]
    gdf = pd.concat([old, gdf], ignore_index=True)
gdf.to_file(OUT + "red_lines.gpkg", layer="red_lines", driver="GPKG")
print("red lines:", gdf.groupby("img").agg(n=("length_m", "size"), km=("length_m", lambda x: round(x.sum() / 1000, 1))).to_string())
