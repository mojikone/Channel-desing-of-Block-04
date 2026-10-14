# W10 — his review of R6: the maps really re-rendered, existing culverts within the corridor extent, the dashboard bars, the bypass QGIS project; reports R7 and stormwater R2

**Live document (W10, 2026-10-14, after the R6 issue of the same night).** His comments on R6 and what was found behind them. W9 is
superseded for the reports, culverts, maps, KMZ, BOQ, bypass workbooks and the submission scripts; the W9 terrain, quantities, per-return-period
layers and the Civil 3D bypass drawing stay the sources (the W10 scripts point at `W9/` for them).

## His comments and the findings

| Comment | Finding and fix | Where |
|---|---|---|
| Figure 41 is old: not all culverts of the Coastal Road and the bypass | True, and wider than that: **every map PNG in W9 was byte-identical to W8**. The maps script asserts on `gis/GCA_RENN.gpkg`, which lives in `W8/gis` and had not been copied into W9, so every W9 render stopped before drawing and the report quietly used the seeded W8 files (figure 41 with 31 crossings, the reach panels with the W8 labels). W10 carries the file; figure 41 (61 crossings, the bypass dashed, the data box per road), the roads map and the four reach panels re-rendered for both reports | `gis/GCA_RENN.gpkg`, `scripts/66_maps_qgis_r5.py` → `maps/png_r7`, `maps/png_sw_r2` |
| Table 26: the existing culverts must be those within the channel corridor extent at the road, projected onto the road for the channels that do not reach it | The crossing footprint = the channel axis buffered by (bed width / 2 + 15.5 m) ∩ the road strip (corridor width); for the four channels ending short of the Coastal Road and the nine starting below the bypass the axis is the line from the channel end (start) to the crossing point, extended across the road. Every inventory structure (one row = one structure, cells x W x H) intersecting the footprint (+5 m) is listed; several per crossing are joined. 21 crossings with existing structures (W9 rule, 10 m radius: 10). The removal of the existing structure enters the culvert cost: culverts 30.73 mOMR (was 29.92) | `scripts/71_culverts.py` → `culverts/` (gpkg layer `crossing_footprints` for QA) |
| Executive summary up to date with the costs | It was already computed from the facts module (299.6 in R6); now 300.4 and the existing-structure sentence is computed too (`existing_claim`): "only one of the existing structures reaches the width of its channel and none its depth" (SHA-CH8-SS: 9 x 2 x 1 on a 17 m channel) | `report/data_facts.py`, `rpt_front.py`, `rpt_r4.py` |
| All maps, figures, text up to date | Audit before the fixes: maps all stale (above); KMZ built 8 min before the final crossing file (52 of 61 crossings); charts, dashboards, BOQ, bypass workbooks, cost chapter and both summaries current. Everything downstream of the culverts rebuilt in W10 | this file |
| Last dashboard page: channel bars in two colours (construction, land), the total as the only label | Done; the dyke and culvert panels unchanged | `scripts/74_cost_dashboard.py` → `report/img/D2_dashboard_items*.png` |
| A QGIS file for the bypass road package | `Block 04 - Bypass road design package.qgz` inside the package: bypass alignment and its 26 culverts (size labels), the two roads, channels and dykes, reaches with his style and the 200-year size labels, design points with his style, bed / corridor / dyke extents, Google background; relative paths. The package also gets the culvert layer and the two roads | `scripts/92_bypass_qgis.py`, `90_submission.py` |

## Second pass the same night: the KMZ extents and the live formulas (his comments of 03:50)

| Comment | Done | Where |
|---|---|---|
| The channel corridor in the KMZ has sharp edges and small gaps at the outer curves; taper upstream to downstream | The extents of step 82 were reach-by-reach flat-capped buffers: a step at every reach limit and a wedge gap on the outer side of every bend between reaches. `82b_extents_taper.py` rebuilds every return period: the bed width equals the designed span at each reach midpoint and varies linearly between consecutive midpoints (constant beyond the first and last); the outline is the union of round-capped buffers of the 5 m centreline segments at the local half-width, which closes every bend and folds a hairpin without artefacts (a first version from quads left a bow-tie at the 137° bend of SAK-CH5-SS). 200-year bed 1,437 ha, corridor 2,123 ha (stepped: 1,398 / 2,076). The KMZ, the GIS extents per return period, the QGIS project and the bypass package all take the tapered layers. The plan-profile sheets keep their own plan-view buffers (W8 pipeline, untouched) | `scripts/82b_extents_taper.py` → `gis/extents/`, `80_kmz_w9.py`, `90/91/92` |
| In all tables and workbooks the formulas must be live inside the cells | Inventory of every client workbook, then: **BOQ** rewritten so the dyke quantities follow from length and height (typical fill section), the culvert quantities from cells, width, depth and length, every cost from a rate, a catchment column on each sheet and a by-catchment block on the summary (2,663 formulas, 0 errors, total 300.38 mOMR unchanged). **Bypass culvert workbook**: cells from the bed width (plus a column for the cells the headwater check added), overall width, size text, every quantity and cost on a rates-and-constants sheet (964 formulas; the headwater check stays a value, it is iterative). **Bypass flows workbook**: the peaks and volumes on the crossings sheet and in every chart legend are MAX / SUM×300 s formulas on the hydrograph sheets, written in full (no 48 h cut; 1,625 formulas). **Channel design tables** rebuilt by `93_design_tables.py`: the size texts, the per-channel aggregates (SUMIF, MAXIFS, MINIFS, INDEX/MATCH, LOOKUP), the size inventory (COUNTIFS/SUMIFS), the invert above MHHW, the culvert overall width and headwater ratio, the dyke section quantities and the land-take sums are formulas; measured and modelled values stay values; the cost sheets that duplicated the BOQ as dead numbers are gone (1,222 formulas). Dam workbooks already carried formulas (13,186 / 585); the HEC-HMS peak-volume table is model output only. All four rebuilt workbooks recalculated through Excel and scanned: 0 error cells | `scripts/87_boq.py`, `85_bypass_flows.py`, `93_design_tables.py`, `90_submission.py` |

## Numbers of R7 / stormwater R2

| | R7 (all channels) | Stormwater R2 |
|---|---|---|
| Crossings / with existing structures | 61 / 21 | 49 / 17 |
| Culverts | 30.73 mOMR | 15.2 mOMR |
| Scheme total | 300.4 mOMR | 168.5 mOMR |
| Pages | 109 | 67 |

Channel construction 93.4, land 167.8, dykes 8.4 mOMR unchanged from W9. Gates PASSED on both PDFs.

## Scripts (in the order run)

`71_culverts.py --radius 10` (the radius is no longer used for the existing structures) · `66_maps_qgis_r5.py M19_culverts M05_roads_utilities
M14_reach_HAW M14_reach_SHA M14_reach_SAR M14_reach_SAK` (and with `MAPS_DIM_FP=1 MAPS_OUT=png_sw_r2`) · `74_cost_dashboard.py`,
`report/charts_b4.py c15` (plain and with `REPORT_ONLY=SM,SS DASH_SUFFIX=_sw CHART_SUFFIX=_sw`) · `87_boq.py` + Excel recalculation
(0 error cells) · `85_bypass_flows.py` · `84_hms_kmz.py`, `80_kmz_w9.py` · `report/build.py --pdf`, `report/build_sw.py --pdf` ·
`90_submission.py` · `92_bypass_qgis.py` · `91_submission_qgis.py` · robocopy to the server · `scripts/sync_deliverables.py --only 18`.

## Traps paid for here

- A maps script that asserts on an input stops before rendering and leaves the seeded PNGs in place: compare the PNG hashes with the
  previous iteration after every render (`cmp`/md5), never trust the timestamp of a copied file.
- Git Bash heredocs: `\1`, `\2`, `\0` become control characters inside the text (three paths were corrupted in W9's documents and
  repaired); the W10 patches were written as files and run.
- The culvert inventory has one row per structure (`Num` cells, `Size` = Num x W x H); the W9 grouping by a code prefix would have
  merged neighbouring structures once the footprint grew.
