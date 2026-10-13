. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Block 04 (2026-10-11 night): the profile "SHA-CH13-SS" in R3 still lists the deleted manhole SHACH13-2 (1682); rewrite its
# element path as SHACH13-1 (1681) > SHACH13-C1 (1984) > SHACH13-O15 (2105), save, verify after reopen, deliver R3 again.
$share = '\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04 11102026'
$dst = 'C:\B4Work\run_20261012_0031\SewerGEMS Block 04_R3.stsw'
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($dst)
  $net = $m.Network
  $o = @($net.Outfalls.Elements() | Where-Object { $_.Label -eq 'SHACH13-O15' })[0]
  $c = @($net.Conduits.Elements() | Where-Object { $_.Label -eq 'SHACH13-C1' })[0]
  $up = @($net.Manholes.Elements() | Where-Object { $_.Label -eq 'SHACH13-1' })[0]
  if (-not $o -or -not $c -or -not $up) { throw 'SHACH13 elements not found in R3' }
  $pm = $m.DomainDataSet.ProfileManager
  $labelF = $pm.SelectionSetField('Label'); $idsF = $pm.SelectionSetField('SelectionSetElementIDs')
  $prof = @($pm.Elements() | Where-Object { $_.Label -eq 'SHA-CH13-SS' })[0]
  if (-not $prof) { throw 'profile SHA-CH13-SS not found' }
  $before = @(); foreach ($i in $idsF.GetValue($prof.Id)) { $before += [int]$i }
  $coll = New-Object Haestad.Support.Support.HmIDCollection
  foreach ($i in @($up.Id, $c.Id, $o.Id)) { [void]$coll.Add([int]$i) }
  $idsF.SetValue($prof.Id, $coll)
  $after = @(); foreach ($i in $idsF.GetValue($prof.Id)) { $after += [int]$i }
  $log.WriteLine('profile SHA-CH13-SS (' + $prof.Id + '): ' + ($before -join ' > ') + '  ->  ' + ($after -join ' > ') + '  = ' + $up.Label + ' > ' + $c.Label + ' > ' + $o.Label)
  $m.Save(); $m.Close()
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($dst); $pm = $m.DomainDataSet.ProfileManager; $idsF = $pm.SelectionSetField('SelectionSetElementIDs')
  $prof = @($pm.Elements() | Where-Object { $_.Label -eq 'SHA-CH13-SS' })[0]; $chk = @(); foreach ($i in $idsF.GetValue($prof.Id)) { $chk += [int]$i }
  $log.WriteLine('after reopen: ' + ($chk -join ' > ') + ' | profiles: ' + @($pm.Elements()).Count)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
if ($log.ToString() -notmatch 'FAILED') { Copy-Item $dst, "$dst.sqlite" $share -Force; $log.WriteLine('R3 .stsw + .sqlite delivered again') }
$log.ToString()
