"""
Build a 2-sheet Excel from peak_flow_volume.csv.

  Sheet 1 - Peak Flow (m3/s) : rows = elements, cols = return periods
  Sheet 2 - Volume (Mm3)     : rows = elements, cols = return periods

Elements are ordered Subbasins (S*), Reaches (R*), numbered Junctions (J*),
then named junctions (dam locations), each group in natural numeric order.

Reads:  W1/output/peak_flow_volume.csv
Writes: W1/output/peak_flow_volume_all_elements.xlsx
"""
from pathlib import Path
import re
import pandas as pd

ROOT       = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "W1" / "output"
CSV        = OUTPUT_DIR / "peak_flow_volume.csv"
XLSX       = OUTPUT_DIR / "peak_flow_volume_all_elements.xlsx"

RP_ORDER = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr",
            "1000yr", "2000yr", "5000yr", "10000yr", "PMP"]


def sort_key(name: str):
    """Group S* < R* < J* < named, then numerically within each group."""
    m = re.fullmatch(r"([SRJ])(\d+)", name)
    if m:
        group = {"S": 0, "R": 1, "J": 2}[m.group(1)]
        return (group, int(m.group(2)), "")
    return (3, 0, name)


def main():
    if not CSV.exists():
        raise FileNotFoundError(f"Run 01_extract_from_dss.py first: {CSV}")

    df  = pd.read_csv(CSV)
    rps = [r for r in RP_ORDER if r in set(df["rp"])]

    pflow = df.pivot(index="element", columns="rp", values="peak_m3s").reindex(columns=rps)
    pvol  = df.pivot(index="element", columns="rp", values="vol_Mm3").reindex(columns=rps)

    order = sorted(pflow.index, key=sort_key)
    pflow = pflow.reindex(order)
    pvol  = pvol.reindex(order)
    pflow.columns.name = None
    pvol.columns.name  = None

    with pd.ExcelWriter(XLSX, engine="openpyxl") as xl:
        pflow.to_excel(xl, sheet_name="Peak Flow m3s")
        pvol.to_excel(xl,  sheet_name="Volume Mm3")

    print(f"Written {pflow.shape[0]} elements x {len(rps)} RPs -> {XLSX}")


if __name__ == "__main__":
    main()
