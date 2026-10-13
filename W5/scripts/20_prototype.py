"""Step 20 - build ONE feature (or a list) in the active Civil 3D drawing through the civil3d-roslyn MCP server, with the
template's styles named in civil3d/styles.json, then inspect the result. Geometry comes from W4 (points/csv, build_spec.json,
profile_views.csv): nothing is recomputed. Usage:
    python 20_prototype.py SHA-CH6-SM            # build one feature and inspect its view
    python 20_prototype.py SHA-CH6-SM --inspect  # inspect only
    python 20_prototype.py --all [--save]        # every feature of the spec, in order
"""
import os, sys, json, csv, time
HERE = os.path.dirname(os.path.abspath(__file__)); W5 = os.path.dirname(HERE); W4 = os.path.join(os.path.dirname(W5), "W4")
sys.path.insert(0, HERE)
from c3d_mcp import McpSession, load_cs
SPEC_PATH = os.path.join(W5, "civil3d", "build_spec_w5.json")                 # the engineer's edited centrelines (23_update_lines.py), else the W4 spec
if not os.path.exists(SPEC_PATH): SPEC_PATH = os.path.join(W4, "civil3d", "build_spec.json")
SPEC = json.load(open(SPEC_PATH))
VIEWS = {r["name"]: r for r in csv.DictReader(open(os.path.join(W4, "civil3d", "profile_views.csv")))}
STYLES = json.load(open(os.path.join(W5, "civil3d", "styles.json")))
REVERSED = set(json.load(open(os.path.join(W5, "civil3d", "corrections.json")))["reversed"])   # digitised against the flow: built reversed
LOG = os.path.join(W5, "log", "20_prototype.log")


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + "  " + msg; print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")


def nums(seq, key): return ", ".join("%.3f" % p[key] for p in seq)


def build(s, feat):
    name, kind = feat["name"], feat["kind"]; v = VIEWS[name]
    k = STYLES["channel" if kind == "channel" else "dyke"]
    rev = feat.get("reverse", name in REVERSED)      # the W5 spec carries the flag (approved direction); the W4 spec relies on corrections.json
    verts = list(reversed(feat["alignment"])) if rev else feat["alignment"]
    code = load_cs(os.path.join(W5, "cs", "11_build_feature.cs"), NAME=name, KIND=kind, CSV=os.path.join(W4, "points", "csv", name + ".csv"),
                   BX=nums(feat["boundary"], "x"), BY=nums(feat["boundary"], "y"), AX=nums(verts, "x"), AY=nums(verts, "y"),
                   INSERT_X=v["insertX"], INSERT_Y=v["insertY"], SURFACE_STYLE=k["surface"], ALIGN_STYLE=k["alignment"], ALIGN_LABELSET=k["alignmentLabelSet"],
                   PROFILE_STYLE=k["profile"], PROFILE_LABELSET=k["profileLabelSet"], PV_STYLE=k["profileView"], BANDSET=k["bandSet"],
                   LEADER_LAYER=STYLES["leader"]["layerChannels" if kind == "channel" else "layerDykes"], LEADER_COLOR=STYLES["leader"]["colorChannels" if kind == "channel" else "colorDykes"],
                   LEADER_TEXT_H=STYLES["leader"]["textHeight"])
    t = time.time(); out = s.execute(code, description="W5 build " + name); dt = time.time() - t
    res = out.get("result", out) if isinstance(out, dict) else out
    log("%s built in %.0f s%s: %s" % (name, dt, " (centreline reversed)" if rev else "", json.dumps(res, ensure_ascii=False)[:1500]))
    return res


def inspect(s, name):
    out = s.query(load_cs(os.path.join(W5, "cs", "12_pv_inspect.cs"), VIEW="PV " + name))
    res = out.get("result", out) if isinstance(out, dict) else out
    path = os.path.join(W5, "civil3d", "qa", "inspect_%s.json" % name); json.dump(res, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    log("inspection of PV %s written to %s" % (name, path)); return res


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; flags = [a for a in sys.argv[1:] if a.startswith("--")]
    s = McpSession(command_timeout_ms=900000); ident = s.identity(); log("drawing: %s" % ident)
    feats = SPEC if "--all" in flags else [f for f in SPEC if f["name"] in args]
    if not feats: sys.exit("no feature selected")
    for f in feats:
        if "--inspect" not in flags: build(s, f)
        if "--all" not in flags: print(json.dumps(inspect(s, f["name"]), indent=1, ensure_ascii=False)[:12000])
    if "--save" in flags: s.execute("return Database.Filename;", save=True); log("saved")
    s.close()
