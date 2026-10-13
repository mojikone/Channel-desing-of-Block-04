"""2.6.1  Reservoir Sediment Trap Efficiency.

Brune (1953) median curve for large storage / normally ponded reservoirs
(the class recommended by the manual for this reservoir).  The curve is
given graphically in the manual as Figure 2.19; it is represented here by
its digitised median-curve points and interpolated in log-ratio space.

Trap efficiency is returned as a fraction (0-1) of the inflowing sediment
that is retained, as a function of the ratio of reservoir capacity to mean
annual inflow (both as volumes).
"""
from __future__ import annotations

import numpy as np

# Digitised Brune (1953) median curve: (capacity/inflow ratio, TE %).
# Consistent with the manual's stated anchor points (see module tests).
_CI_RATIO = np.array([
    0.001, 0.002, 0.003, 0.005, 0.007, 0.01, 0.02, 0.03, 0.05, 0.07,
    0.10, 0.20, 0.30, 0.50, 0.70, 1.00, 2.00, 5.00, 10.0,
])
_TE_PERCENT = np.array([
    0.0, 10.0, 16.0, 24.0, 30.0, 42.0, 52.0, 60.0, 68.0, 74.0,
    78.0, 84.0, 87.0, 91.0, 93.0, 95.0, 96.5, 98.0, 99.0,
])

_LOG_CI = np.log10(_CI_RATIO)


def brune_trap_efficiency(capacity_inflow_ratio: float) -> float:
    """Long-term trap efficiency (fraction) from Brune's median curve.

    Parameters
    ----------
    capacity_inflow_ratio : reservoir capacity divided by mean annual
        inflow volume (dimensionless, both volumes in the same units).
    """
    if capacity_inflow_ratio <= 0:
        raise ValueError("capacity/inflow ratio must be positive")
    x = np.log10(capacity_inflow_ratio)
    te = np.interp(x, _LOG_CI, _TE_PERCENT)  # clamps at the end points
    return float(te) / 100.0
