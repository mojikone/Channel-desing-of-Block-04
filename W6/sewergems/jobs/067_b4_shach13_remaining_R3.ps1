. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Block 04 (engineer, 2026-10-11 night, "if you want to run the whole model, do it"): on R3 (the SHACH13-O15 model of job 066),
# the seven remaining return-period scenarios, each designed with the scope of the trial: design flags on for SHACH13-C1 and its
# two nodes only, everything else analysed with its designed size; exports into the SAME run folder as the 200 yr trial so the
# folder holds all eight scenarios; the flags put back as found; R3 and its result files delivered to the share again.
$share = '\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04 11102026'
$work = 'C:\B4Work\run_20261012_0031'; $dst = "$work\SewerGEMS Block 04_R3.stsw"
$out = '\\VBOXSVR\VBOX\bridge\out\b4\run_20261012_0031'
$log = New-Object IO.StringWriter
$scen = [ordered]@{ '2 yr' = 1; '5 yr' = 2050; '10 yr' = 2051; '25 yr' = 2052; '50 yr' = 2053; '100 yr' = 2054; '500 yr' = 2056 }
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($dst); $net = $m.Network
  $c = @($net.Conduits.Elements() | Where-Object { $_.Label -eq 'SHACH13-C1' })[0]
  $log.WriteLine('R3 opened: manholes ' + @($net.Manholes.Elements()).Count + ', outfalls ' + @($net.Outfalls.Elements()).Count + ', SHACH13-C1 ' + $c.Input.StartNode.Label + ' -> ' + $c.Input.StopNode.Label)
  $snap = New-Object System.Collections.Generic.List[string]
  $snap.Add('kind,id,label,DesignConduit,DesignStartInvert,DesignStopInvert,DesignStructureElement')
  foreach ($x in $net.Conduits.Elements()) { $snap.Add('conduit,' + $x.Id + ',' + $x.Label + ',' + $x.Input.DesignConduit + ',' + $x.Input.DesignStartInvert + ',' + $x.Input.DesignStopInvert + ',') }
  foreach ($x in $net.Manholes.Elements()) { $snap.Add('manhole,' + $x.Id + ',' + $x.Label + ',,,,' + $x.Input.DesignStructureElement) }
  foreach ($x in $net.Outfalls.Elements()) { $snap.Add('outfall,' + $x.Id + ',' + $x.Label + ',,,,' + $x.Input.DesignStructureElement) }
  [IO.File]::WriteAllLines("$out\design_flags_before_067.csv", $snap)
  $nc = 0; $nn = 0
  foreach ($x in $net.Conduits.Elements()) { if ($x.Label -ne 'SHACH13-C1') { $x.Input.DesignConduit = $false; $x.Input.DesignStartInvert = $false; $x.Input.DesignStopInvert = $false; $nc++ } }
  foreach ($x in $net.Manholes.Elements()) { if ($x.Label -ne 'SHACH13-1') { $x.Input.DesignStructureElement = $false; $nn++ } }
  foreach ($x in $net.Outfalls.Elements()) { if ($x.Label -ne 'SHACH13-O15') { $x.Input.DesignStructureElement = $false; $nn++ } }
  $log.WriteLine('design scope: flags off on ' + $nc + ' conduits and ' + $nn + ' nodes')
  $m.Save()
  foreach ($name in $scen.Keys) {
    $id = $scen[$name]; $tag = $name -replace ' ', ''
    $log.WriteLine("######## $name (scenario $id) " + (Get-Date -Format T))
    [Scen]::DesignUntilStable($m, $id, 4, $log)
    [B4]::Export($m, $out, $tag, $log)
    $m.Save()
  }
  $flags = @{}; foreach ($line in ([IO.File]::ReadAllLines("$out\design_flags_before_067.csv") | Select-Object -Skip 1)) { $f = $line.Split(','); $flags[[int]$f[1]] = $f }
  foreach ($x in $net.Conduits.Elements()) { if ($flags.ContainsKey($x.Id)) { $f = $flags[$x.Id]; $x.Input.DesignConduit = [bool]::Parse($f[3]); $x.Input.DesignStartInvert = [bool]::Parse($f[4]); $x.Input.DesignStopInvert = [bool]::Parse($f[5]) } }
  foreach ($x in $net.Manholes.Elements()) { if ($flags.ContainsKey($x.Id)) { $x.Input.DesignStructureElement = [bool]::Parse($flags[$x.Id][6]) } }
  foreach ($x in $net.Outfalls.Elements()) { if ($flags.ContainsKey($x.Id)) { $x.Input.DesignStructureElement = [bool]::Parse($flags[$x.Id][6]) } }
  $m.Save(); $m.Close()
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($dst); $net = $m.Network
  $log.WriteLine('reopened R3: conduits with design off: ' + @($net.Conduits.Elements() | Where-Object { -not $_.Input.DesignConduit }).Count + ', outfalls ' + @($net.Outfalls.Elements()).Count)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
if ($log.ToString() -notmatch 'FAILED') {
  Copy-Item $dst, "$dst.sqlite" $share -Force
  foreach ($id in $scen.Values) { $r3out = "$work\SewerGEMS Block 04_R3.stsw_1_${id}-stmc-gvf.out"; if (Test-Path $r3out) { Copy-Item $r3out $share -Force; $log.WriteLine("result file for scenario $id from this run") } }
  $log.WriteLine('delivered R3 again with the seven result files of this run')
}
[IO.File]::WriteAllText("$out\log_067.txt", $log.ToString())
$log.ToString()
