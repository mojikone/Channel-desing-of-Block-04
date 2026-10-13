. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Block 04: the fields of a profile (a GenericSelectionSet under ProfileManager) and the element list of the Rustaq profile
# "Ais-CH1-FP", read through the collection field; then the element counts of the 43 profiles the Block 04 model inherited from
# Rustaq. Read-only on the guest copies; nothing saved.
$log = New-Object IO.StringWriter
function ListFields($pm, $title) {
  $log.WriteLine("== $title SupportedFields()")
  foreach ($f in $pm.SupportedFields()) { $log.WriteLine(('   {0} | {1} | {2}' -f $f.Name, $f.Label, $f.GetType().Name)) }
}
function Members($coll, $id) {
  # the element list of a selection set: the collection field's list manager -> DataView rows
  $out = @()
  try {
    $lm = $coll.GetValue($id); $dv = $lm.GetType().GetProperty('DataView').GetValue($lm, $null)
    $cols = @(); foreach ($c in $dv.Table.Columns) { $cols += $c.ColumnName }
    $out += ('columns: ' + ($cols -join ', '))
    foreach ($r in $dv) { $vals = @(); foreach ($c in $cols) { $vals += ($c + '=' + $r[$c]) }; $out += ('   ' + ($vals -join ' | ')) }
  } catch { $out += ('! ' + $_.Exception.Message) }
  return $out
}
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\B4Work\rustaq\SewerGEMS Rustaq.stsw')
  $dds = $m.DomainDataSet; $pm = $dds.ProfileManager
  ListFields $pm 'Rustaq ProfileManager'
  $p = @($pm.Elements() | Where-Object { $_.Label -eq 'Ais-CH1-FP' })[0]; $log.WriteLine('Ais-CH1-FP id ' + $p.Id)
  foreach ($f in $pm.SupportedFields()) {
    $v = $null; try { $v = $f.GetValue($p.Id) } catch { $v = '! ' + $_.Exception.Message }
    if ($v -is [string] -or $v -is [int] -or $v -is [double] -or $v -is [bool] -or $v -eq $null) { $log.WriteLine(('   {0} = {1}' -f $f.Name, $v)) }
    else { $log.WriteLine(('   {0} -> {1}' -f $f.Name, $v.GetType().FullName)); foreach ($line in (Members $f $p.Id)) { $log.WriteLine('      ' + $line) } }
  }
  $m.Close()
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\B4Work\inv_20261011_1720\SewerGEMS Block 04.stsw')
  $dds = $m.DomainDataSet; $pm = $dds.ProfileManager
  $log.WriteLine('== Block 04: the inherited profiles and their member counts')
  $coll = $null; foreach ($f in $pm.SupportedFields()) { if ($f.Name -match 'Element' -or $f.Name -match 'Collection' -or $f.Name -match 'Member') { $coll = $f } }
  foreach ($p in $pm.Elements()) {
    $n = '?'; try { $lm = $coll.GetValue($p.Id); $dv = $lm.GetType().GetProperty('DataView').GetValue($lm, $null); $n = $dv.Count } catch { $n = '! ' + $_.Exception.Message }
    $log.WriteLine(('   {0} "{1}" members={2}' -f $p.Id, $p.Label, $n))
  }
  $log.WriteLine('collection field used: ' + $(if ($coll) { $coll.Name } else { 'none' }))
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
