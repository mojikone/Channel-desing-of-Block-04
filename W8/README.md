# W8 — report R5, the stormwater channels report R0, the two drawing sets with key plans, KMZ, the submission folder

> **Two works share this folder.** A parallel session built here, 2026-10-13 01:44–01:58 PDT, the dam characteristics table for Blocks 2, 4
> and 6 (`data/dams_blocks_2_4_6.csv`, `scripts/build_dams_doc.js`, `scripts/build_dams_xlsx.py`, `output/Dams_Blocks_2_4_6.docx/.pdf/.xlsx`).
> Its README was overwritten by this session at 03:41 PDT; what is known of it is reconstructed below from its files and the memory note.
> This session's work (the reports and the submission package) lives in `report/`, `scripts/`, `gis/`, `culverts/`, `maps/`, `kmz/`, `sewergems/`.

## The dam characteristics table for Blocks 2, 4 and 6 (parallel session, 2026-10-13 01:44–01:58)

- From the memory note of that session: **W8 (2026-10-13, `Claude Block 04\W8`, own README): the Block 6-style "characteristics of the proposed dams" table (type, height above wadi, crest length, FSL, capacity) for Blocks 2, 4 and 6 as one Word document** (`W8/output/Dams_Blocks_2_4_6.docx`, docx-js build, PDF through Word COM). **Where the dam-team data lives on W:\2224 …\06-WORKING:** `07-Structures\03-Dam Design\01-Block 6 Dams\Block 6 Dams Details.xlsx` (= Block 6 masterplan Table 30/34), `02-Block 4 Dams\Block 4 Dams Details.xlsx` + `Chracteristics\Block 4 Dams.xlsx` (**Block 4 dam types**: Hawasinah 02/UP, Shafan 08, Sarami 03, Sakhin 04 GFRD; Hawasinah 11 and Shafan 02 GFRD+RCC; Sarami 05 RCC; Sakhin 08 N/A) + `Chracteristics\*.dxf` axis ground profiles (x station, y elevation, 2 m DEM; the dam team's height = crest − lowest profile point, crest length = axis length — verified on Block 6), `03-Block 2 Dams`/`Bidah 03`/`Faydh 01` EMPTY; `Ad-hoc Reports\03-Tentative Costs of Dams` (all 16 dams, rounded H/L, cost); `04-Hydraulic\00 Data\SHP\1st_2nd_Priority_DAM_AXIS_ART_REN 08.01.2025` (axes + reservoir polygons of every priority dam incl. Bidah 03 1,335 m and Faydh 01 919 m); `07-Structures\02-Potential Dam Sites\02-Feasibility\02-Ranking Matrix\Dam site Characteristics.xlsx` (Dec 2023 feasibility: FSL/crest, Hmax, Lc of every candidate); `13-Study and Design\01-FS and PD\14-Blocks\02-Block 4\Report\Block 4 Masterplan Report.docx` (draft, dam chapter still the Block 6 content); 2 m DEM of the whole Batinah `13-Study and Design\01-FS and PD\00-General\01-Topography\NSA_Batinah_2m.tif`. Block 2: Bidah 03 crest 99 / FSL 94 / 15 m / 2.2 MCM, Faydh 01 crest 224 / FSL 219 / 49 m / 7.4 MCM (derived on the 2 m DEM; no dam design exists; both priority 2). Type codes: FSHD faced symmetrical hardfill, GFRD geomembrane-faced rockfill, RCC gravity.
- Files: `data/dams_blocks_2_4_6.csv` (block, dam, label, type, height_m, crest_length_m, fsl_m, capacity_mcm, note with the derivation), `scripts/build_dams_doc.js` (docx-js build of the Block 6 style table, one Word document, PDF through Word), `scripts/build_dams_xlsx.py` (one sheet per block), `output/Dams_Blocks_2_4_6.docx`, `.pdf`, `.xlsx`.

# The reports and the submission package (this session)

**Live document (W8, 2026-10-13, 09:00 to ~16:00 Oman).** His instruction after R4: continue in W8 and "update all the relevant files so a
new chat will know the full story and where we left". Everything below is DONE unless marked open.

| Deliverable | Where | State |
|---|---|---|
| Report R5 (channels feasibility and hydrological report) | `report/R5/Block04_Report_R5.docx` + `.pdf` (107 pages) | his 17 comments and 2 tracked changes on R4 applied; the reach map as four catchment panels (his comment of 13:00); cost chart with the land; gate PASSED |
| Stormwater channels report R0 | `report/SW_R0/Block04_Stormwater_Channels_R0.docx` + `.pdf` (66 pages) | the Block 6 "Hydraulic Design of Stormwater Channels" structure, the 32 SM/SS channels and 16 SM/SS dykes only, FP channels grey on the maps; gate PASSED |
| Plan-profile set, flood protection channels | `sewergems/sheets/scripts/PDF/Set/2224-PD-HY-PP-B4_Plan_and_Profile_Drawings_200yr_R9.pdf` (288 pages, 431 MB) | a key plan after each catchment divider, the table header below the document line, the sheets regenerated without text overlaps; both gates PASSED |
| Plan-profile set, stormwater channels | `.../2224-PD-HY-PP-B4_Stormwater_Channels_Plan_and_Profile_Drawings_200yr_R9.pdf` (224 pages, 349 MB) | the 32 SM/SS channels with the same drawing numbers as in the full set, the key plans with the FP channels dimmed; gate PASSED |
| KMZ | `kmz/Block04_{channels_dykes, extents, design_points, dams, culverts, all}.kmz` | channels and dykes in the agreed colours with name labels, bed and corridor, 227 design points, dam axes + FSL and crest reservoirs, 31 proposed and 346 existing culverts |
| Submission folder | `Block 4\Deliverables\2 Submission 13102026\` (5.6 GB, `scripts/90_submission.py`, log `submission_log.txt`) | 01 Reports, 02 Drawings (+ Civil 3D dwg, tables of drawings), 03 GIS (styled), 04 KMZ, 05 Tables (xlsx), 06 Maps, 07 Models (HEC-HMS with the Basin 6 results, SewerGEMS R9, channel terrain), 08 QGIS (`91_submission_qgis.py`: 76 layers, relative paths, a group per report map + design points, stations, extents, dams, utilities, land use, terrain) |

## How it was done (scripts, in order)

| Step | Script | What |
|---|---|---|
| R5 template | `report/make_template.py [--sw]` | the SUBMITTED Block 6 report as template (title and logos as issued); `--sw` writes `template/Block04_template_sw.docx` with the cover title "Hydraulic Design of Stormwater Channels" |
| R5 culverts | `scripts/71_culverts.py --radius 10` | clear height = full channel depth, existing culverts within 10 m, slope = channel slope; 868 cells, 19.5 mOMR |
| R5 maps | `scripts/66_maps_qgis_r5.py [keys]` → `maps/png_r5/` | M14 = four A3 panels `M14_reach_{HAW,SHA,SAR,SAK}` (names along the lines placed first, reach numbers at the reach midpoints with leaders where they fit); M21 global catchments; the data boxes computed from the layers. `MAPS_DIM_FP=1 MAPS_OUT=png_sw` renders the stormwater set (FP grey, FP reaches/outfalls/culverts/dykes left out) → `maps/png_sw/` |
| charts | `report/charts_b4.py c15` (`CHART_SUFFIX=_sw REPORT_ONLY=SM,SS` for the stormwater one), `scripts/75_sw_charts.py` (C11–C13 of the stormwater report), `scripts/74_cost_dashboard.py` (`DASH_SUFFIX=_sw REPORT_ONLY=SM,SS`) | |
| report builds | `report/build.py --pdf` (R5), `report/build_sw.py --pdf` (R0; sets REPORT_ONLY=SM,SS, MAPS_OUT, REFS_FILE, REPORT_TITLE, DASH/CHART_SUFFIX, APP_LETTERS) | `data_facts.only()` filters every per-channel table by the class suffix of the name when REPORT_ONLY is set; `rpt_sw.py` holds the stormwater-specific sections |
| stations | (inline, this session) → `gis/stations.gpkg` (`stations_500`, `stations_1000`, `dykes`) | points every 500 / 1000 m along the 37 channels and 36 dykes with label and tangent angle |
| key plans | `sewergems/sheets/scripts/make_catmaps.py [--dim-fp] [--png]` → `PDF/Set/_catmap_<CODE>[_sw].pdf` | PyQGIS, A1, satellite, the agreed symbology with names (13 pt), bed and corridor, ticks and station labels perpendicular (8.5 pt) every 500 m, or 1 000 m when more than 6 % of the 500 m labels collide, dam axes; vector PDF 8–10 MB each |
| sheets | `run_all.py`, `export_pdf.py`, `make_set.py --tag R9 [--only SM,SS --catmap-suffix _sw --kind "STORMWATER CHANNELS"]`, gates `W3/report/check_clean.py` + `check_clean_sheets.py` | W8 copies of W7's scripts with `Data/` and the tile cache `IMG/` copied in; seven overlap passes (below) |
| KMZ | `scripts/80_kmz.py` | plain KML (no library), WGS 84, colours from the QML, label placemarks at the line midpoints |
| submission | `scripts/90_submission.py`, `scripts/91_submission_qgis.py` (python-qgis-ltr) | copies with client-facing names; the HMS project without the result files of the superseded basins (B2–B5, 3 GB) |

## The overlap check of the drawing set (his comment: "ensure no text overlap")

The sheet PDFs carry their text as outlines, so the check is made on the DXF text entities with oriented boxes
(`scan_dxf_text2.py` in the session scratchpad; copy in `sewergems/sheets/scripts/PDF/_dxf_text_overlaps_oriented_W8*.csv`):
R9 (W7) had 184 overlapping pairs on 90 sheets. Fixed in the W8 copies of `make_sheet.py` / `make_keymap.py`:
the source axis title "Station (m)" dropped (it landed mid-sheet on the band values); values clamped inside the data area and a
centred value near the edge shifted inside it (Times New Roman measures 0.69 h per character, the estimate is 0.72 h); the 0 m
elevation label on the chart scale and never on the band heading; a profile annotation that lands on a placed one moves to a free
line (its second line follows, never onto the station strip; annotations always on the chart scale); plan station labels on a curve
move outward or are dropped, and never onto the scale bar or the north arrow; key-map station labels perpendicular beyond the frame
corner, flipped to the other corner at a bend or dropped, the sheet number in a tight column that steps aside or shrinks; a last
frame shorter than its label gets the end station only. The table-of-drawings header band moved below the document line (his
"small line overlapping the tables"). What remains in the scan are the two lines of one pipe label touching by 0.3–0.5 mm, which is
the normal line spacing of a two-line label.

## The comments on R4 and what was done (2026-10-13)

| # | his comment | done |
|---|---|---|
| 0, 1 | cover title and logos as the submitted Block 6 report; page numbers | template rebuilt from that file |
| 2 | document control page and list of abbreviations at the front (Ibri R7 format) | `rpt_front.document_control()` and `abbreviations()` (37 terms), before and after the contents |
| 73 | Manning in the criteria table as a Word equation | OMML inline in the cell (`omml.inline`) |
| 74 | minimum slope at the flat sea outfalls 0.0003 → 0.001 | criteria table |
| 77 | typical sections: fill = left half, cut = right half | images cropped (`img/F11`, `F12`) |
| 92 | "what about stormwater main channels?" | their flow and width range added to the paragraph |
| 93 | remove the "five short secondary channels without an inflow point" sentence | removed |
| 101 | reach-labels map messy → channels in the agreed colours with their names, reaches "C#" parallel; then (13:00) "names and reaches overlapping" | M14 = four catchment panels at 2–3× the scale, names first, reach numbers with leaders only where they fit, short titles |
| 108, 116 | culvert clear height = the full channel depth (2.5 / 3), the embankment above; the culvert slope = the channel slope | 71 re-run, table with a slope column |
| 109 | existing structures within 10 m, not 150 | 71 `--radius 10` |
| 110, 111, 113, 114 | never mention files, "on file", photographs, the detailed design, the no-inflow rule | texts rewritten, photograph column removed |
| 124 | land cost from Table 35 of the Block 6 master plan report, no "not priced / Ministry" | `data_facts.LAND_RATE_OMR_HA`, applied to the corridor take by class; channel cost = construction + land; totals, dashboard, summary and conclusion follow |
| tracked 1 | "With the above constraints not sorted out, the system will not be designed for cyclone-level protection" | challenges table |
| tracked 2 | "sized in the SewerGEMS hydraulic model" | sections paragraph |
| key plans (15:30) | "the stations are not legible, also the labels can be larger" | 8.5 pt station labels, 13 pt names, longer ticks, fixed legend box |
| (15:00) | "keep copy of the latest models, HMS, SewerGEMS, etc in the final deliverables" | 07 Models in the submission folder |

Also found and fixed on the way: Appendix C/A carried an empty "Depth / rise" column (195 "nan" cells in R5 — the export has no value), dropped;
the culvert map's data box still said "2.0 or 2.5 m high", now computed from the data; the GCA neighbour names lost their underscores.

## Open

- WhatsApp: the bridge reports "linked" again at 16:00 Oman; nothing sent from W8 yet (the sets are far above the 30 MiB file cap;
  the two report PDFs are 18 and 10 MB).
- The deliverables mirror `1 Deliverables 07102026` carries W8 as group 16 (`scripts/sync_deliverables.py`); the submission folder is the clean copy.
