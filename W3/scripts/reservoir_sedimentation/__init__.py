"""Reservoir sedimentation engine.

Implements the USBR *Erosion and Sedimentation Manual*, Chapter 2,
Section 2.6 (Reservoir Sedimentation):

    2.6.1  Reservoir Sediment Trap Efficiency   -> trap_efficiency.py
    2.6.2  Density of Deposited Sediment         -> density.py
    2.6.3  Sediment Distribution Within a Reservoir (Empirical
           Area-Reduction Method, Borland & Miller 1960 / Lara 1962)
                                                 -> distribution.py

The engine is validated against the manual's own worked examples
(density example on p.2-64; Theodore Roosevelt Lake distribution study,
Tables 2.37 and 2.38; and the analytic F-value table, Figure 2.28).
"""

__all__ = ["density", "trap_efficiency", "distribution", "eav", "pipeline"]
