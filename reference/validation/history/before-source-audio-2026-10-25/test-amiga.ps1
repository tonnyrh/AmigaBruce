#Requires -Version 5.1
[CmdletBinding()]
param([switch]$CollectFrameDrops,[switch]$SourceRooms,[switch]$Disk,[switch]$CombatTest,[switch]$RoomsTest,[switch]$EnemyEdgeTest,[switch]$RoomTour,[switch]$GateTest,[ValidateRange(0,2000)][int]$CombatWarmupSteps=0,[switch]$SkipBuild,[ValidateRange(360,30000)][int]$TestFrames=360)
$ErrorActionPreference='Stop'
if($SourceRooms){$RoomTour=$true}
if($CollectFrameDrops -and !$SourceRooms -and !$CombatTest){throw 'Collection requires source-room inspection or combat replay; it does not pass the real-time gate'}
if($GateTest){$CombatTest=$true;if($RoomsTest -or $EnemyEdgeTest -or $RoomTour -or $CombatWarmupSteps){throw 'Choose one fixture'};if(!$PSBoundParameters.ContainsKey('TestFrames')){$TestFrames=900};if($TestFrames -ne 900){throw 'Gate fixture requires900 fields'}}
if($RoomTour){$CombatTest=$true;if($RoomsTest -or $EnemyEdgeTest -or $CombatWarmupSteps){throw 'Choose one fixture'};if(!$PSBoundParameters.ContainsKey('TestFrames')){$TestFrames=7200};if($TestFrames -ne 7200){throw 'Room tour requires7200 fields'}}
if($EnemyEdgeTest){$CombatTest=$true;if($RoomsTest){throw 'Choose one fixture'};if(!$PSBoundParameters.ContainsKey('TestFrames')){$TestFrames=1080};if($TestFrames -ne 1080 -or $CombatWarmupSteps){throw 'Enemy edge fixture requires1080 fields and no warmup'}}
if($RoomsTest){$CombatTest=$true;if(!$PSBoundParameters.ContainsKey('TestFrames')){$TestFrames=900}}
if($CombatTest -and !$RoomsTest -and !$EnemyEdgeTest -and !$RoomTour -and !$GateTest -and !$PSBoundParameters.ContainsKey('TestFrames')){$TestFrames=6000}
if($RoomsTest -and ($CombatWarmupSteps -or $TestFrames -ne 900)){throw 'Room fixture requires900 fields and no warmup'}
if($CombatWarmupSteps -and (!$CombatTest -or $TestFrames -ge 6000)){throw 'Warmup is only for shorter diagnostic combat runs'}
if($CombatTest -and $TestFrames -lt 900){throw 'Combat route requires at least 900 fields for both enemy entries'}
if(-not $SkipBuild){& (Join-Path $PSScriptRoot 'amiga-build.ps1') -Autotest -CollectFrameDrops:$CollectFrameDrops -CombatTest:$CombatTest -RoomsTest:$RoomsTest -EnemyEdgeTest:$EnemyEdgeTest -RoomTour:$RoomTour -GateTest:$GateTest -CombatWarmupSteps $CombatWarmupSteps -TestFrames $TestFrames}
$executableHash=(Get-FileHash (Join-Path $PSScriptRoot 'amiga/out/bruce_test.exe') -Algorithm SHA256).Hash.ToLower()
$adfHash=(Get-FileHash (Join-Path $PSScriptRoot 'amiga/out/bruce_test.adf') -Algorithm SHA256).Hash.ToLower()
$fighterExpected=Get-Content (Join-Path $PSScriptRoot 'assets/graphics/v2/fighter-dma-manifest.json') -Raw | ConvertFrom-Json
$introExpected=(& python (Join-Path $PSScriptRoot 'tools/verify_intro_audio.py') --assets-only | ConvertFrom-Json)
if($LASTEXITCODE){throw 'Intro asset check failed'}
$sourceIdentity=@('amiga/intro_audio.h','amiga/intro_audio_data.h','tools/build_intro_audio.py','tools/verify_intro_audio.py','assets/audio/intro-v1/manifest.json','assets/audio/intro-v1/generation.json','assets/audio/intro-v1/kiai-source_0.wav','amiga/main.c','amiga/fighter_art_data.h','amiga/fighter_dma_data.h','tools/build_fighter_dma.py','assets/graphics/v2/fighter-dma-manifest.json','tools/build_fighter_art.py','assets/graphics/v2/bruce-source.png','assets/graphics/v2/ninja-source.png','assets/graphics/v2/yamo-green-source-v3.png','assets/graphics/v2/yamo-green-v3-generation.json','assets/graphics/v2/generation.json','assets/graphics/v1/mountains-indexed.png','amiga/combat_audio.h','amiga/combat_audio_data.h','amiga/room_background_data.h','tools/build_room_backgrounds.py','amiga/runtime.c','amiga/start.s','core/game.c','core/game.h','core/presentation.c','core/presentation.h','core/combat.c','core/combat.h','core/rooms.c','core/rooms.h','core/room_data.h','core/room_geometry.h','core/c64_rooms.c','core/c64_rooms.h','core/c64_room_data.h','core/c64_room_programs.h','tools/build_c64_rooms.py','assets/c64/rooms-v1/manifest.json','tests/room_fixture.h','tests/gate_fixture.h','test-amiga.ps1','amiga-build.ps1','amiga-run.ps1','tools/preview_planar.py' | ForEach-Object {
    @{path=$_;sha256=(Get-FileHash (Join-Path $PSScriptRoot $_) -Algorithm SHA256).Hash.ToLower()}
})
& (Join-Path $PSScriptRoot 'amiga-run.ps1') -Autotest -Disk:$Disk
$ownedEmulator=[int](Get-Content (Join-Path $PSScriptRoot '.tmp/winuae-test.pid'))
$needed=if($Disk){1}else{2}
# Host device/window initialization can exceed90s before WinUAE emulates
# anything. This allowance does not relax the measured PAL field contract.
$deadline=[DateTime]::UtcNow.AddSeconds(240+($TestFrames/50)*$needed)
try {
    $results=@()
    while([DateTime]::UtcNow -lt $deadline){
        $results=@()
        for($n=1;$n -le $needed;$n++){
            $path=Join-Path $PSScriptRoot "amiga/out/autotest-$n.txt"
            if(-not(Test-Path -LiteralPath $path)){break}
            $values=@{}
            foreach($line in Get-Content -LiteralPath $path){
                $parts=$line.Split('=',2)
                if($parts.Count -eq 2){$values[$parts[0]]=$parts[1]}
            }
            if($values['parity'] -ne 'PROVISIONAL'){break}
            $results+=$values
        }
        if($results.Count -eq $needed){break}
        if(-not(Get-Process -Id $ownedEmulator -ErrorAction SilentlyContinue)){throw 'Test emulator exited before report'}
        Start-Sleep -Milliseconds 500
    }
    if($results.Count -ne $needed){throw 'A500 test timed out; inspect the owned emulator before retrying'}
    foreach($source in $sourceIdentity){
        if((Get-FileHash (Join-Path $PSScriptRoot $source.path) -Algorithm SHA256).Hash.ToLower() -ne $source.sha256){throw "Source changed during emulator run: $($source.path)"}
    }
    foreach($result in $results){
        if($result['collect_frame_drops'] -ne [string][int][bool]$CollectFrameDrops){throw 'Timing collection build differs from requested mode'}
        if($result['source_profile'] -ne '0'){throw 'Detailed profiling build is diagnostic and cannot satisfy this validation'}
        if($result['runtime_arithmetic_errors'] -ne '0'){throw 'Native68000 arithmetic differs from the independent reference'}
        if($result['intro_pcm_hash'] -ne [string]$introExpected.native_decode_fnv -or $result['intro_samples'] -ne [string]$introExpected.samples){throw 'Native intro ADPCM decode mismatch'}
        foreach($key in @('intro_silence_reload','intro_finished','intro_dma_stopped','intro_bitmap_restored')){
            if($result[$key] -ne '1'){throw "Intro one-shot/bitmap handoff failed: $key"}
        }
        if([int]$result['intro_fields'] -lt 118 -or [int]$result['intro_fields'] -gt 600){throw 'Intro loading stage outside expected PAL window'}
        if(!$CollectFrameDrops -and [int]$result['max_gap_excluding_framebuffer_capture'] -gt 1){throw 'A500 field gap exceeded one period; runtime stopped early and restored OS'}
        if($result['frames'] -ne [string]$TestFrames -or $result['restored_os'] -ne '1'){throw 'Runtime/restore contract failed'}
        if($result['bad_presents'] -ne '0' -or [int]$result['present_min_line'] -lt 300 -or [int]$result['present_max_line'] -gt 308){throw 'Copper pointer published outside safe blanking window'}
        if([int]$result['chip_largest_loaded'] -lt $(if($Disk){65536}else{49152})){throw 'Insufficient contiguous Chip RAM headroom'}
        if($result['sfx_variant_mask'] -ne '15' -or [int]$result['sfx_played'] -lt 4 -or $result['sfx_played'] -ne $result['sfx_silence_reloads']){throw 'Audio variants or one-shot DMA reload contract failed'}
        if($CombatTest -and $result['canvas_residue_bytes'] -ne '0'){throw 'Actor pixels remain outside the current drawing bounds'}
        if(!$CollectFrameDrops -and [int]$result['max_gap_excluding_framebuffer_capture'] -gt 1){throw 'A500 renderer missed a PAL period outside explicit capture'}
        if($GateTest){
            if($result['gate_test'] -ne '1' -or $result['gate_checks'] -ne '127' -or $result['room_transitions'] -ne '3' -or $result['lantern_pickups'] -ne '31' -or $result['score'] -ne '3875'){throw 'Native opening/return regression failed'}
            if(([int]$result['pose_bruce'] -band 240) -ne 240){throw 'Four climb phases not drawn'}
        }elseif($RoomTour){
            if($result['visited_rooms_mask'] -ne '1048575' -or [int]$result['room_load_events'] -lt 19){throw 'Room tour did not visit all20 rooms'}
            if($SourceRooms -and ($result['c64_room_fault'] -ne '0' -or $result['c64_render_mismatches'] -ne '0' -or [int]$result['c64_render_checks'] -lt 20)){throw 'Native source room program reported a fault'}
            if($result['room_tour'] -ne '1'){throw 'Room tour profile missing'}
            $expectedChip=163840+106496+2048+4004+32+[int]$fighterExpected.cache_bytes+[int]$fighterExpected.clip_scratch_bytes
            if([int]$result['explicit_chip_bytes'] -ne $expectedChip){throw 'Room tour Chip allocations differ from explicit cache budget'}
            if($result['fighter_cache_bytes'] -ne [string]$fighterExpected.cache_bytes -or $result['fighter_cache_hash'] -ne [string]$fighterExpected.native_fnv){throw 'Native fighter cache decode differs from offline bytes'}
        }elseif($EnemyEdgeTest){
            if($result['enemy_edge_test'] -ne '1' -or $result['enemy_edge_checks'] -ne '15'){throw 'Native Ninja exit/return event mismatch'}
            if($result['room_transitions'] -ne '0'){throw 'Edge fixture changed player room'}
        }elseif($RoomsTest){
            if($result['room_test'] -ne '1' -or $result['room_load_events'] -ne '2'){throw 'Room loads not exercised'}
            $hostEvidence=Get-Content (Join-Path $PSScriptRoot 'reference/validation/m3-core.json') -Raw | ConvertFrom-Json
            foreach($source in $hostEvidence.source_files){
                if((Get-FileHash (Join-Path $PSScriptRoot $source.path) -Algorithm SHA256).Hash.ToLower() -ne $source.sha256){throw 'Room host evidence stale'}
            }
            $expected=@($hostEvidence.output | Where-Object {$_ -like 'M4_900 *'})
            if($expected.Count -ne 1){throw 'Missing room fixture evidence'}
            foreach($entry in $expected[0].Split(' ')[1..6]){
                $pair=$entry.Split('=');if($result[$pair[0]] -ne $pair[1]){throw "68000/host room replay mismatch: $($pair[0])"}
            }
        }elseif($CombatTest){
            if($result['combat_mode'] -ne '1' -or [int]$result['enemy_spawns'] -lt 2 -or [int]$result['combat_hits'] -lt 1){throw 'Live enemy route did not exercise both spawns and contact'}
            if($TestFrames -ge 6000 -and ([int]$result['player_deaths'] -lt 1 -or [int]$result['player_respawns'] -lt 1 -or [int]$result['enemy_defeats'] -lt 1)){throw 'Live enemy route did not exercise defeat and respawn on both sides'}
            if($TestFrames -eq 6000){
                $hostEvidence=Get-Content (Join-Path $PSScriptRoot 'reference/validation/m3-core.json') -Raw | ConvertFrom-Json
                foreach($source in $hostEvidence.source_files){
                    if((Get-FileHash (Join-Path $PSScriptRoot $source.path) -Algorithm SHA256).Hash.ToLower() -ne $source.sha256){throw 'Host combat evidence is stale; run test-core.ps1 first'}
                }
                $expected=@($hostEvidence.output | Where-Object {$_ -like 'M3_6000 *'})
                if($expected.Count -ne 1){throw 'Missing host combat fixture result'}
                foreach($entry in $expected[0].Split(' ')[1..7]){
                    $pair=$entry.Split('=');if($result[$pair[0]] -ne $pair[1]){throw "68000/host combat replay mismatch: $($pair[0])"}
                }
            }
        }else{
            foreach($key in @('climb_periods','air_periods','jump_starts','fall_starts','prone_periods','punch_periods')){
                if([int]$result[$key] -lt 1){throw "Movement route did not exercise $key"}
            }
            if($TestFrames -gt 360 -and [int]$result['kick_periods'] -lt 1){throw 'Soak did not exercise flying kick'}
            if($TestFrames -ge 1500){
                foreach($key in @('target_hits','target_defeats','target_respawns','target_stomps')){
                    if([int]$result[$key] -lt 1){throw "Combat lab route did not exercise $key"}
                }
            }
            if($TestFrames -ge 1800){
                if($result['timing_seen'] -ne '63' -or $result['timing_mode_changes'] -ne '0'){throw 'Timing event markers or stable PAL field mode missing'}
                if([int]$result['timing_pal_lines'] -notin @(312,313)){throw 'Unexpected PAL field length'}
                foreach($event in @(@('walk',39),@('jump',42),@('fall',87))){
                    if([Math]::Abs([int]$result["timing_$($event[0])_fields"]-[int]$event[1]) -gt 1){throw "Unexpected $($event[0]) elapsed hardware-field count"}
                }
            }
        }
    }
    if($needed -eq 2){
        foreach($key in @('chip_available_before','expansion_available_before','final_x','final_y')){
            if($results[0][$key] -ne $results[1][$key]){throw "Repeat-launch mismatch: $key"}
        }
    }
    $validation=Join-Path $PSScriptRoot 'reference/validation'
    New-Item -ItemType Directory -Force $validation | Out-Null
    $name=if($CollectFrameDrops -and $SourceRooms){'a500-c64-rooms-diagnostic.json'}elseif($CollectFrameDrops){'a500-c64-combat-diagnostic.json'}elseif($SourceRooms){'a500-c64-rooms.json'}elseif($GateTest){'a500-gates.json'}elseif($RoomTour){'a500-room-tour.json'}elseif($EnemyEdgeTest){'a500-enemy-edges.json'}elseif($RoomsTest){'a500-m4-rooms.json'}elseif($CombatTest -and $CombatWarmupSteps){'a500-m3-debug.json'}elseif($CombatTest){'a500-m3-combat.json'}elseif($TestFrames -gt 360){'a500-soak.json'}elseif($Disk){'a500-adf-boot.json'}else{'a500-repeat-launch.json'}
    $preview=$null
    if($CombatTest){
        $imagePath=if($SourceRooms){'docs/images/c64-source-rooms.png'}elseif($GateTest){'docs/images/m4-gates.png'}elseif($RoomTour){'docs/images/room-tour.png'}elseif($EnemyEdgeTest){'docs/images/enemy-edge.png'}elseif($RoomsTest){'docs/images/m4-rooms.png'}elseif($CombatWarmupSteps){'docs/images/m3-repeat.png'}else{'docs/images/m3-combat.png'}
        & python (Join-Path $PSScriptRoot 'tools/preview_planar.py') (Join-Path $PSScriptRoot 'amiga/out/autotest-frame.bpl') (Join-Path $PSScriptRoot $imagePath) --color15 ([int]$results[0]['capture_color15']) --interleaved
        if($LASTEXITCODE){throw 'Combat framebuffer preview failed'}
        $preview=@{path=$imagePath;sha256=(Get-FileHash (Join-Path $PSScriptRoot $imagePath) -Algorithm SHA256).Hash.ToLower()}
    }
    $report=[ordered]@{
        date=(Get-Date -Format 'yyyy-MM-dd');profile='PAL A500 68000 OCS 512KiB Chip + 512KiB slow; Kickstart 1.3';
        execution=$(if($Disk){'ADF boot'}else{'filesystem CLI, two consecutive launches'});
        status=$(if($CollectFrameDrops){'completed_source_inspection_not_a_realtime_pass'}else{'passed_prototype_runtime_contract'});
        collection_only=[bool]$CollectFrameDrops;chip_headroom_requirement=$(if($Disk){65536}else{49152});realtime_contract_passed=(@($results | Where-Object {[int]$_['max_gap_excluding_framebuffer_capture'] -gt 1}).Count -eq 0);
        c64_parity='not_certified';runs=$results;
        preview=$preview;
        executable_sha256=$executableHash;
        adf_sha256=$adfHash;
        uae_config_sha256=(Get-FileHash (Join-Path $PSScriptRoot '.tmp/bruce-a500-test.uae') -Algorithm SHA256).Hash.ToLower();
        source_files=$sourceIdentity
    }
    $report | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $validation $name) -Encoding UTF8
    if(!$CombatTest -and $TestFrames -ge 1800){
        & python (Join-Path $PSScriptRoot 'tools/compare_movement_timing.py')
        if($LASTEXITCODE){throw 'Movement timing comparison failed'}
    }
    if($CollectFrameDrops){Write-Output "COLLECTED: $needed run(s), $TestFrames loop fields each; real-time gate passed=$($report.realtime_contract_passed). See timing deviations in $name"}
    else{Write-Output "PASS: $($report.execution); $needed run(s), $TestFrames periods each, one-period runtime gap, safe blanking, OS restored"}
} finally {
    # Only the process created by this test is stopped.
    $ownedProcess=Get-Process -Id $ownedEmulator -ErrorAction SilentlyContinue
    if($ownedProcess){
        Stop-Process -InputObject $ownedProcess -ErrorAction SilentlyContinue
        if(-not $ownedProcess.WaitForExit(10000)){throw 'Owned emulator did not exit; disk image may still be locked'}
    }
}

