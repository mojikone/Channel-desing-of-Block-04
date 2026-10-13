. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Block 04 (engineer, 2026-10-11 night): READ-ONLY probe of the API members needed to rebuild SHACH13-2 as the outfall SHACH13-O15
# and to scope the design to SHA-CH13-SS: the outfall manager (Create?), an element's Delete, the outfall and conduit inputs
# (SetPoint, elevations, StopNode writable?), an alternative field's setters, the element type ids, the design field names.
# Opens the guest copy of R2 and closes it without saving.
$log = New-Object IO.StringWriter
function Dump($obj, $title, $max) {
  $log.WriteLine("== $title : " + $obj.GetType().FullName); $k = 0
  foreach ($mi in ($obj.GetType().GetMembers() | Sort-Object Name)) {
    if ($mi.MemberType -eq 'Method' -and $mi.Name -match '^(get_|set_|add_|remove_)') { continue }
    if ($mi.DeclaringType -eq [object]) { continue }
    $sig = ''
    if ($mi.MemberType -eq 'Method') { $sig = '(' + (($mi.GetParameters() | ForEach-Object { $_.ParameterType.Name + ' ' + $_.Name }) -join ', ') + ') : ' + $mi.ReturnType.Name }
    elseif ($mi.MemberType -eq 'Property') { $sig = ' : ' + $mi.PropertyType.Name + $(if ($mi.CanWrite) { ' rw' } else { ' ro' }) }
    $log.WriteLine('   ' + $mi.MemberType + ' ' + $mi.Name + $sig); $k++; if ($k -ge $max) { $log.WriteLine('   ...'); break }
  }
}
$src = 'C:\B4Work\run_20261011_1721\SewerGEMS Block 04_R2.stsw'
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $net = $m.Network
  Dump $net.Outfalls 'Outfalls manager' 60
  $o = @($net.Outfalls.Elements() | Where-Object { $_.Label -eq 'SHACH16-O8' })[0]
  Dump $o 'outfall element' 60
  Dump $o.Input 'outfall Input' 90
  $mh = @($net.Manholes.Elements() | Where-Object { $_.Label -eq 'SHACH13-2' })[0]
  Dump $mh 'manhole element' 50
  Dump $mh.Input 'manhole Input' 70
  $c = @($net.Conduits.Elements() | Where-Object { $_.Label -eq 'SHACH13-C1' })[0]
  Dump $c.Input 'conduit Input' 140
  $p = $mh.Input.GetPoint(); $log.WriteLine('SHACH13-2 point ' + $p.X + ' ' + $p.Y + ' | ground ' + $mh.Input.GroundElevation + ' rim ' + $mh.Input.RimElevation + ' invert ' + $mh.Input.InvertElevation)
  $log.WriteLine('SHACH16-O8 ground ' + $o.Input.GroundElevation + ' invert ' + $o.Input.InvertElevation)
  $dds = $m.DomainDataSet; $fm = $dds.FieldManager; $dst = $dds.DomainDataSetType()
  $log.WriteLine('== element types 1..10: count | has SHACH16-O8 (' + $o.Id + ') | has SHACH13-2 (' + $mh.Id + ') | has SHACH13-C1 (' + $c.Id + ')')
  foreach ($et in 1..10) {
    try { $ids = @($dds.DomainElementManager($et).ElementIDs()); $log.WriteLine("   type $et : " + $ids.Count + ' | ' + ($ids -contains $o.Id) + ' | ' + ($ids -contains $mh.Id) + ' | ' + ($ids -contains $c.Id)) }
    catch { $log.WriteLine("   type $et : <" + $_.Exception.GetType().Name + '>') }
  }
  $dt = $dst.AlternativeType('Design').Id; $log.WriteLine('design alternative type id ' + $dt)
  $f = $fm.AlternativeField('Design_DesignConduit', $dt, 3, 17); Dump $f 'AlternativeField Design_DesignConduit' 40
  $log.WriteLine('   SHACH13-C1 Design_DesignConduit = ' + $f.GetValue($c.Id))
  foreach ($et in 1, 3, 5) {
    $log.WriteLine("== design fields on element type $et")
    try { foreach ($fl in $fm.AlternativeFields($dt, $et, 17)) { $log.WriteLine('   ' + $fl.Name) } } catch { $log.WriteLine('   <' + $_.Exception.GetType().Name + '>') }
  }
  $bt = $dst.AlternativeType('BoundaryCondition').Id; $log.WriteLine('boundary alternative type id ' + $bt)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
