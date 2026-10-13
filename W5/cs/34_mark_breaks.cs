// Redraw the grade-break markers on layer W5-GDP-BREAKS from the given alignments and stations: every circle and text
// on that layer is erased first, then one circle + text per break ("<name> GB<i>  k+mmm.m  z=..."). The break list is
// {{BREAKS}}: name|station|elevation entries separated by ';'. Runs inside civil3d_execute.
var spec = "{{BREAKS}}"; double textH = {{TEXT_H}}; var layer = "W5-GDP-BREAKS";
var lt = (LayerTable)Transaction.GetObject(Database.LayerTableId, OpenMode.ForRead);
if (!lt.Has(layer)) { lt.UpgradeOpen(); var rec = new LayerTableRecord { Name = layer, Color = Autodesk.AutoCAD.Colors.Color.FromColorIndex(Autodesk.AutoCAD.Colors.ColorMethod.ByAci, 2) }; lt.Add(rec); Transaction.AddNewlyCreatedDBObject(rec, true); }
var btr = (BlockTableRecord)Transaction.GetObject(SymbolUtilityServices.GetBlockModelSpaceId(Database), OpenMode.ForWrite);
int erased = 0;
foreach (ObjectId id in btr) { var e = Transaction.GetObject(id, OpenMode.ForRead); if ((e is Circle || e is DBText) && ((Autodesk.AutoCAD.DatabaseServices.Entity)e).Layer == layer) { e.UpgradeOpen(); e.Erase(); erased++; } }
var als = new Dictionary<string, Alignment>();
foreach (ObjectId aid in CivilDoc.GetAlignmentIds()) { var a = (Alignment)Transaction.GetObject(aid, OpenMode.ForRead); als[a.Name] = a; }
int made = 0; var missing = new List<string>(); var counters = new Dictionary<string, int>();
foreach (var item in spec.Split(';'))
{
    if (string.IsNullOrWhiteSpace(item)) continue;
    var f = item.Split('|'); var name = f[0]; double sta = double.Parse(f[1], System.Globalization.CultureInfo.InvariantCulture); double elev = double.Parse(f[2], System.Globalization.CultureInfo.InvariantCulture);
    if (!als.ContainsKey(name)) { missing.Add(name); continue; }
    int i = counters.GetValueOrDefault(name); counters[name] = i + 1;
    double x = 0, y = 0; als[name].PointLocation(sta, 0.0, ref x, ref y);
    var c = new Circle(new Point3d(x, y, 0.0), Vector3d.ZAxis, 1.2 * textH); c.SetDatabaseDefaults(); c.Layer = layer; btr.AppendEntity(c); Transaction.AddNewlyCreatedDBObject(c, true);
    var t = new DBText { Position = new Point3d(x + 1.5 * textH, y + 0.5 * textH, 0.0), Height = textH, TextString = name + " GB" + i + "  " + sta.ToString("0+000.0") + "  z=" + elev.ToString("0.00") }; t.SetDatabaseDefaults(); t.Layer = layer; btr.AppendEntity(t); Transaction.AddNewlyCreatedDBObject(t, true);
    made++;
}
return new { erased, made, missing };
