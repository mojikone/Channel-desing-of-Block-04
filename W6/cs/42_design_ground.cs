// GDP-raised profiles (engineer, 2026-10-11): per channel a layout profile "GDP-raised <alignment>" = GDP + raise at every design
// point: the model ground for SewerGEMS (the lower bank top where a point lies in a wadi, the library depth above the bed at
// fix points, the GDP elsewhere). {{PROFILES}}: entries "alignment|sta:elev,sta:elev,..." separated by ';' (stations ascending,
// first at the start, last at the end of the alignment). A profile style "GDP-raised" (cyan 4, continuous, 0.35 mm) is created
// once; an existing GDP-raised profile of the alignment is replaced, as is one under the first name "DG <alignment>" (green style
// "Design ground (GDP+raise)", renamed and recoloured on the engineer's instruction the same afternoon: the EG is green already).
// Label set "_No Labels".
using Autodesk.Civil.DatabaseServices.Styles;
var spec = "{{PROFILES}}"; var styleName = "GDP-raised"; var legacyStyle = "Design ground (GDP+raise)"; var labelSet = "_No Labels";
var styles = CivilDoc.Styles; var log = new List<object>(); var problems = new List<string>();
ObjectId styleId = ObjectId.Null;
try { styleId = styles.ProfileStyles[styleName]; } catch { }
if (styleId.IsNull)
{
    styleId = styles.ProfileStyles.Add(styleName);
    var ps = (ProfileStyle)Transaction.GetObject(styleId, OpenMode.ForWrite);
    foreach (ProfileDisplayStyleProfileType t in Enum.GetValues(typeof(ProfileDisplayStyleProfileType)))
    {
        try
        {
            var ds = ps.GetDisplayStyleProfile(t);
            bool line = t == ProfileDisplayStyleProfileType.Line || t == ProfileDisplayStyleProfileType.Curve || t == ProfileDisplayStyleProfileType.SymmetricalParabola || t == ProfileDisplayStyleProfileType.AsymmetricalParabola;
            ds.Visible = line;
            if (line) { ds.Color = Autodesk.AutoCAD.Colors.Color.FromColorIndex(Autodesk.AutoCAD.Colors.ColorMethod.ByAci, 4); ds.Lineweight = Autodesk.AutoCAD.DatabaseServices.LineWeight.LineWeight035; }
        }
        catch (System.Exception ex) { problems.Add("style component " + t + ": " + ex.Message); }
    }
    log.Add(new { created = styleName });
}
var als = new Dictionary<string, Alignment>();
foreach (ObjectId aid in CivilDoc.GetAlignmentIds()) { var a = (Alignment)Transaction.GetObject(aid, OpenMode.ForRead); als[a.Name] = a; }
int made = 0, replaced = 0, pvisTotal = 0;
foreach (var item in spec.Split(';'))
{
    if (string.IsNullOrWhiteSpace(item)) continue;
    var f = item.Split('|'); var name = f[0];
    if (!als.ContainsKey(name)) { problems.Add(name + ": alignment missing"); continue; }
    var al = als[name]; var dgName = "GDP-raised " + name; var legacyName = "DG " + name;
    foreach (ObjectId pid in al.GetProfileIds()) { var p = (Profile)Transaction.GetObject(pid, OpenMode.ForRead); if (p.Name == dgName || p.Name == legacyName) { p.UpgradeOpen(); p.Erase(); replaced++; } }
    var newId = Profile.CreateByLayout(dgName, al.ObjectId, al.LayerId, styleId, styles.LabelSetStyles.ProfileLabelSetStyles[labelSet]);
    var dg = (Profile)Transaction.GetObject(newId, OpenMode.ForWrite);
    int n = 0; double lastSta = double.NegativeInfinity;
    foreach (var pv in f[1].Split(','))
    {
        var se = pv.Split(':');
        double sta = double.Parse(se[0], System.Globalization.CultureInfo.InvariantCulture), elev = double.Parse(se[1], System.Globalization.CultureInfo.InvariantCulture);
        sta = Math.Max(al.StartingStation, Math.Min(sta, al.EndingStation));
        if (sta - lastSta < 0.01) { problems.Add(dgName + ": PVI at " + sta.ToString("0.00") + " skipped (same station)"); continue; }
        try { dg.PVIs.AddPVI(sta, elev); n++; lastSta = sta; } catch (System.Exception ex) { problems.Add(dgName + " PVI " + sta.ToString("0.00") + ": " + ex.Message); }
    }
    made++; pvisTotal += n; log.Add(new { profile = dgName, pvis = n, start = Math.Round(al.StartingStation, 2), end = Math.Round(al.EndingStation, 2) });
}
bool legacyStyleRemoved = false;
try { ObjectId lid = styles.ProfileStyles[legacyStyle]; if (!lid.IsNull) { var ls = (ProfileStyle)Transaction.GetObject(lid, OpenMode.ForWrite); ls.Erase(); legacyStyleRemoved = true; } } catch { }
return new { made, replaced, pvisTotal, legacyStyleRemoved, log, problems };
