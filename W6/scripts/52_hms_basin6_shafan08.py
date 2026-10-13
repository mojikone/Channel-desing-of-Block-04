"""Step 52 - a TEMPORARY assessment basin for the engineer's question of 2026-10-12: what if the Shafan 08 dam, excluded from the
channel hydrology (Basin 3) on his instruction, had been included? Basin 6 = Basin 3 with
  * the reservoir "Shafan 08 Reservoir" exactly as Basin 4 defines it (Modified Puls, Elev-Area Shafan 08 / Elev-Dis Shafan 08,
    initial level 153) inserted below the junction "Shafan 08 site", draining to SHA-R40 as the site did;
  * the local catchment of the dam routed through the site: in Basin 1/4 the dam receives the Shafan 02 outflow plus S22
    (58.7 km2) and S23 (31.0 km2); in Basin 3 those are SHA-S3 (58.7) and SHA-S23 (21.0, re-delineated), which reach SHA-J20
    and ran down SHA-R18 straight to SHA-J45 past the site. SHA-R18 now ends at the site (length set to the straight distance
    times the reach's sinuosity); the dam outflow then follows SHA-R40 > SHA-J42 > SHA-R43 > SHA-J45 > SHA-R46 > SHA-J47.
Registered in the HMS project (backup first, HMS closed): Basin 6 in the .hms, "Use Basin Model: Basin 6" in every met model,
depth-area analyses "DA <rp> B6" for the eight design return periods with the analysis points restricted to the Shafan line.
Writes the headless compute script and its names.txt into the scratchpad folder given by --out.
    python 52_hms_basin6_shafan08.py --out <folder without spaces>"""
import os, sys, re, shutil, math, datetime
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
OUT = opt("--out"); assert OUT, "--out <folder>"
HMS = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydrology\HEC_HMS_Block_04"
W3 = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Claude Block 04\W3"
RPS = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr"]
ALL = RPS + ["1000yr", "2000yr", "5000yr", "10000yr", "PMP"]
KEEP = {"Shafan 08 site", "Shafan 08 Reservoir", "SHA-R40", "SHA-J42", "SHA-R43", "SHA-J45", "SHA-R46", "SHA-J47", "SHA-J51", "SHA-R18", "SHA-J20", "SHA-R33", "Shafan 02 Reservoir"}
os.makedirs(OUT, exist_ok=True)
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S"); bk = os.path.join(HMS, "_backup_before_basin6_" + stamp); os.makedirs(bk)
for f in ["HEC_HMS_Block_04.hms", "HEC_HMS_Block_04.nals", "HEC_HMS_Block_04.run"] + ["FM_%s.met" % rp for rp in ALL]:
    if os.path.exists(os.path.join(HMS, f)): shutil.copy2(os.path.join(HMS, f), bk)
print("backup:", bk)

# ---- Basin_6.basin
b3 = open(os.path.join(HMS, "Basin_3.basin"), encoding="utf-8").read()
assert b3.startswith("Basin: Basin 3\n"); b6 = "Basin: Basin 6\n" + b3[len("Basin: Basin 3\n"):]
blocks = re.split(r"(?=^(?:Subbasin|Junction|Reach|Reservoir|Sink|Source|Diversion): )", b6, flags=re.M)
def xy(block, key="Canvas"):
    return float(re.search(r"\n\s*%s X: ([\d.-]+)" % key, block).group(1)), float(re.search(r"\n\s*%s Y: ([\d.-]+)" % key, block).group(1))
site = next(b for b in blocks if b.startswith("Junction: Shafan 08 site")); sx, sy = xy(site)
r18 = next(b for b in blocks if b.startswith("Reach: SHA-R18")); fx, fy = xy(r18, "From Canvas"); tx, ty = xy(r18)
L18 = float(re.search(r"\n\s*Length: ([\d.]+)", r18).group(1)); straight = math.hypot(tx - fx, ty - fy); sinu = L18 / straight
newL = round(math.hypot(sx - fx, sy - fy) * sinu, 2)
out = []
for b in blocks:
    if b.startswith("Junction: Shafan 08 site"):
        b = b.replace("     Downstream: SHA-R40\n", "     Downstream: Shafan 08 Reservoir\n")
        res = ("Reservoir: Shafan 08 Reservoir\n     Last Modified Date: 12 October 2026\n     Last Modified Time: 12:00:00\n"
               "     Canvas X: %.1f\n     Canvas Y: %.1f\n     From Canvas X: %.1f\n     From Canvas Y: %.1f\n     Downstream: SHA-R40\n\n"
               "     Route: Modified Puls\n     Routing Curve: Elevation-Area-Outflow\n     Initial Elevation: 153.0\n"
               "     Elevation-Area Table: Elev-Area Shafan 08\n     Elevation-Outflow Table: Elev-Dis Shafan 08\n     Primary Table: Elevation-Area\nEnd:\n\n") % (sx + 150, sy + 110, sx + 150, sy + 110)
        out.append(b); out.append(res); continue
    if b.startswith("Reach: SHA-R18"):
        b = b.replace("     Downstream: SHA-J45\n", "     Downstream: Shafan 08 site\n")
        b = re.sub(r"\n     Canvas X: [\d.-]+\n     Canvas Y: [\d.-]+\n", "\n     Canvas X: %.1f\n     Canvas Y: %.1f\n" % (sx, sy), b, count=1)
        b = re.sub(r"\n     Length: [\d.]+\n", "\n     Length: %.2f\n" % newL, b, count=1)
    out.append(b)
b6 = "".join(out)
assert b6.count("Reservoir: Shafan 08 Reservoir") == 1 and "Downstream: Shafan 08 site" in b6
open(os.path.join(HMS, "Basin_6.basin"), "w", encoding="utf-8", newline="\n").write(b6)
if os.path.exists(os.path.join(HMS, "Basin_3.sqlite")) and not os.path.exists(os.path.join(HMS, "Basin_6.sqlite")): shutil.copy2(os.path.join(HMS, "Basin_3.sqlite"), os.path.join(HMS, "Basin_6.sqlite"))
print("Basin_6.basin written: SHA-R18 now ends at the Shafan 08 site (length %.0f -> %.0f m, sinuosity %.2f); reservoir inserted" % (L18, newL, sinu))

# ---- the project file
hms = open(os.path.join(HMS, "HEC_HMS_Block_04.hms"), encoding="utf-8").read()
if "Basin: Basin 6\n" not in hms:
    blk = re.search(r"^Basin: Basin 3\r?\n.*?^End:\r?\n", hms, re.S | re.M).group(0)
    nb = blk.replace("Basin: Basin 3", "Basin: Basin 6").replace("Basin_3.basin", "Basin_6.basin")
    nb = re.sub(r"Description: .*", "Description: TEMPORARY assessment: Basin 3 + the Shafan 08 reservoir (2026-10-12)", nb)
    hms = hms.replace(blk, blk + nb, 1); open(os.path.join(HMS, "HEC_HMS_Block_04.hms"), "w", encoding="utf-8", newline="\n").write(hms); print("project: Basin 6 registered")
# ---- the met models
for rp in ALL:
    p = os.path.join(HMS, "FM_%s.met" % rp)
    if not os.path.exists(p): continue
    m = open(p, encoding="utf-8").read()
    if "Use Basin Model: Basin 6" not in m:
        m = m.replace("     Use Basin Model: Basin 5\n", "     Use Basin Model: Basin 5\n     Use Basin Model: Basin 6\n", 1); open(p, "w", encoding="utf-8", newline="\n").write(m)
print("met models: Basin 6 allowed")
# ---- the analyses, points restricted to the Shafan line
nals = open(os.path.join(HMS, "HEC_HMS_Block_04.nals"), encoding="utf-8").read(); added = 0
for rp in RPS:
    if "Analysis: DA %s B6\n" % rp in nals: continue
    blk = re.search(r"^Analysis: DA " + rp + r" B3\r?\n.*?^End:\r?\n", nals, re.S | re.M).group(0)
    nb = blk.replace("Analysis: DA %s B3" % rp, "Analysis: DA %s B6" % rp).replace("DA_%s_B3.dss" % rp, "DA_%s_B6.dss" % rp).replace("Basin Model Name: Basin 3", "Basin Model Name: Basin 6")
    lines = nb.split("\n"); kept = []; drop = 0
    for ln in lines:
        m = re.match(r"\s*Analysis Point: (.+)", ln)
        if m and m.group(1).strip() not in KEEP: drop += 1; continue
        kept.append(ln)
    nb = "\n".join(kept)
    nals = nals.replace(blk, blk + nb, 1); added += 1
open(os.path.join(HMS, "HEC_HMS_Block_04.nals"), "w", encoding="utf-8", newline="\n").write(nals); print("analyses added:", added, "(points restricted to the Shafan line, %d points dropped in the last one)" % drop)
# ---- the headless compute script and its names
open(os.path.join(OUT, "names.txt"), "w").write("\n".join("DA %s B6" % rp for rp in RPS) + "\n")
src = open(os.path.join(os.path.dirname(W3), "scripts", "hms_compute_all.py"), encoding="utf-8").read()
src = re.sub(r'HERE = r"[^"]+"', 'HERE = r"%s"' % OUT, src, count=1)
open(os.path.join(OUT, "hms_compute_b6.py"), "w", encoding="utf-8", newline="\n").write(src)
print("compute script:", os.path.join(OUT, "hms_compute_b6.py"))
