// Design-point markers in the profile views and in plan. Input {{MARKERS}}: entries "alignment|station|elevation|kind|label"
// separated by ';' (label text must not contain ';' or '|'). Kinds and layers (colours as in QGIS, nested radii so that
// overlapping points stay visible): flow -> W6-PT-FLOW (blue 5, r 24), junction -> W6-PT-JUNCTION (red 1, r 17),
// fix -> W6-PT-FIX (yellow 2, r 12), fix500 -> W6-PT-FIX500 (orange 30, r 8), sglabel -> W6-PT-SGLABEL (white 7, r 4, the
// text BELOW the point: the SewerGEMS point names of 37/38). The layers of the kinds listed in {{ERASE_KINDS}} (comma separated)
// are cleared first, the others are left alone. In each profile view of the alignment the marker sits at (station, elevation) through FindXYAtStationAndElevation;
// in plan at the alignment's point for the station. Runs inside civil3d_execute.
var spec = "{{MARKERS}}"; double textH = {{TEXT_H}};
var layers = new Dictionary<string, (string layer, short color, double r, bool below)> { ["flow"] = ("W6-PT-FLOW", 5, 24, false), ["junction"] = ("W6-PT-JUNCTION", 1, 17, false), ["fix"] = ("W6-PT-FIX", 2, 12, false), ["fix500"] = ("W6-PT-FIX500", 30, 8, false), ["sglabel"] = ("W6-PT-SGLABEL", 7, 4, true) };
var eraseKinds = "{{ERASE_KINDS}}".Split(',').Select(k => k.Trim()).Where(k => layers.ContainsKey(k)).ToList();
var lt = (LayerTable)Transaction.GetObject(Database.LayerTableId, OpenMode.ForRead);
foreach (var kv in layers.Values) { if (!lt.Has(kv.layer)) { lt.UpgradeOpen(); var rec = new LayerTableRecord { Name = kv.layer, Color = Autodesk.AutoCAD.Colors.Color.FromColorIndex(Autodesk.AutoCAD.Colors.ColorMethod.ByAci, kv.color) }; lt.Add(rec); Transaction.AddNewlyCreatedDBObject(rec, true); } }
var btr = (BlockTableRecord)Transaction.GetObject(SymbolUtilityServices.GetBlockModelSpaceId(Database), OpenMode.ForWrite);
int erased = 0; var mine = new HashSet<string>(eraseKinds.Select(k => layers[k].layer));
foreach (ObjectId id in btr) { var e = Transaction.GetObject(id, OpenMode.ForRead) as Autodesk.AutoCAD.DatabaseServices.Entity; if (e != null && (e is Circle || e is DBText) && mine.Contains(e.Layer)) { e.UpgradeOpen(); e.Erase(); erased++; } }
var als = new Dictionary<string, Alignment>();
foreach (ObjectId aid in CivilDoc.GetAlignmentIds()) { var a = (Alignment)Transaction.GetObject(aid, OpenMode.ForRead); als[a.Name] = a; }
int made = 0, inViews = 0; var problems = new List<string>();
void Put(Point3d p, string layer, double r, string text, double th, bool below)
{
    var c = new Circle(p, Vector3d.ZAxis, r); c.SetDatabaseDefaults(); c.Layer = layer; btr.AppendEntity(c); Transaction.AddNewlyCreatedDBObject(c, true);
    var t = new DBText { Position = below ? new Point3d(p.X + 0.3 * th, p.Y - r - 1.3 * th, 0.0) : new Point3d(p.X + r + 0.3 * th, p.Y + 0.3 * th, 0.0), Height = th, TextString = text }; t.SetDatabaseDefaults(); t.Layer = layer; btr.AppendEntity(t); Transaction.AddNewlyCreatedDBObject(t, true);
}
foreach (var item in spec.Split(';'))
{
    if (string.IsNullOrWhiteSpace(item)) continue;
    var f = item.Split('|'); var name = f[0]; double sta = double.Parse(f[1], System.Globalization.CultureInfo.InvariantCulture); double elev = double.Parse(f[2], System.Globalization.CultureInfo.InvariantCulture); var kind = f[3]; var label = f.Length > 4 ? f[4] : "";
    if (!als.ContainsKey(name) || !layers.ContainsKey(kind)) { problems.Add(item); continue; }
    var L = layers[kind]; var al = als[name];
    foreach (ObjectId vid in al.GetProfileViewIds())
    {
        var pv = (ProfileView)Transaction.GetObject(vid, OpenMode.ForRead); double x = 0, y = 0;
        double s = Math.Max(pv.StationStart, Math.Min(sta, pv.StationEnd)); double e = Math.Max(pv.ElevationMin, Math.Min(elev, pv.ElevationMax));
        try { pv.FindXYAtStationAndElevation(s, e, ref x, ref y); Put(new Point3d(x, y, 0.0), L.layer, L.r, label, textH, L.below); inViews++; } catch (System.Exception ex) { problems.Add(item + " view: " + ex.Message); }
    }
    double px = 0, py = 0; try { al.PointLocation(Math.Max(al.StartingStation, Math.Min(sta, al.EndingStation)), 0.0, ref px, ref py); Put(new Point3d(px, py, 0.0), L.layer, L.r * 0.5, label, textH * 0.6, L.below); } catch (System.Exception ex) { problems.Add(item + " plan: " + ex.Message); }
    made++;
}
return new { erased, markers = made, placedInViews = inViews, problems };
