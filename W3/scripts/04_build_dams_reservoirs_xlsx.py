"""Step 04 - 'dams_reservoirs.xlsx' in the Block 6 (B6 W3) layout, for Block 04's eight reservoirs.

Sheet 'Hydrographs'            : datetime + '<dam> Reservoir Inflow (<rp>)' / 'Outflow (<rp>)' for every return period x dam (5-min, 577 rows)
Sheet 'Peak Inflow Outflow'    : rows = return periods, columns = '<dam> Reservoir Inflow Max (m3/s)' / 'Outflow Max (m3/s)'  (=MAX formulas)
Sheet 'Inflow Outflow Volumes' : same structure in Mm3 (=SUM x 300 s / 1e6 formulas)
Sheet 'Peak Level Attenuation' : peak reservoir level (m, data) and attenuation of the peak (formula)
Writes W3/dams/hydrographs/dams_reservoirs.xlsx (then xl_recalc.py).
"""
import sys, datetime as dt
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter as L
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DAMS9 as DAMS, label, RPS, DT_S, W3, ensure

OUT = ensure(W3 / "dams" / "hydrographs") / "dams_reservoirs.xlsx"
FONT = "Arial"; HDR = Font(name=FONT, bold=True, size=10); F = Font(name=FONT, size=10); BLUE = Font(name=FONT, size=10, color="0000FF")
H = pd.read_csv(W3 / "dams" / "data" / "hydrographs_5min_B4.csv"); S = pd.read_csv(W3 / "dams" / "data" / "dam_summary_B4.csv").set_index(["dam", "rp"])
N = int(H.groupby(["dam", "rp"]).size().max()); FIRST, LAST = 2, 1 + N
t0 = dt.datetime(2000, 1, 1, 0, 0)   # HMS simulation start of the depth-area analyses
wb = Workbook(); ws = wb.active; ws.title = "Hydrographs"
ws.cell(row=1, column=1, value="datetime").font = HDR; ws.column_dimensions["A"].width = 17
for i in range(N):
    c = ws.cell(row=FIRST + i, column=1, value=t0 + dt.timedelta(seconds=DT_S * i)); c.number_format = "yyyy-mm-dd hh:mm"; c.font = F
colmap = {}; col = 2
for rp in RPS:
    for dam in DAMS:
        sub = H[(H.dam == dam) & (H.rp == rp)]
        for kind, vals in (("Inflow", sub.inflow_m3s.values), ("Outflow", sub.outflow_m3s.values)):
            ws.cell(row=1, column=col, value=f"{label(dam)} Reservoir {kind} ({rp})").font = HDR; ws.cell(row=1, column=col).alignment = Alignment(wrap_text=True, vertical="top")
            for i, v in enumerate(vals): ws.cell(row=FIRST + i, column=col, value=round(float(v), 3)).number_format = "0.0"
            colmap[(dam, rp, kind)] = col; ws.column_dimensions[L(col)].width = 13; col += 1
ws.row_dimensions[1].height = 45; ws.freeze_panes = "B2"
def table(name, lab, formula, fmt):
    w = wb.create_sheet(name); w.cell(row=1, column=1, value="return_period").font = HDR; w.column_dimensions["A"].width = 14
    c = 2
    for dam in DAMS:
        for kind in ("Inflow", "Outflow"):
            w.cell(row=1, column=c, value=f"{label(dam)} Reservoir {kind} {lab}").font = HDR; w.cell(row=1, column=c).alignment = Alignment(wrap_text=True, vertical="top"); w.column_dimensions[L(c)].width = 14
            for j, rp in enumerate(RPS):
                src = L(colmap[(dam, rp, kind)]); cell = w.cell(row=2 + j, column=c, value=formula.format(col=src, a=FIRST, b=LAST)); cell.number_format = fmt; cell.font = F
            c += 1
    for j, rp in enumerate(RPS): w.cell(row=2 + j, column=1, value=rp).font = F
    w.row_dimensions[1].height = 45; w.freeze_panes = "B2"; return w
table("Peak Inflow Outflow", "Max (m3/s)", "=MAX(Hydrographs!{col}{a}:{col}{b})", "0.0000")
table("Inflow Outflow Volumes", "Vol (Mm3)", f"=SUM(Hydrographs!{{col}}{{a}}:{{col}}{{b}})*{DT_S}/1000000", "0.000000")
w = wb.create_sheet("Peak Level Attenuation"); w.cell(row=1, column=1, value="return_period").font = HDR; w.column_dimensions["A"].width = 14
for k, dam in enumerate(DAMS):
    w.cell(row=1, column=2 + k, value=f"{label(dam)} peak level (m)").font = HDR; w.cell(row=1, column=11 + k, value=f"{label(dam)} attenuation (%)").font = HDR
    w.column_dimensions[L(2 + k)].width = 14; w.column_dimensions[L(11 + k)].width = 14
    for j, rp in enumerate(RPS):
        c = w.cell(row=2 + j, column=2 + k, value=round(float(S.loc[(dam, rp), "peak_level_m"]), 2)); c.font = BLUE; c.number_format = "0.00"
        ci, co = L(2 + 2 * DAMS.index(dam)), L(3 + 2 * DAMS.index(dam))
        c = w.cell(row=2 + j, column=11 + k, value=f"=IF('Peak Inflow Outflow'!{ci}{2 + j}>0,1-'Peak Inflow Outflow'!{co}{2 + j}/'Peak Inflow Outflow'!{ci}{2 + j},\"-\")"); c.number_format = "0.0%"; c.font = F
for j, rp in enumerate(RPS): w.cell(row=2 + j, column=1, value=rp).font = F
for c in w[1]: c.alignment = Alignment(wrap_text=True, vertical="top")
w.row_dimensions[1].height = 45
w.cell(row=17, column=1, value="Source: HEC-HMS 4.12 HEC_HMS_Block_04, Basin 4 (nine reservoirs), depth-area analyses DA <rp> B4, reservoir elements at their own analysis point (inflow = FLOW-COMBINE, outflow = FLOW, level = ELEVATION). Blue = data; the rest are formulas on 'Hydrographs'.").font = Font(name=FONT, size=9, color="7F7F7F")
wb.save(OUT); print("written", OUT, "| hydrograph columns:", col - 1, "| rows:", N)
