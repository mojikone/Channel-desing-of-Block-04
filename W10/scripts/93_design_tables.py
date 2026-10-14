"""Step 93 (W10) - 'Block 04 - Channel design tables (200-year).xlsx': the design data of the reports as a workbook whose derived
numbers are live formulas (his instruction 2026-10-14) and whose costs live only in the BOQ workbook (no dead copies).
Sheets: Read me; Reaches (SewerGEMS results; the size text by formula); Channel sections (aggregates of Reaches by formula); Size
inventory (COUNTIFS / SUMIFS on Reaches); Outfalls (the invert against MHHW by formula; the flow depth is a model result); Proposed culverts (design
data; size text, overall width and headwater ratio by formula); Dykes (depths and height; the quantities of the typical section by
formula); Channel quantities (measured on the terrain; the land take by class); Land take by class (SUM formulas).
Writes W10/tables/...; step 90 copies it into the submission.
    python 93_design_tables.py"""
import os, sys
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter as L
HERE = os.path.dirname(os.path.abspath(__file__)); W10 = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(W10, "report")); sys.path.insert(0, os.path.join(W10, "report", "lib")); os.environ.pop("REPORT_ONLY", None)
import data_facts as DF
OUT = os.path.join(W10, "tables"); os.makedirs(OUT, exist_ok=True)
HDR = PatternFill("solid", fgColor="1F5F8B"); HFONT = Font(bold=True, color="FFFFFF", name="Arial", size=10); FONT = Font(name="Arial", size=10); BOLD = Font(name="Arial", size=10, bold=True); BLUE = Font(name="Arial", size=10, color="0000FF")
wb = Workbook(); rd = wb.active; rd.title = "Read me"
def sheet(name, headers, widths=None):
    ws = wb.create_sheet(name); ws.append(headers)
    for c in ws[1]: c.fill = HDR; c.font = HFONT; c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    ws.row_dimensions[1].height = 42
    for j in range(1, len(headers) + 1): ws.column_dimensions[L(j)].width = (widths[j - 1] if widths else 13)
    return ws
def finish(ws, freeze="B2"):
    for row in ws.iter_rows(min_row=2):
        for c in row: c.font = BOLD if str(row[0].value) == "Total" or str(row[1].value) == "Total" else FONT
    ws.freeze_panes = freeze
def val(v):
    try:
        if v is None or pd.isna(v): return None
    except (TypeError, ValueError): pass
    return v.item() if hasattr(v, "item") else v
def size_formula(dep, wid): return f'=TEXT({dep},"0.0")&" x "&IF({wid}=INT({wid}),TEXT({wid},"0"),TEXT({wid},"0.0"))'
# ---- Reaches
rt = DF.reach_table()
R = sheet("Reaches", ["Reach", "Channel", "Class", "Length (m)", "Slope (m/m)", "Velocity (m/s)", "Percent full (%)", "Depth / rise", "Depth of section (m)", "Bed width (m)", "Flow 200-year (m³/s)", "Manning n", "Size (depth x width, m)"], [14, 13, 7, 10, 10, 10, 10, 10, 11, 11, 12, 9, 16])
for _, r in rt.iterrows():
    row = R.max_row + 1
    R.append([r.label, r.channel, r.Class, val(r.length_m), val(r.slope), val(r.velocity), val(r.percentfull), val(r.depthtorise), val(r.rise_m), val(r.span_m), val(r.flow), val(r.n), size_formula(f"I{row}", f"J{row}")])
nr = R.max_row; finish(R, "C2")
RB, RD, RF, RI, RJ, RK = (f"Reaches!$B$2:$B${nr}", f"Reaches!$D$2:$D${nr}", f"Reaches!$F$2:$F${nr}", f"Reaches!$I$2:$I${nr}", f"Reaches!$J$2:$J${nr}", f"Reaches!$K$2:$K${nr}")
# ---- Channel sections: aggregates of the Reaches sheet
cs = DF.channel_sections("200yr")
S = sheet("Channel sections", ["Channel", "Class", "Length (km)", "Design flow 200-year (m³/s)", "Bed width, first reach (m)", "Bed width, last reach (m)", "Bed width, min (m)", "Bed width, max (m)", "Depths used (m)", "Velocity, max (m/s)", "Reaches"], [13, 7, 11, 13, 12, 12, 12, 12, 14, 12, 9])
for _, r in cs.iterrows():
    row = S.max_row + 1; a = f"A{row}"
    S.append([r.channel, r.cls, f"=SUMIF({RB},{a},{RD})/1000", f"=_xlfn.MAXIFS({RK},{RB},{a})", f"=INDEX({RJ},MATCH({a},{RB},0))", f"=LOOKUP(2,1/({RB}={a}),{RJ})", f"=_xlfn.MINIFS({RJ},{RB},{a})", f"=_xlfn.MAXIFS({RJ},{RB},{a})",
              ", ".join(f"{float(d):.1f}" for d in r.depths) if isinstance(r.depths, (list, tuple, set)) else str(r.depths), f"=_xlfn.MAXIFS({RF},{RB},{a})", f"=COUNTIF({RB},{a})"])
ns = S.max_row; S.append(["Total", "", f"=SUM(C2:C{ns})", "", "", "", "", "", "", "", f"=SUM(K2:K{ns})"]); finish(S, "C2")
# ---- Size inventory
si = DF.size_inventory()
I = sheet("Size inventory", ["Depth of section (m)", "Bed width (m)", "Size (depth x width, m)", "Reaches", "Length (m)"], [12, 12, 16, 9, 12])
for _, r in si.iterrows():
    row = I.max_row + 1
    I.append([val(r.rise_m), val(r.span_m), size_formula(f"A{row}", f"B{row}"), f"=COUNTIFS({RI},A{row},{RJ},B{row})", f"=SUMIFS({RD},{RI},A{row},{RJ},B{row})"])
ni = I.max_row; I.append(["Total", "", "", f"=SUM(D2:D{ni})", f"=SUM(E2:E{ni})"]); finish(I, "A2")
# ---- Outfalls
ot = DF.outfalls_table()
mh = (ot.invert_m.astype(float) - ot.invert_minus_MHHW.astype(float)).round(3); assert mh.nunique() == 1, mh.unique(); MHHW = float(mh.iloc[0])
mrow = len(ot) + 3
O = sheet("Outfalls", ["Outfall", "Channel", "Flow 200-year (m³/s)", "Bed width (m)", "Invert (m)", "Existing ground (m)", "Flow depth 200-year (m)", "Invert above MHHW (m)"], [12, 13, 12, 11, 10, 12, 13, 13])
for _, r in ot.iterrows():
    row = O.max_row + 1
    O.append([r.outfall, r.channel, val(r.Q200), val(r.width_m), val(r.invert_m), val(r.ground_m), val(r.depth_m), f"=E{row}-$B${mrow}"])
O.append([]); O.append(["MHHW (m)", MHHW]); O.cell(row=O.max_row, column=2).font = BLUE; finish(O, "C2"); O.cell(row=mrow, column=2).font = BLUE
# ---- Proposed culverts: design data; costs in the BOQ
cv = DF.culverts()
PH = ["ID", "Road", "Channel", "Reach", "Station (m)", "Flow 200-year (m³/s)", "Channel bed width (m)", "Channel depth (m)", "Cells", "Cell width (m)", "Cell height (m)", "Cells x width x height (m)", "Overall width (m)", "Length across the road (m)", "Slope (m/m)", "Skew (deg)", "Headwater (m)", "Headwater / height", "Control", "Tailwater (m)", "Existing structure", "Existing size (cells x W x H, m)", "Existing barrels", "Existing structures (no.)", "Existing waterway width (m)", "Existing clear height (m)"]
P = sheet("Proposed culverts", PH, [5, 18, 13, 12, 10, 11, 11, 10, 7, 9, 9, 15, 11, 11, 10, 9, 10, 10, 9, 10, 12, 20, 9, 10, 11, 11])
for _, r in cv.iterrows():
    row = P.max_row + 1
    P.append([int(r.id), r.road, r.channel, r.reach, val(r.station_m), val(r.Q200), val(r.channel_width_m), val(r.channel_depth_m), int(r.cells), val(r.cell_width_m), val(r.cell_height_m), f'=I{row}&" x "&TEXT(J{row},"0")&" x "&TEXT(K{row},"0.0")', f"=I{row}*J{row}+(I{row}+1)*0.25",
              val(r.length_m), val(r.slope), val(r.skew_deg), val(r.HW_m), f"=Q{row}/K{row}", r.control, val(r.tailwater_m), r.existing_type, (r.existing_size if str(r.existing_size) not in ("", "nan") else "–"), val(r.existing_barrels), val(r.get("existing_n")), val(r.get("existing_width_m")), val(r.get("existing_H_m"))])
npc = P.max_row; P.append(["Total", "", "", "", "", "", "", "", f"=SUM(I2:I{npc})"]); finish(P, "E2")
# ---- Dykes: depths and height; the typical fill section by formula
dk = DF.dykes()
Dk = sheet("Dykes", ["ID", "Dyke", "Class", "Length (m)", "Wet length (%)", "200-year depth, mean (m)", "Depth, 90 % (m)", "Depth, max (m)", "Height (m)", "Footprint width (m)", "Clearing (m²)", "Excavation, 0.4 m strip (m³)", "Fill (m³)", "Riprap (m³)"], [5, 13, 8, 10, 9, 11, 10, 10, 9, 11, 12, 13, 12, 12])
for _, r in dk.iterrows():
    row = Dk.max_row + 1
    Dk.append([int(r.id), r["name"], r.cls, val(r.L_m), val(r.wet_pct), val(r.depth_mean), val(r.depth_p90), val(r.depth_max), val(r.H_m), f"=4+3*I{row}+3", f"=J{row}*D{row}", f"=0.4*J{row}*D{row}", f"=(I{row}*(4+1.5*I{row})+0.4*J{row})*D{row}", f"=(0.525+0.2)*1.803*I{row}*D{row}"])
nd = Dk.max_row; Dk.append(["", "Total", "", f"=SUM(D2:D{nd})", "", "", "", "", "", "", f"=SUM(K2:K{nd})", f"=SUM(L2:L{nd})", f"=SUM(M2:M{nd})", f"=SUM(N2:N{nd})"]); finish(Dk, "C2")
# ---- Channel quantities (measured) with the land take by class; costs in the BOQ
q = DF.channel_quantities()
NORM = {"Resedential": "Residential"}
classes = sorted({NORM.get(str(k).strip(), str(k).strip()) for lt in q.land_take_ha for k in (lt or {})} - {"", "nan", "None"})
QH = ["Channel", "Class", "Reaches", "Length (m)", "Bed width, min (m)", "Bed width, max (m)", "Cut (m³)", "Fill (m³)", "Clearing (m²)", "Riprap area (m²)", "Corridor (ha)"] + [f"{c} (ha)" for c in classes] + ["Land in cadastral parcels (ha)"]
Q = sheet("Channel quantities", QH, [13, 7, 8, 10, 10, 10, 12, 12, 12, 12, 10] + [11] * len(classes) + [12])
c0 = 12; c1 = 11 + len(classes)
for _, r in q.iterrows():
    row = Q.max_row + 1; lt = {}
    for k, v in (r.land_take_ha or {}).items(): kk = NORM.get(str(k).strip(), str(k).strip()); lt[kk] = lt.get(kk, 0.0) + float(v)
    Q.append([r.channel, r.cls, val(r.reaches), val(r.length_m), val(r.span_min), val(r.span_max), val(r.cut_m3), val(r.fill_m3), val(r.footprint_m2), val(r.protection_m2), val(r.corridor_ha)] + [round(lt.get(c, 0.0), 3) for c in classes] + [f"=SUM({L(c0)}{row}:{L(c1)}{row})"])
nq = Q.max_row; Q.append(["Total", "", f"=SUM(C2:C{nq})"] + [f"=SUM({L(j)}2:{L(j)}{nq})" for j in range(4, len(QH) + 1)]); finish(Q, "C2")
# ---- Land take by class
Lt = sheet("Land take by class", ["Land use (cadastre)", "Area in the corridors (ha)"], [26, 16])
for j, c in enumerate(classes): Lt.append([c, f"='Channel quantities'!{L(c0 + j)}{nq + 1}"])
nl = Lt.max_row; Lt.append(["Total", f"=SUM(B2:B{nl})"]); finish(Lt, "A2")
# ---- Read me
rd.column_dimensions["A"].width = 150
for i, t in enumerate(["Block 04 - channel design tables (200-year design) - Flood Protection Scheme in North and South Al Batinah", "",
    "Reaches: every reach of the hydraulic model (200-year design, dams in place): length, slope, velocity, percent full, section depth and bed width, design flow; the size text is a formula.",
    "Channel sections: per channel, aggregated from the Reaches sheet by formula (length, largest reach flow, first / last / min / max bed width, max velocity, number of reaches).",
    "Size inventory: the sections used, counted and measured on the Reaches sheet by formula.",
    "Outfalls: the channel ends at the sea: design flow, bed width, invert, existing ground; the 200-year flow depth at the outfall (hydraulic result) and the invert above MHHW by formula (MHHW in the blue cell under the table).",
    "Proposed culverts: the design data of the road crossings (cells of 4 m clear width, the full channel depth as clear height); the size text, the overall width and the headwater ratio by formula; the headwater check (inlet and outlet control) as values. Quantities and costs: the BOQ workbook.",
    "Dykes: the 200-year flood depth along each dyke, the adopted height, and the quantities of the typical fill section by formula (footprint 4 + 3H + 3 m, a 0.4 m strip, the fill, riprap on both faces). Costs: the BOQ workbook.",
    "Channel quantities: cut, fill, clearing and riprap area measured on the designed sections against the 0.5 m terrain model, the corridor area and the land take by land use of the cadastre. Costs: the BOQ workbook.",
    "Land take by class: the land-use totals of the corridors by formula.", "",
    "Every derived number in this workbook is a live formula; measured and modelled values (terrain quantities, hydraulic results, flood depths) are values. Every cost is in 'Block 04 - BOQ and cost estimate.xlsx', a formula on a quantity and a rate."], 1):
    rd.cell(row=i, column=1, value=t).font = Font(name="Arial", size=10, bold=(i == 1))
path = os.path.join(OUT, "Block 04 - Channel design tables (200-year).xlsx"); wb.save(path); print("written", path, "| reaches", nr - 1, "channels", ns - 1, "outfalls", len(ot), "culverts", npc - 1, "dykes", nd - 1)
