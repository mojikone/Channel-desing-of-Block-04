# Jython script for HEC-HMS 4.12: compute depth-area analyses headless.
# Names are read from names.txt next to this script (one analysis name per line).
# Run:  cd "C:\Program Files\HEC\HEC-HMS\4.12" && HEC-HMS.cmd -script <this file>
import traceback, time, os
HERE = r"C:\Users\mojtaba\AppData\Local\Temp\claude\D--Mojtaba-Renardet-2224-WS11-Batinah-Block-4\72a3ff20-809e-4d71-bf42-7b9f694d69ff\scratchpad\delin"
PROJ_DIR = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydrology\HEC_HMS_Block_04"
out = open(os.path.join(HERE, "hms_compute_all.log"), "w")
def log(*a):
    out.write(" ".join(str(x) for x in a) + "\n"); out.flush()
def wait_done(logfile, timeout_s=1800):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            f = open(logfile, "rb"); txt = f.read().decode("latin-1"); f.close()
            if "Finished computing" in txt or "Aborted" in txt: return txt.strip().split("\n")[-1]
        except Exception:
            pass
        time.sleep(2)
    return "TIMEOUT"
try:
    names = [l.strip() for l in open(os.path.join(HERE, "names.txt")) if l.strip()]
    from hms.model.JythonHms import *
    OpenProject("HEC_HMS_Block_04", PROJ_DIR); log("project opened; analyses:", names)
    from java.lang import Class
    from hms.model import ProjectManager
    pm = None
    for f in Class.forName("hms.model.JythonHms").getDeclaredFields():
        f.setAccessible(True)
        try:
            v = f.get(None)
        except:
            v = None
        if isinstance(v, ProjectManager): pm = v; break
    proj = pm.project(); log("project object:", proj)
    for nm in names:
        rp = nm.split()[1]; suf = nm.split()[2]
        logfile = os.path.join(PROJ_DIR, "DA_%s_%s_daa.log" % (rp, suf))
        try:
            os.remove(logfile)
        except Exception:
            pass
        t0 = time.time()
        try:
            r = proj.computeDepthAreaAnalysis(nm); log("called computeDepthAreaAnalysis", nm, "->", r)
        except Exception:
            log("call failed", nm, traceback.format_exc()[-500:]); continue
        res = wait_done(logfile); log("  %s: %s (%.0f s)" % (nm, res, time.time() - t0))
    try:
        SaveAllProjectComponents(); log("saved")
    except Exception:
        log("save failed:", traceback.format_exc()[-300:])
except Exception:
    log("fatal:", traceback.format_exc())
out.close()
try:
    Exit(1)
except Exception:
    pass
