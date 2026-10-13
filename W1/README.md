# Block 4 — HMS Depth-Area Results Extraction

Outputs derived from the HEC-HMS Block 4 depth-area (DAA) runs in
`Data/HEC_HMS_Block_04`, covering 13 return periods: 2, 5, 10, 25, 50, 100,
200, 500, 1000, 2000, 5000, 10000 yr and PMP.

## Run order

```
python scripts/01_extract_from_dss.py          # -> output/peak_flow_volume.csv
python scripts/02_build_excel_flow_volume.py   # -> output/peak_flow_volume_all_elements.xlsx
python scripts/03_build_dam_junctions_excel.py # -> output/dam_junctions.xlsx
python scripts/04_build_point_shapefile.py     # -> output/shp/
python scripts/05_export_kmz.py                # -> output/KMZ/
```

Scripts 02–05 all depend on the CSV from 01. Scripts 03 and 05 are otherwise
independent of each other; 05 requires the shapefile from 04.

Requires `hecdss`, `pandas`, `openpyxl`, `pyshp`, `pyproj`.

## Method

- Values are read from each element's **own analysis point** (DSS B-part equals
  the F-part suffix after `>`), so each element reports its own depth-area
  reduced result rather than a neighbour's.
- Peak = max of the time series. Volume = sum × 300 s ÷ 1e6 [Mm³], the 300 s
  coming from the 5-minute time interval in `Control_1.control`.
- Coordinates are Canvas X/Y from `Basin_1.basin`, EPSG:32640 (UTM zone 40N),
  confirmed against the srid recorded in `Basin_1.sqlite`.

## Outputs

| File | Contents |
|---|---|
| `output/peak_flow_volume.csv` | Long format, 1092 rows = 84 elements × 13 RPs |
| `output/peak_flow_volume_all_elements.xlsx` | Peak flow and volume pivots, all 84 elements |
| `output/dam_junctions.xlsx` | 9 dam locations: hydrographs, peak inflow, inflow volumes |
| `output/shp/points_peak_flow_volume.shp` | 30 junctions, Q/V per RP, `is_dam` flag |
| `output/KMZ/` | 27 files — `All_Junctions.kmz` plus Q and V per RP |

## Dam locations

The 9 named junctions (`is_dam = 'Y'` in the shapefile; generic `J*` junctions
are `'N'`):

Hawasinah 02, Hawasinah 11, Hawasinah EX, Shafan 02, Shafan 08,
Sarami 03, Sarami 05, Sakhin 04, Sakhin 08.

## Two structural differences from the reference project

**No reservoir elements.** The Block 4 basin has 32 subbasins, 30 junctions and
22 reaches — no reservoirs, diversions or sinks. There is therefore no routing
and no attenuation at the dam sites: script 03 verifies that `FLOW` and
`FLOW-COMBINE` are identical at all 9 junctions across all 13 RPs, and they
are. `dam_junctions.xlsx` reports **inflow only**. Outflow cannot be derived
without reservoir elements in the model.

**No basin or reach geometry.** `Basin_1.sqlite` carries the geometry schema but
zero rows, and `Basin_1.basin` stores only point coordinates. The KMZ set is
therefore points-only — the Basins and Reach layers from the reference project
have no source data in this model.

## Verification performed

- 1092 rows extracted with zero missing (element, RP) combinations.
- Peak flow increases monotonically with return period for all 84 elements.
- `FLOW` == `FLOW-COMBINE` at every dam junction, confirming no storage.
- Reprojected dam coordinates fall at 23.8–24.1°N, 56.7–57.0°E in Al Batinah.
- Values cross-checked between the CSV, the shapefile attributes and the
  workbook.

No peak or volume figures are stored in the HMS `.out` or `.results` files, so
these checks are internal. Spot-check a few values against the HMS GUI before
issuing.
