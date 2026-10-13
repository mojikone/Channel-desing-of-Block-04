. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Block 04 (engineer, 2026-10-12): revision R4 = R3 with the design slope constraints changed to min 0.002 and max 0.03 m/m
# (were 0.0003 and 0.02), a FULL design of the 200 yr scenario only (all design flags on, as his model has them), export,
# R4 delivered to the share as new files with that scenario's result file only; the other return periods wait for his approval.
$share = '\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04 11102026'
$stamp = Get-Date -Format yyyyMMdd_HHmm
$work = 'C:\B4Work\run_' + $stamp; New-Item -ItemType Directory -Force $work | Out-Null
$r3 = 'C:\B4Work\run_20261012_0031\SewerGEMS Block 04_R3.stsw'
Copy-Item $r3, "$r3.sqlite" $work -Force
$src = "$work\SewerGEMS Block 04_R3.stsw"; $dst = "$work\SewerGEMS Block 04_R4.stsw"
$out = '\\VBOXSVR\VBOX\bridge\out\b4\run_' + $stamp; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $dds = $m.DomainDataSet; $dst_ = $dds.DomainDataSetType()
  $dt = $dst_.AlternativeType('Design').Id; $am = $dds.AlternativeManager($dt)
  $m.SetActiveScenario($m.Scenarios.Element(2055))
  $altId = 17
  foreach ($pair in @(@('Design_SystemMinSlope', 0.002), @('Design_SystemMaxSlope', 0.03))) {
    $f = $am.SystemRecordField($pair[0]); $before = $f.GetValue($altId)
    $f.SetValue($altId, [double]$pair[1])
    $log.WriteLine($pair[0] + ': ' + $before + ' -> ' + $f.GetValue($altId))
  }
  $m.Save()
  $net = $m.Network
  $log.WriteLine('design flags on: conduits ' + @($net.Conduits.Elements() | Where-Object { $_.Input.DesignConduit }).Count + ' of ' + @($net.Conduits.Elements()).Count + ', nodes ' + (@($net.Manholes.Elements() | Where-Object { $_.Input.DesignStructureElement }).Count + @($net.Outfalls.Elements() | Where-Object { $_.Input.DesignStructureElement }).Count))
  $log.WriteLine('######## 200 yr (scenario 2055), full design ' + (Get-Date -Format T))
  [Scen]::DesignUntilStable($m, 2055, 6, $log)
  [B4]::Export($m, $out, '200yr', $log)
  $m.Save(); $m.Close()
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($dst); $am = $m.DomainDataSet.AlternativeManager($dt)
  $log.WriteLine('reopened R4: min slope ' + $am.SystemRecordField('Design_SystemMinSlope').GetValue($altId) + ', max slope ' + $am.SystemRecordField('Design_SystemMaxSlope').GetValue($altId))
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
if ($log.ToString() -notmatch 'FAILED') {
  Copy-Item $dst, "$dst.sqlite" $share -Force
  foreach ($suffix in '.dwh', '.profiles.dwh') { if (Test-Path "$share\SewerGEMS Block 04_R3.stsw$suffix") { Copy-Item "$share\SewerGEMS Block 04_R3.stsw$suffix" "$share\SewerGEMS Block 04_R4.stsw$suffix" -Force } }
  $r4out = "$work\SewerGEMS Block 04_R4.stsw_1_2055-stmc-gvf.out"; if (Test-Path $r4out) { Copy-Item $r4out $share -Force; $log.WriteLine('result file for scenario 2055 delivered') }
  $log.WriteLine('delivered "SewerGEMS Block 04_R4.stsw" with .sqlite, .dwh, .profiles.dwh and the 200 yr result file (the other scenarios have no results in R4 yet)')
}
[IO.File]::WriteAllText("$out\log.txt", $log.ToString())
$log.ToString()
