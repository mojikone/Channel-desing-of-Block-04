"""Step 23 - the USBR sediment distribution design curves (Figure 2.25 of the manual) drawn from the engine's type
functions, for the reservoir volume reduction section (as in the Majlas sedimentation report), and the relative
sediment-area functions a(p). Writes sediment/figures/design_curves.png and sediment_area_functions.png.
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reservoir_sedimentation import distribution as dist
import figstyle as FS; FS.apply()
from config import W3, ensure
FIG = ensure(W3 / "sediment" / "figures"); p = np.linspace(0.001, 0.999, 400); cols = {1: FS.BLUE, 2: FS.ORANGE, 3: FS.RED, 4: FS.GREY}; names = {1: "Type I, lake", 2: "Type II, flood plain / foothill", 3: "Type III, hill", 4: "Type IV, gorge"}
fig, ax = plt.subplots(figsize=(6.2, 4.6))
for t in (1, 2, 3, 4):
    a = np.array([dist.relative_area(x, t) for x in p]); cum = np.cumsum(a) / a.sum() * 100   # share of the sediment deposited below relative depth p
    ax.plot(cum, p * 100, color=cols[t], lw=1.6, label=names[t])
ax.plot([0, 100], [0, 100], color="#BFBFBF", lw=0.8, ls="--", label="area-increment line")
ax.set_xlabel("sediment deposited below the depth, % of the total"); ax.set_ylabel("depth above the original bed, % of the reservoir depth"); ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.legend(loc="upper left"); FS.finish(ax, "both")
ax.set_title("Sediment distribution design curves (USBR Erosion and Sedimentation Manual, Figure 2.25)", loc="left", fontsize=8.5); fig.tight_layout(); fig.savefig(FIG / "design_curves.png", dpi=200); plt.close(fig)
fig, ax = plt.subplots(figsize=(6.2, 3.6))
for t in (1, 2, 3, 4): ax.plot(p, [dist.relative_area(x, t) for x in p], color=cols[t], lw=1.6, label=names[t])
ax.set_xlabel("relative depth p above the original bed (1 at FSL)"); ax.set_ylabel("relative sediment area a(p)"); ax.set_ylim(0, 3); ax.legend(); FS.finish(ax, "both")
ax.set_title("Relative sediment-area functions a(p) = C pᴬ (1 − p)ᴮ", loc="left", fontsize=8.5); fig.tight_layout(); fig.savefig(FIG / "sediment_area_functions.png", dpi=200); plt.close(fig); print("written", FIG)
