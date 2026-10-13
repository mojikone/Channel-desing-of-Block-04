"""Contents, executive summary, introduction and conclusions (R1: no internal matter, nine dams, Hawasinah UP)."""
from common import T, F, tcap, D, N, A, n0, n1, lab

def contents(d):
    D.title(d, "Table of Contents"); D.toc(d, "1-3")
    D.title(d, "List of Tables", space_before=14); D.list_of(d, "Table")
    D.title(d, "List of Figures", space_before=14); D.list_of(d, "Figure")
    D.pagebreak(d)

def _totals():
    ds = A.dams_sheet(); cat = A.catchments(); pin, pout = A.peaks("in"), A.peaks("out"); s50 = A.sedimentation(50); s100 = A.sedimentation(100); y = A.sediment_yield(); lv = A.levels()
    full = [lab(dam) for dam in A.DAMS if pout.loc[dam, "200yr"] < 1]
    head = lv["PMP"] - ds["FSL"].reindex(A.DAMS)
    return dict(area=A.controlled_area(), cap=float(ds["Reservoir"].reindex(A.DAMS).sum()), qin200=(float(pin["200yr"].min()), float(pin["200yr"].max())), full200=full,
                att02=float(1 - pout.loc["Hawasinah 02", "200yr"] / pin.loc["Hawasinah 02", "200yr"]) * 100, head=(float(head.min()), float(head.max())),
                yld=(float(y.yield_m3_km2_yr.min()), float(y.yield_m3_km2_yr.max())), loss50=s50.loss_pct, loss100=s100.loss_pct, cl=A.climate9())

def executive_summary(d):
    t = _totals(); c = t["cl"]; rains = [c[dam]["rain_mean_annual"] for dam in A.DAMS]
    D.title(d, "Executive Summary")
    D.sub(d, "Project context")
    D.p(d, "The Ministry of Agriculture, Fisheries Wealth and Water Resources commissioned Renardet S.A. & Partners Consulting Engineers, in joint venture with "
           "Artelia Muscat, to prepare the comprehensive master plan for flood protection dams, river training schemes and stormwater drainage in North and South Al Batinah. "
           "Block 04 covers the wadis of Al Hawasinah, Shafan, Sarami and Sakhin between the Hajar foothills and the coast, from Al Khaburah to Saham. The scheme consists of "
           "nine flood-protection dams and a network of flood-protection and stormwater channels and dykes that carry the routed dam outflows and the runoff of the plain to the sea.")
    D.sub(d, "Scope of this report")
    D.p(d, "This report presents the hydrology of Block 04 and the design information of the nine dams: catchments, inflow hydrographs for thirteen return periods up to the "
           "probable maximum precipitation, reservoir elevation-area-volume curves, reservoir routing, the sediment yield of the catchments and the storage lost to sedimentation, "
           "and the climate at the dam sites. It also sets out the channel alignments, the conditions and conflicts along them, the hydraulic design criteria of the channels, the "
           "section of every channel for the 200-year flow, the culverts at the road crossings, the dyke heights and the cost estimate of the scheme.")
    D.sub(d, "Key findings")
    D.bullet(d, f"The nine dams control {n0(t['area'])} km² of catchment and hold {n0(t['cap'])} Mm³ at full supply level. The 200-year peak inflows range from "
                f"{n0(t['qin200'][0])} to {n0(t['qin200'][1])} m³/s.")
    D.bullet(d, f"{['No', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'][len(t['full200'])]} reservoirs ({', '.join(t['full200'])}) store the whole 200-year flood; Hawasinah 02, whose {n0(A.dams_sheet().loc['Hawasinah 02', 'Reservoir'])} Mm³ reservoir drains "
                f"{n0(A.catchments().loc['Hawasinah 02', 'area_km2'])} km², attenuates the 200-year peak by {n0(t['att02'])} % only.")
    D.bullet(d, f"At the probable maximum flood the reservoirs rise {n1(t['head'][0])} to {n1(t['head'][1])} m above full supply level.")
    cs = A.channel_sections("200yr"); fp = cs[cs.cls == "FP"]; cv = A.culverts(); dk = A.dykes(); ct = A.cost_totals()
    D.bullet(d, f"The {len(cs)} channels are sized for the 200-year flow with the dams in place: the flood-protection channels carry {n0(fp.q.min())} to {n0(fp.q.max())} m³/s "
                f"with bed widths of up to {cs.wmax.max():,.0f} m at a depth of 2.5 m, or 3 m where the wadi is deeper.")
    D.bullet(d, f"The channels cross the Batinah Highway and the Coastal Road at {len(cv)} points; none of the structures on file has the width of its channel, and {n0(cv.cells.sum())} "
                f"box-culvert cells of 4 m are proposed. The {len(dk)} dykes stand {n1(dk.H_m.min())} to {n1(dk.H_m.max())} m high on the 200-year flood depth of the plain.")
    D.bullet(d, f"The estimate of the scheme is {n1(ct['total'])} million OMR: {n1(ct['channels'])} for the channels, {n1(ct['dykes'])} for the dykes and {n1(ct['culverts'])} for the culverts, "
                "at the unit rates of the master plan, land not priced.")
    D.bullet(d, f"The sediment yield of the catchments is {n0(t['yld'][0])} to {n0(t['yld'][1])} m³/km²/yr. Over 50 years the reservoirs lose {n1(t['loss50'].min())} to {n1(t['loss50'].max())} % of their "
                f"storage at full supply level; Hawasinah 02 ({n0(t['loss50']['Hawasinah 02'])} % in 50 years, {n0(t['loss100']['Hawasinah 02'])} % in 100) and Shafan 08 "
                f"({n0(t['loss50']['Shafan 08'])} % in 50 years) need a sediment management provision.")
    D.bullet(d, f"The climate at the dam sites is hot and arid: a mean annual temperature of {n1(min(c[x]['t_mean'] for x in A.DAMS))} to {n1(max(c[x]['t_mean'] for x in A.DAMS))} °C and a mean annual rainfall "
                f"of {n0(min(rains))} to {n0(max(rains))} mm; the nearest rain gauges recorded {n0(min(c[x]['gauge']['mean_annual'] for x in A.DAMS if c[x]['gauge']))} to {n0(max(c[x]['gauge']['mean_annual'] for x in A.DAMS if c[x]['gauge']))} mm a year over their short records.")
    D.pagebreak(d)

def introduction(d):
    D.h(d, 1, "Introduction")
    D.p(d, "The study area covers the governorates of North and South Al Batinah in northern Oman. The full project title is “Consultancy Services for Study and Prepare Comprehensive "
           "Master Plan for Flood Protection Dams, River Training Schemes and Updating of Flood Maps and Stormwater Drainage System in North and South Al Batinah Governorates, "
           "Sultanate of Oman”. The master plan combines dams, dykes and stormwater channels to protect the urbanised areas, the industrial zones, the infrastructure and the "
           "planned developments of the plain from flood damage.")
    D.p(d, "Block 04 lies between Al Khaburah and Saham. Its wadis rise in the Hajar foothills and run 15 to 25 km across the coastal plain before reaching the Gulf of Oman. "
           "Nine flood-protection dams sit at the foot of the hills: Hawasinah 02, Hawasinah 11 and Hawasinah UP on Wadi Al Hawasinah, Shafan 02 and Shafan 08 on Wadi Shafan, "
           "Sarami 03 and Sarami 05 on Wadi Sarami, and Sakhin 04 and Sakhin 08 (Mehmum) on Wadi Sakhin. Downstream of the dams, flood-protection channels, stormwater "
           "channels and dykes take the routed outflows and the runoff of the plain to the sea.")
    D.p(d, "All channels are designed with the upstream dams in place, since the dams attenuate the peak inflows, and the design target is the 200-year flood. Attenuated and routed "
           "dam outflows are conveyed through the channel network to the sea; dyke heights follow from two-dimensional hydrodynamic simulation. The design process follows the "
           f"stages of {T('process')}.")
    tcap(d, "Channel design process – Block 04", "process")
    D.table(d, ["Stage", "Title", "Key components and methods"], [
        ["1", "Project input", "Design rainfall, topography, land use, dam characteristics (height, reservoir, spillway)"],
        ["2", "Catchment analysis", "HEC-HMS subbasin delineation, area reduction factor, SCS curve number, time of concentration, reservoir and reach routing"],
        ["3", "Rainfall-runoff simulation (HEC-HMS)", "200-year peak flow and the other return periods, inflow and outflow hydrographs, reservoir levels, sediment yield and reservoir sedimentation"],
        ["4", "Channel alignment", "HEC-RAS 2D results, wadi geometry, site visits, client and authority input"],
        ["5", "Hydraulic channel design (SewerGEMS)", "Manning equation, depth, slope, velocity, freeboard, culvert sizing, constraints (OQ pipelines, bridges and culverts)"],
        ["6", "Performance assessment (HEC-RAS)", "Dyke heights, culvert and bridge capacity, outfalls, 200-year protection check"],
        ["7", "Outputs", "Channel dimensions, dyke heights, crossing capacities, solutions for bottlenecks"]], widths=[1.1, 3.6, 11.5], font=8.5)
    import rpt_r4; rpt_r4.process_figure(d)

def conclusions(d):
    t = _totals()
    D.h(d, 1, "Conclusion")
    D.p(d, f"The HEC-HMS model of Block 04 reproduces the catchments of the hydrology study for the nine dams and extends them to the whole plain, computed as depth-area "
           f"analyses for thirteen return periods up to the probable maximum precipitation. {['No', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'][len(t['full200'])]} of the nine reservoirs hold the whole 200-year flood and two more pass only a "
           f"fraction of it; Hawasinah 02 is the exception, with {n0(t['att02'])} % attenuation. At the probable maximum flood the reservoirs rise {n1(t['head'][0])} to {n1(t['head'][1])} m above full supply level.")
    D.p(d, f"The catchments deliver {n0(t['yld'][0])} to {n0(t['yld'][1])} m³ of sediment per square kilometre and year. The reservoirs lose {n1(t['loss50'].min())} to "
           f"{n1(t['loss50'].max())} % of their storage in 50 years; Hawasinah 02 loses {n0(t['loss50']['Hawasinah 02'])} % and Shafan 08 {n0(t['loss50']['Shafan 08'])} %, and their designs "
           "should provide for sediment management, a dead storage allowance or periodic removal.")
    D.p(d, "The channel alignments follow the wadis across the plain between the dams and the sea, within the constraints of the Batinah Expressway, the Batinah Highway, the coastal "
           "road, the planned bypass, the OQ pipelines and the cadastral land use. The channels are designed for the routed 200-year outflows with the criteria of Section 8; "
           f"their sections ({T('sections')}) carry the 200-year flow with bed widths of {A.channel_sections('200yr').wmin.min():,.0f} to {A.channel_sections('200yr').wmax.max():,.0f} m.")
    cv = A.culverts(); dk = A.dykes(); ct = A.cost_totals(); q = A.channel_quantities()
    D.p(d, f"At the {len(cv)} crossings of the Batinah Highway and the Coastal Road the existing structures on file are far below the channel widths and box culverts of the full "
           f"bed width are proposed, {n0(cv.cells.sum())} cells of 4 m in all, checked for headwater. The {len(dk)} dykes, {n1(dk.L_m.sum() / 1000)} km, are set at {n1(dk.H_m.min())} to "
           f"{n1(dk.H_m.max())} m on the 200-year flood depth of the plain with a margin and the freeboard; the two-dimensional simulation of the scheme will refine them.")
    D.p(d, f"The estimate comes to {n1(ct['total'])} million OMR at the unit rates of the master plan: {n1(ct['channels'])} million for the channels ({n0(q.cut_m3.sum() / 1e6)} million m³ of "
           f"excavation, {n1(q.fill_m3.sum() / 1e6)} million m³ of fill), {n1(ct['dykes'])} million for the dykes and {n1(ct['culverts'])} million for the culverts; the land of the corridors, "
           f"{n0(q.corridor_ha.sum())} ha, is not priced. The long-term effectiveness of the scheme depends on the reservation of the wadi corridors against encroachment, the "
           "maintenance of the channels and crossings, and the control of sand extraction in the beds.")
