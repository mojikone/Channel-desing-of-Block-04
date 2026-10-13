"""Step 09 - QA of the built drawing through COM only: count the Civil 3D entities in model space, then plot three windows
to PNG with the PublishToWeb PNG plotter (overview, one channel view with its leader, the top of the dyke column).
No clicks, no dialogs. The layout's plot configuration is restored afterwards. Guard: acts on the W4 drawing only."""
import os, sys, json, csv, time, pythoncom
import win32com.client
from win32com.client import VARIANT
W4 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(W4, "civil3d", "qa"); os.makedirs(OUT, exist_ok=True)
TARGETS = ("Block04_Channels_Surfaces_C3Dtemplate.dwg", "Block04_Channels_Surfaces.dwg")
app = win32com.client.GetActiveObject("AutoCAD.Application"); doc = app.ActiveDocument
if doc.Name not in TARGETS or not doc.Path.lower().startswith(W4.lower()): print("active is", doc.Name, "- nothing done"); sys.exit(1)
# ---- entity census
t = time.time(); ms = doc.ModelSpace; n = ms.Count; counts = {}
for i in range(n):
    on = ms.Item(i).ObjectName; counts[on] = counts.get(on, 0) + 1
print("model space entities:", n, "in %.0f s" % (time.time() - t))
for k, v in sorted(counts.items(), key=lambda kv: -kv[1]): print("  %-40s %d" % (k, v))
# ---- plot windows from the placement table and the spec
rows = list(csv.DictReader(open(os.path.join(W4, "civil3d", "profile_views.csv"))))
feats = json.load(open(os.path.join(W4, "civil3d", "build_spec.json")))
xs = []; ys = []
for f in feats:
    for p in f["alignment"]: xs.append(p["x"]); ys.append(p["y"])
for r in rows:
    x0, y0, w, h = float(r["insertX"]), float(r["insertY"]), float(r["width_m"]), float(r["height_m"])
    xs += [x0, x0 + w]; ys += [y0, y0 + h]
pad = 500.0
ext = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
r1 = next(r for r in rows if r["name"] == "SAR-CH1-FP")          # the longest channel
f1 = next(f for f in feats if f["name"] == "SAR-CH1-FP"); v0 = f1["alignment"][0]
x0, y0, w, h = float(r1["insertX"]), float(r1["insertY"]), float(r1["width_m"]), float(r1["height_m"])
win_ch = (min(x0, v0["x"]) - 300, min(y0, v0["y"]) - 300, max(x0 + w, v0["x"]) + 300, max(y0 + h, v0["y"]) + 300)
dykes = [r for r in rows if r["kind"] == "dyke"]
dx = min(float(r["insertX"]) for r in dykes); dxe = max(float(r["insertX"]) + float(r["width_m"]) for r in dykes)
dy = sorted(float(r["insertY"]) for r in dykes); dyt = sorted(float(r["insertY"]) + float(r["height_m"]) for r in dykes)
win_dk = (dx - 400, dy[-6] - 200, dxe + 400, dyt[-1] + 200)   # the top six views of the column
print("extents:", ["%.0f" % v for v in ext]); print("channel window:", ["%.0f" % v for v in win_ch]); print("dyke window:", ["%.0f" % v for v in win_dk])
# ---- plot
lay = doc.ActiveLayout
old = (lay.ConfigName, lay.CanonicalMediaName, lay.PlotType, lay.PlotRotation, lay.StandardScale, lay.UseStandardScale)
print('template plot settings:', old)
doc.SetVariable("BACKGROUNDPLOT", 0)
lay.ConfigName = "PublishToWeb PNG.pc3"; lay.RefreshPlotDeviceInfo()
medias = list(lay.GetCanonicalMediaNames())
pick = next((m for m in medias if "1600" in m), medias[-1]); print("media:", pick)
lay.CanonicalMediaName = pick
lay.UseStandardScale = True; lay.StandardScale = 0       # acScaleToFit (a custom scale left in the template plots a blank page)
lay.CenterPlot = True; lay.PlotRotation = 1   # ac90degrees: the PNG page is portrait (1280 x 1600), the windows landscape
lay.PlotWithLineweights = False; lay.PlotWithPlotStyles = False
def pt(x, y): return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [x, y])
for name, (ax, ay, bx, by) in (("qa_overview", ext), ("qa_channel_SAR-CH1-FP", win_ch), ("qa_dyke_column", win_dk)):
    cx, cy = (ax + bx) / 2, (ay + by) / 2; wd, ht = bx - ax, by - ay   # keep the window at the page's 1.25 aspect so the plot fills it
    if wd / ht > 1.25: ht = wd / 1.25
    else: wd = ht * 1.25
    lay.SetWindowToPlot(pt(cx - wd / 2, cy - ht / 2), pt(cx + wd / 2, cy + ht / 2))
    lay.PlotType = 4        # acWindow: valid only after the window is set
    path = os.path.join(OUT, name + ".png")
    if os.path.exists(path): os.remove(path)
    t = time.time(); ok = doc.Plot.PlotToFile(path); time.sleep(1.0)
    print(name, "->", ok, "%.0f s" % (time.time() - t), (os.path.getsize(path) // 1024) if os.path.exists(path) else "missing", "kB")
lay.PlotType = old[2]; lay.PlotRotation = old[3]; lay.UseStandardScale = old[5]
if old[5]: lay.StandardScale = old[4]
lay.ConfigName = old[0] if old[0] else "None"; lay.CanonicalMediaName = old[1]; doc.SetVariable("BACKGROUNDPLOT", 2)
print("plot configuration restored")

