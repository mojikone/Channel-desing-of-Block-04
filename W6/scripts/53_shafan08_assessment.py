"""Step 53 - the Shafan 08 question (engineer, 2026-10-12): peaks at SHA-J47 and SHA-J51 with the dam (Basin 6, step 52) against
without (Basin 3), per return period, the reservoir's inflow and outflow, and what it would do to the SHA-CH1-FP sections: the
75 % part-full rule of the model (n 0.030, the R8 slopes and rises) at the reduced flows, segment by segment, against the R8
design. Reads the depth-area DSS files of the HMS project (own analysis-point runs, F-part "DA <rp> B6>SHA-J47").
    python 53_shafan08_assessment.py [--run run_20261012_1608]  -> W6/sewergems/results/shafan08_assessment.md"""
import os, sys, math, hecdss, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE); W3 = os.path.join(os.path.dirname(W6), "W3")
HMS = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydrology\HEC_HMS_Block_04"
A = sys.argv[1:]
def opt(k, d): return A[A.index(k) + 1] if k in A else d
RUN = opt("--run", "run_20261012_1608"); RPS = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr"]


def series(dssfile, element, point):
    """FLOW series of <element> inside the own run of analysis point <point> (peak, volume Mm3, time of peak h)."""
    d = hecdss.HecDss(dssfile)
    for p in [str(x) for x in d.get_catalog()]:
        parts = p.split("/")
        if len(parts) < 7: continue
        if parts[2] == element and parts[3] == "FLOW" and parts[6].split(">")[-1] == point:
            v = list(d.get(p).values); d.close(); i = max(range(len(v)), key=lambda k: v[k]); return max(v), sum(v) * 300 / 1e6, i * 5 / 60.0
    d.close(); return None


rows = []
for rp in RPS:
    f3, f6 = os.path.join(HMS, "DA_%s_B3.dss" % rp), os.path.join(HMS, "DA_%s_B6.dss" % rp)
    if not (os.path.exists(f3) and os.path.exists(f6)): print("missing", rp); continue
    r = {"rp": rp}
    for pt in ("SHA-J47", "SHA-J51"):
        a, b = series(f3, pt, pt), series(f6, pt, pt)
        r[pt + " B3"], r[pt + " B6"] = a[0], b[0]; r[pt + " t3"], r[pt + " t6"] = a[2], b[2]
    s_in = series(f6, "Shafan 08 site", "SHA-J47"); s_out = series(f6, "Shafan 08 Reservoir", "SHA-J47")
    r["dam in"], r["dam out"], r["dam t_out"] = s_in[0], s_out[0], s_out[2]; rows.append(r)
df = pd.DataFrame(rows)
df["J47 cut %"] = (100 * (1 - df["SHA-J47 B6"] / df["SHA-J47 B3"])).round(1); df["J51 cut %"] = (100 * (1 - df["SHA-J51 B6"] / df["SHA-J51 B3"])).round(1)

# the SHA-CH1-FP sections at 200 yr: R8 against the 75 % rule at the reduced flows
c = pd.read_csv(os.path.join(W6, "sewergems", "results", RUN, "bridge_exports", "conduits_200yr.csv")).set_index("label")
seg = [l for l in c.index if l.startswith("SHACH1-C")]; seg.sort(key=lambda s: int(s.split("-C")[1]))
k200 = df[df["rp"] == "200yr"].iloc[0]; rJ47 = k200["SHA-J47 B6"] / k200["SHA-J47 B3"]; rJ51 = k200["SHA-J51 B6"] / k200["SHA-J51 B3"]
def width(Q, S, rise, n=0.03):
    y = 0.75 * rise; b = 10.0
    while (b * y) * ((b * y) / (b + 2 * y)) ** (2 / 3) * math.sqrt(S) / n < Q: b += 0.5
    return b
W = []
for s in seg:
    q0 = float(c.loc[s, "flow"]); S = max(float(c.loc[s, "slope"]), 1e-4); rise = float(c.loc[s, "rise_m"]); up = c.loc[s, "start"]
    ratio = rJ51 if up in ("SHACH1-11", "SHACH1-12") else rJ47; q1 = q0 * ratio
    W.append((s, round(q0, 0), round(q1, 0), S, rise, float(c.loc[s, "span_m"]), width(q0, S, rise), width(q1, S, rise)))
w = pd.DataFrame(W, columns=["segment", "Q R8", "Q with dam", "slope", "rise", "span R8 (m)", "rule at Q R8", "rule at Q with dam"])

md = ["# What if Shafan 08 had been in the channel hydrology (Basin 6 = Basin 3 + the dam, %s)" % pd.Timestamp.now().strftime("%Y-%m-%d"), "",
      "Peaks in m3/s at the own analysis-point runs; dam inflow and outflow from the SHA-J47 run; cut = reduction of the peak.", "",
      "| RP | SHA-J47 without | with | cut | SHA-J51 without | with | cut | dam inflow | dam outflow | t out (h) |", "|---|---|---|---|---|---|---|---|---|---|"]
for _, r in df.iterrows():
    md.append("| %s | %.0f | %.0f | %.0f %% | %.0f | %.0f | %.0f %% | %.0f | %.0f | %.1f |" % (r["rp"], r["SHA-J47 B3"], r["SHA-J47 B6"], r["J47 cut %"], r["SHA-J51 B3"], r["SHA-J51 B6"], r["J51 cut %"], r["dam in"], r["dam out"], r["dam t_out"]))
md += ["", "## SHA-CH1-FP at 200 yr: the R8 design against the 75 %% rule at the reduced flows (ratios J47 %.3f, J51 %.3f)" % (rJ47, rJ51), "",
       "| segment | Q R8 | Q with dam | slope | rise | span R8 | rule at Q R8 | rule at Q with dam |", "|---|---|---|---|---|---|---|---|"]
for _, r in w.iterrows():
    md.append("| %s | %.0f | %.0f | %.4f | %.1f | %.1f | %.1f | %.1f |" % tuple(r))
md += ["", "Total span R8 %.0f m -> with the dam %.0f m (rule), %.0f %% less." % (w["span R8 (m)"].sum(), w["rule at Q with dam"].sum(), 100 * (1 - w["rule at Q with dam"].sum() / w["rule at Q R8"].sum()))]
# the engine never lets a size decrease downstream: the rule widths read as a running maximum from C1 to C12 (the R8 design equals
# the envelope of the rule at Q R8), so the sizes the engine would choose at the reduced flows are that envelope too
env0, env1, m0, m1 = [], [], 0.0, 0.0
for a, b in zip(w["rule at Q R8"], w["rule at Q with dam"]):
    m0, m1 = max(m0, a), max(m1, b); env0.append(m0); env1.append(m1)
w["envelope R8"], w["envelope with dam"] = env0, env1
md += ["", "## The sizes the engine would choose (no decrease downstream: running maximum of the rule from C1 to C12)", "",
       "| segment | span R8 | envelope of the rule at Q R8 | envelope at Q with dam |", "|---|---|---|---|"]
for _, r in w.iterrows():
    md.append("| %s | %.1f | %.1f | %.1f |" % (r["segment"], r["span R8 (m)"], r["envelope R8"], r["envelope with dam"]))
md += ["", "Total span: R8 %.0f m (the envelope at Q R8 reproduces it: %.0f m) -> with the dam %.0f m, %.0f %% less." % (
    w["span R8 (m)"].sum(), w["envelope R8"].sum(), w["envelope with dam"].sum(), 100 * (1 - w["envelope with dam"].sum() / w["span R8 (m)"].sum()))]
md += ["", "SHA-J47 time of peak at 200 yr: %.1f h without the dam, %.1f h with it; SHA-J51 %.1f / %.1f h." % (k200["SHA-J47 t3"], k200["SHA-J47 t6"], k200["SHA-J51 t3"], k200["SHA-J51 t6"])]
# the dam under its own design storm (Basin 4 dam deliverables, W3) against the dam under the SHA-J47 storm here
b4p = os.path.join(W3, "dams", "data", "dam_summary_B4.csv")
if os.path.exists(b4p):
    b4 = pd.read_csv(b4p); b4 = b4[b4["dam"] == "Shafan 08"].set_index("rp")
    md += ["", "## The dam itself: Basin 4 (its own storm, dam deliverables) against Basin 6 (the SHA-J47 storm, this assessment)", "",
           "Basin 6 reduces the rainfall for the whole SHA-J47 area, so the dam sees less than under its own storm; the J47 peak is what the channel needs.", "",
           "| RP | B4 inflow | B4 outflow | B4 t out (h) | B4 peak level | B6 inflow | B6 outflow | B6 t out (h) |", "|---|---|---|---|---|---|---|---|"]
    for _, r in df.iterrows():
        if r["rp"] in b4.index:
            k = b4.loc[r["rp"]]
            md.append("| %s | %.0f | %.0f | %.1f | %.2f | %.0f | %.0f | %.1f |" % (r["rp"], k["peak_inflow_m3s"], k["peak_outflow_m3s"], k["t_peak_out_h"], k["peak_level_m"], r["dam in"], r["dam out"], r["dam t_out"]))
out = os.path.join(W6, "sewergems", "results", "shafan08_assessment.md"); open(out, "w", encoding="utf-8").write("\n".join(md)); print("\n".join(md)); print("->", out)
