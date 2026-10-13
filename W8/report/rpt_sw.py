"""The stormwater channels report (W8, R0, the structure of the Block 6 "Hydraulic Design of Stormwater Channels" report): the
sections written for the stormwater main and secondary channels and dykes. The shared sections (hydrology, conditions, criteria,
sections, culverts, dykes, costs, appendices) come from rpt_hydrology, rpt_channels and rpt_r4 under the REPORT_ONLY=SM,SS filter
of data_facts; the flood protection channels and the dams are in the channels feasibility and hydrological report."""
import os
from common import T, F, tcap, D, N, A, n0, n1, n2, map_fig, chart
import geopandas as gpd
from common import B4
CLS = {"SM": "Stormwater main", "SS": "Stormwater secondary"}
WORD = ["No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen"]

def _lengths():
    g = gpd.read_file(os.path.join(B4, "Hydrology", "SHP", "temp", "Channels and Dykes 04102026.shp")); g = g[g["Block"] == 4]; g["km"] = g.geometry.length / 1000
    return g.groupby("CHtt")["km"].sum().to_dict()

def _facts():
    cs = A.channel_sections("200yr"); sm = cs[cs.cls == "SM"]; ss = cs[cs.cls == "SS"]; cv = A.culverts(); dk = A.dykes(); ct = A.cost_totals(); q = A.channel_quantities(); o = A.outfalls_table()
    return dict(cs=cs, sm=sm, ss=ss, cv=cv, dk=dk, ct=ct, q=q, o=o, by=_lengths())

def executive_summary(d):
    f = _facts(); cs, sm, ss, cv, dk, ct, q, o = f["cs"], f["sm"], f["ss"], f["cv"], f["dk"], f["ct"], f["q"], f["o"]
    smq = sm[sm.q > 0]; ssq = ss[ss.q > 0]
    D.title(d, "Executive Summary")
    D.sub(d, "Project context")
    D.p(d, "The Ministry of Agriculture, Fisheries Wealth and Water Resources commissioned Renardet S.A. & Partners Consulting Engineers, in joint venture with "
           "Artelia Muscat, to prepare the comprehensive master plan for flood protection dams, river training schemes and stormwater drainage in North and South Al Batinah. "
           "Block 04 covers the wadis of Al Hawasinah, Shafan, Sarami and Sakhin between the Hajar foothills and the coast, from Al Khaburah to Saham. The scheme consists of "
           "nine flood-protection dams, the flood-protection channels that carry their routed outflows to the sea, and the stormwater channels and dykes that drain the plain "
           "between them.")
    D.sub(d, "Scope of this report")
    D.p(d, f"This report presents the hydraulic design of the {len(cs)} stormwater channels of Block 04, {len(sm)} main and {len(ss)} secondary, and of the {len(dk)} stormwater "
           "dykes that lead the runoff of the plain to them: the hydrology of the catchments they drain, their alignments and the conditions along them, the design criteria, "
           "the section of every channel for the 200-year flow, the outfalls, the culverts at the road crossings, the dyke heights and the cost estimate. The nine dams and the "
           "flood-protection channels are presented in the channels feasibility and hydrological report of Block 04.")
    D.sub(d, "Key findings")
    D.bullet(d, f"The {len(cs)} stormwater channels total {n1(cs.km.sum())} km: {n1(sm.km.sum())} km of main channels and {n1(ss.km.sum())} km of secondary channels; the "
                f"{len(dk)} stormwater dykes add {n1(dk.L_m.sum() / 1000)} km.")
    D.bullet(d, f"The channels are sized for the 200-year flow of the plain with the dams in place: the main channels carry {n0(smq.q.min())} to {n0(smq.q.max())} m³/s with bed "
                f"widths of {n0(smq.wmin.min())} to {n0(smq.wmax.max())} m, the secondary channels {n0(ssq.q.min())} to {n0(ssq.q.max())} m³/s with bed widths of {n0(ssq.wmin.min())} to "
                f"{n0(ssq.wmax.max())} m, at a depth of 2.5 m" + (", or 3 m where the wadi is deeper." if any(3.0 in r.depths for r in cs.itertuples()) else "."))
    D.bullet(d, f"{WORD[len(o)]} of the channels discharge directly to the sea; the others join a flood-protection or a main channel.")
    D.bullet(d, f"The channels cross the Batinah Highway and the Coastal Road at {len(cv)} points; {n0(cv.cells.sum())} box-culvert cells of 4 m are proposed, with the full "
                f"channel depth as clear height. The {len(dk)} dykes stand {n1(dk.H_m.min())} to {n1(dk.H_m.max())} m high on the 200-year flood depth of the plain.")
    D.bullet(d, f"The estimate of the stormwater works is {n1(ct['total'])} million OMR: {n1(ct['channels'])} for the construction of the channels, {n1(ct['expropriation'])} for the "
                f"land of their corridors, {n1(ct['dykes'])} for the dykes and {n1(ct['culverts'])} for the culverts, at the unit rates and land rates of the master plan.")
    D.pagebreak(d)

def introduction(d):
    f = _facts(); cs = f["cs"]
    D.h(d, 1, "Introduction")
    D.p(d, "The study area covers the governorates of North and South Al Batinah in northern Oman. The full project title is “Consultancy Services for Study and Prepare Comprehensive "
           "Master Plan for Flood Protection Dams, River Training Schemes and Updating of Flood Maps and Stormwater Drainage System in North and South Al Batinah Governorates, "
           "Sultanate of Oman”. The master plan combines dams, dykes and stormwater channels to protect the urbanised areas, the industrial zones, the infrastructure and the "
           "planned developments of the plain from flood damage.")
    D.p(d, "Block 04 lies between Al Khaburah and Saham. Its wadis rise in the Hajar foothills and run 15 to 25 km across the coastal plain before reaching the Gulf of Oman. "
           "Nine flood-protection dams sit at the foot of the hills and the flood-protection channels take their routed outflows to the sea. Between those channels the plain "
           "drains through its own wadis and depressions; the stormwater main channels collect the runoff of the larger intermediate catchments and the stormwater secondary "
           f"channels drain the local catchments between them. This report covers the {len(cs)} stormwater channels and their dykes.")
    D.p(d, "All channels are designed with the upstream dams in place, since the dams attenuate the peak inflows, and the design target is the 200-year flood. The runoff of "
           "the plain is routed through the channel network to the sea; the dyke heights follow from the two-dimensional flood simulation. The design process follows the "
           f"stages of {T('process')}.")
    tcap(d, "Channel design process – Block 04", "process")
    D.table(d, ["Stage", "Title", "Key components and methods"], [
        ["1", "Project input", "Design rainfall, topography, land use, dam characteristics (height, reservoir, spillway)"],
        ["2", "Catchment analysis", "HEC-HMS subbasin delineation, area reduction factor, SCS curve number, time of concentration, reservoir and reach routing"],
        ["3", "Rainfall-runoff simulation (HEC-HMS)", "200-year peak flow and the other return periods at every inflow point of the channels, with the dams in place"],
        ["4", "Channel alignment", "HEC-RAS 2D results, wadi geometry, site visits, client and authority input"],
        ["5", "Hydraulic channel design (SewerGEMS)", "Manning equation, depth, slope, velocity, freeboard, culvert sizing, constraints (OQ pipelines, bridges and culverts)"],
        ["6", "Performance assessment (HEC-RAS)", "Dyke heights, culvert and bridge capacity, outfalls, 200-year protection check"],
        ["7", "Outputs", "Channel dimensions, dyke heights, crossing capacities, solutions for bottlenecks"]], widths=[1.1, 3.6, 11.5], font=8.5)
    import rpt_r4; rpt_r4.process_figure(d)

def alignments(d):
    by = _facts()["by"]
    D.h(d, 1, "Channel alignments")
    D.p(d, f"Block 04 covers the four global catchments of Al Hawasinah, Shafan, Sarami and Sakhin ({F('gca_map')}), the wadis that reach the coast between Al Khaburah and Saham.")
    D.p(d, "The channel routes were chosen from the two-dimensional flood simulation of the plain, the geometry of the existing wadis, and the site visits made with the client and the "
           "local authorities. Where the wadis leave the foothills the flow is confined, and where the plain flattens it spreads and ponds. The channels follow the wadis "
           "wherever a defined bed exists and cross the flat ground on the shortest route to the sea.")
    D.p(d, f"The stormwater channels come in two classes ({T('channels')} and {F('routes')}): the stormwater main channels, which collect the runoff of the larger intermediate "
           "catchments of the plain, and the stormwater secondary channels, which drain the local catchments between them. Dykes of the same two classes confine the flow where "
           "the ground is too flat for a channel to hold it. The flood-protection channels, drawn in grey on the maps of this report, carry the routed outflows of the dams and "
           "are designed in the channels feasibility and hydrological report.")
    tcap(d, "Stormwater channels and dykes in Block 04", "channels")
    rows = [["Stormwater main channel", n0(by.get("Sw M CH", 0))], ["Stormwater secondary channel", n0(by.get("Sw S CH", 0))], ["Stormwater main dyke", n0(by.get("Sw M D", 0))], ["Stormwater secondary dyke", n0(by.get("Sw S D", 0))]]
    tot = sum(by.get(k, 0) for k in ("Sw M CH", "Sw S CH", "Sw M D", "Sw S D")); rows.append(["**Total**", f"**{n0(tot)}**"])
    D.table(d, ["Type", "Length (km)"], rows, widths=[5, 3], font=8.5)
    map_fig(d, "M21_gca", "Global catchments of Block 04: Al Hawasinah, Shafan, Sarami and Sakhin", key="gca_map")
    map_fig(d, "M03_alignments_flood", "Channel alignments to control the 200-year flood, on the 200-year flood depth without the scheme", key="alignments")
    map_fig(d, "M04_routes", "Stormwater channel and dyke routes by category, with their names; the flood-protection channels in grey", key="routes")

def rainfall_runoff(d):
    D.h(d, 1, "Rainfall-runoff simulation")
    D.p(d, f"The runoff of the plain is computed with the HEC-HMS model of Block 04 ({F('hms')}): the catchments of the nine dams with their reservoirs, and the intermediate "
           "catchments of the plain between the dams and the sea, each with its SCS curve number and lag time, joined by the reaches of the wadis. The model is run for the "
           "design storms of the hydrology study and gives, at every junction, the peak flow and the hydrograph with the dams in place.")
    D.p(d, f"{F('q200a')} and {F('q200b')} give the 200-year peak flow at the junctions of the model; the flows at the inflow points of the stormwater channels are those of "
           "the intermediate catchments, unregulated by any dam, added reach by reach along the channels.")
    map_fig(d, "M08_hms", "HEC-HMS model for Block 04", key="hms")
    map_fig(d, "M10_q200", "(a) Q200 (m³/s) at the junctions of the HEC-HMS model, dams in place", key="q200a")
    map_fig(d, "M11_q200_plain", "(b) Q200 (m³/s) at the dams and the junctions downstream of them, dams in place", size="A3", key="q200b")
    import rpt_r4; rpt_r4.plain_catchments(d)

def outfalls(d):
    o = A.outfalls_table(); cs = A.channel_sections("200yr")
    D.h(d, 1, "Outfalls")
    D.p(d, f"{WORD[len(o)]} of the {len(cs)} stormwater channels discharge directly to the sea, at the crossings of the coastal road; the others join a flood-protection channel "
           f"or a main channel upstream of its outfall. At the 200-year flow the sea outfalls of the stormwater channels receive {n0(o.Q200.min())} to {n0(o.Q200.max())} m³/s.")
    import rpt_r4; rpt_r4.outfalls_extra(d)

def conclusions(d):
    f = _facts(); cs, sm, ss, cv, dk, ct, q = f["cs"], f["sm"], f["ss"], f["cv"], f["dk"], f["ct"], f["q"]
    smq = sm[sm.q > 0]; ssq = ss[ss.q > 0]
    D.h(d, 1, "Conclusion")
    D.p(d, f"The {len(cs)} stormwater channels of Block 04 drain the plain between the flood-protection channels to the sea. Their alignments follow the wadis within the "
           "constraints of the Batinah Expressway, the Batinah Highway, the coastal road, the planned bypass, the OQ pipelines and the cadastral land use. They are designed "
           f"for the 200-year runoff of their catchments with the dams in place, with the criteria of Section 6; their sections ({T('sections')}) carry the 200-year flow with "
           f"bed widths of {n0(cs.wmin.min())} to {n0(cs.wmax.max())} m: the main channels {n0(smq.q.min())} to {n0(smq.q.max())} m³/s, the secondary channels {n0(ssq.q.min())} to "
           f"{n0(ssq.q.max())} m³/s.")
    D.p(d, f"At the {len(cv)} crossings of the Batinah Highway and the Coastal Road box culverts of the full bed width and the full channel depth are proposed, "
           f"{n0(cv.cells.sum())} cells of 4 m in all, checked for headwater. The {len(dk)} stormwater dykes, {n1(dk.L_m.sum() / 1000)} km, are set at {n1(dk.H_m.min())} to "
           f"{n1(dk.H_m.max())} m on the 200-year flood depth of the plain with a margin and the freeboard; the two-dimensional simulation of the scheme will refine them.")
    D.p(d, f"The estimate of the stormwater works comes to {n1(ct['total'])} million OMR at the unit rates and land rates of the master plan: {n1(ct['channels'])} million for the "
           f"construction of the channels ({n1(q.cut_m3.sum() / 1e6)} million m³ of excavation, {n1(q.fill_m3.sum() / 1e6)} million m³ of fill), {n1(ct['expropriation'])} million for "
           f"the land of their corridors, {n1(ct['dykes'])} million for the dykes and {n1(ct['culverts'])} million for the culverts. The long-term effectiveness of the scheme "
           "depends on the reservation of the wadi corridors against development, the removal of the encroachments that narrow them, and the maintenance of the channels "
           "and culverts after every flood.")
