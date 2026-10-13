"""Step 02 - elevation-area-volume workbook for the eight dams (for the dam design team).

Sheet 'Dams'     : the Block 04 Dams sheet (crest, FSL, capacity, QPMF, Hmax, C, spillway length) + values read from the
                   curves by formula (bed, height, area/volume at FSL and crest, difference to the sheet capacity) + the
                   HMS Basin 3 PMP level and outflow.
Sheet per dam    : elevation (0.5 m steps, bed -> crest), area from the 10 m DEM inside the crest polygon, area in m2,
                   incremental and cumulative volume by the conic (frustum) formula  dV = dz/3 (A1 + A2 + sqrt(A1 A2)),
                   the DEM-integrated volume as a check column, head above FSL; two charts (Elevation-Volume,
                   Elevation-Area) with the FSL and the crest drawn as reference lines.
All derived numbers are Excel formulas; only the DEM areas, the DEM check volumes and the dams-sheet values are data.
Writes W3/dams/eav/Block04_Dams_Elevation_Area_Volume.xlsx (then run xl_recalc.py on it).
"""
import sys
from pathlib import Path
import pandas as pd, geopandas as gpd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.chart.series import SeriesLabel, StrRef
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.worksheet.properties import PageSetupProperties
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DAMS9 as DAMS, label, RESERVOIRS, DAMS_SHP, W3, ensure
from xlstyle import style_chart

OUT = ensure(W3 / "dams" / "eav") / "Block04_Dams_Elevation_Area_Volume.xlsx"
FONT = "Arial"
F = lambda **k: Font(name=FONT, size=k.pop("size", 10), **k)
HDR_FILL = PatternFill("solid", fgColor="1F4E79"); KEY_FILL = PatternFill("solid", fgColor="DDEBF7"); DATA_FILL = PatternFill("solid", fgColor="FFF2CC")
thin = Side(style="thin", color="BFBFBF"); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
BLUE_IN = Font(name=FONT, size=10, color="0000FF")          # hardcoded inputs (dams sheet, DEM data)
GREY = Font(name=FONT, size=10, color="7F7F7F")
CURVE, AREA_COL, FSL_COL, CREST_COL = "1F4E79", "2E75B6", "C00000", "595959"

dams = gpd.read_file(DAMS_SHP).set_index("Dam Name")
summ = pd.read_csv(W3 / "dams" / "data" / "dam_summary_B4.csv"); pmp = summ[summ.rp == "PMP"].set_index("dam")
wb = Workbook(); ws = wb.active; ws.title = "Dams"
TOP = 4   # first data row of the curve tables on the dam sheets (header on row TOP-1)

def hdr(ws, row, labels, widths=None):
    for j, lab in enumerate(labels, 1):
        c = ws.cell(row=row, column=j, value=lab); c.font = F(bold=True, color="FFFFFF"); c.fill = HDR_FILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); c.border = BOX
    ws.row_dimensions[row].height = 42
    if widths:
        for j, w in enumerate(widths, 1): ws.column_dimensions[L(j)].width = w

# ------------------------------------------------------------------ dam sheets
n_rows = {}
for dam in DAMS:
    eav = pd.read_csv(RESERVOIRS / f"EAV_{dam.replace(' ', '_')}.csv"); n = len(eav); n_rows[dam] = n
    s = wb.create_sheet(dam); q = f"'{dam}'"
    s["A1"] = f"{dam} - reservoir elevation-area-volume"; s["A1"].font = F(bold=True, size=12)
    s["A2"] = ("Area: 10 m DEM (NSA 5m B04 Res10m) inside the crest polygon, pond connected to the dam axis, 0.5 m steps from bed to crest. "
               "Volume: conic formula between steps, dV = dz/3 (A1 + A2 + sqrt(A1 A2)). Column F: volume integrated cell by cell on the DEM (check only). Blue = data.")
    s["A2"].font = GREY; s["A2"].alignment = Alignment(wrap_text=True, vertical="top"); s.merge_cells("A2:H2"); s.row_dimensions[2].height = 40
    hdr(s, TOP - 1, ["Elevation (m)", "Area (km²)", "Area (m²)", "ΔV conic (Mm³)", "Volume (Mm³)", "Volume DEM-integrated (Mm³)", "Head above FSL (m)", "Head above crest (m)"],
        [13, 12, 15, 14, 14, 16, 14, 14])
    last = TOP + n - 1
    for i, r in enumerate(eav.itertuples(index=False)):
        row = TOP + i
        s.cell(row=row, column=1, value=float(r.elevation_m)).font = BLUE_IN
        s.cell(row=row, column=2, value=float(r.area_km2)).font = BLUE_IN
        s.cell(row=row, column=3, value=f"=B{row}*1000000")
        s.cell(row=row, column=4, value=0 if i == 0 else f"=(A{row}-A{row-1})/3*(C{row-1}+C{row}+SQRT(C{row-1}*C{row}))/1000000")
        s.cell(row=row, column=5, value=0 if i == 0 else f"=E{row-1}+D{row}")
        s.cell(row=row, column=6, value=float(r.volume_Mm3)).font = GREY
        s.cell(row=row, column=7, value=f"=A{row}-$K$5"); s.cell(row=row, column=8, value=f"=A{row}-$K$6")
        for j, fmt in zip(range(1, 9), ["0.0", "0.0000", "#,##0", "0.0000", "0.000", "0.000", "0.0", "0.0"]):
            c = s.cell(row=row, column=j); c.number_format = fmt; c.border = BOX
            if j in (4, 5, 7, 8) or j == 3: c.font = F() if c.font != GREY else GREY
    # key values block (J:K)
    keys = [("Dam", f'="{dam}"'), ("FSL (m)", f"=Dams!C{DAMS.index(dam) + 4}"), ("Crest level (m)", f"=Dams!B{DAMS.index(dam) + 4}"), ("Bed level (m)", f"=A{TOP}"),
            ("Dam height crest-bed (m)", "=K6-K7"), ("Area at FSL (km²)", f"=INDEX(B{TOP}:B{last},MATCH(K5,A{TOP}:A{last},0))"),
            ("Volume at FSL (Mm³)", f"=INDEX(E{TOP}:E{last},MATCH(K5,A{TOP}:A{last},0))"), ("Capacity per dams sheet (Mm³)", f"=Dams!D{DAMS.index(dam) + 4}"),
            ("Difference (%)", "=K10/K11-1"), ("Area at crest (km²)", f"=INDEX(B{TOP}:B{last},MATCH(K6,A{TOP}:A{last},0))"),
            ("Volume at crest (Mm³)", f"=INDEX(E{TOP}:E{last},MATCH(K6,A{TOP}:A{last},0))"), ("Max volume in table (Mm³)", f"=MAX(E{TOP}:E{last})"), ("Max area in table (km²)", f"=MAX(B{TOP}:B{last})")]
    for i, (lab, f) in enumerate(keys):
        s.cell(row=4 + i, column=10, value=lab).font = F(bold=(i == 0)); s.cell(row=4 + i, column=11, value=f).fill = KEY_FILL
        s.cell(row=4 + i, column=11).number_format = {"Difference (%)": "0.0%", "Area at FSL (km²)": "0.00", "Area at crest (km²)": "0.00", "Max area in table (km²)": "0.00"}.get(lab, "0.0" if "m)" in lab else "0.00")
        s.cell(row=4 + i, column=11).border = BOX; s.cell(row=4 + i, column=10).border = BOX
    s.column_dimensions["J"].width = 27; s.column_dimensions["K"].width = 12
    # reference-line helper points (M:P): FSL and crest as horizontal lines across each chart's x range
    s["M3"] = "chart helper: reference lines"; s["M3"].font = GREY
    for j, lab in enumerate(["x volume", "y FSL", "y crest", "x area"], 13): s.cell(row=4, column=j, value=lab).font = GREY
    s["M5"] = 0; s["M6"] = "=K15*1.02"; s["N5"] = "=K5"; s["N6"] = "=K5"; s["O5"] = "=K6"; s["O6"] = "=K6"; s["P5"] = 0; s["P6"] = "=K16*1.02"
    s["M7"] = '="FSL "&TEXT(K5,"0.0")&" m"'; s["M8"] = '="Crest "&TEXT(K6,"0.0")&" m"'; s["M9"] = '="Elevation-volume curve"'; s["M10"] = '="Elevation-area curve"'
    for c in ("M7", "M8", "M9", "M10"): s[c].font = GREY
    # charts
    def line_series(ws, xref, yref, title_cell, colour, width_emu=19050, dash=None):
        ser = Series(yref, xref, title=None); ser.tx = SeriesLabel(strRef=StrRef(f"{q}!{title_cell}"))
        ser.marker.symbol = "none"; ser.smooth = False
        ser.graphicalProperties.line.solidFill = colour; ser.graphicalProperties.line.width = width_emu
        if dash: ser.graphicalProperties.line.dashStyle = dash
        return ser
    def chart(xcol, title, xtitle, ref_x_cells, name_cell, anchor):
        ch = ScatterChart(); ch.title = title; ch.style = 2; ch.height = 9.5; ch.width = 17.5
        ch.x_axis.title = xtitle; ch.y_axis.title = "Elevation (m)"; ch.x_axis.delete = False; ch.y_axis.delete = False
        ch.x_axis.number_format = "0.0" if xcol == "B" else "0"; ch.y_axis.number_format = "0"
        ch.x_axis.scaling.min = 0; ch.y_axis.scaling.min = float((eav.elevation_m.min() // 5) * 5); ch.y_axis.scaling.max = float(dams.loc[dam, "Crest El"] + 1)
        ch.y_axis.majorGridlines.spPr = None; ch.x_axis.majorGridlines = None
        ch.legend.position = "b"; style_chart(ch)
        ch.layout = Layout(manualLayout=ManualLayout(layoutTarget="inner", xMode="edge", yMode="edge", x=0.13, y=0.13, w=0.83, h=0.58))   # room for the title, axis titles and the legend
        xs = Reference(s, min_col=ord(xcol) - 64, min_row=TOP, max_row=last); ys = Reference(s, min_col=1, min_row=TOP, max_row=last)
        ch.series.append(line_series(s, xs, ys, name_cell, CURVE if xcol == "E" else AREA_COL, 22225))
        rx = Reference(s, range_string=f"{q}!${ref_x_cells}$5:${ref_x_cells}$6")
        ch.series.append(line_series(s, rx, Reference(s, range_string=f"{q}!$N$5:$N$6"), "$M$7", FSL_COL, 15875, "dash"))
        ch.series.append(line_series(s, rx, Reference(s, range_string=f"{q}!$O$5:$O$6"), "$M$8", CREST_COL, 15875, "sysDot"))
        for ser in ch.series: ser.graphicalProperties.line.cap = "rnd"
        s.add_chart(ch, anchor)
    chart("E", f"{dam} - elevation vs volume", "Volume (Mm³)", "M", "$M$9", "J19")
    chart("B", f"{dam} - elevation vs area", "Area (km²)", "P", "$M$10", "J40")
    s.freeze_panes = f"A{TOP}"; s.sheet_view.zoomScale = 90

# ------------------------------------------------------------------ Dams summary sheet
ws["A1"] = "Block 04 dams - levels, capacities and reservoir curves (nine dams)"; ws["A1"].font = F(bold=True, size=12)
cols = ["Dam Name", "Crest El (m)", "FSL (m)", "Reservoir Capacity (Mm³)", "QPMF (m³/s)", "Hmax (m)", "C", "Spillway Length (m)",
        "Bed level (m)", "Dam height crest-bed (m)", "Area at FSL (km²)", "Volume at FSL (Mm³)", "Curve vs capacity (%)", "Area at crest (km²)", "Volume at crest (Mm³)",
        "PMP peak level, HMS Basin 3 (m)", "Head over FSL at PMP (m)", "PMP peak outflow, HMS Basin 3 (m³/s)", "PMP peak inflow, HMS Basin 3 (m³/s)"]
hdr(ws, 3, cols, [15, 10, 9, 12, 11, 8, 6, 11, 10, 11, 11, 11, 11, 11, 11, 13, 11, 13, 13])
ws.row_dimensions[3].height = 56
for i, dam in enumerate(DAMS):
    r = 4 + i; d = dams.loc[dam]; q = f"'{dam}'"
    vals = [label(dam), float(d["Crest El"]), float(d["FSL"]), float(d["Reservoir"]), float(d["QPMF"]), float(d["Hmax"]), float(d["C"]), float(d["Spillway L"])]
    for j, v in enumerate(vals, 1):
        c = ws.cell(row=r, column=j, value=v); c.font = BLUE_IN if j > 1 else F(bold=True); c.border = BOX
    forms = [f"={q}!K7", f"=B{r}-I{r}", f"={q}!K9", f"={q}!K10", f"=L{r}/D{r}-1", f"={q}!K13", f"={q}!K14"]
    for j, f in enumerate(forms, 9):
        c = ws.cell(row=r, column=j, value=f); c.border = BOX; c.number_format = "0.0%" if j == 13 else ("0.00" if j in (11, 14) else "0.0")
    for j, v in zip((16, 18, 19), (float(pmp.loc[dam, "peak_level_m"]), float(pmp.loc[dam, "peak_outflow_m3s"]), float(pmp.loc[dam, "peak_inflow_m3s"]))):
        c = ws.cell(row=r, column=j, value=round(v, 2) if j == 16 else round(v)); c.font = BLUE_IN; c.border = BOX; c.number_format = "0.00" if j == 16 else "#,##0"
    c = ws.cell(row=r, column=17, value=f"=P{r}-C{r}"); c.border = BOX; c.number_format = "0.00"
r = 4 + len(DAMS) + 1
notes = ["Blue = data. Columns B-H: 'Block 04 Dams.xlsx' / 'Dams updated.shp' (dam design team). Columns I-O: read by formula from the curve sheets.",
         "Columns P, R, S: HEC-HMS 4.12 project HEC_HMS_Block_04, Basin 4 (the hydrology study's dam catchments + nine reservoirs), depth-area analysis 'DA PMP B4', reservoir element at its own analysis point (2026-10-06).",
         "Curves: 10 m DEM 'NSA 5m B04 Res10m' (the HMS terrain) inside the Crest_Level polygon closed by the dam axis; volumes by the conic formula between 0.5 m steps.",
         "Curve volumes at FSL are 2-6 % below the sheet capacities; the sheet values were kept as the reference for the dam team."]
for k, t in enumerate(notes): ws.cell(row=r + k, column=1, value=t).font = GREY
ws.freeze_panes = "B4"; ws.sheet_view.zoomScale = 90
for s in wb.worksheets:
    for row in s.iter_rows():
        for c in row:
            if c.font is None or c.font.name != FONT: c.font = Font(name=FONT, size=c.font.size or 10, bold=c.font.bold, color=c.font.color)
    s.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True); s.page_setup.orientation = "landscape"
wb.save(OUT); print("written", OUT, "| sheets:", wb.sheetnames, "| rows per dam:", n_rows)
