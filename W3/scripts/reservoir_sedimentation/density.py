"""2.6.2  Density of Deposited Sediment.

Implements the Lara & Pemberton (1965) unit-weight equation and Miller's
(1953) time-compaction approximation, exactly as given in the USBR
Erosion and Sedimentation Manual, Section 2.6.2.

Initial unit weight (Eq. 2.39):

    W1 = Wc*pc + Wm*pm + Ws*ps

Average unit weight after T years (Eq. 2.40, Miller 1953):

    W_T = W1 + 0.4343 * K * ( T/(T-1) * ln(T) - 1 )

Compaction constant (Eq. 2.41):

    K = Kc*pc + Km*pm + Ks*ps

pc, pm, ps are the fractions (0-1) of clay, silt and sand in the
incoming sediment.  Coefficients depend on the reservoir operation type:

    1  Sediment always submerged or nearly submerged
    2  Normally moderate to considerable reservoir drawdown
    3  Reservoir normally empty
    4  Riverbed sediments upstream of reservoir
"""
from __future__ import annotations

import math

# Wc, Wm, Ws  -- initial unit weight coefficients, Eq. 2.39 (manual p.2-63).
# English units are lb/ft3, metric units are kg/m3.
_W_ENGLISH = {
    #        Wc    Wm    Ws
    1: (26.0, 70.0, 97.0),
    2: (35.0, 71.0, 97.0),
    3: (40.0, 72.0, 97.0),
    4: (60.0, 73.0, 97.0),
}
_W_METRIC = {
    1: (416.0, 1120.0, 1550.0),
    2: (561.0, 1140.0, 1550.0),
    3: (641.0, 1150.0, 1550.0),
    4: (961.0, 1170.0, 1550.0),
}

# Kc, Km, Ks  -- compaction coefficients, Eq. 2.41 (manual p.2-63).
_K_ENGLISH = {
    #       Kc    Km   Ks
    1: (16.0, 5.7, 0.0),
    2: (8.4, 1.8, 0.0),
    3: (0.0, 0.0, 0.0),
    4: (0.0, 0.0, 0.0),
}
_K_METRIC = {
    1: (256.0, 91.0, 0.0),
    2: (135.0, 29.0, 0.0),
    3: (0.0, 0.0, 0.0),
    4: (0.0, 0.0, 0.0),
}

_LOG10_E = 0.4343  # log10(e), the constant printed in Eq. 2.40 of the manual

VALID_OPERATIONS = (1, 2, 3, 4)


def _check(pc: float, pm: float, ps: float, operation: int, units: str):
    if operation not in VALID_OPERATIONS:
        raise ValueError(f"operation must be one of {VALID_OPERATIONS}, got {operation!r}")
    if units not in ("english", "metric"):
        raise ValueError("units must be 'english' or 'metric'")
    total = pc + pm + ps
    if not math.isclose(total, 1.0, abs_tol=1e-3):
        raise ValueError(
            f"clay+silt+sand fractions must sum to 1.0 (got {total:.4f}); "
            "pass fractions, not percentages"
        )


def initial_unit_weight(pc: float, pm: float, ps: float, operation: int,
                        units: str = "metric") -> float:
    """Initial (year-1) dry unit weight of the deposit, Eq. 2.39."""
    _check(pc, pm, ps, operation, units)
    Wc, Wm, Ws = (_W_METRIC if units == "metric" else _W_ENGLISH)[operation]
    return Wc * pc + Wm * pm + Ws * ps


def k_factor(pc: float, pm: float, ps: float, operation: int,
             units: str = "metric") -> float:
    """Compaction constant K, Eq. 2.41."""
    _check(pc, pm, ps, operation, units)
    Kc, Km, Ks = (_K_METRIC if units == "metric" else _K_ENGLISH)[operation]
    return Kc * pc + Km * pm + Ks * ps


def compacted_unit_weight(W1: float, K: float, years: float) -> float:
    """Average unit weight after ``years`` of operation, Eq. 2.40 (Miller).

    At T = 1 the compaction term is defined to be zero (no consolidation
    history yet), so the initial unit weight is returned unchanged.
    """
    if years <= 0:
        raise ValueError("years must be positive")
    if math.isclose(years, 1.0):
        return W1
    T = float(years)
    return W1 + _LOG10_E * K * (T / (T - 1.0) * math.log(T) - 1.0)


def deposited_unit_weight(pc: float, pm: float, ps: float, operation: int,
                          years: float, units: str = "metric") -> float:
    """Convenience: T-year average deposited unit weight from fractions."""
    W1 = initial_unit_weight(pc, pm, ps, operation, units)
    K = k_factor(pc, pm, ps, operation, units)
    return compacted_unit_weight(W1, K, years)
