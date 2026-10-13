"""Report charts (nine dams, Basin 4), report style of scripts/figstyle.py -> report/img/*.png. Every series comes from data_facts.
Engineer's instructions of 2026-10-06: Qp and V annotated on every hydrograph panel, x axis 0-36 h, haloed labels,
bigger legends, EAV charts with area on the upper axis, 500-year panel instead of 1 000, distinct colours.
    python charts_b4.py
"""
import os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
HERE = os.path.dirname(os.path.abspath(__file__)); W3 = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(W3, "scripts"))
import data_facts as A
import figstyle as FS; FS.apply()
IMG = os.path.join(HERE, "img"); os.makedirs(IMG, exist_ok=True)
H5 = pd.read_csv(os.path.join(W3, "dams", "data", "hydrographs_5min_B4.csv"))
HALO = [pe.withStroke(linewidth=2.2, foreground="white")]
lab = A.label

def save(fig, name):
    p = os.path.join(IMG, name + ".png"); fig.savefig(p, dpi=200, bbox_inches="tight"); plt.close(fig); print("  ", name); return p

def c01_q200_grid(rp="200yr"):
    """Inflow against outflow at the nine dams, 200-year; peak and volume of both on every panel."""
    fig, axes = plt.subplots(3, 3, figsize=(7.6, 8.4), sharex=True)
    for ax, dam in zip(axes.ravel(), A.DAMS):
        s = H5[(H5.dam == dam) & (H5.rp == rp)]
        ax.plot(s.time_h, s.inflow_m3s, color=FS.BLUE, lw=1.4, label="inflow"); ax.plot(s.time_h, s.outflow_m3s, color=FS.ORANGE, lw=1.4, ls="--", label="outflow")
        qi, vi = s.inflow_m3s.max(), s.inflow_m3s.sum() * 300 / 1e6; qo, vo = s.outflow_m3s.max(), s.outflow_m3s.sum() * 300 / 1e6
        ax.set_title(lab(dam, True), fontsize=8.5, loc="left", fontweight="bold")
        ax.text(0.98, 0.95, f"inflow:  Qp {qi:,.0f} m³/s, V {vi:,.1f} Mm³\noutflow: Qp {qo:,.0f} m³/s, V {vo:,.1f} Mm³", transform=ax.transAxes, ha="right", va="top", fontsize=6.6, color=FS.INK, path_effects=HALO, linespacing=1.4)
        ax.set_xlim(0, 36); ax.set_xticks(range(0, 37, 6)); ax.set_ylim(0, qi * 1.45); FS.finish(ax); ax.tick_params(labelsize=6.8)
    for ax in axes[-1]: ax.set_xlabel("hours from the start of the storm", fontsize=7.5)
    for ax in axes[:, 0]: ax.set_ylabel("flow, m³/s", fontsize=7.5)
    axes[0, 0].legend(loc="center right", fontsize=7, bbox_to_anchor=(0.98, 0.55)); fig.tight_layout(h_pad=1.0, w_pad=1.0); return save(fig, f"C01_q{A.RP_LABEL[rp]}_grid")

def c02_inflows(dam):
    """All return periods at one dam: inflow hydrographs, 0-36 h, peaks labelled with a white halo where there is room."""
    fig, ax = plt.subplots(figsize=(7.6, 4.4)); peaks = {}
    for k, rp in enumerate(A.RPS):
        s = H5[(H5.dam == dam) & (H5.rp == rp)]; col = "#000000" if rp == "PMP" else FS.BLUES[k]
        ax.plot(s.time_h, s.inflow_m3s, color=col, lw=1.7 if rp == "PMP" else 1.15, ls="--" if rp == "PMP" else "-", label=f"{A.RP_LABEL[rp]}{'' if rp == 'PMP' else '-yr'}:  Qp {s.inflow_m3s.max():,.0f} m³/s,  V {s.inflow_m3s.sum() * 300 / 1e6:,.1f} Mm³")
        peaks[rp] = (float(s.time_h.values[s.inflow_m3s.values.argmax()]), float(s.inflow_m3s.max()))
    ymax = max(v for _, v in peaks.values()); last = -1e9
    for rp in sorted(A.RPS, key=lambda r: peaks[r][1]):
        t, q = peaks[rp]
        if q - last >= 0.045 * ymax:
            ax.annotate(f"{A.RP_LABEL[rp]}{'' if rp == 'PMP' else '-yr'}  {q:,.0f} m³/s", (t, q), xytext=(6, 0), textcoords="offset points", fontsize=6.8, color=FS.INK, va="center", path_effects=HALO); last = q
    ax.set_xlim(0, 36); ax.set_xticks(range(0, 37, 6)); ax.set_ylim(0, ymax * 1.08); ax.set_xlabel("hours from the start of the storm"); ax.set_ylabel("inflow, m³/s")
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=7.6, title="return period: peak, volume", title_fontsize=7.6); FS.finish(ax)
    ax.set_title(f"{lab(dam)}: inflow hydrographs of the depth-area analyses", loc="left"); fig.tight_layout(); return save(fig, f"C02_inflows_{dam.replace(' ', '_')}")

def c03_attenuation():
    """Peak inflow and routed outflow at the nine dams for 100, 200 and 500 years."""
    pin, pout = A.peaks("in"), A.peaks("out"); rps = ["100yr", "200yr", "500yr"]
    fig, axes = plt.subplots(1, 3, figsize=(7.6, 3.6)); x = np.arange(len(A.DAMS)); w = 0.38
    for ax, rp in zip(axes, rps):
        b1 = ax.bar(x - w / 2, pin[rp], w, color=FS.BLUE, label="peak inflow"); b2 = ax.bar(x + w / 2, pout[rp], w, color=FS.ORANGE, label="peak outflow")
        for b, v in list(zip(b1, pin[rp])) + list(zip(b2, pout[rp])): ax.text(b.get_x() + b.get_width() / 2, v + pin[rp].max() * 0.012, f"{v:,.0f}", ha="center", fontsize=5.2, color=FS.MUTED, rotation=90, va="bottom")
        ax.set_title(f"{A.RP_LABEL[rp]}-year", loc="left"); ax.set_xticks(x); ax.set_xticklabels([lab(d, True).replace("Hawasinah", "Haw.") for d in A.DAMS], rotation=60, ha="right", fontsize=6.2); ax.set_ylim(0, pin[rp].max() * 1.28); FS.finish(ax)
    axes[0].set_ylabel("m³/s"); axes[0].legend(loc="upper left", fontsize=6.8); fig.tight_layout(); return save(fig, "C03_attenuation")

def c05_eav(dam):
    """Elevation-area-volume of one reservoir in the Block 6 format: capacity on the lower axis, area on the upper
    axis, the full supply level with its capacity and area, the crest dotted."""
    ds = A.dams_sheet(); e = A.eav_curve(dam); z = e.elevation_m.values; a = e.area_km2.values * 1e6; v = np.zeros_like(z)
    for i in range(1, len(z)): v[i] = v[i - 1] + (z[i] - z[i - 1]) / 3 * (a[i - 1] + a[i] + np.sqrt(a[i - 1] * a[i]))
    fsl, crest = float(ds.loc[dam, "FSL"]), float(ds.loc[dam, "Crest El"]); vf, af = np.interp(fsl, z, v) / 1e6, np.interp(fsl, z, a) / 1e6
    fig, ax = plt.subplots(figsize=(3.75, 3.0)); ax.plot(v / 1e6, z, color=FS.BLUE, lw=1.5, label="capacity"); ax.set_xlabel("capacity, Mm³", fontsize=7); ax.set_ylabel("elevation, m", fontsize=7); ax.set_xlim(0, v[-1] / 1e6 * 1.08)
    ax2 = ax.twiny(); ax2.plot(a / 1e6, z, color=FS.ORANGE, lw=1.3, ls="--", label="area"); ax2.set_xlim(a[-1] / 1e6 * 1.08, 0); ax2.set_xlabel("area, km²", fontsize=7); ax2.tick_params(labelsize=6.3, colors=FS.MUTED); ax2.spines["top"].set_color(FS.AXIS)
    ax.axhline(fsl, color=FS.RED, lw=0.8, ls="--"); ax.axhline(crest, color=FS.GREY, lw=0.7, ls=":")
    import matplotlib.transforms as mtr; bt = mtr.blended_transform_factory(ax.transAxes, ax.transData); z0 = float(z[0]); rng = crest - z0; ax.set_ylim(z0, crest + 0.09 * rng)
    ax.text(0.03, fsl - 0.012 * rng, f"FSL {fsl:.0f} m", transform=bt, fontsize=6.4, color=FS.INK, va="top", ha="left", path_effects=HALO)                      # on the FSL line, left end (free below the line)
    ax.text(0.97, fsl - 0.012 * rng, f"{vf:.1f} Mm³ · {af:.2f} km² at FSL", transform=bt, fontsize=6.2, color=FS.INK, va="top", ha="right", path_effects=HALO)  # right end, below the line
    ax.text(0.5, crest - 0.012 * rng, f"crest {crest:.0f} m", transform=bt, fontsize=6.4, color=FS.INK, va="top", ha="center", path_effects=HALO)                # centred under the crest line, between the two curves
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, loc="lower center", fontsize=6.4, bbox_to_anchor=(0.5, 0.04), ncol=2, columnspacing=1.0); FS.finish(ax, "both"); ax.tick_params(labelsize=6.3)
    ax.set_title(lab(dam), fontsize=8, loc="left", fontweight="bold"); fig.tight_layout(); return save(fig, f"C05_eav_{dam.replace(' ', '_')}")


def _climate_block():
    """Block-wide climate = the mean of the nine dam-site records (W3/climate/climate9_summary.json)."""
    import json
    c = json.load(open(os.path.join(W3, "climate", "climate9_summary.json"), encoding="utf-8")); m = range(1, 13)
    monthly = {k: np.array([np.mean([c[d]["monthly"][str(i)][k] for d in A.DAMS]) for i in m]) for k in ("rain", "t_max", "t_mean", "t_min")}
    years = sorted({int(y) for d in A.DAMS for y in c[d]["annual"]}); annual = np.array([np.mean([c[d]["annual"][str(y)]["rain"] for d in A.DAMS if str(y) in c[d]["annual"]]) for y in years])
    spread = max(abs(c[d]["monthly"][str(i)]["rain"] - monthly["rain"][i - 1]) for d in A.DAMS for i in m)
    return monthly, years, annual, spread

def c08_monthly_climate():
    """One climograph for Block 04 in the form of the Ibri concept report: the air temperature (mean daily maximum, daily
    mean, mean daily minimum) on the left axis with value labels, the monthly rainfall as bars on the right axis."""
    monthly, years, annual, spread = _climate_block(); months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]; x = np.arange(12)
    fig, ax = plt.subplots(figsize=(7.8, 4.1)); ax2 = ax.twinx()
    bars = ax2.bar(x, monthly["rain"], width=0.55, color="#B4C7E7", label="rainfall, mm a month (right axis)", zorder=1)
    for xi, v in zip(x, monthly["rain"]): ax2.text(xi, v + 0.5, f"{v:.0f}", ha="center", va="bottom", fontsize=7.6, color="#2E75B6")
    ax2.set_ylim(0, max(monthly["rain"]) * 5.2); ax2.set_ylabel("rainfall, mm", fontsize=8.5); ax2.tick_params(labelsize=8, colors=FS.MUTED); ax2.spines["right"].set_color(FS.AXIS); ax2.spines["top"].set_visible(False); ax2.set_axisbelow(True)
    for key, lab_, col in (("t_max", "mean daily maximum", "#C0392B"), ("t_mean", "daily mean", "#595959"), ("t_min", "mean daily minimum", "#1F3B63")):
        ax.plot(x, monthly[key], color=col, lw=1.6, marker="o", ms=3.4, label=lab_, zorder=3)
        if key != "t_mean":
            for xi, v in zip(x, monthly[key]): ax.text(xi, v + 1.2, f"{v:.0f}", ha="center", va="bottom", fontsize=7.6, color=col)
    ax.set_ylim(0, 52); ax.set_xticks(x); ax.set_xticklabels(months, fontsize=8.5); ax.set_ylabel("air temperature at 2 m, °C", fontsize=8.5); ax.tick_params(labelsize=8); ax.set_xlim(-0.6, 11.6)
    ax.set_zorder(ax2.get_zorder() + 1); ax.patch.set_visible(False); FS.finish(ax)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=4, fontsize=7.8, frameon=False, handlelength=2.2)
    fig.tight_layout(); return save(fig, "C08_monthly_climate")

def c09_annual_rain():
    """Annual rainfall of Block 04, 2001-2023: bars = the mean of the nine dam-site records, with the period mean."""
    monthly, years, annual, spread = _climate_block(); mean = float(annual.mean())
    fig, ax = plt.subplots(figsize=(7.8, 3.8)); x = np.arange(len(years))
    ax.bar(x, annual, width=0.66, color="#9DC3E6", edgecolor="none", zorder=2)
    for xi, v in zip(x, annual): ax.text(xi, v + 2, f"{v:.0f}", ha="center", va="bottom", fontsize=7.2, color="#1F3B63", path_effects=HALO, zorder=5)
    ax.axhline(mean, color="#C0392B", lw=1.0, ls="--", zorder=3); ax.text(-0.45, mean + 3, f"mean {mean:.0f} mm", ha="left", va="bottom", fontsize=8, color="#C0392B", path_effects=HALO, zorder=5)
    ax.set_xticks(x); ax.set_xticklabels([str(y) for y in years], fontsize=7.8, rotation=0); ax.set_ylabel("annual rainfall, mm", fontsize=8.5); ax.tick_params(labelsize=8); ax.set_ylim(0, max(annual) * 1.15); ax.set_xlim(-0.7, len(years) - 0.3)
    FS.finish(ax); fig.tight_layout(); return save(fig, "C09_annual_rain")

def c10_rain_patterns():
    """The temporal distribution of the 24-hour design storm used by the model (hypothetical storm, specified pattern):
    the five percent graphs of the project, as cumulative curves and as 10-minute increments."""
    import json
    pat = json.load(open(os.path.join(W3, "dams", "data", "storm_patterns.json"), encoding="utf-8"))
    order = [("FM 2yr", "2-year", "#9DC3E6"), ("FM 5yr", "5-year", "#5B9BD5"), ("FM 10-1000yr", "10- to 1 000-year", "#1F3B63"), ("FM 2000-10000", "2 000- to 10 000-year", "#ED7D31"), ("FM PMP", "PMP", "#C0392B")]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.8, 3.4), gridspec_kw=dict(width_ratios=[1.15, 1]))
    for key, lab_, col in order:
        x = np.array(pat[key]["x_pct"]) * 0.24; y = np.array(pat[key]["y_pct"]); a1.plot(x, y, color=col, lw=1.5, label=lab_)
        inc = np.diff(y); a2.plot(x[1:] - 0.083, inc, color=col, lw=1.2, label=lab_, drawstyle="steps-post")
    a1.set_xlabel("time, h", fontsize=8); a1.set_ylabel("cumulative share of the 24-hour depth, %", fontsize=8); a1.set_xlim(0, 24); a1.set_ylim(0, 100); a1.set_xticks(range(0, 25, 4)); a1.tick_params(labelsize=7.5)
    a2.set_xlabel("time, h", fontsize=8); a2.set_ylabel("share of the depth in each 10 minutes, %", fontsize=8); a2.set_xlim(0, 24); a2.set_xticks(range(0, 25, 4)); a2.tick_params(labelsize=7.5)
    a1.legend(loc="upper left", fontsize=7, title="pattern of the storm", title_fontsize=7.2); FS.finish(a1); FS.finish(a2); fig.tight_layout(); return save(fig, "C10_rain_patterns")

def c06_outfalls():
    """Outfall peaks and volumes, 200-year, without and with the dams."""
    o = A.outfalls(); ov = A.outfall_volumes(); x = np.arange(len(o)); w = 0.38
    for key, left, right, ylab, fmt, step in (("C06_outfalls_peak", o["B2 200yr"], o["B3 200yr"], "200-year peak flow, m³/s", "{:,.0f}", 40), ("C06_outfalls_volume", ov.reindex(o.index)["B2"], ov.reindex(o.index)["B3"], "200-year runoff volume, Mm³", "{:,.1f}", 0.6)):
        fig, ax = plt.subplots(figsize=(7.6, 3.3)); b1 = ax.bar(x - w / 2, left, w, color="#9DC3E6", label="without the dams"); b2 = ax.bar(x + w / 2, right, w, color=FS.BLUE, label="with the dam reservoirs")
        for b, v in list(zip(b1, left)) + list(zip(b2, right)): ax.text(b.get_x() + b.get_width() / 2, v + step, fmt.format(v), ha="center", fontsize=5.8, color=FS.MUTED, rotation=90, va="bottom")
        ax.set_xticks(x); ax.set_xticklabels(o.index, rotation=45, ha="right", fontsize=7); ax.set_ylabel(ylab); ax.set_ylim(0, max(left.max(), right.max()) * 1.32); ax.legend(loc="upper right"); FS.finish(ax); fig.tight_layout(); save(fig, key)

def c07_sediment_steps():
    """Soil loss, delivery ratio (with the 0.2 floor) and the yield used (with the 90 m3/km2/yr floor) per catchment."""
    y = A.sediment_yield(); x = np.arange(len(A.DAMS)); fig, axes = plt.subplots(1, 3, figsize=(7.6, 3.4))
    for ax, (col, lab_, colour, fmtv) in zip(axes, (("soil_loss_t_ha_yr", "soil loss, t/ha/yr", FS.ORANGE, "{:.1f}"), ("sdr_used", "sediment delivery ratio used", FS.GREY, "{:.2f}"), ("yield_m3_km2_yr", "sediment yield used, m³/km²/yr", FS.RED, "{:.0f}"))):
        b = ax.bar(x, y[col], color=colour, width=0.65)
        for bb, v in zip(b, y[col]): ax.text(bb.get_x() + bb.get_width() / 2, v * 1.01, fmtv.format(v), ha="center", fontsize=5.8, color=FS.MUTED, va="bottom")
        ax.set_title(lab_, loc="left", fontsize=8); ax.set_xticks(x); ax.set_xticklabels([lab(d, True).replace("Hawasinah", "Haw.") for d in A.DAMS], rotation=60, ha="right", fontsize=6.2); ax.set_ylim(0, y[col].max() * 1.18); FS.finish(ax)
    fig.tight_layout(); return save(fig, "C07_sediment_steps")

if __name__ == "__main__":
    import sys as _s
    only = [a for a in _s.argv[1:]]
    if not only or "c05" in only: [c05_eav(d) for d in A.DAMS]
    if not only or "c08" in only: c08_monthly_climate(); c09_annual_rain(); c10_rain_patterns()
    if not only: c01_q200_grid(); [c02_inflows(d) for d in A.DAMS]; c03_attenuation(); c06_outfalls(); c07_sediment_steps()
