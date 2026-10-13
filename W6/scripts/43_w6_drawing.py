"""Step 43 - the W6 drawing (engineer, 2026-10-11): copy the W5 drawing to W6/civil3d/Block04_Channels_W6.dwg, open it (COM) and
add per channel the profile "GDP-raised <name>" = GDP + Raise at every design point of final/Block4_design_points.shp
(cs/42_design_ground.cs): the model ground for SewerGEMS (the lower bank top where a point lies in a wadi, the library depth above
the bed at fix points, the GDP elsewhere; Raise 0 or empty = the GDP). A tributary's last PVI sits at its end station with its
own GDP end elevation + the raise of the junction point on the receiver. Style "GDP-raised" (cyan, continuous; first named
"DG <name>" in green, renamed and recoloured on the engineer's instruction: the EG is green already).
Then 38_sg_labels_markers.py rewrites the point names with D/R (37 writes them into final/final_markers.json) and the drawing is
saved. The W5 drawing stays as it was at the copy; from here on the W6 drawing is the live one (27/32/36/38 accept both names).
    python 43_w6_drawing.py [--no-copy] [--overwrite]   (--no-copy: the W6 drawing is already open and active)"""
import os, sys, json, time, shutil, subprocess
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE); CB = os.path.dirname(W6); W5 = os.path.join(CB, "W5")
sys.path.insert(0, os.path.join(W5, "scripts")); from c3d_mcp import McpSession, load_cs
LOG = os.path.join(W6, "log", "43_w6_drawing.log"); C3D = os.path.join(W6, "civil3d"); os.makedirs(C3D, exist_ok=True)
SRC = os.path.join(W5, "civil3d", "Block04_Channels_W5.dwg"); DST = os.path.join(C3D, "Block04_Channels_W6.dwg")
SPEC = json.load(open(os.path.join(W5, "civil3d", "build_spec_w5.json")))
GDP = {p["alignment"]: sorted(p["pvis"], key=lambda q: q["sta"]) for p in json.load(open(os.path.join(W6, "gdp", "gdp_reviewed_pvis.json")))["profiles"]}
A = sys.argv[1:]


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + "  " + msg; print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")


def gdp_at(name, sta):
    pv = GDP[name]
    if sta <= pv[0]["sta"]: return pv[0]["elev"]
    if sta >= pv[-1]["sta"]: return pv[-1]["elev"]
    for a, b in zip(pv, pv[1:]):
        if a["sta"] <= sta <= b["sta"]: return a["elev"] + (b["elev"] - a["elev"]) * (sta - a["sta"]) / (b["sta"] - a["sta"]) if b["sta"] > a["sta"] else a["elev"]


# ---------------------------------------------------------------- the DG profiles from the final points
pts = pd.read_csv(os.path.join(W6, "final", "Block4_design_points.csv"))
length = {}
for f in SPEC:
    if f["kind"] != "channel": continue
    import numpy as np
    v = list(reversed(f["alignment"])) if f["reverse"] else f["alignment"]; xy = np.array([(p["x"], p["y"]) for p in v]); length[f["name"]] = float(np.hypot(*np.diff(xy, axis=0).T).sum())
junction = {}                                                      # tributary -> the raise of its junction point on the receiver
for _, r in pts[pts["CHend"].notna()].iterrows():
    for trib in str(r["CHend"]).split("; "): junction[trib] = 0.0 if pd.isna(r["Raise"]) else float(r["Raise"])
entries = []; n_pvi = 0; raised = 0
for name in sorted(length):
    own = pts[pts["Channel"] == name].sort_values("Station")
    pv = [(float(r["Station"]), float(r["GdpZ"]) + (0.0 if pd.isna(r["Raise"]) else float(r["Raise"]))) for _, r in own.iterrows()]
    raised += int((own["Raise"].fillna(0) > 0).sum())
    if name in junction: pv.append((length[name], gdp_at(name, length[name]) + junction[name]))   # the end on the receiver's junction point
    entries.append("%s|%s" % (name, ",".join("%.3f:%.3f" % (s, z) for s, z in pv))); n_pvi += len(pv)
spec = ";".join(entries)
log("43 W6 drawing | %d GDP-raised profiles, %d PVIs (%d points raised, %d tributary ends added)" % (len(entries), n_pvi, raised, len([n for n in length if n in junction])))

# ---------------------------------------------------------------- copy the W5 drawing and open the W6 copy
s = McpSession(command_timeout_ms=900000); ident = s.identity(); log("active drawing: %s" % ident["filename"])
if "--no-copy" not in A:
    if not ident["filename"].endswith("Block04_Channels_W5.dwg"): sys.exit("the active drawing is not the W5 drawing: nothing copied")
    s.execute("return Database.Filename;", save=True); log("W5 drawing saved")
    if os.path.exists(DST) and "--overwrite" not in A: sys.exit("%s exists: use --overwrite" % DST)
    shutil.copy2(SRC, DST); log("copied to %s (%.0f MB)" % (DST, os.path.getsize(DST) / 1e6))
    import win32com.client
    app = win32com.client.GetActiveObject("AutoCAD.Application"); app.Documents.Open(DST); time.sleep(3)
    for _ in range(60):
        try:
            ident = s.identity()
            if ident["filename"].lower() == DST.lower(): break
        except Exception: pass
        time.sleep(2)
    log("active drawing now: %s" % ident["filename"])
if ident["filename"].lower() != DST.lower(): s.close(); sys.exit("the W6 drawing is not the active drawing (%s): nothing done" % ident["filename"])

# ---------------------------------------------------------------- the profiles, the names with D/R, save
r = s.execute(load_cs(os.path.join(W6, "cs", "42_design_ground.cs"), PROFILES=spec), description="W6 design ground profiles", timeout=900); r = r.get("result", r) if isinstance(r, dict) else r
log("GDP-raised profiles: made %s, replaced %s, PVIs %s, legacy style removed %s, problems %s" % (r.get("made"), r.get("replaced"), r.get("pvisTotal"), r.get("legacyStyleRemoved"), r.get("problems")))
json.dump(r, open(os.path.join(C3D, "42_design_ground_result.json"), "w"), indent=1)
s.execute("return Database.Filename;", save=True); log("W6 drawing saved"); s.close()
log("running 38_sg_labels_markers.py (point names with D/R)"); subprocess.run([sys.executable, os.path.join(HERE, "38_sg_labels_markers.py")], check=False)
log("done")
