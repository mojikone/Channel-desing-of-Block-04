// Census of the drawing: counts of surfaces, alignments, profiles, profile views and leaders, every view's style and
// band set, and the leaders' vertex extent (must stay inside the block, nothing near the origin). Read-only.
using Autodesk.Civil.DatabaseServices.Styles;
var surf = CivilDoc.GetSurfaceIds().Count; var als = CivilDoc.GetAlignmentIds();
int nProf = 0, nView = 0; var styles = new Dictionary<string, int>(); var bands = new Dictionary<string, int>(); var views = new List<object>();
foreach (ObjectId aid in als)
{
    var al = (Alignment)Transaction.GetObject(aid, OpenMode.ForRead); nProf += al.GetProfileIds().Count;
    foreach (ObjectId vid in al.GetProfileViewIds())
    {
        var pv = (ProfileView)Transaction.GetObject(vid, OpenMode.ForRead); nView++;
        styles[pv.StyleName] = styles.GetValueOrDefault(pv.StyleName) + 1;
        string bs = "?"; try { var items = pv.Bands.GetBottomBandItems(); bs = items.Count + " bottom band(s)"; } catch { }
        bands[bs] = bands.GetValueOrDefault(bs) + 1;
        views.Add(new { pv.Name, al = al.Name, len = Math.Round(pv.StationEnd - pv.StationStart), elev = Math.Round(pv.ElevationMax - pv.ElevationMin, 1), x = Math.Round(pv.Location.X), y = Math.Round(pv.Location.Y) });
    }
}
var btr = (BlockTableRecord)Transaction.GetObject(SymbolUtilityServices.GetBlockModelSpaceId(Database), OpenMode.ForRead);
int nLeader = 0; double minx = 1e12, miny = 1e12, maxx = -1e12, maxy = -1e12; var layers = new Dictionary<string, int>();
foreach (ObjectId id in btr)
{
    if (Transaction.GetObject(id, OpenMode.ForRead) is MLeader m)
    {
        nLeader++; layers[m.Layer] = layers.GetValueOrDefault(m.Layer) + 1;
        for (int i = 0; i < m.LeaderLineCount; i++) { foreach (var p in new[] { m.GetFirstVertex(i), m.GetLastVertex(i), m.TextLocation }) { minx = Math.Min(minx, p.X); maxx = Math.Max(maxx, p.X); miny = Math.Min(miny, p.Y); maxy = Math.Max(maxy, p.Y); } }
    }
}
var ext = Database.Extmin; var ext2 = Database.Extmax;
return new { surfaces = surf, alignments = als.Count, profiles = nProf, viewCount = nView, leaders = nLeader, leaderLayers = layers, viewStyles = styles, viewBands = bands,
    leaderExtent = new { minx, miny, maxx, maxy }, drawingExtents = new { ext.X, ext.Y, x2 = ext2.X, y2 = ext2.Y }, cannoscale = Database.Cannoscale.Name, views };
