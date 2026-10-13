"""Step 01 - the eight reservoirs' 5-minute series from the 13 Basin 3 depth-area analyses.

At each reservoir's OWN analysis point (F-part '...>name' == B-part):
  inflow    = FLOW-COMBINE  (= the dam junction flow, identical to Basin 1/2 within 0.1 %)
  outflow   = FLOW          (spillway + overtopping)
  elevation = ELEVATION     (m)
  storage   = STORAGE       (HMS metric: 1000 m3)
Writes W3/dams/data/hydrographs_5min_B3.csv  (time_h, dam, rp, inflow_m3s, outflow_m3s, elevation_m, storage_1000m3)
       W3/dams/data/dam_summary_B3.csv       (per dam x rp: peaks, volumes, peak level, attenuation, time to peak)
"""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd, hecdss
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DAMS, DAMS9, RPS, DT_S, suffix_dss, own_point, ensure, W3
BASIN = next((a for a in sys.argv[1:] if a in ("B3", "B4")), "B3"); DAMSET = DAMS9 if BASIN == "B4" else DAMS

OUT = ensure(W3 / "dams" / "data")
SERIES = {"inflow_m3s": "FLOW-COMBINE", "outflow_m3s": "FLOW", "elevation_m": "ELEVATION", "storage_1000m3": "STORAGE"}
rows, summ, units_seen = [], [], {}
t0 = time.time()
for rp in RPS:
    f = suffix_dss(rp, BASIN)
    if not f.exists(): print("MISSING", f); continue
    d = hecdss.HecDss(str(f))
    paths = [str(p) for p in d.get_catalog()]
    want = {(p.split("/")[2], p.split("/")[3]): p for p in paths if own_point(p) and p.split("/")[2].endswith(" Reservoir")}
    for dam in DAMSET:
        res = f"{dam} Reservoir"; data = {}
        for col, cpart in SERIES.items():
            p = want.get((res, cpart))
            if p is None: print("no path", rp, res, cpart); continue
            ts = d.get(p); v = np.asarray(ts.values, dtype=float); data[col] = v; units_seen[cpart] = getattr(ts, "units", "?")
        n = len(data["inflow_m3s"]); th = np.arange(n) * DT_S / 3600.0
        df = pd.DataFrame({"time_h": th, "dam": dam, "rp": rp, **{k: data[k] for k in SERIES}}); rows.append(df)
        qi, qo = data["inflow_m3s"], data["outflow_m3s"]
        summ.append(dict(dam=dam, rp=rp, n=n, peak_inflow_m3s=qi.max(), t_peak_in_h=th[qi.argmax()], peak_outflow_m3s=qo.max(), t_peak_out_h=th[qo.argmax()],
                         vol_in_Mm3=qi.sum() * DT_S / 1e6, vol_out_Mm3=qo.sum() * DT_S / 1e6, attenuation_pct=(1 - qo.max() / qi.max()) * 100 if qi.max() > 0 else np.nan,
                         peak_level_m=data["elevation_m"].max(), init_level_m=data["elevation_m"][0], peak_storage_Mm3=data["storage_1000m3"].max() / 1000.0))
    d.close(); print(rp, "done", f"{time.time() - t0:.0f} s")
H = pd.concat(rows, ignore_index=True); H.to_csv(OUT / f"hydrographs_5min_{BASIN}.csv", index=False, float_format="%.4f")
S = pd.DataFrame(summ); S.to_csv(OUT / f"dam_summary_{BASIN}.csv", index=False, float_format="%.4f")
print("units:", units_seen); print(S.pivot(index="dam", columns="rp", values="peak_inflow_m3s")[RPS].round(0).to_string())
print(S.pivot(index="dam", columns="rp", values="peak_outflow_m3s")[RPS].round(0).to_string())
print("written", OUT / f"hydrographs_5min_{BASIN}.csv", len(H), "rows")
