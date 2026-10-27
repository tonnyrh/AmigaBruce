#Requires -Version 5.1
[CmdletBinding()]
param([ValidateSet('baseline','updated')][string]$Label='updated',[ValidateRange(1,2)][int]$Runs=1)
$ErrorActionPreference='Stop'
& (Join-Path $PSScriptRoot 'amiga-build.ps1') -Autotest -CombatTest -ElectricTest -CollectFrameDrops -TestFrames 900
if($LASTEXITCODE){throw 'Electric trap test build failed'}
$captureRoot=Join-Path $PSScriptRoot "reference/analysis/room10-electric-2026-10-26/$Label"
New-Item -ItemType Directory -Force $captureRoot | Out-Null
$paths=@(Get-ChildItem (Join-Path $PSScriptRoot 'core'),(Join-Path $PSScriptRoot 'tests'),(Join-Path $PSScriptRoot 'amiga') -File |
    Where-Object {$_.Extension -in @('.c','.h','.s')} | ForEach-Object {$_.FullName.Substring($PSScriptRoot.Length+1).Replace('\','/')})
$paths+=@('amiga-build.ps1','amiga-run.ps1','test-room10-electric.ps1','amiga/out/bruce_test.exe','amiga/out/bruce_test.adf')
$identities=@(foreach($path in $paths){
    $source=Join-Path $PSScriptRoot $path
    $target=Join-Path $captureRoot $path
    New-Item -ItemType Directory -Force (Split-Path $target -Parent) | Out-Null
    Copy-Item -LiteralPath $source -Destination $target -Force
    @{path=$path;sha256=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLower()}
})
& (Join-Path $PSScriptRoot 'amiga-run.ps1') -Autotest
$ownedEmulator=[int](Get-Content (Join-Path $PSScriptRoot '.tmp/winuae-test.pid'))
$results=@();$deadline=[DateTime]::UtcNow.AddSeconds(900)
try {
    while([DateTime]::UtcNow -lt $deadline){
        $results=@()
        for($n=1;$n -le $Runs;$n++){
            $path=Join-Path $PSScriptRoot "amiga/out/autotest-$n.txt"
            if(-not(Test-Path -LiteralPath $path)){break}
            $values=@{}
            foreach($line in Get-Content -LiteralPath $path){$parts=$line.Split('=',2);if($parts.Count -eq 2){$values[$parts[0]]=$parts[1]}}
            if($values['parity'] -ne 'PROVISIONAL'){break}
            $results+=$values
        }
        if($results.Count -eq $Runs){break}
        if(-not(Get-Process -Id $ownedEmulator -ErrorAction SilentlyContinue)){throw 'Electric test emulator exited before report'}
        Start-Sleep -Milliseconds 500
    }
    if($results.Count -ne $Runs){throw 'Electric test timed out'}
    foreach($source in $identities){
        if((Get-FileHash (Join-Path $PSScriptRoot $source.path) -Algorithm SHA256).Hash.ToLower() -ne $source.sha256){throw "Source changed during electric test: $($source.path)"}
    }
    foreach($result in $results){
        if($result['frames'] -ne '900' -or $result['electric_checks'] -ne '900' -or $result['restored_os'] -ne '1'){throw 'Incomplete electric trap inspection'}
        foreach($key in @('session_fixture_failure','session_wall_fixture_failure','npc_recoil_fixture_failure','movement_fixture_failure','climb_fixture_failure','moving_net_fixture_failure','contact_fixture_failure','sprite_fixture_failure','source_dma_fixture_failure','source_dma_faults','runtime_arithmetic_errors','c64_room_fault','source_audio_faults')){
            if($result[$key] -ne '0'){throw "Electric test regression: $key"}
        }
    }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'amiga/out/autotest-frame.bpl') -Destination (Join-Path $captureRoot 'frame.bpl') -Force
    [ordered]@{date='2026-10-26';label=$Label;status='controlled_room10_presentation_diagnostic';profile='PAL68000 OCS KS1.3 512KiB Chip+512KiB slow';natural_playthrough=$false;full_parity=$false;source_files=$identities;runs=$results} |
        ConvertTo-Json -Depth 7 | Set-Content (Join-Path $captureRoot 'report.json') -Encoding UTF8
    $results | Select-Object electric_checks,electric_mismatch_fields,electric_max_streak,missed_frames,max_work_lines,held_image_fields,max_held_image_streak | Format-List
} finally {
    $ownedProcess=Get-Process -Id $ownedEmulator -ErrorAction SilentlyContinue
    if($ownedProcess){Stop-Process -InputObject $ownedProcess -ErrorAction SilentlyContinue;[void]$ownedProcess.WaitForExit(10000)}
}
