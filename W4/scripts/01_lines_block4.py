"""Step 01 - the Block 4 centrelines, named: lines/Block4_lines.gpkg (+ .shp, .csv) and lines/Block4_centrelines.dxf
(one 2D polyline per feature on its own layer CH_<name> / D_<name>, for the Civil 3D drawing)."""
import sys
from pathlib import Path
import geopandas as gpd, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_w4 import LINES_SHP, LINES, CRS, kind_of, cls_of, gca_of, sort_key

g = gpd.read_file(LINES_SHP); b = g[g["Block"] == 4].copy()
assert b.crs.to_epsg() == 32640 and (b.geom_type == "LineString").all() and b["Name"].notna().all() and b["Name"].is_unique, "Block 4 lines: expected unique names and single-part lines in UTM 40N"
b["kind"] = b["Name"].map(kind_of); b["cls"] = b["Name"].map(cls_of); b["gca"] = b["Name"].map(gca_of); b["length_m"] = b.geometry.length.round(2)
b["x_start"] = b.geometry.apply(lambda l: round(l.coords[0][0], 3)); b["y_start"] = b.geometry.apply(lambda l: round(l.coords[0][1], 3))
b["x_end"] = b.geometry.apply(lambda l: round(l.coords[-1][0], 3)); b["y_end"] = b.geometry.apply(lambda l: round(l.coords[-1][1], 3)); b["n_vertices"] = b.geometry.apply(lambda l: len(l.coords))
b = b.sort_values("Name", key=lambda s: s.map(sort_key)).reset_index(drop=True); b["order"] = range(1, len(b) + 1)
out = b[["order", "Name", "kind", "cls", "gca", "length_m", "n_vertices", "x_start", "y_start", "x_end", "y_end", "CHtt", "geometry"]].rename(columns={"Name": "name"})
out.to_file(LINES / "Block4_lines.gpkg", layer="lines", driver="GPKG"); out.to_file(LINES / "Block4_lines.shp"); out.drop(columns="geometry").to_csv(LINES / "Block4_lines.csv", index=False)

# DXF R12 with a layer table: one LWPOLYLINE-equivalent POLYLINE per feature
def dxf_polylines(gdf, path):
    layers = [("CH_" if r.kind == "channel" else "D_") + r.name for r in gdf.itertuples()]
    L = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "0", "ENDSEC", "0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER", "70", str(len(layers) + 1), "0", "LAYER", "2", "0", "70", "0", "62", "7", "6", "CONTINUOUS"]
    for i, lay in enumerate(layers): L += ["0", "LAYER", "2", lay, "70", "0", "62", str(1 + i % 7), "6", "CONTINUOUS"]
    L += ["0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
    for r, lay in zip(gdf.itertuples(), layers):
        L += ["0", "POLYLINE", "8", lay, "66", "1", "70", "0"]
        for x, y in r.geometry.coords: L += ["0", "VERTEX", "8", lay, "10", f"{x:.3f}", "20", f"{y:.3f}", "30", "0.0"]
        L += ["0", "SEQEND", "8", lay]
    L += ["0", "ENDSEC", "0", "EOF"]
    Path(path).write_text("\n".join(L) + "\n", encoding="ascii")
dxf_polylines(out, LINES / "Block4_centrelines.dxf")
print(f"{len(out)} lines: {int((out.kind == 'channel').sum())} channels {out.loc[out.kind == 'channel', 'length_m'].sum() / 1000:.1f} km, {int((out.kind == 'dyke').sum())} dykes {out.loc[out.kind == 'dyke', 'length_m'].sum() / 1000:.1f} km -> {LINES}")
