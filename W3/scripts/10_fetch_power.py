"""Step 10 - NASA POWER (MERRA-2 reanalysis) climate record at each dam, as used in the Ibri concept design report.

  daily  2001-2024  T2M, T2M_MAX, T2M_MIN (deg C at 2 m), PRECTOTCORR (mm/day)      community AG
  hourly 2015-2024  WS10M (m/s), WD10M (deg, direction the wind blows FROM), local solar time   community RE
POWER is a ~0.5 x 0.625 degree grid, so neighbouring dams fall in the same cell; the cell centre returned by the API is
recorded per dam in climate/data/cells.csv. usage: python 10_fetch_power.py [dam name ...]   -> W3/climate/data/<dam>/
"""
import sys, csv, json, time, urllib.request
from pathlib import Path
from pyproj import Transformer
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DAMS, MODEL, W3, ensure
import basinfile as bf

BASE = "https://power.larc.nasa.gov/api/temporal"; OUT = ensure(W3 / "climate" / "data")
els = bf.parse(MODEL / "Basin_3.basin"); tf = Transformer.from_crs(32640, 4326, always_xy=True)

def get(url):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Renardet-2224-Block04-report/1.0"}), timeout=300) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("   retry", attempt + 1, str(e)[:80]); time.sleep(15)
    raise RuntimeError(url)

def daily(dam, lon, lat, y0=2001, y1=2024):
    d = get(f"{BASE}/daily/point?parameters=T2M,T2M_MAX,T2M_MIN,PRECTOTCORR&community=AG&longitude={lon:.4f}&latitude={lat:.4f}&start={y0}0101&end={y1}1231&format=JSON")
    p = d["properties"]["parameter"]; path = OUT / dam.replace(" ", "_") / f"power_daily_{y0}_{y1}.csv"; path.parent.mkdir(exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["date", "t_mean_c", "t_max_c", "t_min_c", "rain_mm"])
        for k in sorted(p["T2M"]): w.writerow([f"{k[:4]}-{k[4:6]}-{k[6:]}", p["T2M"][k], p["T2M_MAX"][k], p["T2M_MIN"][k], p["PRECTOTCORR"][k]])
    return d["geometry"]["coordinates"], len(p["T2M"])

def hourly(dam, lon, lat, y0=2015, y1=2024):
    path = OUT / dam.replace(" ", "_") / f"power_hourly_wind_{y0}_{y1}.csv"; n = 0
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["datetime_lst", "ws10m_ms", "wd10m_deg"])
        for y in range(y0, y1 + 1):
            d = get(f"{BASE}/hourly/point?parameters=WS10M,WD10M&community=RE&longitude={lon:.4f}&latitude={lat:.4f}&start={y}0101&end={y}1231&format=JSON&time-standard=LST")
            p = d["properties"]["parameter"]
            for k in sorted(p["WS10M"]):
                w.writerow([f"{k[:4]}-{k[4:6]}-{k[6:8]} {k[8:10]}:00", p["WS10M"][k], p["WD10M"][k]]); n += 1
            print(f"   {dam} {y}: {len(p['WS10M'])} h"); time.sleep(1.0)
    return n

sel = [a for a in sys.argv[1:] if a in DAMS] or DAMS; cells = []
for dam in sel:
    x, y = bf.xy(els[dam]); lon, lat = tf.transform(x, y); print(dam, f"lon {lon:.4f} lat {lat:.4f}")
    cell, nd = daily(dam, lon, lat); nh = hourly(dam, lon, lat)
    cells.append(dict(dam=dam, lon=round(lon, 4), lat=round(lat, 4), cell_lon=cell[0], cell_lat=cell[1], daily_days=nd, hourly_hours=nh)); print("  done:", cells[-1])
    with open(OUT / dam.replace(" ", "_") / "SOURCE.txt", "w", encoding="utf-8") as fh:
        fh.write(f"NASA POWER (MERRA-2), https://power.larc.nasa.gov, read {time.strftime('%Y-%m-%d')} at lon {lon:.4f} lat {lat:.4f} (dam junction {dam}); grid cell centre {cell}.\n"
                 "Daily 2001-2024: T2M, T2M_MAX, T2M_MIN, PRECTOTCORR (AG). Hourly 2015-2024: WS10M, WD10M, local solar time (RE). A modelled record on a ~50 km grid, not a station.\n")
import pandas as pd
prev = pd.read_csv(OUT / "cells.csv") if (OUT / "cells.csv").exists() else pd.DataFrame()
pd.concat([prev[~prev.dam.isin(sel)] if len(prev) else prev, pd.DataFrame(cells)]).to_csv(OUT / "cells.csv", index=False); print("cells.csv written")
