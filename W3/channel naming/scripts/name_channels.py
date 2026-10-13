"""Name the Block 4 channels and dykes after the Block 6 convention.

Name = <GCA>-<CH|D><n>-<FP|SM|SS>
  GCA  first three letters (upper case) of the global catchment name (field J_CA of GCA RENN.shp);
       a leading two-letter word such as "Al " is dropped ("Al Hawasinah" -> HAW).
       A feature belongs to the catchment that holds the largest share of its length.
  CH/D channel or dyke, from CHtt (ends with "CH" -> CH, ends with "D" -> D).
  n    one counter per catchment and per kind (channels 1..n, dykes 1..m), ordered
       flood protection (FP) first, then stormwater main (SM), then stormwater secondary (SS),
       and inside each class from west to east by the westernmost vertex (smallest x, EPSG:32640).
  FP/SM/SS from CHtt: "FP CH"/"FP D" -> FP, "Sw M CH"/"Sw M D" -> SM, "Sw S CH"/"Sw S D" -> SS.

Only Block 4 rows (field Block = 4) are named; Block 2 and Block 6 rows are copied unchanged.

Outputs (output/):
  block4_channel_names.csv   one row per Block 4 feature: fid (0-based shapefile record = QGIS fid), the
                             inputs of the rule, the share of length per catchment, the sort key and the name
  block4_naming_flags.csv    features whose catchment is not clear-cut (main share < 90 %)
  Channels and Dykes 04102026 named.shp   the full source layer (247 features) with Name filled for Block 4
  Block04_channel_names.gpkg layer "block4_named": Block 4 features with the extra check fields
  block6_name_audit.csv      anomalies found in the Block 6 names used as the model (information only)

Run:  python name_channels.py      (geopandas >= 1.0)
"""
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "output"
SRC = Path(r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydrology\SHP\temp\Channels and Dykes 04102026.shp")
GCA = Path(r"W:\2224 Flood Protection Scheme in North & South Batinah_MAFWWR\06-WORKING\04-Hydraulic"
           r"\05 Small Tasks\18 Channel Design\Hydraulic\Block 6\Report\Hydraulic Design of Stormwater Channels"
           r"\Data\GCA RENN.shp")
BLOCK = 4
PREFIX_UPPER = True          # HAW (engineer's example); Block 6 used Title case (Taw)
CLEAR_SHARE = 0.90           # below this share of length in the main catchment the feature is flagged
CLASS_ORDER = {"FP": 0, "SM": 1, "SS": 2}
SUFFIX = {"FP CH": "FP", "Sw M CH": "SM", "Sw S CH": "SS", "FP D": "FP", "Sw M D": "SM", "Sw S D": "SS"}


def gca_code(name: str) -> str:
    words = name.strip().split()
    if len(words) > 1 and len(words[0]) == 2:      # "Al Hawasinah" -> "Hawasinah"
        words = words[1:]
    code = re.sub(r"[^A-Za-z]", "", words[0])[:3]  # letters only: "Ma'awil" -> Maa, as Block 6 did
    return code.upper() if PREFIX_UPPER else code.title()


def kind_of(chtt: str) -> str:
    if chtt.endswith("CH"):
        return "CH"
    if chtt.endswith("D"):
        return "D"
    raise ValueError(f"CHtt {chtt!r} is neither channel nor dyke")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ch = gpd.read_file(SRC)
    gca = gpd.read_file(GCA)
    if gca.crs != ch.crs:
        gca = gca.to_crs(ch.crs)
    ch["fid"] = range(len(ch))                      # shapefile record order = QGIS fid

    b4 = ch[ch["Block"] == BLOCK].copy()
    if b4["CHtt"].isna().any():
        raise SystemExit(f"CHtt empty on fids {b4[b4.CHtt.isna()].fid.tolist()}")

    # --- catchment by share of length -------------------------------------------------------------
    b4["length_m"] = b4.geometry.length
    shares = []
    for geom, length in zip(b4.geometry, b4["length_m"]):
        s = {}
        for cname, cgeom in zip(gca["J_CA"], gca.geometry):
            inter = geom.intersection(cgeom)
            if not inter.is_empty and inter.length > 0:
                s[cname] = inter.length / length
        shares.append(dict(sorted(s.items(), key=lambda kv: -kv[1])))
    b4["gca_shares"] = ["; ".join(f"{k} {v:.1%}" for k, v in s.items()) for s in shares]
    b4["GCA"] = [next(iter(s)) if s else None for s in shares]
    b4["gca_share"] = [next(iter(s.values())) if s else 0.0 for s in shares]
    if b4["GCA"].isna().any():
        raise SystemExit(f"no catchment for fids {b4[b4.GCA.isna()].fid.tolist()}")

    # --- rule inputs --------------------------------------------------------------------------------
    b4["prefix"] = b4["GCA"].map(gca_code)
    b4["kind"] = b4["CHtt"].map(kind_of)
    b4["suffix"] = b4["CHtt"].map(SUFFIX)
    chk = b4["CHtype"].map(lambda t: "CH" if t in (1, 2, 3) else "D")
    if (chk != b4["kind"]).any():
        raise SystemExit(f"CHtype and CHtt disagree on fids {b4[chk != b4.kind].fid.tolist()}")
    b4["west_x"] = b4.geometry.bounds["minx"]
    b4["class_rank"] = b4["suffix"].map(CLASS_ORDER)

    # --- numbering ----------------------------------------------------------------------------------
    b4 = b4.sort_values(["prefix", "kind", "class_rank", "west_x"])
    b4["n"] = b4.groupby(["prefix", "kind"]).cumcount() + 1
    b4["Name"] = b4["prefix"] + "-" + b4["kind"] + b4["n"].astype(str) + "-" + b4["suffix"]
    assert b4["Name"].is_unique
    b4["flag"] = ""
    b4.loc[b4["gca_share"] < CLEAR_SHARE, "flag"] = "catchment share < 90 %"

    # --- outputs ------------------------------------------------------------------------------------
    cols = ["fid", "Block", "CHtype", "CHtt", "Layer", "GCA", "gca_share", "gca_shares", "prefix", "kind",
            "suffix", "west_x", "length_m", "n", "Name", "flag"]
    table = b4[cols].copy()
    table["gca_share"] = table["gca_share"].round(4)
    table["west_x"] = table["west_x"].round(1)
    table["length_m"] = table["length_m"].round(1)
    table.to_csv(OUT / "block4_channel_names.csv", index=False)
    table[table["flag"] != ""].to_csv(OUT / "block4_naming_flags.csv", index=False)

    named = ch.copy()
    named.loc[b4.index, "Name"] = b4["Name"]
    named.drop(columns="fid").to_file(OUT / "Channels and Dykes 04102026 named.shp", driver="ESRI Shapefile")
    b4[cols + ["geometry"]].to_file(OUT / "Block04_channel_names.gpkg", layer="block4_named", driver="GPKG")

    audit_block6(ch, gca)

    print(f"{len(b4)} Block {BLOCK} features named")
    print(table.groupby(["GCA", "kind"]).size().unstack(fill_value=0))
    print(f"flagged: {int((table.flag != '').sum())}")


def audit_block6(ch: gpd.GeoDataFrame, gca: gpd.GeoDataFrame) -> None:
    """Record where the Block 6 names depart from their own rule (information for the engineer)."""
    b6 = ch[(ch["Block"] == 6) & ch["Name"].notna()].copy()
    m = b6["Name"].str.extract(r"^(\w+)-(CH|D)(\d+)-(\w+)$")
    b6["pfx"], b6["kind"], b6["num"], b6["suf"] = m[0], m[1], pd.to_numeric(m[2]), m[3]
    rows = []
    for _, r in b6[b6["num"].isna()].iterrows():
        rows.append((r.fid, r.Name, "name does not follow <GCA>-<CH|D><n>-<class>"))
    ok = b6[b6["num"].notna()]
    for name, g in ok.groupby("Name"):
        if len(g) > 1:
            rows.append((" ".join(map(str, g.fid)), name, "duplicate name"))
    for (p, k, n), g in ok.groupby(["pfx", "kind", "num"]):
        if g["suf"].nunique() > 1:
            rows.append((" ".join(map(str, g.fid)), " / ".join(g.Name), "same number used for two classes"))
    for (p, k), g in ok.groupby(["pfx", "kind"]):
        nums = set(g["num"].astype(int))
        gaps = [i for i in range(1, max(nums) + 1) if i not in nums]
        if gaps:
            rows.append(("", f"{p}-{k}", f"numbers missing: {gaps}"))
    bad = ok[ok["suf"] != ok["CHtt"].map(SUFFIX)]
    for _, r in bad.iterrows():
        rows.append((r.fid, r.Name, f"class suffix disagrees with CHtt {r.CHtt!r}"))
    # catchment the feature really sits in
    for _, r in ok.iterrows():
        best, share = None, 0.0
        for cname, cgeom in zip(gca["J_CA"], gca.geometry):
            s = r.geometry.intersection(cgeom).length / r.geometry.length
            if s > share:
                best, share = cname, s
        if best is not None and gca_code(best) != gca_code(r.pfx):
            rows.append((r.fid, r.Name, f"lies in {best} ({share:.0%}), prefix says otherwise"))
    pd.DataFrame(rows, columns=["fid", "name", "issue"]).to_csv(OUT / "block6_name_audit.csv", index=False)


if __name__ == "__main__":
    main()
