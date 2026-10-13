"""Delineate a basin from a D8 grid (WhiteboxTools pointer) and write links table + GIS review layers.
usage: python delineate.py <grid_folder> [--no-channels]
"""
import numpy as np, rasterio, numba as nb, geopandas as gpd, pandas as pd, re, sys, os, time, json
from rasterio.features import rasterize, shapes
from rasterio.warp import reproject, Resampling
from shapely.geometry import Point, LineString, shape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from d8lib import downstream_index
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:6.1f}s]", *a, flush=True)
T = "D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/HEC_HMS_Block_04/terrain/NSA_5m_B04_Res10m/00/"
HMS = "D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/HEC_HMS_Block_04/"
P = "D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Hydrology/SHP/temp/CH WALL for HMS channels/"
N = sys.argv[1].rstrip("/\\") + "/"
USE_CH = "--no-channels" not in sys.argv
OUT = N + "out/"; os.makedirs(OUT, exist_ok=True)
_th = [a for a in sys.argv if a.startswith("--thresh=")]
THRESH_KM2 = float(_th[0].split("=")[1]) if _th else 5.0
THRESH = int(THRESH_KM2 * 1e6 / 100); DIAG = 10 * 2 ** 0.5
OUT = N + f"out_t{THRESH_KM2:g}/" if _th else OUT
os.makedirs(OUT, exist_ok=True)
DAMS = ["Hawasinah 02", "Hawasinah 11", "Hawasinah EX", "Shafan 02", "Sarami 03", "Sarami 05", "Sakhin 04", "Sakhin 08"]
if not USE_CH: DAMS = DAMS + ["Shafan 08"]

# ---------- grids ----------
with rasterio.open(N + "d8.tif") as s: w = s.read(1); tr = s.transform; H, W = w.shape; crs = s.crs
fd = np.full((H, W), -32768, np.int16)
for k, v in {1: 2, 2: 1, 4: 8, 8: 7, 16: 6, 32: 5, 64: 4, 128: 3}.items(): fd[w == k] = v
del w
with rasterio.open(T + "elevation.tif") as s: el = s.read(1)
valid = (el < 1e30) & (fd > 0)
ds = downstream_index(fd, -32768).astype(np.int32); log("ds")
xs_ = (np.arange(W) + 0.5) * tr.a + tr.c; ys_ = (np.arange(H) + 0.5) * tr.e + tr.f

@nb.njit(cache=True)
def accum32(ds):
    n = ds.size; acc = np.ones(n, np.int32); indeg = np.zeros(n, np.int32)
    for i in range(n):
        if ds[i] >= 0: indeg[ds[i]] += 1
    q = np.empty(n, np.int32); h = 0; t = 0
    for i in range(n):
        if indeg[i] == 0: q[t] = i; t += 1
    while h < t:
        i = q[h]; h += 1; j = ds[i]
        if j >= 0:
            acc[j] += acc[i]; indeg[j] -= 1
            if indeg[j] == 0: q[t] = j; t += 1
    return acc, q
acc, order = accum32(ds); accg = acc.reshape(H, W); log("acc max km2", acc.max() * 100 / 1e6)

# ---------- channels ----------
ch = gpd.read_file(P + "CH.shp"); ch["is_channel"] = ch["CHtt"].fillna("").str.contains("CH")
chan = ch[ch.is_channel]
ch_id = np.zeros(H * W, np.int16)
if USE_CH:
    from shapely.ops import linemerge
    def zat_xy(x, y):
        c, r = ~tr * (x, y); r, c = int(r), int(c)
        return float(el[r, c]) if (0 <= r < H and 0 <= c < W and valid[r, c]) else np.nan
    for i, g in chan.geometry.items():
        g = linemerge(g) if g.geom_type == "MultiLineString" else g
        a, b = g.coords[0][:2], g.coords[-1][:2]; za, zb = zat_xy(*a), zat_xy(*b)
        up = a if (np.isnan(zb) or (not np.isnan(za) and za >= zb)) else b
        c, r = ~tr * up; r, c = int(r), int(c); cell = r * W + c; n = 0
        while cell >= 0 and n < 1000000:
            if ch_id[cell] == 0: ch_id[cell] = i + 1
            cell = int(ds[cell]); n += 1
ch_id = ch_id.reshape(H, W)
ch_cells = (ch_id > 0) & valid
ch_line = rasterize(((g, i + 1) for i, g in chan.geometry.items()), out_shape=(H, W), transform=tr, dtype=np.int16) if USE_CH else np.zeros((H, W), np.int16)
stream = ((accg >= THRESH) | ch_cells) & valid
log("channel cells", ch_cells.sum(), "stream cells", stream.sum())

# ---------- break points: dam junctions from Basin 1 ----------
txt = open(HMS + "Basin_1.basin", encoding="utf-8", errors="replace").read()
J1 = {n: (float(x), float(y)) for n, x, y in re.findall(r'^Junction: (.+?)\n.*?Canvas X: (\S+)\n\s*Canvas Y: (\S+)', txt, re.S | re.M)}
# natural confluences on the threshold network (before break points), used to snap junctions onto confluence cells
_sm = stream.ravel(); _sc = np.flatnonzero(_sm).astype(np.int32)
@nb.njit(cache=True)
def _nxt(scells, ds, smask):
    nxt = np.full(ds.size, -1, np.int32)
    for s in scells:
        c = ds[s]
        while c >= 0 and not smask[c]: c = ds[c]
        nxt[s] = c
    return nxt
_nx = _nxt(_sc, ds, _sm); _in = np.zeros(H * W, np.int32); np.add.at(_in, _nx[_sc][_nx[_sc] >= 0], 1)
confl = (_in >= 2).reshape(H, W)
bp = {}; snapped_conf = 0
for n in J1:
    name = n if (n in DAMS or n != "Shafan 08") else "Shafan 08 site"
    x, y = J1[n]; c, r = ~tr * (x, y); r, c = int(r), int(c)
    R = 5; win = confl[r - R:r + R + 1, c - R:c + R + 1]
    if win.any():
        cand = np.argwhere(win); best = cand[np.argmax([accg[r - R + a, c - R + b] for a, b in cand])]
        rs, cs = r - R + best[0], c - R + best[1]; snapped_conf += 1
    else:
        win = accg[r - 3:r + 4, c - 3:c + 4]; k = np.unravel_index(np.argmax(win), win.shape); rs, cs = r - 3 + k[0], c - 3 + k[1]
    bp[name] = rs * W + cs; stream[rs, cs] = True
log("break points:", len(bp), "Basin 1 junctions;", snapped_conf, "snapped onto a confluence cell")

# ---------- stream graph ----------
smask = stream.ravel(); scells = np.flatnonzero(smask).astype(np.int32)
@nb.njit(cache=True)
def compute_nxt(scells, ds, smask):
    nxt = np.full(ds.size, -1, np.int32)
    for s in scells:
        c = ds[s]
        while c >= 0 and not smask[c]: c = ds[c]
        nxt[s] = c
    return nxt
nxt = compute_nxt(scells, ds, smask)
indeg = np.zeros(H * W, np.int32); np.add.at(indeg, nxt[scells][nxt[scells] >= 0], 1)
is_node = np.zeros(H * W, np.bool_)
chflat = ch_cells.ravel()
conf = scells[indeg[scells] >= 2]
# RULE (2026-10-05): walls are catchment boundaries -> a junction (culvert) wherever a channel chain passes through a
# wall line; no junctions at confluences inside a compartment, so one subbasin per wall-closed compartment
from shapely.geometry import LineString as _LS
from shapely.strtree import STRtree as _STR
_wall = gpd.read_file(P + "WALL.shp").geometry
_tree = _STR(list(_wall.values))
culvert = np.zeros(H * W, np.bool_); ncross = 0
for c in np.flatnonzero(chflat & (nxt >= 0)).tolist():
    d = int(nxt[c]); seg = _LS([(xs_[c % W], ys_[c // W]), (xs_[d % W], ys_[d // W])])
    hits = _tree.query(seg)
    if len(hits) and any(_wall.iloc[h].intersects(seg) for h in hits):
        culvert[d] = True; ncross += 1
is_node[culvert] = True
log("channel/wall crossings made junctions (culverts):", int(culvert.sum()), "from", ncross, "crossing arcs")
for n, i in bp.items(): is_node[i] = True
# a confluence that receives a reach (any inflowing branch has a node upstream) must also be a junction
@nb.njit(cache=True)
def reach_cells(scells, nxt, is_node):
    rc = np.zeros(nxt.size, np.bool_)
    for s in scells:
        if not is_node[s]: continue
        c = nxt[s]
        while c >= 0 and not rc[c]:
            rc[c] = True; c = nxt[c]
    return rc
rc_ = reach_cells(scells, nxt, is_node)
reach_in = np.zeros(H * W, np.bool_); src = scells[(nxt[scells] >= 0) & rc_[scells]]; reach_in[nxt[src]] = True
# an inflowing branch "carries a reach" if the inflowing cell itself is a reach cell or a node
node_in = np.zeros(H * W, np.bool_); src2 = scells[(nxt[scells] >= 0) & (rc_[scells] | is_node[scells])]; node_in[nxt[src2]] = True
added = conf[node_in[conf] & ~is_node[conf]]; is_node[added] = True
reach_inflows = np.zeros(H * W, np.int32); np.add.at(reach_inflows, nxt[src2], 1)
log("confluences receiving a reach made junctions:", len(added))
log("confluence nodes on channels:", int(is_node.sum()) - len(bp))
# merge nodes that sit within MERGE_M of the next node downstream (stream distance) into that downstream node
MERGE_M = 100.0
def _step(a, b): return 10.0 if (abs(a // W - b // W) + abs(a % W - b % W)) == 1 else 10 * 2 ** 0.5
bpcells = set(int(i) for i in bp.values()); merged = 0
for _ in range(5):
    changed = False
    for c in np.flatnonzero(is_node).tolist():
        if c in bpcells or reach_inflows[c] >= 2 or culvert[c]: continue   # never merge away a dam, a reach join or a culvert
        d = 0.0; k = int(nxt[c]); prev = c
        while k >= 0 and d <= MERGE_M and not is_node[k]: d += _step(prev, k); prev = k; k = int(nxt[k])
        if k >= 0 and is_node[k] and d + _step(prev, k) <= MERGE_M: is_node[c] = False; changed = True; merged += 1
    if not changed: break
log("nodes merged into a node within", MERGE_M, "m downstream:", merged)

@nb.njit(cache=True)
def link_labels(scells, nxt, is_node):
    lab = np.full(nxt.size, -1, np.int32); buf = np.empty(4000000, np.int32)
    for s in scells:
        if lab[s] >= 0: continue
        k = 0; c = s
        while True:
            if lab[c] >= 0: L = lab[c]; break
            buf[k] = c; k += 1; n = nxt[c]
            if n < 0 or is_node[n]: L = c; break
            c = n
        for p in range(k): lab[buf[p]] = L
    return lab
lab = link_labels(scells, nxt, is_node); links = np.unique(lab[scells]); log("links", len(links), "nodes", is_node.sum())

# ---------- subbasin labels ----------
@nb.njit(cache=True)
def basin_labels(ds, smask, lab, validf):
    n = ds.size; sub = np.full(n, -1, np.int32); buf = np.empty(4000000, np.int32)
    for i in range(n):
        if not validf[i]: sub[i] = -3; continue
        if sub[i] >= 0 or sub[i] == -2: continue
        k = 0; c = i
        while True:
            if sub[c] >= 0 or sub[c] == -2: L = sub[c]; break
            if smask[c]: L = lab[c]; sub[c] = L; break
            buf[k] = c; k += 1; c = ds[c]
            if c < 0: L = -2; break
        for p in range(k): sub[buf[p]] = L
    return sub
sub = basin_labels(ds, smask, lab, valid.ravel()); log("subbasin labels; valid cells draining out without a stream:", (sub == -2).sum())
# single-part subbasins: cells of a label that are not in its largest connected component go to the neighbouring label
from skimage.measure import label as sklabel
from scipy import ndimage as ndi
_sub2 = sub.reshape(H, W); _img = np.where(_sub2 >= 0, _sub2 + 1, 0).astype(np.int32)
comp = sklabel(_img, connectivity=1, background=0); ncomp = comp.max()
csize = np.bincount(comp.ravel(), minlength=ncomp + 1); cval = np.zeros(ncomp + 1, np.int64)
flat_c = comp.ravel(); nz = flat_c > 0; cval[flat_c[nz]] = _img.ravel()[nz]
best = {}
for cid in range(1, ncomp + 1):
    v = cval[cid]
    if v not in best or csize[cid] > csize[best[v]]: best[v] = cid
small = [cid for cid in range(1, ncomp + 1) if best[cval[cid]] != cid]
objs = ndi.find_objects(comp); moved = 0
for cid in small:
    sl = objs[cid - 1]
    if sl is None: continue
    r0, r1 = max(sl[0].start - 1, 0), min(sl[0].stop + 1, H); c0, c1 = max(sl[1].start - 1, 0), min(sl[1].stop + 1, W)
    m = comp[r0:r1, c0:c1] == cid; ring = ndi.binary_dilation(m) & ~m
    nb_ = _img[r0:r1, c0:c1][ring]; nb_ = nb_[(nb_ > 0) & (nb_ != cval[cid])]
    if nb_.size == 0: continue
    newv = np.bincount(nb_).argmax(); _sub2[r0:r1, c0:c1][m] = newv - 1; moved += 1
sub = _sub2.ravel(); log("multi-part clean-up: components reassigned", moved, "of", len(small), "small parts")

# ---------- longest flow path restricted to subbasin ----------
@nb.njit(cache=True)
def flow_lengths(ds, sub, order, W):
    n = ds.size; U = np.zeros(n, np.float32); pred = np.full(n, -1, np.int32)
    for k in range(n):
        i = order[k]; j = ds[i]
        if j < 0 or sub[i] < 0 or sub[j] != sub[i]: continue
        di = abs(i // W - j // W) + abs(i % W - j % W); step = 10.0 if di == 1 else 14.142136
        cand = U[i] + step
        if cand > U[j]: U[j] = cand; pred[j] = i
    return U, pred
U, pred = flow_lengths(ds, sub, order, W); log("flow lengths")

# ---------- CN grid resampled to 10 m ----------
cn = np.full((H, W), 255, np.uint8)
with rasterio.open(HMS + "Hydrology Data/CN_Include_Hill_Area.tif") as s:
    reproject(rasterio.band(s, 1), cn, dst_transform=tr, dst_crs=crs, resampling=Resampling.nearest, dst_nodata=255)
cnv = (cn != 127) & (cn != 255) & (cn > 0); log("CN resampled; valid", cnv.sum())

# ---------- per-link aggregation ----------
def step(a, b): return 10.0 if (abs(a // W - b // W) + abs(a % W - b % W)) == 1 else DIAG
xs = (np.arange(W) + 0.5) * tr.a + tr.c; ys = (np.arange(H) + 0.5) * tr.e + tr.f
pos = np.searchsorted(links, sub); ok = (sub >= 0) & (pos < len(links)); ok[ok] &= (links[pos[ok]] == sub[ok])
idx = np.where(ok, pos, -1).astype(np.int32)
sel = idx >= 0; ii = idx[sel]
cnt_cells = np.bincount(ii, minlength=len(links))
rr, cc = np.divmod(np.arange(H * W), W)
sumx = np.bincount(ii, weights=xs[cc[sel]], minlength=len(links)); sumy = np.bincount(ii, weights=ys[rr[sel]], minlength=len(links))
cnm = cnv.ravel() & sel
cnsum = np.bincount(idx[cnm], weights=cn.ravel()[cnm].astype(float), minlength=len(links)); cncnt = np.bincount(idx[cnm], minlength=len(links))
elr = el.ravel(); chr_ = ch_line.ravel()
labcells = {}
for s in scells.tolist(): labcells.setdefault(int(lab[s]), []).append(s)
rows = []; paths = {}
for i, L in enumerate(links):
    L = int(L); cells = labcells[L]; heads = [c for c in cells if is_node[c]]
    if len(heads) > 1:
        print("   WARNING: link", L, "contains", len(heads), "nodes:", heads)
        for hn in heads:
            c = int(nxt[hn]); k = 0
            while c >= 0 and k < 100000:
                if indeg[c] >= 2 or is_node[c]:
                    print(f"      from node {hn}: confluence/node cell {c} at {xs[c % W]:.0f},{ys[c // W]:.0f} indeg={int(indeg[c])} is_node={bool(is_node[c])} rc={bool(rc_[c])} node_in={bool(node_in[c])} lab={int(lab[c])} in_conf={c in set(conf.tolist())}")
                    if is_node[c]: break
                c = int(nxt[c]); k += 1
    head = heads[0] if heads else -1
    down = int(nxt[L]); area = cnt_cells[i] * 100 / 1e6
    Ltot = float(U[L]) + (step(L, down) if down >= 0 else 0.0)
    path = [L]; c = L
    while pred[c] >= 0: c = int(pred[c]); path.append(c)
    path = path[::-1]
    d = np.zeros(len(path))
    for k in range(1, len(path)): d[k] = d[k - 1] + step(path[k - 1], path[k])
    dfo = Ltot - d
    z = elr[path].astype(float)
    def zat(frac):
        target = frac * Ltot; k = int(np.searchsorted(-dfo, -target)); k = min(max(k, 1), len(path) - 1)
        d1, d0 = dfo[k - 1], dfo[k]
        return z[k] if d1 == d0 else z[k] + (z[k - 1] - z[k]) * (target - d0) / (d1 - d0)
    z10, z85 = (zat(0.10), zat(0.85)) if len(path) > 1 else (z[0], z[0])
    L1085 = 0.75 * Ltot; S1085 = (z85 - z10) / L1085 if L1085 > 0 else np.nan
    rlen = np.nan; rslope = np.nan
    if head >= 0:
        c = head; rlen = 0.0
        while c != down and c >= 0:
            n_ = int(nxt[c]); rlen += step(c, n_) if n_ >= 0 else 0; c = n_
        rslope = (float(elr[head]) - float(elr[down])) / rlen if (down >= 0 and rlen > 0) else np.nan
    chids = chr_[np.array(cells)]; chid = int(np.bincount(chids[chids > 0]).argmax()) if (chids > 0).any() else 0
    cnmean = cnsum[i] / cncnt[i] if cncnt[i] > 0 else np.nan
    paths[L] = path
    rows.append(dict(label=L, head=head, down=down, cells=int(cnt_cells[i]), area_km2=area, cx=sumx[i] / cnt_cells[i], cy=sumy[i] / cnt_cells[i],
                     CN=cnmean, Lfp_m=Ltot, L1085_m=L1085, z10=z10, z85=z85, S1085=S1085, reach_len_m=rlen, reach_slope=rslope,
                     ch_feat=chid - 1 if chid else -1, ch_type=(chan.loc[chid - 1, "CHtt"] if chid else ""), is_outlet=down < 0,
                     outlet_x=xs[L % W], outlet_y=ys[L // W]))
df = pd.DataFrame(rows); log("links table (all)", len(df), "total area km2", round(df.area_km2.sum(), 1))
# integrity: every node that receives a link must be the head of exactly one link, unless it drains straight to nodata
heads = set(int(h) for h in df["head"] if h >= 0); downs = set(int(d) for d in df.down if d >= 0)
for c in sorted(downs - heads):
    print(f"   NODE WITHOUT DOWNSTREAM LINK: cell {c} at {xs[c % W]:.0f},{ys[c // W]:.0f}  nxt={int(nxt[c])} lab={int(lab[c])} is_node={bool(is_node[c])} acc_km2={acc[c]*100/1e6:.2f} inflow links={int((df.down == c).sum())}")
    L = int(lab[c]); rr = df[df.label == L]
    print("      link row for that label:", rr[["label", "head", "down", "cells", "area_km2"]].to_dict("records"), "| node in labcells:", c in labcells.get(L, []), "| nodes in link:", [int(x) for x in labcells.get(L, []) if is_node[x]][:5], "| is_node[nxt]:", bool(is_node[int(nxt[c])]) if nxt[c] >= 0 else None)
chr_flat = ch_id.ravel(); bpset = set(int(i) for i in bp.values())
def keep(L):
    c = int(L); n = 0
    while c >= 0 and n < 1000000:
        if chr_flat[c] > 0 or c in bpset: return True
        c = int(nxt[c]); n += 1
    return False
if USE_CH:
    df = df[df.label.map(keep)].reset_index(drop=True)
else:
    df = df[df.label.map(keep)].reset_index(drop=True)
log("links kept", len(df), "total area km2", round(df.area_km2.sum(), 1))

# ---------- names ----------
node_cells = sorted(set(int(r.down) for r in df.itertuples() if r.down >= 0))
node_name = {int(i): n for n, i in bp.items()}
# name persistence: reuse the junction/outlet names of the previous build for the same (or neighbouring) cell
PREV = "D:/Mojtaba/Renardet/2224 WS11/Batinah/Block 4/Claude Block 04/W2/output/nodes.json"
prev = json.load(open(PREV)) if os.path.exists(PREV) else {"node_name": {}}
prev_j = {int(k): v for k, v in prev["node_name"].items() if not k.startswith("(") and not v.startswith("Outlet")}
prev_o = {int(k.split(",")[1].strip(" )")): v for k, v in prev["node_name"].items() if k.startswith("(")}
used = set(node_name.values()); reused = 0
def near(cell, table, rad=3):
    r0, c0 = cell // W, cell % W; best = None
    for cc, nm in table.items():
        if abs(cc // W - r0) <= rad and abs(cc % W - c0) <= rad and nm not in used:
            d = abs(cc // W - r0) + abs(cc % W - c0)
            if best is None or d < best[0]: best = (d, nm)
    return best[1] if best else None
jnums = [int(v[1:]) for v in prev_j.values() if v[1:].isdigit()]; j = max(jnums + [100]) + 1
for c in sorted(node_cells, key=lambda c: int(acc[c])):
    if c in node_name: continue
    nm = near(c, prev_j)
    if nm: node_name[c] = nm; used.add(nm); reused += 1
    else: node_name[c] = f"J{j}"; used.add(f"J{j}"); j += 1
onums = [int(v.split()[1]) for v in prev_o.values()]; o = max(onums + [0]) + 1
for r in df[df.is_outlet].sort_values("area_km2", ascending=False).itertuples():
    nm = near(int(r.label), prev_o)
    if nm: node_name[("out", int(r.label))] = nm; used.add(nm); reused += 1
    else: node_name[("out", int(r.label))] = f"Outlet {o}" + (f" {r.ch_type} {r.ch_feat}" if r.ch_feat >= 0 else ""); o += 1
log("junction/outlet names reused from previous build:", reused)
df = df.sort_values("area_km2", ascending=False).reset_index(drop=True)
df["sub"] = [f"S{i+1}" for i in range(len(df))]
df["junction"] = [node_name[int(r.down)] if r.down >= 0 else node_name[("out", int(r.label))] for r in df.itertuples()]
df["head_junction"] = [node_name.get(int(r.head), "") if r.head >= 0 else "" for r in df.itertuples()]
df["reach"] = ""; k = 1
for i, r in df.iterrows():
    if r["head"] >= 0: df.loc[i, "reach"] = f"R{k}"; k += 1
df["Ia_mm"] = 0.2 * 25.4 * (1000 / df.CN - 10)
df["S_used"] = df.S1085.clip(lower=0.0005)
df["Lag_min"] = 0.6 * (1 / 52) * np.power(df.L1085_m, 0.77) / np.power(df.S_used, 0.385)
df.to_csv(OUT + "links.csv", index=False)

# ---------- dam catchment comparison ----------
blocks = re.findall(r'^(Subbasin|Junction|Reach): (.+?)\n(.*?)^End:', txt, re.S | re.M)
def g(b, k):
    m = re.search(r'^\s*' + re.escape(k) + r': (.*)$', b, re.M); return m.group(1).strip() if m else None
el_ = {nm: (t, g(b, "Downstream"), float(g(b, "Area") or 0)) for t, nm, b in blocks}
def ua(n): return sum((ua(m) + el_[m][2]) if el_[m][0] == "Subbasin" else ua(m) for m in el_ if el_[m][1] == n)
with rasterio.open(T + "flowaccum.tif") as s: fa1 = s.read(1)
cmp = []
for n in DAMS:
    i = bp[n]; mine = acc[i] * 100 / 1e6
    x, y = J1[n]; c, r = ~tr * (x, y); r, c = int(r), int(c); b1 = fa1[r - 3:r + 4, c - 3:c + 4].max() * 100 / 1e6
    cmp.append(dict(dam=n, basin1_topology=round(ua(n), 3), basin1_grid=round(float(b1), 3), new=round(float(mine), 3), diff_vs_grid=round(float(mine - b1), 3)))
cmp = pd.DataFrame(cmp); print(cmp.to_string(index=False)); cmp.to_csv(OUT + "dam_catchment_comparison.csv", index=False)

# ---------- GIS review layers ----------
subr = np.where(idx >= 0, idx + 1, 0).astype(np.int32).reshape(H, W)
polys = [dict(geometry=shape(geom), lid=int(val) - 1) for geom, val in shapes(subr, mask=subr > 0, transform=tr, connectivity=8)]
gp = gpd.GeoDataFrame(polys, crs=crs).dissolve("lid").reset_index()
gp["label"] = gp.lid.map(lambda i: int(links[i])); gp = gp.drop(columns="lid").merge(df, on="label", how="left")
gp.to_file(OUT + "review.gpkg", layer="subbasins", driver="GPKG")
lines = []
for r in df.itertuples():
    cells = labcells[int(r.label)]
    if r.head >= 0: start = int(r.head)
    else:
        preds = set(int(nxt[c]) for c in cells if nxt[c] >= 0); starts = [c for c in cells if c not in preds]; start = starts[0] if starts else cells[0]
    pts = []; c = start; seen = set()
    while c >= 0 and c not in seen and lab[c] == r.label: pts.append((xs[c % W], ys[c // W])); seen.add(c); c = int(nxt[c])
    if c >= 0: pts.append((xs[c % W], ys[c // W]))
    if len(pts) > 1: lines.append(dict(geometry=LineString(pts), sub=r.sub, reach=r.reach, junction=r.junction, head_junction=r.head_junction, ch_type=r.ch_type, ch_feat=r.ch_feat, area_km2=r.area_km2, reach_len_m=r.reach_len_m, reach_slope=r.reach_slope))
gpd.GeoDataFrame(lines, crs=crs).to_file(OUT + "review.gpkg", layer="links", driver="GPKG")
lfp = [dict(geometry=LineString([(xs[c % W], ys[c // W], float(elr[c])) for c in paths[int(r.label)]]), sub=r.sub, Lfp_m=r.Lfp_m, S1085=r.S1085) for r in df.itertuples() if len(paths[int(r.label)]) > 1]
gpd.GeoDataFrame(lfp, crs=crs).to_file(OUT + "review.gpkg", layer="longest_flowpath", driver="GPKG")
pts = [dict(geometry=Point(xs[c % W], ys[c // W]), name=nm, acc_km2=acc[c] * 100 / 1e6, kind="junction") for c, nm in node_name.items() if not isinstance(c, tuple)]
pts += [dict(geometry=Point(xs[L % W], ys[L // W]), name=nm, acc_km2=acc[L] * 100 / 1e6, kind="outlet") for (tag, L), nm in [(k, v) for k, v in node_name.items() if isinstance(k, tuple)]]
gpd.GeoDataFrame(pts, crs=crs).to_file(OUT + "review.gpkg", layer="junctions", driver="GPKG")
json.dump({"node_name": {str(k): v for k, v in node_name.items()}, "bp": {n: int(i) for n, i in bp.items()}, "W": W, "H": H,
           "culvert_junctions": [v for k, v in node_name.items() if not isinstance(k, tuple) and culvert[int(k)]]}, open(OUT + "nodes.json", "w"))
log("done")
