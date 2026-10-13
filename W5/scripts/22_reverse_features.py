"""Step 22 - rebuild the features listed in civil3d/corrections.json "reversed": delete their alignment, profiles,
profile views and leaders (the corridor surface stays), rebuild them with the centreline reversed (20_prototype.build
does that for every name in the list), verify that the new alignment start equals the old end, save.
    python 22_reverse_features.py [--no-save]"""
import os, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import importlib; proto = importlib.import_module("20_prototype")
from c3d_mcp import McpSession, load_cs
W5 = proto.W5; LOG = os.path.join(W5, "log", "22_reverse_features.log")


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + "  " + msg; print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")


CHECK = """var name = "{{NAME}}"; foreach (ObjectId id in CivilDoc.GetAlignmentIds()) { var a = (Alignment)Transaction.GetObject(id, OpenMode.ForRead);
if (a.Name == name) return new { a.Name, start = a.StartPoint, end = a.EndPoint, a.Length, profiles = a.GetProfileIds().Count, views = a.GetProfileViewIds().Count }; } return null;"""

if __name__ == "__main__":
    s = McpSession(command_timeout_ms=900000); log("drawing: %s" % s.identity())
    names = sorted(proto.REVERSED); results = []
    for name in names:
        feat = next(f for f in proto.SPEC if f["name"] == name); old_start, old_end = feat["alignment"][0], feat["alignment"][-1]
        out = s.execute(load_cs(os.path.join(W5, "cs", "14_delete_feature.cs"), NAME=name), description="W5 delete " + name)
        res = out.get("result", out) if isinstance(out, dict) else out; log("%s: %s" % (name, res.get("log") if isinstance(res, dict) else res))
        proto.build(s, feat)
        chk = s.query(CHECK.replace("{{NAME}}", name)); chk = chk.get("result", chk) if isinstance(chk, dict) else chk
        ok = chk and abs(chk["start"]["x"] - old_end["x"]) < 0.01 and abs(chk["start"]["y"] - old_end["y"]) < 0.01 and abs(chk["end"]["x"] - old_start["x"]) < 0.01
        log("%s: start %.2f,%.2f (old end %.2f,%.2f) end %.2f,%.2f (old start %.2f,%.2f) length %.1f profiles %d views %d -> %s" % (
            name, chk["start"]["x"], chk["start"]["y"], old_end["x"], old_end["y"], chk["end"]["x"], chk["end"]["y"], old_start["x"], old_start["y"], chk["length"], chk["profiles"], chk["views"], "REVERSED OK" if ok else "NOT REVERSED"))
        results.append(ok)
    if "--no-save" not in sys.argv: s.execute("return Database.Filename;", save=True); log("saved")
    s.close(); log("%d of %d reversed" % (sum(results), len(results)))
    sys.exit(0 if all(results) else 1)
