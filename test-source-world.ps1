#Requires -Version 5.1
[CmdletBinding()]
param([switch]$SkipHost,[switch]$SkipBuild,[ValidateRange(900,30000)][int]$TestFrames=1200,[string]$EmulatorPath,[string]$EmulatorIni)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
if(!$SkipHost){
    & (Join-Path $taskRoot 'test-c64-actors.ps1')
    if($LASTEXITCODE){throw 'Source actor controls failed'}
    & python (Join-Path $taskRoot 'tools/audit_c64_world.py')
    if($LASTEXITCODE){throw 'Integrated source world controls failed'}
    & python (Join-Path $taskRoot 'tools/build_source_actor_fixture.py')
    if($LASTEXITCODE){throw 'Source fixture generation failed'}
}
if(!$SkipBuild){
    & (Join-Path $taskRoot 'amiga-build.ps1') -Autotest -SourceWorldTest -TestFrames $TestFrames
}
$paths=@('amiga-build.ps1','amiga-run.ps1','test-source-world.ps1','test-c64-actors.ps1','tests/source_actor_fixture.h',
    'tools/build_source_actor_fixture.py','tools/build_contact_class_kernel.py','tools/build_c64_actors.py','tools/build_c64_rooms.py',
    'tools/audit_c64_actor_chain.py','tools/audit_c64_world.py')
$paths+=@(Get-ChildItem (Join-Path $taskRoot 'core'),(Join-Path $taskRoot 'amiga') -File | Where-Object {$_.Extension -in '.c','.h','.s'} | ForEach-Object {$_.FullName.Substring($taskRoot.Length+1).Replace('\','/')})
$identity=@($paths | Sort-Object -Unique | ForEach-Object {@{path=$_;sha256=(Get-FileHash (Join-Path $taskRoot $_)).Hash.ToLower()}})
# Keep tested artifacts independent of subsequent performance builds in out/.
$buildId=(Get-FileHash (Join-Path $taskRoot 'amiga/out/bruce_test.exe')).Hash.ToLower().Substring(0,12)
$adfId=(Get-FileHash (Join-Path $taskRoot 'amiga/out/bruce_test.adf')).Hash.ToLower().Substring(0,12)
$archive="reference/analysis/actor-chain-2026-10-26/native-builds/$buildId-$adfId"
New-Item -ItemType Directory -Force (Join-Path $taskRoot $archive) | Out-Null
$build=@('exe','elf','adf') | ForEach-Object {
    $source="amiga/out/bruce_test.$_";$p="$archive/bruce_test.$_"
    Copy-Item -LiteralPath (Join-Path $taskRoot $source) -Destination (Join-Path $taskRoot $p) -Force
    @{path=$p;sha256=(Get-FileHash (Join-Path $taskRoot $p)).Hash.ToLower()}}
& (Join-Path $taskRoot 'amiga-run.ps1') -Autotest -TestRuns 1 -EmulatorPath $EmulatorPath -EmulatorIni $EmulatorIni
$owned=[int](Get-Content (Join-Path $taskRoot '.tmp/winuae-test.pid'))
$reportPath=Join-Path $taskRoot 'amiga/out/autotest-1.txt'
try{
    $deadline=(Get-Date).AddMinutes(30);$run=@{}
    while((Get-Date) -lt $deadline){
        if(Test-Path -LiteralPath $reportPath){
            $run=@{};foreach($line in Get-Content -LiteralPath $reportPath){$part=$line.Split('=',2);if($part.Count -eq 2){$run[$part[0]]=$part[1]}}
            if($run['parity'] -eq 'PROVISIONAL'){break}
        }
        if(!(Get-Process -Id $owned -ErrorAction SilentlyContinue)){throw 'Owned emulator exited before report'}
        Start-Sleep -Milliseconds 500
    }
    if($run['parity'] -ne 'PROVISIONAL'){throw 'Source world native test timed out'}
    foreach($item in $identity){if((Get-FileHash (Join-Path $taskRoot $item.path)).Hash.ToLower() -ne $item.sha256){throw "Source changed during test: $($item.path)"}}
    foreach($item in $build){
        $live=Join-Path $taskRoot ('amiga/out/'+[IO.Path]::GetFileName($item.path))
        if((Get-FileHash (Join-Path $taskRoot $item.path)).Hash.ToLower() -ne $item.sha256 -or
           (Get-FileHash $live).Hash.ToLower() -ne $item.sha256){throw 'Test binary changed during native run'}
    }
    $failures=@()
    foreach($key in @('source_actor_fixture_failure','c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','contact_kernel_errors','c64_render_mismatches','capture_fault','vic_compare_errors')){
        if($run[$key] -ne '0'){$failures+="$key=$($run[$key])"}
    }
    if($run['source_actor_fixture_cases'] -ne '53'){$failures+='Missing53 source controls'}
    if($run['contact_kernel_cases'] -ne '454'){$failures+='Missing454 native contact kernel controls'}
    if($run['vic_repeat_cases'] -ne '0'){$failures+='Unexpected separate VIC repeat reference in full fixture image'}
    if($run['source_world_test'] -ne '1' -or $run['frames'] -ne [string]$TestFrames -or $run['restored_os'] -ne '1'){$failures+='Replay/restore incomplete'}
    if([int]$run['chip_largest_loaded'] -lt 49152){$failures+='Chip RAM margin below49152 bytes'}
    if($run['capture_original_hash'] -ne $run['capture_decoded_hash']){$failures+='Capture decode mismatch'}
    if($run['presentation_hold_fields'] -ne '3' -or [int]$run['max_held_image_streak'] -gt 3){$failures+='New presentation starved beyond its decision limit'}
    $output=[ordered]@{date='2026-10-27';status=$(if($failures.Count){'failed_native_source_contract'}else{'passed_scoped_native_source_contract'});
        source_files=$identity;build=$build;run=$run;failures=$failures;
        edition_verified=$false;natural_playthrough=$false;raster_exact=$false;
        realtime_contract_passed=([int]$run['max_gap_excluding_framebuffer_capture'] -le 1);
        limits=@('Controlled one-field-per-loop replay, not normal wall-clock input scheduling','53 injected whole-RAM/register controls, not a natural C64 playthrough','Frame drops remain a failed real-time acceptance item','Initial field gap includes pre-takeover fixtures and is not room-load latency')}
    $output | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $taskRoot 'reference/validation/source-world-native.json') -Encoding utf8
    Copy-Item -LiteralPath $reportPath -Destination (Join-Path $taskRoot 'reference/analysis/actor-chain-2026-10-26/native-final.txt') -Force
    if($failures.Count){throw ($failures -join '; ')}
    Write-Output "PASS53 native source controls; $TestFrames replay loops; largest Chip block $($run['chip_largest_loaded']); real-time gate $($output.realtime_contract_passed)"
}finally{
    if(Get-Process -Id $owned -ErrorAction SilentlyContinue){Stop-Process -Id $owned}
}
