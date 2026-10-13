# W7 — the Shafan 08 dam in the channel hydrology, SewerGEMS revision R9, report R4

**Live document (W7, started 2026-10-12 06:30).** The engineer's decision after the W6 assessment ("this is big change"): the
channel hydrology includes the Shafan 08 dam, with its full catchment, and everything downstream is rebuilt end to end in this
iteration: HMS → design flows → SewerGEMS (all eight scenarios) → results, profiles, 200-yr plan-profile set → QGIS → report R4 →
WhatsApp. W6 stays as the record of the design without the dam (R8 live there for 200 yr). His four answers before the start:
fix the catchment gap; the reservoir starts empty (153 m, as in the dam deliverables); all eight scenarios designed; the report's
Shafan-line flows revised after W7 (then widened to: report R4 inside W7, only the 200-yr flow and the channel sizes for the
channels).

## State

| Step | Script / job | Result |
|---|---|---|
| 60 Basin 6 of record | `scripts/60_hms_basin6_w7.py` | done 06:34: dam catchment fixed, 13 analyses × 362 points, compute 13 × 40–150 s (`hms/60_hms_basin6_w7.log`, `hms/60_basin6_fix_parameters.json`) |
| 61 Basin 6 results | `scripts/61_extract_b6.py` | done 06:55: 362 elements × 13 return periods, `results/basin6_peak_flow_volume_long.csv` + `.xlsx` (+ copies in `hms/`); against Basin 3 only the 22 elements of the Shafan line and the three fixed subbasins moved (`hms/61_basin6_vs_basin3.csv`) |
| 62 design flows | `scripts/62_update_flows.py` | done 06:58: five rows of the flow file (SHA-J47, J48, J49, J51, O5) and four design points (SHACH1-1, -8, -9, -11) refreshed, 13 return periods each; everything else keeps his values (`inputs/62_flow_changes.csv`, 234 values) |
| 63 the R9 job | `scripts/63_make_r9_job.py` → `sewergems/jobs/075_b4_flows_R9_all.ps1` | done 09:28 (06:58 → 09:28): 32 known flows checked and rewritten, all eight scenarios designed (sizes changed in pass 1: 11 / 47 / 56 / 56 / 56 / 56 / 12 / 57, none in pass 2), R9 delivered with the eight result files; run folder `run_20261012_1758`. **Constraints in R9: min slope 0.001, max 0.03** (inherited from R5 through R6–R8; the 0.002 floor lives only in R4) — his decision pending: keep, or R10 at 0.002 |
| 64/65 elements | `scripts/64_build_elements_xlsx_b6.py`, `65_build_shapefiles_b6.py` (W3's 05/06 on Basin 6; `model/Basin_6.basin` + `.sqlite` snapshotted) | done 06:59: `elements/xlsx/peak_flow_volume_all_elements_B6.xlsx` (362 elements), `elements/shp/B6/` Subbasins 110 / Reaches 115 / Points 138 (13 outfalls, 9 reservoirs), `Block04_elements_B6.gpkg` |
| 67 outfalls | `scripts/67_compare_b2_b6.py` | done 06:59: `results/outfalls_B2_vs_B6.csv` (SHA-O5 200 yr 2428 without the dams → 938 with them, −61 %; was 1404 with eight dams), `dams_inflow_vs_outflow_B6.csv` |
| 66 maps | `scripts/66_maps_qgis_r4.py` (python-qgis-ltr) | done 06:59: `maps/png_r4/` M08 (the model drawn from the Basin 6 layers, nine reservoirs, no screenshot), M10, M11 (Q200 at the junctions, Basin 6); the others copied from W3 png_r3; `maps/Block04_R4_maps.qgz` |
| downstream of R9 | `scripts/50_rebuild_after_run.py --run run_20261012_1758 --sqlite <R9 sqlite> --set-tag R9` | done 10:02 in 3 min: exports, sizes, review tables, profile DXFs of 37 channels × 8 scenarios, buffers, 277 sheets, set `PDF/Set/..._200yr_R9.pdf` (394 MB), both gates PASSED |
| QGIS | `scripts/51_qgis_sewergems_200yr_R4.py --new run_20261012_1758 --old run_20261012_1608 --rev R9`, `69_qgis_w7_groups.py`, `69b_qgis_w7_works.py` (both through the MCP) | done 10:03/10:12: `gis/sewergems_200yr_R9.gpkg`; groups "W7 SewerGEMS 200 yr R9", "W7 check R8 to R9 (temporary)" (12 conduits resized, all SHA-CH1-FP; no invert or slope moved) and "W7 culverts, dykes, widths (R9 200 yr)" in his project |
| report R4 | `report/build.py --pdf` (`data_facts.SG_RUN = run_20261012_1758`) | rehearsal 07:00 on R8; the R4 build with the Block 6 layout and the three new sections 10:20 (see below) |
| 70 Tier A figures | `scripts/70_tierA_figures.py` | `report/img/C11_width_hist, C12_lengths_by_class, C13_flow_vs_width, C14_arf_curve, F10_process, F11/F12 sections`; `report/data/size_inventory.csv, reach_table.csv, drawings.csv, outfalls.csv` |
| 71 culverts | `scripts/71_culverts.py` | `culverts/`: 31 crossings (Batinah Highway 21, Coastal Road 10, Expressway none), 17 with a structure on file within 150 m, proposed cells 4.0 × 2.0 / 2.5 m, 868 cells, 19.4 mOMR |
| 72 dykes | `scripts/72_dykes.py` | `dykes/`: 36 dykes, 62.5 km, heights 1.6–4.5 m, 1.30 Mm³ fill, 8.45 mOMR |
| 73 volumes | `scripts/73_channel_volumes.py` (his Channel Terrain tool as a module, 2 m cells on the 5 m DEM) | `volumes/`: 37 channels, 221.3 km, cut 18.55 Mm³, fill 5.15 Mm³, clearing 18.4 km², riprap 2.0 Mm², 73.0 mOMR; land take by cadastre class |
| 66 maps (2) | `scripts/66_maps_qgis_r4.py` M12–M20 | width, depth, reach labels, outfalls, plain catchments, CN grid, design flow, culverts, dykes |

## Step 60: Basin 6 with the dam's full catchment (06:34)

Basin 6 (W6 step 52) was Basin 3 plus the Basin 4 reservoir below the junction "Shafan 08 site", SHA-R18 ending at the site
(3094 m). Its dam catchment was 304.1 km² against 314.1 in Basin 4: the Basin 4 polygon S23 (31.037 km²) was SHA-S23 (20.25 of
its 20.95 km²) + 9.66 km² of SHA-S44 (which drained to SHA-J42, below the dam) + 1.12 km² of SHA-S46 (to SHA-J45). The fix, by the
polygons: SHA-S23 := S23 of Basin 4 (31.037 km², CN 86.2, Ia 8.11, lag 97.5 min, its statistics and flow path), draining straight
to the site as S23 drains to the dam; SHA-S44 := SHA-S44 − S23 (2.747 km², CN 86.7, Ia 7.77, lag 27.7 min, was 58.4); SHA-S46 :=
SHA-S46 − S23 (16.528 km², CN 86.3, Ia 8.07, lag 62.4 min, was 61.6: the convention of decision 6 reproduces the Basin 3 lag).
0.705 km² of the old SHA-S23 outside S23 is left unassigned, as in Basin 4. `Basin_6.sqlite` follows (polygons, centroids, flow
paths, statistics, the S23 outlet, the Shafan 08 reservoir point). Project: Basin 6 description made live, the eight 12-point
analyses of W6 replaced by 13 "DA <rp> B6" analyses with all 362 points of Basin 3, old DSS deleted, headless compute
(`HEC-HMS.cmd -script`, 40–50 s per analysis up to 500 yr, 150 s from 1000 yr). Backup `_backup_before_w7_20261012_063355`.

## The model's flows (probe 074b, 06:40)

The engineer's model holds the design flows as **known flows** in eight System Flows alternatives (2035 … 2042, one per scenario,
field `SystemFlows_KnownFlow` on the manholes, 72–73 nodes with a value), **stored in ft³/s**: SHACH1-1 at 2 yr reads 1059.405 =
29.999 m³/s × 35.3147, and every scenario checked (2, 25, 100, 200, 500 yr) matches the W6 final layer to the third decimal. The
typed manhole input has no flow property; the field manager's `IEditField.SetValue` writes it. The R9 job checks every old value
before replacing it and reads every new one back.

## Open

- The ten fix points withdrawn in W6 stay withdrawn; the fixed-raise rule of W6 holds; the plan outlines use the W6 definition.
- The hydrology report's dam sections (Basin 4) are unchanged in R4; the channel flows, the outfalls, the Q200 maps and the new
  channel-section table come from Basin 6 and R9.

## Steps 61 to 67 (06:55 to 06:59)

- **Basin 6 against Basin 3** (`hms/61_basin6_vs_basin3.csv`): 200 yr SHA-J42 215 → 73 m³/s, SHA-J45 1113 → 278, **SHA-J47 1641 → 917
  (−44 %)**, J48 1661 → 956, J49 1669 → 971, J51 1671 → 996 (−40 %), the outfall SHA-O5 1404 → 938; the dam site receives 1018
  m³/s at 200 yr and the reservoir passes 72 m³/s (late, as the 72 of the dam deliverables); SHA-J20, the uncontrolled tributary 2.6 km above the dam, reads 856 (was 1009 with SHA-S23 draining into it). Nothing off the Shafan line moved (the fix of step 60 is local).
- **The design flows**: only the four SHA-CH1-FP points fed by the Shafan line change (SHACH1-1 1641.2 → 916.7, -8 1660.8 → 956.5,
  -9 1668.5 → 971.1, -11 1670.6 → 996.0 m³/s at 200 yr). His flow file is read only; the W7 copy carries the five refreshed rows;
  the volumes of every other row differ from the new export by 0.001 Mm³ of rounding and were left as his.
- **The elements and the outfalls** are the W3 deliverables rebuilt on Basin 6 (the scripts of W3 copied, the basin list set to 6).
- **The maps**: the HEC-HMS figure is now drawn from the element layers (subbasins, reaches, junctions, the nine reservoirs as
  triangles) instead of the engineer's georeferenced screenshot of the model without Shafan 08.

## Step 68: the drawn reach SHA-R18 (engineer, 18:10, on the Q200 map)

His reading of the map was right: the blue line running north-east from the 856 junction was Basin 3's line of SHA-R18 to
SHA-J45, left in the GIS tables when step 52 re-pointed the reach to the dam site in the model; it carried nothing. And SHA-J20's
canvas point stood 1.2 km east of the end of the SHA-R1 line. Display only, the hydrology stands: SHA-J20 moved to the end of
SHA-R1 (where the dam deliverables' J18 is), SHA-R18 drawn along the wadi line of the dam deliverables from there to the site
(3.5 km; the modelled length stays 3094 m, the dam deliverables route J18 into the dam with no reach at all); Basin_6.basin and
.sqlite, the model/ snapshots, the B6 shapefiles and the three maps rebuilt (`scripts/68_fix_r18_drawing.py`).

## The R9 sizes against R8 (200 yr) and the other scenarios

Only SHA-CH1-FP changed at 200 yr: 12 conduits resized (SHACH1-C1 … C12), e.g. C1 278 → 163 m, C11 364.5 → 226 m, as the W6 assessment
foresaw; no invert or slope moved. The other seven scenarios were redesigned for the first time since R3 under the R5 constraints
(min slope 0.001, max 0.03), so their sizes changed on many channels (47–57 conduits per scenario); they are in the review tables of
`sewergems/results/run_20261012_1758/summary.md`.

## Tier A, B and C of the report (engineer, 2026-10-12 ~19:00 Oman time, after the Block 6 comparison)

The Block 6 channel design report (server, `.../Block 6/Report/.../Channel_Design_Block6_Final.docx`, 13 tables, 29 figures) and its
QGIS projects (`.../Block 6/QGIS Channel Block 6/*.qgz`, 10 layouts: labels, Q200, constraint, depth, width, design labels,
alignments with flood depth, outfalls, culverts, dykes) were compared with R3/R4. Implemented in R4:
- **Tier A** (figures and tables Block 6 has): the design-process flowchart (F10), the project's typical sections in fill and cut
  (F11/F12, the images of the Block 6 report, "it is typical"), the width map to scale (M12), the depth map (M13), the length-weighted
  width histogram and the size inventory (C11, table), the lengths-by-class chart (C12), the per-reach appendix table (212 rows),
  the reach-labels map (M14), the outfalls map and table (M15, invert against MHHW 0.70), the plain catchments without a dam (M16,
  78 catchments, 816 km²), Manning / sizing-rule / bank-height equations in Word form, the CN grid map (M17) and the ARF curve (C14).
- **Tier B** (work Block 04 had not done; done now at feasibility level, his instructions): **culverts** at every crossing of the
  Batinah Highway (21) and the Coastal Road (10) — the existing inventory `Culverts_2_4.shp` (1 662 barrels) within 150 m, photos not
  on file (blank cells); proposed box cells 4.0 m wide × 2.0 m (2.5 m channels) or 2.5 m (3 m channels) per OHDS 2017 Table 12.5.3.1,
  cells = ceil(bed width / 4), headwater by the HDS-5 inlet/outlet equations of his GitHub tool (HW ≤ 1.2 D, all pass without extra
  cells), cost by the Block 6 build-up (`B6 CH D CUL COST.xlsx`, concrete per m calibrated on its 59 structures: N((B+0.25)(D+0.6)−BD)+0.8,
  rebar 0.12 t/m³), crossing length = road corridor 45 / 32 m (assumption); **dykes** — 200-yr depth of the plain without the scheme
  in a 25 m band, H = mean wet depth + 0.5 m + 0.6 m, rounded up to 0.1, floor 1.0; quantities by the typical fill section
  (footprint 4 + 3H + 3, 0.4 m strip, riprap 0.525 + gravel 0.2 on 1.803H), the Block 6 rates; **quantities and cost** — his Channel
  Terrain tool (`C:/Users/mojtaba/Documents/Channel Terrain/W6/scripts/channel_terrain.py`, imported, fields START_NODE/STOP_NOD2,
  2 m cells, the 5 m DEM `Hydrology/Terrain/NSA_Batinah_5m_Block_04.tif`), cut/fill = DEM − designed surface, riprap = the two side
  slopes × 0.3 m as priced, clearing = footprint, rates 2.1 / 4 / 13.2 / 0.3 OMR; land take = corridor (span + 15.5 m) ∩ cadastre
  by class (not priced). Totals: channels 73.0, dykes 8.45, culverts 19.4 → **100.8 mOMR**.
- **Tier C** (mine): the design-flow map along the channels (M18), flow against width by class (C13), the drawing-set list (Appendix D),
  the velocity paragraph (reaches above 3 m/s counted), the cost-by-catchment chart (C15).
- The cost sheet "my colleague gave me" did not arrive as an attachment; the Block 6 cost workbook on the server was used and he was told.

## Issued 10:17 (report) and 10:19 (set), both to his WhatsApp

- `report/R4/Block04_Report_R4.pdf`: 96 pages, 30 tables, 40 figures, clean-room gate PASSED (the issued drawing numbers of Appendix D
  whitelisted in `report/allowed_terms.txt` as `\b2224-PD-HY-PP-B4(-\d{3})?\b`, the same pattern as the sheets' gate). Sent 10:19.
- `sewergems/sheets/scripts/PDF/Set/2224-PD-HY-PP-B4_Plan_and_Profile_Drawings_200yr_R9.pdf`: 277 sheets, 394 MB. Sent 10:17.
- Deliverables mirror: W7 added as group 15 (and its elements and maps under 04 and 07); a colon in a folder name broke the first
  sync (WinError 123), fixed; the 46 HMS files rewritten by the headless saves were not seen as changed by the sync and were forced
  by deleting their copies; the check is back at its 14 known rows.
- **Engineer, 11:20, review of R4 (seven comments)**: (1) intermediate catchments = no dam anywhere in the upstream network (44 subbasins,
  258 km²; the first map had coloured the subbasins below the dams); (2) no flow labels on reaches without flow (design-flow map);
  (3) reach labels smaller and all placed; (4) the outfalls figure as in the Block 6 report: I (designed invert), Fix (existing terrain
  at the point, the EG of the final layer), Δ, the invert in red where below the terrain (`gis/outfalls_levels.gpkg`); (5) a dash
  instead of "None on file" in the existing-structures table; (6) culvert labels with leader lines, no overlap; (7) the dyke-height
  method paragraph removed from the report as internal (it stays here: mean wet depth in a 25 m band + 0.5 m + 0.6 m freeboard,
  rounded up to 0.1 m, floor 1.0 m). Maps M14/M15/M16/M18/M19 re-rendered, report rebuilt and re-sent.
- **Engineer, 11:05**: the third dashboard chart by global catchment like the other two (not by existing structure type as in Block 6); rebuilt and re-sent.
- **Engineer, 10:45**: the costs dashboard of the Block 6 report (its Appendix 1: three bar charts by catchment and by existing
  structure over the total by type, then every item) added as Appendix E (`scripts/74_cost_dashboard.py` → `report/img/D1_dashboard.png`,
  `D2_dashboard_items.png`, two landscape pages); the channel terrain rasters (37 GeoTIFFs at 2 m + VRT + quantities,
  `volumes/Block04_channel_terrain_R9_2m.zip`) sent to his WhatsApp.
- **Engineer, 10:35**: R9 with min slope 0.001 accepted (no R10). SHA-CH19-SS, the channel without a modelled inflow, keeps the 10 m
  minimum section and its culvert is fitted to it (3 cells of 4.0 × 2.0 m); the culvert table now prints a dash for its flow and
  headwater and the text says so. Report rebuilt and re-sent.

## Report R4 (the W3 build copied into `report/`, revision R4)

- `common.py`, `data_facts.py`, `charts_b4.py` read the dams, sediment and climate data from W3 (unchanged) and the channel data from
  W7: `elements(basin="6")`, `outfalls()` = `results/outfalls_B2_vs_B6.csv`, `outfall_volumes()` Basin 2 against Basin 6, the maps
  from `maps/png_r4`; the C06 outfall charts regenerated.
- New in the text: the rainfall-runoff section says all nine dams are routed in the model; the hydraulic design section ends with
  **"Channel sections for the 200-year flow"**, a table of the 37 channels (class, length, the 200-year design flow of the largest
  reach, the bed width of the first and last reach, the depth) from the class-resolved conduit export of the SewerGEMS run named
  in `data_facts.SG_RUN`; the executive summary and the conclusion carry the same figures. The engineer's instruction: only the
  200-year flow and the channel sizes for the channels; the dam tables keep their thirteen return periods.
