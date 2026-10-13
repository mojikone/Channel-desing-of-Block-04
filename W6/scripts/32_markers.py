"""Step 32 - put the design points into the W5 drawing: markers in every profile view and in plan on the layers
W6-PT-FLOW (blue), W6-PT-JUNCTION (red), W6-PT-FIX (yellow), W6-PT-FIX500 (orange), nested radii (cs/40_profile_markers.cs),
from output/profile_markers.json (31_design_points.py). Earlier markers on those layers are replaced. Saves the drawing.
    python 32_markers.py [--no-save]"""
import os, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE); W5 = os.path.join(os.path.dirname(W6), "W5")
sys.path.insert(0, os.path.join(W5, "scripts")); from c3d_mcp import McpSession, load_cs
LOG = os.path.join(W6, "log", "32_markers.log")


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + "  " + msg; print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")


markers = json.load(open(os.path.join(W6, "output", "profile_markers.json")))
clean = lambda t: str(t).replace(";", ",").replace("|", "/")
spec = ";".join("%s|%.3f|%.3f|%s|%s" % (m["alignment"], m["station"], m["elevation"] if m["elevation"] is not None else 0.0, m["kind"], clean(m["label"])) for m in markers if m["elevation"] is not None)
skipped = sum(1 for m in markers if m["elevation"] is None)
s = McpSession(command_timeout_ms=900000); ident = s.identity(); log("drawing: %s | %d markers (%d without elevation skipped)" % (ident["filename"], len(markers), skipped))
if not ident["filename"].endswith(("Block04_Channels_W5.dwg", "Block04_Channels_W6.dwg")): sys.exit("the active drawing is not the W5 drawing: nothing done")
r = s.execute(load_cs(os.path.join(W6, "cs", "40_profile_markers.cs"), MARKERS=spec, TEXT_H=7.5, ERASE_KINDS="flow,junction,fix,fix500"), description="W6 design point markers"); r = r.get("result", r) if isinstance(r, dict) else r
log("markers: %s" % json.dumps(r)[:1500])
if "--no-save" not in sys.argv: s.execute("return Database.Filename;", save=True); log("drawing saved")
s.close()
