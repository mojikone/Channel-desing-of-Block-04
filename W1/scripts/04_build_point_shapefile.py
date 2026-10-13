"""
Build a point shapefile for the junction elements in Basin_1.basin.

Block 4 has only Junction point elements (no reservoirs, diversions or sinks).
All 30 junctions are written so nothing is lost, with an 'is_dam' flag marking
the 9 named dam locations - filter on is_dam = 'Y' for dam-only mapping.

Coordinates: Canvas X/Y (WGS 84 / UTM zone 40N, EPSG:32640 - confirmed by the
srid recorded in Basin_1.sqlite geometry_columns).

Attributes: name, type, is_dam, wadi, then Q{rp} (peak flow m3/s) and
            V{rp} (volume Mm3) columns for all return periods.

Writes: W1/output/shp/points_peak_flow_volume.{shp,dbf,shx,prj}
"""
import re
import csv
from pathlib import Path
import shapefile

ROOT     = Path(__file__).resolve().parents[2]
BASIN    = ROOT / "Data" / "HEC_HMS_Block_04" / "Basin_1.basin"
CSV_PATH = ROOT / "W1" / "output" / "peak_flow_volume.csv"
SHP_DIR  = ROOT / "W1" / "output" / "shp"
SHP_DIR.mkdir(parents=True, exist_ok=True)
SHP_OUT  = SHP_DIR / "points_peak_flow_volume"

RP_ORDER    = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr",
               "1000yr", "2000yr", "5000yr", "10000yr", "PMP"]
POINT_TYPES = ("Junction",)

PRJ_WKT = (
    'PROJCS["WGS 84 / UTM zone 40N",'
    'GEOGCS["WGS 84",'
    'DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],'
    'PRIMEM["Greenwich",0],'
    'UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],'
    'AUTHORITY["EPSG","4326"]],'
    'PROJECTION["Transverse_Mercator"],'
    'PARAMETER["latitude_of_origin",0],'
    'PARAMETER["central_meridian",57],'
    'PARAMETER["scale_factor",0.9996],'
    'PARAMETER["false_easting",500000],'
    'PARAMETER["false_northing",0],'
    'UNIT["metre",1,AUTHORITY["EPSG","9001"]],'
    'AUTHORITY["EPSG","32640"]]'
)


def rp_field(rp: str, prefix: str) -> str:
    """'200yr' -> 'Q200'; 'PMP' -> 'QPMP'."""
    return f"{prefix}PMP" if rp == "PMP" else f"{prefix}{rp.replace('yr', '')}"


def is_named(name: str) -> bool:
    """A dam location is any junction not matching the generic J<number> code."""
    return re.fullmatch(r"J\d+", name) is None


def parse_basin_points(path: Path) -> list[dict]:
    """Return [{name, type, x, y}] for point elements carrying coordinates."""
    text = path.read_text(encoding="utf-8", errors="replace")
    points = []
    for etype in POINT_TYPES:
        for m in re.finditer(rf"^{re.escape(etype)}:\s*(.+?)\s*$", text, re.MULTILINE):
            name   = m.group(1).strip()
            bstart = m.start()
            bend   = text.find("End:", bstart)
            block  = text[bstart: bend if bend != -1 else len(text)]
            x = y = None
            for ln in block.splitlines():
                if "Canvas X:" in ln:
                    try:    x = float(ln.split(":", 1)[1].strip())
                    except ValueError: pass
                elif "Canvas Y:" in ln:
                    try:    y = float(ln.split(":", 1)[1].strip())
                    except ValueError: pass
            if x is not None and y is not None:
                points.append({"name": name, "type": etype, "x": x, "y": y})
    return points


def load_csv() -> tuple[dict, dict]:
    flow, vol = {}, {}
    with open(CSV_PATH, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            k = (r["element"], r["rp"])
            try:
                flow[k] = float(r["peak_m3s"])
                vol[k]  = float(r["vol_Mm3"])
            except (KeyError, ValueError):
                pass
    return flow, vol


def main():
    if not BASIN.exists():
        raise FileNotFoundError(BASIN)
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Run 01_extract_from_dss.py first: {CSV_PATH}")

    points    = parse_basin_points(BASIN)
    flow, vol = load_csv()

    w = shapefile.Writer(str(SHP_OUT), shapeType=shapefile.POINT)
    w.autoBalance = 1
    w.field("name", "C", 80)
    w.field("type", "C", 20)
    w.field("is_dam", "C", 1)
    w.field("wadi", "C", 40)
    for rp in RP_ORDER:
        w.field(rp_field(rp, "Q"), "N", 20, 4)
    for rp in RP_ORDER:
        w.field(rp_field(rp, "V"), "N", 20, 6)

    no_data = 0
    n_dams  = 0
    for pt in points:
        name = pt["name"]
        dam  = is_named(name)
        if dam:
            n_dams += 1
        wadi = name.rsplit(" ", 1)[0] if dam else ""
        w.point(pt["x"], pt["y"])
        rec = [name, pt["type"], "Y" if dam else "N", wadi]
        if not any((name, rp) in flow for rp in RP_ORDER):
            no_data += 1
        for rp in RP_ORDER:
            rec.append(flow.get((name, rp), 0.0))
        for rp in RP_ORDER:
            rec.append(vol.get((name, rp), 0.0))
        w.record(*rec)
    w.close()

    (SHP_DIR / "points_peak_flow_volume.prj").write_text(PRJ_WKT, encoding="utf-8")

    print(f"Written {len(points)} junctions -> {SHP_OUT}.shp")
    print(f"  {n_dams} flagged as dam locations (is_dam = 'Y')")
    if no_data:
        print(f"  Note: {no_data} point(s) had no DSS data (values set to 0).")


if __name__ == "__main__":
    main()
