"""Build the stormwater channels report of Block 04 (W8, R0): the structure of the Block 6 "Hydraulic Design of Stormwater Channels"
report, the stormwater main and secondary channels and dykes only (REPORT_ONLY=SM,SS in data_facts), the maps with the flood
protection channels dimmed (W8/maps/png_sw), the charts and dashboard with the _sw suffix, its own template (make_template.py --sw)
and its own cross-reference store.
    python build_sw.py          build the .docx into SW_R0/
    python build_sw.py --pdf    also render to PDF through Word and run the clean-room gate
Before the first build: scripts/66_maps_qgis_r5.py with MAPS_DIM_FP=1 MAPS_OUT=png_sw, scripts/75_sw_charts.py,
scripts/74_cost_dashboard.py with REPORT_ONLY=SM,SS DASH_SUFFIX=_sw, make_template.py --sw."""
import os, sys
os.environ.update({"REPORT_ONLY": "SM,SS", "MAPS_OUT": "png_sw_r1", "REFS_FILE": "_refs_sw.json", "REPORT_TITLE": "Hydraulic Design of Stormwater Channels",
                   "DASH_SUFFIX": "_sw", "CHART_SUFFIX": "_sw", "APP_LETTERS": "A,B,C"})
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import doc as D  # noqa: E402
import notes as N  # noqa: E402

REV = "R1"; OUT_DIR = os.path.join(HERE, "SW_" + REV); OUT = os.path.join(OUT_DIR, f"Block04_Stormwater_Channels_{REV}.docx")

def build_once():
    d = D.new_document({}, template=os.path.join(HERE, "template", "Block04_template_sw.docx"))
    N.reset(); N.ensure_style(d)
    import rpt_front, rpt_hydrology, rpt_channels, rpt_r4, rpt_sw
    D.front_matter(d); rpt_front.document_control(d); rpt_front.contents(d); rpt_front.abbreviations(d); rpt_sw.executive_summary(d)
    D.body_start(d)
    rpt_sw.introduction(d)           # 1
    rpt_hydrology.section(d)         # 2 hydrology
    rpt_sw.alignments(d)             # 3
    rpt_channels.conditions(d)       # 4
    rpt_sw.rainfall_runoff(d)        # 5
    rpt_channels.hydraulic(d)        # 6 criteria, issues, depth, sections
    rpt_sw.outfalls(d)               # 7
    rpt_r4.culverts(d)               # 8
    rpt_r4.dykes(d)                  # 9
    rpt_r4.costs(d)                  # 10
    rpt_sw.conclusions(d)            # 11
    rpt_r4.appendix_reaches(d); rpt_r4.appendix_drawings(d); rpt_r4.dashboard(d)
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
