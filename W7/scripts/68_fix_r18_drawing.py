"""Step 68 (W7) - the DRAWN geometry of SHA-R18 (engineer, 2026-10-12 18:10 on the Q200 map: "the reach downstream of 856 carries
no flow?"). Step 52 re-pointed SHA-R18 from SHA-J45 to the Shafan 08 site in the model (topology, canvas end, length 3094 m), but
the reach line stored in Basin_6.sqlite (reach2d) was still Basin 3's line from SHA-J20 north-east to SHA-J45, so the maps drew
852 m3/s running past the dam. Also SHA-J20's canvas point sat 1.2 km east of the end of the SHA-R1 line (the Basin 3 canvas
and GIS disagree there), so the "856" dot stood off the wadi.
Fix, display only (no hydrology changes; the 13 analyses stand):
  * SHA-J20's canvas := the end of the SHA-R1 line (the junction of the dam deliverables, J18 of Basin 4, is there too);
    SHA-R1's canvas end and SHA-R18's canvas start follow;
  * SHA-R18's drawn line := the wadi line of the dam deliverables (Basin_4.sqlite reach2d "S23", J17 -> the dam) from its vertex
    nearest the new SHA-J20 to the dam, ending at the site junction;
  * the modelled length of SHA-R18 stays 3094 m (step 52: straight distance x the reach's sinuosity; the dam deliverables route
    J18 into the dam with no reach at all, the drawn wadi line is 3.4 km).
Writes Basin_6.basin and Basin_6.sqlite in the HMS project (HMS closed) and the snapshot in Claude Block 04/model/.
    python 68_fix_r18_drawing.py"""
import os, re, sqlite3, shutil, datetime, math
from shapely import wkb
from shapely.geometry import LineString
HERE = os.path.dirname(os.path.abspath(__file__)); W7 = os.path.dirname(HERE); CB = os.path.dirname(W7)
HMS = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydrology\HEC_HMS_Block_04"
SITE = (485965.0, 2646045.0)
now = datetime.datetime.now(); DATE = now.strftime("%d %B %Y").lstrip("0"); TIME = now.strftime("%H:%M:%S")
# the lines
c6 = sqlite3.connect(os.path.join(HMS, "Basin_6.sqlite"))
r1 = wkb.loads(c6.execute("select GEOMETRY from reach2d where name='SHA-R1'").fetchone()[0]); j20 = (r1.coords[-1][0], r1.coords[-1][1])
old18 = wkb.loads(c6.execute("select GEOMETRY from reach2d where name='SHA-R18'").fetchone()[0])
print("SHA-R1 ends at %.0f %.0f; old SHA-R18 line %.0f m from %s to %s" % (j20[0], j20[1], old18.length, [round(v) for v in old18.coords[0][:2]], [round(v) for v in old18.coords[-1][:2]]))
c4 = sqlite3.connect(os.path.join(HMS, "Basin_4.sqlite"))
cands = [wkb.loads(g) for (g,) in c4.execute("select GEOMETRY from reach2d where name='S23'")]; c4.close()
wadi = max(cands, key=lambda l: l.length); pts = [(x, y) for x, y, *_ in wadi.coords]
assert math.hypot(pts[-1][0] - SITE[0], pts[-1][1] - SITE[1]) < 100, "the Basin 4 wadi line does not end at the dam"
k = min(range(len(pts)), key=lambda i: math.hypot(pts[i][0] - j20[0], pts[i][1] - j20[1]))
new = LineString([(j20[0], j20[1], 0.0)] + [(x, y, 0.0) for x, y in pts[k:]] + [(SITE[0], SITE[1], 0.0)])
print("new SHA-R18 line: %d vertices, %.0f m, starts %.0f m from the SHA-R1 end" % (len(new.coords), new.length, math.hypot(pts[k][0] - j20[0], pts[k][1] - j20[1])))
c6.execute("update reach2d set GEOMETRY=? where name='SHA-R18'", (wkb.dumps(new),)); c6.commit(); c6.close()
# the canvas points in the basin file
p = os.path.join(HMS, "Basin_6.basin"); b = open(p, encoding="utf-8").read()
def set_in(block_re, key, val, txt):
    m = re.search(block_re, txt, re.S | re.M); blk = m.group(0)
    nb, n = re.subn(r"^(\s*%s:\s*).*$" % re.escape(key), lambda mm: mm.group(1) + val, blk, count=1, flags=re.M); assert n == 1, key
    nb = re.sub(r"^(\s*Last Modified Date: ).*$", r"\g<1>" + DATE, nb, count=1, flags=re.M); nb = re.sub(r"^(\s*Last Modified Time: ).*$", r"\g<1>" + TIME, nb, count=1, flags=re.M)
    return txt.replace(blk, nb, 1)
J = r"^Junction: SHA-J20\r?\n.*?^End:\n"; R18 = r"^Reach: SHA-R18\r?\n.*?^End:\n"; R1 = r"^Reach: SHA-R1\r?\n.*?^End:\n"
b = set_in(J, "Canvas X", "%.1f" % j20[0], b); b = set_in(J, "Canvas Y", "%.1f" % j20[1], b)
b = set_in(R18, "From Canvas X", "%.1f" % j20[0], b); b = set_in(R18, "From Canvas Y", "%.1f" % j20[1], b)
b = set_in(R1, "Canvas X", "%.1f" % j20[0], b); b = set_in(R1, "Canvas Y", "%.1f" % j20[1], b)
assert "Length: 3093.63" in re.search(R18, b, re.S | re.M).group(0)
open(p, "w", encoding="utf-8", newline="\n").write(b)
for f in ("Basin_6.basin", "Basin_6.sqlite"): shutil.copy2(os.path.join(HMS, f), os.path.join(CB, "model", f))
print("Basin_6.basin: SHA-J20 canvas, SHA-R1 end and SHA-R18 start moved to %.0f %.0f; Basin_6.sqlite: SHA-R18 line replaced; snapshots refreshed" % j20)
