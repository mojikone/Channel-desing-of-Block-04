"""Step 03 - dam hydrograph workbook, Majlas layout (one sheet per dam) + summary sheets.

Per dam sheet : A = Time (hrs) at 5 min, then Inflow_<rp>, Outflow_<rp> pairs for the 13 return periods (577 rows, 48 h);
                statistics block (AC:AO) with formulas: peak, time to peak, volume (sum x 300 s / 1e6), attenuation,
                peak reservoir level (data, HMS) and head over FSL; legend texts built by formula from the statistics;
                chart 1 = all inflow hydrographs with the return period, peak and volume in the legend and a label on
                every peak that has room; charts 2-14 = inflow vs outflow for each return period.
Summary sheets: Peaks, Volumes, Levels, Attenuation (formulas pointing at the dam sheets), Read me.
Source: HEC-HMS 4.12, project HEC_HMS_Block_04, Basin 3 (eight reservoirs), depth-area analyses DA <rp> B3, each
reservoir at its own analysis point: inflow = FLOW-COMBINE, outflow = FLOW, level = ELEVATION.
Writes W3/dams/hydrographs/Block04_Dam_Hydrographs.xlsx (then xl_recalc.py).
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.chart.series import SeriesLabel, StrRef
from openpyxl.chart.label import DataLabel, DataLabelList
from openpyxl.chart.legend import LegendEntry
from openpyxl.chart.layout import Layout, ManualLayout
def plot_layout(ch, x, y, w, h): ch.layout = Layout(manualLayout=ManualLayout(layoutTarget="inner", xMode="edge", yMode="edge", x=x, y=y, w=w, h=h))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DAMS9 as DAMS, label, RPS, RP_LABEL, DT_S, DAMS_SHP, W3, ensure
from xlstyle import style_chart

OUT = ensure(W3 / "dams" / "hydrographs") / "Block04_Dam_Hydrographs.xlsx"
FONT = "Arial"; F = lambda **k: Font(name=FONT, size=k.pop("size", 10), **k)
HDR_FILL = PatternFill("solid", fgColor="1F4E79"); KEY_FILL = PatternFill("solid", fgColor="DDEBF7")
thin = Side(style="thin", color="BFBFBF"); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
BLUE_IN = Font(name=FONT, size=10, color="0000FF"); GREY = Font(name=FONT, size=9, color="7F7F7F")
INFLOW, OUTFLOW = "1F4E79", "C55A11"
# sequential blues, light -> dark, for the 12 return periods; PMP black dashed (not a return period)
RAMP = ["C6DBEF", "B3CDE8", "9EC9E2", "86B9DC", "6BAED6", "4F9BCF", "3E8AC5", "3182BD", "2171B5", "1A5FA3", "0D4A8E", "08306B"]

H = pd.read_csv(W3 / "dams" / "data" / "hydrographs_5min_B4.csv"); S = pd.read_csv(W3 / "dams" / "data" / "dam_summary_B4.csv").set_index(["dam", "rp"])
dams = gpd.read_file(DAMS_SHP).set_index("Dam Name")
N = int(H.groupby(["dam", "rp"]).size().max()); FIRST, LAST = 2, 1 + N          # data rows
ST = 29                                                                         # statistics block starts at column AC (29)
wb = Workbook(); rd = wb.active; rd.title = "Read me"

def hdr_cell(c, wrap=True):
    c.font = F(bold=True, color="FFFFFF"); c.fill = HDR_FILL; c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=wrap); c.border = BOX

def ser(ws, xref, yref, title_ref, colour, width_emu=19050, dash=None):
    s = Series(yref, xref, title=None); s.tx = SeriesLabel(strRef=StrRef(title_ref)); s.marker.symbol = "none"; s.smooth = False
    s.graphicalProperties.line.solidFill = colour; s.graphicalProperties.line.width = width_emu; s.graphicalProperties.line.cap = "rnd"
    if dash: s.graphicalProperties.line.dashStyle = dash
    return s

def base_chart(title, w, h, ymax=None):
    ch = ScatterChart(); ch.title = title; ch.style = 2; ch.width = w; ch.height = h
    ch.x_axis.title = "Time from start of storm (h)"; ch.y_axis.title = "Flow (m³/s)"; ch.x_axis.delete = False; ch.y_axis.delete = False
    ch.x_axis.scaling.min = 0; ch.x_axis.scaling.max = 48; ch.x_axis.majorUnit = 6; ch.y_axis.scaling.min = 0
    if ymax: ch.y_axis.scaling.max = ymax
    ch.x_axis.number_format = "0"; ch.y_axis.number_format = "#,##0"; ch.x_axis.majorGridlines = None
    style_chart(ch)
    return ch

for dam in DAMS:
    ws = wb.create_sheet(label(dam, True)); q = f"'{label(dam, True)}'"
    sub = {rp: H[(H.dam == dam) & (H.rp == rp)].reset_index(drop=True) for rp in RPS}
    t = sub[RPS[0]].time_h.values
    ws.cell(row=1, column=1, value="Time (hrs)"); hdr_cell(ws.cell(row=1, column=1))
    for i, th in enumerate(t): c = ws.cell(row=FIRST + i, column=1, value=round(float(th), 4)); c.number_format = "0.0000"
    col = {}
    for k, rp in enumerate(RPS):
        ci, co = 2 + 2 * k, 3 + 2 * k; col[rp] = (ci, co)
        ws.cell(row=1, column=ci, value=f"Inflow_{rp}"); ws.cell(row=1, column=co, value=f"Outflow_{rp}"); hdr_cell(ws.cell(row=1, column=ci)); hdr_cell(ws.cell(row=1, column=co))
        qi = sub[rp].inflow_m3s.values; qo = sub[rp].outflow_m3s.values
        for i in range(N):
            a = ws.cell(row=FIRST + i, column=ci, value=round(float(qi[i]), 3)); b = ws.cell(row=FIRST + i, column=co, value=round(float(qo[i]), 3))
            a.number_format = "0.0"; b.number_format = "0.0"
        ws.column_dimensions[L(ci)].width = 12; ws.column_dimensions[L(co)].width = 12
    ws.column_dimensions["A"].width = 10; ws.row_dimensions[1].height = 30
    # ---- statistics block
    labels = ["Return period", "Peak inflow (m³/s)", "Time to peak, inflow (h)", "Peak outflow (m³/s)", "Time to peak, outflow (h)", "Inflow volume (Mm³)", "Outflow volume (Mm³)",
              "Attenuation of peak (%)", "Peak reservoir level (m)", "Head over FSL (m)", "Legend: inflow", "Legend: outflow", "Legend: return period", "Label: peak"]
    for j, lab in enumerate(labels): hdr_cell(ws.cell(row=1, column=ST + j, value=lab))
    widths = [12, 12, 12, 12, 12, 12, 12, 12, 12, 11, 34, 34, 34, 22]
    for j, w in enumerate(widths): ws.column_dimensions[L(ST + j)].width = w
    A = lambda j: L(ST + j)   # column letter of statistics column j
    for k, rp in enumerate(RPS):
        r = 2 + k; ci, co = L(col[rp][0]), L(col[rp][1]); rng_i = f"{ci}${FIRST}:{ci}${LAST}"; rng_o = f"{co}${FIRST}:{co}${LAST}"; rng_t = f"$A${FIRST}:$A${LAST}"
        vals = [RP_LABEL[rp], f"=MAX({rng_i})", f"=INDEX({rng_t},MATCH({A(1)}{r},{rng_i},0))", f"=MAX({rng_o})", f"=IF({A(3)}{r}>0,INDEX({rng_t},MATCH({A(3)}{r},{rng_o},0)),\"-\")",
                f"=SUM({rng_i})*{DT_S}/1000000", f"=SUM({rng_o})*{DT_S}/1000000", f"=IF({A(1)}{r}>0,1-{A(3)}{r}/{A(1)}{r},\"-\")",
                round(float(S.loc[(dam, rp), "peak_level_m"]), 2), f"={A(8)}{r}-$AD$18",
                f'="Inflow: Qp "&TEXT({A(1)}{r},"#,##0")&" m³/s, V "&TEXT({A(5)}{r},"#,##0.0")&" Mm³"',
                f'="Outflow: Qp "&TEXT({A(3)}{r},"#,##0")&" m³/s, V "&TEXT({A(6)}{r},"#,##0.0")&" Mm³"',
                f'={A(0)}{r}&": Qp "&TEXT({A(1)}{r},"#,##0")&" m³/s, V "&TEXT({A(5)}{r},"#,##0.0")&" Mm³"',
                f'={A(0)}{r}&"  "&TEXT({A(1)}{r},"#,##0")&" m³/s"']
        fmts = ["@", "#,##0", "0.00", "#,##0", "0.00", "0.00", "0.00", "0.0%", "0.00", "0.00", "@", "@", "@", "@"]
        for j, (v, fm) in enumerate(zip(vals, fmts)):
            c = ws.cell(row=r, column=ST + j, value=v); c.number_format = fm; c.border = BOX
            if j == 8: c.font = BLUE_IN
    ws.cell(row=17, column=ST, value="Dam").font = F(bold=True); ws.cell(row=17, column=ST + 1, value=label(dam))
    ws.cell(row=18, column=ST, value="FSL (m)").font = F(bold=True); c = ws.cell(row=18, column=ST + 1, value=float(dams.loc[dam, "FSL"])); c.font = BLUE_IN
    ws.cell(row=19, column=ST, value="Crest level (m)").font = F(bold=True); c = ws.cell(row=19, column=ST + 1, value=float(dams.loc[dam, "Crest El"])); c.font = BLUE_IN
    ws.cell(row=20, column=ST, value="Blue = data (HMS Basin 3 peak level; FSL and crest from the dams sheet). Everything else is a formula on columns A:AA.").font = GREY
    # ---- chart 1: all inflow hydrographs
    peaks = {rp: float(S.loc[(dam, rp), "peak_inflow_m3s"]) for rp in RPS}; ymax = max(peaks.values())
    ch = base_chart(f"{label(dam)} - inflow hydrographs, all return periods (depth-area analyses)", 30.0, 15.0)
    ch.legend.position = "r"; plot_layout(ch, 0.085, 0.10, 0.64, 0.72)
    xs = Reference(ws, min_col=1, min_row=FIRST, max_row=LAST)
    sorted_rps = sorted(RPS, key=lambda rp: peaks[rp])
    labelled = []; last_y = -1e9
    for rp in sorted_rps:   # label a peak only if it sits at least 4 % of the axis above the previous labelled peak
        if peaks[rp] - last_y >= 0.04 * ymax: labelled.append(rp); last_y = peaks[rp]
    for k, rp in enumerate(RPS):
        ys = Reference(ws, min_col=col[rp][0], min_row=FIRST, max_row=LAST)
        colour = "000000" if rp == "PMP" else RAMP[k]; s = ser(ws, xs, ys, f"{q}!${A(12)}${2 + k}", colour, 15875 if rp != "PMP" else 19050, "dash" if rp == "PMP" else None)
        ch.series.append(s)
    # peak annotations: one invisible single-point series per labelled return period (x = time to peak, y = peak),
    # its name = short label 'RP  Qp m3/s' shown as a data label to the right of the point; hidden from the legend
    for rp in labelled:
        r = 2 + RPS.index(rp)
        s = Series(Reference(ws, min_col=ST + 1, min_row=r, max_row=r), Reference(ws, min_col=ST + 2, min_row=r, max_row=r), title=None)
        s.tx = SeriesLabel(strRef=StrRef(f"{q}!${A(13)}${r}")); s.marker.symbol = "circle"; s.marker.size = 4
        s.marker.graphicalProperties.solidFill = "000000" if rp == "PMP" else RAMP[RPS.index(rp)]; s.marker.graphicalProperties.line.solidFill = "FFFFFF"
        s.graphicalProperties.line.noFill = True
        s.dLbls = DataLabelList(); s.dLbls.showVal = False; s.dLbls.showSerName = True; s.dLbls.showCatName = False; s.dLbls.showLegendKey = False; s.dLbls.showPercent = False; s.dLbls.position = "r"
        ch.series.append(s)
    ch.legend.legendEntry = [LegendEntry(idx=len(RPS) + i, delete=True) for i in range(len(labelled))]
    ws.add_chart(ch, f"{A(0)}22")
    # ---- charts 2-14: inflow vs outflow per return period, two per row
    for k, rp in enumerate(RPS):
        ch = base_chart(f"{label(dam)} - {RP_LABEL[rp]}", 15.0, 7.5); ch.legend.position = "b"; plot_layout(ch, 0.15, 0.16, 0.81, 0.50)
        ch.series.append(ser(ws, xs, Reference(ws, min_col=col[rp][0], min_row=FIRST, max_row=LAST), f"{q}!${A(10)}${2 + k}", INFLOW, 19050))
        ch.series.append(ser(ws, xs, Reference(ws, min_col=col[rp][1], min_row=FIRST, max_row=LAST), f"{q}!${A(11)}${2 + k}", OUTFLOW, 19050))
        row = 54 + (k // 2) * 16; colx = ST + (k % 2) * 9
        ws.add_chart(ch, f"{L(colx)}{row}")
    ws.freeze_panes = "B2"; ws.sheet_view.zoomScale = 85

# ---- summary sheets (formulas into the dam sheets)
def summary(name, stat_col, fmt, title):
    ws = wb.create_sheet(name); ws["A1"] = title; ws["A1"].font = F(bold=True, size=12)
    hdr_cell(ws.cell(row=3, column=1, value="Dam"))
    for j, rp in enumerate(RPS): hdr_cell(ws.cell(row=3, column=2 + j, value=RP_LABEL[rp])); ws.column_dimensions[L(2 + j)].width = 10
    ws.column_dimensions["A"].width = 16
    for i, dam in enumerate(DAMS):
        ws.cell(row=4 + i, column=1, value=label(dam)).font = F(bold=True); ws.cell(row=4 + i, column=1).border = BOX
        for j, rp in enumerate(RPS):
            c = ws.cell(row=4 + i, column=2 + j, value=f"='{label(dam, True)}'!${L(ST + stat_col)}${2 + j}"); c.number_format = fmt; c.border = BOX
    return ws
w = summary("Peak inflow", 1, "#,##0", "Peak inflow at the dam (m³/s) - Basin 3 depth-area analyses, reservoir element own analysis point (= dam junction flow)")
w2 = summary("Peak outflow", 3, "#,##0", "Peak outflow from the reservoir (m³/s) - spillway + crest overtopping")
summary("Inflow volume", 5, "0.00", "Inflow volume (Mm³) - sum of the 5-minute ordinates x 300 s / 1e6")
summary("Outflow volume", 6, "0.00", "Outflow volume (Mm³)")
summary("Attenuation", 7, "0.0%", "Attenuation of the peak (1 - peak outflow / peak inflow)")
summary("Peak level", 8, "0.00", "Peak reservoir level (m) - HMS Basin 3 (data)")
summary("Head over FSL", 9, "0.00", "Head over FSL at the peak (m)")
# ---- read me
txt = ["Block 04 dams - inflow and outflow hydrographs (dam design team)", "",
       "Source: HEC-HMS 4.12 project 'HEC_HMS_Block_04', basin model 'Basin 4' (the hydrology study's dam catchments + the nine reservoirs, Shafan 08 included), depth-area analyses 'DA <rp> B4', 5-minute step, 48 h storm, computed 2026-10-06.",
       "Each reservoir sits 150 m downstream of its dam junction; inflow = the reservoir element's combined inflow (= the dam junction flow, identical to Basin 1 within 0.1 %, Hawasinah EX 0.8 %), outflow = spillway + crest overtopping (Modified Puls).",
       "Reservoir curves: 10 m DEM inside the crest polygon (see Block04_Dams_Elevation_Area_Volume.xlsx); spillway Q = 2.1 L H^1.5 above FSL with the dams-sheet lengths; crest overtopping 1.7 L_crest (z - crest)^1.5.",
       "Hawasinah EX is reported as Hawasinah UP; Sakhin 08 as Sakhin 08 (Mehmum).",
       "Dam sheets: columns A:AA are the HMS series (data); the statistics block AC:AO and all summary sheets are formulas; the peak reservoir level (AK) is data from the HMS ELEVATION series.",
       "Charts: chart 1 overlays the 13 inflow hydrographs with return period, peak and volume in the legend; charts 2-14 show inflow against outflow per return period.",
       "Depth-area analyses apply the areal reduction of the storm to each analysis point's own catchment area, so the dam inflow here is the proper design hydrograph of the dam, not the basin-wide hypothetical storm run.",
       f"Built by W3/scripts/03_build_hydrograph_workbook.py from W3/dams/data/hydrographs_5min_B4.csv on {pd.Timestamp.today():%Y-%m-%d}."]
for i, tline in enumerate(txt): rd.cell(row=1 + i, column=1, value=tline).font = F(bold=(i == 0), size=12 if i == 0 else 10)
rd.column_dimensions["A"].width = 160
for s in wb.worksheets:
    for row in s.iter_rows():
        for c in row:
            if c.font is None or c.font.name != FONT: c.font = Font(name=FONT, size=c.font.size or 10, bold=c.font.bold, color=c.font.color)
wb.save(OUT); print("written", OUT, "| sheets:", len(wb.sheetnames), "| rows per series:", N)
