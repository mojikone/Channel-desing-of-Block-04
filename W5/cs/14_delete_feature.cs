// Delete one feature's alignment-dependent objects so that it can be rebuilt: its profile views, profiles, the
// alignment itself and the leader(s) naming its view. The corridor surface is kept. Runs inside civil3d_execute.
var name = "{{NAME}}"; var viewName = "PV " + name; var log = new List<string>();
ObjectId aid = ObjectId.Null;
foreach (ObjectId id in CivilDoc.GetAlignmentIds()) { var a = (Alignment)Transaction.GetObject(id, OpenMode.ForRead); if (a.Name == name) aid = id; }
if (!aid.IsNull)
{
    var al = (Alignment)Transaction.GetObject(aid, OpenMode.ForRead);
    var views = new List<ObjectId>(); foreach (ObjectId v in al.GetProfileViewIds()) views.Add(v);
    var profs = new List<ObjectId>(); foreach (ObjectId p in al.GetProfileIds()) profs.Add(p);
    foreach (var v in views) { var pv = (ProfileView)Transaction.GetObject(v, OpenMode.ForWrite); log.Add("erased view " + pv.Name); pv.Erase(); }
    foreach (var p in profs) { var pr = (Profile)Transaction.GetObject(p, OpenMode.ForWrite); log.Add("erased profile " + pr.Name); pr.Erase(); }
    al.UpgradeOpen(); al.Erase(); log.Add("erased alignment " + name);
}
else log.Add("alignment not found: " + name);
var btr = (BlockTableRecord)Transaction.GetObject(SymbolUtilityServices.GetBlockModelSpaceId(Database), OpenMode.ForRead);
int nl = 0;
foreach (ObjectId id in btr)
{
    if (Transaction.GetObject(id, OpenMode.ForRead) is MLeader m && m.Layer.StartsWith("W5-PV-LEADER") && m.ContentType == ContentType.MTextContent && m.MText != null && m.MText.Contents.Contains(viewName))
    { m.UpgradeOpen(); m.Erase(); nl++; }
}
log.Add("erased " + nl + " leader(s) of " + viewName);
return new { name, log };
