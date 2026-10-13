# W3 — Deliverables from the HMS results and the Block 04 report (started 2026-10-06)

Live iteration. Inputs: the HMS project `..\..\Hydrology\HEC_HMS_Block_04` (Basin 2 without reservoirs, Basin 3 with the
eight reservoirs of the channel scheme, **Basin 4 = Basin 1's dam catchments + the nine reservoirs incl. Shafan 08**, 13
depth-area analyses each) and the reservoir curves in `..\reservoirs`. Every number below comes from a script in
`scripts/` (run order = number prefix); every workbook was recalculated in Excel (`scripts/xl_recalc.py`) so its formulas
carry cached values, and its charts were checked as PNG (`scripts/xl_charts_png.py`).

**Which basin feeds what:** the dam deliverables and the report's dam chapters use **Basin 4** (nine dams, the inflow of
Hawasinah UP and Shafan 08 routed through the reservoirs upstream of them); the channel deliverables (element tables,
shapefiles, KMZ, outfalls) use **Basin 3 / Basin 2** (eight dams, Shafan 08 as a plain junction, as the channel design
requires). The two agree at every dam except the two with upstream reservoirs.

| Folder | Deliverable | State |
|---|---|---|
| `dams/eav` | `Block04_Dams_Elevation_Area_Volume.xlsx`: Dams sheet (nine dams, dams-sheet values + curve values by formula + HMS PMP level/outflow) and one sheet per dam (0.5 m steps, areas from the 10 m DEM, conic volumes by formula, DEM-integrated volume as check, elevation-volume and elevation-area charts with FSL and crest lines) | done (R1: nine dams, Basin 4) |
| `dams/hydrographs` | `Block04_Dam_Hydrographs.xlsx` (Majlas layout: sheet per dam, Time (hrs) + Inflow/Outflow per RP, statistics block by formula, chart of all inflows with peak labels, 13 inflow-vs-outflow charts; summary sheets Peak inflow/outflow, volumes, attenuation, peak level, head over FSL); `dams_reservoirs.xlsx` (Block 6 layout); `data/hydrographs_5min_B4.csv` + `dam_summary_B4.csv` (B3 files kept) | done (R1: nine dams, Basin 4) |
| `elements/xlsx` | `peak_flow_volume_all_elements_B3.xlsx` and `_B2.xlsx` (Block 6 layout: Peak Flow m3s, Volume Mm3, element + type) + long CSVs | done |
| `elements/shp` | `B3/`, `B2/`: Subbasins, Reaches, Points shapefiles with HMS parameters and Q<rp>, V<rp> for the 13 return periods; `Block04_elements_B3.gpkg`/`_B2.gpkg` (same layers, full field names) | done |
| `elements/kmz` | `B3/`, `B2/`: 28 KMZ each as Block 6 — `All_Layers`, `Basins_Reach` (polygons and reaches open the full Q/V table), `Q_<rp>` and `V_<rp>` point files labelled with the value | done |
| `sediment/catchments` | `Dam_catchments9.shp/.gpkg` (`scripts/20_dam_catchments9.py`): one polygon per dam (nine, Shafan 08 included) = union of the Basin 1 subbasins upstream of the dam junction, with area, weighted CN, longest flow path, 10–85 slope, basin slope, Kirpich Tc, lag, relief; the eight-dam `Dam_catchments.gpkg` of R0 is kept | done (R1) |
| `sediment/rusle` | the RUSLE pipeline (github.com/mojikone/RUSLE) on the nine catchments: `Data/` downloads (DEM GLO-30, SoilGrids, SM2RAIN, Landsat 8 **mosaic of three scenes**, WorldCover), `Output/Rasters` (R, K, LS, C, P = 1, SoilLoss, 250 m), `Output/CSV/RUSLE_Results.csv` | done |
| `sediment/B4_DAM_RUSLE.xlsx`, `sediment_yield.csv` | Block 6 layout (`scripts/21_sediment_yield9.py`): factors, soil loss, relief ratio, CN, Williams (1977) SDR **with the floor 0.2**, density 1.5 t/m³, yield **with the floor 90 m³/km²/yr**, sediment per year and per 50/100 years — the engineer's rules of 2026-10-06 | done (R1) |
| `sediment/Block04_Reservoir_Sedimentation.xlsx` | USBR 2.6 reservoir volume reduction, 50 and 100 years, nine dams (`scripts/11_reservoir_sedimentation.py`): 2.6.1–2.6.2 by formula, 2.6.3 (Empirical Area-Reduction) by the Majlas engine; revised curves per dam (sheets, `revised_eav/*.csv`, `figures/eav_revised_<dam>.png` in the Block 6 dual-axis form, `figures/storage_loss_summary.png`, `figures/design_curves.png`) | done (R1) |
| `climate` | R1 record **per dam** from the 9 km ECMWF reanalysis through the Open-Meteo archive (`scripts/17_fetch_openmeteo.py` → `data_om/<dam>/`, six distinct cells), MRMWR rain gauges within 15 km from the 2331 project data (`scripts/18_gauges.py` → `gauges/`, read-only source), `scripts/22_climate9.py` → `climate9_summary.json`, `figures/windrose_<dam>.png`, `monthly_all.png`, `annual_rain_all.png`, `Block04_Climate.xlsx` (Read me, Summary, sheet per dam, Gauges). The R0 NASA POWER record (`data/`, `climate_summary.json`, `12_climate.py`) is superseded | done (R1) |
| `maps` | **R2 figures** (`scripts/26_maps_qgis_r2.py`, standalone PyQGIS) in `png_r2/`: the engineer's channel symbology wherever the categories matter and one colour elsewhere, dam names in black with a thin white halo, scale bar on the frame line with a segment chosen from the map scale, key table inside the frame, flood-alignment and land-use maps on the Google image with a dimmed hillshade, the HEC-HMS figure = his screenshot georeferenced by silhouette matching (`scripts/25_georef_hms_shot.py` → `maps/data/hms_model_georef.tif`, check image beside it), the zoomed Q200 map on the dams and every element downstream **on an A3 page** (the template scaled by 420/297, the scale bar re-seated on the frame line), the sediment map coloured by the sediment delivered in 50 years (Mcm); the unlabelled 'all other values' category of the engineer's channel style is dropped from the legends; `Block04_R2_maps.qgz`. R1 figures (`scripts/13_maps_prep.py` nine-dam data → `maps/data`; `scripts/24_maps_qgis_r1.py`) in `png_r1/`, superseded: M01 dams and catchments, M02 channel category, M03 alignments on the 200-year flood depth, M04 channel and dyke routes, M05 roads and utilities, M06 land use, M07 RUSLE sheet (A3: R, K, LS, C, soil loss, yield), M08 HEC-HMS model, M09 sediment yield and storage lost, M10/M11 Q200 at the junctions (whole block / coastal plain, as Block 6 Figure 12 a/b); the engineer's symbology from `styles/*.qml` (`scripts/15_export_user_styles.py` from a copy of his project); `Block04_R1_maps.qgz`. The R0 set (`png/`, `14_maps_qgis.py`, `Block04_W3_maps.qgz`) is superseded | done (R1) |
| `report` | **`R3/Block04_Report_R3.docx` + PDF, live** (R3, 2026-10-06 night = the engineer's four remarks on R2: the storm temporal patterns of the model after the design-rainfall table (`C10`, the five percent graphs read from the project DSS by `charts_b4.py`, saved in `dams/data/storm_patterns.json`), the channel and dyke names along the lines on the routes map, the crest outline thinned under the FSL polygon, one Ibri-form climograph (`C08`: temperature lines with values, rainfall bars, Block average of the nine sites) and one annual-rainfall bar chart (`C09`); maps in `maps/png_r3`, copied from R2 with M01 and M04 re-exported through `MAPS_OUT=png_r3`). **R2, R1 and R0 are superseded.** R2 was (R2 = the engineer's remarks on R1 of 2026-10-06 evening: channel category map dropped, routes map carries the colours; dam names on the maps; HEC-HMS screenshot georeferenced in the layout; zoomed Q200 map on the dams and the plain; sediment map in Mcm over 50 years; EAV charts with FSL and crest annotated on their lines; one-chart climograph `C08` and one-chart annual rainfall `C09` per record). **R1 (64 pages) and R0 are superseded.** R1 was Built from Python (`build.py --pdf`, two passes so the table/figure numbers in the text match the captions, `_refs.json`) on the Block 6 report template re-styled to the Majlas report (`make_template.py`, `lib/doc.py`: Aptos, justified 1.5, blue capital headings with styled numbers, grey italic captions "Table N – text", 1F5C99 table headers, borders all round); every number from `data_facts.py`; charts `charts_b4.py` (C01 200-yr grid with Qp/V, C02 inflows 0–36 h, C03 100/200/500 attenuation, C05 EAV dual axis with FSL/crest on their lines, C06 outfall peaks and volumes, C07 sediment steps, C08 climograph, C09 annual rainfall, C10 storm patterns); sections `rpt_*.py` in the Block 6 order: executive summary, introduction, hydrology, channel alignments, channel condition and conflicts, rainfall-runoff simulation and dams (model, Q200 maps, dams' information, catchments, EAV curves, routing, peaks, volumes, levels, hydrographs, flood protection performance), sediment yield and reservoir sedimentation (Majlas text), climate at the dam sites, hydraulic design criteria, outfalls, conclusion, appendices A (inflow hydrographs) and B (revised reservoir curves). **R0 (53 pages, eight dams, POWER climate, internal matter) is superseded**; the engineer's 70 comments on it (`R0/Block04_Report_R0 - Copy.docx`) are all addressed in R1 | R1 for review |
| `channel naming` | the 73 Block 4 channels and dykes named `<GCA>-<CH or D><n>-<FP/SM/SS>` after the Block 6 convention and written into the `Name` field of `Hydrology\SHP\temp\Channels and Dykes 04102026.shp`; own README | done; 5 boundary-straddling features to confirm |

## Findings and decisions of this iteration

- **Basin 4** (`scripts/19_basin4_build.py --install`, HMS backup `..\..\Hydrology\Backup\19 HEC_HMS_Block_04.rar`, file backup
  `_backup_before_basin4_20261006_101217`): Basin 1 + nine reservoirs, 13 `DA <rp> B4` analyses. Undammed inflow peaks
  reproduce the dams-sheet QPMF (Hawasinah 02 17 809 m³/s …); with the upstream reservoirs routed, Hawasinah UP PMP 34 603
  (sheet 34 783) and Shafan 08 14 778 (sheet 15 764). Shafan 08 reservoir: bed 153, FSL 168 (2.94 km², 13.7 Mm³ conic vs
  sheet 15), crest 173 (`scripts/16_eav_shafan08.py`).
- **Report names (engineer, 2026-10-06):** Hawasinah EX is **Hawasinah UP**, Sakhin 08 is **Sakhin 08 (Mehmum)**; order
  Hawasinah 02, 11, UP; Shafan 02, 08; Sarami 03, 05; Sakhin 04, 08. HMS element names unchanged (`config.LABEL`).
- **Dam inflow = Basin 4 reservoir inflow** (the Basin 3 values differ only at Hawasinah UP, which receives 02 and 11 routed).
- **Reservoir curves**: conic volumes at FSL are 2–7 % below the dams-sheet capacities; the sheet capacities stay the
  dam team's reference.
- **Sediment yield with the engineer's floors** (SDR ≥ 0.2, yield ≥ 90 m³/km²/yr, P = 1, density 1.5 t/m³): 90–185
  m³/km²/yr (Williams SDR alone gives 0.07–0.13 and 40–100 m³/km²/yr). Soil loss 6–14 t/ha/yr.
- **Reservoir volume reduction** (USBR 2.6, operation 3, TE 100 %, deposited density 1 290–1 330 kg/m³): storage lost at
  FSL after 50 years 1.9–8.3 % for seven dams, **Hawasinah 02 37 % (74 % after 100 years)**, **Shafan 08 20 % (39 %)**. Bed
  at the dam rises 0–8 m in 50 years. Hawasinah UP and Shafan 08 are assessed on their whole catchment without credit for
  the upstream reservoirs' trapping (upper bound, footnoted in the report).
- **Climate per dam** (9 km reanalysis 2001–2023, hourly wind 2015–2024): mean 28.4–29.1 °C, 66 (Hawasinah UP) to 106
  mm/yr, calm 8–11 % of hours, land breeze SW/W prevailing at the foothill dams, sea breeze NE/ENE at Hawasinah UP and
  Sarami 05; warming 0.2–0.9 °C/decade. Nearest MRMWR gauges with ≥ 4 complete years: Y3 135, Z71 141, Z64 263 mm/yr
  (2015–2021). The single POWER cell of R0 (100 mm/yr, 2024 artefact) is superseded.
- **Channel file**: `Channels and Dykes 04102026.shp` holds Blocks 2, 4 and 6 (`Block` field); every map and length
  filters `Block = 4` (287 km: FP 57, SM 70, SS 97 km of channels; 63 km of dykes).
- **Storm patterns**: the five hypothetical-storm patterns (2-yr, 5-yr, 10–1000-yr, 2000–10000-yr, PMP) are percent graphs in the project DSS (`//FM <name>/PERCENT GRAPH///TABLE/`, 145 points at 10 min); all centred at hour 12, the 2-yr pattern drops 37 % of its depth in the peak 10 minutes, the PMP 4.6 %. The Block 6 report's figure captioned 'Rainfall Distribution Patterns' is in fact the ARF curve.
- **Maps mechanics (R2)**: the scale bar is seated from the map frame (frame top − 7.75 mm on A4, − 7.8 mm on A3, measured on the export so that the frame line runs through the middle of the bar) and set in metres with the segment chosen from the map scale; the 'Type' field of the channel file is empty for Block 4, so channel/dyke rules use `CHtt`; QGIS manual tables overflow their frame unless the column widths sum below it; a screenshot of the HMS map window is georeferenced with one scale (its full east-west extent) and a vertical offset found by matching the shaded silhouette to the terrain raster's valid-data edge (misfit 0.46 km on 86 m pixels).
- **Report mechanics**: the template's 'List Bullet' style is absent — `add_paragraph(style=...)` on a missing style
  leaves an orphan empty paragraph (the "blank line between bullets" of R0); captions are keyed and the build runs twice
  so the text's Table/Figure numbers never drift; equation symbols render subscripts from `q_s`.
- **Charts**: one shared style (`scripts/xlstyle.py` for native Excel charts, `scripts/figstyle.py` for matplotlib): Arial,
  hairline #EDEDED gridlines, light axes, no borders — the engineer's instruction of 2026-10-06.

## Conventions

**Clean-room gate (global rule 14):** `report/build.py --pdf` scans the rendered PDF with `report/check_clean.py` against
`report/forbidden_terms.txt` (+ the built-in list; `allowed_terms.txt` whitelists SM2RAIN, Open-Meteo and the W1/WT symbols) and
renames the outputs `*_FAILED-CLEAN-CHECK` on any hit. R0 fails it with 73 hits, R3 passes. Add every new internal name to the list.

Every deliverable listed above is mirrored into the latest snapshot of `Block 4\Deliverables` (`<n> Deliverables <ddmmyyyy>`, Oman
date) by `..\scripts\sync_deliverables.py` (manifest-driven; `--check` is the staleness test, `--new-version` starts the next
snapshot), and `..\scriptsuild_deliverables_qgis.py` builds the snapshot's root QGIS project from the map project written by
`scripts/26_maps_qgis_r2.py` (run it for ALL keys first: the script rewrites `maps/Block04_R2_maps.qgz` with only the layouts of
that run). A new output folder in W3 must be added to the sync's SPEC list, a new layer to the builder's lists. The map figures
read nothing outside the project folders: `13_maps_prep.py` clips the 820 MB server depth raster to `maps/data/depth_200yr_plain.tif` (109 MB).

Excel COM is used to recalculate (openpyxl writes no cached values) and to hide helper legend entries; `xl_charts_png.py`
exports native charts through the clipboard (Chart.Export fails under automation). Shapefile field names are ≤ 10
characters (Q2 … Q10000, QPMP; V2 …); the GeoPackages carry the same layers. Maps: `python-qgis-ltr.bat
scripts/24_maps_qgis_r1.py [keys]`; the legend is anchored at its lower-left corner inside the map frame, the scale bar
is set in metres (5 000 m segments) and the key table sized from its own content. Never load anything into the engineer's
open QGIS instance; the Block 6 QGIS project is `..\..\..\..\HMS\B6\60 HMS_Block_6_Mod1\Hydrology Data\QGIS\Block 6 HMS Ais 2D.qgz`.
