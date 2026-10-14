"""Section 2 - hydrology: design rainfall, PMP, ARF, curve number (R1, self-contained)."""
from common import T, F, tcap, D, N, A, n0, n1, chart, map_fig
import omml as M

def section(d):
    D.h(d, 1, "Hydrology")
    p = D.p(d, "A comprehensive nationwide hydrology analysis was conducted for the Ministry. It covers all the rainfall stations: data cleaning, trend and outlier tests, gap "
                "filling, distribution fitting and a regional frequency analysis of the rainfall depth of each region. The 24-hour design precipitation depths and the temporal "
                "patterns of that study, for the return periods of 2 to 10 000 years, drive the rainfall-runoff simulation of Block 04.")
    N.add(p, "MAFWR, nationwide hydrology study: regional frequency analysis of the 24-hour rainfall, design patterns and the PMP grid.")
    tcap(d, "Design rainfalls", "rain")
    D.table(d, ["Recurrence interval (years)", "Depth (mm)"], [[rp, (f"{v:.1f}" if isinstance(v, float) else "PMP grid, 500 to 1 840 mm")] for rp, v in A.rainfall_design()], widths=[3, 3], font=8.5)
    D.p(d, f"The 24-hour depth is distributed in time with the temporal patterns of the nationwide study ({F('patterns')}), one for the 2-year storm, one for the 5-year, one "
           "for the 10- to 1 000-year storms, one for the 2 000- to 10 000-year storms and one for the probable maximum precipitation. All five are centred: the heaviest "
           "interval falls at the twelfth hour, and the rarer the event the flatter the pattern, from a 2-year storm that drops a third of its depth in ten minutes to a probable "
           "maximum storm spread over the whole day.")
    chart(d, "C10_rain_patterns", "Temporal distribution of the 24-hour design storm: cumulative share of the depth (left) and the share falling in each 10-minute interval (right), for the five patterns", 16, key="patterns")
    D.p(d, "The probable maximum precipitation is estimated with the storm transposition and moisture maximisation method recommended by the World Meteorological Organisation. "
           "The severest historical storms of the region are transposed to the catchment of interest and their precipitable water is raised to its theoretical upper limit on "
           "atmospheric thermodynamic principles. The resulting values are the greatest depth of precipitation that is physically possible for a given duration and area, and the "
           "basis for the design of critical hydraulic structures. The nationwide PMP grid supplies the 24-hour depth at each catchment; the dam spillways are sized for the probable "
           "maximum flood that results from it.")
    D.p(d, "The area reduction factor accounts for the spatial variability of rainfall over a catchment. Point rainfall overstates the average depth over a large catchment, because "
           "an intense storm cell seldom covers the whole catchment at once. The factor, a dimensionless value of 1 or less, converts the design point depth to the areal depth. The "
           f"values of the nationwide study ({T('arf')}) are applied to every catchment through depth-area analyses in HEC-HMS: each element of the model is computed with the storm reduced "
           "for its own contributing area, so the peak at a dam site and the peak at a channel junction each carry the right reduction. The reduction matters for the larger "
           "catchments of Block 04, where it lowers the computed peaks appreciably.")
    tcap(d, "Area reduction factor", "arf")
    D.table(d, ["Area (km²)", "ARF"], [[str(a), f"{f:.3f}"] for a, f in A.arf()], widths=[3, 3], font=8.5)
    D.p(d, "The curve number grid combines two global datasets: the ESA WorldCover 2020 land cover at 10 m, which classifies the surface roughness and vegetation, and the ISRIC "
           "SoilGrids texture at 250 m, from which the hydrologic soil groups follow. The two are aligned and combined through the standard SCS lookup table into a spatially "
           "distributed curve number. The area-weighted curve numbers of the dam catchments lie between 87.7 (Sarami 05 and Sakhin 04) and 90.5 (Hawasinah 11), the response of "
           "bare, rocky mountain soils. The initial abstraction and the lag time of each subbasin follow the SCS and Kirpich relations:")
    S = M.r("S"); M.display(d, M.seq(M.sub(M.r("I"), M.r("a")), M.EQ, M.r("0.2 "), S, M.r(",      "), S, M.EQ, M.r("25.4 "), M.delim(M.seq(M.frac(M.r("1000"), M.r("CN")), M.MINUS, M.r("10")))), number=D.next_eq())
    M.display(d, M.seq(M.sub(M.r("t"), M.r("lag")), M.EQ, M.r("0.6 "), M.frac(M.r("1"), M.r("52")), M.r(" "), M.sup(M.r("L"), M.r("0.77")), M.r(" "), M.sup(M.r("S"), M.r("−0.385"))), number=D.next_eq())
    D.symbols(d, [("Ia", "initial abstraction", "mm"), ("S", "potential maximum retention", "mm"), ("CN", "SCS curve number", "–"), ("t_lag", "lag time", "min"),
                  ("L", "length of the 10–85 flow path", "m"), ("S", "slope of the 10–85 flow path", "m/m")])
    import rpt_r4; rpt_r4.hydrology_extra(d)
