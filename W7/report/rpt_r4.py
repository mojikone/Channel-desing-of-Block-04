"""Revision R4 additions (W7, 2026-10-12): the figures and tables that bring the report to the layout of the Block 6 channel design
report, and the three new sections (culverts, dykes, quantities and cost). Every number comes from W7 data through data_facts."""
import os, json
from common import T, F, tcap, D, N, A, n0, n1, n2, chart, map_fig, IMG, fig
import omml as M
import pandas as pd

def wfmt(x): return f"{x:,.1f}".replace(".0", "")

# ---------------------------------------------------------------- 1 introduction: the process as a figure
def process_figure(d):
    fig(d, os.path.join(IMG, "F10_process.png"), "Channel design process", 16, key="process_fig")

# ---------------------------------------------------------------- 2 hydrology: the ARF curve and the curve-number grid
def hydrology_extra(d):
    chart(d, "C14_arf_curve", "Area reduction factor against catchment area", 12, key="arf_curve")
    map_fig(d, "M17_cn", "SCS curve number grid of Block 04", key="cn_map")

# ---------------------------------------------------------------- 5 rainfall-runoff: the intermediate catchments of the plain
def plain_catchments(d):
    sub = A.subbasins_dam()
    inter = sub[sub.inter == 1]; rest = sub[sub.inter == 0]
    D.p(d, f"{len(inter)} intermediate catchments, {n0(inter.area_km2.sum())} km² in all, have no dam anywhere in their upstream network: their runoff reaches the channels "
           f"unregulated ({F('plain_map')}). The other {len(rest)} catchments, {n0(rest.area_km2.sum())} km², either drain to a dam or receive its routed outflow; their "
           "channels are sized on the runoff of the plain added to that outflow.")
    map_fig(d, "M16_plain_catchments", "Intermediate catchments with no dam in their upstream network", key="plain_map")

# ---------------------------------------------------------------- 8 hydraulic: typical sections, the equations of the sizing, the depth
def criteria_extra(d):
    D.p(d, f"The typical sections of the project are shown in {F('sec_fill')} for a channel in fill, between two embankments with a 4 m crest, and in {F('sec_cut')} for a "
           "channel in cut: side slopes of 1:1.5, riprap over geotextile on the inner faces, a toe trench at each bed edge and gravel protection on the outer face of the embankment.")
    fig(d, os.path.join(IMG, "F11_section_fill.png"), "Typical channel section in fill", 16, key="sec_fill")
    fig(d, os.path.join(IMG, "F12_section_cut.png"), "Typical channel section in cut", 16, key="sec_cut")
    D.p(d, "Each reach is sized with Manning's equation for uniform flow on the designed bed slope, with the water surface at three quarters of the channel depth:")
    M.display(d, M.seq(M.r("Q"), M.EQ, M.frac(M.r("1"), M.r("n")), M.r(" A "), M.sup(M.r("R"), M.r("2/3")), M.r(" "), M.sup(M.r("S"), M.r("1/2"))), number=D.next_eq())
    M.display(d, M.seq(M.r("A"), M.EQ, M.r("0.75 b D"), M.r(",      "), M.r("R"), M.EQ, M.frac(M.r("0.75 b D"), M.seq(M.r("b"), M.PLUS, M.r("1.5 D")))), number=D.next_eq())
    D.symbols(d, [("Q", "200-year design flow of the reach", "m³/s"), ("n", "Manning's roughness, 0.030", "s/m^(1/3)"), ("A", "flow area at three quarters of the depth", "m²"), ("R", "hydraulic radius", "m"),
                  ("S", "bed slope of the reach", "m/m"), ("b", "bed width, the smallest value in steps of 0.5 m that carries Q", "m"), ("D", "channel depth, 2.5 m or 3 m", "m")])
    D.p(d, "At the sea outfalls the bank height follows the tidal level or the flow depth, whichever is higher, plus the freeboard:")
    M.display(d, M.seq(M.sub(M.r("H"), M.r("bank")), M.EQ, M.r("max"), M.delim(M.seq(M.r("MHHW"), M.r(", "), M.r("y"))), M.PLUS, M.r("0.6")), number=D.next_eq())
    D.symbols(d, [("H_bank", "bank height above the channel bed", "m"), ("MHHW", "mean higher high water of the nearest reference port", "m"), ("y", "flow depth at the outfall", "m")])

def depth(d):
    cs = A.channel_sections("200yr"); deep = [r.channel for r in cs.itertuples() if 3.0 in r.depths]
    D.h(d, 2, "Channel depth")
    D.p(d, f"The design depth is 2.5 m. Where the existing wadi is deeper than that at the design points, the channel keeps the depth of the wadi, 3 m: {', '.join(deep)} "
           f"over the reaches concerned ({F('depth_map')}). The depth of every reach is in the appendix table.")
    map_fig(d, "M13_depth", "Channel depth: 2.5 m, or 3 m where the wadi is deeper", key="depth_map")

def sections_extra(d):
    cs = A.channel_sections("200yr"); inv = A.size_inventory(); rt = A.reach_table(); fast = rt[(rt.velocity > 3.0) & (rt.flow > 0)]
    D.p(d, f"{F('width_map')} draws the bed of every reach to scale with its width; {F('flow_map')} gives the 200-year design flow along the channels, rising from reach to "
           f"reach as the tributaries join. The lengths by class are in {F('len_chart')}, the distribution of the designed widths, weighted by length, in {F('width_hist')}, "
           f"and the full inventory of sizes in {T('inventory')}. {F('fw_chart')} relates the width of each reach to its design flow: at a given flow the width varies with the "
           "bed slope, the flatter reaches near the coast being the wider.")
    map_fig(d, "M12_width", "Designed bed width of the channels for the 200-year flow (m)", size="A3", key="width_map")
    map_fig(d, "M18_q200_channels", "200-year design flow along the channels (m³/s)", size="A3", key="flow_map")
    chart(d, "C12_lengths_by_class", "Channels and dykes of Block 04 by class", 15, key="len_chart")
    chart(d, "C11_width_hist", "Distribution of the designed bed widths, by length of reach, in 50 m bins", 15, key="width_hist")
    chart(d, "C13_flow_vs_width", "Designed bed width against the 200-year design flow of the reach", 15, key="fw_chart")
    tcap(d, "Channel sizes inventory: depth x bed width (m) and the length of reaches of that size (m)", "inventory")
    rows = [[r.size, n0(r.Length)] for r in inv.itertuples()]
    ncol = 3; per = (len(rows) + ncol - 1) // ncol; cols = [rows[i * per:(i + 1) * per] for i in range(ncol)]
    trows = [sum(((c[i] if i < len(c) else ["", ""]) for c in cols), []) for i in range(per)]
    trows.append(["**Total**", f"**{n0(inv.Length.sum())}**", "", "", "", ""])
    D.table(d, ["Size (m)", "Length (m)"] * ncol, trows, widths=[2.6, 2.6] * ncol, font=7.5)
    D.p(d, f"The reaches are labelled channel by channel in {F('labels_map')}; their length, slope, velocity, depth ratio, size and flow are listed in Appendix C, and the plan and profile drawings in Appendix D. "
           f"{len(fast)} of the {len(rt)} reaches run above 3 m/s at the 200-year flow on the steeper ground of the foothills; energy dissipation, bed protection or a flatter "
           "profile in steps will be set for them in the detailed design.")
    map_fig(d, "M14_reach_labels", "Reach labels of the hydraulic model", size="A3", key="labels_map")

# ---------------------------------------------------------------- 9 outfalls: the map and the table
def outfalls_extra(d):
    o = A.outfalls_table()
    D.p(d, f"{F('outfalls_map')} locates the outfalls with, at each, the designed invert level I, the existing terrain level Fix and their difference; the invert is "
           f"printed in red where it lies below the existing terrain. {T('outfalls_tab')} gives, for each outfall, the 200-year flow and bed width of its last reach, its invert and "
           "ground level, the flow depth and the invert against the mean higher high water of 0.70 m at Al Khaburah.")
    map_fig(d, "M15_outfalls", "Outfalls of the channel system: designed invert, existing terrain level and their difference (m)", key="outfalls_map")
    tcap(d, "Outfalls: 200-year flow, bed width, levels and tidal margin", "outfalls_tab")
    rows = [[r.outfall, r.channel, n0(r.Q200), wfmt(r.width_m), n2(r.invert_m), n2(r.ground_m), n2(r.depth_m), n2(r.invert_minus_MHHW)] for r in o.itertuples()]
    D.table(d, ["Outfall", "Channel", "Q200 (m³/s)", "Bed width (m)", "Invert (m)", "Ground (m)", "Flow depth (m)", "Invert − MHHW (m)"], rows, widths=[2.2, 2.6, 1.8, 1.8, 1.7, 1.7, 1.9, 2.1], font=8)

# ---------------------------------------------------------------- 10 culverts and bridges
def culverts(d):
    pr = A.culverts(); ex = pr[pr.existing_type != "None on file"]
    D.h(d, 1, "Culverts and bridges")
    D.p(d, f"The channels cross the Batinah Highway at {int((pr.road == 'Batinah Highway').sum())} points and the Batinah Coastal Road at {int((pr.road == 'Batinah Coastal Road').sum())}; "
           f"the Batinah Expressway does not cross a Block 04 channel ({F('culvert_map')}). Every crossing needs a structure that passes the designed section: a box culvert of the "
           "full bed width of the channel, with the clear height of the channel depth less a 0.5 m embankment, 2.0 m under the 2.5 m channels and 2.5 m under the 3 m ones.")
    D.p(d, f"The inventory of the existing structures along the Batinah roads lists {len(ex)} structures within 150 m of a crossing ({T('culv_existing')}); none has the width of the "
           "channel it would serve, and at the other crossings no structure is on file. All are to be replaced or added. Photographs and the survey of each structure are collected "
           "in the detailed design.")
    tcap(d, "Existing structures on file at the crossings", "culv_existing")
    rows = [[str(r.id), r.road, r.channel, f"{n0(r.station_m)}", "–" if r.existing_type == "None on file" else "Culvert", r.existing_size or "–", (n0(r.existing_barrels) if r.existing_type != "None on file" else "–"), ""] for r in pr.itertuples()]
    D.table(d, ["ID", "Road", "Channel", "Station (m)", "Existing type", "Cells x width x height (m)", "Barrels", "Photograph"], rows, widths=[0.9, 3.0, 2.4, 1.6, 2.2, 2.8, 1.3, 2.1], font=7.5)
    D.p(d, f"The proposed culverts are in {T('culv_proposed')}: box cells of 4.0 m clear width from the standard combinations of the Oman Highway Design Standard, the number of "
           "cells from the bed width, and the headwater checked with the inlet- and outlet-control equations of the FHWA culvert design method (square-edged inlet with wingwalls, "
           "entrance loss 0.4, barrel roughness 0.015, the tailwater at the normal depth of the channel downstream): every structure keeps its headwater below 1.2 times the "
           "clear height. The length across the road is taken as the road corridor, 45 m on the Batinah Highway and 32 m on the Coastal Road, to be measured in the detailed design. "
           "A channel without a modelled inflow keeps the minimum section of 10 m and its culvert is fitted to that section.")
    tcap(d, "Proposed box culverts at the road crossings (200-year flow)", "culv_proposed")
    rows = [[str(r.id), r.road.replace("Batinah ", ""), r.channel, (n0(r.Q200) if r.Q200 > 0 else "–"), f"{wfmt(r.channel_width_m)} x {wfmt(r.channel_depth_m)}", r.size, wfmt(r.overall_width_m), n0(r.length_m), (n2(r.HW_over_D) if r.Q200 > 0 else "–"), n2(r.cost_mOMR)] for r in pr.itertuples()]
    rows.append(["", "**Total**", "", "", "", f"**{n0(pr.cells.sum())} cells**", "", "", "", f"**{n2(pr.cost_OMR.sum() / 1e6)}**"])
    D.table(d, ["ID", "Road", "Channel", "Q200 (m³/s)", "Channel W x D (m)", "Cells x W x H (m)", "Overall width (m)", "Length (m)", "HW / H", "Cost (million OMR)"], rows, widths=[0.9, 2.2, 2.4, 1.6, 2.2, 2.4, 1.8, 1.5, 1.3, 1.8], font=7.5)
    map_fig(d, "M19_culverts", "Road crossings and the proposed box culverts", key="culvert_map")

# ---------------------------------------------------------------- 11 dykes
def dykes(d):
    dk = A.dykes(); CL = {"FP D": "Flood protection", "Sw M D": "Stormwater main", "Sw S D": "Stormwater secondary"}
    D.h(d, 1, "Dykes")
    D.p(d, f"The dykes keep the flood from spreading before it reaches the channels and lead it to their entrances. The {len(dk)} dykes, {n1(dk.L_m.sum() / 1000)} km in all, "
           f"stand {n1(dk.H_m.min())} to {n1(dk.H_m.max())} m high ({T('dykes_tab')}, {F('dykes_map')}); the highest, {dk.loc[dk.H_m.idxmax(), 'name']}, closes a ponding area "
           f"where the 200-year depth reaches {n1(dk.depth_max.max())} m.")
    tcap(d, "Dykes: 200-year depth along the line, adopted height and cost", "dykes_tab")
    rows = [[str(r.id), r.name, CL.get(r.cls, r.cls), n0(r.L_m), n2(r.depth_mean), n2(r.depth_p90), n2(r.depth_max), n1(r.H_m), n2(r.cost_mOMR)] for r in dk.itertuples()]
    rows.append(["", "**Total**", "", f"**{n0(dk.L_m.sum())}**", "", "", "", "", f"**{n2(dk.cost_OMR.sum() / 1e6)}**"])
    D.table(d, ["ID", "Dyke", "Class", "Length (m)", "Depth, mean (m)", "Depth, 90 % (m)", "Depth, max (m)", "Height (m)", "Cost (million OMR)"], rows, widths=[0.9, 2.4, 2.8, 1.6, 1.7, 1.7, 1.7, 1.5, 2.0], font=7.5)
    map_fig(d, "M20_dykes", "Dyke heights (m)", key="dykes_map")

# ---------------------------------------------------------------- 12 quantities and cost
def costs(d):
    q = A.channel_quantities(); dk = A.dykes(); cv = A.culverts(); tot = A.cost_totals()
    D.h(d, 1, "Quantities and cost estimate")
    D.p(d, "The quantities of the channels are measured on the designed sections against the 5 m terrain model, reach by reach: the channel surface of the typical sections is "
           "built along each reach at its bed width, depth and invert, and the excavation and the fill are the volumes between that surface and the ground. The riprap is the two "
           "side slopes of every reach, 0.3 m thick as priced; the clearing is the footprint of the works. The dykes follow the typical fill section at their height, with a 0.4 m "
           "strip under the footprint. The culverts are priced by their concrete and reinforcement, blinding, waterproofing, the road works over them and the removal of the "
           f"existing structure. The unit rates are those of the master plan estimate ({T('rates')}).")
    tcap(d, "Unit rates of the estimate", "rates")
    D.table(d, ["Item", "Unit", "Rate (OMR)"], [["Clearing and grubbing", "m²", "0.30"], ["Excavation", "m³", "2.10"], ["Embankment and dyke fill", "m³", "4.00"], ["Riprap, 0.3 m, over geotextile", "m³", "13.20"],
                                                 ["Reinforced concrete of the culverts", "m³", "106.90"], ["Reinforcement, 120 kg/m³", "t", "417.10"], ["Blinding concrete", "m³", "45.00"], ["Pavement and road works over the culverts", "m²", "per the master plan build-up"]], widths=[8, 2, 5], font=8.5)
    tcap(d, "Channels: earthworks, protection, land take and cost", "chan_cost")
    rows = []
    for r in q.itertuples():
        lt = r.land_take_ha if isinstance(r.land_take_ha, dict) else {}
        priv = sum(v for k, v in lt.items() if k not in ("", "None", "nan"))
        rows.append([r.channel, n1(r.length_m / 1000), n0(r.cut_m3), n0(r.fill_m3), n0(r.footprint_m2), n0(r.protection_m2), n1(r.corridor_ha), n1(priv), n2(r.cost_mOMR)])
    rows.append(["**Total**", f"**{n1(q.length_m.sum() / 1000)}**", f"**{n0(q.cut_m3.sum())}**", f"**{n0(q.fill_m3.sum())}**", f"**{n0(q.footprint_m2.sum())}**", f"**{n0(q.protection_m2.sum())}**", f"**{n1(q.corridor_ha.sum())}**", "", f"**{n2(q.cost_OMR.sum() / 1e6)}**"])
    D.table(d, ["Channel", "Length (km)", "Cut (m³)", "Fill (m³)", "Clearing (m²)", "Riprap (m²)", "Corridor (ha)", "Of which in cadastral parcels (ha)", "Cost (million OMR)"], rows, widths=[2.4, 1.5, 2.0, 1.8, 2.0, 1.8, 1.6, 2.2, 1.8], font=7.5)
    lu = A.land_take_by_class()
    if len(lu):
        D.p(d, f"The corridors of the channels, the bed with the embankments and an access road on each side, take {n0(q.corridor_ha.sum())} ha, of which {n0(lu.ha.sum())} ha lie in the "
               f"parcels of the cadastre ({T('landtake')}); the land cost is not priced here and follows the valuation of the Ministry.")
        tcap(d, "Land take of the channel corridors by land use of the cadastre", "landtake")
        D.table(d, ["Land use", "Area (ha)"], [[r.cls, n1(r.ha)] for r in lu.itertuples()] + [["**Total**", f"**{n1(lu.ha.sum())}**"]], widths=[6, 3], font=8.5)
    tcap(d, "Cost estimate of the channel scheme of Block 04 (million OMR)", "cost_tot")
    D.table(d, ["Item", "Quantity", "Cost (million OMR)"], [["Channels", f"{n1(q.length_m.sum() / 1000)} km, 37 channels", n2(tot['channels'])], ["Dykes", f"{n1(dk.L_m.sum() / 1000)} km, {len(dk)} dykes", n2(tot['dykes'])],
                                                            ["Culverts", f"{len(cv)} structures, {n0(cv.cells.sum())} cells", n2(tot['culverts'])], ["**Total**", "", f"**{n2(tot['total'])}**"]], widths=[4, 6, 4], font=8.5)
    chart(d, "C15_cost", "Cost of the channels, dykes and culverts by catchment", 15, key="cost_chart")

# ---------------------------------------------------------------- appendices
def appendix_reaches(d):
    from common import h_app
    rt = A.reach_table(); h_app(d, "Appendix C – Reach characteristics at the 200-year flow")
    D.p(d, "Every reach of the hydraulic model with its length, bed slope, roughness, velocity, depth ratio, size (depth x bed width) and 200-year design flow. Reaches without a "
           "modelled inflow carry no flow and take the minimum section.")
    rows = [[r.label, n0(r.length_m), f"{r.slope:.4f}", "0.030", n2(r.velocity) if r.flow > 0 else "–", (n0(100 * r.depthtorise) if r.flow > 0 else "–"), r.size, n0(r.flow) if r.flow > 0 else "–"] for r in rt.itertuples()]
    D.table(d, ["Label", "Length (m)", "Slope (m/m)", "Manning's n", "Velocity (m/s)", "Depth / rise (%)", "Size (m)", "Flow (m³/s)"], rows, widths=[2.4, 1.7, 1.7, 1.6, 1.8, 1.8, 2.2, 1.8], font=7)

def dashboard(d):
    """Appendix E - the costs dashboard, two landscape pages, the layout of the master plan's channel design reports."""
    from common import h_app, _reg
    tot = A.cost_totals(); h_app(d, "Appendix E – Costs dashboard")
    D.p(d, f"The estimate of {n1(tot['total'])} million OMR at a glance: the channel, dyke and culvert costs by catchment and by type, then the cost of every channel, "
           "dyke and culvert of the scheme. Land is not priced.")
    _reg("fig", "dash1", D.wide_figure(d, os.path.join(IMG, "D1_dashboard.png"), "Costs dashboard: channels, dykes and culverts by catchment, and the total by infrastructure type", size="A4"))
    _reg("fig", "dash2", D.wide_figure(d, os.path.join(IMG, "D2_dashboard_items.png"), "Costs dashboard: every channel, dyke and culvert", size="A4"))

def appendix_drawings(d):
    from common import h_app
    dr = A.drawings(); h_app(d, "Appendix D – Plan and profile drawings")
    D.p(d, "The plan and profile drawings of the 37 channels for the 200-year design are issued as a separate set; the sheets are listed by channel.")
    rows = [[r.channel, r.sheets, r.first, r.last] for r in dr.itertuples()]
    D.table(d, ["Channel", "Sheets", "First drawing", "Last drawing"], rows, widths=[3, 1.5, 4, 4], font=8)
