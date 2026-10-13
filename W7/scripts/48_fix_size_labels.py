"""Step 48 - correct the size labels of the bridge exports (the engineer's challenge of 2026-10-11: "HAWCH1-C7 was 3 m depth").
His five catalogue classes share the same 3999 size GUIDs (the n-th size of every class carries the same GUID), so a size is
identified by class + GUID. B4.Export resolved the label by GUID alone and gave the 2.5 m class's label to the two conduits on the
3 m class. This step rewrites conduits_<scenario>.csv from the R2 model database: for every conduit the class and size assigned in
the scenario's physical alternative (a conduit without a row in that alternative inherits from the parent alternative, so the
parent chain is walked) and the size row of that class; it replaces size_label and adds class_id, class_label, material, rise_m,
span_m. The as-run export is moved to bridge_exports_asrun/ first and never overwritten. Gate: the as-run size GUID must equal the
database GUID for every conduit, otherwise the step stops without writing.
    python 48_fix_size_labels.py [--run run_20261011_1721] [--sqlite <the revision's .stsw.sqlite>]"""
import os, sys, glob, shutil, sqlite3
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); W6 = os.path.dirname(HERE)
A = sys.argv[1:]
def opt(k, d=None): return A[A.index(k) + 1] if k in A else d
RUN = opt("--run", "run_20261011_1721"); FT = 0.3048
SQLITE = opt("--sqlite", r"C:\Users\mojtaba\Desktop\Win10 shared folder\SewerGEMS Block 04 11102026\SewerGEMS Block 04_R2.stsw.sqlite")   # the revision the run was made on
EXP = os.path.join(W6, "sewergems", "results", RUN, "bridge_exports"); ASRUN = EXP + "_asrun"

con = sqlite3.connect("file:%s?mode=ro" % SQLITE.replace(" ", "%20").replace("\\", "/"), uri=True)
lab = dict(con.execute("select ElementID, Label from HMIModelingElement"))
phys = dict(con.execute("select ScenarioID, AlternativeID from HMIScenarioAlternative where AlternativeTypeID = 4"))   # scenario -> physical alternative
parent = dict(con.execute("select AlternativeID, ParentID from HMIAlternative"))
tag2sid = {lab[s].replace(" ", ""): s for s in phys if lab.get(s, "").endswith(" yr")}                               # "200 yr" -> "200yr"
sizes = {(cls, g.lower()): (l, r * FT, s * FT) for cls, g, l, r, s in con.execute(
    "select SupportElementID, ClassSizeCollection_Guid, ClassSizeCollection_Label, ClassSizeCollection_Rise, ClassSizeCollection_Span from CatalogConduit_ClassSizeCollection")}
mat = dict(con.execute("select SupportElementID, CatalogConduit_Material from CatalogConduit"))
assign = {(i, a): (c, str(g).lower()) for i, a, c, g in con.execute("select DomainElementID, AlternativeID, CatalogPipeType_CatalogPipeID, CatalogPipeType_CatalogPipeSize from Conduit_Physical_ConduitType_CatalogConduitType")}
con.close()


def resolve(cid, alt):
    """(class, guid, alternative that holds the row) walking up the parent chain; None when no alternative has a row."""
    seen = set()
    while alt and alt not in seen:
        seen.add(alt)
        if (cid, alt) in assign: return assign[(cid, alt)] + (alt,)
        alt = parent.get(alt)
    return None


os.makedirs(ASRUN, exist_ok=True)
for f in sorted(glob.glob(os.path.join(EXP, "nodes_*.csv"))):                                   # the as-run folder is the complete export
    if not os.path.exists(os.path.join(ASRUN, os.path.basename(f))): shutil.copy2(f, ASRUN)
out, bad = [], []
names = sorted({os.path.basename(f) for f in glob.glob(os.path.join(EXP, "conduits_*.csv")) + glob.glob(os.path.join(ASRUN, "conduits_*.csv"))}, key=lambda n: int(n[9:-6]))
for name in names:                                                                               # a file already moved aside is processed too
    f = os.path.join(EXP, name); tag = name[9:-4]; src = os.path.join(ASRUN, name)
    if not os.path.exists(src): shutil.move(f, src)                                              # first run: the as-run file moves aside
    elif os.path.exists(f) and os.path.getsize(f) == 0: os.remove(f)
    c = pd.read_csv(src); sid = tag2sid[tag]; alt = phys[sid]
    cls_id, cls_lab, material, rise, span, label = [], [], [], [], [], []
    changed, inherited, nocat, mism = [], [], [], []
    for _, r in c.iterrows():
        hit = resolve(int(r["id"]), alt)
        if hit is None:
            nocat.append(str(r["label"])); cls_id.append(None); cls_lab.append(""); material.append(""); rise.append(None); span.append(None); label.append(r["size_label"]); continue
        cls, g, holder = hit
        if holder != alt: inherited.append("%s (from alternative %d \"%s\")" % (r["label"], holder, lab.get(holder, "")))
        if str(r["size"]).lower() != g: mism.append("%s: as-run %s vs database %s" % (r["label"], str(r["size"])[:8], g[:8]))
        l, ri, sp = sizes[(cls, g)]
        cls_id.append(cls); cls_lab.append(lab.get(cls, "")); material.append(mat.get(cls, "")); rise.append(round(ri, 3)); span.append(round(sp, 3)); label.append(l)
        if l != r["size_label"]: changed.append("%s: %s -> %s" % (r["label"], r["size_label"], l))
    c["size_label"] = label; k = list(c.columns).index("size_value") + 1
    for j, (col, vals) in enumerate((("class_id", cls_id), ("class_label", cls_lab), ("material", material), ("rise_m", rise), ("span_m", span))):
        if col in c.columns: c[col] = vals                                                       # an export of the fixed B4.Export already carries the columns: overwrite
        else: c.insert(k + j, col, vals)
    if mism: bad += ["%s: %s" % (tag, m) for m in mism]
    else: c.to_csv(f, index=False)
    cnt = pd.Series(cls_lab).value_counts().to_dict(); cnt.pop("", None)
    out.append("- **%s** (scenario %d, physical alternative %d \"%s\"): %d conduits; classes %s; inherited from a parent alternative: %s; without any catalogue row: %s; labels corrected: %s" % (
        tag, sid, alt, lab.get(alt, ""), len(c), ", ".join("%s x%d" % kv for kv in sorted(cnt.items())), ", ".join(inherited) or "none", ", ".join(nocat) or "none", "; ".join(changed) or "none"))
if bad: sys.exit("GUID mismatch between the as-run export and the database, nothing written:\n" + "\n".join(bad))
md = "# Size labels corrected from the R2 database (step 48, %s)\n\nA size is class + GUID: the five catalogue classes share their size GUIDs. The as-run export (label by GUID alone) is kept in `bridge_exports_asrun/`.\n\n%s\n" % (RUN, "\n".join(out))
open(os.path.join(EXP, "..", "size_label_correction.md"), "w", encoding="utf-8").write(md); print(md)
