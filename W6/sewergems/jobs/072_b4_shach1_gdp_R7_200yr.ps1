. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Block 04 (engineer, 2026-10-12): the GDP line of SHA-CH1-FP was edited in the W6 drawing at its last two PVIs (7+124: 2.552 ->
# 3.895; 8+043: 0.500 -> -0.700). Model grounds (GDP-Raised of final/Block4_design_points.shp after 27 + 37): SHACH1-12 stays
# 5.810 (a normal point, ground = the bank, the raise shrinks), the outfall SHACH1-O11 drops 3.500 -> 2.300 (fix point, GDP + 3.0).
# R7 = R6 with those grounds under every scenario, a FULL design of 200 yr, export, R7 delivered as new files.
$share = '\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04 11102026'
$stamp = Get-Date -Format yyyyMMdd_HHmm
$work = 'C:\B4Work\run_' + $stamp; New-Item -ItemType Directory -Force $work | Out-Null
$r6 = 'C:\B4Work\run_20261012_1344\SewerGEMS Block 04_R6.stsw'
Copy-Item $r6, "$r6.sqlite" $work -Force
$src = "$work\SewerGEMS Block 04_R6.stsw"; $dst = "$work\SewerGEMS Block 04_R7.stsw"
$out = '\\VBOXSVR\VBOX\bridge\out\b4\run_' + $stamp; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
$scen = [ordered]@{ '2 yr' = 1; '5 yr' = 2050; '10 yr' = 2051; '25 yr' = 2052; '50 yr' = 2053; '100 yr' = 2054; '200 yr' = 2055; '500 yr' = 2056 }
$ground = [ordered]@{ 'SHACH1-12' = 5.810; 'SHACH1-O11' = 2.300 }
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $net = $m.Network
  $nodes = @{}
  foreach ($x in $net.Manholes.Elements()) { if ($ground.Contains($x.Label)) { $nodes[$x.Label] = $x } }
  foreach ($x in $net.Outfalls.Elements()) { if ($ground.Contains($x.Label)) { $nodes[$x.Label] = $x } }
  if ($nodes.Count -ne $ground.Count) { throw ('found ' + $nodes.Count + ' of ' + $ground.Count + ' nodes') }
  foreach ($name in $scen.Keys) {
    $m.SetActiveScenario($m.Scenarios.Element($scen[$name]))
    foreach ($lab in $ground.Keys) {
      $x = $nodes[$lab]; $before = $x.Input.GroundElevation
      $x.Input.GroundElevation = [double]$ground[$lab]
      if (-not $x.Input.SetRimToGroundElevation) { $x.Input.RimElevation = [double]$ground[$lab] }
      if ($name -eq '200 yr') { $log.WriteLine($lab + ': ground ' + $before + ' -> ' + $x.Input.GroundElevation + ' (rim ' + $x.Input.RimElevation + ', invert before the design ' + $x.Input.InvertElevation + ')') }
    }
  }
  $m.SetActiveScenario($m.Scenarios.Element(2055))
  $m.Save()
  $dds = $m.DomainDataSet; $dt = $dds.DomainDataSetType().AlternativeType('Design').Id; $am = $dds.AlternativeManager($dt)
  $log.WriteLine('constraints: min slope ' + $am.SystemRecordField('Design_SystemMinSlope').GetValue(17) + ', max slope ' + $am.SystemRecordField('Design_SystemMaxSlope').GetValue(17) + ' | design flags on: conduits ' + @($net.Conduits.Elements() | Where-Object { $_.Input.DesignConduit }).Count + ' of ' + @($net.Conduits.Elements()).Count)
  $log.WriteLine('######## 200 yr (scenario 2055), full design ' + (Get-Date -Format T))
  [Scen]::DesignUntilStable($m, 2055, 6, $log)
  [B4]::Export($m, $out, '200yr', $log)
  $m.Save(); $m.Close()
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($dst); $net = $m.Network; $m.SetActiveScenario($m.Scenarios.Element(2055))
  $o = @($net.Outfalls.Elements() | Where-Object { $_.Label -eq 'SHACH1-O11' })[0]; $n12 = @($net.Manholes.Elements() | Where-Object { $_.Label -eq 'SHACH1-12' })[0]
  $log.WriteLine('reopened R7, 200 yr: SHACH1-12 ground ' + $n12.Input.GroundElevation + ' invert ' + $n12.Input.InvertElevation + ' | SHACH1-O11 ground ' + $o.Input.GroundElevation + ' invert ' + $o.Input.InvertElevation)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
if ($log.ToString() -notmatch 'FAILED') {
  Copy-Item $dst, "$dst.sqlite" $share -Force
  foreach ($suffix in '.dwh', '.profiles.dwh') { if (Test-Path "$share\SewerGEMS Block 04_R6.stsw$suffix") { Copy-Item "$share\SewerGEMS Block 04_R6.stsw$suffix" "$share\SewerGEMS Block 04_R7.stsw$suffix" -Force } }
  $r7out = "$work\SewerGEMS Block 04_R7.stsw_1_2055-stmc-gvf.out"; if (Test-Path $r7out) { Copy-Item $r7out $share -Force; $log.WriteLine('result file for scenario 2055 delivered') }
  $log.WriteLine('delivered "SewerGEMS Block 04_R7.stsw" with .sqlite, .dwh, .profiles.dwh and the 200 yr result file')
}
[IO.File]::WriteAllText("$out\log.txt", $log.ToString())
$log.ToString()
