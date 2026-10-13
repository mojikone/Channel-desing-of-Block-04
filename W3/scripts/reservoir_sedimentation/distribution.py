"""2.6.3  Sediment Distribution Within a Reservoir.

Empirical Area-Reduction Method (Borland & Miller 1960; revisions by
Lara 1962), as presented in the USBR Erosion and Sedimentation Manual,
Section 2.6.3.

The relative sediment area for each reservoir type (manual p.2-73):

    a(p) = C * p**A * (1 - p)**B

        Type   C        A       B
        I      5.074    1.85    0.36
        II     2.487    0.57    0.41
        III   16.967    1.15    2.32
        IV     1.486   -0.25    1.34

with p the relative depth measured from the reservoir bottom (p=0) to the
top of the analysed pool (p=1).

The new zero-capacity (sediment) elevation at the dam is the relative
depth p0 where the reservoir function

    f(p) = (S - V_h) / (H * A_h)                                    (2.xx)

equals the type curve

    F(p) = integral_p^1 a(x) dx / a(p) ,

where S is the sediment volume, V_h and A_h are the original capacity and
area at the elevation of relative depth p, and H is the original depth.
This is the "Table of F values" / Figure 2.28 construction.

Sediment is then distributed with area A_s(p) = (A(p0)/a(p0)) * a(p) above
p0, and the reservoir filled completely below p0, giving the revised
(post-sedimentation) area and capacity curves.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import integrate, optimize

from .eav import EAVCurve

# Design-curve coefficients (C, A, B) for reservoir types I..IV.
TYPE_COEFFS = {
    1: (5.074, 1.85, 0.36),
    2: (2.487, 0.57, 0.41),
    3: (16.967, 1.15, 2.32),
    4: (1.486, -0.25, 1.34),
}

TYPE_NAMES = {
    1: "I  (Lake)",
    2: "II  (Flood plain / foothill)",
    3: "III  (Hill)",
    4: "IV  (Gorge)",
}


def relative_area(p: float, reservoir_type: int) -> float:
    """Relative sediment area a(p) for the given reservoir type."""
    C, A, B = TYPE_COEFFS[reservoir_type]
    if p <= 0.0 or p >= 1.0:
        # a -> 0 at p=1; at p=0 it is 0 unless A<0 (type IV) where it -> inf.
        if p <= 0.0:
            return float("inf") if A < 0 else 0.0
        return 0.0
    return C * p**A * (1.0 - p) ** B


def _area_integral(p_lo: float, p_hi: float, reservoir_type: int) -> float:
    val, _ = integrate.quad(relative_area, p_lo, p_hi, args=(reservoir_type,),
                            points=[p_lo, p_hi], limit=100)
    return val


def F_type(p: float, reservoir_type: int) -> float:
    """Type curve F(p) = integral_p^1 a(x) dx / a(p)."""
    a_p = relative_area(p, reservoir_type)
    if not np.isfinite(a_p) or a_p == 0.0:
        return 0.0
    return _area_integral(p, 1.0, reservoir_type) / a_p


def classify_type(m: float) -> int:
    """Reservoir type from the depth-capacity shape factor m (USBR ranges).

        Type I   : m = 3.5 - 4.5   (lake)
        Type II  : m = 2.5 - 3.5   (flood plain / foothill)
        Type III : m = 1.5 - 2.5   (hill)
        Type IV  : m = 1.0 - 1.5   (gorge)
    """
    if m >= 3.5:
        return 1
    if m >= 2.5:
        return 2
    if m >= 1.5:
        return 3
    return 4


def reservoir_shape_m(eav: EAVCurve, bottom: float, top: float) -> float:
    """Depth-capacity shape factor m = slope of ln(capacity) vs ln(depth).

    Fitted on the *original* survey between the bottom and the analysed
    top, using only points with positive depth and capacity (manual: plot
    the stage-capacity relationship for the original survey only).
    """
    mask = (eav.elevation > bottom) & (eav.elevation <= top) & (eav.volume > 0)
    depth = eav.elevation[mask] - bottom
    cap = eav.volume[mask]
    good = depth > 0
    slope, _ = np.polyfit(np.log(depth[good]), np.log(cap[good]), 1)
    return float(slope)


@dataclass
class DistributionResult:
    reservoir_type: int
    sediment_volume: float
    p_zero: float
    new_zero_elevation: float
    elevation: np.ndarray
    original_area: np.ndarray
    original_capacity: np.ndarray
    sediment_area: np.ndarray
    sediment_volume_below: np.ndarray
    revised_area: np.ndarray
    revised_capacity: np.ndarray
    total_sediment: float


def new_zero_relative_depth(eav: EAVCurve, sediment_volume: float,
                            reservoir_type: int, top: float, bottom: float) -> float:
    """Solve f(p) = F_type(p) for the new zero-capacity relative depth p0."""
    H = top - bottom

    def g(p: float) -> float:
        h = bottom + p * H
        A_h = eav.area_at(h)
        V_h = eav.volume_at(h)
        if A_h <= 0:
            return np.inf
        f = (sediment_volume - V_h) / (H * A_h)
        return f - F_type(p, reservoir_type)

    # Block 04 (2026-10-06): the same root, solved on the product form
    #     g2(p) = (S - V_h) - H * A_h * F(p)
    # which is finite everywhere (g itself blows up near p -> 0 where A_h -> 0, so that a linear scan could miss
    # the crossing and the old fallback returned p near 1, i.e. a reservoir "filled" by a small sediment volume).
    # g2 is positive at p -> 0 (sediment volume S) and negative at p = 1 (S < capacity): the first + to - crossing on a
    # log-spaced grid is the new zero-capacity depth; no crossing means the sediment is negligible at the dam.
    def g2(p: float) -> float:
        h = bottom + p * H
        return (sediment_volume - eav.volume_at(h)) - H * eav.area_at(h) * F_type(p, reservoir_type)

    ps = np.unique(np.concatenate([np.logspace(-6, -2, 120), np.linspace(0.01, 0.999, 600)]))
    vals = np.array([g2(p) for p in ps])
    finite = np.isfinite(vals)
    ps, vals = ps[finite], vals[finite]
    cross = np.where((vals[:-1] > 0) & (vals[1:] <= 0))[0]
    if len(cross) == 0:
        return float(ps[0]) if vals[0] <= 0 else float(ps[-1]) if sediment_volume >= eav.volume_at(top) else float(ps[0])
    i = cross[0]
    return float(optimize.brentq(g2, ps[i], ps[i + 1], xtol=1e-9))


def distribute(eav: EAVCurve, sediment_volume: float, reservoir_type: int,
               top: float, bottom: float | None = None) -> DistributionResult:
    """Distribute ``sediment_volume`` through the reservoir by the Empirical
    Area-Reduction Method and return the revised (post-sedimentation) EAV."""
    if bottom is None:
        bottom = eav.elevation_min
    H = top - bottom

    p0 = new_zero_relative_depth(eav, sediment_volume, reservoir_type, top, bottom)
    h0 = bottom + p0 * H
    a0 = relative_area(p0, reservoir_type)
    A0 = eav.area_at(h0)
    V_h0 = eav.volume_at(h0)
    # Block 04 (2026-10-06): the sediment-area scale Ka is fixed by volume conservation above the new zero,
    #     Ka = (S - V(h0)) / (H * integral_p0^1 a(p) dp),
    # which equals A(h0)/a(p0) at the exact intersection but stays finite when p0 sits at the bed (small sediment
    # volume, DEM curve with a finite area at its first step), where A(h0)/a(p0) blew up and "filled" the reservoir.
    integ = _area_integral(p0, 1.0, reservoir_type) * H
    Ka = (sediment_volume - V_h0) / integ if integ > 0 else A0 / a0
    A0 = min(A0, Ka * a0) if np.isfinite(a0) and a0 > 0 else A0

    # Output is returned on the original (clipped) elevation grid so the
    # revised curve lines up row-for-row with the input EAV.  The new zero
    # elevation h0 is used only as an internal integration breakpoint.
    curve = eav.clipped(top)
    elev = curve.elevation.copy()
    orig_area = np.array([eav.area_at(h) for h in elev])
    orig_cap = np.array([eav.volume_at(h) for h in elev])

    sed_area = np.empty_like(elev)
    for i, h in enumerate(elev):
        if h <= h0 + 1e-9:
            sed_area[i] = orig_area[i]           # reservoir filled completely
        else:
            p = (h - bottom) / H
            sed_area[i] = min(Ka * relative_area(p, reservoir_type), orig_area[i])

    # Cumulative sediment volume below each elevation.  Below h0 the
    # reservoir is filled completely (sediment volume == original
    # capacity); above h0 add the average-end-area integral of the
    # sediment area, taken from h0 (where sediment area == A0).
    above_nodes_e = np.concatenate(([h0], elev[elev > h0]))
    above_nodes_sa = np.concatenate(([A0], sed_area[elev > h0]))
    cum_above = np.concatenate(([0.0], np.cumsum(
        0.5 * (above_nodes_sa[1:] + above_nodes_sa[:-1]) * np.diff(above_nodes_e))))
    # map each above-h0 grid elevation to its cumulative value
    sed_below = np.where(elev <= h0 + 1e-9, orig_cap, 0.0)
    above_mask = elev > h0
    sed_below[above_mask] = V_h0 + cum_above[1:]

    # where the clip to the original area removed sediment, scale the unclipped part up (at most 5 passes) so the
    # distributed volume matches the deposited volume
    for _ in range(5):
        total = sed_below[-1]
        if total <= 0 or abs(total - sediment_volume) / sediment_volume < 0.002: break
        free = elev > h0
        unclipped = free & (sed_area < orig_area - 1e-9)
        if not unclipped.any(): break
        Ka *= 1.0 + (sediment_volume - total) / max(total, 1e-9)
        for i in np.where(free)[0]:
            p = (elev[i] - bottom) / H
            sed_area[i] = min(Ka * relative_area(p, reservoir_type), orig_area[i])
        above_nodes_sa = np.concatenate(([A0], sed_area[elev > h0]))
        cum_above = np.concatenate(([0.0], np.cumsum(0.5 * (above_nodes_sa[1:] + above_nodes_sa[:-1]) * np.diff(above_nodes_e))))
        sed_below[above_mask] = V_h0 + cum_above[1:]
    revised_cap = np.clip(orig_cap - sed_below, 0.0, None)
    revised_area = np.clip(orig_area - sed_area, 0.0, None)
    total = sed_below[-1]

    return DistributionResult(
        reservoir_type=reservoir_type,
        sediment_volume=sediment_volume,
        p_zero=p0,
        new_zero_elevation=h0,
        elevation=elev,
        original_area=orig_area,
        original_capacity=orig_cap,
        sediment_area=sed_area,
        sediment_volume_below=sed_below,
        revised_area=revised_area,
        revised_capacity=revised_cap,
        total_sediment=total,
    )
