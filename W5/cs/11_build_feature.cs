// Build one channel or dyke in the active drawing: corridor TIN surface (from the W4 point file + corridor boundary),
// alignment (fixed lines through the centreline vertices), existing-ground profile, profile view and a multileader
// from the view to the alignment start. Styles, band set and label sets are given by NAME (from the template) so the
// template is applied explicitly; object layers come from the drawing's object layer settings (the template's).
// Placeholders are filled by scripts/20_prototype.py. Runs inside civil3d_execute (transaction committed by the host).
using Autodesk.Civil.DatabaseServices.Styles;
using Autodesk.Civil.Settings;
var name = "{{NAME}}"; var kind = "{{KIND}}";
var csv = @"{{CSV}}";
double[] bx = { {{BX}} }; double[] by = { {{BY}} };
double[] ax = { {{AX}} }; double[] ay = { {{AY}} };
var insert = new Point3d({{INSERT_X}}, {{INSERT_Y}}, 0.0);
var surfaceStyle = "{{SURFACE_STYLE}}"; var alignStyle = "{{ALIGN_STYLE}}"; var alignLabelSet = "{{ALIGN_LABELSET}}";
var profileStyle = "{{PROFILE_STYLE}}"; var profileLabelSet = "{{PROFILE_LABELSET}}";
var pvStyle = "{{PV_STYLE}}"; var bandSet = "{{BANDSET}}";
var leaderLayer = "{{LEADER_LAYER}}"; short leaderColor = {{LEADER_COLOR}}; double leaderTextH = {{LEADER_TEXT_H}};
var surfName = "EG " + name; var profName = "EG " + name; var viewName = "PV " + name;
var log = new List<string>();
var styles = CivilDoc.Styles;
ObjectId StyleId(string coll, StyleCollectionBase c, string n) { try { var id = c[n]; if (id.IsNull) throw new System.Exception("null"); return id; } catch { throw new System.Exception(coll + " style '" + n + "' not found"); } }
string ObjLayer(SettingsObjectLayerType t, string objName)
{
    var ol = CivilDoc.Settings.DrawingSettings.ObjectLayerSettings.GetObjectLayerSetting(t); var l = ol.LayerName;
    if (ol.Modifier == ObjectLayerModifierType.Prefix) l = ol.ModifierValue.Replace("*", objName) + l;
    else if (ol.Modifier == ObjectLayerModifierType.Suffix) l = l + ol.ModifierValue.Replace("*", objName);
    if (string.IsNullOrWhiteSpace(l)) l = "0";
    var lt = (LayerTable)Transaction.GetObject(Database.LayerTableId, OpenMode.ForRead);
    if (!lt.Has(l)) { lt.UpgradeOpen(); var rec = new LayerTableRecord { Name = l }; lt.Add(rec); Transaction.AddNewlyCreatedDBObject(rec, true); }
    return l;
}
ObjectId EnsureLayer(string l, short color)
{
    var lt = (LayerTable)Transaction.GetObject(Database.LayerTableId, OpenMode.ForRead);
    if (lt.Has(l)) return lt[l];
    lt.UpgradeOpen(); var rec = new LayerTableRecord { Name = l, Color = Autodesk.AutoCAD.Colors.Color.FromColorIndex(Autodesk.AutoCAD.Colors.ColorMethod.ByAci, color) }; var id = lt.Add(rec); Transaction.AddNewlyCreatedDBObject(rec, true); return id;
}
// ---- surface
ObjectId sid = ObjectId.Null;
foreach (ObjectId id in CivilDoc.GetSurfaceIds()) { var s = (Autodesk.Civil.DatabaseServices.Surface)Transaction.GetObject(id, OpenMode.ForRead); if (s.Name == surfName) sid = id; }
if (sid.IsNull)
{
    var pts = new Point3dCollection(); int n = 0;
    foreach (var line in System.IO.File.ReadLines(csv))
    {
        var f = line.Split(','); if (f.Length < 4) continue;
        if (!double.TryParse(f[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var x)) continue;
        var y = double.Parse(f[2], System.Globalization.CultureInfo.InvariantCulture); var z = double.Parse(f[3], System.Globalization.CultureInfo.InvariantCulture);
        pts.Add(new Point3d(x, y, z)); n++;
    }
    sid = TinSurface.Create(Database, surfName);
    var tin = (TinSurface)Transaction.GetObject(sid, OpenMode.ForWrite);
    tin.AddVertices(pts);
    var ring = new Point3dCollection(); for (int i = 0; i < bx.Length; i++) ring.Add(new Point3d(bx[i], by[i], 0.0));
    tin.BoundariesDefinition.AddBoundaries(ring, 0.5, SurfaceBoundaryType.Outer, false);
    tin.StyleId = StyleId("surface", styles.SurfaceStyles, surfaceStyle);
    tin.Layer = ObjLayer(SettingsObjectLayerType.TinSurface, name);
    log.Add("surface " + surfName + ": " + n + " points, boundary " + bx.Length + " vertices, style " + surfaceStyle + ", layer " + tin.Layer);
}
else log.Add("surface exists");
// ---- alignment
ObjectId aid = ObjectId.Null;
foreach (ObjectId id in CivilDoc.GetAlignmentIds()) { var a = (Alignment)Transaction.GetObject(id, OpenMode.ForRead); if (a.Name == name) aid = id; }
if (aid.IsNull)
{
    var alayer = ObjLayer(SettingsObjectLayerType.Alignment, name);
    StyleId("alignment", styles.AlignmentStyles, alignStyle); StyleId("alignment label set", styles.LabelSetStyles.AlignmentLabelSetStyles, alignLabelSet);
    aid = Alignment.Create(CivilDoc, name, null, alayer, alignStyle, alignLabelSet);
    var al = (Alignment)Transaction.GetObject(aid, OpenMode.ForWrite);
    int seg = 0;
    for (int i = 1; i < ax.Length; i++) { var p = new Point3d(ax[i - 1], ay[i - 1], 0.0); var q = new Point3d(ax[i], ay[i], 0.0); if (p.DistanceTo(q) < 0.001) continue; al.Entities.AddFixedLine(p, q); seg++; }
    log.Add("alignment " + name + ": " + seg + " fixed lines, " + al.Length.ToString("0.0") + " m, style " + alignStyle + " / " + alignLabelSet + ", layer " + alayer);
}
else log.Add("alignment exists");
// ---- profile
ObjectId pid = ObjectId.Null; var alr = (Alignment)Transaction.GetObject(aid, OpenMode.ForRead);
foreach (ObjectId id in alr.GetProfileIds()) { var p = (Profile)Transaction.GetObject(id, OpenMode.ForRead); if (p.Name == profName) pid = id; }
if (pid.IsNull)
{
    var player = ObjLayer(SettingsObjectLayerType.Profile, name); var lt2 = (LayerTable)Transaction.GetObject(Database.LayerTableId, OpenMode.ForRead);
    pid = Profile.CreateFromSurface(profName, aid, sid, lt2[player], StyleId("profile", styles.ProfileStyles, profileStyle), StyleId("profile label set", styles.LabelSetStyles.ProfileLabelSetStyles, profileLabelSet));
    var pr = (Profile)Transaction.GetObject(pid, OpenMode.ForRead);
    log.Add("profile " + profName + ": sta " + pr.StartingStation.ToString("0") + "-" + pr.EndingStation.ToString("0") + ", elev " + pr.ElevationMin.ToString("0.00") + "-" + pr.ElevationMax.ToString("0.00") + ", style " + profileStyle + " / " + profileLabelSet + ", layer " + player);
}
else log.Add("profile exists");
// ---- profile view
ObjectId vid = ObjectId.Null;
foreach (ObjectId id in alr.GetProfileViewIds()) { var v = (ProfileView)Transaction.GetObject(id, OpenMode.ForRead); if (v.Name == viewName) vid = id; }
if (vid.IsNull)
{
    vid = ProfileView.Create(aid, insert, viewName, profileViewBandSetId: StyleId("band set", styles.ProfileViewBandSetStyles, bandSet), profileViewStyleId: StyleId("profile view", styles.ProfileViewStyles, pvStyle));
    var pv = (ProfileView)Transaction.GetObject(vid, OpenMode.ForWrite);
    pv.Layer = ObjLayer(SettingsObjectLayerType.ProfileView, name);
    log.Add("view " + viewName + ": sta " + pv.StationStart.ToString("0") + "-" + pv.StationEnd.ToString("0") + ", elev " + pv.ElevationMin.ToString("0.0") + "-" + pv.ElevationMax.ToString("0.0") + ", style " + pvStyle + ", bands " + bandSet + ", layer " + pv.Layer);
}
else log.Add("view exists");
// ---- leader from the view's lower-left corner to the alignment start (MText placed explicitly: the W4 version left it at the origin)
var btr = (BlockTableRecord)Transaction.GetObject(SymbolUtilityServices.GetBlockModelSpaceId(Database), OpenMode.ForWrite);
bool hasLeader = false;
foreach (ObjectId id in btr) { if (Transaction.GetObject(id, OpenMode.ForRead) is MLeader m && m.Layer == leaderLayer && m.ContentType == ContentType.MTextContent && m.MText != null && m.MText.Contents.Contains(viewName)) hasLeader = true; }
if (!hasLeader)
{
    EnsureLayer(leaderLayer, leaderColor);
    var start = alr.StartPoint; var textPt = new Point3d(insert.X, insert.Y - 4.0 * leaderTextH, 0.0);   // below the band row (25 m) and the axis labels
    var ml = new MLeader(); ml.SetDatabaseDefaults(); ml.Layer = leaderLayer; ml.ContentType = ContentType.MTextContent;
    var mt = new MText(); mt.SetDatabaseDefaults(); mt.Contents = viewName + "  <-  alignment " + name; mt.TextHeight = leaderTextH; mt.Location = textPt; mt.Attachment = AttachmentPoint.MiddleLeft;
    ml.MText = mt;
    int ld = ml.AddLeader(); int ln = ml.AddLeaderLine(ld);
    ml.AddFirstVertex(ln, start); ml.AddLastVertex(ln, new Point3d(textPt.X - 3.0 * leaderTextH, textPt.Y, 0.0));
    ml.TextLocation = textPt; ml.ArrowSize = 1.5 * leaderTextH; ml.LandingGap = 0.5 * leaderTextH; ml.EnableDogleg = true; ml.DoglegLength = 2.0 * leaderTextH; ml.TextHeight = leaderTextH;
    btr.AppendEntity(ml); Transaction.AddNewlyCreatedDBObject(ml, true);
    log.Add("leader from " + start.X.ToString("0.0") + "," + start.Y.ToString("0.0") + " to text at " + textPt.X.ToString("0.0") + "," + textPt.Y.ToString("0.0") + " (h " + leaderTextH + ")");
}
else log.Add("leader exists");
return new { name, kind, log, surface = sid.Handle.ToString(), alignment = aid.Handle.ToString(), profile = pid.Handle.ToString(), view = vid.Handle.ToString() };
