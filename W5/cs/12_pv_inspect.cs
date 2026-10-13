// Inspect one profile view and what makes it legible or not: its style (exaggeration, axis tick intervals, grid
// visibility), its band items (band style, major/minor intervals, label text heights), the profile line style, the
// annotation scale, and the leaders in the drawing. Read-only.
using Autodesk.Civil.DatabaseServices.Styles;
using Autodesk.Civil.Settings;
var viewName = "{{VIEW}}";
ProfileView pv = null;
foreach (ObjectId aid in CivilDoc.GetAlignmentIds()) { var al = (Alignment)Transaction.GetObject(aid, OpenMode.ForRead); foreach (ObjectId id in al.GetProfileViewIds()) { var v = (ProfileView)Transaction.GetObject(id, OpenMode.ForRead); if (v.Name == viewName) pv = v; } }
if (pv == null) return new { error = "view not found: " + viewName };
var o = new Dictionary<string, object>();
string NameOf(ObjectId id) { if (id.IsNull) return "<null>"; try { var e = Transaction.GetObject(id, OpenMode.ForRead); if (e is StyleBase sb) return sb.Name; var p = e.GetType().GetProperty("Name"); if (p != null && p.CanRead) return p.GetValue(e) as string ?? "?"; return e.GetType().Name; } catch (System.Exception ex) { return "<" + ex.GetType().Name + ">"; } }
o["view"] = new { pv.Name, pv.Layer, style = pv.StyleName, pv.StationStart, pv.StationEnd, pv.ElevationMin, pv.ElevationMax, pv.Location, pv.ElevationRangeMode, pv.StationRangeMode };
o["cannoscale"] = new { Database.Cannoscale.Name, Database.Cannoscale.Scale, Database.Cannoscale.DrawingUnits, Database.Cannoscale.PaperUnits, lwdisplay = Autodesk.AutoCAD.ApplicationServices.Core.Application.GetSystemVariable("LWDISPLAY") };
var st = (ProfileViewStyle)Transaction.GetObject(pv.StyleId, OpenMode.ForRead);
var sd = new Dictionary<string, object> { ["name"] = st.Name };
try { sd["verticalExaggeration"] = st.GraphStyle.VerticalExaggeration; } catch (System.Exception ex) { sd["ve"] = ex.Message; }
try
{
    sd["bottomAxis"] = new { major = st.BottomAxis.MajorTickStyle.Interval, minor = st.BottomAxis.MinorTickStyle.Interval, majorLabelH = st.BottomAxis.MajorTickStyle.TextHeight, titleH = st.BottomAxis.TitleStyle.TextHeight };
    sd["leftAxis"] = new { major = st.LeftAxis.MajorTickStyle.Interval, minor = st.LeftAxis.MinorTickStyle.Interval, majorLabelH = st.LeftAxis.MajorTickStyle.TextHeight, titleH = st.LeftAxis.TitleStyle.TextHeight };
    sd["topAxis"] = new { major = st.TopAxis.MajorTickStyle.Interval, minor = st.TopAxis.MinorTickStyle.Interval };
    sd["rightAxis"] = new { major = st.RightAxis.MajorTickStyle.Interval, minor = st.RightAxis.MinorTickStyle.Interval };
}
catch (System.Exception ex) { sd["axes"] = ex.Message; }
var vis = new Dictionary<string, object>();
foreach (ProfileViewDisplayStyleType t in Enum.GetValues(typeof(ProfileViewDisplayStyleType))) { try { var ds = st.GetDisplayStylePlan(t); vis[t.ToString()] = new { ds.Visible, ds.Layer, color = ds.Color.ColorIndex, lw = ds.Lineweight.ToString(), lt = ds.Linetype }; } catch { } }
sd["display"] = vis;
double len = pv.StationEnd - pv.StationStart, h = pv.ElevationMax - pv.ElevationMin;
try { sd["gridLineCounts"] = new { verticalMinor = Math.Round(len / st.BottomAxis.MinorTickStyle.Interval), verticalMajor = Math.Round(len / st.BottomAxis.MajorTickStyle.Interval), horizontalMinor = Math.Round(h / st.LeftAxis.MinorTickStyle.Interval), horizontalMajor = Math.Round(h / st.LeftAxis.MajorTickStyle.Interval) }; } catch { }
o["style"] = sd;
// bands
var bands = new List<object>();
foreach (var side in new[] { "bottom", "top" })
{
    var items = side == "bottom" ? pv.Bands.GetBottomBandItems() : pv.Bands.GetTopBandItems();
    foreach (var it in items)
    {
        var d = new Dictionary<string, object> { ["side"] = side };
        foreach (var p in it.GetType().GetProperties()) { if (p.GetIndexParameters().Length > 0) continue; try { var v = p.GetValue(it); d[p.Name] = v is ObjectId oid ? NameOf(oid) : (v == null ? null : (v.GetType().IsPrimitive || v is string || v is Enum ? v.ToString() : v.GetType().Name)); } catch (System.Exception ex) { d[p.Name] = "err " + ex.GetType().Name; } }
        try
        {
            var bst = Transaction.GetObject(it.BandStyleId, OpenMode.ForRead);
            var bd = new Dictionary<string, object> { ["type"] = bst.GetType().Name };
            foreach (var p in bst.GetType().GetProperties()) { if (p.GetIndexParameters().Length > 0 || p.PropertyType == typeof(ObjectId)) continue; try { var v = p.GetValue(bst); if (v != null && (v.GetType().IsPrimitive || v is string || v is Enum)) bd[p.Name] = v.ToString(); } catch { } }
            d["bandStyle"] = bd;
        }
        catch (System.Exception ex) { d["bandStyle"] = ex.Message; }
        bands.Add(d);
    }
}
o["bands"] = bands;
// profiles in the view and their styles
var profs = new List<object>();
var alg = (Alignment)Transaction.GetObject(pv.AlignmentId, OpenMode.ForRead);
foreach (ObjectId id in alg.GetProfileIds()) { var p = (Profile)Transaction.GetObject(id, OpenMode.ForRead); var ps = (ProfileStyle)Transaction.GetObject(p.StyleId, OpenMode.ForRead); var comp = new Dictionary<string, object>(); foreach (ProfileDisplayStyleProfileType t in Enum.GetValues(typeof(ProfileDisplayStyleProfileType))) { try { var ds = ps.GetDisplayStyleProfile(t); comp[t.ToString()] = new { ds.Visible, ds.Layer, color = ds.Color.ColorIndex, lw = ds.Lineweight.ToString() }; } catch { } } profs.Add(new { p.Name, style = ps.Name, p.Layer, p.ProfileType, components = comp }); }
o["profiles"] = profs;
// leaders
var leaders = new List<object>(); var btr = (BlockTableRecord)Transaction.GetObject(SymbolUtilityServices.GetBlockModelSpaceId(Database), OpenMode.ForRead);
foreach (ObjectId id in btr) { if (Transaction.GetObject(id, OpenMode.ForRead) is MLeader m) { var verts = new List<double[]>(); try { for (int i = 0; i < m.LeaderLineCount; i++) { var c = m.GetFirstVertex(i); var e = m.GetLastVertex(i); verts.Add(new[] { c.X, c.Y, e.X, e.Y }); } } catch { } leaders.Add(new { m.Layer, text = m.MText?.Contents, textLoc = m.TextLocation, m.TextHeight, verts }); } }
o["leaders"] = leaders;
return o;
