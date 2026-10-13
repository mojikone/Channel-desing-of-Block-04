// Inventory of the styles and command defaults of the active drawing (i.e. of the project template when the drawing
// was started from it). Read-only. Returns one JSON object. Reflection is used for the command settings so that no
// guessed member name can break the script.
using Autodesk.Civil.DatabaseServices.Styles;
using Autodesk.Civil.Settings;
var root = CivilDoc.Styles;
var o = new Dictionary<string, object>();
string NameOf(ObjectId id) { if (id.IsNull) return "<null>"; try { var e = Transaction.GetObject(id, OpenMode.ForRead); if (e is StyleBase sb) return sb.Name; var p = e.GetType().GetProperty("Name"); if (p != null && p.CanRead) return p.GetValue(e) as string ?? "?"; return e.GetType().Name; } catch (System.Exception ex) { return "<" + ex.GetType().Name + ">"; } }
List<string> Names(System.Collections.IEnumerable coll) { var l = new List<string>(); foreach (var x in coll) { if (x is ObjectId id) l.Add(NameOf(id)); } return l; }
o["drawing"] = new { Document.Name, Database.Filename, guid = Database.FingerprintGuid.ToString(), cannoscale = Database.Cannoscale.Name, cannoscaleValue = Database.Cannoscale.Scale, lwdisplay = Autodesk.AutoCAD.ApplicationServices.Core.Application.GetSystemVariable("LWDISPLAY"), insunits = Database.Insunits.ToString(), coordSys = CivilDoc.Settings.DrawingSettings.UnitZoneSettings.CoordinateSystemCode };
o["alignmentStyles"] = Names(root.AlignmentStyles);
o["alignmentLabelSets"] = Names(root.LabelSetStyles.AlignmentLabelSetStyles);
o["profileStyles"] = Names(root.ProfileStyles);
o["profileLabelSets"] = Names(root.LabelSetStyles.ProfileLabelSetStyles);
o["profileViewStyles"] = Names(root.ProfileViewStyles);
o["bandSets"] = Names(root.ProfileViewBandSetStyles);
o["profileDataBands"] = Names(root.BandStyles.ProfileViewProfileDataBandStyles);
o["horizGeomBands"] = Names(root.BandStyles.ProfileViewHorizontalGeometryBandStyles);
o["vertGeomBands"] = Names(root.BandStyles.ProfileViewVerticalGeometryBandStyles);
o["surfaceStyles"] = Names(root.SurfaceStyles);
// band set contents: which bands each set carries, with their intervals
var sets = new List<object>();
foreach (ObjectId id in root.ProfileViewBandSetStyles)
{
    var bs = (ProfileViewBandSetStyle)Transaction.GetObject(id, OpenMode.ForRead);
    var items = new List<object>();
    foreach (var side in new[] { "bottom", "top" })
    {
        var coll = side == "bottom" ? bs.GetBottomBandSetItems() : bs.GetTopBandSetItems();
        foreach (var it in coll)
        {
            var d = new Dictionary<string, object> { ["side"] = side };
            foreach (var p in it.GetType().GetProperties())
            {
                try { var v = p.GetValue(it); d[p.Name] = v is ObjectId oid ? NameOf(oid) : (v == null ? null : (v.GetType().IsPrimitive || v is string || v is Enum ? v.ToString() : v.GetType().Name)); } catch (System.Exception ex) { d[p.Name] = "err " + ex.GetType().Name; }
            }
            items.Add(d);
        }
    }
    sets.Add(new { name = bs.Name, items });
}
o["bandSetDetails"] = sets;
// profile view styles: exaggeration, axis intervals, grid components
var pvs = new List<object>();
foreach (ObjectId id in root.ProfileViewStyles)
{
    var s = (ProfileViewStyle)Transaction.GetObject(id, OpenMode.ForRead);
    var d = new Dictionary<string, object> { ["name"] = s.Name };
    try { d["verticalExaggeration"] = s.GraphStyle.VerticalExaggeration; d["direction"] = s.GraphStyle.Direction.ToString(); } catch (System.Exception ex) { d["graph"] = ex.Message; }
    try { d["bottomMajor"] = s.BottomAxis.MajorTickStyle.Interval; d["bottomMinor"] = s.BottomAxis.MinorTickStyle.Interval; d["leftMajor"] = s.LeftAxis.MajorTickStyle.Interval; d["leftMinor"] = s.LeftAxis.MinorTickStyle.Interval; d["topMajor"] = s.TopAxis.MajorTickStyle.Interval; d["rightMajor"] = s.RightAxis.MajorTickStyle.Interval; } catch (System.Exception ex) { d["axes"] = ex.Message; }
    try { var vis = new Dictionary<string, object>(); foreach (ProfileViewDisplayStyleType t in Enum.GetValues(typeof(ProfileViewDisplayStyleType))) { try { var ds = s.GetDisplayStylePlan(t); vis[t.ToString()] = new { ds.Visible, ds.Layer, color = ds.Color.ColorIndex, lw = ds.Lineweight.ToString() }; } catch { } } d["display"] = vis; } catch (System.Exception ex) { d["display"] = ex.Message; }
    pvs.Add(d);
}
o["profileViewStyleDetails"] = pvs;
// command defaults from the template (reflection on the settings classes, no compile-time dependence on their names)
var asm = typeof(CivilDocument).Assembly; var defaults = new Dictionary<string, object>();
string Dump(object obj, int depth)
{
    if (obj == null) return "null";
    var t = obj.GetType();
    if (obj is ObjectId oid) return NameOf(oid);
    if (t.IsPrimitive || obj is string || obj is Enum || obj is decimal) return obj.ToString();
    if (depth > 3) return t.Name;
    var parts = new List<string>();
    foreach (var p in t.GetProperties(System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance))
    {
        if (p.GetIndexParameters().Length > 0) continue;
        try { var v = p.GetValue(obj); var txt = Dump(v, depth + 1); if (txt != null && txt != t.Name) parts.Add(p.Name + "=" + txt); } catch { }
    }
    return "{" + string.Join("; ", parts) + "}";
}
var getSettings = CivilDoc.Settings.GetType().GetMethod("GetSettings");
foreach (var cls in new[] { "SettingsCmdCreateProfileView", "SettingsCmdCreateProfileFromSurface", "SettingsCmdCreateAlignmentEntities", "SettingsCmdCreateAlignmentLayout", "SettingsCmdCreateSurface", "SettingsCmdCreateMultipleProfileView", "SettingsProfileView", "SettingsProfile", "SettingsAlignment", "SettingsSurface" })
{
    var ty = asm.GetType("Autodesk.Civil.Settings." + cls);
    if (ty == null) { defaults[cls] = "<type not found>"; continue; }
    try { var st = getSettings.MakeGenericMethod(ty).Invoke(CivilDoc.Settings, null); defaults[cls] = Dump(st, 0); } catch (System.Exception ex) { defaults[cls] = "err " + (ex.InnerException ?? ex).Message; }
}
o["commandDefaults"] = defaults;
// object layers of the template
var layers = new Dictionary<string, object>();
foreach (SettingsObjectLayerType t in Enum.GetValues(typeof(SettingsObjectLayerType))) { try { var ol = CivilDoc.Settings.DrawingSettings.ObjectLayerSettings.GetObjectLayerSetting(t); layers[t.ToString()] = ol.LayerName + (ol.Modifier != ObjectLayerModifierType.None ? " [" + ol.Modifier + " " + ol.ModifierValue + "]" : ""); } catch { } }
o["objectLayers"] = layers;
// mleader styles, text styles
var ml = new List<string>(); var mld = (DBDictionary)Transaction.GetObject(Database.MLeaderStyleDictionaryId, OpenMode.ForRead); foreach (var e in mld) ml.Add(e.Key); o["mleaderStyles"] = ml;
var ts = new List<string>(); var tst = (TextStyleTable)Transaction.GetObject(Database.TextStyleTableId, OpenMode.ForRead); foreach (ObjectId id in tst) ts.Add(((TextStyleTableRecord)Transaction.GetObject(id, OpenMode.ForRead)).Name); o["textStyles"] = ts;
return o;
