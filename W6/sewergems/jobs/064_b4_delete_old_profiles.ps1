. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Block 04 (engineer, 2026-10-11 night): delete from R2 the 43 profiles inherited from the Rustaq model (their elements do not
# exist in Block 04); keep the 37 channel profiles. On the guest copy of R2, saved, verified after reopen, then R2 .stsw + .sqlite
# copied to the share again (R2 is Claude's revision, the engineer's file is not touched).
$share = '\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04 11102026'
$dst = 'C:\B4Work\run_20261011_1721\SewerGEMS Block 04_R2.stsw'
$keep = @('HAW-CH1-FP','HAW-CH2-SS','HAW-CH3-SS','HAW-CH4-SS','HAW-CH5-SS','HAW-CH6-SS','HAW-CH7-SS','SAK-CH1-FP','SAK-CH2-FP','SAK-CH3-SM','SAK-CH4-SS','SAK-CH5-SS','SAR-CH1-FP','SAR-CH2-SM','SAR-CH3-SS','SAR-CH4-SS','SHA-CH1-FP','SHA-CH10-SS','SHA-CH11-SS','SHA-CH12-SS','SHA-CH13-SS','SHA-CH14-SS','SHA-CH15-SS','SHA-CH16-SS','SHA-CH17-SS','SHA-CH18-SS','SHA-CH19-SS','SHA-CH2-SM','SHA-CH20-SS','SHA-CH21-SS','SHA-CH3-SM','SHA-CH4-SM','SHA-CH5-SM','SHA-CH6-SM','SHA-CH7-SM','SHA-CH8-SS','SHA-CH9-SS')
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($dst)
  $pm = $m.DomainDataSet.ProfileManager
  $log.WriteLine('profiles before: ' + @($pm.Elements()).Count)
  $gone = @()
  foreach ($p in @($pm.Elements())) { if ($keep -notcontains $p.Label) { $gone += ($p.Id.ToString() + ' "' + $p.Label + '"'); $pm.Delete($p.Id) } }
  $log.WriteLine('deleted ' + $gone.Count + ': ' + ($gone -join ', '))
  $log.WriteLine('profiles after: ' + @($pm.Elements()).Count)
  $m.Save(); $m.Close()
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($dst)
  $pm = $m.DomainDataSet.ProfileManager; $names = @(); foreach ($p in $pm.Elements()) { $names += $p.Label }
  $log.WriteLine('after reopen: ' + $names.Count + ' profiles: ' + ($names -join ', '))
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
if ($log.ToString() -notmatch 'FAILED') { Copy-Item $dst, "$dst.sqlite" $share -Force; $log.WriteLine('R2 .stsw + .sqlite copied to the share again') }
$log.ToString()
