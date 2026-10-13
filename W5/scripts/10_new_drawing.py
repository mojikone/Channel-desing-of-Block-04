import os, time, win32com.client
TPL = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Hydrology\DWG\C3D template\C3D Template.dwt"
W4 = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Claude Block 04\W4\civil3d"
W5 = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Claude Block 04\W5\civil3d"
NEW = os.path.join(W5, "Block04_Channels_W5.dwg")
app = win32com.client.GetActiveObject("AutoCAD.Application")
print("quiescent:", app.GetAcadState().IsQuiescent)
# 1. new drawing from the project template, saved under the W5 name (becomes the active document)
d = app.Documents.Add(TPL); time.sleep(2); print("new document:", d.Name)
d.SaveAs(NEW); time.sleep(2); print("saved as:", app.ActiveDocument.Name, "|", app.ActiveDocument.Path)
# 2. the W4 drawings: save the template-based one as the W4 record (it was never saved after the build), close both
for name in ("Block04_Channels_Surfaces_C3Dtemplate.dwg", "Block04_Channels_Surfaces.dwg"):
    for x in app.Documents:
        if x.Name == name and x.Path.lower() == W4.lower():
            if not x.Saved: t = time.time(); x.Save(); print("saved", name, "%.0f s" % (time.time() - t))
            x.Close(False); time.sleep(1); print("closed", name)
print("open now:", [x.Name for x in app.Documents], "| active:", app.ActiveDocument.Name)
