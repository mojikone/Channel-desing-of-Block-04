"""Step 36 - junction fix (engineer, 2026-10-10): every tributary's GDP end point is set to the receiving channel's GDP
elevation at the junction (output/junction_points.csv from 31_design_points.py), receivers before their tributaries, the
previous line kept as a dashed profile "GDP <name> (before junction fix)" (cs/41_junction_fix.cs). Before anything the
drawing is saved and copied to W5/civil3d/backup/. Afterwards the GDP files and markers (W5/scripts/27_gdp_from_drawing.py),
the design points (31) and their markers (32) are regenerated from the adjusted profiles.
    python 36_junction_fix.py [--no-refresh] [--low-only] [--only TRIB1,TRIB2] [--suffix " (before junction fix 2)"] [--tag junction_fix_2]
--low-only keeps only the tributaries flagged LOW in junction_points.csv (second run, 2026-10-10 afternoon: the engineer's
profile edits had put four ends below the receiver again); --suffix names the dashed copy of the previous line (a copy with
the default name already exists from the first run, so a second run needs its own); --tag names the backup file."""
import os, sys, csv, json, time, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE); W5 = os.path.join(os.path.dirname(W6), "W5")
sys.path.insert(0, os.path.join(W5, "scripts")); from c3d_mcp import McpSession, load_cs
LOG = os.path.join(W6, "log", "36_junction_fix.log"); STYLES = json.load(open(os.path.join(W5, "civil3d", "styles.json")))


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + "  " + msg; print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")


junc = list(csv.DictReader(open(os.path.join(W6, "output", "junction_points.csv"), encoding="utf-8")))
recv_of = {r["Tributary"]: r["Receiver"] for r in junc}
def depth(name, seen=()):              # receivers before their tributaries: a channel's depth = 1 + its receiver's depth
    return 0 if name not in recv_of or name in seen else 1 + depth(recv_of[name], seen + (name,))
junc.sort(key=lambda r: depth(r["Tributary"]))
a = sys.argv[1:]
only = set(a[a.index("--only") + 1].split(",")) if "--only" in a else None
if "--low-only" in a: junc = [r for r in junc if r["Flag"].startswith("LOW")]
if only: junc = [r for r in junc if r["Tributary"] in only]
suffix = a[a.index("--suffix") + 1] if "--suffix" in a else " (before junction fix)"
tag = a[a.index("--tag") + 1] if "--tag" in a else "junction_fix"
if not junc: sys.exit("no junction left after the filters: nothing done")
spec = ";".join("%s|%s|%s" % (r["Tributary"], r["Receiver"], r["RecvSta"]) for r in junc)
s = McpSession(command_timeout_ms=900000); ident = s.identity(); log("drawing: %s" % ident["filename"]); log("fixing %d junction(s): %s" % (len(junc), ", ".join(r["Tributary"] for r in junc)))
if not ident["filename"].endswith(("Block04_Channels_W5.dwg", "Block04_Channels_W6.dwg")): sys.exit("the active drawing is not the W5 drawing: nothing done")
# backup: save the current state (the engineer's edits included), then copy the file
s.execute("return Database.Filename;", save=True)
bk = os.path.join(W5, "civil3d", "backup"); os.makedirs(bk, exist_ok=True); stamp = time.strftime("%Y%m%d_%H%M")
dst = os.path.join(bk, "Block04_Channels_W5_before_%s_%s.dwg" % (tag, stamp)); shutil.copy2(ident["filename"], dst); log("backup: %s (%.0f MB)" % (dst, os.path.getsize(dst) / 1e6))
r = s.execute(load_cs(os.path.join(W6, "cs", "41_junction_fix.cs"), JUNCTIONS=spec, DESIGN_STYLE=STYLES["gdp"]["profile"], BEFORE_SUFFIX=suffix), description="W6 junction fix", timeout=900)
r = r.get("result", r) if isinstance(r, dict) else r
json.dump(r, open(os.path.join(W6, "output", "junction_fix_result.json"), "w"), indent=1)
for fx in r.get("fixes", []):
    if "trib" in fx: log("%-12s -> %-12s sta %8s  end %8.3f -> %8.3f (%+.3f)  last seg %6.0f m  slope %.5f -> %.5f  %s" % (fx["trib"], fx["recv"], fx["sta"], fx["oldEnd"], fx["newEnd"], fx["diff"], fx["lastSegment_m"], fx["slopeOld"], fx["slopeNew"], fx["flag"]))
    else: log(str(fx))
for p in r.get("problems", []): log("PROBLEM " + p)
s.execute("return Database.Filename;", save=True); log("drawing saved"); s.close()
with open(os.path.join(W6, "output", "junction_fix.csv"), "w", newline="", encoding="utf-8") as fh:
    rows = [fx for fx in r.get("fixes", []) if "trib" in fx]
    if rows: w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
if "--no-refresh" not in sys.argv:
    for script, cwd in (("27_gdp_from_drawing.py", os.path.join(W5, "scripts")), ("31_design_points.py", HERE), ("32_markers.py", HERE)):
        log("running " + script); subprocess.run([sys.executable, script], cwd=cwd, check=False)
log("done")
