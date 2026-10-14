"""Section - the climate at each dam site: 9 km reanalysis per dam, the MRMWR gauges, wind roses per dam, climate change."""
from common import T, F, tcap, D, N, A, n0, n1, fig, chart, image_grid, lab, CLIF
import os

def section(d):
    c = A.climate9(); MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    spread = max(abs(c[d_]["monthly"][str(i)]["rain"] - sum(c[x]["monthly"][str(i)]["rain"] for x in A.DAMS) / len(A.DAMS)) for d_ in A.DAMS for i in range(1, 13))
    D.h(d, 1, "Climate at the dam sites")
    D.h(d, 2, "Record used")
    p = D.p(d, "The climate at each dam site is described from the ECMWF reanalysis at 9 km resolution read at the dam axis: daily temperature and rainfall for 2001 to 2023 and "
                "hourly wind at 10 m for 2015 to 2024. Neighbouring dams fall in the same grid cell and share a record: Shafan 02, Shafan 08 and Sarami 03 on one hand, "
                f"Sakhin 04 and Sakhin 08 on the other. The rain gauges of the Ministry nearest to the dams, 3 to 14 km away, add the measured rainfall of recent years ({T('gauges')}).")
    N.add(p, "ECMWF IFS at 9 km (2017 on) and ERA5 / ERA5-Land before, through the Open-Meteo historical archive, read in October 2026 at the dam axes. MRMWR rain gauges: gap-filled daily record of July 2024.")
    D.h(d, 2, "Temperature and rainfall")
    t_lo, t_hi = min(c[x]["t_mean"] for x in A.DAMS), max(c[x]["t_mean"] for x in A.DAMS)
    D.p(d, f"The climate is hot and arid. The mean annual temperature at the dams is {n1(t_lo)} to {n1(t_hi)} °C; the hottest month is June or July, with mean daily maxima of "
           f"{n1(min(c[x]['t_max_value'] for x in A.DAMS))} to {n1(max(c[x]['t_max_value'] for x in A.DAMS))} °C, and the coolest January, with mean daily minima of "
           f"{n1(min(c[x]['t_min_value'] for x in A.DAMS))} to {n1(max(c[x]['t_min_value'] for x in A.DAMS))} °C. The mean annual rainfall is "
           f"{n0(min(c[x]['rain_mean_annual'] for x in A.DAMS))} to {n0(max(c[x]['rain_mean_annual'] for x in A.DAMS))} mm, lowest at Hawasinah UP near the coast and highest at the "
           f"dams of the foothills, with a strong variability from year to year: the driest years bring under 30 mm and the wettest over 200 mm. Most of the rain falls from November to "
           f"April, with a secondary summer peak from the convective storms over the mountains.")
    tcap(d, "Temperature and rainfall at the dam sites, 2001–2023", "climate_tr")
    rows = [[lab(dam), n1(c[dam]["t_mean"]), f"{c[dam]['t_max_month']} {n1(c[dam]['t_max_value'])}", f"{c[dam]['t_min_month']} {n1(c[dam]['t_min_value'])}", n1(c[dam]["t_abs_max"]), n1(c[dam]["t_abs_min"]), n0(c[dam]["rain_mean_annual"]), f"{n0(c[dam]['rain_min'])} – {n0(c[dam]['rain_max'])}", n0(c[dam]["wet_days"]), n0(c[dam]["rain_share_nov_apr"])] for dam in A.DAMS]
    D.table(d, ["Dam", "Mean T (°C)", "Hottest month, mean daily max (°C)", "Coolest month, mean daily min (°C)", "Absolute max (°C)", "Absolute min (°C)", "Mean annual rain (mm)", "Driest – wettest year (mm)", "Wet days a year", "Nov–Apr share (%)"], rows, widths=[3, 1.3, 2.2, 2.2, 1.4, 1.4, 1.5, 1.9, 1.3, 1.4], font=7.5)
    D.p(d, f"{F('monthly')} shows the monthly air temperature and rainfall of Block 04 and {F('annual')} its annual rainfall, both as the average of the nine dam sites; the "
           f"sites differ from that average by at most {spread:.0f} mm in any month, and their own annual means are given in {T('climate_tr')}.")
    chart(d, "C08_monthly_climate", "Monthly air temperature and rainfall of Block 04, 2001–2023, averaged over the nine dam sites", 16, key="monthly")
    chart(d, "C09_annual_rain", "Annual rainfall of Block 04, 2001–2023, averaged over the nine dam sites, and its mean", 16, key="annual")
    near, st = A.gauges()
    D.p(d, f"The rain gauges of the Ministry nearest to each dam are listed in {T('gauges')} with their recent records. The telemetry gauges of the plain and the foothills recorded "
           f"{n0(st.loc[[s for s in st.index if st.loc[s, 'years'] >= 4 and st.loc[s, 'mean_annual'] > 20], 'mean_annual'].min())} to {n0(st.loc[[s for s in st.index if st.loc[s, 'years'] >= 4 and st.loc[s, 'mean_annual'] > 20], 'mean_annual'].max())} mm a year over "
           "four to seven complete years, with the extreme year 2017 above 400 mm at some of them. The records are short and are shown beside the reanalysis, which covers 23 years, not instead of it.")
    tcap(d, "Rain gauges nearest to the dams and their records", "gauges")
    rows = []
    for dam in A.DAMS:
        g = c[dam]["gauge"]
        if g: rows.append([lab(dam), g["name"], n1(g["dist_km"]), str(g["years"]), f"{g['first']}–{g['last']}", n0(g["mean_annual"])])
    D.table(d, ["Dam", "Nearest gauge with a record", "Distance (km)", "Complete years", "Period", "Mean annual rainfall (mm)"], rows, widths=[3.2, 3.2, 1.8, 1.8, 2, 2.4], font=8.5)
    D.h(d, 2, "Wind")
    D.p(d, f"The wind at 10 m averages {n1(min(c[x]['wind_mean'] for x in A.DAMS))} to {n1(max(c[x]['wind_mean'] for x in A.DAMS))} m/s at the dam sites and is calm, below 1 m/s, for "
           f"{n0(min(c[x]['wind_calm_pct'] for x in A.DAMS))} to {n0(max(c[x]['wind_calm_pct'] for x in A.DAMS))} % of the hours. At the dams of the foothills the land breeze from the south-west "
           "and west, flowing down the wadis at night, takes the largest share of the hours, and the north-easterly sea breeze the afternoons; at Hawasinah UP and Sarami 05, "
           f"nearer the coast, the sea breeze from the north-east to east-north-east prevails. Speeds above 8 m/s are rare. The wind rose of each dam is given in {T('windroses')}.")
    image_grid(d, [(os.path.join(CLIF, f"windrose_{dam.replace(' ', '_')}.png"), lab(dam)) for dam in A.DAMS], "Wind roses at the dam sites, all hours 2015–2024: the direction the wind blows from and the share of hours in each speed class", cols=3, width_cm=5.2, key="windroses")
    D.h(d, 2, "Climate change")
    p = D.p(d, f"The records themselves show a warming of {min(c[x]['t_trend_c_per_decade'] for x in A.DAMS):.2f} to {max(c[x]['t_trend_c_per_decade'] for x in A.DAMS):.2f} °C per decade over 2001 to 2023. The Sixth "
                "Assessment Report of the IPCC places the Arabian Peninsula among the regions warming faster than the global mean, with more frequent and longer hot spells, and projects "
                "for the Gulf of Oman coast a mean annual rainfall that stays low and uncertain in sign while the intensity of the heaviest daily rainfall increases with the warming of "
                "the sea and the air. The tropical cyclones of the Arabian Sea, Gonu in 2007 and Shaheen in 2021, have already brought daily totals to the Batinah coast beyond anything "
                "in the earlier gauged record.")
    N.add(p, "IPCC (2021), Climate Change 2021: The Physical Science Basis, Sixth Assessment Report, Working Group I, Chapter 11 and Atlas, regional findings for the Arabian Peninsula.")
    D.p(d, "For the dams this means three things. The design rainfall of the national study, derived from the gauged record, is the floor of the flood load and not its ceiling; the "
           "spillway capacity and the head at the probable maximum flood are the margin against a larger event. Hotter and drier years lengthen the empty periods of the reservoirs and "
           "the exposure of their beds, and more intense storms raise the sediment yield above the long-term rate, so the storage lost to sedimentation should be read as a lower "
           "bound. The operating rules of the outlets and the freeboard of the downstream channels should be reviewed against the updated rainfall statistics when the national study is revised.")
