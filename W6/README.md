# W6 — Channel design points for SewerGEMS (started 2026-10-10, Oman date)

Live iteration. The engineer's channel design method (2026-10-10): the reviewed ground design profiles (W5) drive the
channel slopes; on top of them four kinds of points must be seen on the profiles and in QGIS before the SewerGEMS build:

| Kind | Colour / size (nested so overlaps stay visible) | What it is | Source |
|---|---|---|---|
| Flow points | blue, 7 mm hollow | the HMS points that feed Qp (Basin 3 depth-area results at the element's own analysis point), snapped by the engineer to the GDP breaks | `Hydraulic\SHP\tmp\Qp Vol Block 04.shp` (copy in `inputs/`) |
| Channel ends on a receiving channel | red, 5 mm | a channel's end on a higher-class channel (FP > Sw M > Sw S): the receiver's station, its GDP and ground there, the tributary's GDP end elevation, the nearest GDP break of the receiver (merge or new point: the engineer decides on the profile) | geometry of `W5/civil3d/build_spec_w5.json` + `W5/gdp/gdp_reviewed_pvis.json` |
| Fix points | yellow, 4 mm | constraints at OQ pipelines, roads and outfalls: the bed stays at ground, embankments above | `Hydraulic\SHP\tmp\fix points.shp` (copy in `inputs/`) |
| 500 m downstream of a fix point | orange, 3 mm | where the channel returns into cut (not for outfalls) | computed along the channel |

Later, by the engineer: points inside wadis with a defined channel shape (bank elevation as ground; conduit depth
matching the local wadi, 2.5 m standard).

## State (2026-10-10; the table is the first run of the morning, the dated paragraphs below and the final-layers section hold the current figures)

| Step | Script | Result |
|---|---|---|
| Design points | `scripts/31_design_points.py` (ground from the drawing's EG profiles through the MCP) | `output/design_points.gpkg` (4 layers) + CSVs: 76 flow points on channels (11 rows of the file have no geometry) carrying the full attribute table of `Qp Vol Block 04.shp` (32 fields, same names) plus Channel / Station / StaLbl / Ground / GdpZ / SnapDist (engineer, 2026-10-10), **22 channel ends on receivers** (5 flagged LOW: the tributary's reviewed bed is 0.17–0.84 m below the receiver's GDP; 2 within 60 m of an existing break), 54 fix points (all within 60 m of a channel), **28 downstream points**: 39 computed (15 outfalls excluded) minus the 11 the engineer declared redundant on 2026-10-10 (`inputs/downstream_exclusions.json`, matched by fix number and channel, station labels verified) |
| Markers in the drawing | `scripts/32_markers.py` + `cs/40_profile_markers.cs` | 202 markers in every profile view and in plan, layers W6-PT-FLOW / -JUNCTION / -FIX / -FIX500 (nested radii 24/17/12/8 m), drawing saved |
| QGIS | `gis/*.qml` | group "W6 design points" (4 layers) added to the engineer's open project |
| New catchment | `scripts/30_basin5_build.py` | Basin 5 (set to Metric): subbasin **SHA-S51** (16.438 km², CN 86.3, Ia 8.04 mm, longest flow path 10 094 m, S10-85 0.0105, lag 64.7 min) → outlet junction **SHA-J52** at 495922.5, 2651832.5; `Basin_5.sqlite` with polygon, centroid, outlet, flow path; runs FM <rp> B5, analyses DA <rp> B5, met models extended; parameters in `hms/basin5_parameters.json`; backup `_backup_before_basin5_<stamp>` in the HMS folder |
| Compute | `scripts/34_hms_compute_b5.py` (Jython, HEC-HMS.cmd -script from a path without spaces) | 13 analyses in 19 s, `hms/34_hms_compute_b5.log`, `DA_<rp>_B5.dss` in the HMS folder |
| Extract | `scripts/35_extract_b5.py` | `hms/basin5_peak_flow_volume_long.csv`: SHA-S51 Q2 10.8, Q10 105.9, Q100 248.5, **Q200 313.4**, Q1000 523.0, QPMP 1436.8 m³/s; V200 3.34 Mm³ |
| Flow file update | `scripts/33_update_qp.py` | done 2026-10-10 01:24: SAR-S11 (Q200 335.8) and HAW-S14 (Q200 25.2) from the Basin 3 results, "SHA-CH13-SS GB0" renamed **SHA-S51** (Q200 313.4), 13 return periods each, type Subbasin, downstream element; the engineer's file rewritten in place (its original kept as `Qp Vol Block 04_before_20261010_0122.*`), copy in `output/`. QGIS held a lock on the file: the layer was removed, the file written, the layer re-added with its saved style (`gis/Qp_Vol_Block_04_engineer_style.qml`) into its group "HMS OUTPUT" |

## Junction fix (engineer, 2026-10-10 02:09)

For the 22 channels ending on a receiving channel the GDP end point was set to the receiver's GDP elevation at the
junction station (`scripts/36_junction_fix.py`, `cs/41_junction_fix.cs`): only the last PVI moves, the previous line
stays in the view as a dashed magenta layout profile `GDP <name> (before junction fix)` (new profile style "GDP previous
(dashed)"), receivers adjusted before their tributaries (HAW-CH2-SS before HAW-CH3-SS/HAW-CH6-SS, HAW-CH5-SS before
HAW-CH4-SS, SHA-CH10-SS before SHA-CH9-SS, SHA-CH5-SM before SHA-CH11-SS). Backup first: the drawing as saved at that
moment, written to `W5/civil3d/backup/Block04_Channels_W5_before_junction_fix_20261010_0209.dwg` and since renamed by
the engineer to `W5/civil3d/Backup/10 Block04_Channels_W5_before_junction_fix_20261010_0209.dwg`. Changes
−1.24 m (SHA-CH18-SS) to +0.84 m (HAW-CH5-SS), 17 ends lowered, 5 raised; no last segment became flat or reverse
(`output/junction_fix.csv`, `output/junction_fix_result.json`). Afterwards the GDP files (27), the design points (31:
every junction now has DiffZ 0, no LOW flag) and the markers (32) were regenerated. A second QGIS instance of the
engineer (qgis-ltr-bin, found with `scripts/who_locks.py`) held `W5/gdp/Block4_channel_breaks.shp` and `_segments.shp`
for a while; after he closed it the originals were rewritten (02:13) and the review group points at them again.

Labels of the seven review layers (W5 stations, GDP breaks, GDP segments; W6 flow, channel ends, fix, downstream) are
switched OFF at the engineer's request (2026-10-10) with their settings kept, so he switches them on per layer when he
wants; the QML files carry the off state.

## The W6 point layers are the master (from 2026-10-10 evening)

The engineer edits the flow and fix points on the QGIS layers of `output/design_points.gpkg`. `31_design_points.py`
therefore reads `flow_points` and `fix_points` from that file when it exists (his edits, geometry and attributes), the
source shapefiles in `Hydraulic\SHP\tmp` only when it does not, and copies what it read to `inputs/as_read_<stamp>/`
before rewriting anything. **Incident 2026-10-10 11:10:** the earlier version read the source shapefiles and deleted
the GeoPackage before writing; the engineer's point edits made on the W6 layers that morning were lost (no copy existed:
the snapshot had been refreshed after the rewrite, no journal, no recycle bin). He re-did them afterwards.

Second exclusion list (11 more downstream points) applied the same day: 17 downstream points remain. His profile edits
of the morning changed 9 GDPs (fewer breaks: 228 breaks, 191 segments); two channel ends are again below the receiver's
GDP after his edits (SHA-CH18-SS −0.12 m, SHA-CH20-SS −0.24 m on SHA-CH1-FP), his call.

**Update of 2026-10-10 11:47 (engineer's second profile edit and redone point edits):** 227 breaks / 190 segments; the
design points were read from his edited W6 layers (76 flow features, two of them with their geometry cleared by him:
SAK-J7 and SHA-J24, so 74 flow points remain; 54 fix points, several moved: FIX16, 36, 43, 46, 48 to other stations,
FIX47 from SAK-CH2-FP to the end of SAK-CH1-FP, FIX53 to the start of SHA-CH13-SS); 23 exclusions (FIX53+500 added),
22 matched (FIX47+500 on SAK-CH2-FP no longer exists; its new +500 point sits on the SAK-CH1-FP end, 0.6 m away);
17 downstream points; 189 markers. Four channel ends are below their receiver's GDP after his profile edits
(HAW-CH5-SS −0.22, SHA-CH18-SS −0.12, SHA-CH20-SS −0.24, SHA-CH21-SS −0.31 m), his call. Fix numbers now come from the
layer's `Fix` field, so they survive reordering.

**Update of 2026-10-10 12:34–12:41 (engineer's instructions of 12:20):** the four LOW ends were raised to the receiver's GDP
(`36_junction_fix.py --low-only --suffix " (before junction fix 2)" --tag junction_fix_2`: HAW-CH5-SS +0.224, SHA-CH18-SS +0.124,
SHA-CH20-SS +0.239, SHA-CH21-SS +0.306 m; the previous lines kept as dashed "GDP <name> (before junction fix 2)"; backup first:
`W5/civil3d/backup/Block04_Channels_W5_before_junction_fix_2_20261010_1234.dwg`, 119 MB); all 22 ends now match their receiver
(DiffZ 0). Two more downstream points removed on his list (FIX37+500 SHA-CH9-SS 3+832, FIX38+500 SHA-CH8-SS 3+791): 25 exclusions,
24 matched (FIX47+500 on SAK-CH2-FP no longer exists), **15 downstream points**, 187 markers; 227 breaks / 190 segments unchanged
in count. Then the final layers below were built.

## Final layers for SewerGEMS (engineer's specification, 2026-10-10 afternoon) — `final/`

One point layer and one segment layer, `scripts/37_final_layers.py` → `final/Block4_design_points.shp` (**227 points**) and
`final/Block4_design_segments.shp` (**212 segments**) + CSVs, `merges.csv` (every merged group), `final_summary.json` (counts and
checks); every run also writes a frozen copy `final/frozen_<stamp>/` that is never overwritten (his "backup in one folder"; live:
`frozen_20261010_1241`). His rules, as implemented:

- every design point is in: GDP grade breaks (205 = 227 minus the 22 tributary end PVIs), flow points (74), fix points (54), 500 m
  downstream points (15), channel ends on a receiver (22). A channel end on a receiver is the point that **splits the receiving
  channel** (14 coincide with a receiver break, 8 are new split points); the tributary's own end PVI is not a point. A flow or fix
  point on a tributary's last 10 m belongs to that junction point and its Q/V go there (7 moved: HAW-J3, HAW-J4, SAK-J18, FIX47,
  FIX47+500, SHA-J44, SHA-J39 — the first run had made them points of their own and produced zero-length last segments);
- no duplicates: points within **10 m** along a channel are one point, placed at the GDP break when the group has one, otherwise at
  the channel end, then the fix point, the flow point, the downstream point (126 merged groups; 5 spread over more than 1 m, the
  largest 8.1 m: the HAW-CH3-SS end onto HAW-CH2-SS GB1 at 1+516). The tolerance comes from the data: 142 gaps under 4 m, one of
  8 m, none between 8 and 60 m;
- point fields: Label `<channel>-N<nn>` from upstream, Channel, Class, Station, StaLbl, X, Y, Ground (the drawing's EG profile,
  samples cached in `output/eg_samples.json`), GdpZ (GDP of the channel the point is on), the five kind fields **Flow / Fix / Fix500 /
  GDP / CHend** (the matched identity, empty otherwise), FixType, `name` and the 26 Q*/V* fields of the flow layer, Members (all
  merged members), Flag;
- segments `<channel>-C<nn>`: the centreline between two consecutive points with the end vertices set equal to the point
  coordinates (checked: 0 mismatches); a tributary's last segment ends on the receiver's junction point (one jog of 8.1 m,
  HAW-CH3-SS). Fields Label, Channel, Class, Seg, FromNode, ToNode, ToChannel, FromSta, ToSta, Length, USInv, DSInv (the channel's
  own GDP at both ends; at a junction the receiver point's GdpZ can differ by the receiver's slope over the merge distance: 5.6 cm on
  HAW-CH3-SS, 0.7 cm on SAR-CH3-SS), Slope, Flag; no flat or reverse segment, shortest 85.7 m; 53 FP / 68 SM / 96 SS segments,
  56.0 / 68.7 / 96.6 km.

QGIS: "Design points, all kinds (W6, final)" (rule-based nested circles: flow blue 7 mm hollow, channel end red 5, fix yellow 4,
downstream orange 3, GDP grey 2; `gis/design_points_final.qml`) and "Design segments between points (W6, final)" (by class,
`gis/design_segments_final.qml`) in the group "W6 design points", labels off. Re-run after a profile or point edit: remove the two
final layers (QGIS locks the shapefiles), then 27 → 31 → 32 → 37 → 38, re-add; `--merge-tol` changes the 10 m.

**Update of 2026-10-10 13:03 (engineer's instructions of about 12:55):** he moved HAW-CH2-SS GB1 onto the junction of HAW-CH3-SS
in Civil 3D (now 1+508, GDP 32.63 = the tributary's end: no jog left, the largest merge spread is 3.3 m); FIX47 is a fix for
SAK-CH2-FP and needs no +500 point (its exclusion entry re-pointed to SAK-CH1-FP 12+467, where the point was computed: 14
downstream points, 186 markers); the SewerGEMS names were added as new fields with every existing field untouched: points
`SGLabel` = `<GCA><CH n>-<nn>` (HAW-CH7-SS-N01 → HAWCH7-1; the channel number is unique inside a GCA, so the class suffix can
go), segments `SGLabel` = `<GCA><CH n>-C<nn>` with `SGFrom` / `SGTo`; the two QML label expressions use them.
`scripts/38_sg_labels_markers.py` writes every point's SewerGEMS name into the drawing (circle r 4 m, the name below the point, in
every profile view and in plan, layer W6-PT-SGLABEL; `cs/40_profile_markers.cs` now clears only the layers named in ERASE_KINDS, so
the design-point markers of 32 and the names of 38 coexist). Drawing saved 13:03; live frozen copy `final/frozen_20261010_1303`.

## Wadi depth at the design points (engineer's method, 2026-10-11) — `wadi/`, prototype on HAW-CH1-FP

`scripts/39_wadi_depth.py --channel HAW-CH1-FP` (also `--points SGLABEL[,..]`, `--all`): at each point a cross section perpendicular
to the channel is cut from the design terrain `GGC_4_MERGE_HDSM.tif` (0.5 m hybrid DSM on the W: server, read only, about 2 s a
point) and the wadi depth = lower bank top − bed is reported, so that where a point lies in a wadi bed the design ground can be
raised to the bank (bank elevation as ground, conduit depth = wadi depth). Parameters agreed on 2026-10-11: half-width FP 300 m
(HAWCH1-8 is 200 m wide, SAKCH2-8 300 m), SM 100 m, SS 60 m; bed = lowest ground within 30 m of the centreline; a wadi needs
0.5 m. Method: objects narrower than 30 m and more than 1.5 m above the opened profile (walls, roofs, trees) are removed and
bridged, then a 5 m median; bank top per side = the end of the first rise ≥ 0.5 m above the bed (a crest dropping ≥ 0.2 m within
5 m, or a flattening: < 2 % over the next 20 m with no rise over 0.3 m); a candidate less than 1.5 m above the bed is a bench,
not the bank, when a steeper rise (1 m within 15 m) follows within 50 m (this rule took HAWCH1-6 from 0.66 to 3.02 m and
HAWCH1-7 from 0.51 to 3.40 m); the lower bank top is the bankfull level; WadiClass none / shallow (< 1 m) / braided (a second
low beyond the bank) / clear. The plot layer `LandUSE_block4.shp` offered as a building mask is a cadastral grid (516 of the
600 m of the calibration section lie inside "existing" plots), so it is only counted (PlotsM). Outputs: `wadi/<tag>_wadi_points.shp/.csv`
(BedZ, BankLZ / BankRZ with offsets and how they were found, BankZ, BankSide, WadiDepth, WadiClass, BankMinGdp, GroundPt = DSM
at the point, flags), `<tag>_wadi_sections.shp` (the section lines, left end first, left = looking downstream), `<tag>_sections.png`
(one panel per point: raw and processed profile, removed objects in pink, bed, bank tops, lower bank dashed, GDP), `wadi_parameters.json`.
HAW-CH1-FP (8 points): HAWCH1-1 to -4 no wadi or 0.5–0.6 m in undulating ground (flagged), HAWCH1-5 0.72 m shallow swale,
**HAWCH1-6 3.02 m, HAWCH1-7 3.40 m, HAWCH1-8 1.95 m**. Calibration SHACH1-12: 4.66 m on the perpendicular section; the
engineer's 3.2 m came from an oblique line that crossed the left bank further downstream, where the ground is lower. QGIS group
"W6 wadi depth" (sections and points of HAW-CH1-FP and of the calibration point, labels off). Next: his verdict on the rule, then `--all`.

**Update of 2026-10-11 (Hawasinah run, engineer's verdict on the prototype):** HAWCH1-1 to -4 lie in a plain and are no wadi, so the
classes became: none = depth under 0.5 m, or under 1.0 m with a second low beyond both banks or the bed at the edge of the 30 m
window (WadiDepth and Raise 0, the Civil 3D ground stands); shallow = 0.5–1.0 m with one low; clear ≥ 1.0 m; braided = ≥ 1.0 m
with a second low beyond a bank. **Raise = lower bank top − GDP at the point**, floored at 0. When no bank top lies within the
class half-width the search goes on to 300 m ("beyond W" flag). **The design surface is the DTM, not the hybrid DSM:** the W4
README records the Civil 3D strips as cut from `GGC4_DTM_GMAP_NSA.tif`, and at six checked points the DTM equals the EG profile
to 0.01 m while the HDSM differs by up to 1.1 m (HAWCH2-8: EG 7.23, DTM 7.24, HDSM 6.12); the engineer's statement of the morning
("cut from GGC_4_MERGE_HDSM") does not hold. `39_wadi_depth.py` therefore reads the DTM by default (`--raster hdsm` runs the DSM
for comparison, tag suffix _HDSM, never fed into the final layer). Hawasinah, 34 points on the DTM (`wadi/HAW_*`): **5 clear**
(HAWCH1-6 2.98 m, HAWCH1-7 3.07, HAWCH1-8 2.09, HAWCH2-6 2.53, HAWCH7-4 2.48), 18 shallow, 11 none; against the HDSM run 2 class
changes (HAWCH2-1 braided 1.0 m → none, HAWCH7-3 clear 1.55 → shallow 0.58) and 4 depths differing by more than 0.3 m.
`wadi/wadi_results.csv` accumulates the DTM results by SGLabel and `37_final_layers.py` joins **WadiDepth, WadiClass, BankZ, Raise**
into `final/Block4_design_points.shp` (empty where not yet run; WadiDepth sets the SewerGEMS library depth). Panels per channel
`wadi/HAW_sections_<channel>.png`; QGIS: "Wadi sections, HAW (W6)" and "Wadi depth at points, HAW (W6)" in the group "W6 wadi
depth" (the HAW-CH1-FP prototype layers removed, their files kept but superseded). Next: `--gca SAK`, `SAR`, `SHA` on his go.

**Update of 2026-10-11 (all four catchments):** SAK (32 points), SAR (28) and SHA (133) run on the DTM; `wadi/wadi_results.csv`
carries all 227 points and the final point layer has WadiDepth / WadiClass / BankZ / Raise everywhere (its QGIS layer labels
SGLabel / D: depth / R: raise, stacked, at the engineer's request). Totals: **52 clear, 7 braided, 109 shallow, 59 none**; raise
mean 1.53 m for clear and braided (max 4.54 m at SAKCH1-7), 0.45 m for shallow; 16 wadi points have the GDP already above the
lower bank (raise 0). SHACH1-12 on the DTM: 3.27 m, the engineer's 3.2 m calibration that the HDSM had put at 4.66 m. 108 points
needed the search beyond the class half-width (mostly SS channels in Shafan, where 60 m is tight) and 12 found no bank top within
300 m on one side (flagged, maximum used). Per catchment: `wadi/<GCA>_wadi_points.shp/.csv`, `<GCA>_wadi_sections.shp`,
`<GCA>_sections.pdf` (one page per channel; HAW has PNGs only) and the PNGs; QGIS: sections and points of every catchment in
"W6 wadi depth". Next (his): review, then the ground raise and the SewerGEMS import.

**Fix points (engineer, 2026-10-11 afternoon):** at a fix point the bed stays on the GDP and the embankment is the library depth
(2.5 m as standard, more where the wadi downstream is deep), so **Raise is 0 at every fix point** while WadiDepth, WadiClass and
BankZ are kept for the library choice; `39_wadi_depth.py` applies it from the `Fix` field of the final layer and flags "fix point
FIXn: bed fixed at the GDP, no raise (bank x m above GDP)". All four catchments re-run: 54 fix points at raise 0, 44 of them
with a wadi (the deepest SHACH6-7 FIX20 3.67 m, SHACH13-1 FIX53 2.74 m, SHACH1-13 FIX17 2.66 m, HAWCH1-8 FIX7 2.09 m); 114
points keep a raise above 0 (mean 0.91 m); classes unchanged (52 clear, 7 braided, 109 shallow, 59 none).

**Fix points, second instruction (engineer, 2026-10-11, superseding the zero):** the raise at a fix point is the library
(embankment) depth above the GDP bed: **2.5 m as standard, 3.0 m at SHACH1-13 only**, because the segment from SHACH1-12 is the
only one that can take a deeper library (`inputs/fix_raise.json`: default and per-point overrides; `39_wadi_depth.py` reads it
and flags "fix point FIXn: raise = library depth x m above the GDP bed (bank ±y m vs GDP)"). All four catchments re-run and the
final layer rebuilt: 53 fix points at 2.5 m, SHACH1-13 at 3.0 m; every other point keeps Raise = lower bank − GDP.

## The W6 drawing (engineer, 2026-10-11 afternoon) — `civil3d/Block04_Channels_W6.dwg`, the live drawing from now on

`scripts/43_w6_drawing.py` saved the W5 drawing, copied it to `civil3d/Block04_Channels_W6.dwg` (118 MB), opened the copy in
Civil 3D (COM) and added per channel the **profile `GDP-raised <name>` = GDP + Raise at every design point**
(`cs/42_design_ground.cs`, style "GDP-raised", cyan continuous 0.35 mm, label set _No Labels; first built as "DG <name>" in green
and renamed and recoloured the same afternoon on the engineer's instruction, the EG being green already): the model ground
for SewerGEMS — the lower bank top where a point lies in a wadi, the library depth above the bed at fix points, the GDP where
the raise is 0. 37 profiles, 249 PVIs (the 227 points plus, for the 22 tributaries, an end PVI at the tributary's end station
= its own GDP end + the raise of the junction point on the receiver); 168 points raised. Verified at eight points: DG = GDP + Raise
to the millimetre (checked under the first name; the rename kept the PVIs). The point names in the views and in plan (layer W6-PT-SGLABEL, `38_sg_labels_markers.py`) now read
`HAWCH1-6  D 2.98  R 1.91` (37 writes the text into `final/final_markers.json`). The W6 drawing holds everything of W5 at the
copy (EG surfaces and profiles, alignments, views, GDP profiles with their dashed "(before ...)" copies, grade-break and design-
point markers); W5's drawing is frozen at that state. 27, 32, 36 and 38 accept the W6 drawing as the active one. Re-run after a
change of points or raises: 37 → `43_w6_drawing.py --no-copy` (replaces the GDP-raised profiles and the names in the open W6 drawing).

**SewerGEMS readiness (engineer, 2026-10-11 evening):** two fields added at the end of `final/Block4_design_points.shp`:
**`GDP-Raised`** = GdpZ + Raise, the node ground for the import (the GDP-raised profile of the drawing; the `Ground` column stays
the terrain), and **`Outfall`** = "Y" at the end point of each of the 15 channels that join no other channel (all 15 are the
engineer's outfall fix points: HAWCH1-8, HAWCH7-7, SAKCH2-8, SAKCH3-7, SAKCH5-3, SARCH1-15, SARCH2-7, SHACH1-13, SHACH3-17,
SHACH4-11, SHACH6-7, SHACH7-10, SHACH13-2, SHACH16-8, SHACH19-2). Section, library depth and roughness are set in SewerGEMS, not
in the layers. With that the two shapefiles are the import set: points = nodes (SGLabel, X/Y, GDP-Raised as ground, GdpZ as
invert, Q/V at the flow points, Outfall), segments = conduits (SGLabel, SGFrom/SGTo, Length, USInv/DSInv, Slope).

**QGIS crash and restore (2026-10-11 04:01):** the Block 04 QGIS instance crashed with its unsaved layer tree (last save 03:02):
a layer's Properties dialog was open while a rebuild removed and re-added that layer (QGIS locks shapefiles, so every
regeneration swaps the layers), and the dialog's Cancel ran on a freed layer (`%LOCALAPPDATA%\QGIS\QGIS3\crashes\c0094d6a-...`).
`scripts/44_qgis_w6_groups.py`, run inside QGIS (MCP execute_code or the Python console), rebuilds both W6 groups with their 17
layers, styles and labels and re-applies the channel symbology; used right after the engineer reopened the project. Rule from
now on: no layer removal while a layer dialog may be open, and the swap as one script. The project itself is never saved by Claude.

## SewerGEMS run of the engineer's model (2026-10-11 evening) — `sewergems/`

The engineer built the SewerGEMS model from the final layers in the offline VM (`\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04
11102026\SewerGEMS Block 04.stsw`: GVF-Rational (StormCAD) Design, two conduit catalogues of depth 2.5 and 3 m with different
materials, widths 1 to 2000 m in 0.5 m steps with a 10 m minimum, design constraints, transition nodes, outfalls renamed `HAWCH7-O14`,
a System Flows alternative and a physical alternative per return period, eight scenarios 2 to 500 yr, every alternative and
calculation option local) and asked for all scenarios to run. Through the file-drop bridge (`D:\VBOX\bridge`, watcher in the
guest, no network): `sewergems/jobs/057_b4_inventory.ps1` (scenarios, alternatives, engines, catalogues, result fields, on a guest
copy) and `058_b4_run_all.ps1` (copy of the shared model to `C:\B4Work\run_<stamp>`, SaveAs R1, for each scenario
`Scen.DesignUntilStable` = design passes until no catalogue size changes, export by `sewergems/lib/B4.cs` (also in
`D:\VBOX\bridge\lib`): conduits with the catalogue size, flow, velocity, depths in/out, inverts, slope; nodes with ground,
invert, hydraulic grade; then **`SewerGEMS Block 04_R1.stsw` + `.sqlite` delivered to the share as NEW files**, the engineer's
file untouched). Timing: every design pass 9.5–10 min, two passes per scenario (the second changes nothing), 8 scenarios in
2 h 35 min; the job's output file is UTF-16 (PowerShell redirection). `scripts/45_sewergems_results.py` → `sewergems/results/
run_20261011_1721/`: `conduits_long.csv`, `nodes_long.csv`, `summary.md`, the raw exports and both job logs.

Results (212 conduits, 227 nodes, every scenario): designed widths median 10 m (2 yr) → 17 (10 yr) → 30 (50 yr) → 49.5 (200 yr)
→ 77.5 m (500 yr); largest 20 m (2 yr), 243.5 (10 yr), 525 (50 yr), **966.5 m at 200 yr and 1393 m at 500 yr, both SHACH1-C11/C12
at 1670 m³/s**; widths never decrease with the return period; velocities up to 2.9 (2 yr) … 4.7 m/s (500 yr); the hydraulic grade
stays below the GDP-raised ground at every node in every scenario (freeboard 1.41 m or more). **Two findings for the engineer:**
(1) **withdrawn 2026-10-11 after the engineer's challenge ("HAWCH1-C7 was 3 m depth"):** HAWCH1-C7 and SHACH1-C12 ARE on the
3 m catalogue (class 1443) in all nine physical alternatives and were designed 3 m deep in every scenario (200 yr: 3 x 133.5 and
3 x 966 m). The export labelled them "2.5 x …" because his five catalogue classes (1.5, 2.5, 3, 4 and the concrete 2.5) share the
same 3999 size GUIDs, one per row position, and `B4.Export` (and `46_sg_profile_dxf.py`) resolved a size by GUID alone instead of
class + GUID. Wrong for those two conduits in every scenario: `size_label` in the exports, the "depth 3 m on none" line of
`summary.md`, the HAW-CH1-FP profile annotation and crown line (0.5 m low on HAWCH1-C7), the sheet's conduit table and the buffer
width (134 for 133.5). The hydraulics are right, the engine uses the class's own row. Correction pending his go-ahead;
(2) the widths of several hundred metres at 100 yr and above come from the design constraints with a 2.5 m deep section and flow
depths of only 0.7–1.9 m, a review of the constraints (depth ratio, velocity) before these sizes mean anything. The `FullFlowCapacity`
result returned by the API (55 m³/s on a 966 m channel) is not usable and is left out of the summary.

## Profiles inside SewerGEMS (engineer, 2026-10-11 night) — revision R2

He wants SewerGEMS's own profiles and DXF exports, one profile per channel of `Channels and Dykes 04102026`, with the annotation
set and table of the model this one was copied from (Block 6 Rustaq; its export `OUTPUT\DXF\1\Ais-CH1-FP.dxf` sits in
`Block 06 SewerGEMS\Backup\48 SewerGEMS Rustaq with one profile dxf.rar`: layers Grid, Ground_Elevation, Invert, Crown, Structure,
Hydraulic_Grade, Energy_Grade, Annotation, Annotation_Table; x = station, y = elevation × 10; node annotation label/Rim/Invert,
conduit annotation length @ slope and section; table rows Label, Length, Conduit Description, Flow, Slope / Label, Ground, Invert,
Station), the ground from a terrain built on the 0.5 m buffer point DXF, and a plan DXF per scenario with every annotation on.
Doable parts done, the rest at the office:
- **backup 5**: `Backup\5 SewerGEMS Block 04 11102026.zip` (47 MB, the same content rule as his zips 1–4: model files, SHP, XLS).
- **terrain points**: `W4/points/Terrain_Points_B4_0.5m.dxf` (1.15 M points, 0.5 m buffer on the DTM the design ground came from)
  copied to `SewerGEMS Block 04 11102026\Terrain\` for the Terrain tool of the 2D ribbon tab.
- **the 37 profiles**: SewerGEMS keeps a profile as a selection set under `DomainDataSet.ProfileManager` (field
  `SelectionSetElementIDs`, an ordered `HmIDCollection` of node and conduit IDs; found by `jobs/059–062`, the Rustaq profile
  Ais-CH1-FP reads node > conduit > node ... 35 elements). `jobs/063_b4_profiles_R2.ps1` (generated by `jobs/gen_profile_jobs.py`
  from `profiles/profile_paths.csv`: each channel's nodes and conduits from the start to the junction point on the receiver or to the
  outfall, outfalls under his new names such as HAWCH7-O14) created them in **R2 = R1 + profiles** on the guest and delivered to the
  share `SewerGEMS Block 04_R2.stsw` + `.sqlite`, the eight scenarios' result files renamed for R2 (and for R1), and his `.dwh` and
  `.profiles.dwh` copied under the R2 name so drawing and profile settings travel with it. Verified after reopen: 80 profiles with
  elements = the 43 inherited from Rustaq (their elements do not exist in Block 04; his to delete) + the 37 channels.
  His file `SewerGEMS Block 04.stsw` is untouched.
- **not doable through the API**: the profile DXF export and the plan DXF export are GUI commands (Haestad.Framework.Windows.Forms),
  as is building the terrain from the point DXF; either he does them in the GUI on R2 or they are driven by UI automation in the VM
  window at the office. Trap: Git Bash heredocs mangle backslashes, so bridge jobs are written as files (`gen_profile_jobs.py`).

**Later the same night:** `jobs/064_b4_delete_old_profiles.ps1` removed the 43 Rustaq profiles from R2 (37 channel profiles
remain, verified after reopen, R2 redelivered).

## Trial: the SewerGEMS profile export without the GUI, and the plan-profile sheets (2026-10-11 night, HAW-CH1-FP)

The engineer wants SewerGEMS's own DXF profile exports and, from them, the A1 plan-profile sheets delivered to the client in
Block 6. The reference is the Rustaq export `OUTPUT\DXF\1\Ais-CH1-FP.dxf` (dissected entity by entity, see the generator's
docstring) and the Block 6 sheet pipeline `Block 06 SewerGEMS\W5\scripts` (a previous Claude session's work: SewerGEMS profile
DXF + channel shapefile + buffers + title-block template → A1 sheets with ESRI satellite tiles, PDFs, key map).
- **Profile DXF**: `scripts/46_sg_profile_dxf.py --channel HAW-CH1-FP --scenario 200yr` builds `sewergems/dxf/<run>/<scenario>/
  HAW-CH1-FP.dxf` exactly like the export: DXF R12, x = station, y = elevation × 10, the same layers and colours, text style,
  heights, alignments, grid 25 m × 2 m with elevation labels at x = −32.7 and station labels "k+mm" at y = −7.7, both axis titles,
  node annotation label / Rim / Invert at station + 2.44 with leader and arrowhead, conduit annotation "label: length @ slope"
  and "Box - span x rise m material" rotated along the conduit, the nine-row table with the same row positions and formats,
  column lines up to the top of the grid. Data: the R2 exports of the run (node ground = the GDP-raised ground, inverts,
  designed sizes with span/rise/material from the R2 catalogue, flows, depths), the DTM along the alignment for the ground line.
  `scripts/47_sg_profile_dxf_compare.py` proves it feature by feature (`HAW-CH1-FP_vs_Rustaq.md`): every structural check matches;
  the only known difference is the HGL inside a conduit, a straight line between its ends where the export carries the GVF
  profile points (obtainable later from the `GVFConduitProfileCollection` result field through the bridge).
- **Sheets**: the Block 6 pipeline copied to `sewergems/sheets/scripts` with `Data/DXF/HAW-CH1-FP.dxf`, `Data/SHP/Channels.shp`
  (the 37 channels from the oriented build spec, field Name), `Data/SHP/Buffers` built by `make_buffers.py` as **one dissolved
  outline per layer** (engineer, 2026-10-11: no crossing segment ends at the joints; flat-ended segment buffers unioned with a
  disc at every inner point sized by the wider adjacent segment; **widths are placeholders**: bed = the 200-yr designed width
  of each segment, corridor = bed + 10 m each side), the Block 6 template; `config.py` set to Block 04 (catchment order HAW/SAK/SAR/SHA,
  drawing numbers 2224-PD-HY-PP-B4-nnn, no reversed channels, PROJECT-TITLE3 "Block 04"); `requests` and `pikepdf` installed.
  `python run_all.py HAW-CH1-FP` + `export_pdf.py`: 9 sheets + key map in 33 s, PDFs, `PDF/Combined/HAW-CH1-FP.pdf` (10 pages,
  13 MB). Inherited behaviour to review: conduit table values sit at the conduit midpoint, so a sheet whose window does not
  contain the midpoint of a long conduit shows empty conduit rows; the layout tab keeps the template's name
  ("Plan & Profile Ais-CH1-FP 0+000 - 0+850"); the node station cell uses the SewerGEMS "10+44" form while the grid uses
  "1+050". Accepted the same night; what followed is below.

## Size labels corrected, profile DXFs for every channel and scenario, sheets for all 37 channels (2026-10-11 night)

**The correction.** His challenge "HAWCH1-C7 was 3 m depth" was right. His five catalogue classes (1.5, 2.5, 3, 4 and the
concrete 2.5) share the same 3999 size GUIDs, one per row position, so a size is identified by **class + GUID**; `B4.Export`
resolved the label by GUID alone and printed the 2.5 m class's row for the two conduits on the 3 m class. The engine itself uses
the class's own row, so every hydraulic result was right; only the labels, and everything derived from them, were wrong.
- `scripts/48_fix_size_labels.py`: rewrites `results/<run>/bridge_exports/conduits_<scenario>.csv` from the R2 database (the
  class assigned in the scenario's physical alternative, walking up the parent chain when the alternative has no row for the
  conduit, and the size row of that class), adds `class_id, class_label, material, rise_m, span_m`; the as-run export is kept in
  `bridge_exports_asrun/`; gate: the as-run GUID equals the database GUID for all 212 conduits in all 8 scenarios (it did);
  report `results/<run>/size_label_correction.md`. Corrected: HAWCH1-C7 and SHACH1-C12 in every scenario (200 yr: 3 x 133.5 and
  3 x 966 m). `lib/B4.cs` now resolves by class + GUID and writes the five columns itself (compile-checked, not re-run: the
  host-side correction is exact). `45` reads the corrected exports (summary: "depth 3 m on SHACH1-C12, HAWCH1-C7"); `46`
  takes rise, span and material from the corrected export, draws no hydraulic grade and leaves the flow cell empty for a conduit
  without results; `47` normalises the table lines (12 + one per node) and the middle elevation-label column properly and
  reports the text-pattern rows as information: HAW-CH1-FP at 200 yr is **56 checks matched, 3 informational, 0 differing**; the
  GVF profile points inside conduits remain the one known difference.
- `scripts/49_sg_profile_dxf_all.py`: the profile DXF of **all 37 channels in all 8 scenarios** (296 files, 30 s) in
  `sewergems/dxf/run_20261011_1721/<scenario>/`.
- **Sheets for all 37 channels at 200 yr** (the trial's scenario; the design return period is still his decision): the 200-yr
  DXFs copied to `sheets/scripts/Data/DXF/`, `make_buffers.py` rebuilt with the corrected widths, `python run_all.py` and
  `export_pdf.py`: 277 sheets and key maps as DXF and PDF, one combined PDF per channel in `sheets/scripts/PDF/Combined/`.
  **Live version = the highest `_v<n>` of each sheet in `DXF/`**; the pipeline keeps the superseded versions beside it and
  writes PDFs of the newest only. `preview_sheet.py <channel> <sheet|km> [plan|profile] [--conduit SGLabel]` renders a
  viewport to PNG; checked: HAW-CH1-FP sheet 08 (HAWCH1-C7, crown at the rim, "133.5 x 3.0 m Natural stream, weedy") and
  SHA-CH1-FP sheet 08 (SHACH1-C12, "966.0 x 3.0 m").
- **Finding for the engineer: SHA-CH13-SS was never computed.** Its end SHACH13-2 is flagged Outfall = Y in the final points but
  is a manhole in the model (14 outfalls for 15 free ends), so the engine solved nothing for it in any scenario: no flow, no
  depths; its section is the one inherited from the Base alternative (10.0 x 2.5 m, 2.5 m class) and its sheets show that
  section with no flow and no hydraulic grade (the NaN hydraulic grade also crashed its sheet 02 until `46` skipped it). His
  fix: make SHACH13-2 an outfall (SHACH13-O15) and re-run; the channel is an isolated system, nothing else changes.

## The drawing set as one PDF (2026-10-11 night)

He wants the 200-yr sheets combined in one PDF: a cover, a table of drawings, then per global catchment a divider page and its
plan-profiles. `sheets/scripts/make_set.py` builds `sheets/scripts/PDF/Set/2224-PD-HY-PP-B4_Plan_and_Profile_Drawings_200yr.pdf`
(284 pages, 391 MB): cover, two table pages (drawing number, catchment, channel, drawing, station from/to, page), one divider per
catchment in the drawing-number order Al Hawasinah, Sakhin, Sarami, Shafan (his message listed Al Hawasinah, Shafan, Sarami,
Sakhin; that order would renumber every title block), then each channel's key map and sheets from the combined PDFs; bookmarks
cover > table > catchment > channel > drawing; beside it `_contents.csv` and `front_matter_extract.pdf` (the five front pages).
Cover, table and dividers are A1 like the sheets and repeat only the sheets' own title-block lines (client, project, Block 04,
design stage, revision 1, date, consultant) plus "Hydraulic design for the 200-year return period".
- **Gates.** The set PDF passes `W3/report/check_clean.py` with the sheets' own lists `sheets/forbidden_terms.txt` (the W3 list
  plus the Rustaq names `Ais-CH*`, `Rustaq`) and `sheets/allowed_terms.txt` (the W3 list plus the drawing-number prefix, which
  carries the job number by design). The sheet pages have **no text layer** (the vector export draws text as outlines), so
  `sheets/scripts/check_clean_sheets.py` scans the TEXT, MTEXT, attribute strings and layout names of the latest DXF of every
  drawing with the same scanner and lists; it caught the template's layout tab name (a Rustaq channel) in all 277 DXFs.
- **Two fixes in the inherited pipeline.** `run_all.py` numbered a single-channel rebuild from 001 (the rebuilt SHA-CH13-SS
  drawings carried 001–003); it now always numbers over every channel (SHA-CH13-SS = 231–233). `make_sheet.py` and
  `make_keymap.py` rename the layout tab to the drawing number. All 277 drawings were rebuilt, exported and the set rebuilt:
  **both gates PASSED** (`sheets/scripts/rebuild_all_200yr.log`). `preview_sheet.py` renders a sheet's plan or profile viewport.
- **Still not a client issue:** SHA-CH13-SS shows no flow (no outfall in the model) and the bed/corridor outlines are placeholders.
- **Delivery.** The set exceeds the 30 MiB limit of a file card to his phone and the 10 MB cap of the Chrome extension's upload.
  WhatsApp Web through his own Chrome (a new tab shares the logged-in session, no "Use here" was even needed): the native file
  picker never opens from an extension click, and the page's fetch to a local server is blocked by WhatsApp's content-security
  policy; what works is an own `<input type=file>` filled by the extension's upload tool and a synthetic `drop` on `#app`
  (the preview opened), but with the workstation locked the page is hidden, timers are throttled to once a minute and the send
  stalled; the Bird connector sends from a business number and caps documents at 100 MB. What finally worked: a persistent
  linked device on this machine (`C:\Users\mojtaba\wa_link`, Baileys, paired once with the 8-character code, kept at his
  request); the set and the front matter reached his Me MCI chat that way (391 MB in 21 s).

## SHA-CH13-SS computed: revision R3, the design scoped to one channel, all eight scenarios (2026-10-11 night)

His decisions while going to sleep: fix the model through the API (delete the manhole SHACH13-2, create the outfall SHACH13-O15 at
its point, reconnect), run with the design limited to that channel the way he runs a selection in the GUI, the 200 yr first as
the trial, then the whole model; then rebuild everything and reorder the set.
- **The API facts** (`jobs/065_b4_api_probe_outfall.ps1`): `Outfalls.Create()`, `SetPoint(point)`, writable `GroundElevation`,
  `InvertElevation`, `SetRimToGroundElevation`, `Delete()`, a writable `StopNode` on the conduit, and the design flags as plain
  properties `DesignConduit / DesignStartInvert / DesignStopInvert` (conduits) and `DesignStructureElement` (nodes), all on the
  shared "Base Design" alternative 17. Trap: never read a GeometryPoint's X or Y in PowerShell (CLS casing error); pass the point.
- **R3** (`jobs/066_b4_shach13_outfall_R3.ps1`, on a guest copy of R2): the outfall built with the manhole's ground 50.113 and
  invert 47.613 written under every return-period scenario (the physical alternatives are local copies), SHACH13-C1 reconnected,
  the manhole deleted (212 manholes, 15 outfalls); the design flags snapshotted (`design_flags_before.csv` in the run folder),
  switched off on 211 conduits and 225 nodes, kept on SHACH13-C1 and its two nodes; the 200 yr scenario designed (one size
  changed in pass 1, none in pass 2, about 5 min per pass: the engine still solves the whole network, only the sizing is
  scoped); exported; the flags restored; R3 delivered to the share with the result files. `jobs/067` did the same for the seven
  other scenarios (5–10 min each), `jobs/068` rewrote the profile SHA-CH13-SS (the deleted manhole left it dangling) to
  SHACH13-1 > SHACH13-C1 > SHACH13-O15. Bridge run folder `run_20261012_0031` (the guest clock is 11 h ahead).
- **The result**, identical to the hand rule in every scenario (75 % part-full of the 2.5 m rise, no velocity limit, n 0.030,
  slope 0.005): 2.5 x 10 at 2 and 5 yr, 18 at 10 yr, 25 at 25 yr, 31.5 at 50 yr, 39.5 at 100 yr, 49.5 at 200 yr (313.4 m³/s,
  3.40 m/s, depth 1.86 m), 65.5 at 500 yr. Nothing else changed: the 200-yr exports of R3 and of the earlier run differ in
  SHACH13-C1 alone.
- **What the engine does with inverts** (checked on the earlier 200-yr run, 209 of 212 conduits): it hangs the 2.5 m section
  from the raised ground, invert = GDP-Raised − rise, so at a fix point with the 2.5 m library raise the bed stays exactly at the
  GDP and elsewhere the bed goes below the GDP by 2.5 m minus the raise. This is his method, not a defect; it is why the invert
  design flags stay on.
- **Downstream** (`scripts/50_rebuild_after_run.py --run run_20261012_0031 --sqlite <R3>`): exports into
  `results/run_20261012_0031/` (as-run kept beside the corrected ones; the fixed `B4.Export` already writes the class columns,
  `48` now overwrites them), `profile_paths.csv` updated to the outfall, summary, the 296 profile DXFs, buffers, all 277 sheets,
  PDFs, the set, both gates.
- **The set reordered** on his instruction: catchments Al Hawasinah, Shafan, Sarami, Sakhin, and within a catchment the channels
  in the feature order of his `Channels and Dykes 04102026.shp` (`Hydrology\SHP\temp`), written as `CHANNEL_ORDER` in
  `sheets/scripts/config.py` and honoured by the drawing numbers, the table, the dividers and the bookmarks. Every title block
  changes number, hence the full rebuild: 277 drawings in 81 s with the tile cache warm, PDFs, the set (284 pages, 391 MB,
  SHA-CH13-SS = drawings 051-053 with its 49.5 m section and hydraulic grade), **both gates PASSED**
  (`scripts/rebuild_run_20261012_0031.log`); the set and its front matter sent to his chat through the linked device
  (superseded the same morning by the corridor rebuild below).
  **Live:** results `results/run_20261012_0031`, profiles `dxf/run_20261012_0031`, the sheets' highest `_v<n>` per drawing,
  revision R3 on the share. Superseded: `run_20261011_1721` (SHA-CH13-SS without results) and R1/R2.

## The plan outlines defined (engineer, 2026-10-12 morning)

Both outlines come from the design run: **bed = the designed span** of each segment at 200 yr (that was already so), **corridor =
span + 15.5 m on each side**, his definition: an embankment on both sides of every channel, 2.5 m high with 1.5H:1V slopes and a
4 m crest, bottom width 2 x (2.5 x 1.5) + 4 = 11.5 m, plus a 4 m access road (`make_buffers.py`, default `--extra 15.5`, the
10 m placeholder gone). The plan layers change on every sheet, so all 277 drawings, the PDFs, the set and both gates were
rebuilt (`sheets/scripts/rebuild_corridor_15p5.log`). Velocity is a detail-design item by his decision and is no longer flagged.

## Key maps: the oversized sheet numbers (engineer, 2026-10-12 morning)

The key map zoomed to fit the channel and drew the sheet number at 55 % of the frame's short side on paper, so a two-sheet
channel at 1:2000 got a 60 mm number and station labels to match. Now (`make_keymap.py`): the key-map scale is never larger
than 1:5000 and is snapped to the next standard denominator that still fits (5000, 10000, 12500, 15000, 20000, 25000, 50000),
so the title block's scale is the drawn one; the sheet number is capped between 6 and 12 mm and the station labels between
1.8 and 4 mm, the number stays centred in its frame at his request, the station labels sit outside the frames at the joints as
before. `run_all.py --keymaps` rebuilds the 37 key maps alone (switches are no longer taken for channel names); then the PDFs,
the set and both gates (`sheets/scripts/rebuild_keymaps.log`).

## Revision R4: minimum slope 0.002, maximum 0.03, the 200 yr design (engineer, 2026-10-12)

The design constraints had min slope 0.0003 and max 0.02 m/m (system-wide, Base Design alternative 17, no local overrides; no
velocity limit, 75 % part-full). He asked for min 0.002 and max 0.03 in a new revision and a 200 yr run only, the other
return periods after his approval. `jobs/069_b4_slopes_R4_200yr.ps1`: R3 copied to **R4**, the two system constraints written
through `AlternativeManager(Design).SystemRecordField(...).SetValue(17, v)` and verified after reopen, a FULL design of the
200 yr scenario (all flags on): 66 sizes changed in pass 1, none in pass 2, 10 min per pass; exported to bridge run
`run_20261012_0850`; R4 delivered with the 200 yr result file only. Downstream: `50_rebuild_after_run.py --run run_20261012_0850
--scenarios 200yr --sqlite <R4>` (the driver now takes a scenario subset): exports, summary, profiles, buffers, all 277 drawings,
PDFs, the set, both gates PASSED (`scripts/rebuild_run_20261012_0850.log`); the set sent to his chat.
- **R4 against R3 at 200 yr:** 66 conduits changed size, 62 narrower and 4 wider; total designed width 21.7 km → 15.6 km;
  widest 966 → 395.5 m (SHACH1-C10..C12); the 26 conduits that sat on the old 0.0003 floor now run at 0.002; velocities
  unchanged at the top (4.65 m/s), 97 conduits over 3 m/s. Bed outline 20.21 → 14.94 km².
- **The price of the steeper floor:** the engine lowers downstream inverts to hold 0.002 where the ground is flatter. Inverts
  moved at 19 start and 32 stop nodes, by up to 2.0 m (SAKCH2-C6/C7); **8 of the 15 outfalls now end 0.5 to 2.8 m below the
  GDP bed** (SAKCH5-O3 −2.81, SHACH4-O6 −2.58, SAKCH3-O2 −2.47, SHACH3-O7 −2.46, SARCH1-O5 −1.70, HAWCH7-O14 −1.55,
  SHACH16-O8 −1.01, SAKCH2-O1 −0.54); ground minus invert reaches 5.3 m at nodes. His call: accept the cut at the outlets, raise
  the floor less, or fix the outfall inverts.
- **Live:** results `results/run_20261012_0850` (200 yr only), profiles `dxf/run_20261012_0850/200yr`, the sheets' highest
  `_v<n>`, revision R4. Superseded for 200 yr: `run_20261012_0031` and R3 (R3 remains the live source of the other seven
  scenarios until R4 is run for them).
- **QGIS review layers (his request, 2026-10-12, at the office):** `scripts/51_qgis_sewergems_200yr_R4.py` writes
  `gis/sewergems_200yr_R4.gpkg` (segments with the R4 design, manholes, outfalls, the 37 alignments, bed, corridor, and two
  TEMPORARY check layers against R3: `chk_inverts`, the 27 nodes whose invert moved, all lowered, and `chk_conduits`, the 70
  conduits whose size, slope or invert changed, 30 steeper, 17 flatter). Added to his project through the QGIS MCP as two groups
  at the top of the tree, `W6 SewerGEMS 200 yr R4` and `W6 check R3 to R4 (temporary)`: segments labelled label / W / S as a
  stack, the check layers labelled new (old) with blue for up or steeper and red for down or flatter on both label and symbol;
  styles saved in `gis/qml/`. Nothing of his was removed or renamed; the project was not saved.

## Revision R5: minimum slope 0.001; the drawing order corrected; sets kept per revision (engineer, 2026-10-12)

His review of R4: the channels within a catchment must run by CH number (HAW-CH1, HAW-CH2, ...), not by the shapefile's feature
order as I had read his earlier instruction; keep the R4 files for comparison; R5 with min slope 0.001, compared with R3 in QGIS
while the R4 check stays; everything regenerated and the set sent.
- **Order**: `CHANNEL_ORDER = []` in `sheets/scripts/config.py`, so the sort key falls back to catchment order then CH number.
- **Kept files**: the R4 outputs copied untouched to `sheets/archive/R4_200yr/` (PDFs, buffers, config as built) and the set in
  `PDF/Set` renamed `..._200yr_R4.pdf`; from now on `make_set.py --tag` and the driver's `--set-tag` put the revision in the
  set's file name, so no set overwrites another.
- **R5** (`jobs/070_b4_slopes_R5_200yr.ps1`): R3 copied, min slope 0.001 and max 0.03 (the max he set for R4) written and
  verified, full design of 200 yr: 41 sizes changed in pass 1, none in pass 2; bridge run `run_20261012_1119`; R5 delivered
  with the 200 yr result file. Downstream by the driver with `--set-tag R5`, both gates PASSED
  (`scripts/rebuild_run_20261012_1119.log`); set `PDF/Set/..._200yr_R5.pdf`, 284 pages, sent to his chat.
- **R5 against R3 at 200 yr**: 41 conduits narrower, none wider; total width 21.7 → 17.6 km (R4: 15.6); widest 966 → 558 m
  (R4: 395.5); the 18 conduits below 0.001 lifted to it, the 26 below 0.002 unchanged in count; inverts moved at 10 start and
  20 stop nodes, at most 0.82 m (R4: 2.03); outfalls more than 0.5 m below the GDP bed: R3 5, R4 8, R5 6 (SHACH3-O7 −2.38,
  SAKCH3-O2 −2.06, SHACH4-O6 −2.01, SAKCH5-O3 −1.72, SARCH1-O5 −1.42, SHACH16-O8 −0.69). R3 itself already cut 5 outlets,
  so part of that is the ground, not the floor.
- **QGIS**: `51_qgis_sewergems_200yr_R4.py --rev R5` → `gis/sewergems_200yr_R5.gpkg`; groups `W6 SewerGEMS 200 yr R5` and
  `W6 check R3 to R5 (temporary)` (17 inverts moved, all lowered; 43 conduits changed, 20 steeper, 10 flatter, 13 only size or
  invert) added at the top with the R4 styles; the R4 groups kept, collapsed and unchecked.
- **Live**: R5 for 200 yr (`results/run_20261012_1119`, `dxf/run_20261012_1119/200yr`, the set `_R5`); superseded for 200 yr:
  R4 (archived) and R3; R3 remains the source of the other seven scenarios. His decision pending: R4, R5 or another floor.

## Ten fix points withdrawn; revision R6 (engineer, 2026-10-12, "a very important step")

HAWCH1-5, HAWCH2-8, HAWCH5-7, SAKCH2-7, SARCH1-12, SHACH1-11, SHACH14-3, SHACH15-5, SHACH3-11 and SHACH7-8 are no longer fix
points: all ten are Road-OQ crossings, each also a GDP grade break, none with a 500 m partner point or an exclusion rule, so the
point set, the labels, the segments and the model topology do not change. Confirmed by him before any action: the crossings may
be cut (the engine hangs the 2.5 m section from the new ground, so the bed goes 1.7–2.5 m below the GDP there), R6 builds on
R5, I take them out of his fix layer, the QGIS check is against R3 with R4 and R5 kept.
- **Source of truth**: `inputs/fix_removed.json` (FIX5, 6, 4, 48, 42, 16, 28, 25, 29, 11), honoured by `31_design_points.py`
  and `37_final_layers.py` (hook right after the fix layer is read). His master layer `output/design_points.gpkg: fix_points` was
  NOT rewritten (his QGIS holds it); the ten still show there until he deletes them or I do it with his QGIS closed.
- **Raise as normal points** = lower bank − GDP floored at 0, 0 for class none: HAWCH1-5 0.509, HAWCH2-8 0 (bank below the
  GDP), HAWCH5-7 0.831, SAKCH2-7 0 (none), SARCH1-12 0.601, SHACH1-11 0 (none), SHACH14-3 0.466, SHACH15-5 0.252, SHACH3-11
  0.575, SHACH7-8 0.445; written into `wadi/wadi_results.csv` (copy `wadi_results_before_fix_removal_<stamp>.csv`), the
  ground drops 1.67–2.50 m. `37` rerun: 227 points, same labels, exactly the ten changed (Fix, FixType, Members, Raise,
  GDP-Raised), segments identical (the segment shapefile could not be rewritten while his QGIS held it; it needed no change;
  the points shapefile was rewritten after removing and re-adding his layer with its style).
- **Civil 3D**: the ten fix markers dropped from `output/profile_markers.json` (copy kept), `32` (176 markers), `43 --no-copy`
  (37 GDP-raised profiles, 249 PVIs) and `38` (227 names) rerun on the W6 drawing, saved.
- **R6** (`jobs/071_b4_fix_withdrawn_R6_200yr.ps1`): R5 copied, the ten grounds written under every scenario (rim follows the
  ground), full design of 200 yr: 32 sizes changed from R5 in pass 1, none in pass 2; bridge run `run_20261012_1344`; R6
  delivered with the 200 yr result file. Driver with `--set-tag R6`, both gates PASSED; set `PDF/Set/..._200yr_R6.pdf`, sent.
- **R6 against R3 at 200 yr**: 48 sizes changed (46 narrower, 2 wider), total width 21.7 → 16.3 km, widest 966 → 519.5 m;
  against R5: 32 changed, 17.6 → 16.3 km. At the ten nodes the bed sits 1.67–2.50 m below the GDP (HAWCH2-8, SAKCH2-7,
  SHACH1-11 the full 2.5). Outfalls unchanged from R5: 6 more than 0.5 m below the GDP bed.
- **QGIS**: `gis/sewergems_200yr_R6.gpkg`, groups `W6 SewerGEMS 200 yr R6` and `W6 check R3 to R6 (temporary)` (21 inverts
  moved, all lowered; 51 conduits changed, 23 steeper, 14 flatter); R4 and R5 groups kept, collapsed and unchecked.
- **Live**: R6 for 200 yr (`results/run_20261012_1344`, `dxf/run_20261012_1344/200yr`, set `_R6`, the final points layer
  with the ten as normal points, the W6 drawing). Superseded for 200 yr: R5, R4 (archived), R3; R3 still carries the other
  seven scenarios.

## The engineer edited the GDP of SHA-CH1-FP in the drawing; revision R7 (2026-10-12)

He moved the last two PVIs of "GDP SHA-CH1-FP" in the W6 drawing (stations unchanged): 7+124 from 2.552 to 3.895 and the
end 8+043 from 0.500 to −0.700, and asked for the GDP-raised profile, the annotations, the inputs and a new model end to end.
- **Read back**: `W5/scripts/27_gdp_from_drawing.py` (the GDP folder archived first in `gdp/archive_before_shach1_edit_<stamp>`)
  re-read all 37 profiles: only SHA-CH1-FP differs, elevations only. The breaks shapefile and the final layers could only be
  rewritten after removing his three shapefile layers from QGIS (breaks, points, segments) and re-adding them with their styles.
- **What it means under the method**: SHACH1-12 is a normal point, its ground is the lower bank 5.81 and the raise shrank from
  3.26 to 1.92, so **its model ground did not move**; SHACH1-13 is the outfall fix point with the 3.0 library raise, so its
  ground dropped from 3.50 to 2.30 and the outlet invert from 0.50 to −0.70. `wadi/wadi_results.csv` updated (copy kept),
  `37` rerun: exactly SHACH1-12 (GdpZ, Raise) and SHACH1-13 (GdpZ, GDP-Raised) changed, segments SHACH1-C11/C12 inverts.
- **Drawing**: the FIX17 marker's elevation in `output/profile_markers.json` set to the new GDP, then `32`, `43 --no-copy`
  (37 GDP-raised profiles) and `38`, drawing saved.
- **R7** (`jobs/072_b4_shach1_gdp_R7_200yr.ps1`): R6 copied, the two grounds written under every scenario, full design of
  200 yr: 2 sizes changed in pass 1, none in pass 2; run `run_20261012_1513`; R7 delivered with the 200 yr result file.
  Driver with `--set-tag R7`, both gates PASSED; set `PDF/Set/..._200yr_R7.pdf`, sent to his chat.
- **R7 against R6**: SHACH1-C11 and C12 only, 519.5 → 519.0 m, C12 slope 0.003 → 0.004, the outfall invert 1.2 m lower;
  the widths barely move because the 75 % part-full rule, not the slope, sets them.
- **QGIS**: `gis/sewergems_200yr_R7.gpkg`, groups `W6 SewerGEMS 200 yr R7` and `W6 check R3 to R7 (temporary)`; R4, R5, R6
  groups kept, collapsed and unchecked. **Live**: R7 for 200 yr (`results/run_20261012_1513`, set `_R7`, the W6 drawing).
- **Second edit the same hour**: he lowered the GDP of SHACH1-12 from 3.895 to 2.839 (read back, archive
  `gdp/archive_before_shach1_edit2_<stamp>`, only that PVI differs). Under the method the point is a normal point in a wadi,
  so its ground stays the bank 5.81 and the raise grows to 2.971: the layers, the wadi record and the drawing (GDP-raised
  profiles, labels) were updated, but **the model input is unchanged, so no R8 was run**; R7 stays live. To make the bed
  follow the GDP there, the point has to become a fix point with a library raise.
- **Third edit**: the GDP of SHACH1-12 lowered again to 1.951 (archive `gdp/archive_before_shach1_edit3_<stamp>`): raise 3.859,
  ground still 5.81, no model ground changed, no R8; layers, wadi record and drawing labels updated.

## The rule corrected by the engineer: the raise is fixed, an edited GDP moves the ground (2026-10-12); revision R8

His correction: the raise of a point is the value of the wadi analysis and stays; when he edits the GDP in the drawing the
ground (GDP + raise) moves one to one and SewerGEMS redesigns on the new slopes. My recomputation of the raise as bank minus the
edited GDP (the two entries above) was wrong under this rule and is withdrawn: for SHACH1-12 the raise goes back to its
wadi-analysis value 3.26 (from the original GDP 2.552), so with the GDP at 1.951 the ground is 5.211 instead of 5.81
(`wadi/wadi_results.csv`, copy `wadi_results_before_fixed_raise_<stamp>`). Consequence for the pipeline: `39_wadi_depth.py`
must not be rerun on points whose GDP was edited after the analysis, since it would recompute the raise from the edited GDP;
the raise lives in `wadi/wadi_results.csv` and `37` only joins it.
- `37` rerun: only SHACH1-12 changed (Raise 3.859 → 3.26, GDP-Raised 5.81 → 5.211); the GDP-raised profile of SHA-CH1-FP
  and the labels refreshed in the drawing, saved; his three QGIS layers removed and re-added around the rewrite.
- **R8** (`jobs/073_b4_shach1_12_R8_200yr.ps1`): R7 copied, SHACH1-12 ground 5.211 under every scenario, full design of 200 yr:
  2 sizes changed in pass 1, none in pass 2; run `run_20261012_1608`; R8 delivered with the 200 yr result file. Driver with
  `--set-tag R8`, both gates PASSED; set `PDF/Set/..._200yr_R8.pdf`, sent to his chat.
- **R8 against R7**: SHACH1-12 invert 2.81 → 2.21; SHACH1-C11 slope 0.001 → 0.002 and C12 0.004 → 0.003; both 519.0 → 364.5 m
  (velocity 2.4–2.7 m/s). Nothing else moved.
- **QGIS**: `gis/sewergems_200yr_R8.gpkg`, groups `W6 SewerGEMS 200 yr R8` and `W6 check R3 to R8 (temporary)`; R4–R7 groups
  kept, collapsed and unchecked. **Live**: R8 for 200 yr (`results/run_20261012_1608`, set `_R8`, the W6 drawing, the final
  layers with the fixed raise). Superseded for 200 yr: R7, R6, R5, R4 (archived), R3; R3 still carries the other seven scenarios.

## Assessment: what if the Shafan 08 dam had been in the channel hydrology (engineer, 2026-10-12, before the other return periods)

Basin 3 excludes Shafan 08 on his instruction: its site junction only passes the Shafan 02 outflow, and the dam's local catchment
(Basin 1/4: S22 58.7 km2 + S23 31.0 km2; in Basin 3 SHA-S3 58.7 + SHA-S23 21.0, re-delineated) runs from SHA-J20 down SHA-R18
straight to SHA-J45 past the site. `scripts/52_hms_basin6_shafan08.py` built a TEMPORARY **Basin 6** = Basin 3 with the Basin 4
reservoir definition (Modified Puls, Elev-Area/Elev-Dis Shafan 08, initial 153) below the site and SHA-R18 ending at the site
(length 6229 → 3094 m at the reach's sinuosity), registered with eight depth-area analyses `DA <rp> B6` restricted to the Shafan
line (8 s each, headless); HMS project backup `_backup_before_basin6_<stamp>`; Basin 6 and its analyses stay in the project until
he removes them. `scripts/53_shafan08_assessment.py` → `sewergems/results/shafan08_assessment.md`.
- **Peaks**: at 200 yr SHA-J47 1641 → 955 m3/s (−42 %), SHA-J51 1671 → 1031 (−38 %); 2 yr −40 %, 10 yr −30 %, 100 yr −39 %,
  500 yr −42 %. The dam stores the whole event up to 200 yr (outflow 0; inflow 837 m3/s at 200 yr); at 500 yr it spills 373 m3/s
  at 23.6 h, after the peak. About 10 km2 of the dam's catchment stays outside the routed subbasins (31.0 vs 21.0), so the cut is
  slightly understated.
- **SHA-CH1-FP at 200 yr** under the model's own rule (75 % part-full, n 0.030, R8 slopes and rises, the engine's no-decrease-
  downstream envelope): C1–C3 278 → 163 m, C4–C9 319 → 187, C10 334 → 195.5, C11–C12 364.5 → 226; total span 3811 → about
  2260 m, 41 % less. Nothing of this is in the flow file, the model or the sheets: it is an assessment for his decision.
- **The dam itself**: under its own storm (Basin 4, the dam deliverables) Shafan 08 passes 72 m3/s at 200 yr, at 22.3 h with the
  level just over FSL (168.07), and 494 at 500 yr; under the SHA-J47 storm of this assessment 0 and 373. Either way the spill
  comes about 6 h after the channel peak (SHA-J47 peaks at 16.3 h, the spill at 22.3 h) and does not add to it.
- HMS 4.12 dropped the empty `HEC_HMS_Block_04.gage` (an empty Gage Manager, 88 bytes) on the headless save; restored from the
  Deliverables copy. The mirror check is back at its 14 known rows.

## Live GDP files (from 2026-10-10)

`gdp/` holds the live copies of the GDP outputs (`Block4_channel_breaks.*`, `Block4_channel_segments.*`,
`gdp_reviewed_pvis.json`, `gdp_summary.csv`, `gdp_parameters.json`), copied from `W5/gdp` after the junction fix; W5's
copies are frozen at that state. When the engineer edits profiles in Civil 3D: `python ..\W5\scripts\27_gdp_from_drawing.py`
reads the drawing's `GDP <name>` PVIs, redraws the break markers and rewrites these W6 files (the W5 ones are not
touched); then `31_design_points.py` and `32_markers.py` refresh the design points and markers from them. The layer
"GDP grade breaks (W6, live)" in the engineer's QGIS group "W6 design points" reads `gdp/Block4_channel_breaks.shp`
(remove the layer before a rewrite, QGIS locks shapefiles; re-add afterwards with `W5/gis/Block4_channel_breaks.qml`).

## Findings

- The delineated catchment's outlet (495922.5, 2651832.5) is 1.4 km east of the flow point it feeds (the start of
  SHA-CH13-SS at 494670, 2651149, which is also a road/OQ fix point); the engineer assigned it there deliberately.
- Fix point snapping tolerance 60 m, channel-end tolerance 15 m; every point snapped at the first try.
