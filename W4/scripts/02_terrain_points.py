"""Step 02 - terrain points of every Block 4 channel and dyke: the 0.5 m DEM cells whose centres lie within 0.5 m of the
centreline (1 m corridor, native 0.5 m spacing, pixel-centre rule), read tile-parallel straight off the network DEM as in
the August 2026 run, but kept PER FEATURE:
  points/csv/<name>.csv              P,E,N,Z,D point file of each feature (Civil 3D point-file format, D = name)
  points/Terrain_Points_B4_0.5m.dxf  one DXF, every point on the layer PT_<name>
  points/Block4_buffers_0.5m.gpkg    the corridor polygon of each feature
  points/points_summary.csv          points, elevation range and corridor area per feature
"""
import os, sys, time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio.windows import Window
from rasterio.features import rasterize
from shapely import wkb as shp_wkb
from shapely.geometry import box
from shapely.strtree import STRtree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_w4 import TERRAIN, LINES, POINTS, BUFFER_M, ND_LIMIT, TILE_PX, N_WORKERS, CRS

def worker(args):
    """one DEM window x one feature: the valid cells inside the feature's corridor"""
    fid, col_off, row_off, ncols, nrows, wkb = args
    poly = shp_wkb.loads(wkb)
    with rasterio.open(TERRAIN) as src:
        win = Window(col_off, row_off, ncols, nrows); tr = src.window_transform(win)
        mask = rasterize([(poly, 1)], out_shape=(nrows, ncols), transform=tr, fill=0, dtype="uint8", all_touched=False)
        if not mask.any(): return fid, None
        z = src.read(1, window=win)
    ok = (mask > 0) & np.isfinite(z) & (z < ND_LIMIT)
    if not ok.any(): return fid, None
    rows, cols = np.nonzero(ok)
    return fid, np.column_stack([tr.c + (cols + 0.5) * tr.a, tr.f + (rows + 0.5) * tr.e, z[rows, cols].astype("float64")])

def main():
    t0 = time.time(); lines = gpd.read_file(LINES / "Block4_lines.gpkg"); lines = lines.sort_values("order").reset_index(drop=True)
    buf = lines.copy(); buf["geometry"] = lines.geometry.buffer(BUFFER_M, cap_style=2); buf["area_m2"] = buf.geometry.area.round(1)
    buf[["name", "kind", "cls", "gca", "length_m", "area_m2", "geometry"]].to_file(POINTS / "Block4_buffers_0.5m.gpkg", layer="buffers", driver="GPKG")
    jobs = []
    with rasterio.open(TERRAIN) as src:
        rt, W, H = src.transform, src.width, src.height; px = rt.a
        for fid, poly in enumerate(buf.geometry):
            minx, miny, maxx, maxy = poly.bounds
            c0 = max(0, int((minx - rt.c) / px) - 1); c1 = min(W, int((maxx - rt.c) / px) + 2); r0 = max(0, int((maxy - rt.f) / rt.e) - 1); r1 = min(H, int((miny - rt.f) / rt.e) + 2)
            for row_off in range(r0, r1, TILE_PX):
                nrows = min(TILE_PX, r1 - row_off)
                for col_off in range(c0, c1, TILE_PX):
                    ncols = min(TILE_PX, c1 - col_off)
                    tile = box(rt.c + col_off * px, rt.f + (row_off + nrows) * rt.e, rt.c + (col_off + ncols) * px, rt.f + row_off * rt.e)
                    part = poly.intersection(tile)
                    if not part.is_empty: jobs.append((fid, col_off, row_off, ncols, nrows, part.wkb))
    print(f"{len(lines)} features, {len(jobs)} window jobs, {N_WORKERS} workers  [{time.time() - t0:.0f}s]")
    parts = {fid: [] for fid in range(len(lines))}; done = 0
    with ProcessPoolExecutor(max_workers=N_WORKERS) as ex:
        for fut in as_completed([ex.submit(worker, j) for j in jobs]):
            fid, arr = fut.result(); done += 1
            if arr is not None: parts[fid].append(arr)
            if done % 50 == 0 or done == len(jobs): print(f"  {done}/{len(jobs)} windows  [{time.time() - t0:.0f}s]", flush=True)
    (POINTS / "csv").mkdir(exist_ok=True); rows = []
    layers = [("PT_" + r.name) for r in lines.itertuples()]
    with open(POINTS / "Terrain_Points_B4_0.5m.dxf", "w", encoding="ascii", buffering=32 * 1024 * 1024) as dxf:
        dxf.write("0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n0\nENDSEC\n0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLAYER\n70\n" + str(len(layers) + 1) + "\n0\nLAYER\n2\n0\n70\n0\n62\n7\n6\nCONTINUOUS\n")
        for i, lay in enumerate(layers): dxf.write(f"0\nLAYER\n2\n{lay}\n70\n0\n62\n{1 + i % 7}\n6\nCONTINUOUS\n")
        dxf.write("0\nENDTAB\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n")
        for fid, r in enumerate(lines.itertuples()):
            arr = np.vstack(parts[fid]) if parts[fid] else np.zeros((0, 3))
            arr = arr[np.lexsort((arr[:, 0], -arr[:, 1]))] if len(arr) else arr                     # north to south, west to east: deterministic files
            pd.DataFrame({"P": np.arange(1, len(arr) + 1), "E": arr[:, 0].round(3), "N": arr[:, 1].round(3), "Z": arr[:, 2].round(3), "D": r.name}).to_csv(POINTS / "csv" / f"{r.name}.csv", index=False, header=False)
            dxf.write("".join(f"0\nPOINT\n8\n{layers[fid]}\n10\n{x:.3f}\n20\n{y:.3f}\n30\n{z:.3f}\n" for x, y, z in arr))
            rows.append(dict(name=r.name, kind=r.kind, cls=r.cls, gca=r.gca, length_m=r.length_m, n_points=len(arr), pts_per_m=round(len(arr) / r.length_m, 2) if r.length_m else 0, z_min=round(float(arr[:, 2].min()), 2) if len(arr) else None, z_max=round(float(arr[:, 2].max()), 2) if len(arr) else None))
        dxf.write("0\nENDSEC\n0\nEOF\n")
    s = pd.DataFrame(rows); s.to_csv(POINTS / "points_summary.csv", index=False)
    print(f"DONE {int(s.n_points.sum()):,} points in {len(s)} features, {s.n_points.min():,} to {s.n_points.max():,} per feature, {s.pts_per_m.median():.1f} points per metre; DXF {os.path.getsize(POINTS / 'Terrain_Points_B4_0.5m.dxf') / 1e6:.0f} MB  [{time.time() - t0:.0f}s]")
    empty = s[s.n_points == 0]
    if len(empty): print("NO POINTS (outside the DEM?):", empty.name.tolist())

if __name__ == "__main__":
    main()
