"""Section 6 - sediment yield of the catchments and the reservoir volume reduction (text on the Majlas report pattern)."""
from common import T, F, tcap, D, N, A, n0, n1, n2, n3, chart, map_fig, fig, lab, SEDF
import omml as M
import os

def section(d):
    y = A.sediment_yield(); s50, s100 = A.sedimentation(50), A.sedimentation(100); cat = A.catchments(); eav = A.eav_summary()
    D.h(d, 1, "Sediment yield and reservoir sedimentation")
    D.h(d, 2, "Soil loss of the catchments")
    p = D.p(d, "The soil loss of each catchment is estimated with the Revised Universal Soil Loss Equation on a 250 m grid from public remote-sensing data:")
    N.add(p, "Renard, K.G. et al. (1997), Predicting soil erosion by water: a guide to conservation planning with the Revised Universal Soil Loss Equation (RUSLE), USDA Agriculture Handbook 703.")
    M.display(d, M.seq(M.r("A"), M.EQ, M.r("R "), M.r("K "), M.r("LS "), M.r("C "), M.r("P")), number=D.next_eq())
    D.symbols(d, [("A", "mean annual soil loss", "t/ha/yr"), ("R", "rainfall erosivity", "MJ mm/(ha h yr)"), ("K", "soil erodibility", "t ha h/(ha MJ mm)"), ("LS", "slope length and steepness factor", "–"), ("C", "cover management factor", "–"), ("P", "support practice factor, 1 (no conservation practice)", "–")])
    D.p(d, "The rainfall erosivity comes from the mean monthly precipitation of the SM2RAIN climatology at 1 km, the soil erodibility from the sand, silt and clay fractions of the "
           "SoilGrids topsoil by the Williams relation, the slope factor from the Copernicus 30 m terrain model and its flow accumulation by Moore and Burch, and the cover factor from "
           "the vegetation index of a Landsat 8 mosaic. With no conservation practice in the catchments, the support practice factor is 1:")
    M.display(d, M.seq(M.r("R"), M.EQ, M.r("1.73 × "), M.sup(M.r("10"), M.seq(M.r("1.5 "), M.delim(M.seq(M.func("log", M.sub(M.r("P"), M.r("m"))), M.MINUS, M.r("0.08188")))))), number=D.next_eq())
    M.display(d, M.seq(M.r("LS"), M.EQ, M.r("1.4 "), M.sup(M.delim(M.frac(M.r("FA · 30"), M.r("22.13"))), M.r("0.4")), M.r(" "), M.sup(M.delim(M.frac(M.func("sin", M.r("θ")), M.r("0.0896"))), M.r("1.3")), M.r(",      "), M.r("C"), M.EQ, M.r("0.1 "), M.frac(M.seq(M.r("1"), M.MINUS, M.r("NDVI")), M.r("2"))), number=D.next_eq())
    D.symbols(d, [("P_m", "mean monthly precipitation", "mm"), ("FA", "flow accumulation, cells of 30 m, capped at 300", "–"), ("θ", "slope angle, capped at 30°", "°"), ("NDVI", "normalised difference vegetation index", "–")])
    D.p(d, f"The catchment means of the factors and of the soil loss are listed in {T('rusle')} and mapped in {F('rusle_map')}. The soil loss runs from {n1(y.soil_loss_t_ha_yr.min())} t/ha/yr "
           f"(Sakhin 04) to {n1(y.soil_loss_t_ha_yr.max())} t/ha/yr (Hawasinah 11); the steep mountain catchments carry the highest erosivity and slope factors, the catchments of the "
           "foothills the lowest.")
    tcap(d, "RUSLE factors and soil loss, catchment means", "rusle")
    rows = [[lab(dam), n1(y.loc[dam, "R"]), n3(y.loc[dam, "K"]), n1(y.loc[dam, "LS"]), f"{y.loc[dam, 'C']:.4f}", "1", n1(y.loc[dam, "soil_loss_t_ha_yr"])] for dam in A.DAMS]
    D.table(d, ["Dam", "R", "K", "LS", "C", "P", "Soil loss A (t/ha/yr)"], rows, widths=[3.4, 2, 2, 2, 2, 1.4, 2.6], font=8.5)
    map_fig(d, "M07_rusle", "RUSLE factors and soil loss over the dam catchments, and the sediment yield delivered to each dam", size="A3", key="rusle_map")
    D.h(d, 2, "Sediment delivery and yield")
    p = D.p(d, "Only part of the eroded soil reaches the dam; the rest settles on the way. The sediment delivery ratio follows Williams (1977) from the catchment area, its relief ratio "
                "and its curve number; the relief ratio is the relief of the catchment divided by the longest flow path to the dam:")
    N.add(p, "Williams, J.R. (1977), Sediment delivery ratios determined with sediment and runoff models, IAHS Publication 122. The delivered mass is converted to a volume at 1.5 t/m³.")
    M.display(d, M.seq(M.r("SDR"), M.EQ, M.r("1.366 × "), M.sup(M.r("10"), M.r("−11")), M.r(" "), M.sup(M.r("A"), M.r("−0.1")), M.r(" "), M.sup(M.r("RR"), M.r("0.363")), M.r(" "), M.sup(M.r("CN"), M.r("5.444"))), number=D.next_eq())
    D.symbols(d, [("SDR", "sediment delivery ratio", "–"), ("A", "catchment area", "km²"), ("RR", "relief ratio, relief / longest flow path", "–"), ("CN", "area-weighted curve number", "–")])
    p = D.p(d, f"The equation gives delivery ratios of {y.sdr_williams.min():.2f} to {y.sdr_williams.max():.2f} for the catchments of Block 04; a floor of 0.2 is adopted for the design, together with a minimum sediment yield "
               f"of 90 m³/km²/yr, so that the storage lost to sedimentation is not underestimated for the smaller and gentler catchments. {T('sdr')} gives the resulting sediment yield "
               "and the sediment delivered to each dam in 50 and 100 years.")
    N.add(p, "Hawasinah UP and Shafan 08 are assessed on their whole catchment, without credit for the sediment that the reservoirs upstream of them (Hawasinah 02 and 11, Shafan 02) will trap; their sediment loads are therefore upper bounds.")
    tcap(d, "Sediment delivery and yield of the dam catchments", "sdr")
    rows = [[lab(dam), n0(cat.loc[dam, "area_km2"]), f"{y.loc[dam, 'relief_ratio']:.4f}", n1(y.loc[dam, "cn"]), "Williams (1977)", n3(y.loc[dam, "sdr_williams"]), n2(y.loc[dam, "sdr_used"]), "1.5", n0(y.loc[dam, "yield_raw_m3_km2_yr"]), n0(y.loc[dam, "yield_m3_km2_yr"]), n2(y.loc[dam, "sed50_Mcm"]), n2(y.loc[dam, "sed100_Mcm"]), n0(y.loc[dam, "tc_min"])] for dam in A.DAMS]
    D.table(d, ["Dam", "Area (km²)", "Basin relief ratio", "CN", "SDR method", "SDR value", "SDR used (min 0.2)", "Sediment density (t/m³)", "Mean soil loss (m³/km²/yr) with SDR", "Yield used (m³/km²/yr, min 90)", "Sediment in 50 yr (Mcm)", "Sediment in 100 yr (Mcm)", "Tc (min)"],
            rows, widths=[2.6, 1.3, 1.4, 1.1, 1.9, 1.3, 1.3, 1.3, 1.6, 1.6, 1.4, 1.4, 1.1], font=7)
    chart(d, "C07_sediment_steps", "From soil loss to sediment yield: the catchment mean soil loss, the delivery ratio used and the yield delivered to each dam", 16, key="sed_steps")
    map_fig(d, "M09_sediment50", "Sediment delivered to each dam in 50 years (Mcm) and the storage lost at full supply level", key="yield_map")
    D.h(d, 2, "Reservoir volume reduction")
    p = D.p(d, "The storage each reservoir loses to the deposited sediment, and its elevation-area-volume curve after 50 and 100 years, follow Chapter 2, Section 2.6 of the "
                "USBR Erosion and Sedimentation Manual. The three components are the reservoir sediment trap efficiency (§2.6.1), the density of the deposited sediment (§2.6.2) and "
                "the distribution of the sediment within the reservoir by the Empirical Area-Reduction Method (§2.6.3).")
    N.add(p, "U.S. Bureau of Reclamation (2006), Erosion and Sedimentation Manual, Chapter 2, Section 2.6: Brune (1953); Lara and Pemberton (1965); Miller (1953); Borland and Miller (1960); Lara (1962).")
    D.h(d, 3, "Reservoir sediment trap efficiency")
    D.p(d, "The trap efficiency is the fraction of the inflowing sediment retained in the reservoir. For large storage reservoirs the manual recommends Brune's median curve, in which "
           "the efficiency is a function of the ratio of the reservoir capacity to the mean annual inflow. The reservoirs of Block 04 are large relative to their sediment supply and "
           "a trap efficiency of 100 % is adopted, a conservative assumption for the storage loss. The volume of sediment retained over the design horizon is:")
    M.display(d, M.seq(M.r("S"), M.EQ, M.sub(M.r("q"), M.r("s")), M.r(" "), M.sub(M.r("A"), M.r("c")), M.r(" T η")), number=D.next_eq())
    D.symbols(d, [("S", "sediment volume retained", "m³"), ("q_s", f"specific sediment yield of {T('sdr')}", "m³/km²/yr"), ("A_c", "catchment area", "km²"), ("T", "design horizon, 50 and 100 years", "years"), ("η", "trap efficiency, 1.0", "–")])
    D.h(d, 3, "Density of deposited sediment")
    D.p(d, "The deposited dry unit weight characterises the deposit and converts the sediment mass to the volume it occupies in the reservoir. The initial unit weight is given by "
           "Lara and Pemberton from the clay, silt and sand fractions of the incoming sediment and the reservoir operation; the reservoirs of Block 04 are flood-protection "
           "reservoirs that stand empty between floods (operation 3, reservoir normally empty), for which the deposit does not compact with time and the unit weight after T years "
           "equals the initial one:")
    M.display(d, M.seq(M.sub(M.r("W"), M.r("1")), M.EQ, M.sub(M.r("W"), M.r("c")), M.r(" "), M.sub(M.r("p"), M.r("c")), M.PLUS, M.sub(M.r("W"), M.r("m")), M.r(" "), M.sub(M.r("p"), M.r("m")), M.PLUS, M.sub(M.r("W"), M.r("s")), M.r(" "), M.sub(M.r("p"), M.r("s"))), number=D.next_eq())
    M.display(d, M.seq(M.sub(M.r("W"), M.r("T")), M.EQ, M.sub(M.r("W"), M.r("1")), M.PLUS, M.r("0.4343 K "), M.delim(M.seq(M.frac(M.r("T"), M.seq(M.r("T"), M.MINUS, M.r("1"))), M.r(" "), M.func("ln", M.r("T")), M.MINUS, M.r("1")))), number=D.next_eq())
    D.symbols(d, [("W_1", "initial dry unit weight", "kg/m³"), ("W_c, W_m, W_s", "clay, silt and sand coefficients for operation 3: 641, 1 150, 1 550", "kg/m³"), ("p_c, p_m, p_s", "clay, silt and sand fractions of the incoming sediment", "–"),
                  ("W_T", "average unit weight after T years", "kg/m³"), ("K", "compaction constant, 0 for operation 3", "–")])
    D.p(d, f"The sediment yield of {T('sdr')} is expressed as a volume at 1.5 t/m³; the deposited volume is rescaled to the deposited unit weight, V_dep = V_trap × 1 500 / W_T. The "
           "catchment topsoil texture is taken from the ISRIC SoilGrids clay, silt and sand contents averaged over each catchment.")
    D.h(d, 3, "Sediment distribution: Empirical Area-Reduction Method")
    D.p(d, "The deposited sediment is distributed by depth with the Empirical Area-Reduction Method. The reservoir is assigned one of four standard types from the shape factor m, "
           "the slope of the logarithm of capacity against the logarithm of depth of the original curve, and each type has a relative sediment-area design curve:")
    M.display(d, M.seq(M.r("a"), M.delim(M.r("p")), M.EQ, M.r("C "), M.sup(M.r("p"), M.r("A")), M.r(" "), M.sup(M.delim(M.seq(M.r("1"), M.MINUS, M.r("p"))), M.r("B"))), number=D.next_eq())
    D.symbols(d, [("a(p)", "relative sediment area", "–"), ("p", "relative depth from the reservoir bed (0) to full supply level (1)", "–"), ("C, A, B", "type coefficients: type II 2.487, 0.57, 0.41; type III 16.967, 1.15, 2.32", "–")])
    fig(d, os.path.join(SEDF, "design_curves.png"), "Sediment distribution design curves (reproduction of USBR Figure 2.25): percentage of the reservoir depth against the percentage of the sediment deposited, for types I to IV and the area-increment line.", 12.5)
    fig(d, os.path.join(SEDF, "sediment_area_functions.png"), "Relative sediment-area functions a(p) = C·pᴬ·(1−p)ᴮ for reservoir types I to IV.", 12.5)
    D.p(d, "The new zero-capacity elevation at the dam is the relative depth p₀ at which the reservoir function f(p) = (S − V_h) / (H A_h) equals the type curve F(p) = ∫ a dp / a(p), "
           "where V_h and A_h are the original capacity and area at the elevation of relative depth p and H the original reservoir depth. Below p₀ the reservoir is filled completely; "
           "above it the sediment area is a(p) scaled to the sediment volume, and the revised area and capacity follow by subtracting the sediment area and volume from the original curves.")
    D.h(d, 3, "Input data and results")
    tcap(d, "Sediment-supply and soil-texture inputs", "sed_inputs")
    rows = [[lab(dam), n0(cat.loc[dam, "area_km2"]), n0(y.loc[dam, "yield_m3_km2_yr"]), n0(s50.loc[dam, "clay"] * 100), n0(s50.loc[dam, "silt"] * 100), n0(s50.loc[dam, "sand"] * 100), n0(s50.loc[dam, "WT_kg_m3"]), f"{s50.loc[dam, 'shape_m']:.2f}", ["", "I", "II", "III", "IV"][int(s50.loc[dam, "reservoir_type"])]] for dam in A.DAMS]
    D.table(d, ["Dam", "Catchment (km²)", "Sediment yield (m³/km²/yr)", "Clay (%)", "Silt (%)", "Sand (%)", "Deposited unit weight (kg/m³)", "Shape factor m", "Reservoir type"], rows, widths=[3.2, 1.8, 2, 1.4, 1.4, 1.4, 2.2, 1.6, 1.6], font=8)
    D.p(d, f"{T('sed_results')} gives the sediment deposited in 50 and 100 years, the revised capacity at full supply level, the storage lost and the rise of the bed at the dam. Seven "
           f"reservoirs lose {n1(s50.loss_pct.drop(['Hawasinah 02', 'Shafan 08']).min())} to {n1(s50.loss_pct.drop(['Hawasinah 02', 'Shafan 08']).max())} % of their storage in 50 years and "
           f"{n1(s100.loss_pct.drop(['Hawasinah 02', 'Shafan 08']).min())} to {n1(s100.loss_pct.drop(['Hawasinah 02', 'Shafan 08']).max())} % in 100 years. Hawasinah 02 and Shafan 08 are the exceptions: "
           f"{n2(s50.loc['Hawasinah 02', 'deposited_Mm3'] / 50 * 1000 / 1000)} Mm³ of sediment a year settle in the {n1(s50.loc['Hawasinah 02', 'capacity_fsl_Mm3'])} Mm³ reservoir of Hawasinah 02, which "
           f"loses {n0(s50.loc['Hawasinah 02', 'loss_pct'])} % of its storage in 50 years and {n0(s100.loc['Hawasinah 02', 'loss_pct'])} % in 100, and Shafan 08 loses {n0(s50.loc['Shafan 08', 'loss_pct'])} % "
           f"and {n0(s100.loc['Shafan 08', 'loss_pct'])} %. Their designs should provide for sediment management, a dead storage allowance or periodic removal; at Hawasinah 02 the lost "
           "storage also degrades a flood-routing performance that already passes the 200-year peak almost unattenuated.")
    tcap(d, "Reservoir volume reduction after 50 and 100 years", "sed_results")
    rows = [[lab(dam), n2(s50.loc[dam, "capacity_fsl_Mm3"]), n2(s50.loc[dam, "deposited_Mm3"]), n2(s50.loc[dam, "revised_capacity_fsl_Mm3"]), n1(s50.loc[dam, "loss_pct"]), n1(s50.loc[dam, "bed_rise_m"]), n2(s100.loc[dam, "deposited_Mm3"]), n2(s100.loc[dam, "revised_capacity_fsl_Mm3"]), n1(s100.loc[dam, "loss_pct"]), n1(s100.loc[dam, "bed_rise_m"])] for dam in A.DAMS]
    D.table(d, ["Dam", "Capacity at FSL (Mm³)", "Deposit 50 yr (Mm³)", "Capacity 50 yr (Mm³)", "Loss 50 yr (%)", "Bed rise 50 yr (m)", "Deposit 100 yr (Mm³)", "Capacity 100 yr (Mm³)", "Loss 100 yr (%)", "Bed rise 100 yr (m)"],
            rows, widths=[3, 1.6, 1.5, 1.6, 1.3, 1.4, 1.5, 1.6, 1.3, 1.4], font=7.5)
    fig(d, os.path.join(SEDF, "storage_loss_summary.png"), "Storage lost at full supply level after 50 and 100 years, per dam.", 15.5)
    fig(d, os.path.join(SEDF, "eav_revised_Hawasinah_02.png"), "Hawasinah 02: elevation-area-volume curves before and after sedimentation, capacity on the lower axis and area on the upper axis. The curves of the other dams are in Appendix B.", 16)
