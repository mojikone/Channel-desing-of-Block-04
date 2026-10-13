// W4 tool for Civil 3D 2026 (Block 4 channel design base). NETLOAD the DLL from a path without spaces, then:
//   W4BUILD   builds everything from civil3d/build_spec.json and points/csv/<name>.csv: one TIN surface per channel and
//             dyke (the corridor cells, outer boundary = the corridor), one alignment per feature (fixed lines through the
//             centreline vertices), one existing-ground profile, one profile view at the computed insertion point and a
//             leader from the view to the alignment; assigns the coordinate system UTM84-40N. Re-running skips what exists.
//   W4PV      the views and leaders only (for alignments and profiles made another way).
//   W4PVDEL   erases the views named "PV ..." and the leaders.
using System;
using System.IO;
using System.Globalization;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.AutoCAD.Runtime;
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.Geometry;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.Civil;
using Autodesk.Civil.ApplicationServices;
using Autodesk.Civil.DatabaseServices;
using Autodesk.Civil.DatabaseServices.Styles;
using CivilSurface = Autodesk.Civil.DatabaseServices.Surface;

namespace W4
{
    public class App : IExtensionApplication
    {
        public void Initialize() { Commands.Log("assembly loaded (W4Tools): commands W4BUILD, W4PV, W4PVDEL"); }
        public void Terminate() { }
    }

    public class Commands
    {
        public static void Log(string msg)
        {
            try { File.AppendAllText(W4DIR + @"\log\w4tools.log", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + "  " + msg + "\r\n"); } catch { }
        }
        const string W4DIR = @"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Claude Block 04\W4";
        const string SPEC = W4DIR + @"\civil3d\build_spec.json";
        const string CSV = W4DIR + @"\civil3d\profile_views.csv";

        class Feat { public string name, kind, surface, site, profile, view; public double insertX, insertY; public List<Point3d> boundary = new List<Point3d>(); public List<Point3d> alignment = new List<Point3d>(); }

        static List<Feat> ReadSpec()
        {
            var feats = new List<Feat>();
            using (var doc = JsonDocument.Parse(File.ReadAllText(SPEC)))
                foreach (var e in doc.RootElement.EnumerateArray())
                {
                    var f = new Feat { name = e.GetProperty("name").GetString(), kind = e.GetProperty("kind").GetString(), surface = e.GetProperty("surface").GetString(), site = e.GetProperty("site").GetString(),
                                       profile = e.GetProperty("profile").GetString(), view = e.GetProperty("view").GetString(), insertX = e.GetProperty("insertX").GetDouble(), insertY = e.GetProperty("insertY").GetDouble() };
                    foreach (var p in e.GetProperty("boundary").EnumerateArray()) f.boundary.Add(new Point3d(p.GetProperty("x").GetDouble(), p.GetProperty("y").GetDouble(), 0.0));
                    foreach (var p in e.GetProperty("alignment").EnumerateArray()) f.alignment.Add(new Point3d(p.GetProperty("x").GetDouble(), p.GetProperty("y").GetDouble(), 0.0));
                    feats.Add(f);
                }
            return feats;
        }

        static Point3dCollection ReadPoints(string name)
        {
            var pts = new Point3dCollection();
            foreach (var line in File.ReadAllLines(Path.Combine(W4DIR, "points", "csv", name + ".csv")))
            {
                var c = line.Split(','); if (c.Length < 4) continue;
                pts.Add(new Point3d(double.Parse(c[1], CultureInfo.InvariantCulture), double.Parse(c[2], CultureInfo.InvariantCulture), double.Parse(c[3], CultureInfo.InvariantCulture)));
            }
            return pts;
        }

        static ObjectId FirstStyle(System.Collections.IEnumerable ids, Transaction tr, string prefer)
        {
            ObjectId first = ObjectId.Null;
            foreach (object o in ids)
            {
                ObjectId id = (ObjectId)o; if (first.IsNull) first = id;
                var st = tr.GetObject(id, OpenMode.ForRead) as StyleBase;
                if (st != null && prefer != null && st.Name.IndexOf(prefer, StringComparison.OrdinalIgnoreCase) >= 0) return id;
            }
            return first;
        }

        [CommandMethod("W4BUILD")]
        public static void W4BUILD()
        {
            var doc = Application.DocumentManager.MdiActiveDocument; var db = doc.Database; var ed = doc.Editor; var civil = CivilApplication.ActiveDocument;
            try { civil.Settings.DrawingSettings.UnitZoneSettings.CoordinateSystemCode = "UTM84-40N"; Msg(ed, "\nW4BUILD: coordinate system UTM84-40N."); }
            catch (System.Exception ex) { Msg(ed, "\nW4BUILD: coordinate system not assigned: " + ex.Message); }
            var feats = ReadSpec(); int nS = 0, nA = 0, nP = 0, nV = 0, nF = 0; var t0 = DateTime.Now;
            foreach (var f in feats)
            {
                try
                {
                    using (var tr = db.TransactionManager.StartTransaction())
                    {
                        // ---- surface
                        ObjectId sid = ObjectId.Null;
                        foreach (ObjectId id in civil.GetSurfaceIds()) { var s = (CivilSurface)tr.GetObject(id, OpenMode.ForRead); if (s.Name == f.surface) sid = id; }
                        if (sid.IsNull)
                        {
                            sid = TinSurface.Create(db, f.surface); var tin = (TinSurface)tr.GetObject(sid, OpenMode.ForWrite);
                            tin.Description = f.kind + " " + f.name + ", 1 m corridor on the 0.5 m DEM";
                            tin.AddVertices(ReadPoints(f.name));
                            var ring = new Point3dCollection(); foreach (var p in f.boundary) ring.Add(p);
                            try { tin.BoundariesDefinition.AddBoundaries(ring, 0.5, SurfaceBoundaryType.Outer, false); }
                            catch (System.Exception ex) { Msg(ed, "\nW4BUILD: boundary of " + f.name + " not added: " + ex.Message); }
                            nS++;
                        }
                        // ---- alignment
                        ObjectId aid = ObjectId.Null;
                        foreach (ObjectId id in civil.GetAlignmentIds()) { var a = (Alignment)tr.GetObject(id, OpenMode.ForRead); if (a.Name == f.name) aid = id; }
                        if (aid.IsNull)
                        {
                            var layer = ((LayerTableRecord)tr.GetObject(db.Clayer, OpenMode.ForRead)).Name;
                            var astyle = (StyleBase)tr.GetObject(FirstStyle(civil.Styles.AlignmentStyles, tr, null), OpenMode.ForRead);
                            var aset = (StyleBase)tr.GetObject(FirstStyle(civil.Styles.LabelSetStyles.AlignmentLabelSetStyles, tr, null), OpenMode.ForRead);
                            aid = Alignment.Create(civil, f.name, null, layer, astyle.Name, aset.Name);
                            var al = (Alignment)tr.GetObject(aid, OpenMode.ForWrite); al.Description = f.kind + " " + f.name;
                            for (int i = 0; i + 1 < f.alignment.Count; i++) al.Entities.AddFixedLine(f.alignment[i], f.alignment[i + 1]);
                            nA++;
                        }
                        // ---- existing-ground profile
                        var alr = (Alignment)tr.GetObject(aid, OpenMode.ForRead); bool hasProfile = false, hasView = false;
                        foreach (ObjectId pid in alr.GetProfileIds()) { var pr = (Profile)tr.GetObject(pid, OpenMode.ForRead); if (pr.Name == f.profile) hasProfile = true; }
                        if (!hasProfile)
                        {
                            var pstyle = FirstStyle(civil.Styles.ProfileStyles, tr, "Existing"); var pset = FirstStyle(civil.Styles.LabelSetStyles.ProfileLabelSetStyles, tr, null);
                            Profile.CreateFromSurface(f.profile, aid, sid, db.Clayer, pstyle, pset); nP++;
                        }
                        // ---- profile view + leader
                        foreach (ObjectId vid in alr.GetProfileViewIds()) { var pv0 = (ProfileView)tr.GetObject(vid, OpenMode.ForRead); if (pv0.Name == f.view) hasView = true; }
                        if (!hasView)
                        {
                            ObjectId pvId = ProfileView.Create(aid, new Point3d(f.insertX, f.insertY, 0.0)); var pv = (ProfileView)tr.GetObject(pvId, OpenMode.ForWrite); pv.Name = f.view;
                            if (nV == 0) { try { var st = (ProfileViewStyle)tr.GetObject(pv.StyleId, OpenMode.ForRead); Msg(ed, string.Format("\nW4BUILD: profile view style '{0}', vertical exaggeration {1}", st.Name, st.GraphStyle.VerticalExaggeration)); } catch { } }
                            Leader(db, tr, ed, f.name, f.kind, alr.StartPoint, new Point3d(f.insertX, f.insertY, 0.0)); nV++;
                        }
                        tr.Commit();
                    }
                    Msg(ed, string.Format("\nW4BUILD: {0} done [{1:0} s]", f.name, (DateTime.Now - t0).TotalSeconds));
                }
                catch (System.Exception ex) { nF++; Msg(ed, "\nW4BUILD: " + f.name + " FAILED: " + ex.Message); }
            }
            Msg(ed, string.Format("\nW4BUILD: {0} surfaces, {1} alignments, {2} profiles, {3} views created; {4} features failed [{5:0} s]", nS, nA, nP, nV, nF, (DateTime.Now - t0).TotalSeconds));
        }

        static void Msg(Editor ed, string m) { ed.WriteMessage(m); Log(m.TrimStart('\n')); }

        static void Leader(Database db, Transaction tr, Editor ed, string name, string kind, Point3d at, Point3d text)
        {
            try
            {
                bool isDyke = kind == "dyke"; string layer = isDyke ? "W4-PV-LEADER-DYKES" : "W4-PV-LEADER-CHANNELS"; EnsureLayer(db, tr, layer, (short)(isDyke ? 6 : 1));
                var btr = (BlockTableRecord)tr.GetObject(SymbolUtilityServices.GetBlockModelSpaceId(db), OpenMode.ForWrite);
                var ml = new MLeader(); ml.SetDatabaseDefaults(); ml.Layer = layer; ml.ContentType = ContentType.MTextContent;
                var mt = new MText(); mt.SetDatabaseDefaults(); mt.Contents = "PV " + name + "  <-  alignment " + name; mt.TextHeight = 40.0; ml.MText = mt;
                int li = ml.AddLeaderLine(at); ml.AddFirstVertex(li, at); ml.AddLastVertex(li, text); ml.ArrowSize = 60.0; ml.LandingGap = 10.0; ml.TextHeight = 40.0;
                btr.AppendEntity(ml); tr.AddNewlyCreatedDBObject(ml, true);
            }
            catch (System.Exception ex) { Msg(ed, "\nW4: leader for " + name + " not drawn: " + ex.Message); }
        }

        static void EnsureLayer(Database db, Transaction tr, string name, short colour)
        {
            var lt = (LayerTable)tr.GetObject(db.LayerTableId, OpenMode.ForRead);
            if (lt.Has(name)) return;
            lt.UpgradeOpen(); var ltr = new LayerTableRecord(); ltr.Name = name; ltr.Color = Autodesk.AutoCAD.Colors.Color.FromColorIndex(Autodesk.AutoCAD.Colors.ColorMethod.ByAci, colour);
            lt.Add(ltr); tr.AddNewlyCreatedDBObject(ltr, true);
        }

        [CommandMethod("W4PV")]
        public static void W4PV()
        {
            var doc = Application.DocumentManager.MdiActiveDocument; var db = doc.Database; var ed = doc.Editor; var civil = CivilApplication.ActiveDocument;
            var rows = new List<string[]>();
            foreach (var line in File.ReadAllLines(CSV)) { var f = line.Split(','); if (f.Length >= 4 && f[0] != "name") rows.Add(f); }
            int made = 0, skipped = 0, failed = 0;
            using (var tr = db.TransactionManager.StartTransaction())
            {
                var byName = new Dictionary<string, ObjectId>();
                foreach (ObjectId id in civil.GetAlignmentIds()) { var a = (Alignment)tr.GetObject(id, OpenMode.ForRead); byName[a.Name] = id; }
                foreach (var f in rows)
                {
                    string name = f[0]; double x = double.Parse(f[2], CultureInfo.InvariantCulture), y = double.Parse(f[3], CultureInfo.InvariantCulture);
                    if (!byName.ContainsKey(name)) { Msg(ed, "\nW4PV: no alignment " + name); failed++; continue; }
                    var al = (Alignment)tr.GetObject(byName[name], OpenMode.ForRead); bool exists = false;
                    foreach (ObjectId pvid in al.GetProfileViewIds()) { var pv0 = (ProfileView)tr.GetObject(pvid, OpenMode.ForRead); if (pv0.Name == "PV " + name) exists = true; }
                    if (exists) { skipped++; continue; }
                    try
                    {
                        ObjectId pvId = ProfileView.Create(byName[name], new Point3d(x, y, 0.0)); var pv = (ProfileView)tr.GetObject(pvId, OpenMode.ForWrite); pv.Name = "PV " + name; made++;
                        Leader(db, tr, ed, name, f[1], al.StartPoint, new Point3d(x, y, 0.0));
                    }
                    catch (System.Exception ex) { Msg(ed, "\nW4PV: " + name + " failed: " + ex.Message); failed++; }
                }
                tr.Commit();
            }
            Msg(ed, string.Format("\nW4PV: {0} profile views created, {1} already existed, {2} failed.", made, skipped, failed));
        }

        [CommandMethod("W4PVDEL")]
        public static void W4PVDEL()
        {
            var doc = Application.DocumentManager.MdiActiveDocument; var db = doc.Database; var ed = doc.Editor; var civil = CivilApplication.ActiveDocument; int n = 0, m = 0;
            using (var tr = db.TransactionManager.StartTransaction())
            {
                foreach (ObjectId id in civil.GetAlignmentIds())
                {
                    var al = (Alignment)tr.GetObject(id, OpenMode.ForRead);
                    foreach (ObjectId pvid in al.GetProfileViewIds()) { var pv = (ProfileView)tr.GetObject(pvid, OpenMode.ForWrite); if (pv.Name.StartsWith("PV ")) { pv.Erase(); n++; } }
                }
                var btr = (BlockTableRecord)tr.GetObject(SymbolUtilityServices.GetBlockModelSpaceId(db), OpenMode.ForRead);
                foreach (ObjectId eid in btr) { var ent = tr.GetObject(eid, OpenMode.ForRead) as MLeader; if (ent != null && ent.Layer.StartsWith("W4-PV-LEADER")) { ent.UpgradeOpen(); ent.Erase(); m++; } }
                tr.Commit();
            }
            Msg(ed, string.Format("\nW4PVDEL: {0} profile views and {1} leaders erased.", n, m));
        }
    }
}
