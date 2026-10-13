// Junction fix (engineer, 2026-10-10): for every tributary channel ending on a receiving channel, set the LAST PVI of
// "GDP <tributary>" to the receiver's GDP elevation at the junction station (interpolated between the receiver's current
// PVIs), after keeping the previous line as a dashed layout profile "GDP <tributary> (before junction fix)" in the same
// view. {{JUNCTIONS}}: entries "tributary|receiver|receiverStation" separated by ';', receivers before their tributaries.
// {{BEFORE_SUFFIX}}: suffix of the dashed copy's name, " (before junction fix)" on the first run.
// A profile style "GDP previous (dashed)" (copy of the design style's line component, DASHED, colour 6) is created once.
using Autodesk.Civil.DatabaseServices.Styles;
var spec = "{{JUNCTIONS}}"; var designStyle = "{{DESIGN_STYLE}}"; var prevStyleName = "GDP previous (dashed)"; var labelSet = "_No Labels";
var styles = CivilDoc.Styles; var log = new List<object>(); var problems = new List<string>();
// ---- dashed style for the previous line
var ltt = (LinetypeTable)Transaction.GetObject(Database.LinetypeTableId, OpenMode.ForRead);
if (!ltt.Has("DASHED")) { try { Database.LoadLineTypeFile("DASHED", "acad.lin"); } catch (System.Exception ex) { problems.Add("DASHED linetype not loaded: " + ex.Message); } }
ObjectId prevStyleId = ObjectId.Null;
try { prevStyleId = styles.ProfileStyles[prevStyleName]; } catch { }
if (prevStyleId.IsNull)
{
    prevStyleId = styles.ProfileStyles.Add(prevStyleName);
    var ps = (ProfileStyle)Transaction.GetObject(prevStyleId, OpenMode.ForWrite);
    foreach (ProfileDisplayStyleProfileType t in Enum.GetValues(typeof(ProfileDisplayStyleProfileType)))
    {
        try
        {
            var ds = ps.GetDisplayStyleProfile(t);
            bool line = t == ProfileDisplayStyleProfileType.Line || t == ProfileDisplayStyleProfileType.Curve || t == ProfileDisplayStyleProfileType.SymmetricalParabola || t == ProfileDisplayStyleProfileType.AsymmetricalParabola;
            ds.Visible = line;
            if (line) { ds.Color = Autodesk.AutoCAD.Colors.Color.FromColorIndex(Autodesk.AutoCAD.Colors.ColorMethod.ByAci, 6); if (ltt.Has("DASHED")) ds.Linetype = "DASHED"; ds.LinetypeScale = 1.0; }
        }
        catch (System.Exception ex) { problems.Add("style component " + t + ": " + ex.Message); }
    }
    log.Add(new { created = prevStyleName });
}
// ---- helpers
var als = new Dictionary<string, Alignment>();
foreach (ObjectId aid in CivilDoc.GetAlignmentIds()) { var a = (Alignment)Transaction.GetObject(aid, OpenMode.ForRead); als[a.Name] = a; }
Profile Gdp(string al, bool write)
{
    foreach (ObjectId pid in als[al].GetProfileIds()) { var p = (Profile)Transaction.GetObject(pid, write ? OpenMode.ForWrite : OpenMode.ForRead); if (p.Name == "GDP " + al) return p; }
    return null;
}
List<(double sta, double elev)> Pvis(Profile p) { var l = new List<(double, double)>(); foreach (ProfilePVI q in p.PVIs) l.Add((q.Station, q.Elevation)); l.Sort((a, b) => a.Item1.CompareTo(b.Item1)); return l; }
double At(List<(double sta, double elev)> pv, double s)
{
    if (s <= pv[0].sta) return pv[0].elev; if (s >= pv[pv.Count - 1].sta) return pv[pv.Count - 1].elev;
    for (int i = 1; i < pv.Count; i++) if (s <= pv[i].sta) { var a = pv[i - 1]; var b = pv[i]; return b.sta > a.sta ? a.elev + (b.elev - a.elev) * (s - a.sta) / (b.sta - a.sta) : a.elev; }
    return pv[pv.Count - 1].elev;
}
// ---- the fixes, in the given order
foreach (var item in spec.Split(';'))
{
    if (string.IsNullOrWhiteSpace(item)) continue;
    var f = item.Split('|'); var trib = f[0]; var recv = f[1]; double sta = double.Parse(f[2], System.Globalization.CultureInfo.InvariantCulture);
    if (!als.ContainsKey(trib) || !als.ContainsKey(recv)) { problems.Add(item + ": alignment missing"); continue; }
    var pr = Gdp(recv, false); var pt = Gdp(trib, true);
    if (pr == null || pt == null) { problems.Add(item + ": GDP profile missing"); continue; }
    double target = At(Pvis(pr), sta);
    var old = Pvis(pt); int n = old.Count; double oldEnd = old[n - 1].elev;
    // the previous line, kept dashed (once: skip if it already exists)
    bool exists = false; foreach (ObjectId pid in als[trib].GetProfileIds()) { var p = (Profile)Transaction.GetObject(pid, OpenMode.ForRead); if (p.Name == "GDP " + trib + "{{BEFORE_SUFFIX}}") exists = true; }
    if (!exists)
    {
        var prevId = Profile.CreateByLayout("GDP " + trib + "{{BEFORE_SUFFIX}}", als[trib].ObjectId, als[trib].LayerId, prevStyleId, styles.LabelSetStyles.ProfileLabelSetStyles[labelSet]);
        var prev = (Profile)Transaction.GetObject(prevId, OpenMode.ForWrite); foreach (var q in old) prev.PVIs.AddPVI(q.sta, q.elev);
    }
    // move the last PVI
    ProfilePVI last = null; foreach (ProfilePVI q in pt.PVIs) if (last == null || q.Station > last.Station) last = q;
    last.Elevation = target;
    var now = Pvis(pt); double L = now[n - 1].sta - now[n - 2].sta;
    double slopeOld = (old[n - 2].elev - old[n - 1].elev) / L, slopeNew = (now[n - 2].elev - now[n - 1].elev) / L;
    log.Add(new { trib, recv, sta = Math.Round(sta, 1), oldEnd = Math.Round(oldEnd, 3), newEnd = Math.Round(target, 3), diff = Math.Round(target - oldEnd, 3), lastSegment_m = Math.Round(L, 1), slopeOld = Math.Round(slopeOld, 5), slopeNew = Math.Round(slopeNew, 5), flag = slopeNew < 0 ? "REVERSE SLOPE on the last segment" : (slopeNew < 0.0005 ? "flat last segment" : "") });
}
return new { fixes = log, problems };
