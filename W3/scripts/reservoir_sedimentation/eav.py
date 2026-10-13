"""Elevation-Area-Volume (EAV) curve container and helpers.

Holds the reservoir stage relationship and provides the interpolation and
average-end-area utilities consumed by the sediment-distribution routines.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class EAVCurve:
    """A monotonic elevation-area-volume curve.

    Parameters
    ----------
    elevation : array, increasing.  Reservoir stage.
    area : array.  Water-surface area at each elevation.
    volume : array.  Cumulative storage below each elevation.

    Units are whatever the caller supplies and are carried through
    unchanged; the class performs no unit conversion.
    """

    elevation: np.ndarray
    area: np.ndarray
    volume: np.ndarray

    def __post_init__(self):
        self.elevation = np.asarray(self.elevation, dtype=float)
        self.area = np.asarray(self.area, dtype=float)
        self.volume = np.asarray(self.volume, dtype=float)
        n = len(self.elevation)
        if not (len(self.area) == n and len(self.volume) == n):
            raise ValueError("elevation, area and volume must have equal length")
        if n < 2:
            raise ValueError("need at least two points")
        if not np.all(np.diff(self.elevation) > 0):
            raise ValueError("elevation must be strictly increasing")

    # -- extent -----------------------------------------------------------
    @property
    def elevation_min(self) -> float:
        return float(self.elevation[0])

    @property
    def elevation_max(self) -> float:
        return float(self.elevation[-1])

    # -- interpolation ----------------------------------------------------
    def area_at(self, h: float) -> float:
        return float(np.interp(h, self.elevation, self.area))

    def volume_at(self, h: float) -> float:
        return float(np.interp(h, self.elevation, self.volume))

    def relative_depth(self, h: float, top: float, bottom: float | None = None) -> float:
        """Relative depth p measured from the bottom (p=0) to ``top`` (p=1)."""
        if bottom is None:
            bottom = self.elevation_min
        return (h - bottom) / (top - bottom)

    # -- construction -----------------------------------------------------
    @classmethod
    def from_xlsx(cls, path: str | Path, sheet: str,
                  elevation_col: str, area_col: str, volume_col: str) -> "EAVCurve":
        import openpyxl

        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb[sheet]
        rows = list(ws.iter_rows(values_only=True))
        header = [str(c).strip() if c is not None else "" for c in rows[0]]
        idx = {name: header.index(name) for name in (elevation_col, area_col, volume_col)}
        elev, area, vol = [], [], []
        for r in rows[1:]:
            e = r[idx[elevation_col]]
            if e is None:
                continue
            elev.append(float(e))
            area.append(float(r[idx[area_col]]))
            vol.append(float(r[idx[volume_col]]))
        order = np.argsort(elev)
        return cls(np.asarray(elev)[order], np.asarray(area)[order], np.asarray(vol)[order])

    def clipped(self, top: float) -> "EAVCurve":
        """Return the curve restricted to elevations <= ``top`` with an
        interpolated end point exactly at ``top``."""
        mask = self.elevation < top
        e = np.append(self.elevation[mask], top)
        a = np.append(self.area[mask], self.area_at(top))
        v = np.append(self.volume[mask], self.volume_at(top))
        return EAVCurve(e, a, v)
