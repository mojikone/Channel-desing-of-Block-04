# W5 — Civil 3D drawing of the Block 4 channels and dykes, rebuilt on the project template (2026-10-07, Oman date)

**Live iteration.** The Civil 3D base of the channel design: `civil3d/Block04_Channels_W5.dwg` (113 MB, Civil 3D 2026,
UTM84-40N, from `Hydrology\DWG\C3D template\C3D Template.dwt`). Supersedes the W4 drawings, which stay as the record of
the first build: their profile views were illegible (view style "Major Grids" with 20/10 m ticks and a band set whose
label interval is 0, so every sampled point was labelled) and every leader's text sat at the origin. W4's geometry is
reused unchanged: corridor points (`W4/points/csv`), corridor boundaries and centreline vertices
(`W4/civil3d/build_spec.json`), profile-view placement (`W4/civil3d/profile_views.csv`).

Method (engineer's instruction 2026-10-07): a new drawing from the template; ONE channel first (SHA-CH6-SM, 5.3 km) with
the template's styles chosen explicitly and checked; then all 73.

## What the drawing contains (census of 2026-10-07, `cs/13_census.cs` → `civil3d/qa/census.json`)

| Object | Count | Name / style / layer |
|---|---|---|
| TIN surfaces | 73 | `EG <name>`, the 1 m corridor cells with the corridor polygon as outer boundary; style "Border Only"; layer C-TOPO |
| Alignments | 73 | `<name>` (37 channels, 36 dykes), fixed lines through the centreline vertices; "ARJV_ (Alignment)" + "ARJV_Alignment Label Set"; layer C-ROAD |
| Ground profiles | 73 | `EG <name>`, dynamic surface profiles; "ARJV_ Existing Ground Level" + "_No Labels"; layer C-ROAD-PROF |
| Profile views | 73 | `PV <name>`; "ARJV_ Land Desktop Profile View" (VE 10, ticks 50/25 m horizontal, 5 m vertical, 2.5 mm text at 1:1000) with band set "HTJ (EG-FG Elevations and Stations)" (stations and elevations at 50/25 m); layer C-ROAD-PROF-VIEW; channel views beside their alignment, dyke views in one column at x = 511 948 |
| Leaders | 73 | multileader from the view's lower-left corner to the alignment start, text `PV <name>  <-  alignment <name>` 15 m high; layers W5-PV-LEADER-CHANNELS (red) and W5-PV-LEADER-DYKES (magenta); all vertices inside the block |

**Direction correction (engineer, 2026-10-07):** SAK-CH1-FP, SHA-CH11-SS, SHA-CH1-FP, SHA-CH17-SS and SAK-D4-FP are
digitised against the flow in the source shapefile; `civil3d/corrections.json` lists them and the build reverses their
centreline vertices (`20_prototype.py`), so station 0 is at the upstream end. `scripts/22_reverse_features.py` deleted
their alignment, profile, view and leader (`cs/14_delete_feature.cs`), rebuilt them and verified that the new start
equals the old end (5 of 5, log `log/22_reverse_features.log`). The source shapefile and the W4 files keep the original
vertex order; flip those five in QGIS before the next export, or the correction list has to stay.

**Centreline update (engineer, 2026-10-07 05:15):** the engineer trimmed channel ends in the source shapefile so that
start and end sit at the proper locations. `scripts/23_update_lines.py` reads the shapefile (Block = 4), compares every
feature with the W4 geometry and writes `civil3d/build_spec_w5.json` (the W4 spec with the new vertices and a per-feature
`reverse` flag that keeps the approved direction: a new line is reversed when its first vertex is nearer the approved end),
`lines/Block4_lines_w5.gpkg/.csv` and the change report `civil3d/qa/line_changes.csv`. 17 channels changed, all
shortened (11 m to 503 m: HAW-CH1-FP, HAW-CH7-SS, SAK-CH2-FP, SAK-CH3-SM, SAK-CH4-SS, SAK-CH5-SS, SAR-CH1-FP, SAR-CH2-SM,
SHA-CH1-FP, SHA-CH3-SM, SHA-CH4-SM, SHA-CH6-SM, SHA-CH7-SM, SHA-CH9-SS, SHA-CH10-SS, SHA-CH16-SS, SHA-CH19-SS); the
corridor surfaces still cover them, so only alignment, profile, view and leader were deleted and rebuilt
(`scripts/24_update_features.py`, 17 of 17 verified against the spec, log `log/24_update_features.log`). The five
reversed features stay reversed (the shapefile still has their original order). `20_prototype.py` reads the W5 spec
when it exists, so a full rebuild also uses the edited lines.

**Frozen on 2026-10-10 (engineer):** `gdp/Block4_channel_breaks.*` and `gdp/Block4_channel_segments.*` stay as they
are after the junction fix; the live copies that follow his further profile edits are in `W6/gdp/` (the update script
`scripts/27_gdp_from_drawing.py` writes there now).

**Junction fix (2026-10-10, W6):** the 22 GDPs of channels ending on another channel had their last PVI set to the
receiver's GDP elevation (engineer's instruction); the previous lines remain as dashed magenta profiles `GDP <name>
(before junction fix)`; backup of the drawing before the change in `civil3d/backup/`. Detail in `W6/README.md`.

## Ground design profiles (GDP) for SewerGEMS (2026-10-07)

The engineer designs the channels in SewerGEMS and needs, per channel, a **ground design profile**: a line through
ground points with a grade break wherever the ground trend changes, ignoring noise, so that the channel can be split
into straight-slope segments (nodes at the breaks, SewerGEMS samples the ground there). His method, shown in the sample
profile `SAK-CH3-SM GDP` in the drawing: connect start and end, add a break at the largest departure from the ground,
repeat until it follows the terrain. That is the Ramer-Douglas-Peucker rule with a vertical tolerance; `scripts/25_gdp.py`
runs it for the 37 channels:

1. the EG profile of the alignment read from the drawing every 1 m (`cs/30_read_profiles.cs`; a few cells without
   ground carry the previous value);
2. the trend: rolling median over 201 m then rolling mean over 51 m (removes road/bund crossings and single-cell
   spikes, which the raw rule chases: 16 breaks on SAK-CH3-SM at 1.5 m on the raw ground);
3. breaks by the rule on the trend with a 0.75 m tolerance (calibration: the engineer's 5-PVI sample departs 0.87 m
   from the 201 m trend and 2.25 m from the raw ground; 0.75 m gives 6 breaks on SAK-CH3-SM, one at 3 321 m next to
   his 3 357 m; his break at 980 m is a judgement the rule does not find);
4. each break stitched to the raw ground (moved up to 30 m to a sample within 0.3 m of the trend); the two ends stay at
   the alignment ends and take the trend elevation when the ground there is a spike;
5. in the drawing: layout profile `GDP <name>` (style "ARJV_Design Profile", no labels, replaced on re-run) and the
   breaks marked in plan on layer `W5-GDP-BREAKS` (circle + text `<name> GB<i> station z`; `cs/31_create_gdp.cs`);
6. for SewerGEMS: `gdp/Block4_channel_segments.shp/.csv` (the centreline split at the breaks; Label `<name>-<seg>`,
   StaFrom/StaTo, Length_m, ZFrom/ZTo, Slope) and `gdp/Block4_channel_breaks.shp/.csv` (points; Label `<name> GB<i>`,
   Station, Z_m, X, Y, GradeIn/GradeOut), `gdp/gdp_summary.csv` (per channel: breaks, segment lengths, departures),
   `gdp/gdp_parameters.json`.

7. **no reverse slope** (engineer, 2026-10-07: a channel invert cannot climb downstream): a segment whose downstream
   end is higher is merged with a neighbour, dropping whichever of its two breaks keeps the trend closest to the merged
   chord, until every segment is level or falls (`--min-slope`, default 0, sets the smallest fall allowed); a channel
   whose end is higher than its start would be flagged (none is).

**Reviewed (engineer, 2026-10-08):** the engineer adjusted every `GDP <name>` in Civil 3D by hand. From then on the
drawing's profiles are the source: `scripts/27_gdp_from_drawing.py` reads their PVIs (`cs/33_read_gdp.cs`), redraws the
plan markers from them (`cs/34_mark_breaks.cs`), rewrites the break and segment files and the summary, saves the
drawing; the rule of `25_gdp.py` is not re-applied. Reviewed state: 37 channels, **241 breaks, 204 segments** (2 to 14
breaks per channel; segment lengths 115 m to 5 682 m, median 929 m; no reverse slope, 3 segments flatter than 0.05 %).
The reviewed end PVIs sit up to 1.5 m inside the alignment ends; the files snap those two stations to the ends
(elevations kept) so the segments cover the whole centreline. `gdp/gdp_reviewed_pvis.json` holds the PVIs as read.
The QGIS group was refreshed with the reviewed files (QGIS locks a loaded shapefile: remove the layer, write, re-add).

Rule-based result before the review (run of 2026-10-07 06:02, `--min-seg 100`): 37 channels, 288 breaks, 251 segments; no reverse slope, 7 segments
flatter than 0.05 %, 19 breaks dropped for reverse slope on 15 channels; segment lengths median 681 m, longest 5 682 m,
three under 100 m (75–92 m, their break is needed to stay within 1.5 m of the trend); the trend departs up to 2.04 m
from a GDP where a merge spans a local rise (12 channels over 1 m: the line cuts through highs), the raw ground up to
5.5 m (SHA-CH4-SM, a crossing). Earlier runs: 323 breaks / 286 segments without a minimum segment (19 under 100 m,
shortest 22 m); 307 / 270 with 100 m before the slope rule. Re-run with another tolerance, trend window, minimum
segment or minimum slope (`--tol`, `--window`, `--min-seg`, `--min-slope`): one minute, profiles and files are
replaced. The engineer's sample `SAK-CH3-SM GDP` is left in the drawing beside `GDP SAK-CH3-SM`. Dykes are not included (no SewerGEMS
element); `25_gdp.py <dyke names>` would work the same way.

Views span 47 m (SHA-D16-SS) to 17.6 km (SAR-CH1-FP, 111 m of elevation range). Annotation scale 1:1000 as in the
template. The styles are the template's own command defaults (`civil3d/styles.json` records them and why); the surface
style "Border Only" is a template style chosen for lightness instead of the template's contour default (a 1 m corridor
has no meaningful contours).

| Folder | Contents | State |
|---|---|---|
| `civil3d/` | `Block04_Channels_W5.dwg` (live), `styles.json` (the chosen template styles), `corrections.json` (features built with the centreline reversed), `build_spec_w5.json` (the live build spec: edited centrelines + reverse flags, W4 boundaries and view insertions), `qa/` (+ `line_changes.csv`) (`style_inventory.json`, `band_styles.json`: everything the template offers; `census.json`; `inspect_<name>.json`; `qa_*.png` plots) | done |
| `scripts/` | `c3d_mcp.py` (MCP stdio client), `10_new_drawing.py` (COM: new drawing from the template, save, close the W4 drawings), `20_prototype.py` (build one feature / `--all`, `--inspect`, `--save`; applies `corrections.json`), `21_qa_plot.py` (COM plots to PNG), `22_reverse_features.py` (delete + rebuild the reversed features, verify, save), `23_update_lines.py` (edited shapefile → W5 spec + change report), `24_update_features.py` (delete + rebuild the changed features, verify, save), `25_gdp.py` (ground design profiles + SewerGEMS segment/break files; `--calibrate`), `26_stations_gis.py` (station points + QML styles for the QGIS review) | done |
| `lines/` | `Block4_lines_w5.gpkg/.csv`: the edited Block 4 centrelines of 2026-10-07 05:15 with the `reverse` and `changed` flags | done |
| `gis/` | review layers for the engineer's QGIS (`26_stations_gis.py`): `Block4_alignment_stations.gpkg/.shp` (2 948 station points every 100 m on the 73 alignments, Civil 3D label form `k+mmm`, majors every 500 m, start/end named, line bearing for the tick markers) and the QML styles of the stations, the GDP breaks and the GDP segments (slope labels). Added 2026-10-07 to the engineer's open project `Hydrology\QGIS\QGIS Block 04.qgz` as group "W5 Civil 3D review" through the QGIS MCP (his project, unsaved: he keeps or drops the group) | done |
| `gdp/` | the ground design profiles' outputs for SewerGEMS: `Block4_channel_segments.shp/.csv`, `Block4_channel_breaks.shp/.csv`, `gdp_summary.csv`, `gdp_parameters.json`, `sample_SAK-CH3-SM.json` (the engineer's sample as read) | done |
| `cs/` | the C# bodies run inside Civil 3D: `01_style_inventory.cs`, `02_band_styles.cs`, `11_build_feature.cs` (one feature, placeholders filled by 20), `12_pv_inspect.cs`, `13_census.cs`, `14_delete_feature.cs`, `15_relocate_leaders.cs`, `30_read_profiles.cs` (profiles + EG samples of an alignment), `31_create_gdp.cs` (layout profile from PVIs + plan markers) | done |
| `log/` | `c3d_mcp.log` (every MCP call), `20_prototype.log`, `20_build_all.out` | |

Build time: 29 s for the 73 features (0–1 s each; the W4 command needed 72 s for 47 because it created the leaders'
text at the origin and the dense views). Rebuild: `python scripts/20_prototype.py --all --save` on an open template
drawing (existing objects are skipped, so a feature can be deleted in Civil 3D and rebuilt alone).

## Tooling: the civil3d-roslyn MCP server

Chosen on the engineer's instruction to find and install the best Civil 3D MCP on GitHub (2026-10-07). Survey (GitHub
API, stars / last push): Sacred-G/Civil3D-mcp (41 stars, 180 fixed tools; the one previously installed at `C:\Civil3D-mcp`,
whose surface creation, profile-view creation, style listing and statistics are guesses at API names), barbosaihan/civil3d-mcp
(38 stars, 19 forks, May 2026: Roslyn C# execution, 3 tools), **nezolder/civil3d-mcp-roslyn** (fork of barbosaihan with
tests, drawing guards, api_lookup, pushed the day before), SantosSjba/mcp-to-c3d (fork, sandbox modes), shtirlitsDva/cad-mcp
(Roslyn session, named pipes, licence "TBD", plugin only in a release zip), Jjo37/new-acad (270 fixed tools + its own LLM
palette), HorizunGroup, arihov, KevinGriffin (fixed tools). The Roslyn family is the right kind for this work: the AI
sends C#, the plugin compiles and runs it inside Civil 3D with the real API, no assembly reload per iteration. nezolder's
fork was taken as the maintained one; barbosaihan's original is the fallback.

Install (`C:\mcp\civil3d-mcp-roslyn`): `npm install && npm run build`; the five Civil 3D 2026 reference DLLs copied to
`C_References`; `dotnet build -c Release -p:AssemblyName=Civil3dMcpRoslyn` in `plugin/Civil3dMcpPlugin` (renamed because
the Sacred-G plugin loaded in the same session is also called Civil3dMcpPlugin and .NET refuses a second assembly of the
same name); NETLOAD through COM (`(command "NETLOAD" "...")` with FILEDIA 0) + one click on **Load Once** in the
security prompt; `claude mcp add --scope user civil3d-roslyn -- node C:\mcp\civil3d-mcp-roslyn\build\index.js`. The
plugin listens on a free localhost port (8080 was taken by the older plugin) and writes an endpoint record to
`%LOCALAPPDATA%\Civil3dMcpRoslyn\endpoints`; `scripts/c3d_mcp.py` reads it and pins `CIVIL3D_PORT`, otherwise the server
sees two instances and refuses (`CIVIL3D.INSTANCE_SELECTION_REQUIRED`). The MCP tools reach Claude Code after a session
restart; until then the same server is driven over stdio by `c3d_mcp.py`.

Script rules learned: bodies get `Document, CivilDoc, Database, Transaction, Editor`; add `using
Autodesk.Civil.DatabaseServices.Styles; using Autodesk.Civil.Settings;` (not auto-imported); `Application` is ambiguous,
use `Autodesk.AutoCAD.ApplicationServices.Core.Application`; `civil3d_skills api_lookup` returns the real signatures
(`AddFixedLine(Point3d, Point3d)`, `ProfileView.Create(alignId, Point3d, name, bandSetId, viewStyleId)`,
`SettingsObjectLayerType`, `DisplayStyle.Lineweight`); `civil3d_execute` needs the drawing identity from a prior query
and commits its transaction; `saveDrawing: true` saves afterwards; a 1000-item cap on returned collections.

## Findings and traps

- **Why W4 looked wrong:** the first style of each collection had been taken. "Major Grids" ticks every 20/10 m and
  2/1 m; "Land Desktop Standard Band Set" has a label interval of 0 → a label at every sampled point → solid bars. The
  template's own defaults (read from its command settings) are the ARJV view style and the HTJ band set.
- **Legibility is a scale question, not a style bug:** at 1:1000 a 5 km view is 5 m of paper; whole-view zoom shows
  212 vertical grid lines (every 25 m) and text 2.5 m high. Zoomed to a few hundred metres it reads like a sheet. Two
  cheap options if the engineer wants more at whole-view zoom: a derived view style with 100/50 m ticks (halves the
  lines), or an annotation scale 1:2000–1:5000; both apply to the 73 views by one script, no rebuild.
- **MLeader:** create the MText with `Location`, assign `ml.MText`, then `AddLeader` / `AddLeaderLine(ld)` /
  `AddFirstVertex` / `AddLastVertex` and set `TextLocation`; without the location the text and the landing go to the origin.
- **Plotting to PNG through COM:** `Plot.PlotToFile` with "PublishToWeb PNG.pc3" works for display/extents plots only
  (a window plot is blank in Civil 3D 2026); set `UseStandardScale = True` before `StandardScale = 0` or the template's
  custom scale plots a blank page; the PNG media is portrait, so plot rotated 90° and turn the image back.
- **COM goes dead while a selection prompt is pending** in Civil 3D ("Specify opposite corner"): `GetAcadState().IsQuiescent`
  false, `ActiveDocument` fails; one Escape in Civil 3D frees it.
