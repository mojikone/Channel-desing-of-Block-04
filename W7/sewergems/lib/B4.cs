using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Reflection;
using System.Collections.Generic;
using System.Collections;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;
using OpenFlows.StormSewer.Domain.ModelingElements;

// Block 04 channel model (Batinah, 2026-10-11): conduit and node tables of the active scenario, inputs as designed plus the
// results of the last run. A catalogue size is identified by CLASS + GUID: the engineer's five classes share their size GUIDs
// (the n-th size of every class carries the same GUID), so the label, rise, span and material come from the size row of the
// class assigned to the conduit in the active scenario's physical alternative (found 2026-10-11, HAWCH1-C7 on the 3 m class).
// results of the last run. Result values are read through reflection by method name, so a method the API does not offer
// gives an empty cell instead of a compile error; ResultMethods() lists what the results object really offers.
public static class B4
{
    static readonly System.Globalization.CultureInfo CI = System.Globalization.CultureInfo.InvariantCulture;
    public static string[] CONDUIT = { "Flow", "Velocity", "DepthIn", "DepthOut", "HydraulicGradeIn", "HydraulicGradeOut", "EnergyGradeIn", "EnergyGradeOut", "Capacity", "FullFlowCapacity", "PercentFull", "DepthToRise", "HeadlossTotal", "CriticalDepth", "NormalDepth", "FroudeNumber", "FlowCapacityRatio" };
    public class CatSize { public int ClassId; public string ClassLabel, Material, Label; public double Rise, Span, InsideDiameterMm; }
    // Catalogue sizes by "classId:guid" (rise and span stored in feet, returned in metres).
    public static Dictionary<string, CatSize> CatalogueByClass(IStormSewerModel m)
    {
        var dds = m.DomainDataSet;
        var st = dds.DomainDataSetType().SupportElementType("CatalogConduit");
        var f = dds.FieldManager.SupportElementField("ClassSizeCollection", st.Id);
        var fmat = dds.FieldManager.SupportElementField("CatalogConduit_Material", st.Id);
        var res = new Dictionary<string, CatSize>();
        foreach (IModelingElement el in dds.SupportElementManager(st.Id).Elements())
        {
            string material = Convert.ToString(fmat.GetValue(el.Id));
            var lm = f.GetValue(el.Id);
            var dv = (System.Data.DataView)lm.GetType().GetProperty("DataView").GetValue(lm, null);
            foreach (System.Data.DataRowView r in dv)
                res[el.Id + ":" + Convert.ToString(r["ClassSizeCollection_Guid"]).ToLowerInvariant()] = new CatSize { ClassId = el.Id, ClassLabel = el.Label, Material = material,
                    Label = Convert.ToString(r["ClassSizeCollection_Label"]), Rise = Convert.ToDouble(r["ClassSizeCollection_Rise"]) * 0.3048,
                    Span = Convert.ToDouble(r["ClassSizeCollection_Span"]) * 0.3048, InsideDiameterMm = Convert.ToDouble(r["ClassSizeCollection_InsideDiameter"]) * 304.8 };
        }
        return res;
    }
    // Conduit id -> catalogue class id in the active scenario's physical alternative.
    public static Dictionary<int, int> ConduitClasses(IStormSewerModel m)
    {
        var dds = m.DomainDataSet; var dst = dds.DomainDataSetType();
        var hs = (IScenario)dds.ScenarioManager.Element(m.ActiveScenario.Id);
        int altId = hs.AlternativeID("Physical");
        var vals = dds.FieldManager.AlternativeField("CatalogPipeType_CatalogPipeID", dst.AlternativeType("Physical").Id, 3, altId).GetValues();
        var res = new Dictionary<int, int>();
        foreach (DictionaryEntry e in vals) { if (e.Value != null && e.Value != DBNull.Value) res[Convert.ToInt32(e.Key)] = Convert.ToInt32(e.Value); }
        return res;
    }
    public static string[] NODE = { "HydraulicGrade", "EnergyGrade", "Flow", "FlowIn", "FlowOut", "Depth", "Freeboard", "DepthToRim" };

    static string S(object v)
    {
        if (v == null) return "";
        if (v is double) { var d = (double)v; return double.IsNaN(d) ? "" : d.ToString("R", CI); }
        if (v is float) { var d = (float)v; return float.IsNaN(d) ? "" : d.ToString("R", CI); }
        var s = Convert.ToString(v, CI);
        return s.Contains(",") || s.Contains("\"") ? "\"" + s.Replace("\"", "\"\"") + "\"" : s;
    }
    public static object Res(object element)
    {
        if (element == null) return null;
        var p = element.GetType().GetProperty("Results");
        return p == null ? null : p.GetValue(element, null);
    }
    static string R(object results, string name)
    {
        if (results == null) return "";
        MethodInfo mi = null;
        try { mi = results.GetType().GetMethod(name, Type.EmptyTypes); } catch { }
        if (mi == null) return "";
        try { return S(mi.Invoke(results, null)); } catch { return "ERR"; }
    }
    public static IList<string> ResultMethods(object results)
    {
        if (results == null) return new List<string>();
        return results.GetType().GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .Where(m => m.GetParameters().Length == 0 && m.ReturnType != typeof(void) && !m.Name.StartsWith("get_") && m.DeclaringType != typeof(object))
            .Select(m => m.Name).Distinct().OrderBy(x => x).ToList();
    }

    public static void Export(IStormSewerModel m, string dir, string tag, TextWriter log)
    {
        Directory.CreateDirectory(dir);
        var cat = CatalogueByClass(m); var cls = ConduitClasses(m);   // the size reference holds the real size (the diameter field can be stale); a size is class + GUID
        int nc = 0, nn = 0;
        using (var w = new StreamWriter(Path.Combine(dir, "conduits_" + tag + ".csv"), false, new UTF8Encoding(false)))
        {
            w.WriteLine("id,label,start,stop,active,length_m,size,size_label,size_value,class_id,class_label,material,rise_m,span_m,start_inv,stop_inv,slope," + string.Join(",", CONDUIT.Select(x => x.ToLowerInvariant())));
            foreach (var c in m.Network.Conduits.Elements())
            {
                var i = c.Input; CatSize sz = null; int classId;
                string key = i.Size == null ? "" : i.Size.ToString();
                if (key != "" && cls.TryGetValue(c.Id, out classId)) cat.TryGetValue(classId + ":" + key.ToLowerInvariant(), out sz);
                double L = i.Length; string slope = L > 0 ? ((i.StartInvert - i.StopInvert) / L).ToString("R", CI) : "";
                var res = Res(c);
                w.WriteLine(string.Join(",", c.Id, S(c.Label), S(i.StartNode.Label), S(i.StopNode.Label), i.IsActive, S(L), S(key),
                    S(sz != null ? sz.Label : i.ConduitShapeLabel), S(sz != null ? (object)sz.InsideDiameterMm : (object)i.ConduitDiameter),
                    sz != null ? sz.ClassId.ToString() : "", S(sz != null ? sz.ClassLabel : ""), S(sz != null ? sz.Material : ""), S(sz != null ? (object)sz.Rise : null), S(sz != null ? (object)sz.Span : null),
                    S(i.StartInvert), S(i.StopInvert), slope, string.Join(",", CONDUIT.Select(n => R(res, n)))));
                nc++;
            }
        }
        using (var w = new StreamWriter(Path.Combine(dir, "nodes_" + tag + ".csv"), false, new UTF8Encoding(false)))
        {
            w.WriteLine("id,label,type,active,x,y,ground,rim,invert," + string.Join(",", NODE.Select(x => x.ToLowerInvariant())));
            foreach (var n in m.Network.Manholes.Elements())
            {
                var i = n.Input; var p = i.GetPoint(); var res = Res(n);
                w.WriteLine(string.Join(",", n.Id, S(n.Label), "MH", i.IsActive, S(p.X), S(p.Y), S(i.GroundElevation), S(i.RimElevation), S(i.InvertElevation), string.Join(",", NODE.Select(x => R(res, x))))); nn++;
            }
            foreach (var n in m.Network.Outfalls.Elements())
            {
                var i = n.Input; var p = i.GetPoint(); var res = Res(n);
                w.WriteLine(string.Join(",", n.Id, S(n.Label), "OF", i.IsActive, S(p.X), S(p.Y), S(i.GroundElevation), S(i.RimElevation), S(i.InvertElevation), string.Join(",", NODE.Select(x => R(res, x))))); nn++;
            }
        }
        log.WriteLine("  exported '{0}': {1} conduits, {2} nodes", tag, nc, nn);
    }
}
