r"""Step 50 - everything downstream of a SewerGEMS run, in order, stopping at the first failure (engineer, 2026-10-11 night:
"then update everything"). For the run folder <run> written by the bridge jobs:
  1. the as-run exports and job logs copied into W6/sewergems/results/<run>/ (bridge_exports/ + logs)
  2. 48_fix_size_labels.py  --run <run> --sqlite <revision>   sizes by class + GUID from the revision's database
  3. profile_paths.csv       SHACH13-2 -> SHACH13-O15 (the manhole became the outfall in R3)
  4. 45_sewergems_results.py <bridge run folder>               review tables and summary.md
  5. 49_sg_profile_dxf_all.py --run <run>                      profile DXFs of all channels and scenarios
  6. sheets: make_buffers.py --run <run>, the 200-yr DXFs copied in, run_all.py, export_pdf.py, make_set.py, both gates
    python 50_rebuild_after_run.py --run run_20261012_0031 --sqlite "<...>\SewerGEMS Block 04_R3.stsw.sqlite" [--scenarios 200yr] [--set-tag R5]
"""
import os, sys, glob, shutil, subprocess, time, io
HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE); B4 = os.path.dirname(W6)
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
RUN = opt("--run", "run_20261012_0031")
SQLITE = opt("--sqlite", r"C:\Users\mojtaba\Desktop\Win10 shared folder\SewerGEMS Block 04 11102026\SewerGEMS Block 04_R3.stsw.sqlite")
BRIDGE = os.path.join(r"D:\VBOX\bridge\out\b4", RUN); RES = os.path.join(W6, "sewergems", "results", RUN)
TAG = opt("--set-tag", "")
SHEETS = os.path.join(W6, "sewergems", "sheets", "scripts"); SETPDF = os.path.join(SHEETS, "PDF", "Set", "2224-PD-HY-PP-B4_Plan_and_Profile_Drawings_200yr" + ("_" + TAG if TAG else "") + ".pdf")
T0 = time.time()


def step(title, cmd, cwd=HERE):
    t = time.time(); print("\n### %s  (%s)" % (title, " ".join(os.path.basename(x) if os.sep in x else x for x in cmd)), flush=True)
    r = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    tail = (r.stdout + r.stderr).strip().splitlines()[-6:]; print("\n".join("    " + l[:160] for l in tail))
    print("    -> %s in %.0f s" % ("ok" if r.returncode == 0 else "FAILED (%d)" % r.returncode, time.time() - t), flush=True)
    if r.returncode != 0: sys.exit("stopped at: " + title)


# 1. the as-run exports and logs into the results folder
exp = os.path.join(RES, "bridge_exports"); os.makedirs(exp, exist_ok=True)
scen = opt("--scenarios", "2yr,5yr,10yr,25yr,50yr,100yr,200yr,500yr").split(",")      # a partial run (e.g. --scenarios 200yr) is allowed
missing = [s for s in scen if not os.path.exists(os.path.join(BRIDGE, "conduits_%s.csv" % s))]
if missing: sys.exit("the bridge run folder lacks scenarios: " + ", ".join(missing))
for f in glob.glob(os.path.join(BRIDGE, "*.csv")): shutil.copy2(f, exp if os.path.basename(f).startswith(("conduits_", "nodes_")) else RES)
for f in glob.glob(os.path.join(BRIDGE, "log*.txt")): shutil.copy2(f, RES)
print("1. exports copied:", sorted(os.listdir(exp)))
# 2. sizes by class + GUID
step("2. size labels from the revision's database", [sys.executable, os.path.join(HERE, "48_fix_size_labels.py"), "--run", RUN, "--sqlite", SQLITE])
# 3. the profile path of SHA-CH13-SS
pp = os.path.join(W6, "sewergems", "profiles", "profile_paths.csv"); s = io.open(pp, encoding="utf-8").read()
if "SHACH13-2" in s:
    s = s.replace("SHACH13-2", "SHACH13-O15").replace(" 1682", " 2105"); io.open(pp, "w", encoding="utf-8", newline="\n").write(s); print("3. profile_paths.csv: SHACH13-2 -> SHACH13-O15")
else: print("3. profile_paths.csv already updated")
# 4. review tables
step("4. review tables and summary", [sys.executable, os.path.join(HERE, "45_sewergems_results.py"), BRIDGE])
# 5. profile DXFs
step("5. profile DXFs, all channels and scenarios", [sys.executable, os.path.join(HERE, "49_sg_profile_dxf_all.py"), "--run", RUN, "--scenarios", ",".join(scen)])
# 6. sheets
step("6a. buffers", [sys.executable, os.path.join(SHEETS, "make_buffers.py"), "--run", RUN], cwd=SHEETS)
for f in glob.glob(os.path.join(W6, "sewergems", "dxf", RUN, "200yr", "*.dxf")): shutil.copy2(f, os.path.join(SHEETS, "Data", "DXF"))
print("6b. 200-yr profile DXFs copied into the sheet pipeline:", len(glob.glob(os.path.join(SHEETS, "Data", "DXF", "*.dxf"))))
step("6c. sheets and key maps, all channels", [sys.executable, os.path.join(SHEETS, "run_all.py")], cwd=SHEETS)
step("6d. PDFs and combined PDFs", [sys.executable, os.path.join(SHEETS, "export_pdf.py")], cwd=SHEETS)
step("6e. the set", [sys.executable, os.path.join(SHEETS, "make_set.py")] + (["--tag", TAG] if TAG else []), cwd=SHEETS)
step("6f. gate: set PDF", [sys.executable, os.path.join(B4, "W3", "report", "check_clean.py"), SETPDF, "--terms", os.path.join(SHEETS, "..", "forbidden_terms.txt"), "--allow", os.path.join(SHEETS, "..", "allowed_terms.txt"), "--quiet"], cwd=SHEETS)
step("6g. gate: sheet DXF text", [sys.executable, os.path.join(SHEETS, "check_clean_sheets.py"), "--quiet"], cwd=SHEETS)
print("\nALL DONE in %.0f min" % ((time.time() - T0) / 60))
