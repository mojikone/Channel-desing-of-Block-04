# Jython script for HEC-HMS: open the project, list the scripting API, try to compute one run and one depth-area analysis
import sys, traceback
out = open(r"C:\Users\mojtaba\AppData\Local\Temp\claude\D--Mojtaba-Renardet-2224-WS11-Batinah-Block-4\72a3ff20-809e-4d71-bf42-7b9f694d69ff\scratchpad\delin\hms_probe.log", "w")
def log(*a):
    out.write(" ".join(str(x) for x in a) + "\n"); out.flush()
try:
    from hms.model.JythonHms import *
    import hms.model.JythonHms as JH
    log("JythonHms functions:", [n for n in dir(JH) if not n.startswith("_")])
    OpenProject("HEC_HMS_Block_04", r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydrology\HEC_HMS_Block_04")
    log("project opened")
    try:
        ComputeRun("FM 200yr B2"); log("ComputeRun FM 200yr B2: done")
    except Exception:
        log("ComputeRun failed:", traceback.format_exc())
    try:
        log("Compute doc:", getattr(JH.Compute, "__doc__", None))
        Compute("DA 200yr B2"); log("Compute DA 200yr B2: done")
    except Exception:
        log("Compute failed:", traceback.format_exc())
    try:
        SaveAllProjectComponents(); log("saved")
    except Exception:
        log("save failed:", traceback.format_exc())
except Exception:
    log("fatal:", traceback.format_exc())
out.close()
try:
    Exit(1)
except Exception:
    pass
