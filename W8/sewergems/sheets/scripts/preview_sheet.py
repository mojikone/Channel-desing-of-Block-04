"""Render the plan or profile viewport of a generated sheet DXF to PNG for a visual check (no AutoCAD needed).
    python preview_sheet.py <channel> <sheet 1..n | km> [plan|profile] [--conduit SGLabel]   (--conduit picks the sheet that holds the conduit's midpoint)"""
import os, sys, glob, re, ezdxf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy
from config import VP_PLAN_X0, VP_PLAN_Y0, VP_PLAN_X1, VP_PLAN_Y1, VP_PROF_X0, VP_PROF_Y0, VP_PROF_X1, VP_PROF_Y1, DXF_DIR, OUT_DXF, SEGMENT_LEN
A = sys.argv[1:]; ch = A[0]; which = A[2] if len(A) > 2 and not A[2].startswith("--") else "profile"
if "--conduit" in A:
    lab = A[A.index("--conduit") + 1]; src = ezdxf.readfile(os.path.join(DXF_DIR, ch + ".dxf")).modelspace()
    t = [e for e in src.query('TEXT[layer=="Annotation"]') if e.dxf.text.startswith(lab + ":")][0]; sheet = int(t.dxf.insert.x // SEGMENT_LEN) + 1
    print("%s midpoint at station %.0f -> sheet %02d" % (lab, t.dxf.insert.x, sheet))
else: sheet = A[1]
tag = "KeyMap" if str(sheet) == "km" else "Sheet%02d" % int(sheet)
name = sorted(glob.glob(os.path.join(OUT_DXF, "%s-%s_v*.dxf" % (ch, tag))), key=os.path.getmtime)[-1]
doc = ezdxf.readfile(name); lay = doc.paperspace([l.name for l in doc.layouts][1])
for e in lay.query("IMAGE"): lay.delete_entity(e)
x0, y0, x1, y1 = (VP_PLAN_X0, VP_PLAN_Y0, VP_PLAN_X1, VP_PLAN_Y1) if which == "plan" else (VP_PROF_X0, VP_PROF_Y0, VP_PROF_X1, VP_PROF_Y1)
fig = plt.figure(figsize=(16, 16 * (y1 - y0) / (x1 - x0))); ax = fig.add_axes([0, 0, 1, 1]); ctx = RenderContext(doc); ctx.set_current_layout(lay)
Frontend(ctx, MatplotlibBackend(ax), config=Configuration(background_policy=BackgroundPolicy.WHITE)).draw_layout(lay, finalize=False)
ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal", adjustable="box"); ax.axis("off")
out = os.path.join(OUT_DXF, "%s-%s_%s_preview.png" % (ch, tag, which)); fig.savefig(out, dpi=110, facecolor="white"); print("preview of", os.path.basename(name), "->", out)
