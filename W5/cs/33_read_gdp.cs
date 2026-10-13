// The PVIs of every "GDP <name>" layout profile in the drawing (the engineer's reviewed ground design profiles), with
// the plan coordinates of each PVI on its alignment. Read-only; one call for all alignments.
var result = new List<object>();
foreach (ObjectId aid in CivilDoc.GetAlignmentIds())
{
    var al = (Alignment)Transaction.GetObject(aid, OpenMode.ForRead);
    foreach (ObjectId pid in al.GetProfileIds())
    {
        var p = (Profile)Transaction.GetObject(pid, OpenMode.ForRead);
        if (p.ProfileType == ProfileType.EG || !p.Name.StartsWith("GDP ") || p.Name.Contains("(before")) continue;   // the dashed "before junction fix" copies are not the live GDP
        var pvis = new List<object>();
        foreach (ProfilePVI pvi in p.PVIs)
        {
            double x = 0, y = 0; try { al.PointLocation(pvi.Station, 0.0, ref x, ref y); } catch { }
            string ty = "?"; try { ty = pvi.PVIType.ToString(); } catch { }
            pvis.Add(new { sta = Math.Round(pvi.Station, 3), elev = Math.Round(pvi.Elevation, 3), x = Math.Round(x, 3), y = Math.Round(y, 3), type = ty });
        }
        result.Add(new { alignment = al.Name, profile = p.Name, style = p.StyleName, alStart = Math.Round(al.StartingStation, 3), alEnd = Math.Round(al.EndingStation, 3), pStart = Math.Round(p.StartingStation, 3), pEnd = Math.Round(p.EndingStation, 3), entities = p.Entities.Count, pvis });
    }
}
return new { count = result.Count, saved = Convert.ToInt32(Autodesk.AutoCAD.ApplicationServices.Core.Application.GetSystemVariable("DBMOD")) == 0, profiles = result };
