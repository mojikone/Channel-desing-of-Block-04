"""Step 11 - reservoir volume reduction by sedimentation, eight dams, 50- and 100-year horizons.

Method: USBR Erosion and Sedimentation Manual, Chapter 2, Section 2.6, with the engine of the Wadi Majlas study
(scripts/reservoir_sedimentation, validated against the manual's worked examples):
  2.6.1 sediment supply = RUSLE yield x Williams SDR (step 09, m3/km2/yr at 1.5 t/m3) x catchment area x horizon; trap efficiency 100 %
  2.6.2 deposited unit weight from the catchment topsoil texture (SoilGrids 0-5 cm, RUSLE input), Lara & Pemberton, operation 3
        (reservoir normally empty: flood-protection dams drain after each event); the yield volume is re-expressed at that density
  2.6.3 Empirical Area-Reduction Method: reservoir type from the shape factor m, new zero-capacity elevation, revised area and
        capacity at every 0.5 m step below FSL; above FSL the original increments are kept
Inputs : sediment/sediment_yield.csv, sediment/catchments/Dam_catchments.gpkg, reservoirs/EAV_<dam>.csv (areas; volumes by the
         conic formula as in the EAV workbook), rusle/Data/SoilGrids/{sand,silt,clay}_0-5cm_mean.tif, dams shapefile (FSL, crest)
Writes : sediment/reservoir_sedimentation_summary.csv, sediment/revised_eav/<dam>_<T>yr.csv, sediment/figures/*.png,
         sediment/Block04_Reservoir_Sedimentation.xlsx (formulas for 2.6.1-2.6.2, engine values for 2.6.3)
"""
import sys, math
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio import mask as rmask
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.chart.series import SeriesLabel, StrRef
from openpyxl.chart.layout import Layout, ManualLayout
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DAMS9 as DAMS, label, RESERVOIRS, DAMS_SHP, W3, ensure
from reservoir_sedimentation import density, distribution
from reservoir_sedimentation.eav import EAVCurve
from xlstyle import style_chart
import figstyle as FS; FS.apply()
figstyle = FS

SED = W3 / "sediment"; REV = ensure(SED / "revised_eav"); FIG = ensure(SED / "figures")
HORIZONS = (50, 100); OPERATION = 3; TE = 1.0; REF_DENSITY = 1500.0   # kg/m3 of the step-09 yield volume (Block 6 convention 1.5 t/m3)
WC = {1: (416.0, 1120.0, 1550.0), 2: (561.0, 1140.0, 1550.0), 3: (641.0, 1150.0, 1550.0), 4: (961.0, 1170.0, 1550.0)}; KC = {1: (256.0, 91.0, 0.0), 2: (135.0, 29.0, 0.0), 3: (0.0, 0.0, 0.0), 4: (0.0, 0.0, 0.0)}
yld = pd.read_csv(SED / "sediment_yield.csv").set_index("name"); cat = gpd.read_file(SED / "catchments" / "Dam_catchments9.gpkg").set_index("name"); dams = gpd.read_file(DAMS_SHP).set_index("Dam Name")

def conic_volume(z, a_m2):
    v = np.zeros_like(z, dtype=float)
    for i in range(1, len(z)): v[i] = v[i - 1] + (z[i] - z[i - 1]) / 3.0 * (a_m2[i - 1] + a_m2[i] + math.sqrt(a_m2[i - 1] * a_m2[i]))
    return v

def texture(dam):
    """Catchment mean clay / silt / sand fractions from the SoilGrids 0-5 cm rasters downloaded for RUSLE (g/kg)."""
    geom = cat.loc[dam, "geometry"]; out = {}
    for prop in ("clay", "silt", "sand"):
        with rasterio.open(SED / "rusle" / "Data" / "SoilGrids" / f"{prop}_0-5cm_mean.tif") as src:
            g = gpd.GeoSeries([geom], crs=cat.crs).to_crs(src.crs).iloc[0]; arr, _ = rmask.mask(src, [g], crop=True, nodata=-32768); a = arr[0].astype(float); a = a[(a > 0) & (a < 1000)]
            out[prop] = float(a.mean()) / 1000.0
    s = sum(out.values()); return {k: v / s for k, v in out.items()}

rows = []; curves = {}
for dam in DAMS:
    eav = pd.read_csv(RESERVOIRS / f"EAV_{dam.replace(' ', '_')}.csv"); z = eav.elevation_m.values; a = eav.area_km2.values * 1e6; v = conic_volume(z, a)
    curve = EAVCurve(z, a, v); fsl = float(dams.loc[dam, "FSL"]); crest = float(dams.loc[dam, "Crest El"]); bottom = float(z[0]); tex = texture(dam)
    area_km2 = float(cat.loc[dam, "area_km2"]); y = float(yld.loc[dam, "yield_m3_km2_yr"])
    W1 = density.initial_unit_weight(tex["clay"], tex["silt"], tex["sand"], OPERATION, units="metric"); K = density.k_factor(tex["clay"], tex["silt"], tex["sand"], OPERATION, units="metric")
    m = distribution.reservoir_shape_m(curve, bottom=bottom, top=fsl); rtype = distribution.classify_type(m)
    for T in HORIZONS:
        gross = y * area_km2 * T; trapped = gross * TE; WT = density.compacted_unit_weight(W1, K, T); deposited = trapped * REF_DENSITY / WT
        d = distribution.distribute(curve, deposited, reservoir_type=rtype, top=fsl, bottom=bottom)
        cap0 = curve.volume_at(fsl); cap1 = float(np.interp(fsl, d.elevation, d.revised_capacity))
        cons = (d.total_sediment - deposited) / deposited * 100 if deposited else 0.0
        if abs(cons) > 2: print(f"WARNING {dam} {T} yr: distributed sediment differs from the deposited volume by {cons:.1f} %")
        rows.append(dict(dam=dam, horizon_yr=T, area_km2=area_km2, yield_m3_km2_yr=y, yield_m3_yr=round(y * area_km2), clay=round(tex["clay"], 3), silt=round(tex["silt"], 3), sand=round(tex["sand"], 3),
                         W1_kg_m3=round(W1, 1), K=round(K, 2), WT_kg_m3=round(WT, 1), gross_Mm3=round(gross / 1e6, 4), deposited_Mm3=round(deposited / 1e6, 4), shape_m=round(m, 3), reservoir_type=rtype,
                         bottom_m=bottom, fsl_m=fsl, crest_m=crest, new_zero_m=round(d.new_zero_elevation, 2), bed_rise_m=round(d.new_zero_elevation - bottom, 2),
                         sediment_balance_pct=round(cons, 2), capacity_fsl_Mm3=round(cap0 / 1e6, 3), revised_capacity_fsl_Mm3=round(cap1 / 1e6, 3), loss_Mm3=round((cap0 - cap1) / 1e6, 3), loss_pct=round((cap0 - cap1) / cap0 * 100, 2),
                         area_fsl_km2=round(curve.area_at(fsl) / 1e6, 3), revised_area_fsl_km2=round(float(np.interp(fsl, d.elevation, d.revised_area)) / 1e6, 3)))
        tbl = pd.DataFrame(dict(elevation_m=d.elevation, original_area_km2=d.original_area / 1e6, sediment_area_km2=d.sediment_area / 1e6, revised_area_km2=d.revised_area / 1e6,
                                original_capacity_Mm3=d.original_capacity / 1e6, sediment_below_Mm3=d.sediment_volume_below / 1e6, revised_capacity_Mm3=d.revised_capacity / 1e6)).round(5)
        tbl.to_csv(REV / f"{dam.replace(' ', '_')}_{T}yr.csv", index=False); curves[(dam, T)] = tbl
S = pd.DataFrame(rows); S.to_csv(SED / "reservoir_sedimentation_summary.csv", index=False); pd.set_option("display.width", 250)
print(S[["dam", "horizon_yr", "yield_m3_km2_yr", "WT_kg_m3", "deposited_Mm3", "sediment_balance_pct", "shape_m", "reservoir_type", "new_zero_m", "capacity_fsl_Mm3", "revised_capacity_fsl_Mm3", "loss_pct"]].to_string(index=False))

# ---- figures: revised curve per dam (50-yr and 100-yr capacity, 50-yr area) + loss summary
GREY, BLUE, RED, ORANGE, TEAL = FS.GREY, FS.BLUE, FS.RED, FS.ORANGE, FS.TEAL
for dam in DAMS:
    t50 = curves[(dam, 50)]; t100 = curves[(dam, 100)]; fsl = float(dams.loc[dam, "FSL"]); r50 = S[(S.dam == dam) & (S.horizon_yr == 50)].iloc[0]; r100 = S[(S.dam == dam) & (S.horizon_yr == 100)].iloc[0]
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    ax.plot(t50.original_capacity_Mm3, t50.elevation_m, color=BLUE, lw=1.6, label="capacity, original"); ax.plot(t50.revised_capacity_Mm3, t50.elevation_m, color=ORANGE, lw=1.6, ls="--", label=f"capacity after 50 years (−{r50.loss_pct:.1f} %)")
    ax.plot(t100.revised_capacity_Mm3, t100.elevation_m, color=RED, lw=1.3, ls=":", label=f"capacity after 100 years (−{r100.loss_pct:.1f} %)")
    ax.axhline(fsl, color=GREY, lw=0.8, ls="--"); ax.set_xlabel("capacity, Mm³"); ax.set_ylabel("elevation, m"); ax.set_xlim(left=0)
    ax2 = ax.twiny(); ax2.plot(t50.original_area_km2, t50.elevation_m, color=TEAL if "TEAL" in dir() else "#2E75B6", lw=1.2, ls="-.", label="area, original"); ax2.plot(t50.revised_area_km2, t50.elevation_m, color="#7F3C8D", lw=1.2, ls="-.", label="area after 50 years")
    ax2.set_xlim(ax2.get_xlim()[1] * 1.05, 0); ax2.set_xlabel("water-surface area, km²"); ax2.tick_params(labelsize=7.5, colors=FS.MUTED); ax2.spines["top"].set_color(FS.AXIS)
    ax.text(0.02, (fsl - ax.get_ylim()[0]) / (ax.get_ylim()[1] - ax.get_ylim()[0]) + 0.02, f"FSL {fsl:.0f} m: {r50.capacity_fsl_Mm3:.1f} Mm³ original, {r50.revised_capacity_fsl_Mm3:.1f} after 50 years", transform=ax.transAxes, fontsize=7, color=GREY)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, loc="lower right", fontsize=7); FS.finish(ax, "both")
    ax.set_title(f"{label(dam)}: reservoir curves before and after sedimentation (bed at the dam rises to {r50.new_zero_m:.1f} m after 50 years, {r100.new_zero_m:.1f} m after 100)", loc="left", fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / f"eav_revised_{dam.replace(' ', '_')}.png", dpi=200); plt.close(fig)
fig, ax = plt.subplots(figsize=(7.6, 3.2)); x = np.arange(len(DAMS)); w = 0.38
l50 = [S[(S.dam == d) & (S.horizon_yr == 50)].loss_pct.iloc[0] for d in DAMS]; l100 = [S[(S.dam == d) & (S.horizon_yr == 100)].loss_pct.iloc[0] for d in DAMS]
b1 = ax.bar(x - w / 2, l50, w, color=FS.BLUE, label="50 years"); b2 = ax.bar(x + w / 2, l100, w, color=FS.ORANGE, label="100 years")
for b, v in list(zip(b1, l50)) + list(zip(b2, l100)): ax.text(b.get_x() + b.get_width() / 2, v + 0.15, f"{v:.1f}", ha="center", fontsize=6.8, color=GREY)
ax.set_xticks(x); ax.set_xticklabels([label(d, True) for d in DAMS], fontsize=7.5, rotation=20); ax.set_ylabel("storage lost at FSL, %", fontsize=8); ax.legend(frameon=False, fontsize=7.5)
figstyle.finish(ax); fig.tight_layout(); fig.savefig(FIG / "storage_loss_summary.png", dpi=200); plt.close(fig)

# ---- workbook
FONT = "Arial"; HDR_FILL = PatternFill("solid", fgColor="1F4E79"); KEY = PatternFill("solid", fgColor="DDEBF7"); thin = Side(style="thin", color="BFBFBF"); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
F = lambda **k: Font(name=FONT, size=k.pop("size", 10), **k); BLUE_IN = Font(name=FONT, size=10, color="0000FF"); GREYF = Font(name=FONT, size=9, color="7F7F7F")
def hdr(ws, row, labels, widths=None, height=54):
    for j, lab in enumerate(labels, 1):
        c = ws.cell(row=row, column=j, value=lab); c.font = F(bold=True, color="FFFFFF"); c.fill = HDR_FILL; c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); c.border = BOX
    ws.row_dimensions[row].height = height
    if widths:
        for j, wd in enumerate(widths, 1): ws.column_dimensions[L(j)].width = wd
wb = Workbook(); ws = wb.active; ws.title = "Summary"
ws["A1"] = "Block 04 dams - reservoir volume reduction by sedimentation (USBR Erosion and Sedimentation Manual, Section 2.6)"; ws["A1"].font = F(bold=True, size=12)
# inputs block
ws["A3"] = "Inputs"; ws["A3"].font = F(bold=True)
inputs = [("Trap efficiency (fraction)", TE, "0.00"), ("Reservoir operation (USBR 2.6.2): 3 = normally empty", OPERATION, "0"), ("Reference density of the step-09 yield volume (kg/m³)", REF_DENSITY, "0"),
          ("Wc, Wm, Ws for the operation (kg/m³)", None, None), ("Kc, Km, Ks for the operation", None, None)]
for i, (lab, v, fm) in enumerate(inputs):
    ws.cell(row=4 + i, column=1, value=lab).font = F()
    if v is not None: c = ws.cell(row=4 + i, column=2, value=v); c.font = BLUE_IN; c.number_format = fm; c.fill = KEY
for j, v in enumerate(WC[OPERATION]): c = ws.cell(row=7, column=2 + j, value=v); c.font = BLUE_IN; c.fill = KEY
for j, v in enumerate(KC[OPERATION]): c = ws.cell(row=8, column=2 + j, value=v); c.font = BLUE_IN; c.fill = KEY
cols = ["Dam", "Horizon (yr)", "Catchment (km²)", "Sediment yield (m³/km²/yr) at 1.5 t/m³", "Sediment yield (m³/yr)", "Clay", "Silt", "Sand", "W1 initial unit weight (kg/m³)", "K", "WT after T years (kg/m³)",
        "Gross sediment (Mm³)", "Trapped (Mm³)", "Deposited at WT (Mm³)", "Shape factor m", "Reservoir type", "Bed at dam (m)", "FSL (m)", "New zero-capacity elevation (m)", "Bed rise (m)",
        "Original capacity at FSL (Mm³)", "Revised capacity at FSL (Mm³)", "Storage lost (Mm³)", "Storage lost (%)", "Area at FSL (km²)", "Revised area at FSL (km²)"]
hdr(ws, 10, cols, [15, 8, 10, 13, 11, 7, 7, 7, 11, 7, 11, 10, 10, 11, 8, 8, 9, 8, 12, 8, 12, 12, 10, 9, 10, 11])
for i, r in enumerate(S.itertuples(), 11):
    vals = [r.dam, r.horizon_yr, r.area_km2, r.yield_m3_km2_yr, f"=D{i}*C{i}", r.clay, r.silt, r.sand, f"=$B$7*F{i}+$C$7*G{i}+$D$7*H{i}", f"=$B$8*F{i}+$C$8*G{i}+$D$8*H{i}",
            f"=I{i}+0.4343*J{i}*(B{i}/(B{i}-1)*LN(B{i})-1)", f"=E{i}*B{i}/1000000", f"=L{i}*$B$4", f"=M{i}*$B$6/K{i}", r.shape_m, r.reservoir_type, r.bottom_m, r.fsl_m, r.new_zero_m, f"=S{i}-Q{i}",
            r.capacity_fsl_Mm3, r.revised_capacity_fsl_Mm3, f"=U{i}-V{i}", f"=W{i}/U{i}", r.area_fsl_km2, r.revised_area_fsl_km2]
    fm = ["@", "0", "0.00", "0.0", "#,##0", "0.000", "0.000", "0.000", "0", "0.0", "0", "0.000", "0.000", "0.000", "0.00", "0", "0.0", "0.0", "0.00", "0.00", "0.000", "0.000", "0.000", "0.0%", "0.000", "0.000"]
    for j, (v, f) in enumerate(zip(vals, fm), 1):
        c = ws.cell(row=i, column=j, value=v); c.number_format = f; c.border = BOX; c.font = BLUE_IN if (isinstance(v, (int, float)) and j > 2) else F(bold=(j == 1))
n = 11 + len(S)
notes = ["Blue = data (step 09 yield, SoilGrids texture, engine results of 2.6.3), black = formulas. Sediment yield = RUSLE soil loss x Williams (1977) SDR (sediment/B4_DAM_RUSLE.xlsx), expressed as a volume at 1.5 t/m³.",
         "2.6.2: W1 = Wc pc + Wm pm + Ws ps (Lara & Pemberton); WT = W1 + 0.4343 K (T/(T-1) ln T - 1) (Miller); operation 3 (reservoir normally empty) gives K = 0, so WT = W1. The deposited volume = trapped volume x 1500 / WT.",
         "2.6.3: Empirical Area-Reduction Method (Borland & Miller / Lara): reservoir type from the shape factor m (ln capacity vs ln depth), new zero-capacity elevation from the sediment volume, sediment area a = C p^A (1-p)^B scaled to the volume; computed by the validated engine of the Majlas study (W3/scripts/reservoir_sedimentation). Revised curves per dam on the 'Revised' sheets and in sediment/revised_eav/.",
         "Trap efficiency 100 % is conservative for storage (flood-protection reservoirs that drain through outlets pass part of the fines; Brune's curve needs the mean annual inflow, not available). Deposition above FSL neglected.",
         "Original curves: areas from the 10 m DEM inside the crest polygon, conic volumes, as in Block04_Dams_Elevation_Area_Volume.xlsx."]
for k, t in enumerate(notes): ws.cell(row=n + 1 + k, column=1, value=t).font = GREYF
ws.freeze_panes = "C11"
for dam in DAMS:
    sh = wb.create_sheet(f"Revised {dam}"[:31]); q = f"'{sh.title}'"; t50 = curves[(dam, 50)]; t100 = curves[(dam, 100)]; fsl = float(dams.loc[dam, "FSL"])
    sh["A1"] = f"{dam} - original and revised elevation-area-capacity (Empirical Area-Reduction Method)"; sh["A1"].font = F(bold=True, size=12)
    hdr(sh, 3, ["Elevation (m)", "Original area (km²)", "Sediment area 50 yr (km²)", "Revised area 50 yr (km²)", "Original capacity (Mm³)", "Sediment below 50 yr (Mm³)", "Revised capacity 50 yr (Mm³)", "Revised area 100 yr (km²)", "Revised capacity 100 yr (Mm³)"], [12, 12, 12, 12, 12, 12, 12, 12, 12], 48)
    for i, (r50, r100) in enumerate(zip(t50.itertuples(index=False), t100.itertuples(index=False)), 4):
        vals = [r50.elevation_m, r50.original_area_km2, r50.sediment_area_km2, r50.revised_area_km2, r50.original_capacity_Mm3, r50.sediment_below_Mm3, r50.revised_capacity_Mm3, r100.revised_area_km2, r100.revised_capacity_Mm3]
        for j, v in enumerate(vals, 1): c = sh.cell(row=i, column=j, value=float(v)); c.number_format = "0.0" if j == 1 else "0.0000"; c.font = BLUE_IN; c.border = BOX
    last = 3 + len(t50); sh["K3"] = "FSL (m)"; sh["L3"] = fsl; sh["L3"].font = BLUE_IN; sh["K4"] = "x for FSL line"; sh["L4"] = 0; sh["L5"] = f"=MAX(E4:E{last})*1.02"; sh["M4"] = "=L3"; sh["M5"] = "=L3"
    sh["K7"] = '="Original"'; sh["K8"] = '="After 50 years"'; sh["K9"] = '="After 100 years"'; sh["K10"] = '="FSL "&TEXT(L3,"0.0")&" m"'
    ch = ScatterChart(); ch.title = f"{dam} - capacity before and after sedimentation"; ch.style = 2; ch.height = 9.5; ch.width = 17; ch.x_axis.title = "Capacity (Mm³)"; ch.y_axis.title = "Elevation (m)"
    ch.x_axis.delete = False; ch.y_axis.delete = False; ch.x_axis.scaling.min = 0; ch.x_axis.number_format = "0"; ch.y_axis.number_format = "0"; ch.x_axis.majorGridlines = None; ch.legend.position = "b"; ch.title.overlay = False; ch.legend.overlay = False
    ch.layout = Layout(manualLayout=ManualLayout(layoutTarget="inner", xMode="edge", yMode="edge", x=0.13, y=0.13, w=0.83, h=0.58)); style_chart(ch)
    ys = Reference(sh, min_col=1, min_row=4, max_row=last)
    for col, name_cell, colour, dash in ((5, "$K$7", "1F4E79", None), (7, "$K$8", "C55A11", "dash"), (9, "$K$9", "C00000", "sysDot")):
        s = Series(ys, Reference(sh, min_col=col, min_row=4, max_row=last), title=None); s.tx = SeriesLabel(strRef=StrRef(f"{q}!{name_cell}")); s.marker.symbol = "none"; s.smooth = False
        s.graphicalProperties.line.solidFill = colour; s.graphicalProperties.line.width = 19050
        if dash: s.graphicalProperties.line.dashStyle = dash
        ch.series.append(s)
    s = Series(Reference(sh, range_string=f"{q}!$M$4:$M$5"), Reference(sh, range_string=f"{q}!$L$4:$L$5"), title=None); s.tx = SeriesLabel(strRef=StrRef(f"{q}!$K$10")); s.marker.symbol = "none"; s.graphicalProperties.line.solidFill = "7F7F7F"; s.graphicalProperties.line.dashStyle = "dash"; s.graphicalProperties.line.width = 12700; ch.series.append(s)
    sh.add_chart(ch, "K12"); sh.freeze_panes = "A4"
for s_ in wb.worksheets:
    for row in s_.iter_rows():
        for c in row:
            if c.font is None or c.font.name != FONT: c.font = Font(name=FONT, size=c.font.size or 10, bold=c.font.bold, color=c.font.color)
out = SED / "Block04_Reservoir_Sedimentation.xlsx"; wb.save(out); print("written", out)
