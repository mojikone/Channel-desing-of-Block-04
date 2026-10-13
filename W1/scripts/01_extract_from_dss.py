"""
Extract peak flow (m3/s) and volume (Mm3) for all elements from the Block 4
depth-area (DAA) DSS files.

For each element and return period:
  - Uses the element's OWN analysis point only (B-part == F-part suffix after '>').
  - C-part = FLOW for all elements.
  - Peak   = max(time-series values)
  - Volume = sum(values) x 300 s (5-min control interval) / 1e6  [Mm3]

Block 4 differences from the reference project:
  - DSS files are named DA_{rp}.dss (no _1D_DAM___All suffix).
  - F-part reads 'DAA:DA 100yr>S11' (space, not underscore).
  - Basin has no reservoirs, diversions or sinks - junctions only.

Writes: W1/output/peak_flow_volume.csv
Columns: element, rp, peak_m3s, vol_Mm3
"""
from pathlib import Path
import csv
import hecdss

ROOT       = Path(__file__).resolve().parents[2]
DATA_DIR   = ROOT / "Data" / "HEC_HMS_Block_04"
OUTPUT_DIR = ROOT / "W1" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RP_ORDER = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr",
            "1000yr", "2000yr", "5000yr", "10000yr", "PMP"]

INTERVAL_S = 300.0   # 5-minute control interval (Control_1.control)


def dss_name(rp: str) -> str:
    return f"DA_{rp}.dss"


def own_ap_flow_paths(paths: list[str]) -> dict[str, str]:
    """
    Return {element_name: first_path} for paths where:
      B-part == F-part suffix  (element's own analysis point)
      C-part == 'FLOW'
    Only the first D-part block per element is kept - every D-part block for
    the same occurrence holds the full time series.
    """
    seen: dict[str, str] = {}
    for p in paths:
        parts = p.split("/")
        if len(parts) < 7:
            continue
        b_part = parts[2]
        c_part = parts[3]
        if c_part != "FLOW":
            continue
        f_part = p.rstrip("/").split(">")[-1] if ">" in p else ""
        if b_part == f_part and b_part not in seen:
            seen[b_part] = p
    return seen


def read_peak_vol(dss: hecdss.HecDss, path: str) -> tuple[float, float]:
    """Return (peak_m3s, vol_Mm3) from a DSS regular time-series record."""
    rec = dss.get(path)
    if rec is None:
        return 0.0, 0.0
    vals = rec.values
    peak = float(max(vals))
    vol = float(sum(vals)) * INTERVAL_S / 1e6
    return peak, vol


def main():
    rows: list[dict] = []

    for rp in RP_ORDER:
        dss_path = DATA_DIR / dss_name(rp)
        if not dss_path.exists():
            print(f"  WARN: {dss_path.name} not found - skipping {rp}")
            continue

        print(f"  {rp} ...", end=" ", flush=True)
        with hecdss.HecDss(str(dss_path)) as dss:
            paths = dss.get_catalog().uncondensed_paths
            flow_map = own_ap_flow_paths(paths)
            for elem in sorted(flow_map):
                peak, vol = read_peak_vol(dss, flow_map[elem])
                rows.append({
                    "element":  elem,
                    "rp":       rp,
                    "peak_m3s": round(peak, 4),
                    "vol_Mm3":  round(vol, 6),
                })
        print(f"{len(flow_map)} elements")

    out = OUTPUT_DIR / "peak_flow_volume.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["element", "rp", "peak_m3s", "vol_Mm3"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nWritten {len(rows)} rows -> {out}")

    # ---- Sanity checks -----------------------------------------------------
    elems = sorted({r["element"] for r in rows})
    rps_found = [rp for rp in RP_ORDER if any(r["rp"] == rp for r in rows)]
    print(f"\n{len(elems)} elements x {len(rps_found)} return periods")

    missing = [(e, rp) for e in elems for rp in rps_found
               if not any(r["element"] == e and r["rp"] == rp for r in rows)]
    print(f"Missing (element, rp) combinations: {len(missing)}")

    # Peak flow must increase with return period for every element
    lookup = {(r["element"], r["rp"]): r["peak_m3s"] for r in rows}
    breaks = []
    for e in elems:
        seq = [lookup.get((e, rp)) for rp in rps_found]
        for a, b in zip(seq, seq[1:]):
            if a is not None and b is not None and b < a:
                breaks.append(e)
                break
    if breaks:
        print(f"WARN: peak not monotonic with RP for {len(breaks)} element(s): "
              f"{', '.join(breaks[:10])}")
    else:
        print("Monotonicity check (peak increases with RP): PASSED")


if __name__ == "__main__":
    main()
