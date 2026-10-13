. \\VBOXSVR\VBOX\bridge\lib\load.ps1
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
  @{ label = 'SHACH1-1'; scen = 1; rp = '2'; old = 1059.404687; new = 641.384977 },
  @{ label = 'SHACH1-1'; scen = 2050; rp = '5'; old = 4857.143946; new = 3260.638493 },
  @{ label = 'SHACH1-1'; scen = 2051; rp = '10'; old = 14649.300679; new = 9886.729410 },
  @{ label = 'SHACH1-1'; scen = 2052; rp = '25'; old = 22903.256473; new = 14689.630028 },
  @{ label = 'SHACH1-1'; scen = 2053; rp = '50'; old = 31680.752201; new = 19403.502371 },
  @{ label = 'SHACH1-1'; scen = 2054; rp = '100'; old = 43119.172752; new = 25231.411191 },
  @{ label = 'SHACH1-1'; scen = 2055; rp = '200'; old = 57956.771233; new = 32374.014423 },
  @{ label = 'SHACH1-1'; scen = 2056; rp = '500'; old = 82980.814701; new = 44585.614287 },
  @{ label = 'SHACH1-8'; scen = 1; rp = '2'; old = 1049.340007; new = 692.520614 },
  @{ label = 'SHACH1-8'; scen = 2050; rp = '5'; old = 4847.820874; new = 3362.026901 },
  @{ label = 'SHACH1-8'; scen = 2051; rp = '10'; old = 14675.927937; new = 10240.264538 },
  @{ label = 'SHACH1-8'; scen = 2052; rp = '25'; old = 22966.610985; new = 15239.090927 },
  @{ label = 'SHACH1-8'; scen = 2053; rp = '50'; old = 31832.358065; new = 20161.637636 },
  @{ label = 'SHACH1-8'; scen = 2054; rp = '100'; old = 43476.415920; new = 26263.764843 },
  @{ label = 'SHACH1-8'; scen = 2055; rp = '200'; old = 58651.163525; new = 33777.454593 },
  @{ label = 'SHACH1-8'; scen = 2056; rp = '500'; old = 84428.009743; new = 46423.566117 },
  @{ label = 'SHACH1-9'; scen = 1; rp = '2'; old = 1046.973924; new = 711.555220 },
  @{ label = 'SHACH1-9'; scen = 2050; rp = '5'; old = 4849.869125; new = 3462.850275 },
  @{ label = 'SHACH1-9'; scen = 2051; rp = '10'; old = 14699.800652; new = 10374.778104 },
  @{ label = 'SHACH1-9'; scen = 2052; rp = '25'; old = 23001.501875; new = 15443.174386 },
  @{ label = 'SHACH1-9'; scen = 2053; rp = '50'; old = 31910.721310; new = 20446.132591 },
  @{ label = 'SHACH1-9'; scen = 2054; rp = '100'; old = 43633.707446; new = 26651.555198 },
  @{ label = 'SHACH1-9'; scen = 2055; rp = '200'; old = 58922.803941; new = 34293.366559 },
  @{ label = 'SHACH1-9'; scen = 2056; rp = '500'; old = 85005.757691; new = 47153.944054 },
  @{ label = 'SHACH1-11'; scen = 1; rp = '2'; old = 1035.849804; new = 748.529676 },
  @{ label = 'SHACH1-11'; scen = 2050; rp = '5'; old = 4828.397807; new = 3639.035147 },
  @{ label = 'SHACH1-11'; scen = 2051; rp = '10'; old = 14685.145065; new = 10618.873080 },
  @{ label = 'SHACH1-11'; scen = 2052; rp = '25'; old = 22916.146326; new = 15782.760222 },
  @{ label = 'SHACH1-11'; scen = 2053; rp = '50'; old = 31842.705262; new = 20924.681640 },
  @{ label = 'SHACH1-11'; scen = 2054; rp = '100'; old = 43601.429840; new = 27300.356255 },
  @{ label = 'SHACH1-11'; scen = 2055; rp = '200'; old = 58996.223133; new = 35173.902459 },
  @{ label = 'SHACH1-11'; scen = 2056; rp = '500'; old = 85449.557107; new = 48383.247602 }
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
