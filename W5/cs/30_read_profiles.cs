// Read the profiles of one alignment: every profile's name, type, style and PVIs (station, elevation, grades), and the
// existing-ground profile sampled every {{STEP}} m (elevations as one comma-separated string: the result cap of 1000
// items would truncate a list). Read-only.
var alName = "{{NAME}}"; double step = {{STEP}};
Alignment al = null;
foreach (ObjectId id in CivilDoc.GetAlignmentIds()) { var a = (Alignment)Transaction.GetObject(id, OpenMode.ForRead); if (a.Name == alName) al = a; }
if (al == null) return new { error = "alignment not found: " + alName };
var profiles = new List<object>(); string egSamples = null; double egStart = 0, egEnd = 0; string egName = null;
foreach (ObjectId pid in al.GetProfileIds())
{
    var p = (Profile)Transaction.GetObject(pid, OpenMode.ForRead);
    var pvis = new List<object>();
    if (p.ProfileType != ProfileType.EG) try { foreach (ProfilePVI pvi in p.PVIs) { double gi = double.NaN, go = double.NaN; try { gi = pvi.GradeIn; } catch { } try { go = pvi.GradeOut; } catch { } string ty = "?"; try { ty = pvi.PVIType.ToString(); } catch { } pvis.Add(new { sta = Math.Round(pvi.Station, 3), elev = Math.Round(pvi.Elevation, 3), gIn = double.IsNaN(gi) ? (object)null : Math.Round(gi, 5), gOut = double.IsNaN(go) ? (object)null : Math.Round(go, 5), type = ty }); } } catch (System.Exception ex) { pvis.Add(new { err = ex.Message }); }
    profiles.Add(new { p.Name, type = p.ProfileType.ToString(), style = p.StyleName, p.Layer, start = Math.Round(p.StartingStation, 3), end = Math.Round(p.EndingStation, 3), entities = p.Entities.Count, pviCount = pvis.Count, pvis });
    if (p.ProfileType == ProfileType.EG && egSamples == null)
    {
        var sb = new System.Text.StringBuilder(); egStart = p.StartingStation; egEnd = p.EndingStation; egName = p.Name;
        for (double s = egStart; s <= egEnd + 1e-9; s += step) { double e; try { e = p.ElevationAt(Math.Min(s, egEnd)); } catch { e = double.NaN; } sb.Append(e.ToString("0.000", System.Globalization.CultureInfo.InvariantCulture)).Append(','); }
        egSamples = sb.ToString().TrimEnd(',');
    }
}
var views = new List<object>();
foreach (ObjectId vid in al.GetProfileViewIds()) { var v = (ProfileView)Transaction.GetObject(vid, OpenMode.ForRead); views.Add(new { v.Name, v.StationStart, v.StationEnd, v.ElevationMin, v.ElevationMax }); }
return new { alignment = al.Name, length = al.Length, startStation = al.StartingStation, profiles, views, eg = new { name = egName, start = egStart, end = egEnd, step, samples = egSamples } };
