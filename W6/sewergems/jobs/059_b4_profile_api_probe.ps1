. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Block 04: does the OpenFlows / Haestad API expose engineering profiles? Support element types of the data set, members of the
# model and data-set objects mentioning "Profile", public types named *Profile* in the loaded assemblies, and the result files of
# the 17:21 run. Read-only on the guest copy of the 17:20 inventory; nothing saved.
$work = 'C:\B4Work\inv_20261011_1720'
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$work\SewerGEMS Block 04.stsw")
  $dds = $m.DomainDataSet; $dst = $dds.DomainDataSetType()
  $log.WriteLine('== support element types')
  try { foreach ($t in $dst.SupportElementTypes()) { $n = '?'; try { $n = $dds.SupportElementManager($t.Id).Count } catch {}; $log.WriteLine(('  [{0}] {1} / {2}  count={3}' -f $t.Id, $t.Name, $t.Label, $n)) } } catch { $log.WriteLine('  SupportElementTypes(): ' + $_.Exception.Message) }
  $log.WriteLine('== model members with Profile'); foreach ($mi in $m.GetType().GetMembers()) { if ($mi.Name -match 'Profile') { $log.WriteLine('  ' + $mi.MemberType + ' ' + $mi.Name) } }
  $log.WriteLine('== data set members with Profile'); foreach ($mi in $dds.GetType().GetMembers()) { if ($mi.Name -match 'Profile') { $log.WriteLine('  ' + $mi.MemberType + ' ' + $mi.Name) } }
  $log.WriteLine('== public types named *Profile* in the loaded assemblies (first 80)'); $k = 0
  foreach ($a in [AppDomain]::CurrentDomain.GetAssemblies()) { try { foreach ($ty in $a.GetTypes()) { if ($ty.IsPublic -and $ty.Name -match 'Profile' -and $k -lt 80) { $log.WriteLine('  ' + $a.GetName().Name + ' : ' + $ty.FullName); $k++ } } } catch {} }
  $log.WriteLine('== SewerGEMS folder assemblies with Profile in the name')
  foreach ($f in Get-ChildItem 'C:\Program Files (x86)\Bentley\SewerGEMS\x64' -Filter *.dll) { if ($f.Name -match 'Profile') { $log.WriteLine('  ' + $f.Name + '  ' + $f.Length) } }
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.WriteLine('== result files of the 17:21 run (guest work folder)')
foreach ($f in Get-ChildItem 'C:\B4Work\run_20261011_1721') { $log.WriteLine(('  {0,12}  {1}' -f $f.Length, $f.Name)) }
$log.ToString()
