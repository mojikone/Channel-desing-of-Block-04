"""Peak flow and volume at every Basin 2 element's own depth-area analysis point, all return periods.
usage: python extract_b2.py <HMS project folder> <output folder>
Method as W1: own analysis point (B-part == F-part suffix), C-part FLOW, peak = max, volume = sum x 300 s / 1e6 Mm3.
"""
import sys, os, re, pandas as pd, hecdss
HMS = sys.argv[1].rstrip("/\\") + "/"; OUT = sys.argv[2].rstrip("/\\") + "/"; os.makedirs(OUT, exist_ok=True)
SUF = sys.argv[3] if len(sys.argv) > 3 else "B2"          # B2 = Basin 2 (no reservoirs), B3 = Basin 3 (with reservoirs)
RPS = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr", "1000yr", "2000yr", "5000yr", "10000yr", "PMP"]
txt = open(HMS + ("Basin_3.basin" if SUF == "B3" else "Basin_2.basin"), encoding="utf-8").read()
kind = {n: t for t, n in re.findall(r'^(Subbasin|Junction|Reach|Reservoir): (.+?)$', txt, re.M)}
g = lambda s, k: (re.search(r'^\s*' + re.escape(k) + r': (.*)$', s, re.M) or [None, None])[1]
area = {n: float(g(s, "Area")) for n, s in re.findall(r'^Subbasin: (.+?)\n(.*?)^End:', txt, re.S | re.M)}
rows = []
for rp in RPS:
    f = HMS + f"DA_{rp}_{SUF}.dss"
    if not os.path.exists(f): print("missing", f); continue
    dss = hecdss.HecDss(f); seen = set()
    for p in [str(x) for x in dss.get_catalog()]:
        parts = p.split("/")
        if len(parts) < 7: continue
        b, c, fpart = parts[2], parts[3], parts[6]
        own = fpart.split(">")[-1] if ">" in fpart else ""
        if c != "FLOW" or own != b or b in seen: continue
        vals = list(dss.get(p).values); seen.add(b)
        rows.append(dict(element=b, type=kind.get(b, "?"), rp=rp, peak_m3s=max(vals), vol_Mm3=sum(vals) * 300 / 1e6))
    dss.close(); print(rp, "elements:", len(seen))
df = pd.DataFrame(rows); df["rp"] = pd.Categorical(df.rp, RPS, ordered=True)
df.to_csv(OUT + f"basin{SUF[1]}_peak_flow_volume_long.csv", index=False)
pk = df.pivot(index="element", columns="rp", values="peak_m3s").round(1); vol = df.pivot(index="element", columns="rp", values="vol_Mm3").round(3)
pk.insert(0, "type", pk.index.map(kind)); vol.insert(0, "type", vol.index.map(kind))
def skey(n):
    m = re.match(r"^([A-Z]{3})-([SJRO])(\d+)$", n); return (m.group(1), "SJRO".index(m.group(2)), int(m.group(3))) if m else ("ZZZ", 9, 0)
pk = pk.loc[sorted(pk.index, key=skey)]; vol = vol.loc[sorted(vol.index, key=skey)]
with pd.ExcelWriter(OUT + f"basin{SUF[1]}_peak_flow_volume.xlsx") as xw:
    pk.to_excel(xw, sheet_name="peak flow m3s"); vol.to_excel(xw, sheet_name="volume Mm3")
    pk[pk.type == "Reach"].to_excel(xw, sheet_name="reaches Q"); pk[pk.type == "Junction"].to_excel(xw, sheet_name="junctions Q")
    if (pk.type == "Reservoir").any(): pk[pk.type == "Reservoir"].to_excel(xw, sheet_name="reservoir outflow Q")
print("written", OUT + f"basin{SUF[1]}_peak_flow_volume.xlsx", "| elements:", pk.shape[0], "| rps:", df.rp.nunique())
