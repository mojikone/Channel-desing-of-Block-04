"""Give the new Basin 2 reaches their stream geometry (reach2d rows in Basin_2.sqlite, matched by name like Basin 1)
and replace the natural-reach trapezoid placeholders by DEM cross-section estimates.
usage: python add_reach_geometry.py <W2 output/hms folder> [--install <HMS project folder>]
"""
import sys, os, re, sqlite3, shutil, datetime
import numpy as np, pandas as pd, geopandas as gpd, rasterio
from shapely import wkb
from shapely.geometry import LineString, Point
OUT = sys.argv[1].rstrip("/\\") + "/"
INSTALL = sys.argv[sys.argv.index("--install") + 1].rstrip("/\\") + "/" if "--install" in sys.argv else None
T = "D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/HEC_HMS_Block_04/terrain/NSA_5m_B04_Res10m/00/elevation.tif"
dem = rasterio.open(T); A = dem.read(1); tr = dem.transform; H, W = A.shape
def z_at(xy):
    c, r = ~tr * xy; r, c = int(r), int(c)
    if 0 <= r < H and 0 <= c < W and A[r, c] < 1e30: return float(A[r, c])
    return np.nan

reaches = gpd.read_file(OUT + "Basin_2_review.gpkg", layer="reaches_new")
reaches = reaches[reaches.R.notna() & (reaches.R != "")].copy()
print("new reaches with geometry:", len(reaches))

# ---------- DEM cross-sections for natural reaches ----------
def section_stats(line, half=400.0, step=10.0, every=100.0):
    L = line.length; st = np.arange(min(50.0, L / 2), max(L - 50.0, L / 2) + 1, every)
    if len(st) > 60: st = np.linspace(st[0], st[-1], 60)
    w05, w15, zs = [], [], []
    offs = np.arange(-half, half + step, step)
    for s in st:
        p = line.interpolate(s); p1 = line.interpolate(max(s - 5, 0)); p2 = line.interpolate(min(s + 5, L))
        dx, dy = p2.x - p1.x, p2.y - p1.y; n = np.hypot(dx, dy)
        if n == 0: continue
        nx, ny = -dy / n, dx / n
        z = np.array([z_at((p.x + o * nx, p.y + o * ny)) for o in offs])
        mid = (np.abs(offs) <= 60) & np.isfinite(z)
        if not mid.any(): continue
        i0 = np.where(mid)[0][np.nanargmin(z[mid])]; z0 = z[i0]
        def width(h):
            lvl = z0 + h
            l = i0
            while l > 0 and (not np.isfinite(z[l]) or z[l] < lvl): l -= 1
            r = i0
            while r < len(z) - 1 and (not np.isfinite(z[r]) or z[r] < lvl): r += 1
            if l == 0 or r == len(z) - 1: return np.nan
            return offs[r] - offs[l]
        w05.append(width(0.5)); w15.append(width(1.5)); zs.append(z0)
    w05 = np.array(w05, float); w15 = np.array(w15, float)
    return dict(n_sections=len(zs), w05_med=np.nanmedian(w05) if np.isfinite(w05).any() else np.nan,
                w15_med=np.nanmedian(w15) if np.isfinite(w15).any() else np.nan, frac_found=np.isfinite(w15).mean() if len(w15) else 0)

rows = []
for r in reaches.itertuples():
    natural = (r.ch_type is None) or (str(r.ch_type) in ("", "nan", "None"))
    rec = dict(R=r.R, S=r.S, natural=natural, length_m=r.geometry.length, straight_m=Point(r.geometry.coords[0]).distance(Point(r.geometry.coords[-1])))
    zf, zt = z_at(r.geometry.coords[0][:2]), z_at(r.geometry.coords[-1][:2]); rec.update(z_from=zf, z_to=zt, relief_m=zf - zt, slope_dem=(zf - zt) / rec["length_m"] if rec["length_m"] > 0 else np.nan)
    if natural:
        st = section_stats(r.geometry); rec.update(st)
        b = st["w05_med"]; T_ = st["w15_med"]
        if np.isfinite(b) and np.isfinite(T_) and st["frac_found"] >= 0.5:
            b = float(np.clip(b, 10, 600)); zz = float(np.clip(((T_ - b) / 2) / 1.0, 1, 25))
            rec.update(bottom_width=round(b, 0), side_slope=round(zz, 1), source="DEM sections (0.5 m / 1.5 m above thalweg)")
        else:
            rec.update(bottom_width=100.0, side_slope=5.0, source="placeholder (sections not resolved)")
    else:
        rec.update(bottom_width=np.nan, side_slope=np.nan, source="channel: type placeholder kept, design section required")
    rows.append(rec)
df = pd.DataFrame(rows); df.to_csv(OUT + "Basin_2_reach_geometry_and_sections.csv", index=False)
nat = df[df.natural]
print(f"natural reaches: {len(nat)} | DEM-derived sections: {(nat.source.str.startswith('DEM')).sum()} | bottom width median {nat.bottom_width.median():.0f} m (range {nat.bottom_width.min():.0f}-{nat.bottom_width.max():.0f}) | side slope median {nat.side_slope.median():.1f}")

# ---------- update the .basin: natural reach sections ----------
p = OUT + "Basin_2.basin"; txt = open(p, encoding="utf-8").read()
def patch_reach(txt, name, b, zz):
    m = re.search(r'^Reach: ' + re.escape(name) + r'\n.*?^End:', txt, re.S | re.M); blk = m.group(0)
    blk2 = re.sub(r'^(\s*Bottom Width: ).*$', lambda k: k.group(1) + f"{b:g}", blk, flags=re.M)
    blk2 = re.sub(r'^(\s*Side Slope: ).*$', lambda k: k.group(1) + f"{zz:g}", blk2, flags=re.M)
    return txt[:m.start()] + blk2 + txt[m.end():]
for r in nat.itertuples(): txt = patch_reach(txt, r.R, r.bottom_width, r.side_slope)
open(p, "w", encoding="utf-8", newline="\n").write(txt); print("Basin_2.basin: natural reach sections updated")

# ---------- reach2d + reach_statistics rows in Basin_2.sqlite (matched by name, as Basin 1 does) ----------
c = sqlite3.connect(OUT + "Basin_2.sqlite")
c.execute("delete from reach2d where name like 'R1__' or name like 'R2__'")   # idempotent for R100-R299
c.execute("delete from reach_statistics where reach_name like 'R1__' or reach_name like 'R2__'")
n = 0
for r in reaches.itertuples():
    pts = [(x, y, z_at((x, y)) if np.isfinite(z_at((x, y))) else 0.0) for x, y in [cc[:2] for cc in r.geometry.coords]]
    c.execute("insert into reach2d (GEOMETRY, name) values (?,?)", (wkb.dumps(LineString(pts)), r.R))
    d = df[df.R == r.R].iloc[0]
    c.execute("insert into reach_statistics (reach_name, reach_length, reach_slope, reach_relief, reach_sinuosity, length_units) values (?,?,?,?,?,?)",
              (r.R, str(d.length_m), str(d.slope_dem), str(d.relief_m), str(d.length_m / d.straight_m if d.straight_m > 0 else 1.0), "m"))
    n += 1
c.commit(); c.close(); print("Basin_2.sqlite: reach2d geometry rows written:", n)

if INSTALL:
    for f in ["Basin_2.basin", "Basin_2.sqlite"]: shutil.copy2(OUT + f, INSTALL + f)
    print("installed into", INSTALL)
