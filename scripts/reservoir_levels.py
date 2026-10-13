"""Peak reservoir level per dam and return period from the Basin 3 depth-area results (own analysis point, ELEVATION).
usage: python reservoir_levels.py <HMS project folder> <results folder> [B3]
Adds FSL / crest from the dams shapefile, head over FSL and freeboard at PMP.
"""
import sys, os, hecdss, pandas as pd, geopandas as gpd
HMS = sys.argv[1].rstrip("/\\") + "/"; OUT = sys.argv[2].rstrip("/\\") + "/"; SUF = sys.argv[3] if len(sys.argv) > 3 else "B3"
RPS = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr", "1000yr", "2000yr", "5000yr", "10000yr", "PMP"]
info = gpd.read_file("W:/2224 Flood Protection Scheme in North & South Batinah_MAFWWR/06-WORKING/04-Hydraulic/05 Small Tasks/18 Channel Design/SHP/Block 04 Dams/Dams updated.shp").set_index("Dam Name")
rows = []
for rp in RPS:
    f = HMS + f"DA_{rp}_{SUF}.dss"
    if not os.path.exists(f): print("missing", f); continue
    d = hecdss.HecDss(f)
    for p in [str(x) for x in d.get_catalog()]:
        parts = p.split("/")
        if len(parts) > 6 and parts[3] == "ELEVATION" and parts[2].endswith(" Reservoir") and parts[6].endswith(">" + parts[2]):
            v = d.get(p).values; rows.append(dict(reservoir=parts[2].replace(" Reservoir", ""), rp=rp, max_elev=round(float(max(v)), 2)))
    d.close()
df = pd.DataFrame(rows).drop_duplicates(["reservoir", "rp"]); pv = df.pivot(index="reservoir", columns="rp", values="max_elev")[RPS]
pv.insert(0, "crest", [float(info.loc[r, "Crest El"]) for r in pv.index]); pv.insert(0, "FSL", [float(info.loc[r, "FSL"]) for r in pv.index])
pv["head_over_FSL_PMP_m"] = (pv["PMP"] - pv["FSL"]).round(2); pv["freeboard_PMP_m"] = (pv["crest"] - pv["PMP"]).round(2)
pd.set_option("display.width", 250); print(pv.to_string()); pv.to_csv(OUT + "reservoir_max_elevation.csv")
