param([string]$Mode='release')
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../..").Path
$run=Join-Path $root 'reference/analysis/op-score-2026-10-31/run.ps1'
$stage=Join-Path $root '.tmp/field-work'
$cases=@(
    @("long-$Mode","long-$Mode-a",1,3,2),@($Mode,"$Mode-a",1,3,2),
    @($Mode,"$Mode-still-a",1,3,0),@("long-$Mode","long-$Mode-b",1,3,2),
    @($Mode,"$Mode-b",1,3,2),@($Mode,"$Mode-still-b",1,3,0),
    @($Mode,"$Mode-stairs",12,3,1),@($Mode,"$Mode-yamo",13,1,0))
$jobs=@()
foreach($case in $cases){
    if(!(Test-Path -LiteralPath "$stage/$($case[0])/bruce_amiga.exe")){throw "Missing built probe $($case[0])"}
    while(@(Get-Process winuae64 -ErrorAction SilentlyContinue).Count -ge 5 -or @($jobs|Where-Object State -eq Running).Count -ge 2){Start-Sleep 2}
    $jobs+=Start-Job -ArgumentList @($run,$case[0],$case[1],$case[2],$case[3],$case[4]) -ScriptBlock {
        param($script,$mode,$label,$room,$mask,$route)
        & $script $mode $label $room $mask $route -StageName field-work
    }
    Start-Sleep 3
}
$jobs|Wait-Job|Out-Null
foreach($job in $jobs){
    Receive-Job $job
    if($job.State -ne 'Completed'){throw 'Incomplete field measurement'}
}
