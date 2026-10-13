"""Step 18 - MRMWR rain gauges near the dams (read-only server 2331, gap-filled daily record of July 2024):
for every gauge within 15 km of a dam: record length, mean annual rainfall (complete years), wettest year, and for each
dam the nearest gauge. Writes W3/climate/gauges/{gauges_near_dams.csv, gauge_annual.csv, gauge_daily_near.csv}.
"""
import sys, numpy as np, pandas as pd, geopandas as gpd, shapely
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import HMS, W3, ensure
import basinfile as bf

B = "W:/2331 Flood Hazard Maps for Muscat-Dhofar-Musandam_MWR/06-WORKING/03-Hydrology"
SHP = B + "/17.shp/RainGaugesUpdatedShp18July2024/RainGaugesUpdatedShp/Final_Rainfall_ListGIS.shp"
CSV = B + "/10. Rainfall data/20240714_MRMWR_Rainfall Data_Complete/01_Gap_filling_updated_merged_data_daily.csv"
OUT = ensure(W3 / "climate" / "gauges")
DAMS9 = ["Hawasinah 02", "Hawasinah 11", "Hawasinah EX", "Shafan 02", "Shafan 08", "Sarami 03", "Sarami 05", "Sakhin 04", "Sakhin 08"]
els = bf.parse(HMS / "Basin_1.basin"); dams = {d: bf.xy(els[d]) for d in DAMS9}
g = gpd.read_file(SHP).to_crs(32640); rows = []
for dam, (x, y) in dams.items():
    dist = g.geometry.distance(shapely.geometry.Point(x, y)) / 1000
    for i in dist[dist < 15].sort_values().index: rows.append(dict(dam=dam, site_id=g.loc[i, "SITE_ID"], name=g.loc[i, "Local_Name"], type=g.loc[i, "Guge_Type"], elev_m=g.loc[i, "Elevation"], dist_km=round(float(dist[i]), 1), E=int(g.loc[i, "EASTING"]), N=int(g.loc[i, "NORTHING"])))
near = pd.DataFrame(rows); near.to_csv(OUT / "gauges_near_dams.csv", index=False); ids = sorted(set(near.site_id)); print("gauges within 15 km of a dam:", len(ids))
keep = []
for ch in pd.read_csv(CSV, usecols=["SITE_ID", "Date", "VOLUME_VALUE", "Best_Filled_Value", "filled_code", "LONG_NAME", "ELEVATION"], chunksize=500000, low_memory=False):
    keep.append(ch[ch.SITE_ID.isin(ids)])
d = pd.concat(keep); d["date"] = pd.to_datetime(d.Date, errors="coerce"); d = d.dropna(subset=["date"]); d["value"] = pd.to_numeric(d.Best_Filled_Value, errors="coerce").fillna(pd.to_numeric(d.VOLUME_VALUE, errors="coerce"))
d = d[(d.value >= 0)].copy(); d["year"] = d.date.dt.year; d.to_csv(OUT / "gauge_daily_near.csv", index=False)
ann = d.groupby(["SITE_ID", "year"]).agg(rain=("value", "sum"), days=("value", "size")).reset_index(); ann = ann[ann.days >= 330]
stats = ann.groupby("SITE_ID").agg(years=("year", "size"), first=("year", "min"), last=("year", "max"), mean_annual=("rain", "mean"), median_annual=("rain", "median"), max_annual=("rain", "max"), min_annual=("rain", "min")).round(0)
stats = stats.join(g.set_index("SITE_ID")[["Local_Name", "Elevation", "Guge_Type"]]); stats.to_csv(OUT / "gauge_annual.csv"); ann.to_csv(OUT / "gauge_annual_series.csv", index=False)
pd.set_option("display.width", 220); print(stats.sort_values("years", ascending=False).to_string())
print("\nnearest gauge with 10+ complete years per dam:")
for dam in DAMS9:
    cand = near[near.dam == dam].merge(stats[["years", "mean_annual", "first", "last"]], left_on="site_id", right_index=True); cand = cand[cand.years >= 10].sort_values("dist_km")
    if len(cand): r = cand.iloc[0]; print(f"  {dam}: {r['name']} ({r.site_id}) {r.dist_km} km, {int(r.years)} years {int(r['first'])}-{int(r['last'])}, mean {r.mean_annual:.0f} mm/yr")
