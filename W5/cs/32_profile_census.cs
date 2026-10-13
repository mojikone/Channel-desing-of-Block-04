// Count the profiles of the drawing by type: existing ground, GDP layout profiles, other layout profiles (by name),
// and the GDP plan markers. Read-only.
int eg = 0, gdp = 0; var others = new List<string>(); var gdpPvis = new List<object>();
foreach (ObjectId aid in CivilDoc.GetAlignmentIds())
{
    var al = (Alignment)Transaction.GetObject(aid, OpenMode.ForRead);
    foreach (ObjectId pid in al.GetProfileIds())
    {
        var p = (Profile)Transaction.GetObject(pid, OpenMode.ForRead);
        if (p.ProfileType == ProfileType.EG) eg++;
        else if (p.Name.StartsWith("GDP ")) { gdp++; gdpPvis.Add(new { p.Name, pvis = p.PVIs.Count, style = p.StyleName }); }
        else others.Add(p.Name + " (" + p.ProfileType + ", " + p.StyleName + ")");
    }
}
int circles = 0, texts = 0; var btr = (BlockTableRecord)Transaction.GetObject(SymbolUtilityServices.GetBlockModelSpaceId(Database), OpenMode.ForRead);
foreach (ObjectId id in btr) { var e = Transaction.GetObject(id, OpenMode.ForRead); if (e is Circle c && c.Layer == "W5-GDP-BREAKS") circles++; else if (e is DBText t && t.Layer == "W5-GDP-BREAKS") texts++; }
return new { existingGround = eg, gdpProfiles = gdp, gdpPviTotal = gdpPvis.Sum(x => (int)x.GetType().GetProperty("pvis").GetValue(x)), otherLayoutProfiles = others, markers = new { circles, texts }, gdpPvis };
