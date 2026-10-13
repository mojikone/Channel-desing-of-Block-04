. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Block 04 W7 (engineer, 2026-10-12): READ-ONLY probe on a guest copy of R8. Where do the per-scenario flows live and in what
# unit? The inventory says alternative type SystemFlows (8 alternatives 2035..2042, one per scenario), field SystemFlows_KnownFlow.
# Prints, for the four SHA-CH1-FP nodes fed by the Shafan line (SHACH1-1/-8/-9/-11) and two controls, the stored value under every
# System Flows alternative (field manager = stored unit) and any typed Input property with "Flow" in its name (display unit).
$work = 'C:\B4Work\probe_' + (Get-Date -Format yyyyMMdd_HHmm); New-Item -ItemType Directory -Force $work | Out-Null
$r8 = 'C:\B4Work\run_20261012_1608\SewerGEMS Block 04_R8.stsw'
Copy-Item $r8, "$r8.sqlite" $work -Force
$src = "$work\SewerGEMS Block 04_R8.stsw"
$log = New-Object IO.StringWriter
$want = @('SHACH1-1', 'SHACH1-8', 'SHACH1-9', 'SHACH1-11', 'HAWCH1-1', 'SAKCH1-1')
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $net = $m.Network; $dds = $m.DomainDataSet; $fm = $dds.FieldManager; $dst = $dds.DomainDataSetType()
  $sfT = $dst.AlternativeType('SystemFlows').Id; $mhT = $dst.DomainElementType('Manhole').Id
  $log.WriteLine('SystemFlows alternative type id ' + $sfT + ', manhole element type id ' + $mhT)
  $am = $dds.AlternativeManager($sfT)
  foreach ($a in $am.Elements()) { $log.WriteLine('  alternative ' + $a.Id + " '" + $a.Label + "'") }
  foreach ($s in $dds.ScenarioManager.Elements()) { $log.WriteLine('  scenario ' + $s.Id + " '" + $s.Label + "' -> system flows alternative " + $s.AlternativeID($sfT)) }
  $nodes = @{}
  foreach ($x in $net.Manholes.Elements()) { if ($want -contains $x.Label) { $nodes[$x.Label] = $x } }
  $log.WriteLine('nodes found: ' + ($nodes.Keys -join ', '))
  $x0 = $nodes['SHACH1-1']
  $log.WriteLine('typed Input members with Flow in the name: ' + (($x0.Input | Get-Member | Where-Object { $_.Name -match 'Flow' } | ForEach-Object { $_.Name + ':' + $_.MemberType }) -join ' | '))
  foreach ($s in $dds.ScenarioManager.Elements()) {
    $altId = $s.AlternativeID($sfT)
    $f = $fm.AlternativeField('SystemFlows_KnownFlow', $sfT, $mhT, $altId)
    $log.WriteLine('scenario ' + $s.Label + ' (alt ' + $altId + '): field type ' + $f.GetType().Name + ', unit ' + $(try { $f.Unit } catch { '?' }) + ', is IEditField ' + ($f -is [Haestad.Domain.IEditField]))
    foreach ($lab in $want) {
      if ($nodes.ContainsKey($lab)) { $v = $f.GetValue($nodes[$lab].Id); $log.WriteLine('   ' + $lab + ' id ' + $nodes[$lab].Id + ' stored KnownFlow = ' + $v) }
    }
    $vals = $f.GetValues(); $n = 0; $sum = 0.0
    foreach ($e in $vals.GetEnumerator()) { $d = 0.0; if ($e.Value -ne $null -and [double]::TryParse([string]$e.Value, [ref]$d) -and $d -ne 0) { $n++; $sum += $d } }
    $log.WriteLine('   manholes with a non-zero known flow: ' + $n + ', sum ' + $sum)
  }
  $m.SetActiveScenario($m.Scenarios.Element(2055))
  foreach ($lab in $want) { if ($nodes.ContainsKey($lab)) { $i = $nodes[$lab].Input; $log.WriteLine('200 yr typed: ' + $lab + ' ground ' + $i.GroundElevation + ' | ' + (($i | Get-Member -MemberType Property | Where-Object { $_.Name -match 'Flow' } | ForEach-Object { $_.Name + '=' + $i.($_.Name) }) -join ' ')) } }
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
