"""Step 26 - review layers for QGIS: the alignment stations of every channel and dyke as points every `STEP` m along the
W5 spec centrelines (the same vertices and direction as the Civil 3D alignments, so the stations match the profile
views), with the Civil 3D label form "k+mmm", a major flag every MAJOR m, the start/end flagged and the line bearing for
rotated tick markers; plus QML styles for the stations, the GDP breaks and the GDP segments (slope labels).
Outputs: gis/Block4_alignment_stations.gpkg (+ .shp), gis/*.qml."""
import os, sys, json, math
import geopandas as gpd
from shapely.geometry import Point
HERE = os.path.dirname(os.path.abspath(__file__)); W5 = os.path.dirname(HERE); GIS = os.path.join(W5, "gis"); os.makedirs(GIS, exist_ok=True)
SPEC = json.load(open(os.path.join(W5, "civil3d", "build_spec_w5.json")))
STEP, MAJOR = 100.0, 500.0


def fmt(sta): return "%d+%03d" % (int(sta // 1000), int(round(sta % 1000)))


rows = []
for f in SPEC:
    v = list(reversed(f["alignment"])) if f["reverse"] else f["alignment"]
    segs = [(v[i - 1], v[i], math.hypot(v[i]["x"] - v[i - 1]["x"], v[i]["y"] - v[i - 1]["y"])) for i in range(1, len(v))]
    total = sum(s[2] for s in segs)
    stations = [k * STEP for k in range(int(total // STEP) + 1)] + [total]
    acc = 0.0; si = 0
    for sta in stations:
        while si < len(segs) - 1 and acc + segs[si][2] < sta - 1e-9: acc += segs[si][2]; si += 1
        p, q, L = segs[si]; t = max(0.0, min(1.0, (sta - acc) / L)) if L > 0 else 0.0
        x = p["x"] + t * (q["x"] - p["x"]); y = p["y"] + t * (q["y"] - p["y"])
        bearing = (math.degrees(math.atan2(q["x"] - p["x"], q["y"] - p["y"])) + 360) % 360      # from north, clockwise (QGIS marker rotation)
        kind = "start" if sta == 0 else ("end" if abs(sta - total) < 1e-6 else ("major" if abs(sta / MAJOR - round(sta / MAJOR)) < 1e-9 else "minor"))
        rows.append({"name": f["name"], "kind": f["kind"], "station": round(sta, 2), "label": fmt(sta), "point": kind, "bearing": round(bearing, 1), "length": round(total, 1), "geometry": Point(x, y)})
g = gpd.GeoDataFrame(rows, crs="EPSG:32640")
g.to_file(os.path.join(GIS, "Block4_alignment_stations.gpkg"), layer="stations", driver="GPKG"); g.to_file(os.path.join(GIS, "Block4_alignment_stations.shp"))
print("%d station points for %d alignments (%d channels) -> %s" % (len(g), g["name"].nunique(), (g["kind"] == "channel").sum() and g[g["kind"] == "channel"]["name"].nunique(), GIS))

# ---- QML styles: rule-based so that minor stations stay small and majors/ends stand out
QML_STATIONS = """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.44" styleCategories="Symbology|Labeling">
 <renderer-v2 type="RuleRenderer" forceraster="0" enableorderby="0">
  <rules key="{rules}">
   <rule key="{r1}" filter="&quot;point&quot; = 'minor'" symbol="0" label="station every 100 m"/>
   <rule key="{r2}" filter="&quot;point&quot; = 'major'" symbol="1" label="station every 500 m"/>
   <rule key="{r3}" filter="&quot;point&quot; IN ('start','end')" symbol="2" label="start / end"/>
  </rules>
  <symbols>
   <symbol type="marker" name="0" alpha="1"><layer class="SimpleMarker"><Option type="Map"><Option name="name" type="QString" value="line"/><Option name="color" type="QString" value="0,0,0,255"/><Option name="outline_color" type="QString" value="0,0,0,255"/><Option name="outline_width" type="QString" value="0.3"/><Option name="size" type="QString" value="2.2"/><Option name="angle" type="QString" value="90"/></Option><data_defined_properties><Option type="Map"><Option name="properties" type="Map"><Option name="angle" type="Map"><Option name="active" type="bool" value="true"/><Option name="expression" type="QString" value="&quot;bearing&quot; + 90"/><Option name="type" type="int" value="3"/></Option></Option></Option></data_defined_properties></layer></symbol>
   <symbol type="marker" name="1" alpha="1"><layer class="SimpleMarker"><Option type="Map"><Option name="name" type="QString" value="line"/><Option name="color" type="QString" value="0,0,0,255"/><Option name="outline_color" type="QString" value="0,0,0,255"/><Option name="outline_width" type="QString" value="0.6"/><Option name="size" type="QString" value="3.6"/></Option><data_defined_properties><Option type="Map"><Option name="properties" type="Map"><Option name="angle" type="Map"><Option name="active" type="bool" value="true"/><Option name="expression" type="QString" value="&quot;bearing&quot; + 90"/><Option name="type" type="int" value="3"/></Option></Option></Option></data_defined_properties></layer></symbol>
   <symbol type="marker" name="2" alpha="1"><layer class="SimpleMarker"><Option type="Map"><Option name="name" type="QString" value="circle"/><Option name="color" type="QString" value="255,255,255,255"/><Option name="outline_color" type="QString" value="0,0,0,255"/><Option name="outline_width" type="QString" value="0.6"/><Option name="size" type="QString" value="3"/></Option></layer></symbol>
  </symbols>
 </renderer-v2>
 <labeling type="rule-based">
  <rules key="{lrules}">
   <rule key="{l1}" filter="&quot;point&quot; IN ('major','start','end')" description="major stations"><settings calloutType="simple"><text-style fontSize="8" fontFamily="Arial" fontWeight="75" textColor="0,0,0,255" fieldName="CASE WHEN &quot;point&quot; = 'start' THEN &quot;name&quot; || '  ' || &quot;label&quot; WHEN &quot;point&quot; = 'end' THEN &quot;label&quot; || '  end ' || &quot;name&quot; ELSE &quot;label&quot; END" isExpression="1" namedStyle="Bold"><text-buffer bufferDraw="1" bufferSize="0.8" bufferColor="255,255,255,255"/></text-style><placement placement="6" dist="1.5" quadOffset="4"/><rendering scaleVisibility="1" scaleMin="1" scaleMax="150000"/></settings></rule>
   <rule key="{l2}" filter="&quot;point&quot; = 'minor'" description="minor stations"><settings calloutType="simple"><text-style fontSize="6.5" fontFamily="Arial" textColor="60,60,60,255" fieldName="label" isExpression="0"><text-buffer bufferDraw="1" bufferSize="0.6" bufferColor="255,255,255,255"/></text-style><placement placement="6" dist="1" quadOffset="4"/><rendering scaleVisibility="1" scaleMin="1" scaleMax="15000"/></settings></rule>
  </rules>
 </labeling>
</qgis>
"""
QML_BREAKS = """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.44" styleCategories="Symbology|Labeling">
 <renderer-v2 type="singleSymbol"><symbols><symbol type="marker" name="0" alpha="1"><layer class="SimpleMarker"><Option type="Map"><Option name="name" type="QString" value="circle"/><Option name="color" type="QString" value="255,0,0,255"/><Option name="outline_color" type="QString" value="120,0,0,255"/><Option name="outline_width" type="QString" value="0.4"/><Option name="size" type="QString" value="3.2"/></Option></layer></symbol></symbols></renderer-v2>
 <labeling type="simple"><settings calloutType="simple"><text-style fontSize="7.5" fontFamily="Arial" fontWeight="75" textColor="170,0,0,255" fieldName="'GB' || &quot;GB&quot; || '  ' || lpad(floor(&quot;Station&quot;/1000), 1, '0') || '+' || lpad(round(&quot;Station&quot; % 1000), 3, '0') || '  z=' || round(&quot;Z_m&quot;, 2)" isExpression="1" namedStyle="Bold"><text-buffer bufferDraw="1" bufferSize="0.8" bufferColor="255,255,255,255"/></text-style><placement placement="6" dist="2" quadOffset="2"/><rendering scaleVisibility="1" scaleMin="1" scaleMax="150000"/></settings></labeling>
</qgis>
"""
QML_SEGMENTS = """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.44" styleCategories="Symbology|Labeling">
 <renderer-v2 type="singleSymbol"><symbols><symbol type="line" name="0" alpha="1"><layer class="SimpleLine"><Option type="Map"><Option name="line_color" type="QString" value="0,90,200,255"/><Option name="line_width" type="QString" value="0.9"/></Option></layer></symbol></symbols></renderer-v2>
 <labeling type="simple"><settings calloutType="simple" placement="2"><text-style fontSize="7" fontFamily="Arial" textColor="0,60,160,255" fieldName="&quot;Label&quot; || '  ' || round(&quot;Length_m&quot;) || ' m  ' || round(&quot;Slope&quot; * 100, 2) || ' %'" isExpression="1"><text-buffer bufferDraw="1" bufferSize="0.8" bufferColor="255,255,255,255"/></text-style><placement placement="2" dist="1.2" lineAnchorPercent="0.5" placementFlags="10"/><rendering scaleVisibility="1" scaleMin="1" scaleMax="150000" mergeLines="0"/></settings></labeling>
</qgis>
"""
import uuid
k = lambda: "{%s}" % uuid.uuid4()
for name, text in (("Block4_alignment_stations.qml", QML_STATIONS.format(rules=k(), r1=k(), r2=k(), r3=k(), lrules=k(), l1=k(), l2=k())), ("Block4_channel_breaks.qml", QML_BREAKS), ("Block4_channel_segments.qml", QML_SEGMENTS)):
    p = os.path.join(GIS, name)          # written only when missing: the files in gis/ are the live styles (labels switched off by the engineer, 2026-10-10)
    if not os.path.exists(p): open(p, "w", encoding="utf-8").write(text)
print("styles: existing QML files kept")
