# Claude Block 04 — everything Claude found, did and we decided (Block 04, Flood Protection Scheme North & South Batinah, MAFWWR, Renardet 2224 WS11)

**Live document. A new session starts here.** Last update 2026-10-13 (**W8 done (2026-10-13): report R5 (his 17 comments + 2 tracked changes, the reach map as four catchment panels), the stormwater channels report R0 (the 32 SM/SS channels, the Block 6 'Hydraulic Design of Stormwater Channels' structure), the two plan-profile sets with a key plan after each catchment divider and no text overlaps (288 and 224 pages), KMZ files, the clean submission folder `Block 4\Deliverables\2 Submission 13102026` (5.6 GB: reports, drawings, GIS with styles, KMZ, tables, maps, HEC-HMS + SewerGEMS + channel terrain models, a QGIS project with a group per report map); nothing sent on WhatsApp yet; also in W8, by a parallel session: the dam characteristics table for Blocks 2, 4 and 6 — `W8/README.md`**; 2026-10-12: **W7: the Shafan 08 dam with its full catchment in the channel hydrology (Basin 6, SHA-J47 200 yr 1641 → 917 m³/s), SewerGEMS R9 (all eight scenarios, 09:28; constraints min slope 0.001 / max 0.03 inherited from R5, his decision on a 0.002 rerun pending), the 200-yr set R9, the R9 groups in his QGIS, and report R4 brought to the Block 6 layout with culverts (31 crossings), dykes (36 heights) and a cost estimate (100.8 mOMR) — `W7/README.md`**; 2026-10-11: SewerGEMS: all eight scenarios designed through the bridge, the 37 channel profiles inside R2, **the SewerGEMS-format profile DXFs of all 37 channels in all 8 scenarios and the A1 plan-profile sheets of all 37 channels at 200 yr** built without the GUI (`W6/sewergems/dxf`, `W6/sewergems/sheets`), **and the complete 200-yr drawing set as one PDF with cover, table of drawings and catchment dividers, both clean-room gates passed** (`W6/sewergems/sheets/scripts/PDF/Set`); size labels corrected after his challenge, HAWCH1-C7 and SHACH1-C12 are 3 m deep in every scenario; **SHA-CH13-SS fixed in revision R3 through the API (outfall SHACH13-O15) and designed in all eight scenarios with the design scoped to that channel: 2.5 x 49.5 m at 200 yr, the hand rule's number**; the set reordered to Al Hawasinah, Shafan, Sarami, Sakhin with the channels in the shapefile's order; **revision R4 (min slope 0.002, max 0.03): the 200 yr design re-run, 66 sizes changed, widest channel 966 → 395.5 m, 8 of 15 outfalls cut 0.5–2.8 m below the GDP bed; **R5 (min slope 0.001): 41 sizes changed, widest 558 m, 6 outfalls below the bed against R3's own 5**; R4 kept in `W6/sewergems/sheets/archive`, sets now tagged per revision, drawings ordered by CH number within the catchments; **R6: ten Road-OQ crossings withdrawn as fix points (ground = GDP + wadi raise), 48 sizes changed from R3, widest 519.5 m**; **R7: his GDP edit of SHA-CH1-FP read back from the drawing, outfall SHACH1-O11 lowered 1.2 m, two conduits changed; **R8: his rule that the raise is fixed and an edited GDP moves the ground, SHACH1-12 lowered 0.6 m, SHACH1-C11/C12 from 519 to 364.5 m**; **assessment: with the Shafan 08 dam in the hydrology the 200-yr peak at SHA-J47 falls 42 % (1641 → 955 m3/s) and SHA-CH1-FP would be about 41 % narrower; temporary Basin 6 in the HMS project** (`W6/README.md`); his choice of floor pending before the other return periods; W6: **the channel design points for SewerGEMS** — flow, channel-end, fix and 500 m downstream points as layers in the engineer's QGIS project and as markers in every profile view; **Basin 5** (SHA-S51, Q200 313.4 m³/s) built, computed and written into his flow file; the 22 channel ends set to their receiver's GDP in the drawing; the W6 point layers are the master of his point edits after a data-loss incident; the live GDP files moved to `W6/gdp`, 227 breaks / 190 segments after his two profile edits; afternoon: the four LOW ends raised, and **the final SewerGEMS layers** `W6/final/Block4_design_points.shp` (227 points, all kinds merged) and `Block4_design_segments.shp` (212 segments between them), with the SewerGEMS names `HAWCH7-1` / `HAWCH7-C1` as fields and written into the profile views; 2026-10-11: **wadi depth at the design points** on all 227 design points (52 clear and 7 braided wadis, 109 shallow, 59 none) from the 0.5 m DTM the Civil 3D ground was cut from, perpendicular sections, lower bank top minus bed, Raise = bank − GDP (at the 54 fix points the library depth above the GDP bed instead: 2.5 m, 3.0 m at SHACH1-13) and WadiDepth joined into the final point layer, plus `GDP-Raised` (the node ground) and the outfall flag at the 15 free channel ends: the point and segment layers are the SewerGEMS import set (`W6/wadi`, `39_wadi_depth.py`); **the eight return-period scenarios of his SewerGEMS model designed in the offline VM** through the bridge (`W6/sewergems`, results in `sewergems/results/run_20261011_1721`, the computed copy delivered as `SewerGEMS Block 04_R1.stsw`; widths up to 966 m at 200 yr and the 3 m catalogue never used: his review; then **the 37 channel profiles created inside SewerGEMS** as revision R2 with the scenario results beside it, backup 5 of his model and the 0.5 m terrain point DXF in the model folder; the 43 Rustaq profiles then deleted from R2; **trial on HAW-CH1-FP: the SewerGEMS profile DXF reproduced without the GUI, entity for entity against the Rustaq export, and the A1 plan-profile sheets built with the Block 6 pipeline** (`W6/sewergems/dxf`, `W6/sewergems/sheets`)); **the live Civil 3D drawing is now `W6/civil3d/Block04_Channels_W6.dwg`** (copy of W5 plus the cyan profiles `GDP-raised <name>` = GDP + Raise and the point names with D/R; W5's drawing frozen); Deliverables refreshed). Before that 2026-10-07 (W5: **the Civil 3D drawing of the 73 channels and dykes** rebuilt on the project template through the civil3d-roslyn MCP server, after the W4 build's illegible views and misplaced leaders; five reversed centrelines corrected and 17 trimmed ones followed; **ground design profiles of the 37 channels** with the SewerGEMS segment and break shapefiles in `W5/gdp`; W4 keeps the geometry; Deliverables refreshed). Before that 2026-10-06 late night (W3: **report R3** issued — storm patterns figure, channel names on the routes map, Block-wide climate charts; R2 and R1 had been issued — the engineer's remarks on R1 applied to the maps, the EAV charts and the climate charts; R1 had been issued the same evening — nine dams incl. Shafan 08 from the new **Basin 4**, all 70 R0 comments addressed, Majlas style, Q200 junction maps; dam workbooks, sediment, climate and maps rebuilt for nine dams; Block 4 channels and dykes named in the shapefile — `W3/channel naming`). Rules of the folder: iterations live in `W#`
folders and are never overwritten; the category folders hold the *current* copies of what matters; this README is the
project state.

## Where things are

| Folder | Contents |
|---|---|
| `README.md` | this file: state, decisions, findings |
| `..\Deliverables\` | **the one organised copy of everything**, in numbered snapshots `<n> Deliverables <ddmmyyyy>` (Oman date; the PC clock runs on US Pacific time): report, HMS model files, dam and channel tables, shapefiles, KMZ, sediment, climate, maps, QGIS projects, scripts, the references from other projects and the server. Built and refreshed by `scripts/sync_deliverables.py` into the latest snapshot (`--new-version` starts the next; older ones are frozen), with `MANIFEST.csv` (source, size, hash per file), a generated `README.md` and `10 References/SOURCES.md`. **`Block04_Deliverables.qgz` at each snapshot's root** (built by `scripts/build_deliverables_qgis.py` after the sync) holds every relevant layer in groups and subgroups and every report map layout, all paths relative and inside the snapshot. Internal. Refresh after every substantive change; `--check` fails when a copy is stale or a new file was never synced |
| `scripts/` | current Python/Jython scripts (also archived per iteration in `W2/scripts`) |
| `model/` | `Basin_2.basin/.sqlite`, `Basin_3.basin/.sqlite`, `basin4_staging/` (Basin 4 as installed) and `project_files/` = snapshot of the HMS project files after the runs (.hms, .run, .nals, .pdata, .dss, .met); `_sizing_backups/` = basin files as they were before each width rewrite, including the wrong-file versions of the 2026-10-05 incident (see findings). **The live model is `..\Hydrology\HEC_HMS_Block_04\`** (backups `..\Hydrology\Backup\1…19 HEC_HMS_Block_04.rar`; 19 = before Basin 4) |
| `results/` | depth-area results for Basin 2 and Basin 3 (`basin2/3_peak_flow_volume.xlsx`: peak and volume at every element, 13 return periods), dam inflow vs outflow, outfalls B2 vs B3, reservoir peak levels, channel sizing tables (applied) and the second-pass check `Basin_3_reach_sizing_Q200_pass2_check.csv` (not applied), element rename map. The first-pass Basin 3 results (computed with Basin 2's sections) are kept only in `W2/output/hms/results/*_pass1_B2sections.*` |
| `gis/` | `Basin_2_review.gpkg` (subbasins, reaches, junctions for QGIS), red lines and merge regions digitised from the engineer's screenshots, result overlays (`result_<n>.png`), raw delineation `review.gpkg`, reconditioned DEM |
| `reservoirs/` | elevation-area-volume curve per dam (`EAV_<dam>.csv`), summary vs the dams sheet, crest polygons, spillway ratings (`reservoirs_added.csv`) |
| `inputs/` | copies of the inputs used: engineer's review screenshots, `CH.shp`/`WALL.shp` (channels and dykes/roads used to recondition the terrain), Block 04 dams shapefiles and `Block 4 Dams Details.xlsx`, global catchments `GCA RENN.shp` |
| `W1/` | July 2026: peak flow / volume extraction from Basin 1's depth-area runs (Basin 1 only). `W1/Data` (input snapshot, large) is still at `..\Hydrology\Claude Block 04\Data` — locked by an open application when the folder was moved; move it here when free |
| `W2/` | October 2026: the whole Basin 2 / Basin 3 build, step by step, with its own README (method detail, validation, every rule) |
| `W4/` | 2026-10-07: the geometry of the channel design's Civil 3D base — 1 m corridor points of every channel and dyke on the 0.5 m DEM (terrain point DXF, per-feature CSV and DEM strips), LandXML surfaces + alignments, centrelines, profile-view placement, `build_spec.json`, scripts, own README. Its two drawings are the record of the first build (illegible views, leaders at the origin): **superseded by W5** |
| `W8/` | 2026-10-13: **report R5, the stormwater channels report R0, the two drawing sets with key plans, KMZ, the submission folder** — his review of R4 applied (template from the submitted Block 6 report, document control, abbreviations, land cost, culvert depth, 10 m radius, reach map in four panels, GCA map); the sheets regenerated in W8 without text overlaps (seven passes, oriented-box scan); `Deliverables/2 Submission 13102026` built by `scripts/90_submission.py` + `91_submission_qgis.py`; also the dam characteristics table for Blocks 2, 4 and 6 (parallel session). `W8/README.md` |
| `W7/` | 2026-10-12: **the Shafan 08 dam in the channel hydrology** (his decision after the W6 assessment): Basin 6 = Basin 3 + the Basin 4 reservoir with its full 31.0 km² catchment (SHA-S23 := S23, SHA-S44 and SHA-S46 trimmed), 13 depth-area analyses × 362 points, `results/basin6_*`; flows refreshed on the four SHA-CH1-FP points only; SewerGEMS **R9** (all eight scenarios) through the bridge; elements B6, maps R4, **report R4** in `W7/report`; the 200-yr plan-profile set R9. `W7/README.md` |
| `W8/` | 2026-10-13: **characteristics of the proposed dams of Blocks 2, 4 and 6 in the Block 6 table layout** (type, height above wadi, crest length, FSL, capacity), one Word document built from the dam team's sheets and axis profiles on the server (`07-Structures\03-Dam Design`), the January 2025 axes of Bidah 03 and Faydh 01 on the 2 m DEM, and the 2023 feasibility ranking; Block 2 has no dam design yet. `W8/README.md` lists where every dam figure lives on W:. |
| `W6/` | 2026-10-10: **the channel design points for SewerGEMS** — flow points (the engineer's `Hydraulic\SHP\tmp\Qp Vol Block 04.shp`, three points filled: SAR-S11, HAW-S14 from Basin 3, SHA-S51 from the new **Basin 5** catchment), channel ends on receiving channels, fix points and their 500 m downstream points, as four layers in his QGIS project and as markers in every profile view of the W5 drawing; Basin 5 build, compute and extraction scripts; junction fix (22 channel ends set to the receiver's GDP, the previous line kept dashed, backup of the drawing first); `gdp/` holds the live GDP files (227 breaks / 190 segments), rewritten after each of his profile edits, `W5/gdp` frozen; **`output/design_points.gpkg` is the master of the flow and fix points** (his edits live there; read and archived before every rewrite since the 2026-10-10 11:10 incident); **`final/`: the one point layer (227 points: GDP breaks, flow, fix, 500 m and channel-end points merged within 10 m, junction points split the receiver) and the segment layer (212, ends equal to the points) for the SewerGEMS import, with frozen copies**; `wadi/` the wadi depth at every point from the DTM; **`civil3d/Block04_Channels_W6.dwg` the live drawing** (W5 copy + cyan profiles `GDP-raised <name>` = GDP + Raise + point names with D/R); own README |
| `W5/` | 2026-10-07: **the Civil 3D drawing `W5/civil3d/Block04_Channels_W5.dwg`** on the project template (the live drawing until 2026-10-11, then copied to W6 and frozen): 73 corridor surfaces, alignments, ground profiles, profile views and view-to-alignment leaders, styles of the template (`civil3d/styles.json`), built from the W4 geometry through the civil3d-roslyn MCP server (C# run inside Civil 3D, `cs/*.cs`, `scripts/`), QA plots and inspections in `civil3d/qa`, own README |
| `W3/` | 2026-10-06: deliverables from the results — dam EAV and hydrograph workbooks (nine dams, Basin 4), element tables/shapefiles/KMZ (Basin 3/2), dam catchments, RUSLE sediment yield with the engineer's floors, reservoir volume reduction (USBR 2.6), per-dam climate record and gauges, eleven R1 maps and the Block 04 report R1; `channel naming/` (2026-10-06): the 73 Block 4 channels and dykes named after the Block 6 convention and written into the channel shapefile. Own README with the state table and findings |

## What the project is

Block 04: nine flood-protection dams for the dam design (Hawasinah 02, 11, EX = **Hawasinah UP** in the report; Shafan 02
and 08; Sarami 03, 05; Sakhin 04, 08 = **Sakhin 08 (Mehmum)**) and a network of flood-protection channels (FP CH),
stormwater main and secondary channels (Sw M/S CH) and dykes on the Batinah plain between the dams and the sea. The
channel scheme is designed with eight dams (Shafan 08 excluded from it at the engineer's instruction, not to be mentioned
in the report). HEC-HMS 4.12 project `Hydrology\HEC_HMS_Block_04`:

- **Basin 1** (the hydrologist's): dam catchments only, 32 subbasins, no reservoirs, hand-edited after delineation.
- **Basin 2** (Claude, 2026-10-05): Basin 1's elements copied verbatim + 80 new subbasins for the channel network,
  110 subbasins / 129 junctions / 115 reaches / 13 outfalls. No reservoirs. 13 depth-area runs `DA <rp> B2`.
- **Basin 3** (Claude, 2026-10-05): Basin 2 + a reservoir 150 m below each dam junction. 13 depth-area runs `DA <rp> B3`.
- **Basin 4** (Claude, 2026-10-06): Basin 1's 32 subbasins + the nine reservoirs (Shafan 08 included, bed 153 / FSL
  168 / crest 173), 13 depth-area runs `DA <rp> B4` — the source of the dam deliverables and the report's dam chapters.
- **Basin 5** (engineer's empty model, filled by Claude 2026-10-10): one subbasin **SHA-S51** (16.44 km², the catchment
  delineated for 495922.5, 2651832.5; CN 86.3, Ia 8.04 mm, longest flow path 10.1 km, S10-85 0.0105, lag 64.7 min, the
  decision-6 method) → outlet junction SHA-J52; 13 depth-area runs `DA <rp> B5`; its flows feed the channel design point
  SHA-S51 (the start of SHA-CH13-SS). `W6/scripts/30_basin5_build.py`, backup `_backup_before_basin5_20261010_012139`.
- Met models FM 2yr … FM PMP (hypothetical storms, ARF table) and Control 1 are shared by all basins.

## Decisions (engineer's, in order)

1. Dam catchments in Basin 2/3 are Basin 1's own elements, unchanged (one deliberate exception: S111, 7 km², merged
   into Hawasinah EX's local subbasin S16 at the engineer's request; EX inflow is therefore 0.4–0.8% off Basin 1).
2. Shafan 08 dam removed; its ground is re-delineated and drains to the channels.
3. Walls (dykes and the long roads) are catchment boundaries; a junction wherever a channel passes through a wall
   (culvert); no junctions at confluences inside a wall-closed compartment; subbasins < 1 km² or enclosed by another
   are merged into their neighbour; free-ended dykes stay as drawn; dyke ends within 10 m of another dyke are snapped.
4. Catchment shapes reviewed on HMS screenshots: red loops = one catchment each; the engineer's own HMS merges and
   deletions (R151, R170, R199, R196, J210, Outlets 11 and 13, S238) are re-applied on every rebuild.
5. Naming: outfalls `<GCA>-O<n>` west to east within the global catchment; other elements `<GCA>-S/R/J<n>` after the
   global catchment they fall in (`J_CA` of `GCA RENN.shp`: HAW, SHA, SAR, SAK; Mashin-side elements pinned to HAW);
   dam junctions keep their names.
6. Hydrology parameters: CN from `CN_Include_Hill_Area.tif`; Ia = 0.2·25.4·(1000/CN − 10); lag = Kirpich on the
   10–85 flow path, 0.6·(1/52)·L^0.77/S^0.385 (verified to be what Basin 1 used).
7. Muskingum-Cunge: n 0.1 on every reach as in Basin 1; channel reaches are trapezoids, side slope 1V:3H, bottom width
   so that the 200-year depth-area flow runs 2 m deep — Basin 2 on its own flows, Basin 3 on the reservoir-routed flows.
   Natural plain reaches: trapezoid from DEM cross-sections; Basin 1 reaches: Basin 1's values.
8. Reservoirs: elevation-area from the 10 m DEM inside the crest polygons (Crest_Level contour closed by the dam axis);
   spillway Q = 2.1·L·H^1.5 above FSL with the sheet's lengths, dam-crest overtopping above crest; Modified Puls.
9. Channel and dyke names (2026-10-06): `<GCA>-<CH or D><n>-<FP/SM/SS>` as Block 6 (`HAW-CH1-FP`): upper-case code of
   the global catchment holding most of the feature's length (`Al ` dropped), one counter per catchment for channels
   and one for dykes, flood protection first, then stormwater main, then stormwater secondary, west to east by the
   westernmost vertex; class from `CHtt`. Written into `Hydrology\SHP\temp\Channels and Dykes 04102026.shp` (Name
   field, Block 4 rows only). Five features straddling a catchment boundary keep the majority catchment until the
   engineer says otherwise (`W3/channel naming/README.md`).

## Findings worth remembering

- Basin 1 cannot be regenerated from terrain (hand merges); the pipeline reproduces 24 of its 32 subbasins exactly
  and all dam catchments within 0.8 km² on its own terrain, so copying its elements is the honest route.
- HMS lets a burn (channel) cut through a wall where they cross; treating the crossing additively diverted 41 km²
  from Sakhin 04. Thin (8-connected) walls leak diagonally in D8; walls must be rasterised diagonal-tight.
- HMS draws only the first part of a multi-part subbasin polygon; "missing catchments" on screen were that.
- Outlet junctions must not carry a `Downstream:` line, or HMS reports "Invalid link … to None".
- HMS rewrites project files from memory on save/exit: **HMS must be closed whenever files are written**, and every
  file written is diffed against the HMS-saved version first so the engineer's in-HMS edits survive.
- Headless compute works (`scripts/hms_compute_all.py`): `HEC-HMS.cmd -script` from the HMS folder, depth-area
  analyses through `Project.computeDepthAreaAnalysis` reached by reflection; ~2 min per analysis of 354–362 points.
- With n 0.1 and 2 m depth the undammed FP channels below the dams come out 1–6 km wide (Basin 2); with the
  reservoirs (Basin 3) the channel below Hawasinah EX (HAW-R21) carries ~180 instead of 5 900 m³/s at 200 years and
  is 66 m instead of 2 308 m wide; 6 Basin 3 reaches are still over 1 km.
- The sections feed back on the flows: Basin 3 with its own (narrower) sections gives 200-year peaks 7–10% higher at
  HAW-O1, SAK-O1 and SHA-O5 and up to 33% higher on SAR-R12/R13 than the same basin with Basin 2's sections (less
  Muskingum-Cunge attenuation); reservoir outflows and levels do not change.
- **Incident 2026-10-05:** the first sizing script read `Basin_3.basin` and wrote `Basin_2.basin`, so Basin 2 became a
  copy of Basin 3 and Basin 3 kept Basin 2's widths until the engineer spotted HAW-R21 at 2 308 m. Basin 2 was
  restored from the pre-reservoir backup (identical to the file behind the Basin 2 results), Basin 3 re-sized and
  recomputed. Rule since then: after writing any basin file, check header, element counts and one known value in
  **every** basin file of the project.
- Reservoir check: at PMP all eight reservoirs rise 4.7–5.0 m above FSL (= the sheet's Hmax 5 m) and Hawasinah 02's
  PMP outflow is 17 750 vs the sheet's QPMF 17 809 m³/s. Five dams store the whole 100-year flood and Hawasinah 11 all but
  15 m³/s; Hawasinah 02 (11 Mm³ on 420 km²) attenuates almost nothing; Hawasinah EX receives less in Basin 3 because 02 and 11 are upstream of it.
- Dam inflows: Basin 2 = Basin 1 within 0.1% (EX within 0.8%, see decision 1).

10. Report R1 (2026-10-06): Shafan 08 in the report for the dam team; Hawasinah EX written Hawasinah UP and Sakhin 08
    as Sakhin 08 (Mehmum); dam order Hawasinah 02, 11, UP; Shafan 02, 08; Sarami 03, 05; Sakhin 04, 08; no internal
    matter in the report (no file or folder names, basins, revisions, other blocks or the dam team); sediment floors
    SDR 0.2 and 90 m³/km²/yr with P = 1; Majlas report style; per-dam climate from a finer source with the 2331 gauges.

11. Clean-room gate for the report (2026-10-07, global rule 14): nothing internal reaches the client, and a scan proves it.
    `W3/report/build.py --pdf` runs `W3/report/check_clean.py` on the rendered PDF against `forbidden_terms.txt` (Basin names,
    job code, Block 6 / Majlas / Ibri, the dam team, Hawasinah EX, model file names, plus the built-in list: paths, extensions,
    W#/R# tags, process talk, placeholders) after blanking `allowed_terms.txt` (SM2RAIN, Open-Meteo, the W1/WT symbols); any
    hit fails the build and renames the outputs `*_FAILED-CLEAN-CHECK`. R0 fails with 73 hits, R3 passes. Every new internal
    name goes into `forbidden_terms.txt` the moment it appears.

## W3 deliverables (2026-10-06) — see `W3/README.md`

- Channel naming: `W3/channel naming/output/block4_channel_names.csv` (QGIS fid → Name, catchment shares, flags);
  the source shapefile `Hydrology\SHP\temp\Channels and Dykes 04102026.shp` now carries the 73 Block 4 names
  (pre-edit copy in `W3/channel naming/input/`); Block 6's own names audited in `block6_name_audit.csv`.
- Dam design team: `W3/dams/eav/Block04_Dams_Elevation_Area_Volume.xlsx`, `W3/dams/hydrographs/Block04_Dam_Hydrographs.xlsx`
  (+ `dams_reservoirs.xlsx`), `W3/sediment/B4_DAM_RUSLE.xlsx`, `W3/sediment/Block04_Reservoir_Sedimentation.xlsx`,
  `W3/climate/Block04_Climate.xlsx`; element tables/shapefiles/KMZ in `W3/elements/`.
- Report: `W3/report/R3/Block04_Report_R3.docx` + PDF — live; R2, R1 and R0 superseded (kept).
- Findings (R1): PMP dam inflows reproduce the dams-sheet QPMF; per-dam 9 km reanalysis climate 66–106 mm/yr; sediment
  yield with the floors 90–185 m³/km²/yr; storage lost in 50 years 1.9–8.3 % except **Hawasinah 02 (37 %, 74 % in 100
  years) and Shafan 08 (20 %, 39 %)** — both need a sediment management provision; the Majlas sedimentation engine needed
  two numerical fixes on DEM curves (W3 README).
- Decisions: nine dams in the dam deliverables (Basin 4), eight in the channel scheme (Basin 3); reservoir operation 3
  (normally empty) and trap efficiency 100 % for sedimentation; Williams (1977) SDR with the 0.2 floor, yield floor 90
  m³/km²/yr, density 1.5 t/m³, P = 1; all charts in one report style (hairline gridlines, Arial).

## Open

000. Channel design points (2026-10-10, `W6`): the engineer edits the flow and fix points on the W6 QGIS layers
    (`W6/output/design_points.gpkg`, the master since the 11:10 incident) and the GDPs in the W5 drawing; after the
    junction fix of 02:09 (22 channel ends set to the receiver's GDP, previous line dashed) and his two profile edits,
    four ends were again below the receiver's GDP and were raised on his instruction (12:34, backup first), so all 22 ends
    match; 74 flow points (SAK-J7 and SHA-J24 left without geometry by him), 54 fix points, 15 downstream points (25
    declared redundant in `W6/inputs/downstream_exclusions.json`). **The final layers for SewerGEMS are built** (`W6/final`,
    227 points / 212 segments, `W6/README.md`): he reviews the four merges over 1 m (3.3 m at most; the HAW-CH3-SS case
    was resolved by him moving GB1 onto the junction) and the junction points, reviews the wadi depth of all 227 points (`W6/wadi`, on the DTM: 52 clear, 7 braided, 109 shallow, 59 none; Raise =
    bank − GDP; at fix points the library depth above the GDP bed, 2.5 m standard and 3.0 m at SHACH1-13, the one segment
    that can take a deeper library; WadiDepth, GDP-Raised and Outfall in the final point layer, stacked labels in QGIS); the
    two final shapefiles were imported by him into SewerGEMS (model of 2026-10-11, eight scenarios) and all scenarios were
    designed through the bridge (`W6/sewergems/results/run_20261011_1721/summary.md`); he reviews the design constraints
    (widths of hundreds of metres at 100 yr and above, flow depths 0.7–1.9 m in a 2.5 m section), then decides the design return period. **Correction 2026-10-11:** the earlier finding that the 3 m catalogue was never used was
    wrong; HAWCH1-C7 and SHACH1-C12 are on it in every scenario, 3 m deep (his five catalogue classes share their size GUIDs, a
    size is class + GUID; exports, summary, profiles and sheets corrected, `W6/README.md`). The SewerGEMS-format profile DXFs of
    all 37 channels in all 8 scenarios and the plan-profile sheets of all 37 channels at 200 yr are built
    (`W6/sewergems/sheets/scripts/PDF/Combined/<channel>.pdf`); on the plans the bed is the designed span and the corridor the
    span + 15.5 m each side (embankment 11.5 m + access road 4 m, his definition of 2026-10-12). SHA-CH13-SS, never computed because its end was a manhole, was fixed through the API in **revision R3** (outfall
    SHACH13-O15, the design scoped to the channel, all eight scenarios, `W6/README.md`). At the office he opens R3 (37 channel
    profiles, the Rustaq ones deleted),
    builds the terrain from `Terrain\Terrain_Points_B4_0.5m.dxf`, and decides the design return period and the real bed and
    corridor widths for the sheets. The design ground is the DTM `GGC4_DTM_GMAP_NSA.tif`, not the
    hybrid DSM: verified 2026-10-11 against the EG profiles (DTM = EG to 1 cm, HDSM off by up to 1.1 m).
00. Ground design profiles: `GDP <name>` on the 37 channels, generated 2026-10-07 by the engineer's method (largest
    departure from the ground, 201 m trend, 0.75 m tolerance, 100 m minimum segment, no reverse slope) and **reviewed
    and adjusted by hand by the engineer on 2026-10-08 and twice more on 2026-10-10**. **The live GDP files are
    `W6/gdp/Block4_channel_segments.shp` (190 segments) and `Block4_channel_breaks.shp` (227 breaks)**, rewritten from
    the drawing by `W5/scripts/27_gdp_from_drawing.py` after every profile edit, and the SewerGEMS input; `W5/gdp`
    (241 breaks / 204 segments) is frozen at the junction-fix state. The review layers sit in his QGIS project (groups
    "W5 Civil 3D review" and "W6 design points"); the channel design itself (sections, SewerGEMS model in the offline
    VM) is the next step.
0. W5 Civil 3D drawing (2026-10-07): built and saved with the template's styles (profile view "ARJV_ Land Desktop Profile View" 50/25 m ticks, band set "HTJ (EG-FG Elevations and Stations)", 1:1000). Engineer to review the legibility in Civil 3D: a km-long view at 1:1000 is only legible zoomed in; options are a derived view style with 100/50 m ticks or an annotation scale of 1:2000–1:5000 (both are one script run over the 73 views, no rebuild). The `civil3d-roslyn` MCP tools appear in Claude after a session restart.

1. Channel widths follow the n 0.1 / 2 m rule; design n and depths per channel type (Block 6 report) not yet applied.
2. The hydraulic design of the channels (`..\Hydraulic\` is empty).
3. Design return period for the channels not fixed.
5. W3 report R3 is with the engineer for review (2026-10-06 late night); channel design started 2026-10-07 in W4/W5 (Civil 3D base: the W5 drawing); the channel design chapters (sections, widths, dykes, crossings) wait for the channel design; the sediment loads of Hawasinah UP and Shafan 08 are upper bounds (no credit for upstream trapping) — engineer to decide whether to credit it.
4. Second sizing pass not applied: on Basin 3 it would widen 8 of 81 channel reaches by more than 10% (SAR-R12/R13
   +34%, SHA-R48…R52 +14–16%; `results/Basin_3_reach_sizing_Q200_pass2_check.csv`), the rest by a few %. Engineer to
   decide whether to iterate. Hawasinah EX inflow differs from Basin 1 by the S111 merge (engineer: "no need" to revert).
7. Five features are digitised against the flow in `Hydrology\SHP\temp\Channels and Dykes 04102026.shp` (SAK-CH1-FP,
   SHA-CH11-SS, SHA-CH1-FP, SHA-CH17-SS, SAK-D4-FP; engineer, 2026-10-07). The W5 drawing builds them reversed
   (`W5/civil3d/corrections.json`); the shapefile itself is the engineer's to flip in QGIS before the next export.
   The engineer trimmed 17 channel ends in that shapefile (2026-10-07 05:15); the W5 drawing follows it
   (`W5/scripts/23_update_lines.py` → `build_spec_w5.json`, `24_update_features.py`): the channel lengths of the W3
   deliverables and report (from the 04102026 shapefile before the trim, up to 503 m longer for SAK-CH2-FP) are now
   stale by those trims — to be refreshed when the channel design chapters are written.
6. Five Block 4 channel/dyke features straddle a global-catchment boundary (HAW-CH7-SS 53/47 with Mashin, HAW-D1-FP,
   SAK-D3-FP, SAR-D3-SM, SHA-CH2-SM): named by majority length, engineer to confirm or move (2026-10-06). Prefix case
   differs between blocks (Block 4 `HAW`, Block 6 `Taw`).

## Block 06 precedents for the channel design (engineer, 2026-10-07)

- Block 06 channel design was done before; its SewerGEMS output DXF profiles were used to create the sheets, in `D:\Mojtaba\Renardet\2224 WS11\Block 06 SewerGEMS` (W1–W5).
- The channel terrain was generated in `C:\Users\mojtaba\Documents\Channel Terrain\W9`; usable for the BOQ.
- The project's Civil 3D template is `..\Hydrology\DWG\C3D template\C3D Template.dwt` (alignment, profile view and other styles): new Civil 3D drawings start from it (the W5 drawing, 2026-10-07; its command defaults name the styles to use: `W5/civil3d/qa/style_inventory.json`).
- Civil 3D automation (2026-10-07): the **civil3d-roslyn MCP server** (`C:\mcp\civil3d-mcp-roslyn`, nezolder/civil3d-mcp-roslyn, MIT) runs C# inside Civil 3D 2026 through its NETLOADed plugin `Civil3dMcpRoslyn.dll`; `W5/scripts/c3d_mcp.py` drives it from Python; `W5/README.md` has the traps (port pinning next to the older plugin, the "Load Once" security click, `using` directives, api_lookup for real signatures).

## Conventions for the next session

HMS closed before writing; back up (`..\Hydrology\Backup\<n+1> HEC_HMS_Block_04.rar`, files at archive root) before
model changes; new work in `W3/` with its own README; update this file on every substantive change; **a report is issued
only after the clean-room gate passed (decision 11)**; **refresh
`..\Deliverables` with `scripts/sync_deliverables.py`, rebuild its root QGIS project with `scripts/build_deliverables_qgis.py`
(QGIS Python) when layers or layouts changed, and run `--check` before ending a session** (a new output folder or an
external reference must be added to the sync script's SPEC list, a new layer to the builder's TREE/NEW lists, or the check
will not know it). The map figures read nothing outside the project folders: the 200-year depth raster of the server is
clipped by `W3/scripts/13_maps_prep.py` into `W3/maps/data`.

## GitHub repository

`https://github.com/mojikone/Channel-desing-of-Block-04` holds this folder (pushed 2026-10-13). Left out by `.gitignore`: the generated
intermediates of the plan-profile sheet pipelines (sheet DXFs, per-sheet and combined PDFs, satellite tile caches), AutoCAD backups, and
every file of 100 MB and more (the assembled drawing sets, the Civil 3D drawings, a few rasters), listed with sizes in
`LARGE_FILES_NOT_IN_GIT.md`. The complete client package is the submission folder `Block 4\Deliverables Submission 13102026` on the PC.
