"""
Build the dam-locations workbook for the 9 NAMED junctions in Block 4.

Block 4 has no reservoir elements, so there is no routing and no attenuation:
FLOW and FLOW-COMBINE at these junctions are the same unrouted hydrograph.
What is reported is therefore the INFLOW hydrograph at each dam site - there
is no outflow column, and none can be derived without reservoir elements.
The script verifies the FLOW == FLOW-COMBINE assumption and reports any
junction where it does not hold.

  Sheet 1 - Hydrographs   : datetime + one column per (junction x RP) = 117 series
  Sheet 2 - Peak Inflow   : rows = return periods, cols = junctions (m3/s)
  Sheet 3 - Inflow Volumes: rows = return periods, cols = junctions (Mm3)

Writes: W1/output/dam_junctions.xlsx
"""
from pathlib import Path
import pandas as pd
import hecdss

ROOT       = Path(__file__).resolve().parents[2]
DATA_DIR   = ROOT / "Data" / "HEC_HMS_Block_04"
OUTPUT_DIR = ROOT / "W1" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
XLSX = OUTPUT_DIR / "dam_junctions.xlsx"

RP_ORDER = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr",
            "1000yr", "2000yr", "5000yr", "10000yr", "PMP"]

INTERVAL_S = 300.0   # 5-minute control interval

# Named junctions = dam locations, grouped by wadi system (confirmed by user)
DAM_JUNCTIONS = [
    "Hawasinah 02",
    "Hawasinah 11",
    "Hawasinah EX",
    "Shafan 02",
    "Shafan 08",
    "Sarami 03",
    "Sarami 05",
    "Sakhin 04",
    "Sakhin 08",
]


def dss_name(rp: str) -> str:
    return f"DA_{rp}.dss"


def own_ap_path(paths: list[str], b_part: str, c_part: str) -> str | None:
    """First path with B-part == b_part, C-part == c_part, F-part suffix == b_part."""
    for p in paths:
        parts = p.split("/")
        if len(parts) < 7:
            continue
        if parts[2] != b_part or parts[3] != c_part:
            continue
        f_suf = p.rstrip("/").split(">")[-1] if ">" in p else ""
        if f_suf == b_part:
            return p
    return None


def read_series(dss: hecdss.HecDss, path: str | None):
    """Return (times, values) or (None, None)."""
    if path is None:
        return None, None
    try:
        rec = dss.get(path)
        if rec is None:
            return None, None
        return list(rec.times), list(rec.values)
    except Exception as e:
        print(f"  WARN read error: {e}")
        return None, None


def peak_vol(values) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    return float(max(values)), float(sum(values)) * INTERVAL_S / 1e6


def main():
    data: dict[tuple[str, str], dict] = {}
    mismatches: list[str] = []

    for rp in RP_ORDER:
        dss_path = DATA_DIR / dss_name(rp)
        if not dss_path.exists():
            print(f"  WARN: {dss_path.name} not found - skipping {rp}")
            continue
        print(f"  {rp} ...", end=" ", flush=True)
        with hecdss.HecDss(str(dss_path)) as dss:
            paths = dss.get_catalog().uncondensed_paths
            for jn in DAM_JUNCTIONS:
                t, v = read_series(dss, own_ap_path(paths, jn, "FLOW"))
                _, v_comb = read_series(dss, own_ap_path(paths, jn, "FLOW-COMBINE"))
                # Verify the no-storage assumption: FLOW == FLOW-COMBINE
                if v and v_comb:
                    dmax = max(abs(a - b) for a, b in zip(v, v_comb))
                    if dmax > 1e-6:
                        mismatches.append(f"{jn} / {rp} (max diff {dmax:.4f} m3/s)")
                data[(jn, rp)] = {"t": t, "v": v}
        print("done")

    # ---- Sheet 2: Peak inflow ---------------------------------------------
    peak_rows = []
    for rp in RP_ORDER:
        row: dict = {"return_period": rp}
        for jn in DAM_JUNCTIONS:
            pk, _ = peak_vol(data.get((jn, rp), {}).get("v"))
            row[f"{jn} Inflow Peak (m3/s)"] = round(pk, 4)
        peak_rows.append(row)
    df_peak = pd.DataFrame(peak_rows)

    # ---- Sheet 3: Inflow volumes ------------------------------------------
    vol_rows = []
    for rp in RP_ORDER:
        row = {"return_period": rp}
        for jn in DAM_JUNCTIONS:
            _, vol = peak_vol(data.get((jn, rp), {}).get("v"))
            row[f"{jn} Inflow Vol (Mm3)"] = round(vol, 6)
        vol_rows.append(row)
    df_vol = pd.DataFrame(vol_rows)

    # ---- Sheet 1: Hydrographs ---------------------------------------------
    ref_times = next((data[(jn, rp)]["t"] for rp in RP_ORDER for jn in DAM_JUNCTIONS
                      if data.get((jn, rp), {}).get("t")), None)

    if ref_times is not None:
        idx = pd.DatetimeIndex(ref_times)
        cols: dict[str, list] = {}
        for rp in RP_ORDER:
            for jn in DAM_JUNCTIONS:
                d = data.get((jn, rp), {})
                label = f"{jn} Inflow ({rp})"
                if d.get("v") is not None:
                    ser = pd.Series(d["v"], index=pd.DatetimeIndex(d["t"]))
                    cols[label] = ser.reindex(idx).values.tolist()
                else:
                    cols[label] = [None] * len(idx)
        df_hydro = pd.DataFrame(cols, index=idx)
        df_hydro.index.name = "datetime"
        df_hydro = df_hydro.reset_index()
    else:
        df_hydro = pd.DataFrame(columns=["datetime"])
        print("  WARN: no time series read; Hydrographs sheet is empty.")

    with pd.ExcelWriter(XLSX, engine="openpyxl") as xl:
        df_hydro.to_excel(xl, sheet_name="Hydrographs",   index=False)
        df_peak.to_excel(xl,  sheet_name="Peak Inflow",   index=False)
        df_vol.to_excel(xl,   sheet_name="Inflow Volumes", index=False)

    print(f"\nWritten -> {XLSX}")
    print(f"  Hydrographs: {df_hydro.shape[0]} time steps x {df_hydro.shape[1]-1} series")

    # ---- Verification ------------------------------------------------------
    print("\n--- FLOW vs FLOW-COMBINE (no-storage check) ---")
    if mismatches:
        print(f"  {len(mismatches)} mismatch(es) - routing IS present at:")
        for m in mismatches[:10]:
            print(f"    {m}")
    else:
        print("  Identical at all junctions and RPs: confirms no routing/storage.")

    print("\n--- Peak inflow at dam locations (m3/s) ---")
    print(f"  {'junction':16s} {'100yr':>10s} {'PMP':>10s}")
    for jn in DAM_JUNCTIONS:
        p100, _ = peak_vol(data.get((jn, "100yr"), {}).get("v"))
        ppmp, _ = peak_vol(data.get((jn, "PMP"), {}).get("v"))
        print(f"  {jn:16s} {p100:10.1f} {ppmp:10.1f}")


if __name__ == "__main__":
    main()
