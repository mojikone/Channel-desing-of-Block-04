"""Every number the Block 04 report quotes, read from the W3 outputs (never typed): dams, HMS results, reservoirs,
sediment, climate. Each accessor names its file so a reviewer can reproduce the figure."""
import os, json, re
import pandas as pd, geopandas as gpd

HERE = os.path.dirname(os.path.abspath(__file__)); W8 = os.path.dirname(HERE); CB04 = os.path.dirname(W8); B4 = os.path.dirname(CB04); W3 = os.path.join(CB04, "W3"); W7 = os.path.join(CB04, "W7")
RPS = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr", "1000yr", "2000yr", "5000yr", "10000yr", "PMP"]
RP_LABEL = {rp: (rp.replace("yr", "") if rp != "PMP" else "PMP") for rp in RPS}
DAMS = ["Hawasinah 02", "Hawasinah 11", "Hawasinah EX", "Shafan 02", "Shafan 08", "Sarami 03", "Sarami 05", "Sakhin 04", "Sakhin 08"]   # report order (engineer)
LABEL = {"Hawasinah EX": "Hawasinah UP", "Sakhin 08": "Sakhin 08 (Mehmum)"}
def label(dam, short=False): return ("Sakhin 08" if (short and dam == "Sakhin 08") else LABEL.get(dam, dam))
GCA = {"Hawasinah 02": "HAW", "Hawasinah 11": "HAW", "Hawasinah EX": "HAW", "Shafan 02": "SHA", "Shafan 08": "SHA", "Sarami 03": "SAR", "Sarami 05": "SAR", "Sakhin 04": "SAK", "Sakhin 08": "SAK"}
GCA_NAME = {"HAW": "Al Hawasinah", "SHA": "Shafan", "SAR": "Sarami", "SAK": "Sakhin"}
_c = {}

def dams_sheet():
    """inputs/dams/Dams updated.shp (= Hydrology/XLS/Block 04 Dams.xlsx): crest, FSL, capacity, QPMF, Hmax, C, spillway length."""
    if "dams" not in _c:
        g = gpd.read_file(os.path.join(CB04, "inputs", "dams", "Dams updated.shp")).set_index("Dam Name")
        g["axis_len_m"] = g.geometry.length; _c["dams"] = g
    return _c["dams"]

def catchments():
    """W3/sediment/catchments/Dam_catchments.gpkg: area, weighted CN, subbasins per dam."""
    if "cat" not in _c: _c["cat"] = gpd.read_file(os.path.join(W3, "sediment", "catchments", "Dam_catchments9.gpkg")).set_index("name")
    return _c["cat"]

def controlled_area():
    """Area controlled by the nine dams, km2: the union of their catchments (nested catchments counted once), W3/maps/data/extent.json (step 13)."""
    return float(json.load(open(os.path.join(W3, "maps", "data", "extent.json")))["controlled_km2"])

def dam_summary():
    """W3/dams/data/dam_summary_B3.csv: per dam x rp peak inflow/outflow, volumes, attenuation, peak level (Basin 3 depth-area analyses)."""
    if "ds" not in _c: _c["ds"] = pd.read_csv(os.path.join(W3, "dams", "data", "dam_summary_B4.csv"))
    return _c["ds"]

def peaks(kind="in"):
    """dam x rp table of peak inflow ('in') or outflow ('out'), m3/s."""
    d = dam_summary(); col = "peak_inflow_m3s" if kind == "in" else "peak_outflow_m3s"
    return d.pivot(index="dam", columns="rp", values=col).reindex(DAMS)[RPS]

def volumes(kind="in"):
    d = dam_summary(); col = "vol_in_Mm3" if kind == "in" else "vol_out_Mm3"
    return d.pivot(index="dam", columns="rp", values=col).reindex(DAMS)[RPS]

def levels():
    return dam_summary().pivot(index="dam", columns="rp", values="peak_level_m").reindex(DAMS)[RPS]

def eav_summary():
    """Claude Block 04/reservoirs/summary.csv + conic volumes of the EAV workbook: bed, area/volume at FSL and crest."""
    if "eav" not in _c:
        import openpyxl
        wb = openpyxl.load_workbook(os.path.join(W3, "dams", "eav", "Block04_Dams_Elevation_Area_Volume.xlsx"), data_only=True); ws = wb["Dams"]
        rows = []
        for r in ws.iter_rows(min_row=4, max_row=12, values_only=True):
            if not r[0]: continue
            rows.append(dict(dam={v: k for k, v in LABEL.items()}.get(r[0], r[0]), crest=r[1], fsl=r[2], capacity_sheet=r[3], qpmf_sheet=r[4], hmax=r[5], C=r[6], spill_L=r[7], bed=r[8], height=r[9], A_fsl=r[10], V_fsl=r[11], diff=r[12], A_crest=r[13], V_crest=r[14], lvl_pmp=r[15], head_pmp=r[16], qout_pmp=r[17], qin_pmp=r[18]))
        _c["eav"] = pd.DataFrame(rows).set_index("dam")
    return _c["eav"]

def eav_curve(dam):
    return pd.read_csv(os.path.join(CB04, "reservoirs", f"EAV_{dam.replace(' ', '_')}.csv"))

def sediment_yield():
    """W3/sediment/sediment_yield.csv (RUSLE factors, relief ratio, CN, Williams SDR, yield)."""
    if "sy" not in _c: _c["sy"] = pd.read_csv(os.path.join(W3, "sediment", "sediment_yield.csv")).set_index("name").reindex(DAMS)
    return _c["sy"]

def sedimentation(horizon=50):
    """W3/sediment/reservoir_sedimentation_summary.csv (USBR 2.6 results)."""
    if "sed" not in _c: _c["sed"] = pd.read_csv(os.path.join(W3, "sediment", "reservoir_sedimentation_summary.csv"))
    s = _c["sed"]; return s[s.horizon_yr == horizon].set_index("dam").reindex(DAMS)

def climate():
    """W3/climate/climate_summary.json (NASA POWER 2001-2023, one cell; SM2RAIN catchment rainfall)."""
    if "cl" not in _c: _c["cl"] = json.load(open(os.path.join(W3, "climate", "climate_summary.json"), encoding="utf-8"))
    return _c["cl"]

def climate_monthly():
    """Monthly table recomputed from the daily record (same filter as 12_climate.py)."""
    d = pd.read_csv(os.path.join(W3, "climate", "data", "Hawasinah_02", "power_daily_2001_2024.csv"), parse_dates=["date"]); d = d[d.date.dt.year <= 2023]; ny = d.date.dt.year.nunique()
    m = d.groupby(d.date.dt.month).agg(t_mean=("t_mean_c", "mean"), t_max=("t_max_c", "mean"), t_min=("t_min_c", "mean"), rain=("rain_mm", "sum")); m["rain"] /= ny; return m

# ---- the stormwater report (W8): REPORT_ONLY="SM,SS" restricts every per-channel table to those classes (the class is the suffix of
#      the channel or dyke name: -FP, -SM, -SS); unset, the tables cover the whole scheme
ONLY = {c.strip().upper() for c in os.environ.get("REPORT_ONLY", "").split(",") if c.strip()}
def _cls_of_name(name): return str(name).rsplit("-", 1)[-1].upper()
def only(df, col="channel"):
    """Rows of df whose channel/dyke name (column col) belongs to the REPORT_ONLY classes; df unchanged when no filter is set."""
    if not ONLY or df is None or len(df) == 0 or col not in df.columns: return df
    return df[df[col].map(_cls_of_name).isin(ONLY)].reset_index(drop=True)
_SEG_CLASS = None
def _label_class(label):
    """Class of a hydraulic-model reach label (SHACH12-C3) through the final segment layer."""
    global _SEG_CLASS
    if _SEG_CLASS is None:
        s = gpd.read_file(os.path.join(W7, "final", "Block4_design_segments.shp"))[["SGLabel", "Class"]]; _SEG_CLASS = dict(zip(s.SGLabel, s.Class))
    return str(_SEG_CLASS.get(label, "")).upper()
def only_labels(df, col="label"):
    if not ONLY or df is None or len(df) == 0 or col not in df.columns: return df
    return df[df[col].map(_label_class).isin(ONLY)].reset_index(drop=True)
SG_RUN = "run_20261012_1758"   # the SewerGEMS run the report quotes; step 68 sets it to the R9 run of W7 before the build
def channel_sections(rp="200yr"):
    """Per channel: class, length (km, the sum of its design segments), the 200-year design flow (the largest reach flow on the
    channel, m3/s), the bed width of its first and last designed section (m) and the depths used (m), from the class-resolved
    export W7/sewergems/results/<SG_RUN>/bridge_exports/conduits_<rp>.csv on the final segment layer."""
    import re
    c = pd.read_csv(os.path.join(W7, "sewergems", "results", SG_RUN, "bridge_exports", f"conduits_{rp}.csv"))
    seg = gpd.read_file(os.path.join(W7, "final", "Block4_design_segments.shp"))[["SGLabel", "Channel", "Class", "Seg", "Length"]]
    m = seg.merge(c[["label", "flow", "span_m", "rise_m", "slope", "velocity"]], left_on="SGLabel", right_on="label", how="left").sort_values(["Channel", "Seg"])
    rows = []
    for ch, g in m.groupby("Channel", sort=False):
        rows.append(dict(channel=ch, cls=g.Class.iloc[0], km=g.Length.sum() / 1000, q=g.flow.max(), wfirst=g.span_m.iloc[0], wlast=g.span_m.iloc[-1], wmin=g.span_m.min(), wmax=g.span_m.max(),
                         depths=sorted(set(g.rise_m.dropna().round(1))), vmax=g.velocity.max(), n=len(g)))
    df = pd.DataFrame(rows); order = {"HAW": 0, "SHA": 1, "SAR": 2, "SAK": 3}
    df["k"] = df.channel.map(lambda s: (order.get(s[:3], 9), int(re.search(r"CH(\d+)", s).group(1))))
    return only(df.sort_values("k").drop(columns="k").reset_index(drop=True))

DATA_W7 = os.path.join(W8, "report", "data")   # the W8 copies of the W7 tables
def subbasins_dam():
    """Basin 6 subbasins with dam = 1 when a reservoir lies downstream of them (W7/elements/shp/B6/Subbasins_B6_dam.shp)."""
    return gpd.read_file(os.path.join(W7, "elements", "shp", "B6", "Subbasins_B6_dam.shp"))[["name", "area_km2", "dam", "inter"]]   # inter = 1: no dam anywhere upstream (his definition, 2026-10-12)
def size_inventory():
    if not ONLY: return pd.read_csv(os.path.join(DATA_W7, "size_inventory.csv"))
    rt = reach_table(); g = rt.groupby("size", sort=False)["length_m"].sum().reset_index(); g.columns = ["size", "Length"]
    g["k"] = g["size"].map(lambda s: tuple(float(x) for x in str(s).replace("m", "").split("x"))); return g.sort_values("k").drop(columns="k").reset_index(drop=True)
def reach_table(): return only_labels(pd.read_csv(os.path.join(DATA_W7, "reach_table.csv")))
def outfalls_table(): return only(pd.read_csv(os.path.join(DATA_W7, "outfalls.csv")))
def culverts():
    """W8/culverts (R5 rules: clear height = channel depth, existing culverts within 10 m, slope = channel slope)."""
    c = pd.read_csv(os.path.join(W8, "culverts", "culverts_proposed.csv"), keep_default_na=False)
    c["existing_type"] = c.existing_type.replace("", "None"); c["existing_barrels"] = pd.to_numeric(c.existing_barrels, errors="coerce").fillna(0); return only(c)
LAND_RATE_OMR_HA = {"Agricultural": 50189.0, "Commercial": 1486900.0, "Industrial": 1500000.0, "Residential": 754797.0, "Roads": 330061.0}   # Block 6 master plan, Table 35: estimated cost / area of the land units
LAND_CLASS = {"Resedential": "Residential", "Residential": "Residential", "Residential Commercial": "Residential", "Commercial": "Commercial", "Tourism": "Commercial", "Industrial": "Industrial", "Agricultural": "Agricultural", "Roads": "Roads", "Road": "Roads"}
def land_rate(cls): return LAND_RATE_OMR_HA.get(LAND_CLASS.get(str(cls).strip(), ""), 0.0)
def expropriation(land_take):
    """OMR of the land take dict {class: ha} at the master plan rates; government, planned and unclassified land at no cost."""
    return sum(float(v) * land_rate(k) for k, v in (land_take or {}).items())
def gca():
    """The global catchments of the study area (GCA layer) with the four of Block 04 flagged."""
    g = gpd.read_file(os.path.join(W8, "gis", "GCA_RENN.gpkg"), layer="gca") if os.path.exists(os.path.join(W8, "gis", "GCA_RENN.gpkg")) else None; return g
def dykes(): return only(pd.read_csv(os.path.join(W7, "dykes", "dykes.csv")), "name")
def channel_quantities():
    import json, ast
    q = pd.read_csv(os.path.join(W8, "volumes", "channel_quantities.csv"))   # W9: the terrain run on the 0.5 m ground (W8 here = the W9 folder)
    q["land_take_ha"] = q.land_take_ha.map(lambda s: ast.literal_eval(s) if isinstance(s, str) and s.startswith("{") else {}); return only(q)
def land_take_by_class():
    q = channel_quantities(); acc = {}
    for lt in q.land_take_ha:
        for k, v in lt.items():
            if k in ("", "None", "nan"): continue
            acc[k] = acc.get(k, 0.0) + v
    name = {"Resedential": "Residential"}
    return pd.DataFrame([(name.get(k, k), v) for k, v in sorted(acc.items(), key=lambda kv: -kv[1])], columns=["cls", "ha"])
def cost_totals():
    q = channel_quantities(); d = dykes(); c = culverts(); exp = sum(expropriation(lt) for lt in q.land_take_ha) / 1e6
    t = dict(channels=q.cost_OMR.sum() / 1e6, expropriation=exp, dykes=d.cost_OMR.sum() / 1e6, culverts=c.cost_OMR.sum() / 1e6); t["total"] = t["channels"] + t["expropriation"] + t["dykes"] + t["culverts"]; return t
def cost_by_catchment():
    q = channel_quantities(); d = dykes(); c = culverts(); rows = []
    for g in ("HAW", "SHA", "SAR", "SAK"):
        qg = q[q.channel.str.startswith(g)]
        rows.append(dict(gca=GCA_NAME[g], channels=qg.cost_OMR.sum() / 1e6, expropriation=sum(expropriation(lt) for lt in qg.land_take_ha) / 1e6, dykes=d[d.name.str.startswith(g)].cost_OMR.sum() / 1e6, culverts=c[c.channel.str.startswith(g)].cost_OMR.sum() / 1e6))
    return pd.DataFrame(rows)
def drawings():
    """The plan-profile set by channel: number of sheets, first and last drawing number (W7/report/data/drawings.csv from the set's contents file)."""
    dr = pd.read_csv(os.path.join(DATA_W7, "drawings.csv"))   # columns dwg, cat, ch, drawing, s0, s1, page (the set's contents file)
    g = dr.groupby("ch", sort=False)["dwg"].agg(["size", "first", "last"]).reset_index(); g.columns = ["channel", "sheets", "first", "last"]; return only(g)

def elements(basin="6"):
    """Claude Block 04/results/basin{b}_peak_flow_volume_long.csv -> peak table (element x rp)."""
    df = pd.read_csv(os.path.join(CB04, "results", f"basin{basin}_peak_flow_volume_long.csv"))
    return df.pivot(index="element", columns="rp", values="peak_m3s")[RPS], df.drop_duplicates("element").set_index("element")["type"]

def outfalls():
    """Outfall peaks without the dams (Basin 2) and with the nine dams (Basin 6): Claude Block 04/results/outfalls_B2_vs_B6.csv (W7 step 67)."""
    return pd.read_csv(os.path.join(CB04, "results", "outfalls_B2_vs_B6.csv"), index_col=0)

def outfall_volumes(rp="200yr"):
    """Outfall volumes without (Basin 2) and with the nine dams (Basin 6), Mm3, from the element results."""
    out = {}
    for b in ("2", "6"):
        df = pd.read_csv(os.path.join(CB04, "results", f"basin{b}_peak_flow_volume_long.csv")); df = df[(df.rp == rp) & df.element.str.contains(r"-O\d+$")]
        out[b] = df.set_index("element")["vol_Mm3"]
    o = pd.DataFrame({"B2": out["2"], "B6": out["6"]}).sort_index(key=lambda i: [(x.split("-")[0], int(x.split("-O")[1])) for x in i]); return o

def global_volumes(rp="200yr"):
    """200-year runoff volume of each global catchment without the dams: the sum of its outfall volumes in Basin 2 (Mm3)."""
    o = outfall_volumes(rp); return {g: float(o.loc[[i for i in o.index if i.startswith(g + "-O")], "B2"].sum()) for g in ("HAW", "SHA", "SAR", "SAK")}

def gauges():
    """W3/climate/gauges: MRMWR gauges within 15 km of each dam (2331 project data, read-only) and their annual statistics."""
    near = pd.read_csv(os.path.join(W3, "climate", "gauges", "gauges_near_dams.csv")); st = pd.read_csv(os.path.join(W3, "climate", "gauges", "gauge_annual.csv"), index_col=0); return near, st

def climate9():
    """W3/climate/climate9_summary.json: per-dam climate from the 9 km reanalysis (step 22)."""
    return json.load(open(os.path.join(W3, "climate", "climate9_summary.json"), encoding="utf-8"))

def basin_counts(basin="3"):
    """Element counts of Basin_{b}.basin."""
    txt = open(os.path.join(CB04, "model", f"Basin_{basin}.basin"), encoding="utf-8").read()
    return {k: len(re.findall(rf"^{k}: ", txt, re.M)) for k in ("Subbasin", "Junction", "Reach", "Reservoir")}

def rainfall_design():
    """The nationwide design depths quoted in the Block 6 report (MAFWR regional frequency analysis), mm, 24 h."""
    return [("2", 27.6), ("5", 55.3), ("10", 105.5), ("25", 137.5), ("50", 168.1), ("100", 205.4), ("200", 251.0), ("500", 327.2), ("1000", 399.9), ("2000", 488.7), ("5000", 639.1), ("10000", 685.1), ("PMP", "grid")]

def arf():
    return [(1, 1), (5, 0.994), (10, 0.987), (20, 0.976), (30, 0.965), (40, 0.956), (50, 0.948), (100, 0.913), (200, 0.864), (500, 0.776), (1000, 0.694), (2000, 0.606)]

def fmt(v, dec=0):
    return f"{v:,.{dec}f}" if isinstance(v, (int, float)) and v == v else str(v)

if __name__ == "__main__":
    pd.set_option("display.width", 220)
    print(dams_sheet()[["Crest El", "FSL", "Reservoir", "QPMF", "Spillway L"]]); print(peaks("in").round(0)); print(eav_summary()[["bed", "V_fsl", "capacity_sheet", "lvl_pmp"]]); print(sediment_yield()[["soil_loss_t_ha_yr", "sdr_williams", "yield_m3_km2_yr"]]); print(sedimentation(50)[["deposited_Mm3", "loss_pct", "new_zero_m"]])
    print(basin_counts("3"), basin_counts("2"), outfall_volumes().round(1).T.to_string()); print(global_volumes())
