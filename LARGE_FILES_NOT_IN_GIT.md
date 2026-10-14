# Files not in this repository (100 MB and more; GitHub's limit without Git LFS)

| File | Size (MB) |
|---|---|
| `W2/output/terrain/reconditioned_CH_WALL_10m.tif` | 122 |
| `W3/maps/data/depth_200yr_plain.tif` | 109 |
| `W3/sediment/rusle/Data/FlowAccum/flowaccum_30m.tif` | 143 |
| `W3/sediment/rusle/Data/Landsat8/landsat8_2017_B4B5.tif` | 118 |
| `W4/civil3d/Block04_Channels_Surfaces.bak` | 168 |
| `W4/civil3d/Block04_Channels_Surfaces.dwg` | 168 |
| `W4/civil3d/Block04_Channels_Surfaces_C3Dtemplate.dwg` | 125 |
| `W5/civil3d/Backup/1 Block04_Channels_W5.dwg` | 119 |
| `W5/civil3d/Backup/10 Block04_Channels_W5_before_junction_fix_20261010_0209.dwg` | 118 |
| `W5/civil3d/Backup/11 Block04_Channels_W5.dwg` | 119 |
| `W5/civil3d/Backup/12 Block04_Channels_W5.dwg` | 119 |
| `W5/civil3d/Backup/13 Block04_Channels_W5_before_junction_fix_2_20261010_1234.dwg` | 119 |
| `W5/civil3d/Backup/14 Block04_Channels_W5.dwg` | 119 |
| `W5/civil3d/Backup/2 Block04_Channels_W5.dwg` | 118 |
| `W5/civil3d/Backup/3 Block04_Channels_W5.dwg` | 118 |
| `W5/civil3d/Backup/4 Block04_Channels_W5.dwg` | 119 |
| `W5/civil3d/Backup/5 Block04_Channels_W5.dwg` | 119 |
| `W5/civil3d/Backup/6 Block04_Channels_W5.dwg` | 118 |
| `W5/civil3d/Backup/7 Block04_Channels_W5.dwg` | 119 |
| `W5/civil3d/Backup/8 Block04_Channels_W5.dwg` | 119 |
| `W5/civil3d/Backup/9 Block04_Channels_W5.dwg` | 118 |
| `W5/civil3d/Block04_Channels_W5.bak` | 119 |
| `W5/civil3d/Block04_Channels_W5.dwg` | 118 |
| `W6/civil3d/Backup/1 Block04_Channels_W6.dwg` | 119 |
| `W6/civil3d/Backup/2 Block04_Channels_W6.dwg` | 118 |
| `W6/civil3d/Block04_Channels_W6.bak` | 118 |
| `W6/civil3d/Block04_Channels_W6.dwg` | 118 |
| `W6/sewergems/sheets/archive/R4_200yr/PDF/Set/2224-PD-HY-PP-B4_Plan_and_Profile_Drawings_200yr_R4.pdf` | 393 |
| `W6/sewergems/sheets/scripts/PDF/Set/2224-PD-HY-PP-B4_Plan_and_Profile_Drawings_200yr_R4.pdf` | 393 |
| `W6/sewergems/sheets/scripts/PDF/Set/2224-PD-HY-PP-B4_Plan_and_Profile_Drawings_200yr_R5.pdf` | 394 |
| `W6/sewergems/sheets/scripts/PDF/Set/2224-PD-HY-PP-B4_Plan_and_Profile_Drawings_200yr_R6.pdf` | 394 |
| `W6/sewergems/sheets/scripts/PDF/Set/2224-PD-HY-PP-B4_Plan_and_Profile_Drawings_200yr_R7.pdf` | 394 |
| `W6/sewergems/sheets/scripts/PDF/Set/2224-PD-HY-PP-B4_Plan_and_Profile_Drawings_200yr_R8.pdf` | 394 |
| `W7/sewergems/sheets/scripts/PDF/Set/2224-PD-HY-PP-B4_Plan_and_Profile_Drawings_200yr_R9.pdf` | 394 |
| `W8/sewergems/sheets/scripts/PDF/Set/2224-PD-HY-PP-B4_Plan_and_Profile_Drawings_200yr_R9.pdf` | 431 |
| `W8/sewergems/sheets/scripts/PDF/Set/2224-PD-HY-PP-B4_Stormwater_Channels_Plan_and_Profile_Drawings_200yr_R9.pdf` | 349 |
| `gis/reconditioned_CH_WALL_10m.tif` | 122 |

Also left out: the generated sheet intermediates (DXF, per-sheet PDFs, satellite tile caches, the combined PDFs per channel) and the AutoCAD backups; the drawing sets are in the submission folder.
| `W9/bypass/civil3d/Block04_Channel_Profiles_Bypass.dwg` | 113 |
| `W9/volumes/SAR-CH1-FP/ground_2m.tif` | 151 |

## Also left out: derived rasters under 100 MB

`W9/volumes/<channel>/ground_2m.tif` (37 files, 811 MB in all): the 0.5 m project ground resampled to 2 m over each channel corridor,
written by `W9/scripts/73_terrain_w9.py` from the project DEM (`Block 4\Hydraulic\Terrain\GGC_4_MERGE_HDSM.tif`, a copy of the server DTM).
The channel surfaces, quantities and the merged terrain rasters (`W9/terrain`) are in the repository.
