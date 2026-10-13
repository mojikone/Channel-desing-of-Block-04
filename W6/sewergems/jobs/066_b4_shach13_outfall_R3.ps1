. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Block 04 (engineer, 2026-10-11 night): SHA-CH13-SS was never computed because its end SHACH13-2 was a manhole. On a copy of R2
# saved as R3: create the outfall SHACH13-O15 at the manhole's point with the manhole's elevations under every return-period
# scenario (the physical alternatives are local copies), reconnect SHACH13-C1 to it, delete the manhole; scope the design to that
# channel (design flags off everywhere else, the flags as found kept in design_flags_before.csv); run the 200 yr scenario as the
# trial; export; put the flags back; deliver R3 to the share as NEW files, the other scenarios' result files carried over from R2.
# R2 and the engineer's file are not touched.
$share = '\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04 11102026'
$stamp = Get-Date -Format yyyyMMdd_HHmm
$work = 'C:\B4Work\run_' + $stamp; New-Item -ItemType Directory -Force $work | Out-Null
$r2 = 'C:\B4Work\run_20261011_1721\SewerGEMS Block 04_R2.stsw'
Copy-Item $r2, "$r2.sqlite" $work -Force
$src = "$work\SewerGEMS Block 04_R2.stsw"; $dst = "$work\SewerGEMS Block 04_R3.stsw"
$out = '\\VBOXSVR\VBOX\bridge\out\b4\run_' + $stamp; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
$scen = [ordered]@{ '2 yr' = 1; '5 yr' = 2050; '10 yr' = 2051; '25 yr' = 2052; '50 yr' = 2053; '100 yr' = 2054; '200 yr' = 2055; '500 yr' = 2056 }
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $net = $m.Network
  $mh = @($net.Manholes.Elements() | Where-Object { $_.Label -eq 'SHACH13-2' })[0]
  $up = @($net.Manholes.Elements() | Where-Object { $_.Label -eq 'SHACH13-1' })[0]
  $c  = @($net.Conduits.Elements() | Where-Object { $_.Label -eq 'SHACH13-C1' })[0]
  if (-not $mh -or -not $up -or -not $c) { throw 'SHACH13 elements not found' }
  $log.WriteLine('before: manholes ' + @($net.Manholes.Elements()).Count + ', outfalls ' + @($net.Outfalls.Elements()).Count + ', SHACH13-C1 ' + $c.Input.StartNode.Label + ' -> ' + $c.Input.StopNode.Label)
  $pt = $mh.Input.GetPoint(); $ground = $mh.Input.GroundElevation; $invert = $mh.Input.InvertElevation
  # 1. the outfall, its elevations written under every return-period scenario
  $o = $net.Outfalls.Create(); $o.Label = 'SHACH13-O15'; $o.SetPoint($pt)
  foreach ($name in $scen.Keys) {
    $m.SetActiveScenario($m.Scenarios.Element($scen[$name]))
    $o.SetRimToGroundElevation = $true; $o.GroundElevation = $ground; $o.InvertElevation = $invert
  }
  $m.SetActiveScenario($m.Scenarios.Element(2055))
  $o.Input.DesignStructureElement = $true
  $log.WriteLine('outfall ' + $o.Label + ' (' + $o.Id + '): ground ' + $o.GroundElevation + ', invert ' + $o.InvertElevation + ', rim ' + $o.RimElevation + ' (manhole SHACH13-2 had ground ' + $ground + ', invert ' + $invert + ')')
  # 2. reconnect the conduit, delete the manhole
  $c.Input.StopNode = $o
  $log.WriteLine('SHACH13-C1 stop node now ' + $c.Input.StopNode.Label)
  $mh.Delete()
  $log.WriteLine('after: manholes ' + @($net.Manholes.Elements()).Count + ', outfalls ' + @($net.Outfalls.Elements()).Count)
  # 3. design scope: every flag as found, then only SHA-CH13-SS keeps its flags
  $snap = New-Object System.Collections.Generic.List[string]
  $snap.Add('kind,id,label,DesignConduit,DesignStartInvert,DesignStopInvert,DesignStructureElement')
  foreach ($x in $net.Conduits.Elements()) { $snap.Add('conduit,' + $x.Id + ',' + $x.Label + ',' + $x.Input.DesignConduit + ',' + $x.Input.DesignStartInvert + ',' + $x.Input.DesignStopInvert + ',') }
  foreach ($x in $net.Manholes.Elements()) { $snap.Add('manhole,' + $x.Id + ',' + $x.Label + ',,,,' + $x.Input.DesignStructureElement) }
  foreach ($x in $net.Outfalls.Elements()) { $snap.Add('outfall,' + $x.Id + ',' + $x.Label + ',,,,' + $x.Input.DesignStructureElement) }
  [IO.File]::WriteAllLines("$out\design_flags_before.csv", $snap)
  $nc = 0; $nn = 0
  foreach ($x in $net.Conduits.Elements()) { if ($x.Label -ne 'SHACH13-C1') { $x.Input.DesignConduit = $false; $x.Input.DesignStartInvert = $false; $x.Input.DesignStopInvert = $false; $nc++ } }
  foreach ($x in $net.Manholes.Elements()) { if ($x.Label -ne 'SHACH13-1') { $x.Input.DesignStructureElement = $false; $nn++ } }
  foreach ($x in $net.Outfalls.Elements()) { if ($x.Label -ne 'SHACH13-O15') { $x.Input.DesignStructureElement = $false; $nn++ } }
  $log.WriteLine('design scope: flags off on ' + $nc + ' conduits and ' + $nn + ' nodes; kept on SHACH13-C1 ' + $c.Input.DesignConduit + '/' + $c.Input.DesignStartInvert + '/' + $c.Input.DesignStopInvert + ', SHACH13-1 ' + $up.Input.DesignStructureElement + ', SHACH13-O15 ' + $o.Input.DesignStructureElement)
  $m.Save()
  # 4. the trial: 200 yr
  $log.WriteLine('######## 200 yr (scenario 2055) ' + (Get-Date -Format T))
  [Scen]::DesignUntilStable($m, 2055, 4, $log)
  [B4]::Export($m, $out, '200yr', $log)
  $m.Save()
  # 5. the flags back as found (results untouched)
  $flags = @{}; foreach ($line in ([IO.File]::ReadAllLines("$out\design_flags_before.csv") | Select-Object -Skip 1)) { $f = $line.Split(','); $flags[[int]$f[1]] = $f }
  foreach ($x in $net.Conduits.Elements()) { if ($flags.ContainsKey($x.Id)) { $f = $flags[$x.Id]; $x.Input.DesignConduit = [bool]::Parse($f[3]); $x.Input.DesignStartInvert = [bool]::Parse($f[4]); $x.Input.DesignStopInvert = [bool]::Parse($f[5]) } }
  foreach ($x in $net.Manholes.Elements()) { if ($flags.ContainsKey($x.Id)) { $x.Input.DesignStructureElement = [bool]::Parse($flags[$x.Id][6]) } }
  foreach ($x in $net.Outfalls.Elements()) { if ($flags.ContainsKey($x.Id)) { $x.Input.DesignStructureElement = [bool]::Parse($flags[$x.Id][6]) } }
  $m.Save(); $m.Close()
  # 6. reopen check
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($dst); $net = $m.Network
  $c = @($net.Conduits.Elements() | Where-Object { $_.Label -eq 'SHACH13-C1' })[0]
  $log.WriteLine('reopened R3: manholes ' + @($net.Manholes.Elements()).Count + ', outfalls ' + @($net.Outfalls.Elements()).Count + ', SHACH13-C1 ' + $c.Input.StartNode.Label + ' -> ' + $c.Input.StopNode.Label + ', section ' + $c.Input.ConduitShapeLabel + ', flags ' + $c.Input.DesignConduit + '/' + $c.Input.DesignStartInvert + '/' + $c.Input.DesignStopInvert + ', conduits with design off: ' + @($net.Conduits.Elements() | Where-Object { -not $_.Input.DesignConduit }).Count)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
if ($log.ToString() -notmatch 'FAILED') {
  Copy-Item $dst, "$dst.sqlite" $share -Force
  foreach ($suffix in '.dwh', '.profiles.dwh') { if (Test-Path "$share\SewerGEMS Block 04_R2.stsw$suffix") { Copy-Item "$share\SewerGEMS Block 04_R2.stsw$suffix" "$share\SewerGEMS Block 04_R3.stsw$suffix" -Force } }
  foreach ($id in $scen.Values) {
    $r3out = "$work\SewerGEMS Block 04_R3.stsw_1_${id}-stmc-gvf.out"; $r2out = "$share\SewerGEMS Block 04_R2.stsw_1_${id}-stmc-gvf.out"
    if (Test-Path $r3out) { Copy-Item $r3out $share -Force; $log.WriteLine("result file for scenario $id from this run") }
    elseif (Test-Path $r2out) { Copy-Item $r2out "$share\SewerGEMS Block 04_R3.stsw_1_${id}-stmc-gvf.out" -Force; $log.WriteLine("result file for scenario $id carried over from R2") }
  }
  $log.WriteLine('delivered "SewerGEMS Block 04_R3.stsw" with .sqlite, .dwh, .profiles.dwh and the result files to the share as new files')
}
[IO.File]::WriteAllText("$out\log.txt", $log.ToString())
$log.ToString()
