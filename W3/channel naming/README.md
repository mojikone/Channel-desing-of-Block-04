# Channel naming — Block 4 channels and dykes (2026-10-06)

Names the 73 Block 4 features of `Hydrology\SHP\temp\Channels and Dykes 04102026.shp` (field `Block` = 4) after the
Block 6 convention, and writes them into the `Name` field of that shapefile through the layer open in QGIS
(`Hydrology\QGIS\QGIS Block 04.qgz`, layer "Channels and Dykes 04102026"). Block 2 and Block 6 rows are untouched.

**State: applied.** Committed to the source shapefile on 2026-10-06 (73 names, verified on disk against the CSV; Block 2/6
attributes and every geometry identical to the pre-edit copy). The engineer's review of the five flagged catchment
assignments is pending (see *Open*).

| Folder / file | What it is |
|---|---|
| `scripts/name_channels.py` | the whole rule, one run: reads the source shapefile and `GCA RENN.shp`, writes `output/` |
| `input/source_copy_20261006/` | the source shapefile as received, `Name` empty for Block 4 — the roll-back copy |
| `output/block4_channel_names.csv` | one row per Block 4 feature: QGIS fid, CHtt, catchment and its share of the length, sort key, number, Name, flag |
| `output/block4_naming_flags.csv` | the five features whose catchment share is below 90 % |
| `output/Channels and Dykes 04102026 named.shp` | the full layer (247 rows) with Block 4 names — the same content the source now carries |
| `output/Block04_channel_names.gpkg` | layer `block4_named`: Block 4 only, with the check fields, for QGIS |
| `output/block6_name_audit.csv` | where the Block 6 names depart from their own rule (information, nothing changed there) |

## The rule

`<GCA>-<CH|D><n>-<FP|SM|SS>`, as `HAW-CH1-FP`.

- **GCA** — first three letters, upper case, of the global catchment name (field `J_CA` of
  `W:\...\18 Channel Design\Hydraulic\Block 6\Report\Hydraulic Design of Stormwater Channels\Data\GCA RENN.shp`). A leading
  two-letter word is dropped (`Al Hawasinah` → HAW); letters only (Block 6 wrote `Ma'awil` as Maa). Block 4: HAW, SHA, SAR, SAK,
  the codes the HMS Basin 2/3 elements already use.
- **Catchment of a feature** — the one holding the largest share of its length (intersection with the GCA polygons).
- **CH / D** — from `CHtt` (`... CH` channel, `... D` dyke); cross-checked against `CHtype` (1–3 channel, 4–6 dyke).
- **n** — one counter per catchment for channels and a separate one for dykes, continuous across the classes:
  flood protection first, then stormwater main, then stormwater secondary; inside a class from west to east by the
  westernmost vertex (smallest x, EPSG:32640).
- **FP / SM / SS** — from `CHtt`: `FP CH`/`FP D`, `Sw M CH`/`Sw M D`, `Sw S CH`/`Sw S D`.

Decisions taken here that the instruction left open (each is one line in the script):
1. Upper-case prefix (`HAW`) as in the engineer's example; Block 6 used Title case (`Taw`). `PREFIX_UPPER` switches it.
2. "Left to right" = westernmost vertex. Block 6 follows its own west-to-east order only loosely (rank correlation
   about 0.55 between number and x, whichever x is used — minimum, centroid, start or end), so no key reproduces Block 6
   exactly; the westernmost vertex is the literal reading and marginally the best fit.
3. Catchment by majority length; anything under 90 % is flagged, not resolved.

## Result

| Catchment | Channels | Dykes |
|---|---|---|
| Al Hawasinah (HAW) | 7 | 3 |
| Shafan (SHA) | 21 | 23 |
| Sarami (SAR) | 4 | 4 |
| Sakhin (SAK) | 5 | 6 |

Five features straddle a catchment boundary (`block4_naming_flags.csv`):

| QGIS fid | Name given | Shares of length |
|---|---|---|
| 216 | HAW-CH7-SS | Al Hawasinah 53 %, **Mashin 47 %** (Mashin is not a Block 4 catchment) |
| 179 | HAW-D1-FP | Al Hawasinah 59 %, Shafan 41 % |
| 212 | SAK-D3-FP | Sakhin 69 %, Sarami 31 % |
| 208 | SAR-D3-SM | Sarami 67 %, Sakhin 33 % |
| 220 | SHA-CH2-SM | Shafan 62 %, Sarami 38 % |

Moving any of them to the other catchment renumbers the features after it in that catchment and class (re-run the script
with the assignment overridden, then re-apply).

## Block 6 names used as the model — what the audit found

Not changed, only recorded (`block6_name_audit.csv`): four `Rus-FP1-CH`-style names that follow a different pattern;
three duplicate names (`Ful-CH6-SS`, `Taw-D9-FP`, `Taw-D12-FP`); four numbers shared by two classes (`Taw-CH3-FP` /
`Taw-CH3-SM`, `Taw-CH4`, `Ful-D3`, `Ful-D4`); gaps in five counters; `Ful-D5-SS` on a `Sw M D` feature; and six features
whose prefix is not the catchment they lie in (`Taw-CH4-FP` and `Taw-D16-SS` in Fulaij, `Ais-D11/D12-SM` in Bani Kharus,
`Ais-CH6-FP` 53 % in Bani Kharus, `Maa-CH8-SS` 85 % in Al Taww). So "Block 6 is named correctly" holds for the pattern,
not for every name.

## Re-running

```bash
python "scripts/name_channels.py"
```

then apply `output/block4_channel_names.csv` (fid → Name) to the layer in QGIS, or copy
`output/Channels and Dykes 04102026 named.*` over the source once nobody has it open. The QGIS fid of a shapefile is
the 0-based record order, the same `fid` the CSV carries (checked on 2026-10-06 against the open layer).

## Open

1. The five flagged assignments above — keep the majority-length catchment or move them.
2. Prefix case: `HAW` (Block 4, as instructed) against `Taw` (Block 6). One of the two blocks will have to change if the
   report tables are to read the same.
