"""Step 49 - run 46_sg_profile_dxf.py for every channel profile of profile_paths.csv and every scenario of the run, in parallel.
    python 49_sg_profile_dxf_all.py [--run run_20261011_1721] [--scenarios 200yr,500yr] [--channels SHA-CH13-SS] [--workers 8]"""
import os, sys, subprocess, time
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE)
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
RUN = opt("--run", "run_20261011_1721"); W = int(opt("--workers", "8"))
SC = opt("--scenarios", "2yr,5yr,10yr,25yr,50yr,100yr,200yr,500yr").split(",")
CH = pd.read_csv(os.path.join(W6, "sewergems", "profiles", "profile_paths.csv"))["profile"].tolist()
if opt("--channels"): CH = [c for c in CH if c in opt("--channels").split(",")]
def run(job):
    ch, sc = job; t = time.time()
    r = subprocess.run([sys.executable, os.path.join(HERE, "46_sg_profile_dxf.py"), "--channel", ch, "--scenario", sc, "--run", RUN], capture_output=True, text=True)
    return ch, sc, r.returncode, time.time() - t, (r.stdout + r.stderr).strip().splitlines()[-3:]
t0 = time.time(); jobs = [(c, s) for s in SC for c in CH]; fails = []
with ThreadPoolExecutor(W) as ex:
    for ch, sc, rc, dt, tail in ex.map(run, jobs):
        if rc != 0: fails.append((ch, sc, tail)); print("FAILED %s %s: %s" % (ch, sc, " | ".join(tail)))
print("%d profiles x %d scenarios: %d written, %d failed, %.0f s" % (len(CH), len(SC), len(jobs) - len(fails), len(fails), time.time() - t0))
sys.exit(1 if fails else 0)
