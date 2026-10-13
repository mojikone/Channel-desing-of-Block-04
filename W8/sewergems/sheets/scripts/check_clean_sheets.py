"""Clean-room gate for the sheets themselves. The sheet PDFs carry no text layer (the vector export draws the text as outlines),
so the PDF scan of the set only sees the cover, the table and the dividers. The rendered text of the sheets is therefore scanned
at its source: the TEXT, MTEXT and block-attribute strings and the layout names of the latest DXF of every sheet and key map,
with the same scanner and the same term lists as the set PDF (W3/report/check_clean.py; sheets/forbidden_terms.txt and
allowed_terms.txt). Any hit fails; the set is not issued until both scans pass.
    python check_clean_sheets.py [--quiet]"""
import os, sys, ezdxf
HERE = os.path.dirname(os.path.abspath(__file__)); SHEETS = os.path.dirname(HERE)
B4 = os.path.dirname(os.path.dirname(os.path.dirname(SHEETS)))                      # ...\Claude Block 04
sys.path.insert(0, os.path.join(B4, "W3", "report")); sys.path.insert(0, HERE)
import check_clean as cc
from export_pdf import _latest_dxfs, DXF_DIR
TERMS = os.path.join(SHEETS, "forbidden_terms.txt"); ALLOW = os.path.join(SHEETS, "allowed_terms.txt")


def dxf_text(path):
    doc = ezdxf.readfile(path); parts = []
    for lay in doc.layouts:
        parts.append("layout name: " + lay.name)
        for e in lay:
            if e.dxftype() == "TEXT": parts.append(e.dxf.text)
            elif e.dxftype() == "MTEXT": parts.append(e.plain_text())
            elif e.dxftype() == "INSERT": parts.extend(a.dxf.text for a in e.attribs)
    return "\n".join(p for p in parts if p)


files = sorted(_latest_dxfs(DXF_DIR))
cc.text_of = lambda p: [(os.path.basename(f), dxf_text(f)) for f in files]       # the scanner reads the DXF text instead of a PDF
hits = cc.scan("sheets", TERMS, ALLOW)
if "--quiet" not in sys.argv:
    for where, hit, ctx, t in hits: print("  %s  [%s]  ...%s..." % (where, hit, ctx))
print("clean-room gate (sheet DXF text, %d drawings): %s" % (len(files), "PASSED" if not hits else "FAILED, %d hit(s)" % len(hits)))
sys.exit(1 if hits else 0)
