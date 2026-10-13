"""Step 24 - rebuild the features whose centreline changed (civil3d/qa/line_changes.csv from 23_update_lines.py, or names
given on the command line): delete alignment, profiles, views and leader (the corridor surface stays), rebuild from the
W5 spec in the approved direction, verify start and end against the spec, save.
    python 24_update_features.py [names...] [--no-save]"""
import os, sys, csv, json, time, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import importlib; proto = importlib.import_module("20_prototype")
from c3d_mcp import McpSession, load_cs
W5 = proto.W5; LOG = os.path.join(W5, "log", "24_update_features.log")
CHECK = """var name = "{{NAME}}"; foreach (ObjectId id in CivilDoc.GetAlignmentIds()) { var a = (Alignment)Transaction.GetObject(id, OpenMode.ForRead);
if (a.Name == name) return new { a.Name, start = a.StartPoint, end = a.EndPoint, a.Length, profiles = a.GetProfileIds().Count, views = a.GetProfileViewIds().Count }; } return null;"""


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + "  " + msg; print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")


if __name__ == "__main__":
    names = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not names: names = [r["name"] for r in csv.DictReader(open(os.path.join(W5, "civil3d", "qa", "line_changes.csv"))) if r["changed"] == "True"]
    assert proto.SPEC_PATH.endswith("build_spec_w5.json"), "the W5 spec is missing: run 23_update_lines.py first"
    s = McpSession(command_timeout_ms=900000); log("drawing: %s | %d features to rebuild: %s" % (s.identity()["filename"], len(names), names))
    ok_all = []
    for name in names:
        feat = next(f for f in proto.SPEC if f["name"] == name); v = list(reversed(feat["alignment"])) if feat["reverse"] else feat["alignment"]
        out = s.execute(load_cs(os.path.join(W5, "cs", "14_delete_feature.cs"), NAME=name), description="W5 delete " + name)
        res = out.get("result", out) if isinstance(out, dict) else out; log("%s: %s" % (name, res.get("log") if isinstance(res, dict) else res))
        proto.build(s, feat)
        chk = s.query(CHECK.replace("{{NAME}}", name)); chk = chk.get("result", chk) if isinstance(chk, dict) else chk
        ok = bool(chk) and math.hypot(chk["start"]["x"] - v[0]["x"], chk["start"]["y"] - v[0]["y"]) < 0.01 and math.hypot(chk["end"]["x"] - v[-1]["x"], chk["end"]["y"] - v[-1]["y"]) < 0.01 and chk["profiles"] == 1 and chk["views"] == 1
        log("%s: length %.1f (spec %.1f), start %.2f,%.2f end %.2f,%.2f, profiles %d views %d -> %s" % (name, chk["length"], feat["length_m"], chk["start"]["x"], chk["start"]["y"], chk["end"]["x"], chk["end"]["y"], chk["profiles"], chk["views"], "OK" if ok else "MISMATCH"))
        ok_all.append(ok)
    if "--no-save" not in sys.argv: s.execute("return Database.Filename;", save=True); log("saved")
    s.close(); log("%d of %d rebuilt and verified" % (sum(ok_all), len(ok_all))); sys.exit(0 if all(ok_all) else 1)
