"""End-to-end reservoir-sedimentation study pipeline.

Chains the three parts of Section 2.6 of the manual:

    2.6.1  trap efficiency         -> mass/volume of sediment retained
    2.6.2  deposited unit weight   -> characterises (and can rescale) volume
    2.6.3  area-reduction method   -> revised elevation-area-volume curve

All internal computation is done in base SI units (elevation m, area m2,
volume m3); results are reported additionally in Mm3 for convenience.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import density, distribution, trap_efficiency
from .eav import EAVCurve


@dataclass
class StudyConfig:
    # -- elevation-area-volume input -------------------------------------
    eav_path: str | Path
    eav_sheet: str
    elevation_col: str
    area_col: str
    volume_col: str
    volume_unit_to_m3: float = 1.0        # multiply workbook volume to get m3

    # -- sediment supply (2.6.1) -----------------------------------------
    catchment_area_km2: float = 0.0
    sediment_yield_m3_per_km2_yr: float = 0.0
    horizon_years: float = 50.0
    trap_efficiency: float | None = 1.0   # fraction; or None to use Brune
    mean_annual_inflow_Mm3: float | None = None  # required if using Brune

    # -- deposited density (2.6.2) ---------------------------------------
    reservoir_operation: int = 2
    clay: float = 0.20
    silt: float = 0.40
    sand: float = 0.40
    reference_unit_weight_kg_m3: float | None = None  # None -> no volume rescale

    # -- distribution (2.6.3) --------------------------------------------
    full_supply_level: float = 0.0
    bottom_elevation: float | None = None
    reservoir_type: int | None = None     # None -> classify from shape factor


@dataclass
class StudyResult:
    config: StudyConfig
    bottom_elevation: float
    full_supply_level: float
    original_curve: EAVCurve
    original_capacity_fsl_Mm3: float
    # sediment
    gross_sediment_Mm3: float
    trap_efficiency: float
    deposited_unit_weight_kg_m3: float
    initial_unit_weight_kg_m3: float
    k_factor: float
    deposited_sediment_Mm3: float
    # shape / distribution
    shape_factor_m: float
    reservoir_type: int
    p_zero: float
    new_zero_elevation: float
    revised_capacity_fsl_Mm3: float
    capacity_loss_pct: float
    revised_curve: EAVCurve
    distribution: distribution.DistributionResult
    diagnostics: dict = field(default_factory=dict)


def run_study(cfg: StudyConfig) -> StudyResult:
    # ---- load EAV, convert volume to m3 --------------------------------
    raw = EAVCurve.from_xlsx(cfg.eav_path, cfg.eav_sheet,
                             cfg.elevation_col, cfg.area_col, cfg.volume_col)
    eav = EAVCurve(raw.elevation, raw.area, raw.volume * cfg.volume_unit_to_m3)
    bottom = cfg.bottom_elevation if cfg.bottom_elevation is not None else eav.elevation_min
    fsl = cfg.full_supply_level
    to_Mm3 = 1.0 / 1e6

    # ---- 2.6.1 trap efficiency & sediment supply -----------------------
    gross_m3 = (cfg.sediment_yield_m3_per_km2_yr * cfg.catchment_area_km2
                * cfg.horizon_years)
    if cfg.trap_efficiency is not None:
        te = cfg.trap_efficiency
    else:
        if cfg.mean_annual_inflow_Mm3 is None:
            raise ValueError("Brune trap efficiency needs mean_annual_inflow_Mm3")
        cap_fsl_Mm3 = eav.volume_at(fsl) * to_Mm3
        te = trap_efficiency.brune_trap_efficiency(
            cap_fsl_Mm3 / cfg.mean_annual_inflow_Mm3)
    trapped_m3 = gross_m3 * te

    # ---- 2.6.2 deposited unit weight -----------------------------------
    W1 = density.initial_unit_weight(cfg.clay, cfg.silt, cfg.sand,
                                     cfg.reservoir_operation, units="metric")
    K = density.k_factor(cfg.clay, cfg.silt, cfg.sand,
                         cfg.reservoir_operation, units="metric")
    WT = density.compacted_unit_weight(W1, K, cfg.horizon_years)

    # Optional mass<->volume rescale: if the supplied yield volume was
    # expressed at a reference unit weight, convert to the deposited unit
    # weight (deposited volume = trapped_volume * ref / WT).
    if cfg.reference_unit_weight_kg_m3 is not None:
        deposited_m3 = trapped_m3 * cfg.reference_unit_weight_kg_m3 / WT
    else:
        deposited_m3 = trapped_m3

    # ---- 2.6.3 distribution --------------------------------------------
    m = distribution.reservoir_shape_m(eav, bottom=bottom, top=fsl)
    rtype = cfg.reservoir_type if cfg.reservoir_type is not None \
        else distribution.classify_type(m)
    dist = distribution.distribute(eav, deposited_m3, reservoir_type=rtype,
                                   top=fsl, bottom=bottom)

    # ---- assemble revised full-range curve -----------------------------
    # Below FSL: use redistributed area/capacity. Above FSL: original
    # incremental storage is preserved (no sediment above normal pool).
    rev_elev = dist.elevation
    rev_area = dist.revised_area
    rev_cap = dist.revised_capacity
    above = eav.elevation > fsl
    if np.any(above):
        cap_fsl_rev = rev_cap[-1]
        cap_fsl_orig = eav.volume_at(fsl)
        extra_e = eav.elevation[above]
        extra_a = eav.area[above]
        extra_v = cap_fsl_rev + (eav.volume[above] - cap_fsl_orig)
        rev_elev = np.concatenate([rev_elev, extra_e])
        rev_area = np.concatenate([rev_area, extra_a])
        rev_cap = np.concatenate([rev_cap, extra_v])
    # revised_curve volumes are kept in m3 for internal consistency
    revised_curve = EAVCurve(rev_elev, rev_area, rev_cap)

    orig_cap_fsl_Mm3 = eav.volume_at(fsl) * to_Mm3
    rev_cap_fsl_Mm3 = float(np.interp(fsl, rev_elev, rev_cap)) * to_Mm3
    loss_pct = 100.0 * (orig_cap_fsl_Mm3 - rev_cap_fsl_Mm3) / orig_cap_fsl_Mm3

    return StudyResult(
        config=cfg,
        bottom_elevation=bottom,
        full_supply_level=fsl,
        original_curve=eav,
        original_capacity_fsl_Mm3=orig_cap_fsl_Mm3,
        gross_sediment_Mm3=gross_m3 * to_Mm3,
        trap_efficiency=te,
        deposited_unit_weight_kg_m3=WT,
        initial_unit_weight_kg_m3=W1,
        k_factor=K,
        deposited_sediment_Mm3=deposited_m3 * to_Mm3,
        shape_factor_m=m,
        reservoir_type=rtype,
        p_zero=dist.p_zero,
        new_zero_elevation=dist.new_zero_elevation,
        revised_capacity_fsl_Mm3=rev_cap_fsl_Mm3,
        capacity_loss_pct=loss_pct,
        revised_curve=revised_curve,
        distribution=dist,
        diagnostics={
            "gross_sediment_m3": gross_m3,
            "trapped_sediment_m3": trapped_m3,
            "deposited_sediment_m3": deposited_m3,
        },
    )
