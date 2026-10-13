# W4 — Civil 3D surfaces and ground profiles of the Block 4 channels and dykes (started 2026-10-07, Oman date)

**Superseded for the drawing by `W5/` (2026-10-07):** the two W4 drawings are kept as the record of the first build; the
live Civil 3D drawing is `W5/civil3d/Block04_Channels_W5.dwg`. W4's geometry (points, boundaries, centrelines, view
placement, LandXML) stays the source and is read unchanged by W5. Why superseded: the W4 profile views were illegible
(view style "Major Grids": ticks every 20/10 m horizontally and 2/1 m vertically; band set "Land Desktop Standard Band
Set" with a label interval of 0, which labels every sampled point; 3.5 mm text at 1:1000 over kilometre-long views) and
every leader's text sat at the origin (the MLeader was created without an MText location). Purpose of W4: give the channel design its Civil 3D base, light-weight: one small ground surface per channel
and per dyke (the 1 m corridor of the centreline on the 0.5 m project DEM, nothing interpolated between channels), one
named alignment per feature, one existing-ground profile per alignment, one profile view per alignment (channel views
near their own alignment, dyke views in a separate stack), and the terrain point DWG of the corridors.

Inputs: the centrelines `Hydrology\SHP\temp\Channels and Dykes 04102026.shp` (Block = 4 only: 37 channels 224.1 km,
36 dykes 62.5 km, named `<GCA>-<CH|D><n>-<FP|SM|SS>`, identical to `Hydrology\DWG\Channels and Dykes 04102026.dwg`) and
the 0.5 m DEM `\\FILESERVER-\Works\...\GGC4_DTM_GMAP_NSA.tif` (the shortcut in `Hydrology\DWG\Claude for CAD Points\Data\Terrain`;
GDAL needs the forward-slash form of the UNC path). The August 2026 corridor-points run in `Hydrology\DWG\Claude for CAD
Points\W1` is the method's origin (0.5 m buffer each side, pixel-centre rule, tile-parallel windowed reads).

| Folder | Contents | State |
|---|---|---|
| `lines/` | `Block4_lines.gpkg/.shp/.csv` (order, name, kind, class, catchment, length, ends), `Block4_centrelines.dxf` (one polyline per feature on layer `CH_<name>` / `D_<name>`) | done |
| `points/` | `Terrain_Points_B4_0.5m.dxf` (1 146 232 POINT entities, 4 per metre, one layer `PT_<name>` per feature, 84 MB), `csv/<name>.csv` (P,E,N,Z,D point files), `strips/<name>.tif` (the same cells as a GeoTIFF strip per feature), `Block4_buffers_0.5m.gpkg` (the corridors), `points_summary.csv` | done |
| `landxml/` | `Block4_channels.xml` (86 MB) and `Block4_dykes.xml` (24 MB): one TIN surface per feature (Delaunay on the corridor cells, triangles outside the corridor removed) + one alignment per feature; `*_with_EG_profiles.xml` the same plus static ground profiles sampled every 0.5 m (the self-contained fallback); `surfaces_summary.csv` | done |
| `civil3d/` | `Block04_Channels_Surfaces.dwg` (160 MB): first build on the Autodesk metric NCS template by LandXML import, 73 surfaces + alignments + ground profiles, no views. `Block04_Channels_Surfaces_C3Dtemplate.dwg` (119 MB): second build on the project template by the own command `W4BUILD` (73 surfaces `EG <name>`, alignments `<name>`, ground profiles `EG <name>`, views `PV <name>` at the positions of `profile_views.csv`, 73 leaders), illegible views and leaders at the origin, see above. `build_spec.json` (per feature: corridor boundary ring, centreline vertices deduplicated at 1 mm, view insertion), `profile_views.csv`, QA sketch `profile_view_layout.png/.dxf`, `qa/` (plots of the second build: `diag_extents.png` shows the leaders running to the origin). `tool/W4ProfileViews`: the C# command assembly `W4Tools.dll` (`W4BUILD`, `W4PV`, `W4PVDEL`; .NET 8 against the Civil 3D 2026 managed assemblies, staged at `C:\Civil3D-mcp\tools\W4Tools.dll`) | superseded by W5 |
| `scripts/` | `config_w4.py`, `01_lines_block4.py`, `02_terrain_points.py`, `03_landxml.py`, `04_profile_view_layout.py`, `05_dem_strips.py`, `06_build_spec.py` (run in order), `07_run_w4build.py` (COM: NETLOAD + `W4BUILD`), `09_qa_plot.py` (COM plot to PNG; its window plot is blank in Civil 3D 2026, W5's version zooms and plots the display) | done |
| `log/` | run logs | |

## How the Civil 3D drawing is built (and rebuilt): no dialogs, no clicking

1. Scripts 01–06 (plain Python, 4 min; the DEM sampling takes 100 s over the network with 16 workers).
2. Civil 3D 2026 open, a new drawing from the project template `Hydrology\DWG\C3D template\C3D Template.dwt` (the MCP
   plugin's `drawing new` with that template; saved as `civil3d/Block04_Channels_Surfaces.dwg`).
3. `scripts/07_run_w4build.py`: through Civil 3D's COM interface it NETLOADs `C:\Civil3D-mcp	ools\W4ProfileViews.dll`
   (the built copy of `civil3d/tool/W4ProfileViews`; NETLOAD refuses paths with spaces) and runs **`W4BUILD`**, which reads
   `civil3d/build_spec.json` and `points/csv/<name>.csv` and creates, per feature and skipping what already exists: the TIN
   surface `EG <name>` from the corridor cells with the corridor polygon as outer boundary (nothing interpolated between
   channels), the alignment `<name>` (fixed lines through the centreline vertices, the template's first alignment style
   and label set, no site), the existing-ground profile `EG <name>` (surface profile, the template's "Existing" profile
   style if it has one), the profile view `PV <name>` at the insertion point of `profile_views.csv` (channel views beside
   their alignment, dyke views in one column east of the block), and an MLeader from the view to the alignment's start
   with the names (layers `W4-PV-LEADER-CHANNELS` and `W4-PV-LEADER-DYKES`, the latter long: freeze it when not needed).
   It also assigns the coordinate system UTM84-40N. `W4PVDEL` erases the views and leaders, `W4PV` recreates them (after a
   re-run of step 04 with another vertical exaggeration, for instance).
4. The LandXML files remain the hand-import alternative (Insert > LandXML) and the portable exchange format.

## Findings and traps

- **W4BUILD results (2026-10-07):** run 1 made 26 features and failed 47 with "Value does not fall within the expected
  range" from `AddFixedLine`: zero-length segments from duplicate consecutive vertices in the shapefile; `dedupe()` (1 mm)
  added to `06_build_spec.py` and `03_landxml.py`; run 2 made the remaining 47 in 72 s. Styles were taken as the first of
  each collection ("Major Grids", "Land Desktop Standard Band Set"): the cause of the illegible views. The MLeader needs
  its MText created with a Location and `TextLocation` set, else the text lands at the origin (fixed in W5).
- **NETLOAD of an unsigned assembly** shows the security prompt "Load Once / Always Load"; one click, no change to the
  trusted paths. The assembly must sit at a path without spaces, and it cannot be reloaded in the same session (rebuild
  under a new name or restart Civil 3D).
- **The Civil 3D MCP plugin** (`C:\Civil3D-mcp`, loaded with NETLOAD, HTTP on port 8080) works for listing, surface
  elevations, `profile create_from_surface`, drawing new (with a template path)/save. Its surface creation (`create_from_dem`, `add_points`,
  `add_boundary`), its `profile_view_create` and its statistics are guesses at API names and fail or return zeros in
  Civil 3D 2026; `drawing undo` does nothing. It cannot import LandXML. Hence the own command `W4BUILD` built on the real API (`TinSurface.Create` + `AddVertices` + `BoundariesDefinition.AddBoundaries`,
  `Alignment.Create` + `Entities.AddFixedLine`, `Profile.CreateFromSurface`, `ProfileView.Create`, `MLeader`).
- **LANDXMLIN ignores FILEDIA**: it always opens its file dialog; a command sent from outside while that dialog is up
  blocks the plugin and COM until the dialog is closed. The dialog remembers the last file and goes straight to the
  options page; use *Browse...* for the next file.
- **Profile view footprint**: alignment length by (elevation range + 4 m) × 10 (the style's vertical exaggeration) + 40 m
  of bands; channel views sit a median 1.7 km from their alignment (0.15–8 km), between the corridors of the other
  alignments; dyke views in one column east of the block at x = 511 948.
- **Terrain points**: 188 (SHA-D16-SS, 47 m) to 70 581 (SAR-CH1-FP, 17.6 km) cells per feature; the nearest corridor
  cell is at most 0.53 m from any station of the centreline.
