. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Block 04 channel model (engineer's build of 2026-10-11): inventory of scenarios, alternatives, calculation options, catalogues
# and result fields, on a COPY of the shared-folder model inside the guest. Nothing is changed, nothing is saved.
$share = '\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04 11102026'
$work = 'C:\B4Work\inv_' + (Get-Date -Format yyyyMMdd_HHmm); New-Item -ItemType Directory -Force $work | Out-Null
Copy-Item "$share\SewerGEMS Block 04.stsw", "$share\SewerGEMS Block 04.stsw.sqlite" $work -Force
$out = '\\VBOXSVR\VBOX\bridge\out\b4\inventory'; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
$log.WriteLine('copied ' + (Get-Item "$share\SewerGEMS Block 04.stsw.sqlite").LastWriteTime.ToString('o') + ' -> ' + $work)
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$work\SewerGEMS Block 04.stsw")
  [Inventory]::Run($m, $out, $log)
  $log.WriteLine('== counts: conduits ' + @($m.Network.Conduits.Elements()).Count + ' manholes ' + @($m.Network.Manholes.Elements()).Count + ' outfalls ' + @($m.Network.Outfalls.Elements()).Count)
  $cat = [SizeCheck]::Catalogue($m); $log.WriteLine('== catalogue sizes ' + $cat.Count)
  foreach ($k in $cat.Keys) { $log.WriteLine('   ' + $k + ' -> ' + $cat[$k].Item1 + ' | ' + $cat[$k].Item2) }
  $first = @($m.DomainDataSet.ScenarioManager.Elements())[0]
  $ids = New-Object 'System.Collections.Generic.List[int]'
  [ResultFields]::Export($m, $first.Id, $ids, "$out\fields_probe.csv", $log)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
