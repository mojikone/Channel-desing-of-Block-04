"""Step 38 - the SewerGEMS point names into the W5 drawing (engineer, 2026-10-10 afternoon: "ensure all data on Civil 3D are up to
date"): for every point of final/Block4_design_points.shp a small circle (r 4 m) with its SGLabel (e.g. HAWCH7-1) written BELOW the
point, in every profile view of the channel at (station, GDP elevation) and in plan, on the layer W6-PT-SGLABEL (cs/40_profile_markers.cs,
kind sglabel; only that layer is cleared first, the design-point layers of 32 are left alone). Input final/final_markers.json, written
by 37_final_layers.py. Saves the drawing.
    python 38_sg_labels_markers.py [--no-save]"""
import os, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE); W5 = os.path.join(os.path.dirname(W6), "W5")
sys.path.insert(0, os.path.join(W5, "scripts")); from c3d_mcp import McpSession, load_cs
LOG = os.path.join(W6, "log", "38_sg_labels_markers.log")


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + "  " + msg; print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")


markers = json.load(open(os.path.join(W6, "final", "final_markers.json")))
clean = lambda t: str(t).replace(";", ",").replace("|", "/")
spec = ";".join("%s|%.3f|%.3f|%s|%s" % (m["alignment"], m["station"], m["elevation"], m["kind"], clean(m["label"])) for m in markers if m["elevation"] is not None)
skipped = sum(1 for m in markers if m["elevation"] is None)
s = McpSession(command_timeout_ms=900000); ident = s.identity(); log("drawing: %s | %d SewerGEMS point names (%d without elevation skipped)" % (ident["filename"], len(markers), skipped))
if not ident["filename"].endswith(("Block04_Channels_W5.dwg", "Block04_Channels_W6.dwg")): sys.exit("the active drawing is not the W5 drawing: nothing done")
r = s.execute(load_cs(os.path.join(W6, "cs", "40_profile_markers.cs"), MARKERS=spec, TEXT_H=5.0, ERASE_KINDS="sglabel"), description="W6 SewerGEMS point names"); r = r.get("result", r) if isinstance(r, dict) else r
log("names: %s" % json.dumps(r)[:1500])
if "--no-save" not in sys.argv: s.execute("return Database.Filename;", save=True); log("drawing saved")
s.close()
