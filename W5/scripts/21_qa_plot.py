"""Step 21 - QA images of the active W5 drawing through COM only (no clicks): zoom to a window, plot the display to PNG
with the PublishToWeb PNG plotter (a window plot comes out blank in Civil 3D 2026, a display plot does not).
    python 21_qa_plot.py <name>            # three images for one feature: whole profile view, its first 600 m, the plan at the alignment start
    python 21_qa_plot.py --extents         # the whole drawing
The plot configuration of the Model layout is restored afterwards."""
import os, sys, json, csv, time, pythoncom
import win32com.client
from win32com.client import VARIANT
HERE = os.path.dirname(os.path.abspath(__file__)); W5 = os.path.dirname(HERE); W4 = os.path.join(os.path.dirname(W5), "W4")
OUT = os.path.join(W5, "civil3d", "qa"); os.makedirs(OUT, exist_ok=True)
TARGET = "Block04_Channels_W5.dwg"
app = win32com.client.GetActiveObject("AutoCAD.Application"); doc = app.ActiveDocument
if doc.Name != TARGET: sys.exit("active drawing is %s, not %s: nothing done" % (doc.Name, TARGET))
def upright(path):
    """The page is plotted rotated 90 degrees (portrait PNG media, landscape windows): turn the image back so X runs right and Y up."""
    from PIL import Image
    if os.path.exists(path): Image.open(path).rotate(90, expand=True).save(path)
def p3(x, y, z=0.0): return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [x, y, z])
lay = doc.ActiveLayout; old = (lay.ConfigName, lay.CanonicalMediaName, lay.PlotType, lay.PlotRotation, lay.UseStandardScale, lay.StandardScale)
doc.SetVariable("BACKGROUNDPLOT", 0)
lay.ConfigName = "PublishToWeb PNG.pc3"; lay.RefreshPlotDeviceInfo()
lay.CanonicalMediaName = next((m for m in lay.GetCanonicalMediaNames() if "1600" in m), lay.CanonicalMediaName)
lay.UseStandardScale = True; lay.StandardScale = 0; lay.CenterPlot = True; lay.PlotRotation = 1; lay.PlotWithLineweights = False; lay.PlotWithPlotStyles = False; lay.PlotType = 0
def shot(name, ax, ay, bx, by):
    cx, cy = (ax + bx) / 2, (ay + by) / 2; wd, ht = bx - ax, by - ay   # the page is 1600 x 1280 after rotation
    if wd / ht > 1.25: ht = wd / 1.25
    else: wd = ht * 1.25
    app.ZoomWindow(p3(cx - wd / 2, cy - ht / 2), p3(cx + wd / 2, cy + ht / 2)); time.sleep(0.5)
    path = os.path.join(OUT, name + ".png")
    if os.path.exists(path): os.remove(path)
    ok = doc.Plot.PlotToFile(path); time.sleep(0.5); upright(path); print(name, ok, (os.path.getsize(path) // 1024) if os.path.exists(path) else "missing", "kB"); return path
if "--extents" in sys.argv:
    app.ZoomExtents(); lay.PlotType = 1; path = os.path.join(OUT, "qa_extents.png")
    if os.path.exists(path): os.remove(path)
    print("qa_extents", doc.Plot.PlotToFile(path)); upright(path); lay.PlotType = 0
else:
    name = sys.argv[1]
    v = next(r for r in csv.DictReader(open(os.path.join(W4, "civil3d", "profile_views.csv"))) if r["name"] == name)
    f = next(f for f in json.load(open(os.path.join(W4, "civil3d", "build_spec.json"))) if f["name"] == name)
    x0, y0, w, h = float(v["insertX"]), float(v["insertY"]), float(v["width_m"]), float(v["height_m"])
    shot("qa_%s_view" % name, x0 - 0.05 * w, y0 - 60, x0 + 1.05 * w, y0 + h + 60)
    shot("qa_%s_view_start600m" % name, x0 - 60, y0 - 40, x0 + 600, y0 + min(h, 400) + 40)
    a0 = f["alignment"][0]; shot("qa_%s_plan_start" % name, a0["x"] - 150, a0["y"] - 120, a0["x"] + 150, a0["y"] + 120)
lay.PlotType = old[2]; lay.PlotRotation = old[3]; lay.UseStandardScale = old[4]
if old[4]: lay.StandardScale = old[5]
lay.ConfigName = old[0] if old[0] else "None"; lay.RefreshPlotDeviceInfo()
try: lay.CanonicalMediaName = old[1]
except Exception as ex: print("media not restored:", ex)
doc.SetVariable("BACKGROUNDPLOT", 2); print("plot configuration restored:", lay.ConfigName)
