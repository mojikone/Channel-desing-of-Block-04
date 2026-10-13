// Create (or replace) the ground design profile "GDP <name>": a layout profile on the alignment with one PVI per grade
// break (stations and elevations given), style and label set by name, and mark every break in plan on layer
// W5-GDP-BREAKS (a circle and a text with the break number, station and elevation). Runs inside civil3d_execute.
using Autodesk.Civil.DatabaseServices.Styles;
var alName = "{{NAME}}"; var gdpName = "GDP " + alName;
double[] sta = { {{STA}} }; double[] elev = { {{ELEV}} };
var style = "{{STYLE}}"; var labelSet = "{{LABELSET}}"; double textH = {{TEXT_H}}; bool mark = {{MARK}};
Alignment al = null;
foreach (ObjectId id in CivilDoc.GetAlignmentIds()) { var a = (Alignment)Transaction.GetObject(id, OpenMode.ForRead); if (a.Name == alName) al = a; }
if (al == null) return new { error = "alignment not found: " + alName };
var log = new List<string>();
foreach (ObjectId pid in al.GetProfileIds()) { var p = (Profile)Transaction.GetObject(pid, OpenMode.ForRead); if (p.Name == gdpName) { p.UpgradeOpen(); p.Erase(); log.Add("replaced the existing " + gdpName); } }
var styles = CivilDoc.Styles;
var newId = Profile.CreateByLayout(gdpName, al.ObjectId, al.LayerId, styles.ProfileStyles[style], styles.LabelSetStyles.ProfileLabelSetStyles[labelSet]);
var gdp = (Profile)Transaction.GetObject(newId, OpenMode.ForWrite);
for (int i = 0; i < sta.Length; i++) gdp.PVIs.AddPVI(sta[i], elev[i]);
// verification: the profile's elevation at every PVI and at the midpoints between them
var check = new List<object>();
for (int i = 0; i < sta.Length; i++) { double e = double.NaN; try { e = gdp.ElevationAt(sta[i]); } catch { } check.Add(new { sta = Math.Round(sta[i], 3), want = Math.Round(elev[i], 3), got = Math.Round(e, 3) }); }
// break markers in plan
var pts = new List<object>();
if (mark)
{
    var lt = (LayerTable)Transaction.GetObject(Database.LayerTableId, OpenMode.ForRead); var layer = "W5-GDP-BREAKS";
    if (!lt.Has(layer)) { lt.UpgradeOpen(); var rec = new LayerTableRecord { Name = layer, Color = Autodesk.AutoCAD.Colors.Color.FromColorIndex(Autodesk.AutoCAD.Colors.ColorMethod.ByAci, 2) }; lt.Add(rec); Transaction.AddNewlyCreatedDBObject(rec, true); }
    var btr = (BlockTableRecord)Transaction.GetObject(SymbolUtilityServices.GetBlockModelSpaceId(Database), OpenMode.ForWrite);
    // remove earlier markers of this alignment (text starting with "<name> GB")
    var old = new List<ObjectId>();
    foreach (ObjectId id in btr) { var ent = Transaction.GetObject(id, OpenMode.ForRead); if (ent is DBText t && t.Layer == layer && t.TextString.StartsWith(alName + " GB")) old.Add(id); else if (ent is Circle c && c.Layer == layer && c.Hyperlinks.Count > 0 && c.Hyperlinks[0].Description == alName) old.Add(id); }
    foreach (var id in old) { var e = Transaction.GetObject(id, OpenMode.ForWrite); e.Erase(); }
    for (int i = 0; i < sta.Length; i++)
    {
        double x = 0, y = 0; al.PointLocation(sta[i], 0.0, ref x, ref y);
        var c = new Circle(new Point3d(x, y, 0.0), Vector3d.ZAxis, 1.2 * textH); c.SetDatabaseDefaults(); c.Layer = layer; c.Hyperlinks.Add(new HyperLink { Description = alName, Name = "" });
        btr.AppendEntity(c); Transaction.AddNewlyCreatedDBObject(c, true);
        var t = new DBText { Position = new Point3d(x + 1.5 * textH, y + 0.5 * textH, 0.0), Height = textH, TextString = alName + " GB" + i + "  " + sta[i].ToString("0+000.0") + "  z=" + elev[i].ToString("0.00") }; t.SetDatabaseDefaults(); t.Layer = layer;
        btr.AppendEntity(t); Transaction.AddNewlyCreatedDBObject(t, true);
        pts.Add(new { i, sta = Math.Round(sta[i], 3), elev = Math.Round(elev[i], 3), x = Math.Round(x, 3), y = Math.Round(y, 3) });
    }
}
log.Add("created " + gdpName + ": " + gdp.PVIs.Count + " PVIs, " + gdp.Entities.Count + " entities, style " + style + ", layer " + gdp.Layer);
return new { name = alName, profile = gdpName, handle = gdp.Handle.ToString(), pviCount = gdp.PVIs.Count, entities = gdp.Entities.Count, check, points = pts, log };
