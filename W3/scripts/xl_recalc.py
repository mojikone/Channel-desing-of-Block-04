"""Recalculate a workbook in real Excel (COM), save it, and optionally export every chart as PNG.
usage: python xl_recalc.py <workbook.xlsx> [--png <folder>]
Excel computes every formula (openpyxl writes none of the cached values), so pandas / Word / previewers see numbers.
"""
import sys, os, time
import pythoncom, win32com.client as win32

def recalc(path, png_dir=None, hide_after=None):
    """hide_after=N: in every chart with more than N series, delete the legend entries beyond the N-th (helper series
    such as peak labels stay plotted but leave the legend) - openpyxl's legendEntry/delete is not honoured by Excel."""
    path = os.path.abspath(path); pythoncom.CoInitialize()
    # Chart.Export needs a rendered chart: Excel must be visible (kept minimised) and the sheet/chart activated,
    # otherwise it fails with "The specified dimension is not valid for the current chart type".
    xl = win32.DispatchEx("Excel.Application"); xl.Visible = bool(png_dir); xl.DisplayAlerts = False; xl.ScreenUpdating = True
    try:
        wb = xl.Workbooks.Open(path, UpdateLinks=0, ReadOnly=False)
        xl.CalculateFullRebuild(); time.sleep(0.5)
        n_charts = 0; failed = []; n_hidden = 0
        if hide_after:
            for ws in wb.Worksheets:
                for i in range(1, ws.ChartObjects().Count + 1):
                    ch = ws.ChartObjects(i).Chart; n = ch.SeriesCollection().Count
                    if n > hide_after and ch.HasLegend:
                        for j in range(ch.Legend.LegendEntries().Count, hide_after, -1):
                            try: ch.Legend.LegendEntries(j).Delete(); n_hidden += 1
                            except Exception: pass
            print("legend entries hidden:", n_hidden)
        for ws in wb.Worksheets:
            if png_dir:
                os.makedirs(png_dir, exist_ok=True); ws.Activate()
                for i in range(1, ws.ChartObjects().Count + 1):
                    co = ws.ChartObjects(i); name = f"{ws.Name}_{i:02d}".replace(" ", "_").replace("/", "-")
                    try:
                        co.Activate(); xl.ActiveWindow.ScrollRow = max(1, co.TopLeftCell.Row - 1); xl.ActiveWindow.ScrollColumn = max(1, co.TopLeftCell.Column - 1)
                        time.sleep(0.15); co.Chart.Export(os.path.join(png_dir, name + ".png"), "PNG"); n_charts += 1
                    except Exception as e:
                        failed.append((name, str(e)[:80]))
        if failed: print("chart export failed:", len(failed), failed[:3])
        wb.Save(); wb.Close(SaveChanges=False)
    finally:
        xl.Quit(); pythoncom.CoUninitialize()
    # formula errors as cached by Excel (read back with openpyxl)
    import openpyxl
    errs = []
    wb2 = openpyxl.load_workbook(path, data_only=True)
    for ws in wb2.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("#") and c.value[1:4].isupper(): errs.append(f"{ws.title}!{c.coordinate}={c.value}")
    return dict(errors=errs, charts_exported=n_charts)

if __name__ == "__main__":
    p = sys.argv[1]; png = sys.argv[sys.argv.index("--png") + 1] if "--png" in sys.argv else None
    hide = int(sys.argv[sys.argv.index("--hide-legend-after") + 1]) if "--hide-legend-after" in sys.argv else None
    r = recalc(p, png, hide); print("recalculated", os.path.basename(p), "| formula errors:", len(r["errors"]), r["errors"][:10], "| charts exported:", r["charts_exported"])
