"""Generate the bridge jobs that create the Block 04 channel profiles (selection sets under ProfileManager) from
W6/sewergems/profiles/profile_paths.csv. Written as a file because Git Bash heredocs mangle backslashes."""
import pandas as pd, sys
CB = r"D:\Mojtaba\Renardet\2224 WS11\Batinah\Block 4\Claude Block 04"
df = pd.read_csv(CB + r"\W6\sewergems\profiles\profile_paths.csv")

HEAD = r'''. \\VBOXSVR\VBOX\bridge\lib\load.ps1
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
'''

# ---------------- 062: read the Rustaq profile's list, test one profile on a scratch copy
row = df[df["profile"] == "HAW-CH1-FP"].iloc[0]
test = HEAD + r'''
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
  [void](MakeProfile $pm 'HAW-CH1-FP' @(''' + ", ".join(row["ids"].split()) + r'''))
  $m.Save(); $m.Close()
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$work\SewerGEMS Block 04.stsw")
  $pm = $m.DomainDataSet.ProfileManager; $idsF = $pm.SelectionSetField('SelectionSetElementIDs')
  $q = @($pm.Elements() | Where-Object { $_.Label -eq 'HAW-CH1-FP' })
  $log.WriteLine('after reopen: ' + $q.Count + ' profile(s) named HAW-CH1-FP; total profiles ' + @($pm.Elements()).Count)
  if ($q.Count -gt 0) { $b = @(); foreach ($i in $idsF.GetValue($q[0].Id)) { $b += [int]$i }; $log.WriteLine('   ids persisted: ' + $b.Count + ' : ' + ($b -join ' ')) }
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
'''
open(CB + r"\W6\sewergems\jobs\062_b4_profile_test.ps1", "w", encoding="utf-8", newline="\r\n").write(test)

# ---------------- 063: all 37 profiles into R2 = R1 + profiles, delivered to the share with the result files
lines = "\n".join("  [void](MakeProfile $pm '%s' @(%s))" % (r["profile"], ", ".join(r["ids"].split())) for _, r in df.iterrows())
full = HEAD + r'''
# Block 04 (engineer, 2026-10-11): the 37 channel profiles, named as the channels of "Channels and Dykes 04102026", written into
# a NEW revision: R2 = the computed R1 of the 17:21 run (designed sizes of all eight scenarios) + the profiles. Each profile is a
# selection set under ProfileManager holding the channel's nodes and conduits from the start to the junction point on the receiving
# channel or the outfall. Delivered to the share: R2 .stsw + .sqlite, the result files of the eight scenarios renamed for R2, and
# the engineer's .dwh and .profiles.dwh copied under the R2 name so the drawing and profile settings travel with it. The 43 profiles
# inherited from the Rustaq model (their elements do not exist here) are left in place for the engineer to delete.
$share = '\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04 11102026'
$work = 'C:\B4Work\run_20261011_1721'
$src = "$work\SewerGEMS Block 04_R1.stsw"; $dst = "$work\SewerGEMS Block 04_R2.stsw"
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $pm = $m.DomainDataSet.ProfileManager
  $log.WriteLine('profiles before: ' + @($pm.Elements()).Count)
''' + lines + r'''
  $log.WriteLine('profiles after: ' + @($pm.Elements()).Count)
  $m.Save(); $m.Close()
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($dst)
  $pm = $m.DomainDataSet.ProfileManager; $idsF = $pm.SelectionSetField('SelectionSetElementIDs'); $n = 0
  foreach ($p in $pm.Elements()) { $b = @(); foreach ($i in $idsF.GetValue($p.Id)) { $b += [int]$i }; if ($b.Count -gt 0) { $n++ } }
  $log.WriteLine('after reopen: ' + @($pm.Elements()).Count + ' profiles, ' + $n + ' with elements')
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
if ($log.ToString() -notmatch 'FAILED') {
  Copy-Item $dst, "$dst.sqlite" $share -Force
  foreach ($f in Get-ChildItem $work -Filter 'SewerGEMS Block 04_R1.stsw_*.out') { Copy-Item $f.FullName (Join-Path $share ($f.Name -replace '_R1\.stsw_', '_R2.stsw_')) -Force }
  foreach ($f in Get-ChildItem $work -Filter 'SewerGEMS Block 04_R1.stsw_*.out') { Copy-Item $f.FullName (Join-Path $share $f.Name) -Force }
  Copy-Item "$share\SewerGEMS Block 04.stsw.dwh" "$share\SewerGEMS Block 04_R2.stsw.dwh" -Force
  Copy-Item "$share\SewerGEMS Block 04.stsw.profiles.dwh" "$share\SewerGEMS Block 04_R2.stsw.profiles.dwh" -Force
  $log.WriteLine('delivered R2 (.stsw, .sqlite, .dwh, .profiles.dwh) and the result files of R1 and R2 to the share')
}
$log.ToString()
'''
open(CB + r"\W6\sewergems\jobs\063_b4_profiles_R2.ps1", "w", encoding="utf-8", newline="\r\n").write(full)
print("jobs written: 062 (test, %d ids) and 063 (%d profiles)" % (len(row["ids"].split()), len(df)))
