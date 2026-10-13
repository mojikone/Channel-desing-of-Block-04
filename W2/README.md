# W2 — HEC-HMS "Basin 2": Block 4 channel network added to the Basin 1 dam catchments

**Status: LIVE (2026-10-05).** W1 (DSS results extraction) is unaffected and still valid for Basin 1.
Basin 2 is installed in the HMS project (`Hydrology/HEC_HMS_Block_04/Basin_2.basin`, `Basin_2.sqlite`,
registered in `HEC_HMS_Block_04.hms`; the previous `.hms` is in `_backup_before_basin2_20261005_063814/`).
**Opened in HMS 4.12 on 2026-10-05 and loads; rebuilt 2026-10-05 after the engineer's screenshot review (red-loop catchments, virtual walls); not run yet.**

## What Basin 2 is

| | Basin 1 (carried over verbatim) | New (channel network) | Basin 2 total |
|---|---|---|---|
| Subbasins | 30 | 80 | 110 |
| Junctions | 27 | 102 (13 outfalls, <GCA>-O<n>) | 129 |
| Reaches | 20 | 95 | 115 |
| Area, km² | 1549.8 | 912.7 | 2462.5 |

- **Dam catchments are Basin 1's own elements, copied text-for-text** (areas, CN, lag, reach parameters, manual
  edits included). The only change to those blocks is that the terminal dam junctions (Hawasinah EX, Sarami 03,
  Sarami 05, Sakhin 04, Sakhin 08) and Shafan 02 now have a downstream reach into the plain.
- **Shafan 08 is removed**, as instructed. Its Basin 1 sub-network (S22, S23, J17, J18, R15, R16, junction Shafan 08)
  is not carried over; that ground is re-delineated from the new terrain and drains into the channels. Basin 1
  junction locations J17/J18 are kept as plain junctions.
- **New subbasins** (117): one per wall-closed compartment and channel exit; the largest is 108 km² of plain
  draining to a single culvert, the smallest 0.04 km². Names S101…, junctions J101…, reaches R101…, sea outlets
  "Outlet n <type> <CH feature id>".

## Dam catchments: new terrain vs Basin 1

Delineated on the CH/WALL-reconditioned terrain, break points at Basin 1's junction coordinates
(`output/dam_catchment_comparison.csv`):

| Dam | Basin 1 grid, km² | New terrain, km² | Diff |
|---|---|---|---|
| Hawasinah 02 | 419.84 | 420.38 | +0.54 |
| Hawasinah 11 | 226.04 | 226.27 | +0.23 |
| Hawasinah EX | 841.41 | 842.41 | +0.99 |
| Shafan 02 | 224.37 | 224.52 | +0.16 |
| Sarami 03 | 227.78 | 227.80 | +0.02 |
| Sarami 05 | 53.70 | 53.69 | −0.01 |
| Sakhin 04 | 110.49 | 110.49 | 0.00 |
| Sakhin 08 | 81.31 | 81.31 | 0.00 |

The differences are flat-area routing noise between WhiteboxTools and HMS (same magnitude on Basin 1's own terrain,
`output/validation/dam_catchments_on_basin1_terrain.csv`). Basin 1's *topology* figures differ from its own grid at
Hawasinah EX (852.2 vs 841.4) and Shafan 08 because of manual edits in Basin 1, not because of this work.

## Method

1. **Reconditioning** (`scripts/build_recond.py`): Basin 1's 10 m terrain `NSA_5m_B04_Res10m/elevation.tif`;
   CH lines burned −1005 m, WALL lines raised +1005 m (the magnitudes HMS used for Basin 1), 3-cell taper
   3.75/2.5/1.25 m. **Walls are rasterised diagonal-tight** (`all_touched`), otherwise D8 flow slips between two
   diagonally adjacent wall cells: with thin walls 1180 flow arcs crossed dykes, with tight walls none.
   **Priority at crossings: channel cell > wall (centre and taper) > burn taper**, i.e. a channel opens the dyke only
   on its own cells (a culvert); doing it additively diverted 41 km² away from Sakhin 04, and letting the burn taper
   open the dyke leaked 70 m wide. Fill + D8 + accumulation with WhiteboxTools 2.4.
2. **Streams**: natural network at 5 km² (Basin 1's threshold) plus every CH channel traced along D8 from its
   upstream end (so each channel has a catchment regardless of size).
3. **Junctions** (rules fixed with the client engineer on 2026-10-05: *walls are catchment boundaries; very small
   catchments inside a wall-closed compartment are merged into one; free-ended dykes stay as drawn; a dyke end
   within one cell (10 m) of another dyke is snapped shut, wider gaps are openings*): Basin 1's 30 junction
   coordinates (snapped onto the confluence cell within 50 m); a **culvert junction wherever a channel chain passes
   through a WALL line** (57); every confluence that receives a reach (HMS needs a junction there); sea outlets.
   No junctions at plain confluences inside a compartment. Junctions within 100 m of the next one downstream are
   merged unless they are dams, culverts or reach joins. One subbasin per inflowing stream branch at each junction,
   then subbasins < 0.5 km² are merged into the largest subbasin of the same compartment (27 merges; CN area-weighted,
   flow path and lag of the host kept).
4. **Parameters**: area; CN = zonal mean of `CN_Include_Hill_Area.tif`; Ia = 0.2·25.4·(1000/CN − 10) mm;
   longest flow path per subbasin, 10–85 length = 0.75·L, 10–85 slope from the DEM;
   Lag [min] = 0.6·(1/52)·(L₁₀₋₈₅ [m])^0.77 / S₁₀₋₈₅^0.385 (slope floored at 0.0005, used once).
5. **Assembly** (`scripts/write_basin.py`): Basin 1 blocks verbatim + new blocks; links draining into the retained
   Basin 1 network discarded; 10.9 km² where Basin 1's hand-extended polygons (mainly S16) overlap the new
   subbasins removed from the new ones so nothing is counted twice.

## Walls and catchment boundaries (checked 2026-10-05, `output/hms/walls_inside_catchments.csv`)

After the fixes above, 32 flow arcs cross a dyke line: 30 are channel cells (culverts, now junctions) and 2 are
spill points of closed compartments (S161 area, 4.6 km², at the far east; one negligible). With culvert junctions,
no catchment extends through a road or dyke any more. 11 new subbasins still have a dyke inside them, all of them
dykes with a free end (water rounds the end), which the engineer accepted as drawn. `output/wall_endpoints.csv`
lists the dyke ends that stop 1–150 m short of another dyke; only the 9.8 m one (W51 to W54) is snapped.

## Engineer's review round (2026-10-05, screenshots in `input_screenshots_20261005/`)

The engineer marked up 8 HMS screenshots with red loops (and merged 6 subbasins himself in HMS). Workflow
(`scripts/georef.py`, `faces.py`, `result_overlays.py`, outputs in `output/red_lines/`):
1. Each screenshot is georeferenced by a north-up similarity transform fitted on labelled element icons
   (5–37 m rms); the red strokes are skeletonised and traced into UTM polylines (`red_lines.gpkg`).
2. Closed loops become faces (`faces.gpkg`); every face = one subbasin, unassigned ground inside it included,
   draining to the face's exit junction. The engineer's own HMS merges are re-applied the same way, and S111 was
   merged into Basin 1's S16 (area 88.4 → 95.4 km²). `merge_regions.gpkg` holds all 20 regions.
3. The red lines were first also used as virtual walls in the terrain; the engineer then said the boundaries are
   tentative, so the final build uses the natural divides and the loops only as merge regions. S239 and S106 are
   forced to drain to J176 (his instruction).
4. Multi-part subbasin polygons (HMS draws only the first part, hence "missing" catchments) are made single-part
   by giving stray pieces to the neighbouring subbasin.
5. Gaps: slivers of ground that drained to a dam junction on the grid but lie outside Basin 1's hand-edited polygons
   (16 pieces, 0.25 km²) are joined to the adjacent new subbasin, so the catchments tile without holes.
6. Second round (screenshots 10 and 11, same day): the loops of screenshot 10 are hard boundaries (virtual walls)
   and merge regions (S240 25.7 km², S130 11.1 km²). The engineer's own HMS deletions (R151, R170, R199, J210,
   Outlet 13; R169 now to Outlet 9; J128 and J150 are end junctions) are re-applied by name on every rebuild
   (`USER_EDITS` in `write_basin.py`). Holes inside a subbasin that no polygon covers are filled, detached parts
   go to the neighbour, so every written polygon is single-part; the 46 ha "small catchment inside S239" was such
   a hole, now part of S239.
7. Naming (engineer 2026-10-05, third round): **outfalls `<GCA>-O<n>`, numbered west to east within each global catchment**; every other element is named
   `<GCA>-S<n>`, `<GCA>-R<n>`, `<GCA>-J<n>` after the global catchment it falls in (`J_CA` field of
   `GCA RENN.shp`, copied to `output/red_lines/`): first three letters, "Al " dropped (HAW, SHA, SAR, SAK; the east-edge elements the shapefile puts in Mashin
   are pinned to HAW on the engineer's instruction; AHI-S1 falls in Ahin). Numbering is upstream to downstream within each
   catchment (junction topological rank, then west to east; subbasins by their junction's rank then area). Dam
   junctions keep their names. Basin 1's copied elements are renamed too (S1 → see `output/hms/Basin_2_rename_map.csv`).
   Also: no subbasin under 1 km² and none enclosed by another (merged into the neighbour with the longest shared
   boundary, same junction preferred); the engineer's HMS deletions (R151, R170, R199, R196, J210, Outlet 11,
   Outlet 13, S238) are re-applied structurally on every rebuild.
8. Names persist: subbasins keep the engineer's names where the polygon is the same (79 of 85), junctions,
   outlets and reaches keep theirs where the cell or the junction pair is the same; new ones continue the
   numbering (S239…, J2xx). Two junctions emptied by merges (J18, J183) were dropped.
HMS opened the first build with 13 errors "Invalid link from element Outlet… to None": outlet junctions must not
carry a `Downstream:` line. Fixed in `write_basin.py`; the installed file has none.
Result overlays per screenshot: `output/red_lines/result_<n>.png` (and `overlay_<n>.png` = red lines over the
model before the change).

## Runs and depth-area analyses for Basin 2 (2026-10-05)

- The 13 met models (FM 2yr … FM PMP, hypothetical storms, uniform depth, ARF table "ARF FM") are linked to Basin 2
  (`Use Basin Model: Basin 2` + one blank-depth `Subbasin:` block per Basin 2 subbasin). Control 1 unchanged.
- 13 runs `FM <rp> B2` (Basin 2 + FM <rp> + Control 1 → `FM_<rp>_B2.dss`) and 13 depth-area analyses `DA <rp> B2`
  (every Basin 2 element as analysis point → `DA_<rp>_B2.dss`), same dates and time zone as Basin 1's.
- **Headless compute**: `scripts/hms_compute_all.py` (Jython, run with `HEC-HMS.cmd -script …` from the HMS folder,
  analysis names in `names.txt`). The documented scripting API has no depth-area call; the script reaches
  `Project.computeDepthAreaAnalysis(name)` through the `ProjectManager` held in a static field of `JythonHms`.
  One 200-year analysis of 354 points takes about 2 min. Basin 1's runs and results are untouched.
- **Muskingum-Cunge sections** (engineer's rule): n 0.1 on every reach, as in Basin 1. Channel reaches (81, the ones
  that follow a CH feature) are trapezoids with side slope 1V:3H and the bottom width that puts the 200-year
  depth-area flow at 2 m normal depth (Manning, reach energy slope). First pass computed with the earlier
  placeholders, widths written by `scripts/size_reaches.py` (`output/hms/Basin_2_reach_sizing_Q200.csv`), then all 13
  analyses recomputed. Natural plain reaches keep their DEM sections, Basin 1 reaches their own.
  **Consequence of the rule**: the main FP channels below the dams carry 2 500–5 900 m³/s and come out 1–6 km wide
  (26 reaches over 1 km; the two short reaches at the coast with the 0.0005 slope floor hit the 6 km solver cap).
- Results: `scripts/extract_b2.py` → `output/hms/results/basin2_peak_flow_volume.xlsx` (peak and volume at every
  element's own analysis point, 13 return periods; sheets per element type).

## Basin 3 = Basin 2 + the eight dam reservoirs (2026-10-05)

Basin 2 stays without reservoirs. Basin 3 is a copy with a **Reservoir element 150 m downstream of each dam junction**
(junction → reservoir → the old downstream reach): Modified Puls, routing curve Elevation-Area-Outflow, initial
elevation = reservoir bed, syntax copied from the project's Qashab model.
- **Elevation-area** (`scripts/hypsometry3.py`, `output/reservoirs/EAV_<dam>.csv`): pond at level z = cells of the
  10 m DEM below z, 4-connected to the dam axis, inside the union of the dam's D8 catchment and the crest-contour
  polygon (crest contour from `Crest_Level.shp` closed by the dam axis from `Dams updated.shp`, both in
  `…8 Channel Design\SHP\Block 04 Dams`). 0.5 m steps from bed to crest, extended to crest + 5 m for overtopping.
  Volumes at FSL are 2–6% below the capacities in `Block 4 Dams Details.xlsx` (`output/reservoirs/summary.csv`).
  The catchment alone misses most of Hawasinah EX (29 instead of 81 Mm³) because the 9.8 km embankment impounds
  ground that drains elsewhere on the DEM; the crest polygon fixes that.
- **Spillway rating** (`output/reservoirs/reservoirs_added.csv`): Q = C·L·H^1.5 above FSL with C 2.1 and the
  spillway length L from the dams shapefile/sheet, plus dam-crest overtopping Q = 1.7·L_crest·(z − crest)^1.5 above
  crest level, tabulated as a Stage-Flow table. This is the broad-crested weir HMS would compute inside a spillway
  structure; the structure form of the element was not used because no example of its file syntax was available.
- Tables live in the project DSS (`Elev-Area <dam>` ELEVATION-AREA in m/m², `Elev-Dis <dam>` STAGE-FLOW in m/m³/s)
  and in `HEC_HMS_Block_04.pdata`; met models linked to Basin 3; runs `FM <rp> B3`, analyses `DA <rp> B3` with all
  362 elements as analysis points, computed headless (`scripts/write_reservoirs.py`, `hms_compute_all.py`).
- **Channel sections in Basin 3** are sized separately, with the same rule (n 0.1, 1V:3H, 2 m depth) but on the
  reservoir-routed 200-year flows (`output/hms/Basin_3_reach_sizing_Q200.csv` = the applied table): pass 1 = the 13
  analyses computed with Basin 2's sections (kept as `results/*_pass1_B2sections.*`), widths derived from them and
  written to `Basin_3.basin`, then the 13 analyses recomputed (final results, 2026-10-05 late evening). Below
  Hawasinah EX the 200-year flow falls from 5 900 to about 180 m³/s and HAW-R21 from 2 308 to 66 m bottom width;
  6 reaches remain over 1 km.
- **Error found and corrected the same day.** The first version of `size_reaches.py` read `Basin_3.basin` but wrote
  the result to `Basin_2.basin` (hard-coded output name). For about ten hours the project's `Basin_2.basin` was a copy
  of Basin 3 (header "Basin 3", eight reservoirs, Basin 3 widths) while Basin 3 kept Basin 2's widths; the engineer
  noticed HAW-R21 at 2 308 m in Basin 3. Fix: Basin 2 restored from `_backup_before_reservoirs_20261005_125741`
  (byte-identical to the file that produced the Basin 2 results, HAW-R21 2 308.2 m, no reservoirs); Basin 3 re-sized
  (HAW-R21 66.1 m, all 81 channel widths verified against the table); the 13 Basin 3 analyses recomputed. The
  wrong-file versions are kept in `../../model/_sizing_backups/`. Lesson: after writing any basin file, check the
  header line, the element counts and one known value in **every** basin file of the project, not only the target.
- **Sensitivity to the sections** (`results/basin3_peak_flow_volume.xlsx` vs `*_pass1_B2sections.xlsx`): reservoir
  outflows and levels unchanged; the narrower channels attenuate less, so the 200-year peaks rise by 7–10% at HAW-O1,
  SAK-O1 and SHA-O5 and by up to 33% on SAR-R12/R13 (9 of 115 reaches change by more than 5%). A second sizing pass
  on the new flows (`results/Basin_3_reach_sizing_Q200_pass2_check.csv`, **not applied**) would widen 8 of 81 channel
  reaches by more than 10% (SAR-R12/R13 +34%, SHA-R48…R52 +14–16%, SAK-R21 +9%); the rest stay within a few %.
- Results: `output/hms/results/basin3_peak_flow_volume.xlsx`; `dams_inflow_vs_outflow.csv` and
  `outfalls_B2_vs_B3.csv` from `scripts/compare_b2_b3.py`; `reservoir_max_elevation.csv` from
  `scripts/reservoir_levels.py`.

## Validation performed

- On Basin 1's own terrain, the same pipeline reproduces all 9 dam catchments within 0.8 km² and **24 of 32
  Basin 1 subbasin polygons exactly** (overlap ≥ 0.995; `output/validation/compare_basin1_on_basin1_terrain.csv`).
  Flow path length, 10–85 slope and CN match HMS to 3 significant figures on those; recomputed lag equals Basin 1's
  (e.g. S6 126.1 vs 126, S14 138.7 vs 139, S26 148.8 vs 148), which confirms Basin 1 used the same Kirpich formula.
  The 8 non-matching subbasins are Basin 1 manual merges/deletions (S15 deleted into S16; J6/J20/J21 single-subbasin
  junctions; Shafan 08 and Sakhin 04 local edits).
- Basin 2 topology check (`scripts/validate_basin.py`): no duplicate names, every downstream target exists,
  every reach has exactly one upstream junction, no cycles, 13 terminals all sea outlets.

## Placeholders and limits — read before using results

- **Channel reach sections are placeholders**, not design: Muskingum-Cunge trapezoid, n 0.035, bottom width
  15 m (FP CH) / 8 m (Sw M CH) / 4 m (Sw S CH), side slope 2. Replace with the Block 6-type sections before
  quoting routed flows.
- **Natural plain reaches (18)**: n 0.1 (Basin 1 style). Trapezoid from DEM cross-sections every 100 m
  (`scripts/add_reach_geometry.py`, results in `output/hms/Basin_2_reach_geometry_and_sections.csv`): bottom width =
  median width 0.5 m above the thalweg (40–60 m), side slope from the width 1.5 m above the thalweg, clamped at
  1V:25H (the plain wadis are 110–340 m wide at 1.5 m, so the clamp binds on all 11 resolved reaches). 7 reaches
  where fewer than half the sections resolved keep the 100 m / 1V:5H placeholder.
- **Reach geometry**: the 60 new reaches have their stream polylines in `Basin_2.sqlite` table `reach2d`
  (matched by reach name, which is how Basin 1 stores them), so they draw along the wadi/channel instead of as
  straight lines. Added 2026-10-05 after the first HMS check.
- Energy slope floored at 0.0005 on 3 short plain reaches whose DEM slope was ≤ 0 (incl. R149 below Hawasinah EX).
- HMS re-saved `Basin_2.basin` on first open (dropped the `Downstream: None` lines of the 13 outlets, snapped 5
  reach start points to the exact Basin 1 junction coordinates, added computation-point stubs). That HMS-saved
  version is now the source copy in `output/hms/`; the pre-HMS file is kept as `Basin_2_pre_hms.basin`.
- Shortest new reach is 38 m, smallest subbasin 0.005 km²; harmless but may be merged by hand.
- `Basin_2.sqlite` is a copy of Basin 1's with the new subbasin polygons, centroids, outlets, longest flow paths and
  statistics appended (reach2d not populated). HMS may rewrite it on first save.
- CH features 36–52 (type None) and 35 (FP D) are mountain burn lines, not channels; WALL = dykes.
- Not run in HMS. Open the project, select Basin 2, check it loads and that the schematic looks right, then create
  runs (the 13 FM/DA precipitation sets exist; analysis points for the DA runs must be added for the new elements).

## Files

| Path | Contents |
|---|---|
| `output/hms/Basin_2.basin`, `Basin_2.sqlite` | the basin model (same copies installed in the HMS project) |
| `output/hms/Basin_2_new_elements.csv` | every new subbasin/reach with all parameters and the derivation columns |
| `output/hms/Basin_2_review.gpkg` | QGIS review: `subbasins_new`, `reaches_new`, `stream_links_new`, `junctions`, `subbasins_basin1_carried_over` |
| `output/links.csv`, `output/review.gpkg` | raw delineation of the whole DEM before assembly (internal names) |
| `output/dam_catchment_comparison.csv` | table above |
| `output/validation/` | pipeline vs Basin 1 on Basin 1's terrain |
| `output/terrain/reconditioned_CH_WALL_10m.tif` | the reconditioned DEM (fill/D8/accumulation can be regenerated with `build_recond.py`) |
| `output/ch_topology.csv` | CH features: flow direction, where each ends (sea / other channel) |

## Rerun

```
python scripts/build_recond.py 1.0,2.0,3.0     # -> <cwd>/new/{reconditioned,fill,d8,acc}.tif
python scripts/delineate.py new                # -> new/out/links.csv, review.gpkg, dam_catchment_comparison.csv
python scripts/write_basin.py new <HMS project folder> [--install]
python scripts/validate_basin.py new/out/hms/Basin_2.basin
```
Requires rasterio, geopandas, shapely, pyproj, numba, scipy, whitebox (2.4), pandas. Paths to the CH/WALL
shapefiles, the HMS terrain and the CN grid are set at the top of each script.
