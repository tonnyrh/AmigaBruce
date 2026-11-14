#Requires -Version 5.1
[CmdletBinding()]
param([ValidateRange(0,3)][int]$PerfEnemies=3,[ValidateRange(0,30000)][int]$PerfSourceSteps=0,[switch]$Autotest,[switch]$SourceWorldTest,[switch]$SourcePerfTest,[switch]$SourceProfile,[switch]$SeparateContactTest,[switch]$SpriteCopyTest,[switch]$CollectFrameDrops,[switch]$CombatTest,[switch]$RoomsTest,[switch]$EnemyEdgeTest,[switch]$RoomTour,[switch]$GateTest,[switch]$RoomLoadTest,[switch]$RoomLoadBaseline,[switch]$ElectricTest,[ValidateRange(0,19)][int]$TestStartRoom=0,[ValidateRange(0,2000)][int]$CombatWarmupSteps=0,[ValidateRange(360,30000)][int]$TestFrames=360,
      [string]$PythonExecutable)
$ErrorActionPreference='Stop'
if($PerfSourceSteps -and !$SourcePerfTest){throw 'PerfSourceSteps requires SourcePerfTest'}
if($RoomsTest -or $EnemyEdgeTest -or $RoomTour -or $GateTest -or $RoomLoadTest){$CombatTest=$true}
$taskRoot=$PSScriptRoot
$buildPython = & (Join-Path $taskRoot 'tools/resolve-art-python.ps1') -PythonExecutable $PythonExecutable
Write-Host "Build Python: $buildPython"
& $buildPython (Join-Path $taskRoot 'tools/build_contact_class_kernel.py')
if($LASTEXITCODE){throw 'Source contact class kernel generation failed'}
& $buildPython (Join-Path $taskRoot 'tools/build_c64_audio.py')
if($LASTEXITCODE){throw 'Source audio extraction failed'}
& $buildPython (Join-Path $taskRoot 'tools/build_enhanced_audio.py')
if($LASTEXITCODE){throw 'Enhanced combat sample packing failed'}
& $buildPython (Join-Path $taskRoot 'tools/build_c64_sprites.py')
if($LASTEXITCODE){throw 'C64 sprite extraction failed'}
& $buildPython (Join-Path $taskRoot 'tools/build_enhanced_art.py')
if($LASTEXITCODE){throw 'Enhanced artwork preparation failed'}
& $buildPython (Join-Path $taskRoot 'tools/build_title_art.py')
if($LASTEXITCODE){throw 'Title art packing failed'}
& $buildPython (Join-Path $taskRoot 'tools/build_c64_hit_masks.py')
if($LASTEXITCODE){throw 'C64 combat mask extraction failed'}
& $buildPython (Join-Path $taskRoot 'tools/build_c64_rooms.py')
if($LASTEXITCODE){throw 'C64 room compilation failed'}
& $buildPython (Join-Path $taskRoot 'tools/build_c64_actors.py')
if($LASTEXITCODE){throw 'C64 actor compilation failed'}
$extension=Get-ChildItem -Directory (Join-Path $env:USERPROFILE '.vscode/extensions') -Filter 'bartmanabyss.amiga-debug-*' |
    Sort-Object Name -Descending | Select-Object -First 1
if(-not $extension){throw 'BartmanAbyss Amiga toolchain not found.'}
$bin=Join-Path $extension.FullName 'bin/win32'
$compiler=Join-Path $bin 'opt/bin/m68k-amiga-elf-gcc.exe'
$converter=Join-Path $bin 'elf2hunk.exe'
$out=Join-Path $taskRoot 'amiga/out'
New-Item -ItemType Directory -Force $out | Out-Null
$flags=@('-m68000','-O2','-g','-nostdlib','-ffreestanding','-fno-builtin','-fno-tree-loop-distribute-patterns','-fomit-frame-pointer','-ffunction-sections','-fdata-sections','-Wall','-Wextra','-Wno-volatile-register-var','-Wno-array-bounds')
$flags += if($Autotest){'-DBL_AUTOTEST=1'}else{'-DBL_AUTOTEST=0'}
if($SourcePerfTest){if(!$Autotest){throw 'SourcePerfTest requires Autotest'};$SourceWorldTest=$true;$flags+='-DBL_SOURCE_PERF_TEST=1';$flags+="-DBL_SOURCE_PERF_ENEMIES=$PerfEnemies";$flags+="-DBL_SOURCE_PERF_STEPS=$PerfSourceSteps"}
if($SourceWorldTest){if(!$Autotest){throw 'SourceWorldTest requires Autotest'};$flags+='-DBL_SOURCE_WORLD_TEST=1';$flags+='-DBL_COMBAT_TEST=1';$flags+='-DBL_COLLECT_FRAME_DROPS=1'}
if($SpriteCopyTest){if(!$SourcePerfTest -or $SourceProfile){throw 'SpriteCopyTest requires unprofiled SourcePerfTest'};$flags+='-DBL_SPRITE_COPY_TEST=1'}
if($SeparateContactTest){if(!$SourceWorldTest -or $SourcePerfTest){throw 'SeparateContactTest requires full SourceWorldTest'};$flags+='-DBL_SEPARATE_CONTACT_TEST=1'}
if($SourceProfile){$flags+='-DBL_C64_PROFILE=1'}
if($CollectFrameDrops){if(!$Autotest -or (!$RoomTour -and !$CombatTest)){throw 'CollectFrameDrops requires an autotest room tour or combat replay'};$flags+='-DBL_COLLECT_FRAME_DROPS=1'}
if($TestStartRoom){if(!$Autotest -or !$RoomTour){throw 'TestStartRoom requires an autotest room tour'};$flags+="-DBL_TEST_START_ROOM=$TestStartRoom"}
if($Autotest){$flags+="-DBL_TEST_FRAMES=$TestFrames"}
if($CombatTest){$flags+='-DBL_COMBAT_TEST=1';$flags+="-DBL_COMBAT_WARMUP=$CombatWarmupSteps"}
if($ElectricTest){if(!$Autotest -or !$CombatTest){throw 'ElectricTest requires Autotest and CombatTest'};$flags+='-DBL_ELECTRIC_TEST=1'}
if($RoomsTest){$flags+='-DBL_ROOM_TEST=1'}
if($EnemyEdgeTest){$flags+='-DBL_ENEMY_EDGE_TEST=1'}
if($RoomTour){$flags+='-DBL_ROOM_TOUR=1'}
if($GateTest){$flags+='-DBL_GATE_TEST=1'}
if($RoomLoadTest){if(!$Autotest){throw 'RoomLoadTest requires Autotest'};$flags+='-DBL_ROOM_LOAD_TEST=1'}
if($RoomLoadBaseline){if(!$RoomLoadTest){throw 'RoomLoadBaseline requires RoomLoadTest'};$flags+='-DBL_ROOM_REUSE=0'}
$sources=@('amiga/start.s','amiga/vic_compare.s','amiga/contact_rows.s','amiga/sprite_copy.s','amiga/contact_align.s','amiga/contact_prepare.s','amiga/main.c','amiga/runtime.c','core/game.c','core/source_wall.c','core/source_climb.c','core/presentation.c','core/c64_sprites.c','core/combat.c','core/rooms.c','core/session.c','core/c64_rooms.c','core/source_audio.c','core/source_dma.c','amiga/vic_wide.s')
$objects=@()
foreach($source in $sources){
    $obj=Join-Path $out ([IO.Path]::GetFileNameWithoutExtension($source)+'.o')
    $sourceFlags=@($flags);if($source -eq 'core/c64_rooms.c'){$sourceFlags+='-mshort';$sourceFlags+='-Os'}
    & $compiler @sourceFlags -c (Join-Path $taskRoot $source) -o $obj
    if($LASTEXITCODE){throw "Compile failed: $source"}
    $objects+=$obj
}
$program=Join-Path $out $(if($Autotest){'bruce_test'}else{'bruce_amiga'})
& $compiler @flags '-Wl,--emit-relocs,--gc-sections,-Ttext=0,-e,_start' "-Wl,-Map=$program.map" @objects -o "$program.elf"
if($LASTEXITCODE){throw 'Link failed'}
& $buildPython (Join-Path $taskRoot 'tools/verify_amiga_entry.py') "$program.elf"
if($LASTEXITCODE){throw 'AmigaDOS entry validation failed'}
& $converter "$program.elf" "$program.exe"
if($LASTEXITCODE){throw 'ELF to Hunk conversion failed'}
& (Join-Path $bin 'exe2adf.exe') -i "$program.exe" -l 'Bruce' -a "$program.adf"
if($LASTEXITCODE){throw 'ADF creation failed'}
Get-Item "$program.exe","$program.adf" | Select-Object Name,Length
