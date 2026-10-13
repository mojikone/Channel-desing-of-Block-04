"""W3 shared settings: paths, the eight dams, return periods. Every W3 script imports this."""
from pathlib import Path

W3 = Path(__file__).resolve().parents[1]                 # ...\Claude Block 04\W3
CB04 = W3.parent                                          # ...\Claude Block 04
BLOCK4 = CB04.parent                                      # ...\Block 4
HMS = BLOCK4 / "Hydrology" / "HEC_HMS_Block_04"           # live HMS project (results read here, never written)
RESERVOIRS = CB04 / "reservoirs"                          # EAV_<dam>.csv, summary.csv, reservoirs_added.csv
MODEL = CB04 / "model"                                    # Basin_2/3 .basin + .sqlite snapshots
RESULTS_CB04 = CB04 / "results"                           # basin2/3_peak_flow_volume.xlsx etc.
DAMS_SHP = CB04 / "inputs" / "dams" / "Dams updated.shp"  # Dam Name, Crest El, FSL, Reservoir (Mm3), QPMF, Hmax, C, Spillway L
DAMS_XLSX = BLOCK4 / "Hydrology" / "XLS" / "Block 04 Dams.xlsx"

# the eight dams of the scheme (Shafan 08 removed), in the order of the dams sheet west->east is NOT meaningful; keep sheet order
DAMS = ["Hawasinah 02", "Shafan 02", "Hawasinah EX", "Hawasinah 11", "Sarami 03", "Sarami 05", "Sakhin 08", "Sakhin 04"]
# the nine dams of the report (engineer, 2026-10-06): Hawasinah, Shafan, Sarami, Sakhin; HMS names kept, report labels mapped
DAMS9 = ["Hawasinah 02", "Hawasinah 11", "Hawasinah EX", "Shafan 02", "Shafan 08", "Sarami 03", "Sarami 05", "Sakhin 04", "Sakhin 08"]
LABEL = {"Hawasinah EX": "Hawasinah UP", "Sakhin 08": "Sakhin 08 (Mehmum)"}          # names used in the report; charts may drop the bracket
def label(dam, short=False): return ("Sakhin 08" if (short and dam == "Sakhin 08") else LABEL.get(dam, dam))
RPS = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr", "1000yr", "2000yr", "5000yr", "10000yr", "PMP"]
RP_LABEL = {rp: (rp.replace("yr", "-yr") if rp != "PMP" else "PMP") for rp in RPS}
RP_YEARS = {rp: (int(rp[:-2]) if rp != "PMP" else None) for rp in RPS}
DT_S = 300                                                # HMS time step, s
CRS = "EPSG:32640"                                        # WGS 84 / UTM 40N

def suffix_dss(rp, basin="B3"):
    """DSS file of one depth-area analysis: DA_<rp>_<B2|B3>.dss"""
    return HMS / f"DA_{rp}_{basin}.dss"

def own_point(path):
    """True if the DSS pathname is the element's own analysis point (F-part '...>name' == B-part)."""
    parts = path.split("/")
    return len(parts) > 6 and ">" in parts[6] and parts[6].split(">")[-1] == parts[2]

def ensure(p):
    Path(p).mkdir(parents=True, exist_ok=True); return Path(p)
