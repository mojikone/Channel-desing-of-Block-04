# Jython script for HEC-HMS 4.12 (W6): compute the 13 depth-area analyses "DA <rp> B5" of Basin 5 headless.
# Copy to a path WITHOUT spaces, then from "C:\Program Files\HEC\HEC-HMS\4.12":  HEC-HMS.cmd -script <copy>
# (the launcher's relative java/GDAL paths only resolve from that folder). HMS must be closed. Method: hms-headless-compute memory.
import traceback, time, os
LOGDIR = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Claude Block 04\W6\hms"
PROJ_DIR = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydrology\HEC_HMS_Block_04"
RPS = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr", "1000yr", "2000yr", "5000yr", "10000yr", "PMP"]
out = open(os.path.join(LOGDIR, "34_hms_compute_b5.log"), "w")
def log(*a):
    out.write(" ".join(str(x) for x in a) + "\n"); out.flush()
def wait_done(logfile, timeout_s=1800):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            f = open(logfile, "rb"); txt = f.read().decode("latin-1"); f.close()
            if "Finished computing" in txt or "Aborted" in txt or "ERROR" in txt: return txt.strip().split("\n")[-1]
        except Exception:
            pass
        time.sleep(2)
    return "TIMEOUT"
try:
    from hms.model.JythonHms import *
    OpenProject("HEC_HMS_Block_04", PROJ_DIR); log("project opened")
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
    for rp in RPS:
        nm = "DA %s B5" % rp; logfile = os.path.join(PROJ_DIR, "DA_%s_B5_daa.log" % rp)
        try:
            os.remove(logfile)
        except Exception:
            pass
        t0 = time.time()
        try:
            proj.computeDepthAreaAnalysis(nm)
        except Exception:
            log(nm, "EXCEPTION", traceback.format_exc())
        log(nm, "->", wait_done(logfile), "in %.0f s" % (time.time() - t0))
    log("done")
except Exception:
    log("FATAL", traceback.format_exc())
out.close()
Exit(1)
