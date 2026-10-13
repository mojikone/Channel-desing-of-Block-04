"""Appendices: A inflow hydrographs of the dams, B reservoir curves after sedimentation."""
from common import h_app, D, N, A, chart, fig, lab, SEDF
import os

def appendices(d):
    h_app(d, "Appendix A – Inflow hydrographs of the dams")
    D.p(d, "Inflow hydrographs of the thirteen depth-area analyses at each dam, with the peak flow and the volume of every event.")
    for dam in A.DAMS: chart(d, f"C02_inflows_{dam.replace(' ', '_')}", f"{lab(dam)}: inflow hydrographs for the return periods of 2 to 10 000 years and the PMP.", 16)
    h_app(d, "Appendix B – Reservoir curves after sedimentation")
    D.p(d, "Original and revised elevation-area-volume curves of each reservoir after 50 and 100 years of sedimentation (Section 6): capacity on the lower axis, water-surface area on the upper axis.")
    for dam in A.DAMS: fig(d, os.path.join(SEDF, f"eav_revised_{dam.replace(' ', '_')}.png"), f"{lab(dam)}: reservoir curves before and after sedimentation.", 16)
