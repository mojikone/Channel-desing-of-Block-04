"""Section 5 - rainfall-runoff simulation and the dams, in the Block 6 order: model, dams' information, catchments, EAV curves,
peak flows, volumes, levels, hydrographs, performance. Section 8 - outfalls."""
from common import T, F, tcap, D, N, A, n0, n1, n2, chart, map_fig, fig, image_grid, merge_first_column_pairs, lab, IMG, HMS_SHOT
import omml as M, os

def section(d):
    ds = A.dams_sheet(); cat = A.catchments(); eav = A.eav_summary(); pin, pout = A.peaks("in"), A.peaks("out"); vin, vout = A.volumes("in"), A.volumes("out"); lv = A.levels(); y = A.sediment_yield(); s50 = A.sedimentation(50)
    D.h(d, 1, "Rainfall-runoff simulation")
    D.p(d, "The HEC-HMS model of Block 04 is comprehensive: it includes the subbasins of the nine dams and those of the channel network, delineated on the 10 m terrain model with the "
           "channel alignments and the dykes as breaklines, so that even the smallest channel of the design has its own catchment. Depth-area analyses are run for every return "
           "period, so that the areal reduction of the storm is applied to each element for its own catchment area. The dams are represented by reservoir elements with their "
           f"elevation-area curves and spillway ratings, all nine routed in the model so that the flows on the plain carry their attenuation; the reaches are routed by Muskingum-Cunge. {F('hms')} shows the model.")
    map_fig(d, "M08_hms", "HEC-HMS model for Block 04", key="hms")
    D.p(d, f"The 200-year peak flow at every junction of the model, with the dams in place, is mapped in {F('q200a')} for the whole block and in {F('q200b')} for the dams and the plain "
           "downstream of them, where the channels are designed. The peaks at the junctions of the plain are the design flows of the channel reaches that leave them.")
    map_fig(d, "M10_q200", "(a) Q200 (m³/s) at the junctions of the HEC-HMS model, dams in place", key="q200a")
    map_fig(d, "M11_q200_plain", "(b) Q200 (m³/s) at the dams and the junctions downstream of them, dams in place", size="A3", key="q200b")
    import rpt_r4; rpt_r4.plain_catchments(d)
    D.p(d, "Some important points about the catchments of the study area are the following.")
    D.bullet(d, "Hawasinah UP, the existing dam on Wadi Al Hawasinah, receives the routed outflows of Hawasinah 02 and Hawasinah 11 upstream of it, and Shafan 08 receives the routed outflow of Shafan 02.")
    D.bullet(d, "Wadi Sarami and Wadi Sakhin each carry two dams on separate tributaries; their channels join on the plain before the sea.")
    D.bullet(d, "The intermediate catchments of the plain, below the dams, have no upstream storage; their flood-protection and stormwater channels are sized on their own runoff added to the routed dam outflows.")
    D.h(d, 2, "Dams' information")
    D.p(d, f"The nine dams sit at the foot of the hills where the wadis leave their gorges. Their characteristics are listed in {T('dams_info')}: crest level, full supply level, height above "
           "the wadi bed, reservoir capacity at full supply level, spillway length, probable maximum flood and dam length.")
    tcap(d, "Dams' information", "dams_info")
    rows = [[lab(dam), n0(ds.loc[dam, "Crest El"]), n0(ds.loc[dam, "FSL"]), n1(eav.loc[dam, "height"]), n0(ds.loc[dam, "Reservoir"]), n0(ds.loc[dam, "Spillway L"]), n0(ds.loc[dam, "QPMF"]), n0(ds.loc[dam, "axis_len_m"])] for dam in A.DAMS]
    D.table(d, ["Dam", "Crest level (m)", "FSL (m)", "Height crest–bed (m)", "Capacity at FSL (Mm³)", "Spillway length (m)", "QPMF (m³/s)", "Dam length (m)"], rows, widths=[3.4, 2, 1.8, 2.2, 2.4, 2.2, 2.2, 2.2], font=8.5)
    D.p(d, f"The dam catchments are listed in {T('catchments')} with their physiographic characteristics. Together the dams control {n0(A.controlled_area())} km², the nested catchments counted once. Hawasinah UP drains the largest "
           f"area, {n0(cat.loc['Hawasinah EX', 'area_km2'])} km², which includes the catchments of Hawasinah 02 and 11 upstream of it, and Shafan 08 includes that of Shafan 02. "
           "The longest flow paths run 15 to 80 km from the mountain divides to the dams, with 10–85 slopes of 0.8 to 2.8 %, and the times of concentration by Kirpich range from "
           "two to eleven hours.")
    tcap(d, "Dam catchments", "catchments")
    rows = [[lab(dam), n0(cat.loc[dam, "area_km2"]), n1(cat.loc[dam, "lfp_km"]), f"{cat.loc[dam, 's1085']:.4f}", f"{cat.loc[dam, 'basin_slope']:.3f}", n0(cat.loc[dam, "tc_min"]), n0(cat.loc[dam, "lag_min"]), n1(cat.loc[dam, "cn_w"]), n0(cat.loc[dam, "relief_m"])] for dam in A.DAMS]
    D.table(d, ["Dam", "Area (km²)", "Longest flow path length (km)", "Longest flow path slope (10–85)", "Basin slope", "Tc (min)", "Lag (min)", "Curve number", "Relief (m)"], rows, widths=[3.2, 1.6, 1.8, 2, 1.7, 2.1, 1.6, 1.6, 1.5], font=8)
    map_fig(d, "M01_dams", "The nine dams of Block 04, their catchments and reservoirs, and the channel and dyke alignments of the plain", key="dams_map")
    D.h(d, 2, "Dams' elevation-volume-area curves")
    D.p(d, "The reservoir elevation-area-volume curves are derived from the 10 m terrain model inside the crest-level contour of each dam, at 0.5 m steps from the wadi bed to the crest; "
           f"the volume between steps follows the conic formula. {T('eav_grid')} gives the curves of the nine reservoirs with the full supply level and the capacity and area at it, and "
           f"{T('eav_summary')} summarises the values at full supply level and at crest.")
    image_grid(d, [(os.path.join(IMG, f"C05_eav_{dam.replace(' ', '_')}.png"), lab(dam)) for dam in A.DAMS], "Dams' elevation-volume-area curves", cols=2, width_cm=7.6, key="eav_grid")
    tcap(d, "Reservoir curves at full supply level and at crest", "eav_summary")
    rows = [[lab(dam), n1(eav.loc[dam, "bed"]), n2(eav.loc[dam, "A_fsl"]), n1(eav.loc[dam, "V_fsl"]), n2(eav.loc[dam, "A_crest"]), n1(eav.loc[dam, "V_crest"])] for dam in A.DAMS]
    D.table(d, ["Dam", "Bed (m)", "Area at FSL (km²)", "Volume at FSL (Mm³)", "Area at crest (km²)", "Volume at crest (Mm³)"], rows, widths=[3.4, 1.8, 2.4, 2.4, 2.4, 2.4], font=8.5)
    D.h(d, 2, "Reservoir routing")
    D.p(d, "Each reservoir is routed by the Modified Puls method on its elevation-area curve. The outflow is the spillway discharge above full supply level, a broad-crested weir with "
           f"the spillway length of {T('dams_info')} and a coefficient of 2.1, plus the flow over the dam crest once the level exceeds it:")
    M.display(d, M.seq(M.r("Q"), M.EQ, M.r("C L "), M.sup(M.r("H"), M.r("1.5")), M.PLUS, M.r("1.7 "), M.sub(M.r("L"), M.r("crest")), M.r(" "), M.sup(M.delim(M.seq(M.r("z"), M.MINUS, M.sub(M.r("z"), M.r("crest")))), M.r("1.5"))), number=D.next_eq())
    D.symbols(d, [("Q", "outflow", "m³/s"), ("C", "spillway discharge coefficient, 2.1", "m^0.5/s"), ("L", "spillway length", "m"), ("H", "head over the full supply level", "m"), ("L_crest", "length of the dam crest", "m"), ("z", "reservoir level", "m")])
    D.p(d, "The reservoirs are empty at the start of every event; a low-level outlet empties them between events and does not change the flood peak.")
    D.h(d, 2, "Dams' peak flows")
    D.p(d, f"Peak inflows and outflows at the dam sites are presented in {T('peaks')} for all the return periods; the dams are designed to hold the 200-year flood. The inflow of "
           "Hawasinah UP and of Shafan 08 includes the routed outflow of the dams upstream of them.")
    tcap(d, "Dams' peak flow (m³/s) for the return periods", "peaks")
    rows = []
    for dam in A.DAMS: rows.append([lab(dam, True), "In"] + [n0(pin.loc[dam, rp]) for rp in A.RPS]); rows.append([lab(dam, True), "Out"] + [n0(pout.loc[dam, rp]) for rp in A.RPS])
    t = D.table(d, ["Dam", ""] + [A.RP_LABEL[rp] for rp in A.RPS], rows, widths=[2.6, 0.9] + [1.0] * 13, font=6.5, keep_together=True); merge_first_column_pairs(t)
    full = [lab(dam) for dam in A.DAMS if pout.loc[dam, "200yr"] < 1]
    D.p(d, f"{['No', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'][len(full)]} reservoirs store the whole 200-year flood: {', '.join(full)} release nothing up to 200 years. Hawasinah UP and Hawasinah 11 release "
           f"{n0(pout.loc['Hawasinah EX', '200yr'])} and {n0(pout.loc['Hawasinah 11', '200yr'])} m³/s against inflows of {n0(pin.loc['Hawasinah EX', '200yr'])} and {n0(pin.loc['Hawasinah 11', '200yr'])} m³/s, "
           f"Shafan 08 releases {n0(pout.loc['Shafan 08', '200yr'])} m³/s, and Sakhin 08 (Mehmum) halves its 200-year peak. Hawasinah 02 is different: its reservoir holds "
           f"{n0(ds.loc['Hawasinah 02', 'Reservoir'])} Mm³ against a 200-year inflow volume of {n0(vin.loc['Hawasinah 02', '200yr'])} Mm³, so the spillway runs from the 10-year event and the "
           f"200-year peak passes almost unattenuated, at {n0(pout.loc['Hawasinah 02', '200yr'])} m³/s; Hawasinah UP downstream of it holds that flood up to the 200-year event.")
    chart(d, "C03_attenuation", "Dams' peak inflow and outflow for the 100-, 200- and 500-year events", 16, key="attenuation")
    tcap(d, "Dams' inflow and outflow volume (Mm³) for the return periods", "volumes")
    rows = []
    for dam in A.DAMS: rows.append([lab(dam, True), "In"] + [n1(vin.loc[dam, rp]) for rp in A.RPS]); rows.append([lab(dam, True), "Out"] + [n1(vout.loc[dam, rp]) for rp in A.RPS])
    t = D.table(d, ["Dam", ""] + [A.RP_LABEL[rp] for rp in A.RPS], rows, widths=[2.6, 0.9] + [1.0] * 13, font=6.5, keep_together=True); merge_first_column_pairs(t)
    D.h(d, 2, "Reservoir levels")
    D.p(d, f"The peak reservoir level of every event is listed in {T('levels')}. At the probable maximum flood the reservoirs reach "
           f"{n1(min(lv.loc[dam, 'PMP'] - ds.loc[dam, 'FSL'] for dam in A.DAMS))} to {n1(max(lv.loc[dam, 'PMP'] - ds.loc[dam, 'FSL'] for dam in A.DAMS))} m above full supply level.")
    tcap(d, "Peak reservoir level (m) for the return periods", "levels")
    rows = [[lab(dam, True), n0(ds.loc[dam, "FSL"])] + [n1(lv.loc[dam, rp]) for rp in A.RPS] for dam in A.DAMS]
    D.table(d, ["Dam", "FSL"] + [A.RP_LABEL[rp] for rp in A.RPS], rows, widths=[2.6, 0.9] + [1.0] * 13, font=6.5)
    D.h(d, 2, "Hydrographs")
    D.p(d, f"The inflow and outflow hydrographs of all the dam sites are presented in {F('q200grid')} for the 200-year event, with the peak and the volume of each. The area between the two "
           "curves is the volume the reservoir stores; the delay of the outflow peak and its reduction measure the dam's performance. The inflow hydrographs of all the return periods "
           "are given for every dam in Appendix A.")
    chart(d, "C01_q200_grid", "Inflow and outflow hydrographs of the nine dams for the 200-year event", 15.5, key="q200grid")
    D.h(d, 2, "Flood protection performance")
    gv = A.global_volumes("200yr")
    D.p(d, f"{T('performance')} measures the flood protection each dam offers to its global catchment: the potential net capacity is the capacity at full supply level less the sediment "
           "deposited in 50 years; the site runoff volume is the 200-year inflow volume at the dam; the global catchment volume is the 200-year runoff volume of the whole wadi "
           "catchment reaching the sea without the dams; and the performance is the ratio of the net capacity to that volume.")
    tcap(d, "Flood protection performance of the dams", "performance")
    rows = []
    for dam in A.DAMS:
        net = float(eav.loc[dam, "V_fsl"]) - float(s50.loc[dam, "deposited_Mm3"]); g = A.GCA[dam]; gvol = gv[g]
        rows.append([lab(dam), A.GCA_NAME[g], n1(net), n1(vin.loc[dam, "200yr"]), n1(gvol), n0(100 * net / gvol)])
    D.table(d, ["Dam site", "Global catchment", "Potential net capacity (MCM)", "Site 200-yr runoff volume (MCM)", "Global catchment 200-yr runoff volume (MCM)", "Global flood protection performance (%)"], rows, widths=[3.2, 2.4, 2.4, 2.6, 2.8, 2.6], font=8)

def outfalls(d):
    o = A.outfalls(); ov = A.outfall_volumes()
    D.h(d, 1, "Outfalls")
    D.p(d, f"The thirteen outfalls of the channel network to the sea receive, in the 200-year event, between {n0(o['B6 200yr'].min())} and {n0(o['B6 200yr'].max())} m³/s with the "
           f"dams in operation. Without the dams the three largest outfalls would carry {n0(o.loc['HAW-O1', 'B2 200yr'])}, {n0(o.loc['SAR-O2', 'B2 200yr'])} and {n0(o.loc['SHA-O5', 'B2 200yr'])} m³/s; "
           f"the reservoirs cut them to {n0(o.loc['HAW-O1', 'B6 200yr'])}, {n0(o.loc['SAR-O2', 'B6 200yr'])} and {n0(o.loc['SHA-O5', 'B6 200yr'])} m³/s. The outfalls fed by the plain alone are unchanged. "
           f"The 200-year volumes fall likewise, from {n1(ov['B2'].sum())} to {n1(ov['B6'].sum())} Mm³ over the thirteen outfalls.")
    chart(d, "C06_outfalls_peak", "200-year peak flow at the thirteen outfalls without and with the dams", 16, key="outfalls_peak")
    chart(d, "C06_outfalls_volume", "200-year runoff volume at the thirteen outfalls without and with the dams", 16, key="outfalls_volume")
    import rpt_r4; rpt_r4.outfalls_extra(d)
