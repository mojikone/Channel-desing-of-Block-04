"""Size the channel reaches of Basin 2 for the 200-year depth-area flow: trapezoid, n 0.1, side slope 1V:3H,
bottom width such that normal depth = 2 m at Q200 (engineer's rule, 2026-10-05). Natural plain reaches keep their DEM sections.
usage: python size_reaches.py <HMS project folder> <W2 output/hms folder> [--apply]
"""
import sys, re, os, math, shutil, datetime
import pandas as pd, hecdss
HMS = sys.argv[1].rstrip("/\\") + "/"; W2 = sys.argv[2].rstrip("/\\") + "/"; APPLY = "--apply" in sys.argv
SUF = next((a for a in sys.argv[3:] if a in ("B2", "B3")), "B2"); BASIN = "Basin_3.basin" if SUF == "B3" else "Basin_2.basin"
N_MANNING, DEPTH, Z = 0.10, 2.0, 3.0
# ---- peak flows at every element's own analysis point in the 200-yr Basin 2 depth-area results ----
dss = hecdss.HecDss(HMS + f"DA_200yr_{SUF}.dss")
cat = dss.get_catalog(); paths = [str(p) for p in cat]
peaks = {}   # (element, cpart) -> peak
for p in paths:
    parts = p.split("/")
    if len(parts) < 7: continue
    b, c, f = parts[2], parts[3], parts[6]
    own = f.split(">")[-1] if ">" in f else ""
    if own != b or c not in ("FLOW", "FLOW-COMBINE"): continue      # outflow and combined inflow only (not the cumulative volume series)
    if (b, c) in peaks: continue
    ts = dss.get(p); vals = list(ts.values)
    if vals: peaks[(b, c)] = max(vals)
dss.close()
els = sorted(set(b for b, c in peaks)); cparts = sorted(set(c for b, c in peaks))
print("elements with own-point flow:", len(els), "| C-parts:", cparts)
# ---- reaches of Basin 2 ----
txt = open(HMS + BASIN, encoding="utf-8").read()
g = lambda s, k: (re.search(r'^\s*' + re.escape(k) + r': (.*)$', s, re.M) or [None, None])[1]
reaches = {n: s for n, s in re.findall(r'^Reach: (.+?)\n(.*?)^End:', txt, re.S | re.M)}
geo = pd.read_csv(W2 + "Basin_2_reach_geometry_and_sections.csv") if os.path.exists(W2 + "Basin_2_reach_geometry_and_sections.csv") else None
el = pd.read_csv(W2 + "Basin_2_new_elements.csv"); el["R"] = el.R.fillna(""); el["ch_type"] = el.ch_type.fillna("")
chan_R = set(el.R[(el.R != "") & (el.ch_type != "")])          # reaches that follow a designed channel
def manning_Q(b, y, S):
    A = (b + Z * y) * y; P = b + 2 * y * math.sqrt(1 + Z * Z); R = A / P
    return A * R ** (2 / 3) * math.sqrt(S) / N_MANNING
def width_for(Q, S, y=DEPTH):
    lo, hi = 0.0, 6000.0
    if manning_Q(lo, y, S) >= Q: return 0.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if manning_Q(mid, y, S) < Q: lo = mid
        else: hi = mid
    return hi
rows = []
for n, s in reaches.items():
    S = float(g(s, "Energy Slope")); L = float(g(s, "Length")); b0 = float(g(s, "Bottom Width")); z0 = float(g(s, "Side Slope")); n0 = float(g(s, "Mannings n"))
    q = max([v for (e, c), v in peaks.items() if e == n] or [float("nan")])
    kind = "channel" if n in chan_R else ("Basin 1" if re.match(r"^(HAW|SHA|SAR|SAK)-R\d+$", n) and n0 == 0.1 and b0 in (90.0, 500.0) else "natural/other")
    b_new = width_for(q, S) if (kind == "channel" and q == q) else None
    if b_new is not None: b_new = max(round(b_new, 1), 2.0)
    rows.append(dict(reach=n, kind=kind, Q200_m3s=round(q, 1) if q == q else None, slope=S, length_m=L, b_old=b0, z_old=z0, n_old=n0,
                     b_new=b_new, z_new=Z if b_new is not None else z0, n_new=N_MANNING, depth_at_Q200=DEPTH if b_new is not None else None))
df = pd.DataFrame(rows); df.to_csv(W2 + BASIN.replace(".basin", "_reach_sizing_Q200.csv"), index=False)
ch = df[df.kind == "channel"]
print(f"channel reaches sized: {len(ch)} | Q200 range {ch.Q200_m3s.min()}-{ch.Q200_m3s.max()} m3/s | bottom width range {ch.b_new.min()}-{ch.b_new.max()} m | at minimum 2 m: {(ch.b_new <= 2.0).sum()}")
print(ch.sort_values("Q200_m3s", ascending=False).head(12)[["reach", "Q200_m3s", "slope", "b_old", "b_new"]].to_string(index=False))
if APPLY:
    now = datetime.datetime.now(); shutil.copy2(HMS + BASIN, HMS + BASIN.replace(".basin", f"_before_sizing_{now:%Y%m%d_%H%M}.basin.bak"))
    for r in ch.itertuples():
        blk = re.search(r'^Reach: ' + re.escape(r.reach) + r'\n.*?^End:', txt, re.S | re.M).group(0)
        b2 = re.sub(r'^(\s*Bottom Width: ).*$', lambda m: m.group(1) + f"{r.b_new:g}", blk, flags=re.M)
        b2 = re.sub(r'^(\s*Side Slope: ).*$', lambda m: m.group(1) + f"{Z:g}", b2, flags=re.M)
        b2 = re.sub(r'^(\s*Mannings n: ).*$', lambda m: m.group(1) + f"{N_MANNING:g}", b2, flags=re.M)
        txt = txt.replace(blk, b2)
    open(HMS + BASIN, "w", encoding="utf-8", newline="\n").write(txt); shutil.copy2(HMS + BASIN, W2 + BASIN)
    print(BASIN, "updated (channel reaches) and copied to W2")
