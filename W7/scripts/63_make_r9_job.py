"""Step 63 (W7) - write the bridge job that makes revision R9: R8 copied in the guest, the known flows of every design point whose
flow moved (step 62: W7/final against W6/final, the eight model scenarios) rewritten in the scenario's own System Flows
alternative (field SystemFlows_KnownFlow, STORED IN ft3/s: probe 074b of 2026-10-12 read 1059.405 for 29.999 m3/s), each old
value checked before it is replaced, then a full design of all eight scenarios, the exports, and R9 delivered to the share as
NEW files. The job is written to W7/sewergems/jobs/075_b4_flows_R9_all.ps1 and must be dropped into D:/VBOX/bridge/jobs by hand.
    python 63_make_r9_job.py"""
import os, io, geopandas as gpd
HERE = os.path.dirname(os.path.abspath(__file__)); W7 = os.path.dirname(HERE); CB = os.path.dirname(W7)
CFS = 35.314666721
SCEN = [("2", 1), ("5", 2050), ("10", 2051), ("25", 2052), ("50", 2053), ("100", 2054), ("200", 2055), ("500", 2056)]
old = gpd.read_file(os.path.join(CB, "W6", "final", "Block4_design_points.shp")).set_index("SGLabel")
new = gpd.read_file(os.path.join(W7, "final", "Block4_design_points.shp")).set_index("SGLabel")
rows = []
for lab in new.index:
    for rp, sid in SCEN:
        a, b = float(old.loc[lab, "Q" + rp] or 0), float(new.loc[lab, "Q" + rp] or 0)
        if abs(a - b) > 0.0005: rows.append((lab, sid, rp, a, b))
assert rows, "no flow changed between W6/final and W7/final"
labels = sorted({r[0] for r in rows}); print("nodes with new flows:", labels, "| rows:", len(rows))
ps_rows = ",\n".join("  @{ label = '%s'; scen = %d; rp = '%s'; old = %.6f; new = %.6f }" % (lab, sid, rp, a * CFS, b * CFS) for lab, sid, rp, a, b in rows)
job = r'''. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Block 04 W7 (engineer, 2026-10-12): revision R9 = R8 with the design flows of Basin 6 (the Shafan 08 dam and its full catchment in
# the channel hydrology) at the nodes listed below, written into each scenario's System Flows alternative (SystemFlows_KnownFlow,
# stored in ft3/s), every old value checked first; then a FULL design of all eight scenarios, the exports, R9 delivered as new files.
# Written by W7/scripts/63_make_r9_job.py.
$share = '\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04 11102026'
$stamp = Get-Date -Format yyyyMMdd_HHmm
$work = 'C:\B4Work\run_' + $stamp; New-Item -ItemType Directory -Force $work | Out-Null
$r8 = 'C:\B4Work\run_20261012_1608\SewerGEMS Block 04_R8.stsw'
Copy-Item $r8, "$r8.sqlite" $work -Force
$src = "$work\SewerGEMS Block 04_R8.stsw"; $dst = "$work\SewerGEMS Block 04_R9.stsw"
$out = '\\VBOXSVR\VBOX\bridge\out\b4\run_' + $stamp; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
$scen = [ordered]@{ '2 yr' = 1; '5 yr' = 2050; '10 yr' = 2051; '25 yr' = 2052; '50 yr' = 2053; '100 yr' = 2054; '200 yr' = 2055; '500 yr' = 2056 }
$flows = @(
__ROWS__
)
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $net = $m.Network; $dds = $m.DomainDataSet; $fm = $dds.FieldManager; $dst0 = $dds.DomainDataSetType()
  $sfT = $dst0.AlternativeType('SystemFlows').Id; $mhT = $dst0.DomainElementType('Manhole').Id
  $nodes = @{}
  foreach ($x in $net.Manholes.Elements()) { $nodes[$x.Label] = $x }
  $byScen = @{}
  foreach ($s in $dds.ScenarioManager.Elements()) { $byScen[[int]$s.Id] = $s }
  $n = 0
  foreach ($r in $flows) {
    if (-not $nodes.ContainsKey($r.label)) { throw ('node not a manhole: ' + $r.label) }
    $s = $byScen[[int]$r.scen]; $altId = $s.AlternativeID($sfT)
    $f = $fm.AlternativeField('SystemFlows_KnownFlow', $sfT, $mhT, $altId)
    $id = $nodes[$r.label].Id; $cur = [double]$f.GetValue($id)
    if ([math]::Abs($cur - $r.old) -gt [math]::Max(0.001 * [math]::Abs($r.old), 0.05)) { throw ('stored flow of ' + $r.label + ' in ' + $s.Label + ' is ' + $cur + ' ft3/s, expected ' + $r.old) }
    $f.SetValue($id, [double]$r.new); $back = [double]$f.GetValue($id); $n++
    $log.WriteLine($r.label + ' ' + $s.Label + ' (alt ' + $altId + '): known flow ' + [math]::Round($cur / 35.314666721, 3) + ' -> ' + [math]::Round($back / 35.314666721, 3) + ' m3/s (stored ' + $cur + ' -> ' + $back + ' ft3/s)')
    if ([math]::Abs($back - $r.new) -gt 0.01) { throw ('read-back mismatch on ' + $r.label) }
  }
  $log.WriteLine('known flows rewritten: ' + $n)
  $m.SetActiveScenario($m.Scenarios.Element(2055)); $m.Save()
  $dt = $dst0.AlternativeType('Design').Id; $am = $dds.AlternativeManager($dt)
  $log.WriteLine('constraints: min slope ' + $am.SystemRecordField('Design_SystemMinSlope').GetValue(17) + ', max slope ' + $am.SystemRecordField('Design_SystemMaxSlope').GetValue(17) + ' | design flags on: conduits ' + @($net.Conduits.Elements() | Where-Object { $_.Input.DesignConduit }).Count + ' of ' + @($net.Conduits.Elements()).Count)
  foreach ($name in $scen.Keys) {
    $id = $scen[$name]; $tag = $name -replace ' ', ''
    $log.WriteLine("######## $name (scenario $id), full design " + (Get-Date -Format T))
    [Scen]::DesignUntilStable($m, $id, 6, $log)
    [B4]::Export($m, $out, $tag, $log)
    $m.Save()
  }
  $m.Close()
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($dst); $net = $m.Network; $m.SetActiveScenario($m.Scenarios.Element(2055))
  $n1 = @($net.Manholes.Elements() | Where-Object { $_.Label -eq 'SHACH1-1' })[0]
  $log.WriteLine('reopened R9, 200 yr: SHACH1-1 ground ' + $n1.Input.GroundElevation + ' invert ' + $n1.Input.InvertElevation)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
if ($log.ToString() -notmatch 'FAILED') {
  Copy-Item $dst, "$dst.sqlite" $share -Force
  foreach ($suffix in '.dwh', '.profiles.dwh') { if (Test-Path "$share\SewerGEMS Block 04_R8.stsw$suffix") { Copy-Item "$share\SewerGEMS Block 04_R8.stsw$suffix" "$share\SewerGEMS Block 04_R9.stsw$suffix" -Force } }
  foreach ($id in $scen.Values) { $f = "$work\SewerGEMS Block 04_R9.stsw_1_$id-stmc-gvf.out"; if (Test-Path $f) { Copy-Item $f $share -Force; $log.WriteLine('result file for scenario ' + $id + ' delivered') } }
  $log.WriteLine('delivered "SewerGEMS Block 04_R9.stsw" with .sqlite, .dwh, .profiles.dwh and the eight result files')
}
[IO.File]::WriteAllText("$out\log.txt", $log.ToString())
$log.ToString()
'''.replace("__ROWS__", ps_rows)
out = os.path.join(W7, "sewergems", "jobs", "075_b4_flows_R9_all.ps1")
io.open(out, "w", encoding="utf-8", newline="\r\n").write(job); print("written", out)
