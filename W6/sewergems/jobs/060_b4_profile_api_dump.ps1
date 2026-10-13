. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Block 04: how the Haestad data set stores engineering profiles. (1) Members of ProfileManager / ProfileElementManager and of a
# profile element on the Block 04 copy; (2) the Rustaq model (Block 6, has the profile "Ais-CH1-FP"): every profile with its
# fields and its element list, read through the same managers. Read-only on guest copies; nothing saved.
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
function DumpFields($dds, $el, $title) {
  $log.WriteLine("-- $title fields")
  foreach ($pi in $el.GetType().GetProperties()) { try { $v = $pi.GetValue($el, $null); if ($v -is [string] -or $v -is [int] -or $v -is [double] -or $v -is [bool]) { $log.WriteLine('   ' + $pi.Name + ' = ' + $v) } else { $log.WriteLine('   ' + $pi.Name + ' : ' + $(if ($v -eq $null) { 'null' } else { $v.GetType().Name })) } } catch { $log.WriteLine('   ' + $pi.Name + ' !' + $_.Exception.Message) } }
}
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  # ---- (1) Block 04 copy: the managers' API
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\B4Work\inv_20261011_1720\SewerGEMS Block 04.stsw')
  $dds = $m.DomainDataSet
  Dump $dds.ProfileManager 'ProfileManager' 80
  Dump $dds.ProfileElementManager 'ProfileElementManager' 80
  $log.WriteLine('Block 04 profiles: ' + @($dds.ProfileManager.Elements()).Count + ' | profile elements: ' + @($dds.ProfileElementManager.Elements()).Count)
  $m.Close()
  # ---- (2) Rustaq: existing profiles and their element lists
  $src = '\\VBOXSVR\Win10_shared_folder\sewergems 06042026\B6 SewerGEMS Rustaq'; $work = 'C:\B4Work\rustaq'; New-Item -ItemType Directory -Force $work | Out-Null
  foreach ($f in 'SewerGEMS Rustaq.stsw', 'SewerGEMS Rustaq.stsw.sqlite', 'SewerGEMS Rustaq.stsw.dwh', 'SewerGEMS Rustaq.stsw.profiles.dwh') { Copy-Item "$src\$f" $work -Force }
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$work\SewerGEMS Rustaq.stsw")
  $dds = $m.DomainDataSet; $pm = $dds.ProfileManager; $pem = $dds.ProfileElementManager
  $profiles = @($pm.Elements()); $log.WriteLine('Rustaq profiles: ' + $profiles.Count + ' | profile elements: ' + @($pem.Elements()).Count)
  $first = $true
  foreach ($p in $profiles) {
    if ($first) { Dump $p 'a profile element object' 60; DumpFields $dds $p 'profile'; $first = $false }
    $lab = ''; try { $lab = $p.Label } catch {}
    $log.WriteLine(('profile {0} "{1}"' -f $p.Id, $lab))
  }
  $k = 0
  foreach ($pe in $pem.Elements()) { if ($k -eq 0) { Dump $pe 'a profile-element (path member) object' 60; DumpFields $dds $pe 'profile element'; try { Dump $pe.Input 'its Input' 60; DumpFields $dds $pe.Input 'Input' } catch {} }; $k++; if ($k -ge 1) { break } }
  $log.WriteLine('-- first 40 profile elements (Id, Label, and every scalar property)')
  $k = 0
  foreach ($pe in $pem.Elements()) {
    $vals = @(); foreach ($pi in $pe.GetType().GetProperties()) { try { $v = $pi.GetValue($pe, $null); if ($v -is [string] -or $v -is [int] -or $v -is [double] -or $v -is [bool]) { $vals += ($pi.Name + '=' + $v) } } catch {} }
    try { foreach ($pi in $pe.Input.GetType().GetProperties()) { try { $v = $pi.GetValue($pe.Input, $null); if ($v -is [string] -or $v -is [int] -or $v -is [double] -or $v -is [bool]) { $vals += ('Input.' + $pi.Name + '=' + $v) } } catch {} } } catch {}
    $log.WriteLine('   ' + ($vals -join ' | ')); $k++; if ($k -ge 40) { break }
  }
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
