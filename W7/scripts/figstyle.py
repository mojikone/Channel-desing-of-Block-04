"""Report-grade matplotlib defaults for every W3 figure: Arial, muted ink, hairline grid, no top/right spines."""
import matplotlib as mpl

INK, MUTED, GRID, AXIS = "#404040", "#595959", "#EDEDED", "#BFBFBF"
BLUE, ORANGE, RED, GREY, PALE, TEAL = "#1F4E79", "#C55A11", "#C0504D", "#595959", "#9DC3E6", "#2E75B6"
BLUES = ["#C6DBEF", "#B3CDE8", "#9EC9E2", "#86B9DC", "#6BAED6", "#4F9BCF", "#3E8AC5", "#3182BD", "#2171B5", "#1A5FA3", "#0D4A8E", "#08306B"]

def apply():
    mpl.rcParams.update({
        "font.family": "Arial", "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.4,
        "axes.edgecolor": AXIS, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK, "axes.titlecolor": INK,
        "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 3, "ytick.major.size": 3,
        "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True,
        "legend.frameon": False, "figure.dpi": 100, "savefig.dpi": 200, "savefig.facecolor": "white", "lines.linewidth": 1.5, "lines.markersize": 3.2,
    })

def finish(ax, grid_axis="y"):
    """Per-axes touch-up when an axes was created before apply() or needs a different grid."""
    ax.grid(False); ax.grid(axis=grid_axis, color=GRID, lw=0.5); ax.set_axisbelow(True)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"): ax.spines[sp].set_color(AXIS)
    ax.tick_params(colors=MUTED)
