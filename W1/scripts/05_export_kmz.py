"""
05_export_kmz.py - Export the junction point layer to KMZ (Google Earth)

Points only. The Block 4 model carries no subbasin polygons or reach polylines
- Basin_1.sqlite holds the geometry schema but zero rows, and Basin_1.basin
stores only Canvas X/Y point coordinates - so the Basins and Reach layers from
the reference project have no source data here.

Outputs (27 files) in W1/output/KMZ/:
  All_Junctions.kmz      - all 30 junctions, labelled by name
  Q_2yr.kmz  ... Q_PMP.kmz - labelled with integer peak flow  (13 files)
  V_2yr.kmz  ... V_PMP.kmz - labelled with integer volume     (13 files)

Every file separates dam locations from generic junctions into two folders so
they can be toggled independently in Google Earth. Dam points are drawn larger
and in amber; generic junctions are white and smaller.

Projection: EPSG:32640 (UTM zone 40N) -> EPSG:4326 (WGS84)
"""
from pathlib import Path
import zipfile
import io
import shapefile
from pyproj import Transformer

ROOT       = Path(__file__).resolve().parents[2]
POINTS_SHP = ROOT / "W1" / "output" / "shp" / "points_peak_flow_volume.shp"
OUT_DIR    = ROOT / "W1" / "output" / "KMZ"

RP_ORDER = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr",
            "1000yr", "2000yr", "5000yr", "10000yr", "PMP"]


def rp_field(prefix: str, rp: str) -> str:
    """'2yr' -> 'Q2', 'PMP' -> 'QPMP'."""
    return f"{prefix}{rp.replace('yr', '')}"


XF = Transformer.from_crs("EPSG:32640", "EPSG:4326", always_xy=True)


def to_wgs84(x, y):
    return XF.transform(x, y)


def rgb_to_kml(r, g, b, a=255):
    """KML uses ABGR byte order."""
    return f"{a:02x}{b:02x}{g:02x}{r:02x}"


COL_WHITE = "ffffffff"
COL_DAM   = rgb_to_kml(255, 170, 0)   # amber - dam locations

ICON_URL = "http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png"


def _esc(s) -> str:
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def kml_header(name: str) -> str:
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
            f'<Document>\n<name>{_esc(name)}</name>\n')


def kml_footer() -> str:
    return "</Document>\n</kml>\n"


def point_style(style_id: str, colour: str, icon_scale: float, label_scale: float) -> str:
    return (f'<Style id="{style_id}">\n'
            '  <IconStyle>\n'
            f'    <color>{colour}</color>\n'
            f'    <scale>{icon_scale}</scale>\n'
            f'    <Icon><href>{ICON_URL}</href></Icon>\n'
            '  </IconStyle>\n'
            '  <LabelStyle>\n'
            f'    <color>{colour}</color>\n'
            f'    <scale>{label_scale}</scale>\n'
            '  </LabelStyle>\n'
            '</Style>\n')


STYLES = (point_style("dam", COL_DAM, 1.1, 1.0) +
          point_style("point", COL_WHITE, 0.8, 0.8))


def point_description(rec) -> str:
    """HTML popup listing every Q and V value for the element."""
    rows_q = "".join(
        f"<tr><td><b>{rp}</b></td><td align='right'>{rec[rp_field('Q', rp)]:.1f}</td></tr>"
        for rp in RP_ORDER)
    rows_v = "".join(
        f"<tr><td><b>{rp}</b></td><td align='right'>{rec[rp_field('V', rp)]:.2f}</td></tr>"
        for rp in RP_ORDER)
    dam_line = ("<p><b>Dam location</b>"
                f"{' - ' + _esc(rec['wadi']) if rec['wadi'] else ''}</p>"
                if rec["is_dam"] == "Y" else "")
    return ("<![CDATA["
            f"<h3>{_esc(rec['name'])}</h3>"
            f"<p><b>Type:</b> {_esc(rec['type'])}</p>"
            + dam_line +
            "<table border='1' cellpadding='3' cellspacing='0'>"
            "<tr><th>Return Period</th><th>Q peak (m&#179;/s)</th></tr>"
            + rows_q +
            "</table><br/>"
            "<table border='1' cellpadding='3' cellspacing='0'>"
            "<tr><th>Return Period</th><th>Volume (Mm&#179;)</th></tr>"
            + rows_v +
            "</table>]]>")


def point_placemark(label, desc: str, x: float, y: float, style_id: str) -> str:
    lon, lat = to_wgs84(x, y)
    return ("<Placemark>\n"
            f"  <name>{_esc(label)}</name>\n"
            f"  <description>{desc}</description>\n"
            f"  <styleUrl>#{style_id}</styleUrl>\n"
            f"  <Point><coordinates>{lon},{lat},0</coordinates></Point>\n"
            "</Placemark>\n")


def points_fragment(records, label_field: str) -> str:
    """Two folders: dam locations first, then generic junctions."""
    frags = []
    for is_dam, folder, style_id in (("Y", "Dam locations", "dam"),
                                     ("N", "Junctions", "point")):
        subset = [(rec, shp) for rec, shp in records if rec["is_dam"] == is_dam]
        if not subset:
            continue
        frags.append(f'<Folder><name>{_esc(folder)}</name>\n')
        for rec, shp in subset:
            pt    = shp.points[0]
            label = rec[label_field] if label_field == "name" else round(rec[label_field] or 0)
            frags.append(point_placemark(label, point_description(rec),
                                         pt[0], pt[1], style_id))
        frags.append("</Folder>\n")
    return "".join(frags)


def write_kmz(out_path: Path, kml_text: str):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doc.kml", kml_text.encode("utf-8"))
    out_path.write_bytes(buf.getvalue())


def main():
    if not POINTS_SHP.exists():
        raise FileNotFoundError(f"Run 04_build_point_shapefile.py first: {POINTS_SHP}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sf = shapefile.Reader(str(POINTS_SHP))
    records = [(sr.record.as_dict(), sr.shape) for sr in sf.shapeRecords()]

    kml = kml_header("All Junctions") + STYLES + points_fragment(records, "name") + kml_footer()
    write_kmz(OUT_DIR / "All_Junctions.kmz", kml)
    print("Written: All_Junctions.kmz")

    for prefix, title, fmt in (("Q", "Q Peak", "Q_{}.kmz"),
                               ("V", "Volume", "V_{}.kmz")):
        for rp in RP_ORDER:
            frag = points_fragment(records, rp_field(prefix, rp))
            kml  = kml_header(f"{title} - {rp}") + STYLES + frag + kml_footer()
            fname = fmt.format(rp)
            write_kmz(OUT_DIR / fname, kml)
            print(f"Written: {fname}")

    print(f"\nDone - {1 + len(RP_ORDER) * 2} KMZ files written to {OUT_DIR}")


if __name__ == "__main__":
    main()
