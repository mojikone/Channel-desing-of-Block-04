"""Step 12 - climate at the dams from the NASA POWER record (step 10): workbook with formulas, figures, summary JSON.

All eight dams lie in one POWER grid cell (0.5 x 0.625 deg), so the record is identical for every dam; the workbook
and the figures carry the single record and name the dams it applies to. Per-catchment mean annual rainfall from the
1 km SM2RAIN climatology (RUSLE input) is added when available, to show the mountain-to-plain gradient the coarse grid hides.
Workbook  climate/Block04_Climate.xlsx : Read me, Daily (data), Monthly (formulas), Annual (formulas), Wind (sector table), Dams
Figures   climate/figures/monthly_climate.png, annual_rainfall.png, windrose_annual.png, windrose_seasons.png
Summary   climate/climate_summary.json (numbers quoted in the report)
"""
import sys, json, math
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.chart import LineChart, BarChart, RadarChart, Reference, Series
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.drawing.image import Image as XLImage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DAMS, W3, ensure
from xlstyle import style_chart
import figstyle; figstyle.apply()

CL = W3 / "climate"; FIG = ensure(CL / "figures"); DATA = CL / "data"
cells = pd.read_csv(DATA / "cells.csv"); src_dam = cells.dam.iloc[0].replace(" ", "_")
D = pd.read_csv(DATA / src_dam / "power_daily_2001_2024.csv", parse_dates=["date"]); W = pd.read_csv(DATA / src_dam / "power_hourly_wind_2015_2024.csv", parse_dates=["datetime_lst"])
D = D[(D.t_mean_c > -90) & (D.rain_mm >= 0)].reset_index(drop=True); W = W[(W.ws10m_ms >= 0) & (W.wd10m_deg >= 0)].reset_index(drop=True)
# 2024 is excluded: the POWER record carries 1 312 mm in August 2024 (272.8 mm on 18 Aug 2024), an artefact of the
# near-real-time precipitation stream - no such event occurred on the Batinah; 2001-2023 gives a 100 mm/yr mean.
YEAR_END = 2023; EXCLUDED_NOTE = "2024 excluded from the daily record: August 2024 carries 1 312 mm (272.8 mm on 18 August), an artefact of the near-real-time POWER precipitation stream."
D = D[D.date.dt.year <= YEAR_END].reset_index(drop=True)
D["year"] = D.date.dt.year; D["month"] = D.date.dt.month; years = sorted(D.year.unique()); NY = len(years)
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# ---- statistics (Python side, for figures and the JSON; the workbook recomputes them with formulas)
mon = D.groupby("month").agg(t_mean=("t_mean_c", "mean"), t_max=("t_max_c", "mean"), t_min=("t_min_c", "mean"), t_abs_max=("t_max_c", "max"), t_abs_min=("t_min_c", "min"), rain=("rain_mm", "sum"), wet=("rain_mm", lambda s: (s >= 1).sum()))
mon["rain"] /= NY; mon["wet"] /= NY
ann = D.groupby("year").agg(rain=("rain_mm", "sum"), t_mean=("t_mean_c", "mean"), t_max=("t_max_c", "max"), t_min=("t_min_c", "min"), wet=("rain_mm", lambda s: (s >= 1).sum()), max_day=("rain_mm", "max"))
trend = np.polyfit(ann.index.values, ann.t_mean.values, 1)[0] * 10
# wind: 16 sectors, 5 speed classes, share of hours; direction = where the wind blows FROM
SECT = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]; CLASSES = ["0-2", "2-4", "4-6", "6-8", ">8"]; EDGES = [0, 2, 4, 6, 8, 99]
W["sector"] = ((W.wd10m_deg % 360 + 11.25) // 22.5).astype(int) % 16; W["cls"] = pd.cut(W.ws10m_ms, EDGES, labels=CLASSES, right=False, include_lowest=True)
W["hour"] = W.datetime_lst.dt.hour; W["month"] = W.datetime_lst.dt.month
def rose(sub):
    t = pd.crosstab(sub.sector, sub.cls).reindex(index=range(16), columns=CLASSES, fill_value=0) / len(sub) * 100
    return dict(table=t, mean=float(sub.ws10m_ms.mean()), calm=float((sub.ws10m_ms < 1).mean() * 100), n=len(sub))
R = {"all": rose(W), "night": rose(W[(W.hour >= 20) | (W.hour < 6)]), "summer": rose(W[W.month.isin([5, 6, 7, 8, 9])]), "winter": rose(W[W.month.isin([11, 12, 1, 2, 3])])}
tot = R["all"]["table"].sum(axis=1); top = tot.sort_values(ascending=False)
# per-catchment rainfall from SM2RAIN (1 km monthly climatology), if the RUSLE inputs are present
sm = {}
try:
    import rasterio, geopandas as gpd
    from rasterio import mask as rmask
    cat = gpd.read_file(W3 / "sediment" / "catchments" / "Dam_catchments.gpkg"); smdir = W3 / "sediment" / "rusle" / "Data" / "SM2RAIN"
    files = sorted(smdir.glob("sm2rain_*.tif"))
    if len(files) == 12:
        for dam in DAMS:
            g = cat[cat.name == dam].to_crs(rasterio.open(files[0]).crs).geometry.iloc[0]; s = 0.0
            for f in files:
                with rasterio.open(f) as srcr:
                    a, _ = rmask.mask(srcr, [g], crop=True, nodata=np.nan); a = a[0]; a = a[np.isfinite(a) & (a > -1)]; s += float(a.mean())
            sm[dam] = round(s, 0)
except Exception as e:
    print("SM2RAIN per-catchment rainfall skipped:", str(e)[:80])
summary = dict(source="NASA POWER (MERRA-2), daily 2001-2024, hourly wind 2015-2024, one grid cell for all eight dams", years=[int(years[0]), int(years[-1])],
               t_mean=round(float(D.t_mean_c.mean()), 1), t_max_mean_month=MONTHS[int(mon.t_max.idxmax()) - 1], t_max_month_value=round(float(mon.t_max.max()), 1),
               t_min_mean_month=MONTHS[int(mon.t_min.idxmin()) - 1], t_min_month_value=round(float(mon.t_min.min()), 1), t_abs_max=round(float(D.t_max_c.max()), 1), t_abs_min=round(float(D.t_min_c.min()), 1),
               rain_mean_annual=round(float(ann.rain.mean()), 0), rain_min_year=[int(ann.rain.idxmin()), round(float(ann.rain.min()), 0)], rain_max_year=[int(ann.rain.idxmax()), round(float(ann.rain.max()), 0)],
               rain_wettest_months=[MONTHS[i - 1] for i in mon.rain.sort_values(ascending=False).index[:3]], rain_share_nov_apr=round(float(mon.rain[[11, 12, 1, 2, 3, 4]].sum() / mon.rain.sum() * 100), 0),
               wet_days_per_year=round(float(ann.wet.mean()), 1), max_daily_rain=[round(float(D.rain_mm.max()), 1), str(D.loc[D.rain_mm.idxmax(), "date"].date())],
               t_trend_c_per_decade=round(float(trend), 2), wind_mean=round(R["all"]["mean"], 1), wind_calm_pct=round(R["all"]["calm"], 0),
               wind_top_sectors=[(SECT[i], round(float(top.iloc[k]), 1)) for k, i in enumerate(top.index[:4])],
               wind_summer_top=SECT[int(R["summer"]["table"].sum(axis=1).idxmax())], wind_winter_top=SECT[int(R["winter"]["table"].sum(axis=1).idxmax())], wind_night_top=SECT[int(R["night"]["table"].sum(axis=1).idxmax())],
               sm2rain_catchment_mm=sm, excluded=EXCLUDED_NOTE)
json.dump(summary, open(CL / "climate_summary.json", "w"), indent=1); print(json.dumps(summary, indent=1)[:1500])

# ---- figures
GREY, RED, BLUE, PALE = figstyle.GREY, figstyle.RED, figstyle.BLUE, figstyle.PALE
style = figstyle.finish
x = np.arange(12)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.6, 5.4), sharex=True, gridspec_kw=dict(height_ratios=[1.3, 1]))
for key, col, lab in (("t_max", RED, "mean daily maximum"), ("t_mean", GREY, "daily mean"), ("t_min", BLUE, "mean daily minimum")):
    a1.plot(x, mon[key], color=col, lw=1.6, marker="o", ms=3.2, label=lab)
    if key != "t_mean":
        for xi, v in zip(x, mon[key]): a1.text(xi, v + 1.0, f"{v:.0f}", ha="center", fontsize=6.8, color=col)
a1.set_ylabel("air temperature at 2 m, °C", fontsize=8); a1.set_ylim(0, 50); a1.legend(frameon=False, fontsize=7.4, loc="lower center", ncol=3); style(a1)
bars = a2.bar(x, mon.rain, width=0.6, color=PALE)
for b, v in zip(bars, mon.rain): a2.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.4, f"{v:.0f}", ha="center", va="bottom", fontsize=6.8, color=GREY)
a2.set_ylabel("rainfall, mm a month", fontsize=8); a2.set_xticks(x); a2.set_xticklabels(MONTHS); a2.set_ylim(0, max(mon.rain) * 1.3); style(a2)
fig.suptitle(f"Monthly temperature and rainfall at the Block 04 dams, {years[0]}-{years[-1]} (NASA POWER, MERRA-2)", fontsize=9, color=GREY); fig.tight_layout(); fig.savefig(FIG / "monthly_climate.png", dpi=200); plt.close(fig)
fig, ax = plt.subplots(figsize=(7.6, 3.0)); ax.bar(ann.index, ann.rain, color=PALE, width=0.7); ax.axhline(ann.rain.mean(), color=GREY, lw=1, ls="--")
ax.text(ann.index[-1] + 0.4, ann.rain.mean(), f"mean {ann.rain.mean():.0f} mm", fontsize=7.4, color=GREY, va="center")
for yv, v in zip(ann.index, ann.rain): ax.text(yv, v + 3, f"{v:.0f}", ha="center", fontsize=6.4, color=GREY)
ax.set_ylabel("annual rainfall, mm", fontsize=8); ax.set_xticks(ann.index); ax.set_xticklabels(ann.index, rotation=90, fontsize=7); style(ax); fig.tight_layout(); fig.savefig(FIG / "annual_rainfall.png", dpi=200); plt.close(fig)
SPEED_COL = ["#C6D6EA", "#8FADD1", "#4F81BD", "#1F497D", "#C0504D"]
def draw_rose(ax, r, title, rmax):
    th = np.deg2rad(np.arange(16) * 22.5); wdt = 2 * np.pi / 16 * 0.86; bottom = np.zeros(16)
    for c, col in zip(CLASSES, SPEED_COL):
        v = r["table"][c].values; ax.bar(th, v, width=wdt, bottom=bottom, color=col, edgecolor="white", linewidth=0.3, zorder=3); bottom += v
    ax.set_theta_zero_location("N"); ax.set_theta_direction(-1); ax.set_xticks(np.deg2rad(np.arange(0, 360, 45))); ax.set_xticklabels(["N", "NE", "E", "SE", "S", "SW", "W", "NW"], fontsize=7.6, color="#404040")
    ticks = list(range(4, int(rmax) + 1, 4)); ax.set_ylim(0, rmax); ax.set_yticks(ticks); ax.set_yticklabels([f"{t} %" for t in ticks], fontsize=6.2, color="#7A7A7A"); ax.set_rlabel_position(78)
    ax.grid(color="#D9D9D9", lw=0.5); ax.spines["polar"].set_color("#BFBFBF"); ax.set_title(f"{title}\nmean {r['mean']:.1f} m/s, below 1 m/s {r['calm']:.0f} % of hours", fontsize=8, color="#404040", pad=10)
names = {"0-2": "under 2 m/s", "2-4": "2 to 4", "4-6": "4 to 6", "6-8": "6 to 8", ">8": "over 8 m/s"}
rmax = 4 * math.ceil(max(R[k]["table"].sum(axis=1).max() for k in R) / 4.0)
fig = plt.figure(figsize=(4.6, 5.0)); ax = fig.add_subplot(111, projection="polar"); draw_rose(ax, R["all"], f"Wind at 10 m, all hours {W.datetime_lst.dt.year.min()}-{W.datetime_lst.dt.year.max()}", rmax)
fig.legend(handles=[Patch(color=c, label=names[k]) for k, c in zip(CLASSES, SPEED_COL)], frameon=False, fontsize=7.2, loc="lower center", ncol=3, title="a bar points to where the wind comes from", title_fontsize=7.2)
fig.tight_layout(rect=(0, 0.1, 1, 1)); fig.savefig(FIG / "windrose_annual.png", dpi=200); plt.close(fig)
fig, axes = plt.subplots(2, 2, figsize=(7.6, 7.9), subplot_kw={"projection": "polar"})
for ax, (k, t) in zip(axes.ravel(), (("all", "All hours"), ("night", "Night, 20:00 to 06:00"), ("summer", "Summer, May to September"), ("winter", "Winter, November to March"))): draw_rose(ax, R[k], t, rmax)
fig.legend(handles=[Patch(color=c, label=names[k]) for k, c in zip(CLASSES, SPEED_COL)], frameon=False, fontsize=7.8, loc="lower center", ncol=5, title="wind speed at 10 m; a bar points to where the wind comes from", title_fontsize=7.8)
fig.tight_layout(rect=(0, 0.06, 1, 1), h_pad=2.2); fig.savefig(FIG / "windrose_seasons.png", dpi=200); plt.close(fig)

# ---- workbook
FONT = "Arial"; HDR_FILL = PatternFill("solid", fgColor="1F4E79"); thin = Side(style="thin", color="BFBFBF"); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
F = lambda **k: Font(name=FONT, size=k.pop("size", 10), **k); BLUE_IN = Font(name=FONT, size=10, color="0000FF"); GREYF = Font(name=FONT, size=9, color="7F7F7F")
def hdr(ws, row, labels, widths=None, height=30):
    for j, lab in enumerate(labels, 1):
        c = ws.cell(row=row, column=j, value=lab); c.font = F(bold=True, color="FFFFFF"); c.fill = HDR_FILL; c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); c.border = BOX
    ws.row_dimensions[row].height = height
    if widths:
        for j, w in enumerate(widths, 1): ws.column_dimensions[L(j)].width = w
wb = Workbook(); rd = wb.active; rd.title = "Read me"
lines = ["Block 04 dams - climate record (NASA POWER, MERRA-2 reanalysis, https://power.larc.nasa.gov)", "",
         f"Daily {years[0]}-{years[-1]}: T2M, T2M_MAX, T2M_MIN (air temperature at 2 m, deg C), PRECTOTCORR (bias-corrected precipitation, mm/day). Hourly {W.datetime_lst.dt.year.min()}-{W.datetime_lst.dt.year.max()}: WS10M (m/s), WD10M (degrees the wind blows FROM), local solar time.",
         "POWER is a modelled record on a grid of about 0.5 x 0.625 degrees (55 x 64 km). All eight dams of Block 04 lie in one cell, so the record is the same for every dam (verified: the eight downloads are identical). It describes the regime; it is not a station record.",
         EXCLUDED_NOTE + " The raw 2001-2024 download is kept in W3/climate/data.",
         "Sheet 'Daily' holds the data (blue); 'Monthly' and 'Annual' are formulas on it; 'Wind' is the sector x speed-class table computed from the hourly series (W3/scripts/12_climate.py); 'Dams' lists the dams and, where available, the mean annual rainfall of each dam catchment from the 1 km SM2RAIN climatology (the RUSLE rainfall input), which shows the mountain-to-plain gradient the POWER grid cannot.",
         f"Downloaded {pd.Timestamp.today():%Y-%m-%d} by W3/scripts/10_fetch_power.py at the dam junction coordinates (W3/climate/data/cells.csv)."]
for i, t in enumerate(lines, 1): rd.cell(row=i, column=1, value=t).font = F(bold=(i == 1), size=12 if i == 1 else 10)
rd.column_dimensions["A"].width = 170
ws = wb.create_sheet("Daily"); hdr(ws, 1, ["Date", "T mean (°C)", "T max (°C)", "T min (°C)", "Rain (mm)", "Year", "Month"], [12, 11, 11, 11, 11, 8, 8])
for i, r in enumerate(D.itertuples(), 2):
    ws.cell(row=i, column=1, value=r.date.to_pydatetime()).number_format = "yyyy-mm-dd"
    for j, v in enumerate((r.t_mean_c, r.t_max_c, r.t_min_c, r.rain_mm), 2): c = ws.cell(row=i, column=j, value=round(float(v), 2)); c.font = BLUE_IN; c.number_format = "0.00"
    ws.cell(row=i, column=6, value=f"=YEAR(A{i})"); ws.cell(row=i, column=7, value=f"=MONTH(A{i})")
nD = 1 + len(D); ws.freeze_panes = "A2"
rng = lambda col: f"Daily!${col}$2:${col}${nD}"
wm = wb.create_sheet("Monthly"); hdr(wm, 1, ["Month", "Mean daily T (°C)", "Mean daily max (°C)", "Mean daily min (°C)", "Absolute max (°C)", "Absolute min (°C)", "Rainfall (mm/month)", "Wet days (≥1 mm)"], [8, 13, 13, 13, 13, 13, 13, 12], 42)
for m in range(1, 13):
    r = 1 + m; wm.cell(row=r, column=1, value=MONTHS[m - 1]).font = F(bold=True)
    forms = [f"=AVERAGEIFS({rng('B')},{rng('G')},{m})", f"=AVERAGEIFS({rng('C')},{rng('G')},{m})", f"=AVERAGEIFS({rng('D')},{rng('G')},{m})", f"=_xlfn.MAXIFS({rng('C')},{rng('G')},{m})", f"=_xlfn.MINIFS({rng('D')},{rng('G')},{m})",
             f"=SUMIFS({rng('E')},{rng('G')},{m})/{NY}", f"=COUNTIFS({rng('G')},{m},{rng('E')},\">=1\")/{NY}"]
    for j, f in enumerate(forms, 2): c = wm.cell(row=r, column=j, value=f); c.number_format = "0.0"; c.border = BOX
wm.cell(row=14, column=1, value="Year").font = F(bold=True)
for j, f in enumerate([f"=AVERAGE({rng('B')})", f"=AVERAGE({rng('C')})", f"=AVERAGE({rng('D')})", f"=MAX({rng('C')})", f"=MIN({rng('D')})", "=SUM(G2:G13)", "=SUM(H2:H13)"], 2): c = wm.cell(row=14, column=j, value=f); c.number_format = "0.0"; c.border = BOX; c.font = F(bold=True)
def lay(ch, x, y, w, h): ch.layout = Layout(manualLayout=ManualLayout(layoutTarget="inner", xMode="edge", yMode="edge", x=x, y=y, w=w, h=h))
ch = LineChart(); ch.title = "Monthly temperature (mean of daily values)"; ch.y_axis.title = "°C"; ch.y_axis.number_format = "0"; ch.x_axis.title = None; ch.height = 7.5; ch.width = 16; ch.style = 2; ch.y_axis.delete = False; ch.x_axis.delete = False
for col, colour in ((3, "C0504D"), (2, "595959"), (4, "1F4E79")):
    s = Series(Reference(wm, min_col=col, min_row=1, max_row=13), title_from_data=True); s.graphicalProperties.line.solidFill = colour; s.graphicalProperties.line.width = 19050; s.marker.symbol = "circle"; s.marker.size = 4; s.smooth = False; ch.series.append(s)
ch.set_categories(Reference(wm, min_col=1, min_row=2, max_row=13)); ch.legend.position = "b"; ch.y_axis.scaling.min = 0; lay(ch, 0.1, 0.14, 0.86, 0.6); style_chart(ch); wm.add_chart(ch, "J2")
bc = BarChart(); bc.title = "Monthly rainfall (mean over the record)"; bc.y_axis.title = "mm"; bc.y_axis.number_format = "0"; bc.height = 7.5; bc.width = 16; bc.style = 2; bc.y_axis.delete = False; bc.x_axis.delete = False
s = Series(Reference(wm, min_col=7, min_row=1, max_row=13), title_from_data=True); s.graphicalProperties.solidFill = "9DC3E6"; bc.series.append(s); bc.set_categories(Reference(wm, min_col=1, min_row=2, max_row=13)); bc.legend = None; lay(bc, 0.1, 0.14, 0.86, 0.68); style_chart(bc); wm.add_chart(bc, "J18")
wa = wb.create_sheet("Annual"); hdr(wa, 1, ["Year", "Rainfall (mm)", "Wet days (≥1 mm)", "Max daily rain (mm)", "Mean T (°C)", "Max T (°C)", "Min T (°C)"], [8, 12, 12, 13, 11, 11, 11], 42)
for k, y in enumerate(years):
    r = 2 + k; wa.cell(row=r, column=1, value=int(y)).font = F(bold=True)
    forms = [f"=SUMIFS({rng('E')},{rng('F')},A{r})", f"=COUNTIFS({rng('F')},A{r},{rng('E')},\">=1\")", f"=_xlfn.MAXIFS({rng('E')},{rng('F')},A{r})", f"=AVERAGEIFS({rng('B')},{rng('F')},A{r})", f"=_xlfn.MAXIFS({rng('C')},{rng('F')},A{r})", f"=_xlfn.MINIFS({rng('D')},{rng('F')},A{r})"]
    for j, f in enumerate(forms, 2): c = wa.cell(row=r, column=j, value=f); c.number_format = "0.0" if j != 3 else "0"; c.border = BOX
r0 = 2 + NY
for k, (lab, fn) in enumerate((("Mean", "AVERAGE"), ("Minimum", "MIN"), ("Maximum", "MAX"), ("Std deviation", "STDEV"))):
    wa.cell(row=r0 + 1 + k, column=1, value=lab).font = F(bold=True)
    for j in range(2, 8): c = wa.cell(row=r0 + 1 + k, column=j, value=f"={fn}({L(j)}2:{L(j)}{r0 - 1})"); c.number_format = "0.0"; c.border = BOX; c.font = F(bold=True)
wa.cell(row=r0 + 6, column=1, value="Trend of annual mean T (°C per decade)").font = F(bold=True); c = wa.cell(row=r0 + 6, column=5, value=f"=SLOPE(E2:E{r0 - 1},A2:A{r0 - 1})*10"); c.number_format = "0.00"
bc = BarChart(); bc.title = "Annual rainfall"; bc.y_axis.title = "mm"; bc.y_axis.number_format = "0"; bc.height = 7.5; bc.width = 18; bc.style = 2; bc.y_axis.delete = False; bc.x_axis.delete = False
s = Series(Reference(wa, min_col=2, min_row=1, max_row=r0 - 1), title_from_data=True); s.graphicalProperties.solidFill = "9DC3E6"; bc.series.append(s); bc.set_categories(Reference(wa, min_col=1, min_row=2, max_row=r0 - 1)); bc.legend = None; lay(bc, 0.08, 0.14, 0.88, 0.66); style_chart(bc); wa.add_chart(bc, "I2")
ww = wb.create_sheet("Wind"); ww["A1"] = f"Wind at 10 m, share of hours (%) by direction the wind blows FROM and speed class - all hours {W.datetime_lst.dt.year.min()}-{W.datetime_lst.dt.year.max()} ({len(W):,} hours)"; ww["A1"].font = F(bold=True)
hdr(ww, 3, ["Sector"] + [f"{c} m/s" for c in CLASSES] + ["All speeds"], [9, 10, 10, 10, 10, 10, 11])
t = R["all"]["table"]
for i, sname in enumerate(SECT):
    r = 4 + i; ww.cell(row=r, column=1, value=sname).font = F(bold=True)
    for j, c in enumerate(CLASSES, 2): cell = ww.cell(row=r, column=j, value=round(float(t.loc[i, c]), 3)); cell.font = BLUE_IN; cell.number_format = "0.0"; cell.border = BOX
    cell = ww.cell(row=r, column=7, value=f"=SUM(B{r}:F{r})"); cell.number_format = "0.0"; cell.border = BOX
ww.cell(row=20, column=1, value="Total").font = F(bold=True)
for j in range(2, 8): c = ww.cell(row=20, column=j, value=f"=SUM({L(j)}4:{L(j)}19)"); c.number_format = "0.0"; c.font = F(bold=True); c.border = BOX
ww.cell(row=22, column=1, value="Mean speed (m/s)").font = F(bold=True); ww.cell(row=22, column=2, value=round(R["all"]["mean"], 2)).font = BLUE_IN
ww.cell(row=23, column=1, value="Calm, below 1 m/s (% of hours)").font = F(bold=True); ww.cell(row=23, column=2, value=round(R["all"]["calm"], 1)).font = BLUE_IN
ww.cell(row=24, column=1, value="Prevailing sector").font = F(bold=True); ww.cell(row=24, column=2, value="=INDEX(A4:A19,MATCH(MAX(G4:G19),G4:G19,0))")
for k, (key, lab) in enumerate((("night", "Night 20:00-06:00"), ("summer", "Summer May-Sep"), ("winter", "Winter Nov-Mar"))):
    c0 = 9 + k * 3; ww.cell(row=3, column=c0, value=lab).font = F(bold=True); ww.cell(row=3, column=c0 + 1, value="% of hours").font = F(bold=True)
    tt = R[key]["table"].sum(axis=1)
    for i, sname in enumerate(SECT): ww.cell(row=4 + i, column=c0, value=sname); ww.cell(row=4 + i, column=c0 + 1, value=round(float(tt.loc[i]), 2)).font = BLUE_IN
rc = RadarChart(); rc.type = "filled"; rc.title = "Wind rose - share of hours by direction (all speeds)"; rc.height = 11; rc.width = 13; rc.style = 2
s = Series(Reference(ww, min_col=7, min_row=3, max_row=19), title_from_data=True); s.graphicalProperties.solidFill = "4F81BD"; s.graphicalProperties.line.solidFill = "1F497D"; rc.series.append(s); rc.set_categories(Reference(ww, min_col=1, min_row=4, max_row=19)); rc.legend = None; rc.y_axis.delete = False; rc.x_axis.delete = False; rc.y_axis.number_format = "0"; style_chart(rc, grid_y=True)
ww.add_chart(rc, "A27")
img = XLImage(str(FIG / "windrose_annual.png")); img.width, img.height = 420, 456; ww.add_image(img, "I27")
wd = wb.create_sheet("Dams"); hdr(wd, 1, ["Dam", "Longitude", "Latitude", "POWER record", "Catchment mean annual rainfall, SM2RAIN 1 km (mm)"], [15, 11, 11, 34, 24], 42)
for i, r in enumerate(cells.itertuples(), 2):
    wd.cell(row=i, column=1, value=r.dam).font = F(bold=True); wd.cell(row=i, column=2, value=r.lon).font = BLUE_IN; wd.cell(row=i, column=3, value=r.lat).font = BLUE_IN
    wd.cell(row=i, column=4, value="same cell as all other dams (identical series)"); v = sm.get(r.dam); c = wd.cell(row=i, column=5, value=v if v is not None else "n/a"); c.font = BLUE_IN
wd.cell(row=11, column=1, value="SM2RAIN: OpenLandMap SM2RAIN v0.3 monthly precipitation climatology (2007-2018), 1 km, zonal mean over each dam catchment; the RUSLE R-factor input (W3/sediment/rusle/Data/SM2RAIN).").font = GREYF
for s_ in wb.worksheets:
    for row in s_.iter_rows():
        for c in row:
            if c.font is None or c.font.name != FONT: c.font = Font(name=FONT, size=c.font.size or 10, bold=c.font.bold, color=c.font.color)
out = CL / "Block04_Climate.xlsx"; wb.save(out); print("written", out, "| daily rows", len(D), "| hourly", len(W), "| figures:", sorted(p.name for p in FIG.glob("*.png")))
