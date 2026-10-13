"""Export the engineer's layer styles (QML) from a COPY of his QGIS project, so the map figures use his symbology.
run: python-qgis-ltr.bat 15_export_user_styles.py   -> maps/styles/<layer>.qml  (the copy is read; his project is never touched)"""
import os
from qgis.core import QgsApplication, QgsProject
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", r"C:\Program Files\QGIS 3.44.8\apps\qgis-ltr"), True)
app = QgsApplication([], False); app.initQgis()
HERE = os.path.dirname(os.path.abspath(__file__)); ST = os.path.join(os.path.dirname(HERE), "maps", "styles")
proj = QgsProject.instance(); ok = proj.read(os.path.join(ST, "_user_project_copy.qgz")); print("project read:", ok, "| layers:", len(proj.mapLayers()))
want = {"Channels and Dykes 04102026": "channels_dykes", "Dam axis": "dam_axis", "Dikes": "dam_dikes", "Polygon_FSL": "fsl_polygon", "Crest Level": "crest_polygon", "Block4_200Yr": "depth_200yr", "Block_4_Hazard_200y": "hazard_200yr",
        "LandUSE_block4": "landuse", "Bathinah Highway CL": "highway", "Batinah Coastal RD CL": "coastal_road", "Muscat Expressway CL": "expressway", "North Batina Bypass": "bypass", "Pipeline": "pipeline_south", "Pipelines": "pipeline_north",
        "GCA RENN": "global_catchments", "Streams NSA 5m Batinah": "streams", "Culverts_RDs": "culverts"}
for l in proj.mapLayers().values():
    if l.name() in want:
        p = os.path.join(ST, want[l.name()] + ".qml"); msg, ok = l.saveNamedStyle(p); print(f"{l.name():30s} -> {os.path.basename(p)} ok={ok} src={l.source()[:90]}")
app.exitQgis()
