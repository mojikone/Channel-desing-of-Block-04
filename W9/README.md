# W9 — his second review round: labels, culverts with the bypass, the 0.5 m ground, GIS and KMZ second generation, the bypass package, reports R6 and stormwater R1

**Live document (W9, 2026-10-14).** His list after the W8 submission, every item DONE unless marked open; the
submission folder `Block 4\Deliverables\2 Submission 13102026` updated in place and mirrored to the server
(`W:\…\18 Channel Design\Hydraulic\Block 4\2 Submission 13102026`, robocopy /MIR /XO).

## What changed and why (his comments, in his order)

| His comment | Done | Where |
|---|---|---|
| Labels of segments and manholes: only the SGLabel | the reach panels of both reports label the reaches with the full SGLabel; the QGIS project labels reaches and points with his own expressions (SGLabel, width, slope; SGLabel, wadi depth, raise); the KMZ reach labels carry the SGLabel and the size | `scripts/66_maps_qgis_r5.py`, `91_submission_qgis.py`, `80_kmz_w9.py` |
| Culverts for the channels ending just short of the Coastal Road (HAW-CH7-SS, SHA-CH3-SM, SAK-CH3-SM, SAK-CH5-SS) | the crossing set at the nearest point of the road with the last reach's width, depth, slope and flow (ends 5 to 101 m short) | `scripts/71_culverts.py` (END_RADIUS 150 m, outfall channels only) |
| Culverts for the bypass | the 17 crossings of the planned North Batinah Bypass, corridor 45 m (as the Highway; assumption, the bypass section is not designed yet) | same |
| Bypass: the nine channels starting right downstream (his list) | a culvert under the bypass at the channel start, sized on the first reach (starts 6 to 45 m from the bypass; SAK-CH4-SS carries no modelled inflow at its start and takes the minimum section) | same (START_AT_BYPASS) |
| **No mention of the gap between a channel end or start and its culvert** (his instruction, 2026-10-14 02:30) | the two sentences removed from the culvert section of both reports; the delivered culvert CSV and the crossings GeoPackage go out without `end_short_m` / `start_short_m` / `existing_dist_m` and `extended` / `start_short`; the bypass culvert workbook without its "Channel starts downstream of the bypass" column and note. The distances stay in `culverts/culverts_proposed.csv` and `crossings.gpkg` (internal) | `report/rpt_r4.py`, `scripts/90_submission.py` (`cp_csv_drop`, `cp_gpkg_drop`), `scripts/85_bypass_flows.py` |
| Bypass road design package | folder `09 Bypass road design package` in the submission: the HEC-HMS model (Basin 6 results), the layers (channels and dykes, reaches with the sizes of all return periods, extents, dyke extent, design points, the bypass alignment), the Civil 3D drawing with every channel's profile view showing the existing ground, the invert profile with the grade in percent (the firm's "ARJV_ Percent Grade" line labels), the crown profile and the design point annotations of W6, the workbook of peak flows and volumes of the 13 return periods with the 48-hour hydrographs at the 26 crossings (the HEC-HMS junction feeding the channel just upstream, dams in place, charts as the dam workbook), the workbook of the culverts under the bypass | `scripts/85_bypass_flows.py`, `bypass/civil3d/build_profiles.cs` (run through the Civil 3D scripting bridge on the copy of the W6 drawing; the GDP profiles erased in the copy, 251 PVIs, the view bands re-pointed; dyke views untouched) |
| QGIS: ticks perpendicular | marker rotation `180 - angle` (clockwise) on the station layers | `91_submission_qgis.py` |
| QGIS: existing culverts are lines | line symbology (they are 1 662 LineString barrels of the inventory; 346 on the plain) | same, and the KMZ |
| QGIS: dyke extent | 15.5 m each side of the dyke line, as the fill-channel allowance (embankment 11.5 + road 4), assumption stated | `scripts/82_segments_rp.py` → `gis/dyke_extent.shp` |
| QGIS: his point style, his reach labels | the QML saved from his open project (`gis/qml/design_points_his.qml`, `segments_his.qml`) applied; the reach label expression re-pointed at the span/slope fields of the all-return-period layer | `91_submission_qgis.py` |
| QGIS: red outfalls | rule renderer and red labels where the invert lies below the existing level | same |
| KMZ: labels disturbing | every label in a Region (appears when zoomed in), smaller; names along the alignments at the midpoint; bed fill only, corridor outline only; reaches with size; dam names white; design points 0.35 scale without label; culverts as circles labelled with the size; the HEC-HMS model (subbasins, reaches, junctions with popups of all return periods, junction labels = Q200); all-in-one rebuilt | `scripts/80_kmz_w9.py`, `84_hms_kmz.py` → `kmz/` |
| Tables: the dam workbooks, one BOQ and cost workbook | copied; `Block 04 - BOQ and cost estimate.xlsx` with every cost a formula on a quantity and a rate (sheet Rates, blue on yellow), recalculated in Excel, no error cells | `scripts/87_boq.py` → `tables/` |
| Channel terrain: one tif, the W4 ground | the Channel Terrain tool re-run on the 0.5 m project terrain (his local copy `Hydraulic\Terrain\GGC_4_MERGE_HDSM.tif`; it equals the server DTM used by W4, median difference 0.00 m) → `terrain/Block04_channel_surfaces_2m.tif` and `Block04_terrain_with_channels_2m.tif` (the ground over the corridors + 100 m with the channels cut in), per channel surfaces and ground | `scripts/73_terrain_w9.py` → `volumes/`, `terrain/` |
| GIS: sizes of all return periods on the segments; extents per return period | `gis/segments_all_rp.gpkg/.shp` (span, rise, size, flow, slope for 2 to 500 years), `gis/extents/extent_<rp>yr.shp` (bed + corridor, field kind) | `scripts/82_segments_rp.py` |

## The numbers that moved

- **Culverts**: 61 crossings (Highway 21, Coastal Road 14, Bypass 26), 29.92 million OMR (W8: 31 crossings, 19.51).
- **Earthworks on the 0.5 m ground**: cut 34.87 Mm³, fill 1.75 Mm³, clearing 17.52 km² (W7/W8 on the 5 m model: 18.55, 5.15, 18.37). The 0.5 m
  terrain sits 0.4 to 0.7 m above the 5 m model over the channel footprints, so the extra cut is real and the 5 m figures were low.
  Channel construction 93.4 million OMR (was 73.0). Scheme total 299.6 million OMR (was 268.8); stormwater works 168.2 (was 154.7).
- Reports: R6 (109 pages) and stormwater R1 (67 pages), gates PASSED; the culvert section rewritten for the bypass. Second build of both
  (02:40): no gap sentences, the cut column of the channel quantities table widened (the bold total wrapped), the quantities text names the
  0.5 m terrain model (the first build still said 5 m).
- Civil 3D bypass drawing: the second band slot of every channel profile view points at the invert profile (the W6 views had the existing
  ground in both slots); the dyke views are untouched.

## Scripts (W9/scripts, in the order run)

`82_segments_rp.py` (sizes per return period, extents, dyke extent) · `84_hms_kmz.py` (HEC-HMS KMZ) · `71_culverts.py --radius 10`
(W9 rules) · `73_terrain_w9.py` (0.5 m ground, merged rasters) · `80_kmz_w9.py` (KMZ v2) · `85_bypass_flows.py` (bypass workbooks,
hecdss) · `87_boq.py` (BOQ) · `66_maps_qgis_r5.py` (R6 maps: `M14_reach_*`, `M19_culverts`; with MAPS_DIM_FP=1 MAPS_OUT=png_sw_r1
for the stormwater report) · `74_cost_dashboard.py`, `report/charts_b4.py c15` (both modes) · `report/build.py --pdf`,
`report/build_sw.py --pdf` · `90_submission.py` · `91_submission_qgis.py` · `bypass/civil3d/build_profiles.cs` (Civil 3D) ·
`scripts/sync_deliverables.py --only 17` · robocopy to the server.

## HEC-RAS check: the conduit export with the designed sizes (2026-10-14, after the submission)

His SewerGEMS GUI export of the R9 conduits (`SHP\from SewerGEMS\Channels.shp` in the model share) shows SPAN = 10 for all 212
conduits and SIZE = a GUID. SPAN is the conduit's own stored span, which SewerGEMS never updates for catalogue conduits (the design
assigns a catalogue item), and SIZE is that item's identifier; the designed size lives behind the catalogue reference and is resolved by
class + item (the W6 trap). `scripts/88_hecras_conduits.py` joins the sizes resolved in W7 (200 yr, `W7/gis/sewergems_200yr_R9.gpkg`)
and W9 (all return periods, `gis/segments_all_rp.gpkg`) onto his geometry by the conduit label: 212/212 matched, his inverts agree within
5 mm, slope and rise exactly, length within 5 cm. Output `Channels_R9_designed_sizes.shp` + `_README.txt` beside his export (his file
untouched; the share takes new files only) and in `gis/hecras/`. Fields: nodes, length, inverts, slope, shape and class, width / depth /
size text / flow / velocity / flow depth at 200 yr, and W / D / Q / S per return period. Dam-controlled reaches carry zero flow in the
scenarios where the dam stores the whole event (for example HAWCH1-C5: 0 up to 100 yr, 174 m³/s at 200 yr, 1 576 at 500 yr).

## Superseded by W10 (2026-10-14, his review of R6)

W10 holds the live reports (R7, stormwater R2), culverts, maps, KMZ, BOQ, bypass workbooks and submission scripts. Found in W10: **the W9
map renders never ran** — `scripts/66_maps_qgis_r5.py` asserts on `gis/GCA_RENN.gpkg`, which lives in `W8/gis` and was not copied into
W9, so the script stopped before rendering and every PNG in `maps/png_r6` and `maps/png_sw_r1` is the W8 file (figure 41 of R6 shows
31 crossings, the reach panels the W8 labels). R6 and stormwater R1 are superseded; the W9 KMZ was built before the final crossing file.

## Open

- WhatsApp: nothing sent from W9 (he did not ask this round).
- The bypass corridor width (45 m) and the dyke extent (15.5 m each side) are stated assumptions; the stormwater report R1 and the channels report R6 are first revisions of this round, to be read.
