"""Step 21 - sediment yield of the nine dam catchments (replaces step 09 for the report):
RUSLE factors with P = 1 (engineer), Williams (1977) SDR with a floor of 0.2, sediment yield at 1.5 t/m3 with a floor of
90 m3/km2/yr (engineer, 2026-10-06), sediment in 50 and 100 years (Mcm), Tc. Columns as the engineer listed.
Reads  sediment/rusle/Output/CSV/RUSLE_Results.csv (9 catchments), sediment/catchments/Dam_catchments9.gpkg
Writes sediment/sediment_yield.csv (input of step 11) and sediment/B4_DAM_RUSLE.xlsx
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter as L
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DAMS9, label, W3, ensure

SED = ensure(W3 / "sediment"); DENSITY = 1.5; SDR_MIN = 0.2; YIELD_MIN = 90.0
cat = gpd.read_file(SED / "catchments" / "Dam_catchments9.gpkg").set_index("name")
rus = pd.read_csv(SED / "rusle" / "Output" / "CSV" / "RUSLE_Results.csv"); rus["Name"] = rus["Name"].astype(str); rus = rus.set_index("Name")
rows = []
for dam in DAMS9:
    r = rus.loc[dam]; c = cat.loc[dam]; rr = float(c.relief_m) / (float(c.lfp_km) * 1000)
    sl = float(r["Mean Soil Loss (t/ha/yr)"]); sdr_w = 1.366e-11 * float(c.area_km2) ** -0.1 * rr ** 0.363 * float(c.cn_w) ** 5.444; sdr = max(sdr_w, SDR_MIN)
    y_raw = sl * 100 / DENSITY * sdr; y = max(y_raw, YIELD_MIN)
    rows.append(dict(name=dam, soil_loss_t_ha_yr=round(sl, 3), R=float(r["R"]), K=float(r["K"]), LS=float(r["LS"]), C=float(r["C"]), P=1.0, area_km2=float(c.area_km2), relief_m=float(c.relief_m), flow_path_km=float(c.lfp_km),
                     relief_ratio=round(rr, 5), cn=float(c.cn_w), tc_min=float(c.tc_min), lag_min=float(c.lag_min), s1085=float(c.s1085), basin_slope=float(c.basin_slope),
                     sdr_williams=round(sdr_w, 4), sdr_used=round(sdr, 4), yield_raw_m3_km2_yr=round(y_raw, 1), yield_m3_km2_yr=round(y, 1), yield_m3_yr=round(y * float(c.area_km2)),
                     sed50_Mcm=round(y * float(c.area_km2) * 50 / 1e6, 3), sed100_Mcm=round(y * float(c.area_km2) * 100 / 1e6, 3)))
df = pd.DataFrame(rows); df.to_csv(SED / "sediment_yield.csv", index=False); pd.set_option("display.width", 250)
print(df[["name", "soil_loss_t_ha_yr", "area_km2", "relief_ratio", "cn", "sdr_williams", "sdr_used", "yield_raw_m3_km2_yr", "yield_m3_km2_yr", "sed50_Mcm", "sed100_Mcm", "tc_min"]].to_string(index=False))
# ---- workbook, Block 6 layout with the engineer's columns
FONT = "Arial"; HDR_FILL = PatternFill("solid", fgColor="1F4E79"); thin = Side(style="thin", color="BFBFBF"); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
BLUE = Font(name=FONT, size=10, color="0000FF"); BLK = Font(name=FONT, size=10); GREY = Font(name=FONT, size=9, color="7F7F7F")
wb = Workbook(); ws = wb.active; ws.title = "B4 DAM RUSLE"
cols = ["Name", "Mean Soil Loss (t/ha/yr)", "R", "K", "LS", "C", "P", "Area km2", "Basin Relief Ratio", "CN", "SDR method", "SDR value (Williams)", "SDR used (min 0.2)", "Sediment Density 1.3-1.8 (t/m3)",
        "Mean Soil Loss (m3/km2/year) considering SDR", "Sediment yield used (m3/km2/yr, min 90)", "Sediment in 50 yr (Mcm)", "Sediment in 100 yr (Mcm)", "TC (min)", "Lag (min)", "Relief (m)", "Longest flow path (km)", "10-85 slope", "Basin slope"]
for j, h in enumerate(cols, 1):
    c = ws.cell(row=1, column=j, value=h); c.font = Font(name=FONT, bold=True, color="FFFFFF"); c.fill = HDR_FILL; c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); c.border = BOX; ws.column_dimensions[L(j)].width = 13 if j > 1 else 20
ws.row_dimensions[1].height = 54
ws["Z1"] = "Floors (engineer)"; ws["Z2"] = "SDR min"; ws["AA2"] = SDR_MIN; ws["Z3"] = "Yield min (m3/km2/yr)"; ws["AA3"] = YIELD_MIN; ws["AA2"].font = BLUE; ws["AA3"].font = BLUE
for i, r in enumerate(df.itertuples(), 2):
    vals = [label(r.name), r.soil_loss_t_ha_yr, r.R, r.K, r.LS, r.C, 1, r.area_km2, r.relief_ratio, r.cn, "Williams (1977)", f"=1.366*10^-11*H{i}^-0.1*I{i}^0.363*J{i}^5.444", f"=MAX(L{i},$AA$2)", DENSITY if i == 2 else "=$N$2",
            f"=(B{i}*100/N{i})*M{i}", f"=MAX(O{i},$AA$3)", f"=P{i}*H{i}*50/1000000", f"=P{i}*H{i}*100/1000000", r.tc_min, r.lag_min, r.relief_m, r.flow_path_km, r.s1085, r.basin_slope]
    fm = ["@", "0.000", "0.000", "0.0000", "0.000", "0.0000", "0", "0.00", "0.00000", "0.0", "@", "0.0000", "0.0000", "0.0", "0.0", "0.0", "0.000", "0.000", "0", "0", "0", "0.00", "0.00000", "0.0000"]
    for j, (v, f) in enumerate(zip(vals, fm), 1):
        c = ws.cell(row=i, column=j, value=v); c.number_format = f; c.border = BOX; c.font = BLK if (isinstance(v, str) and v.startswith("=")) or j in (1, 11) else BLUE
n = 2 + len(df)
notes = ["Blue = data, black = formulas. RUSLE factors from github.com/mojikone/RUSLE on the nine Basin 1 dam catchments (R SM2RAIN, K SoilGrids 0-5 cm Williams 1995, LS Copernicus GLO-30 Moore & Burch, C Landsat 8 2017 mosaic Durigon); P = 1 (engineer).",
         "Williams (1977): SDR = 1.366e-11 A^-0.1 RR^0.363 CN^5.444; relief ratio = relief / longest flow path; CN area-weighted. Floors (engineer, 2026-10-06): SDR >= 0.2, yield >= 90 m3/km2/yr. Density 1.5 t/m3 (cell N2).",
         "Tc and lag by Kirpich on the longest flow path and its 10-85 slope (10 m terrain), basin slope = mean cell slope. Catchments: W3/sediment/catchments/Dam_catchments9.shp."]
for k, t in enumerate(notes): ws.cell(row=n + 1 + k, column=1, value=t).font = GREY
ws.freeze_panes = "B2"; out = SED / "B4_DAM_RUSLE.xlsx"; wb.save(out); print("written", out)
