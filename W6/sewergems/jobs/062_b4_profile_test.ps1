. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$log = New-Object IO.StringWriter
function Dump($obj, $title, $max) {
  $log.WriteLine("== $title : " + $obj.GetType().FullName); $k = 0
  foreach ($mi in ($obj.GetType().GetMembers() | Sort-Object Name)) {
    if ($mi.MemberType -eq 'Method' -and $mi.Name -match '^(get_|set_|add_|remove_)') { continue }
    if ($mi.DeclaringType -eq [object]) { continue }
    $sig = ''; if ($mi.MemberType -eq 'Method') { $sig = '(' + (($mi.GetParameters() | ForEach-Object { $_.ParameterType.Name + ' ' + $_.Name }) -join ', ') + ') : ' + $mi.ReturnType.Name } elseif ($mi.MemberType -eq 'Property') { $sig = ' : ' + $mi.PropertyType.Name }
    $log.WriteLine('   ' + $mi.MemberType + ' ' + $mi.Name + $sig); $k++; if ($k -ge $max) { $log.WriteLine('   ...'); break }
  }
}
function MakeProfile($pm, $label, $path) {
  $labelF = $pm.SelectionSetField('Label'); $idsF = $pm.SelectionSetField('SelectionSetElementIDs')
  $existing = @($pm.Elements() | Where-Object { $_.Label -eq $label })
  foreach ($e in $existing) { $pm.Delete($e.Id); $log.WriteLine('  replaced the existing profile "' + $label + '" (' + $e.Id + ')') }
  $new = $pm.Add(); $labelF.SetValue($new, $label)
  $coll = New-Object Haestad.Support.Support.HmIDCollection
  foreach ($i in $path) { [void]$coll.Add([int]$i) }
  $idsF.SetValue($new, $coll)
  $b = @(); foreach ($i in $idsF.GetValue($new)) { $b += [int]$i }
  $log.WriteLine('  profile ' + $new + ' "' + $labelF.GetValue($new) + '": ' + $b.Count + ' elements')
  return $new
}

# Block 04: (1) the element-ID collection of the Rustaq profile "Ais-CH1-FP" (order, count, element types); (2) TEST on a scratch
# copy of the Block 04 model: create the profile "HAW-CH1-FP" as a selection set with the channel's node/conduit path, save, reopen,
# read back. The scratch copy stays in the guest; nothing reaches the share.
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\B4Work\rustaq\SewerGEMS Rustaq.stsw')
  $dds = $m.DomainDataSet; $pm = $dds.ProfileManager; $f = $pm.SelectionSetField('SelectionSetElementIDs')
  $p = @($pm.Elements() | Where-Object { $_.Label -eq 'Ais-CH1-FP' })[0]
  $ids = $f.GetValue($p.Id); Dump $ids 'HmIDCollection' 40
  $arr = @(); foreach ($i in $ids) { $arr += [int]$i }
  $log.WriteLine('Ais-CH1-FP: ' + $arr.Count + ' ids: ' + ($arr -join ' '))
  $labels = @(); foreach ($i in $arr) { $l = '?'; try { $l = $dds.Element($i).Label + '(' + $dds.Element($i).ModelingElementType.Name + ')' } catch {}; $labels += $l }
  $log.WriteLine('labels: ' + ($labels -join ' > '))
  $m.Close()
  $work = 'C:\B4Work\profile_test'; New-Item -ItemType Directory -Force $work | Out-Null
  Copy-Item 'C:\B4Work\inv_20261011_1720\SewerGEMS Block 04.stsw', 'C:\B4Work\inv_20261011_1720\SewerGEMS Block 04.stsw.sqlite' $work -Force
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$work\SewerGEMS Block 04.stsw")
  $pm = $m.DomainDataSet.ProfileManager
  [void](MakeProfile $pm 'HAW-CH1-FP' @(1580, 1942, 1691, 2007, 1730, 1840, 1741, 2014, 1752, 1809, 1763, 1821, 1774, 1953, 2023))
  $m.Save(); $m.Close()
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$work\SewerGEMS Block 04.stsw")
  $pm = $m.DomainDataSet.ProfileManager; $idsF = $pm.SelectionSetField('SelectionSetElementIDs')
  $q = @($pm.Elements() | Where-Object { $_.Label -eq 'HAW-CH1-FP' })
  $log.WriteLine('after reopen: ' + $q.Count + ' profile(s) named HAW-CH1-FP; total profiles ' + @($pm.Elements()).Count)
  if ($q.Count -gt 0) { $b = @(); foreach ($i in $idsF.GetValue($q[0].Id)) { $b += [int]$i }; $log.WriteLine('   ids persisted: ' + $b.Count + ' : ' + ($b -join ' ')) }
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
