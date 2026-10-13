"""Build the Block 04 report on the Block 6 report template, in the Block 6 order (revision R2: the engineer's comments on R1 of 2026-10-06, maps, EAV charts, climate charts).

    python build.py            -> R<n>/Block04_Report_R<n>.docx
    python build.py --pdf      also render to PDF through Word (fields updated: contents, lists)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import doc as D  # noqa: E402
import notes as N  # noqa: E402

REV = "R3"; OUT_DIR = os.path.join(HERE, REV); OUT = os.path.join(OUT_DIR, f"Block04_Report_{REV}.docx")

def build_once():
    d = D.new_document({}, template=os.path.join(HERE, "template", "Block04_template.docx"))
    N.reset(); N.ensure_style(d)
    import rpt_front, rpt_hydrology, rpt_channels, rpt_dams, rpt_sediment, rpt_climate, rpt_app
    D.front_matter(d); rpt_front.contents(d); rpt_front.executive_summary(d)
    D.body_start(d)
    rpt_front.introduction(d)        # 1
    rpt_hydrology.section(d)         # 2
    rpt_channels.alignments(d)       # 3
    rpt_channels.conditions(d)       # 4
    rpt_dams.section(d)              # 5
    rpt_sediment.section(d)          # 6
    rpt_climate.section(d)           # 7
    rpt_channels.hydraulic(d)        # 8
    rpt_dams.outfalls(d)             # 9
    rpt_front.conclusions(d)         # 10
    rpt_app.appendices(d)
    D.number_pages(d)
    return d

def main(render_pdf=False):
    os.makedirs(OUT_DIR, exist_ok=True)
    import common
    for k in range(3):
        d = build_once()
        if common.refs_stable(): break
        print(f"   cross-reference numbers moved, pass {k + 2}")
    out = OUT
    try: N.save(d, out)
    except PermissionError:
        out = OUT.replace(".docx", "_new.docx"); N.save(d, out); print("NOTE: the target file is open in Word; wrote a copy instead.")
    print("wrote", out)
    if render_pdf:
        import to_pdf; pdf, n = to_pdf.convert(out); print("pdf:", pdf, n, "pages")
        # the clean-room gate (global rule 14): nothing internal reaches the client, and the scan proves it
        import check_clean
        hits = check_clean.scan(pdf, os.path.join(HERE, "forbidden_terms.txt"), os.path.join(HERE, "allowed_terms.txt"))
        if hits:
            for where, hit, ctx, _ in hits: print(f"   {where:>6}  [{hit}]  ...{ctx}...".encode("ascii", "replace").decode())
            bad_docx = out.replace(".docx", "_FAILED-CLEAN-CHECK.docx"); bad_pdf = pdf.replace(".pdf", "_FAILED-CLEAN-CHECK.pdf")
            os.replace(out, bad_docx); os.replace(pdf, bad_pdf); print(f"clean-room gate FAILED: {len(hits)} hit(s); outputs renamed *_FAILED-CLEAN-CHECK"); sys.exit(1)
        print("clean-room gate PASSED (forbidden_terms.txt + built-in list, allowed_terms.txt)")
    return out

if __name__ == "__main__":
    main("--pdf" in sys.argv)
