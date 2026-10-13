"""Export every native chart of a workbook to PNG through Excel's clipboard (Chart.Export fails in automation here).
usage: python xl_charts_png.py <workbook.xlsx> <png folder> [sheet-name substring filter] [max charts per sheet]
Fallback per chart: the chart's cell range is printed to a one-page PDF (ExportAsFixedFormat).
"""
import sys, os, time
import pythoncom, win32com.client as win32
from PIL import ImageGrab

def export(path, out, flt=None, maxn=99):
    path = os.path.abspath(path); os.makedirs(out, exist_ok=True); pythoncom.CoInitialize()
    xl = win32.DispatchEx("Excel.Application"); xl.Visible = True; xl.DisplayAlerts = False
    n_ok = n_pdf = 0
    try:
        wb = xl.Workbooks.Open(path, ReadOnly=True)
        for ws in wb.Worksheets:
            if flt and flt.lower() not in ws.Name.lower(): continue
            if ws.ChartObjects().Count == 0: continue
            ws.Activate()
            for i in range(1, min(ws.ChartObjects().Count, maxn) + 1):
                co = ws.ChartObjects(i); name = f"{ws.Name}_{i:02d}".replace(" ", "_")
                xl.ActiveWindow.ScrollRow = max(1, co.TopLeftCell.Row); xl.ActiveWindow.ScrollColumn = max(1, co.TopLeftCell.Column); time.sleep(0.2)
                img = None
                for attempt in range(3):
                    try:
                        co.Select(); co.CopyPicture(1, 2); time.sleep(0.4); img = ImageGrab.grabclipboard()
                        if img is None: co.Chart.CopyPicture(1, 2); time.sleep(0.4); img = ImageGrab.grabclipboard()
                        if img is not None and hasattr(img, "save"): break
                        img = None
                    except Exception:
                        time.sleep(0.5)
                if img is not None:
                    img.save(os.path.join(out, name + ".png")); n_ok += 1
                else:   # print the chart's cell range to a one-page PDF and rasterise it
                    rng = ws.Range(co.TopLeftCell, co.BottomRightCell); ws.PageSetup.PrintArea = rng.Address
                    ws.PageSetup.Zoom = False; ws.PageSetup.FitToPagesWide = 1; ws.PageSetup.FitToPagesTall = 1; ws.PageSetup.Orientation = 2
                    pdf = os.path.join(os.path.abspath(out), name + ".pdf"); ws.ExportAsFixedFormat(0, pdf); n_pdf += 1
                    try:
                        import fitz
                        d = fitz.open(pdf); d[0].get_pixmap(dpi=130).save(os.path.join(out, name + ".png")); d.close(); os.remove(pdf)
                    except Exception as e:
                        print("pdf->png failed", name, str(e)[:60])
        wb.Close(SaveChanges=False)
    finally:
        xl.Quit(); pythoncom.CoUninitialize()
    return n_ok, n_pdf

if __name__ == "__main__":
    flt = sys.argv[3] if len(sys.argv) > 3 else None; maxn = int(sys.argv[4]) if len(sys.argv) > 4 else 99
    ok, pdf = export(sys.argv[1], sys.argv[2], flt, maxn); print("charts as PNG:", ok, "| as PDF fallback:", pdf, "->", sys.argv[2])
