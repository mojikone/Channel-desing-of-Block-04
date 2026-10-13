// Details of the candidate band styles, profile styles and profile view styles: every primitive property (text heights,
// band heights, label intervals) and the display components. Read-only. Names of interest are listed below.
using Autodesk.Civil.DatabaseServices.Styles;
var wanted = new HashSet<string> { "ARJV_Station", "ARJV_Existing Ground Level", "ARJV_Dam Crest", "ARJV_Excavation Level", "HTJ (STA & ELE)", "HTJ (Elevations and Stations)", "Elevations and Stations", "Stations", "Profile Data", "EX", "ARJV_ Horizontal Data" };
var root = CivilDoc.Styles; var o = new Dictionary<string, object>();
Dictionary<string, object> Dump(object obj)
{
    var d = new Dictionary<string, object>();
    foreach (var p in obj.GetType().GetProperties())
    {
        if (p.GetIndexParameters().Length > 0 || !p.CanRead) continue;
        try { var v = p.GetValue(obj); if (v == null) continue; var t = v.GetType(); if (t.IsPrimitive || v is string || v is Enum || v is decimal) d[p.Name] = v.ToString(); else if (p.PropertyType.Namespace != null && p.PropertyType.Namespace.StartsWith("Autodesk.Civil") && !(v is ObjectId)) { var sub = new Dictionary<string, object>(); foreach (var q in t.GetProperties()) { if (q.GetIndexParameters().Length > 0 || !q.CanRead) continue; try { var w = q.GetValue(v); if (w != null && (w.GetType().IsPrimitive || w is string || w is Enum)) sub[q.Name] = w.ToString(); } catch { } } if (sub.Count > 0) d[p.Name] = sub; } }
        catch { }
    }
    return d;
}
var bands = new Dictionary<string, object>();
foreach (var coll in new System.Collections.IEnumerable[] { root.BandStyles.ProfileViewProfileDataBandStyles, root.BandStyles.ProfileViewHorizontalGeometryBandStyles })
    foreach (ObjectId id in coll) { var s = (StyleBase)Transaction.GetObject(id, OpenMode.ForRead); if (wanted.Contains(s.Name)) bands[s.Name] = Dump(s); }
o["bandStyles"] = bands;
var profs = new Dictionary<string, object>();
foreach (ObjectId id in root.ProfileStyles) { var s = (ProfileStyle)Transaction.GetObject(id, OpenMode.ForRead); if (!s.Name.StartsWith("ARJV") && s.Name != "Basic" && s.Name != "Standard") continue; var comp = new Dictionary<string, object>(); foreach (ProfileDisplayStyleProfileType t in Enum.GetValues(typeof(ProfileDisplayStyleProfileType))) { try { var ds = s.GetDisplayStyleProfile(t); comp[t.ToString()] = new { ds.Visible, ds.Layer, color = ds.Color.ColorIndex, lw = ds.Lineweight.ToString(), lt = ds.Linetype }; } catch { } } profs[s.Name] = comp; }
o["profileStyles"] = profs;
var pvs = new Dictionary<string, object>();
foreach (ObjectId id in root.ProfileViewStyles) { var s = (ProfileViewStyle)Transaction.GetObject(id, OpenMode.ForRead); var d = new Dictionary<string, object>(); try { d["graph"] = Dump(s.GraphStyle); d["bottomAxis"] = Dump(s.BottomAxis); d["bottomMajorTick"] = Dump(s.BottomAxis.MajorTickStyle); d["bottomMinorTick"] = Dump(s.BottomAxis.MinorTickStyle); d["bottomTitle"] = Dump(s.BottomAxis.TitleStyle); d["leftAxis"] = Dump(s.LeftAxis); d["leftMajorTick"] = Dump(s.LeftAxis.MajorTickStyle); d["leftMinorTick"] = Dump(s.LeftAxis.MinorTickStyle); d["leftTitle"] = Dump(s.LeftAxis.TitleStyle); d["grid"] = Dump(s.GridStyle); } catch (System.Exception ex) { d["err"] = ex.Message; } pvs[s.Name] = d; }
o["profileViewStyles"] = pvs;
return o;
