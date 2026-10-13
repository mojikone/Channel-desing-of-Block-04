"""Step 17 - climate at each dam from the Open-Meteo historical archive (ECMWF IFS 9 km / ERA5-Land blend, 'best_match'):
  daily  2001-2023  temperature_2m_mean/max/min (deg C), precipitation_sum (mm)
  hourly 2015-2024  wind_speed_10m (m/s), wind_direction_10m (deg FROM), local time Asia/Muscat
One record per dam; the grid cell returned by the API is recorded so the report can state how many dams share a cell.
usage: python 17_fetch_openmeteo.py [dam ...]   -> W3/climate/data_om/<dam>/
"""
import sys, csv, json, time, urllib.request
from pathlib import Path
from pyproj import Transformer
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import MODEL, HMS, W3, ensure
import basinfile as bf

DAMS9 = ["Hawasinah 02", "Hawasinah 11", "Hawasinah EX", "Shafan 02", "Shafan 08", "Sarami 03", "Sarami 05", "Sakhin 04", "Sakhin 08"]
OUT = ensure(W3 / "climate" / "data_om"); BASE = "https://archive-api.open-meteo.com/v1/archive"
els = bf.parse(HMS / "Basin_1.basin"); tf = Transformer.from_crs(32640, 4326, always_xy=True)

def get(url):
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Renardet-2224-Block04/1.0"}), timeout=300) as r: return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("   retry", attempt + 1, str(e)[:80]); time.sleep(20 * (attempt + 1))
    raise RuntimeError(url)

sel = [a for a in sys.argv[1:] if a in DAMS9] or DAMS9; cells = []
for dam in sel:
    x, y = bf.xy(els[dam]); lon, lat = tf.transform(x, y); d = ensure(OUT / dam.replace(" ", "_")); print(dam, f"lon {lon:.4f} lat {lat:.4f}")
    r = get(f"{BASE}?latitude={lat:.4f}&longitude={lon:.4f}&start_date=2001-01-01&end_date=2023-12-31&daily=temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum&models=best_match&timezone=Asia%2FMuscat")
    dd = r["daily"]
    with open(d / "daily_2001_2023.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["date", "t_mean_c", "t_max_c", "t_min_c", "rain_mm"])
        for i, t in enumerate(dd["time"]): w.writerow([t, dd["temperature_2m_mean"][i], dd["temperature_2m_max"][i], dd["temperature_2m_min"][i], dd["precipitation_sum"][i]])
    cell = (r.get("latitude"), r.get("longitude"), r.get("elevation")); n = 0
    with open(d / "hourly_wind_2015_2024.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["datetime_local", "ws10m_ms", "wd10m_deg"])
        for yr in range(2015, 2025):
            h = get(f"{BASE}?latitude={lat:.4f}&longitude={lon:.4f}&start_date={yr}-01-01&end_date={yr}-12-31&hourly=wind_speed_10m,wind_direction_10m&models=best_match&timezone=Asia%2FMuscat&wind_speed_unit=ms")["hourly"]
            for i, t in enumerate(h["time"]):
                if h["wind_speed_10m"][i] is not None: w.writerow([t.replace("T", " "), h["wind_speed_10m"][i], h["wind_direction_10m"][i]]); n += 1
            time.sleep(0.8)
    cells.append(dict(dam=dam, lon=round(lon, 4), lat=round(lat, 4), cell_lat=cell[0], cell_lon=cell[1], cell_elev_m=cell[2], daily_days=len(dd["time"]), hourly_hours=n)); print("  ", cells[-1])
    with open(d / "SOURCE.txt", "w", encoding="utf-8") as fh:
        fh.write(f"Open-Meteo historical weather archive (open-meteo.com), model best_match = ECMWF IFS 9 km (2017 on) / ERA5 and ERA5-Land, read {time.strftime('%Y-%m-%d')} at the dam axis (lon {lon:.4f}, lat {lat:.4f}); grid cell {cell}.\n"
                 "Daily 2001-2023: temperature_2m mean/max/min, precipitation_sum. Hourly 2015-2024: wind_speed_10m, wind_direction_10m, local time.\n")
import pandas as pd
prev = pd.read_csv(OUT / "cells.csv") if (OUT / "cells.csv").exists() else pd.DataFrame()
pd.concat([prev[~prev.dam.isin(sel)] if len(prev) else prev, pd.DataFrame(cells)]).to_csv(OUT / "cells.csv", index=False); print("cells.csv written")
