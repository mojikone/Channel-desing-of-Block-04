. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Block 04 (engineer, 2026-10-12): ten Road-OQ fix points withdrawn (HAWCH1-5, HAWCH2-8, HAWCH5-7, SAKCH2-7, SARCH1-12, SHACH1-11,
# SHACH14-3, SHACH15-5, SHACH3-11, SHACH7-8): their model ground becomes GDP + the wadi raise instead of GDP + 2.5 (the values below
# are the GDP-Raised of final/Block4_design_points.shp after 37 with inputs/fix_removed.json). R6 = R5 (min slope 0.001, max 0.03)
# with those grounds written under every return-period scenario, a FULL design of 200 yr, export, R6 delivered as new files.
$share = '\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04 11102026'
$stamp = Get-Date -Format yyyyMMdd_HHmm
$work = 'C:\B4Work\run_' + $stamp; New-Item -ItemType Directory -Force $work | Out-Null
$r5 = 'C:\B4Work\run_20261012_1119\SewerGEMS Block 04_R5.stsw'
Copy-Item $r5, "$r5.sqlite" $work -Force
$src = "$work\SewerGEMS Block 04_R5.stsw"; $dst = "$work\SewerGEMS Block 04_R6.stsw"
$out = '\\VBOXSVR\VBOX\bridge\out\b4\run_' + $stamp; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
$scen = [ordered]@{ '2 yr' = 1; '5 yr' = 2050; '10 yr' = 2051; '25 yr' = 2052; '50 yr' = 2053; '100 yr' = 2054; '200 yr' = 2055; '500 yr' = 2056 }
$ground = [ordered]@{ 'HAWCH1-5' = 6.330; 'HAWCH2-8' = 7.236; 'HAWCH5-7' = 7.280; 'SAKCH2-7' = 4.507; 'SARCH1-12' = 10.660; 'SHACH1-11' = 6.389; 'SHACH14-3' = 12.510; 'SHACH15-5' = 14.350; 'SHACH3-11' = 11.660; 'SHACH7-8' = 9.710 }
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $net = $m.Network
  $nodes = @{}
  foreach ($x in $net.Manholes.Elements()) { if ($ground.Contains($x.Label)) { $nodes[$x.Label] = $x } }
  if ($nodes.Count -ne $ground.Count) { throw ('found ' + $nodes.Count + ' of ' + $ground.Count + ' nodes as manholes') }
  foreach ($name in $scen.Keys) {
    $m.SetActiveScenario($m.Scenarios.Element($scen[$name]))
    foreach ($lab in $ground.Keys) {
      $x = $nodes[$lab]; $before = $x.Input.GroundElevation
      $x.Input.GroundElevation = [double]$ground[$lab]
      if (-not $x.Input.SetRimToGroundElevation) { $x.Input.RimElevation = [double]$ground[$lab] }
      if ($name -eq '200 yr') { $log.WriteLine($lab + ': ground ' + $before + ' -> ' + $x.Input.GroundElevation + ' (rim ' + $x.Input.RimElevation + ', rim follows ground ' + $x.Input.SetRimToGroundElevation + ')') }
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
  $chk = @($net.Manholes.Elements() | Where-Object { $ground.Contains($_.Label) } | ForEach-Object { $_.Label + '=' + $_.Input.GroundElevation })
  $log.WriteLine('reopened R6, 200 yr grounds: ' + ($chk -join ' '))
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
if ($log.ToString() -notmatch 'FAILED') {
  Copy-Item $dst, "$dst.sqlite" $share -Force
  foreach ($suffix in '.dwh', '.profiles.dwh') { if (Test-Path "$share\SewerGEMS Block 04_R5.stsw$suffix") { Copy-Item "$share\SewerGEMS Block 04_R5.stsw$suffix" "$share\SewerGEMS Block 04_R6.stsw$suffix" -Force } }
  $r6out = "$work\SewerGEMS Block 04_R6.stsw_1_2055-stmc-gvf.out"; if (Test-Path $r6out) { Copy-Item $r6out $share -Force; $log.WriteLine('result file for scenario 2055 delivered') }
  $log.WriteLine('delivered "SewerGEMS Block 04_R6.stsw" with .sqlite, .dwh, .profiles.dwh and the 200 yr result file')
}
[IO.File]::WriteAllText("$out\log.txt", $log.ToString())
$log.ToString()
