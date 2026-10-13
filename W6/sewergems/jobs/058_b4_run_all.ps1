. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Block 04 channel model (engineer's build of 2026-10-11): run the DESIGN of every return-period scenario on a COPY of the shared
# model inside the guest, repeat each design until no catalogue size changes, export conduit and node tables per scenario, and
# deliver the computed copy to the share as a NEW file "SewerGEMS Block 04_R1.stsw" (the engineer's file is never touched).
$share = '\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04 11102026'
$stamp = Get-Date -Format yyyyMMdd_HHmm
$work = 'C:\B4Work\run_' + $stamp; New-Item -ItemType Directory -Force $work | Out-Null
Copy-Item "$share\SewerGEMS Block 04.stsw", "$share\SewerGEMS Block 04.stsw.sqlite" $work -Force
$src = "$work\SewerGEMS Block 04.stsw"; $dst = "$work\SewerGEMS Block 04_R1.stsw"
$out = '\\VBOXSVR\VBOX\bridge\out\b4\run_' + $stamp; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
$log.WriteLine('model copied: ' + (Get-Item "$share\SewerGEMS Block 04.stsw.sqlite").LastWriteTime.ToString('o') + ' -> ' + $work)
$scen = [ordered]@{ '2 yr' = 1; '5 yr' = 2050; '10 yr' = 2051; '25 yr' = 2052; '50 yr' = 2053; '100 yr' = 2054; '200 yr' = 2055; '500 yr' = 2056 }
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $log.WriteLine('result methods, conduit: ' + ([B4]::ResultMethods([B4]::Res(@($m.Network.Conduits.Elements())[0])) -join ' '))
  $log.WriteLine('result methods, manhole: ' + ([B4]::ResultMethods([B4]::Res(@($m.Network.Manholes.Elements())[0])) -join ' '))
  foreach ($name in $scen.Keys) {
    $id = $scen[$name]; $tag = $name -replace ' ', ''
    $s = $m.Scenarios.Element($id)
    $log.WriteLine("######## $name (scenario $id '" + $s.Label + "') " + (Get-Date -Format T))
    [Scen]::DesignUntilStable($m, $id, 4, $log)
    [B4]::Export($m, $out, $tag, $log)
    $m.Save()
  }
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
if ($log.ToString() -notmatch 'FAILED') {
  Copy-Item $dst, "$dst.sqlite" $share -Force
  $log.WriteLine('delivered "SewerGEMS Block 04_R1.stsw" and its .sqlite to the share (new files)')
}
[IO.File]::WriteAllText("$out\log.txt", $log.ToString())
$log.ToString()
