// Shift every W5 leader's text and landing down by {{DY}} m so that the text clears the profile view's band row.
// Runs inside civil3d_execute.
var btr = (BlockTableRecord)Transaction.GetObject(SymbolUtilityServices.GetBlockModelSpaceId(Database), OpenMode.ForRead);
double dy = {{DY}}; int n = 0; var log = new List<string>();
foreach (ObjectId id in btr)
{
    if (!(Transaction.GetObject(id, OpenMode.ForRead) is MLeader m) || !m.Layer.StartsWith("W5-PV-LEADER")) continue;
    m.UpgradeOpen();
    var t = m.TextLocation; m.TextLocation = new Point3d(t.X, t.Y - dy, 0.0);
    for (int i = 0; i < m.LeaderLineCount; i++) { var e = m.GetLastVertex(i); m.SetLastVertex(i, new Point3d(e.X, e.Y - dy, 0.0)); }
    n++;
}
return new { shifted = n, dy };
