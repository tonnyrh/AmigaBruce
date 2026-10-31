#Requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9-]+$')][string]$Label,
    [ValidateRange(0,3)][int]$PerfEnemies=3,[switch]$Profile,[switch]$ContactRun,[switch]$Controlled,[switch]$SkipBuild,
    [ValidateRange(360,30000)][int]$TestFrames=360,[ValidateRange(0,30000)][int]$SourceSteps=0)
$ErrorActionPreference='Stop'
if($SourceSteps -and ($Controlled -or $TestFrames -lt $SourceSteps)){throw 'Fixed source steps require PAL benchmark and sufficient outer-loop safety limit'}
$taskRoot=$PSScriptRoot
$folder=Join-Path $taskRoot "reference/analysis/optimization-2026-10-27/$Label"
if(Test-Path -LiteralPath $folder){throw 'Benchmark label already exists; keep previous measurements'}
New-Item -ItemType Directory -Force $folder | Out-Null
if(!$SkipBuild){
    $build=@{Autotest=$true;TestFrames=$TestFrames;SourceProfile=$Profile;ContactRunTest=$ContactRun;PerfEnemies=$PerfEnemies;PerfSourceSteps=$SourceSteps}
    if($Controlled){$build.SourceWorldTest=$true}else{$build.SourcePerfTest=$true}
    & (Join-Path $taskRoot 'amiga-build.ps1') @build
}
$identity=@(Get-ChildItem (Join-Path $taskRoot 'core'),(Join-Path $taskRoot 'amiga') -File |
    Where-Object {$_.Extension -in '.c','.h','.s'} | ForEach-Object {
        @{path=$_.FullName.Substring($taskRoot.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash.ToLower()}})
$buildIdentity=@('exe','elf','adf') | ForEach-Object {
    $p="amiga/out/bruce_test.$_";Copy-Item -LiteralPath (Join-Path $taskRoot $p) -Destination $folder
    @{path=$p;sha256=(Get-FileHash (Join-Path $taskRoot $p)).Hash.ToLower()}}
$runtime=Join-Path $taskRoot '.tmp/session-ui'
& (Join-Path $taskRoot 'amiga-run.ps1') -Autotest -TestRuns 1 -EmulatorPath (Join-Path $runtime 'winuae64.exe') -EmulatorIni (Join-Path $runtime 'winuae.ini')
$owned=[int](Get-Content (Join-Path $taskRoot '.tmp/winuae-test.pid'))
$report=Join-Path $taskRoot 'amiga/out/autotest-1.txt'
try{
    $deadline=(Get-Date).AddMinutes(25);$run=@{}
    while((Get-Date) -lt $deadline){
        if(Test-Path -LiteralPath $report){
            $run=@{};foreach($line in Get-Content -LiteralPath $report){$p=$line.Split('=',2);if($p.Count -eq 2){$run[$p[0]]=$p[1]}}
            if($run['parity'] -eq 'PROVISIONAL'){break}
        }
        if(!(Get-Process -Id $owned -ErrorAction SilentlyContinue)){throw 'Owned emulator exited before benchmark report'}
        Start-Sleep -Milliseconds 500
    }
    if($SourceSteps){
        if($run['source_perf_steps'] -ne [string]$SourceSteps -or $run['source_world_steps'] -ne [string]$SourceSteps -or [int]$run['frames'] -ge $TestFrames){throw 'Benchmark did not reach exactly the requested source steps before safety limit'}
    }elseif($run['frames'] -ne [string]$TestFrames){throw 'Benchmark did not finish outer loops'}
    if($run['restored_os'] -ne '1'){throw 'Benchmark did not restore OS'}
    $expectedKernelCases=if($ContactRun){'710'}elseif($Profile -or $Controlled){'454'}else{'1046'}
    if($run['contact_kernel_cases'] -ne $expectedKernelCases){throw 'Native contact kernel controls missing'}
    $expectedVicCases=if($Profile -or $Controlled -or $ContactRun){'0'}else{'1536'}
    if($run['vic_repeat_cases'] -ne $expectedVicCases){throw 'Native VIC repeat controls missing'}
    foreach($item in $identity){if((Get-FileHash (Join-Path $taskRoot $item.path)).Hash.ToLower() -ne $item.sha256){throw "Source changed during benchmark: $($item.path)"}}
    foreach($key in @('c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','vic_compare_errors','contact_kernel_errors')){
        if($run[$key] -ne '0'){throw "$key=$($run[$key])"}}
    if($Profile -and $run['perf_errors'] -ne '0'){throw 'Unbalanced profiler nesting'}
    Copy-Item -LiteralPath $report -Destination (Join-Path $folder 'native.txt')
    @{source_files=$identity;build=$buildIdentity;run=$run;controlled=[bool]$Controlled;
        contact_run=[bool]$ContactRun;profile=[bool]$Profile;enemy_mask=$PerfEnemies;source_steps_target=$SourceSteps;outer_loop_limit=$TestFrames;edition_verified=$false;natural_playthrough=$false;
        method=$(if($Controlled){'One injected field per loop, source-world control route'}else{'Actual PAL scheduler, stationary invincible Bruce, source-world path; no fixture/capture in measured loop'});
        limits=@('Benchmark only; does not replace 53 native controls or real-time acceptance','Profile overhead and native diagnostic bookkeeping affect timing')} |
        ConvertTo-Json -Depth 8 | Set-Content (Join-Path $folder 'identity.json') -Encoding utf8
    & python (Join-Path $taskRoot 'tools/summarize_source_performance.py') (Join-Path $folder 'native.txt')
    if($LASTEXITCODE){throw 'Profile report parsing failed'}
}finally{
    if(Get-Process -Id $owned -ErrorAction SilentlyContinue){Stop-Process -Id $owned}
}
