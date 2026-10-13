"""Sections 3 and 4 - channel alignments; channel condition and conflicts. Section 7 - hydraulic design criteria and main issues (Block 6 structure)."""
from common import T, F, tcap, D, N, A, n0, n1, map_fig
import geopandas as gpd, os
from common import B4

def _lengths():
    g = gpd.read_file(os.path.join(B4, "Hydrology", "SHP", "temp", "Channels and Dykes 04102026.shp")); g = g[g["Block"] == 4]; g["km"] = g.geometry.length / 1000
    by = g.groupby("CHtt")["km"].sum().to_dict(); return by, float(g.km.sum())

def alignments(d):
    by, tot = _lengths()
    D.h(d, 1, "Channel alignments")
    D.p(d, "The channel routes were chosen from the two-dimensional flood simulation of the plain, the geometry of the existing wadis, and the site visits made with the client and the "
           "local authorities. The flood flow pattern depends on the terrain: where the wadis leave the foothills the flow is confined, and where the plain flattens it spreads and ponds. "
           "The channels follow the wadis wherever a defined bed exists and cross the flat ground on the shortest route to the sea.")
    D.p(d, f"By the flood or stormwater flow they carry, the channels are classified in three categories ({T('channels')} and {F('routes')}): flood-protection channels, which take the routed "
           "outflows of the dams and the main wadis to the sea; stormwater main channels, which collect the runoff of the larger intermediate catchments of the plain; and stormwater "
           "secondary channels, which drain the local catchments between them. Dykes of the same three classes confine the flow where the ground is too flat for a channel to hold it.")
    tcap(d, "Channels and dykes in Block 04", "channels")
    rows = [["Flood protection channel", n0(by.get("FP CH", 0))], ["Stormwater main channel", n0(by.get("Sw M CH", 0))], ["Stormwater secondary channel", n0(by.get("Sw S CH", 0))],
            ["Flood protection dyke", n0(by.get("FP D", 0))], ["Stormwater main dyke", n0(by.get("Sw M D", 0))], ["Stormwater secondary dyke", n0(by.get("Sw S D", 0))], ["**Total**", f"**{n0(tot)}**"]]
    D.table(d, ["Type", "Length (km)"], rows, widths=[5, 3], font=8.5)
    map_fig(d, "M03_alignments_flood", "Channel alignments to control the 200-year flood, on the 200-year flood depth without the scheme", key="alignments")
    map_fig(d, "M04_routes", "Channel and dyke routes by category, with the channel and dyke names", key="routes")

def conditions(d):
    D.h(d, 1, "Channel condition and conflicts")
    D.p(d, "Several conditions along the routes govern how the channels can be designed: the existing flow patterns, the roads and the utilities that cross or run along the wadis, "
           "and the land use. The flood flow pattern depends strongly on the geometry of the plain; where the wadis leave the hills and spread over the flatter ground, the flow widens "
           "and loses its defined bed.")
    D.p(d, f"The Batinah Expressway, the Batinah Highway, the Batinah Coastal Road, the planned North Batinah bypass and the OQ pipelines are the main constraints ({F('roads')}). The "
           "existing crossings of the roads fix the channel levels and widths where they are kept, and the shallow pipelines limit the depth of the channels that cross them. Other "
           "utility corridors, electricity, water, wastewater and stormwater, also have to be respected and their exact position and depth are required for the detailed design.")
    map_fig(d, "M05_roads_utilities", "Roads and utilities", key="roads")
    D.p(d, f"The land use of the plain, managed mainly by the Ministry of Housing and Urban Planning, also shapes the alignments ({F('landuse')}). Houses have been built inside the wadis "
           "or have encroached on them and narrowed their beds, and farms extend their boundaries into the wadi. The channels keep to the wadi corridor wherever it is free and "
           "deviate around the built plots where it is not.")
    map_fig(d, "M06_landuse", "Land use", key="landuse")

def hydraulic(d):
    D.h(d, 1, "Hydraulic design criteria")
    D.p(d, "The hydraulic design of the channels follows one set of criteria for the channel geometry, the flow parameters, the slopes, the outfall conditions and the crossings, "
           f"applied to every reach so that the system is coherent and hydraulically sound. The criteria are summarised in {T('criteria')}.")
    tcap(d, "Channel design criteria", "criteria")
    D.table(d, ["Item", "Criterion"], [
        ["Channel geometry", "Trapezoidal section; depth 2.5 m, or the depth of the existing wadi where it is deeper; side slopes 1:1.5 on both sides; freeboard 0.6 m"],
        ["Flow formula", "Manning equation, Q = (1/n) A R^(2/3) S^(1/2)"],
        ["Manning's n", "Earth channels 0.03; concrete culverts 0.02 (higher than the material value, for sedimentation)"],
        ["Velocity and slope", "Maximum velocity 3 m/s; minimum slope at the flat sea outfalls 0.0003 m/m"],
        ["Outfall conditions", "Bank height = max (MHHW, flow depth) + 0.6 m freeboard; the channels terminate at the coastal road crossings"],
        ["Culvert design", "Barrel height = channel height; full channel width covered; slope 0.5 to 5 %; n = 0.02"],
        ["Cut and fill", "Cut preferred, so that the surrounding runoff drains into the channel; fill only where a constraint forces the bed above ground, with embankments on both sides and a return to cut within 500 m"],
        ["Geometric constraints", "OQ pipelines; existing culverts and bridges at the Expressway, the Batinah Highway and the coastal road; outfalls"]], widths=[3.2, 12.4], font=8.5)
    tcap(d, "Mean tidal levels in North and South Al Batinah (m), Oman Maritime Book 2024", "tides")
    D.table(d, ["Reference port", "Mean", "MHHW", "MLHW", "MHLW", "MLLW"], [["Al Khaburah", "1.80", "0.70", "0.62", "-0.23", "-1.00"], ["Saham", "1.82", "0.68", "0.61", "-0.25", "-1.02"], ["Port of Suhar (Majis)", "1.20", "1.40", "1.30", "0.50", "-0.30"]], widths=[4, 2, 2, 2, 2, 2], font=8.5)
    D.p(d, "The channels are trapezoidal in cut and in fill, with side slopes of 1:1.5 on the inner and the outer face. Cut is preferred, because the surrounding surface runoff then "
           "drains into the channel; where a constraint forces the bed above the ground, the channel runs in fill between two embankments and returns to cut within 500 m.")
    D.h(d, 2, "Main issues in channel design")
    D.p(d, "A number of constraints and site-specific challenges affect both the hydraulic performance of the channels and the practicality of their construction. They fall in four "
           "groups: road and culvert crossings, energy corridors and utilities, wadi path and land-use conflicts, and sand mining and environmental risks.")
    tcap(d, "Challenges in the design of the channels", "challenges")
    D.table(d, ["Group", "Issues"], [
        ["Culverts and road crossings", "Existing culvert and bridge sizes insufficient for the channelised flow; drainage crossings that have altered the wadi paths downstream; floodways recommended for the internal roads"],
        ["Energy corridors and utilities", "Conflicts with the OQ pipelines, which are shallow; the exact position and depth of every utility are required for the detailed design"],
        ["Wadi path and land-use conflicts", "Wadi ownership by the Ministry is critical for enforcement; wadis blocked by constructions; depressed areas where the wadis flatten into wide plains and pond around homes and farms; wadis narrowed as farm owners extend their boundaries; the wadi bed to be reserved against developments within the 200-year flood extent"],
        ["Sand mining and environmental risks", "Sand extraction up to 3 m deep destabilises the channel beds; animal carcasses in the ponds after floods are a health hazard"],
        ["Consequences", "The system is not designed for cyclone-level protection; conveyance is constrained by undersized crossings, narrowed wadis and shallow pipelines; the upstream dams are essential to capture and reduce the flood volumes before they reach the developments"]], widths=[4, 11.6], font=8.5)
