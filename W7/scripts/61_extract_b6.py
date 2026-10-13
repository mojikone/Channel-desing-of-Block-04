"""Step 61 (W7) - peak flow and volume of every Basin 6 element at its own depth-area analysis point, 13 return periods, by the
method of scripts/extract_b2.py (own analysis point: F-part suffix == B-part, C-part FLOW, peak = max, volume = sum x 300 s / 1e6
Mm3). Writes results/basin6_peak_flow_volume_long.csv and basin6_peak_flow_volume.xlsx (the project's results folder, beside the
Basin 2 and 3 files the report reads) and copies both into W7/hms/. Then the check that matters: every element OFF the Shafan
line below the dam must keep its Basin 3 peak (the fix of step 60 moved 10 km2 into the dam, nothing else), reported in
W7/hms/61_basin6_vs_basin3.csv with the elements that changed.
    python 61_extract_b6.py"""
import os, re, pandas as pd, hecdss, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__)); W7 = os.path.dirname(HERE); CB = os.path.dirname(W7)
HMS = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydrology\HEC_HMS_Block_04"
RES = os.path.join(CB, "results"); OUT = os.path.join(W7, "hms"); os.makedirs(OUT, exist_ok=True)
RPS = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr", "1000yr", "2000yr", "5000yr", "10000yr", "PMP"]
SUF = "B6"
txt = open(os.path.join(HMS, "Basin_6.basin"), encoding="utf-8").read()
kind = {n: t for t, n in re.findall(r'^(Subbasin|Junction|Reach|Reservoir): (.+?)$', txt, re.M)}
rows = []
for rp in RPS:
    f = os.path.join(HMS, "DA_%s_%s.dss" % (rp, SUF))
    if not os.path.exists(f): print("missing", f); continue
    with contextlib.redirect_stdout(io.StringIO()):     # hecdss floods stdout with its own log
        dss = hecdss.HecDss(f); seen = set()
        for p in [str(x) for x in dss.get_catalog()]:
            parts = p.split("/")
            if len(parts) < 7: continue
            b, c, fpart = parts[2], parts[3], parts[6]
            own = fpart.split(">")[-1] if ">" in fpart else ""
            if c != "FLOW" or own != b or b in seen: continue
            vals = list(dss.get(p).values); seen.add(b)
            rows.append(dict(element=b, type=kind.get(b, "?"), rp=rp, peak_m3s=max(vals), vol_Mm3=sum(vals) * 300 / 1e6))
        dss.close()
    print(rp, "elements:", len(seen))
df = pd.DataFrame(rows); df["rp"] = pd.Categorical(df.rp, RPS, ordered=True)
df.to_csv(os.path.join(RES, "basin6_peak_flow_volume_long.csv"), index=False)
pk = df.pivot(index="element", columns="rp", values="peak_m3s").round(1); vol = df.pivot(index="element", columns="rp", values="vol_Mm3").round(3)
pk.insert(0, "type", pk.index.map(kind)); vol.insert(0, "type", vol.index.map(kind))
def skey(n):
    m = re.match(r"^([A-Z]{3})-([SJRO])(\d+)$", n); return (m.group(1), "SJRO".index(m.group(2)), int(m.group(3))) if m else ("ZZZ", 9, 0)
pk = pk.loc[sorted(pk.index, key=skey)]; vol = vol.loc[sorted(vol.index, key=skey)]
xl = os.path.join(RES, "basin6_peak_flow_volume.xlsx")
with pd.ExcelWriter(xl) as xw:
    pk.to_excel(xw, sheet_name="peak flow m3s"); vol.to_excel(xw, sheet_name="volume Mm3")
    pk[pk.type == "Reach"].to_excel(xw, sheet_name="reaches Q"); pk[pk.type == "Junction"].to_excel(xw, sheet_name="junctions Q")
    if (pk.type == "Reservoir").any(): pk[pk.type == "Reservoir"].to_excel(xw, sheet_name="reservoir outflow Q")
print("written", xl, "| elements:", pk.shape[0], "| rps:", df.rp.nunique())
import shutil
for f in ("basin6_peak_flow_volume_long.csv", "basin6_peak_flow_volume.xlsx"): shutil.copy2(os.path.join(RES, f), os.path.join(OUT, f))

# ---- Basin 6 against Basin 3: which elements changed, and are they all on the Shafan line below the dam?
b3 = pd.read_csv(os.path.join(RES, "basin3_peak_flow_volume_long.csv"))
m = df.merge(b3, on=["element", "rp"], suffixes=("_b6", "_b3"), how="outer", indicator=True)
m["d_pct"] = 100 * (m.peak_m3s_b6 / m.peak_m3s_b3 - 1)
chg = m[(m._merge == "both") & (m.d_pct.abs() > 0.5)]
only6 = sorted(set(m[m._merge == "left_only"].element)); only3 = sorted(set(m[m._merge == "right_only"].element))
chain = []
down = {n: (re.search(r"\n\s*Downstream: (.+)", body) or [None, None])[1] for k, n, body in re.findall(r"^(Subbasin|Junction|Reach|Reservoir|Sink): (.+?)\r?\n(.*?)^End:", txt, re.S | re.M)}
n = "Shafan 08 Reservoir"
while n: chain.append(n); n = (down.get(n) or "").strip() or None
chain_set = set(chain) | {"SHA-S23", "SHA-S44", "SHA-S46", "SHA-R18", "SHA-J20", "Shafan 08 site"}
off = sorted(set(chg.element) - chain_set)
rep = chg[["element", "type_b6", "rp", "peak_m3s_b3", "peak_m3s_b6", "d_pct"]].rename(columns={"type_b6": "type"}).sort_values(["element", "rp"])
rep.to_csv(os.path.join(OUT, "61_basin6_vs_basin3.csv"), index=False)
print("elements only in Basin 6:", only6, "| only in Basin 3:", only3)
print("elements whose peak changed by more than 0.5 %% in any return period: %d -> %s" % (len(set(chg.element)), sorted(set(chg.element), key=skey)))
print("of these OFF the Shafan line and the three fixed subbasins:", off if off else "none (as expected)")
k = m[(m.rp == "200yr") & m.element.isin(["SHA-J42", "SHA-J45", "SHA-J47", "SHA-J48", "SHA-J49", "SHA-J51", "SHA-O5", "Shafan 08 site", "Shafan 08 Reservoir"])]
print(k[["element", "peak_m3s_b3", "peak_m3s_b6", "d_pct"]].round(1).to_string(index=False))
