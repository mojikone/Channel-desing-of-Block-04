"""Step 35 - peak flow and volume of the Basin 5 elements at their own depth-area analysis point, all return periods
(the method of scripts/extract_b2.py: C-part FLOW, F-part suffix == element, peak = max, volume = sum x 300 s / 1e6 Mm3).
Writes hms/basin5_peak_flow_volume_long.csv and hms/basin5_peak_flow_volume.csv (wide)."""
import os, re, pandas as pd, hecdss
HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE)
HMS = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydrology\HEC_HMS_Block_04"; OUT = os.path.join(W6, "hms")
RPS = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr", "1000yr", "2000yr", "5000yr", "10000yr", "PMP"]
txt = open(os.path.join(HMS, "Basin_5.basin"), encoding="utf-8").read()
kind = {n: t for t, n in re.findall(r'^(Subbasin|Junction|Reach|Reservoir): (.+?)$', txt, re.M)}
rows = []
for rp in RPS:
    f = os.path.join(HMS, "DA_%s_B5.dss" % rp)
    if not os.path.exists(f): print("missing", f); continue
    dss = hecdss.HecDss(f); seen = set()
    for p in [str(x) for x in dss.get_catalog()]:
        parts = p.split("/")
        if len(parts) < 7: continue
        b, c, fpart = parts[2], parts[3], parts[6]; own = fpart.split(">")[-1] if ">" in fpart else ""
        if c != "FLOW" or own != b or b in seen: continue
        vals = list(dss.get(p).values); seen.add(b)
        rows.append(dict(element=b, type=kind.get(b, "?"), rp=rp, peak_m3s=max(vals), vol_Mm3=sum(vals) * 300 / 1e6))
    dss.close(); print(rp, "elements:", sorted(seen))
df = pd.DataFrame(rows); df["rp"] = pd.Categorical(df.rp, RPS, ordered=True)
df.to_csv(os.path.join(OUT, "basin5_peak_flow_volume_long.csv"), index=False)
pk = df.pivot(index="element", columns="rp", values="peak_m3s").round(2); vol = df.pivot(index="element", columns="rp", values="vol_Mm3").round(4)
pd.concat({"peak_m3s": pk, "vol_Mm3": vol}, axis=1).to_csv(os.path.join(OUT, "basin5_peak_flow_volume.csv"))
print(pk.to_string()); print(vol.to_string())
