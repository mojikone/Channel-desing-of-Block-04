"""Step 45 - read the SewerGEMS run of the Block 04 channel model (bridge job 058_b4_run_all.ps1: every return-period scenario
designed on a copy of the engineer's model inside the VM, conduit and node tables exported per scenario by lib/B4.cs) and write
the review tables into W6/sewergems/results/<run>/:
  conduits_long.csv   one row per scenario x conduit: designed size (depth x width parsed from the catalogue label), flow, velocity,
                      depths, grades, slope, inverts
  nodes_long.csv      one row per scenario x node: ground (GDP-raised), invert, hydraulic grade, freeboard = ground - HGL
  summary.md          per scenario: widths designed (count by width, largest), conduits at the top of their catalogue, velocity
                      range, nodes with the HGL above ground, the two 3 m segments
    python 45_sewergems_results.py [run_folder]   (default: the newest D:\\VBOX\\bridge\\out\\b4\\run_*; when results/<run>/bridge_exports exists, the
    exports corrected by step 48 are read instead of the raw bridge files)"""
import os, sys, re, glob, shutil, time
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE)
BRIDGE = r"D:\VBOX\bridge\out\b4"
run = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob(os.path.join(BRIDGE, "run_*")))[-1]
tag = os.path.basename(run); OUT = os.path.join(W6, "sewergems", "results", tag); os.makedirs(OUT, exist_ok=True)
if os.path.isdir(os.path.join(OUT, "bridge_exports")): run = os.path.join(OUT, "bridge_exports")   # the exports corrected by 48_fix_size_labels.py (sizes by class + GUID) replace the raw bridge files
SCEN = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr"]
num = lambda s: pd.to_numeric(s, errors="coerce")


def size_parts(label):
    m = re.match(r"\s*([\d.]+)\s*[xX×]\s*([\d.]+)", str(label))
    return (float(m.group(1)), float(m.group(2))) if m else (None, None)


def md_table(df, index=True):
    """A markdown table without the tabulate dependency."""
    d = df.reset_index() if index else df
    cols = [str(c) for c in d.columns]; rows = [["" if (isinstance(v, float) and v != v) else (("%g" % v) if isinstance(v, float) else str(v)) for v in r] for r in d.itertuples(index=False)]
    return chr(10).join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(r) + " |" for r in rows])


cond, nodes, log = [], [], []
for sc in SCEN:
    fc, fn = os.path.join(run, "conduits_%s.csv" % sc), os.path.join(run, "nodes_%s.csv" % sc)
    if not os.path.exists(fc): log.append("%s: no conduit table" % sc); continue
    c = pd.read_csv(fc); c.insert(0, "scenario", sc)
    c["depth_m"], c["width_m"] = zip(*c["size_label"].map(size_parts)); cond.append(c)
    if os.path.exists(fn):
        n = pd.read_csv(fn); n.insert(0, "scenario", sc)
        for col in ("ground", "invert", "hydraulicgrade"):
            if col in n.columns: n[col] = num(n[col])
        if "hydraulicgrade" in n.columns and "ground" in n.columns: n["freeboard_m"] = (n["ground"] - n["hydraulicgrade"]).round(3)
        nodes.append(n)
C = pd.concat(cond, ignore_index=True); N = pd.concat(nodes, ignore_index=True) if nodes else pd.DataFrame()
for col in C.columns:
    if col not in ("scenario", "label", "start", "stop", "size", "size_label", "active", "class_label", "material"): C[col] = num(C[col])
C.to_csv(os.path.join(OUT, "conduits_long.csv"), index=False)
if len(N): N.to_csv(os.path.join(OUT, "nodes_long.csv"), index=False)
if os.path.exists(os.path.join(run, "log.txt")): shutil.copy2(os.path.join(run, "log.txt"), os.path.join(OUT, "run_log.txt"))
filled = [col for col in C.columns if C[col].notna().any()]
md = ["# SewerGEMS run %s — Block 04 channel design, every return-period scenario" % tag, "",
      "Source: `%s` (job 058_b4_run_all.ps1 on a copy of the engineer's model; the computed copy was delivered as SewerGEMS Block 04_R1.stsw)." % run,
      "Conduits %d, scenarios %s. Result columns with values: %s." % (C["label"].nunique(), ", ".join(sorted(C["scenario"].unique(), key=SCEN.index)), ", ".join(filled)), ""]
md.append("## Designed widths per scenario (count of conduits by catalogue width, m)")
pv = C.pivot_table(index="width_m", columns="scenario", values="label", aggfunc="count").reindex(columns=[s for s in SCEN if s in C["scenario"].unique()]).fillna(0).astype(int)
md += ["", md_table(pv), ""]
md.append("## Per scenario")
for sc in [s for s in SCEN if s in C["scenario"].unique()]:
    d = C[C["scenario"] == sc]
    top = d[d["width_m"] >= d.groupby("depth_m")["width_m"].transform("max")] if d["width_m"].notna().any() else d.iloc[0:0]
    vel = d["velocity"] if "velocity" in d.columns else pd.Series(dtype=float)
    line = "- **%s**: widths %s to %s m (median %s); depth 3 m on %s; " % (sc, d["width_m"].min(), d["width_m"].max(), d["width_m"].median(), ", ".join(d[d["depth_m"] == 3.0]["label"].tolist()) or "none")
    if vel.notna().any(): line += "velocity %.2f to %.2f m/s (%d conduits over 3 m/s); " % (vel.min(), vel.max(), int((vel > 3).sum()))
    if len(N) and "freeboard_m" in N.columns:
        nn = N[N["scenario"] == sc]; over = nn[nn["freeboard_m"] < 0]
        line += "%d nodes with the HGL above the GDP-raised ground%s" % (len(over), (": " + ", ".join("%s (%.2f m)" % (r["label"], -r["freeboard_m"]) for _, r in over.sort_values("freeboard_m").head(12).iterrows())) if len(over) else "")
    md.append(line)
md += ["", "## Largest designed widths (200 yr)", ""]
d200 = C[C["scenario"] == ("200yr" if "200yr" in C["scenario"].unique() else C["scenario"].iloc[-1])]
cols = [c for c in ("label", "size_label", "width_m", "length_m", "slope", "flow", "velocity", "depthin", "depthout") if c in d200.columns]
md += [md_table(d200.sort_values("width_m", ascending=False).head(15)[cols], index=False), ""]
open(os.path.join(OUT, "summary.md"), "w", encoding="utf-8").write("\n".join(md + log))
print("\n".join(md[:12])); print("...written", OUT)
