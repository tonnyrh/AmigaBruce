#Requires -Version 5.1
[CmdletBinding()]
param([switch]$LegacyBlockout)
$ErrorActionPreference='Stop'
if(!$LegacyBlockout){
    & (Join-Path $PSScriptRoot 'test-c64-rooms.ps1')
    & (Join-Path $PSScriptRoot 'test-core.ps1')
    Write-Output 'PASS scoped source-room CPU controls; full actor/natural-play parity remains open'
    return
}
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if(-not $vs){throw 'MSVC Build Tools required for host checks'}
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$testOut=Join-Path $taskRoot '.tmp/core-trace'
New-Item -ItemType Directory -Force $testOut | Out-Null
$command='set "TEMP='+$testOut+'" && set "TMP='+$testOut+'" && call "'+$vcvars+'" >nul && cl /nologo /W4 /WX /Od /Fe:"'+$testOut+'\core-trace.exe" /Fo"'+$testOut+'\\" "'+$taskRoot+'\core\game.c" "'+$taskRoot+'\tests\core_trace.c"'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Host replay compilation failed'}
& python (Join-Path $taskRoot 'tools/compare_movement.py') (Join-Path $testOut 'core-trace.exe')
if($LASTEXITCODE){throw 'Candidate regression gates failed; see reference/validation/candidate-movement.json'}
& python (Join-Path $taskRoot 'tools/compare_movement.py') (Join-Path $testOut 'core-trace.exe') --traces (Join-Path $taskRoot 'reference/traces/MACHINE-0002') --output (Join-Path $taskRoot 'reference/validation/candidate-climb.json')
if($LASTEXITCODE){throw 'Candidate climb regression gates failed; see reference/validation/candidate-climb.json'}
& python (Join-Path $taskRoot 'tools/compare_movement.py') (Join-Path $testOut 'core-trace.exe') --traces (Join-Path $taskRoot 'reference/traces/MACHINE-0003') --output (Join-Path $taskRoot 'reference/validation/candidate-net-top.json')
if($LASTEXITCODE){throw 'Candidate net-top regression gates failed; see reference/validation/candidate-net-top.json'}
& python (Join-Path $taskRoot 'tools/compare_movement.py') (Join-Path $testOut 'core-trace.exe') --traces (Join-Path $taskRoot 'reference/traces/MACHINE-0004') --output (Join-Path $taskRoot 'reference/validation/candidate-ledge-prone.json')
if($LASTEXITCODE){throw 'Candidate ledge/prone regression gates failed; see reference/validation/candidate-ledge-prone.json'}
& python (Join-Path $taskRoot 'tools/compare_movement.py') (Join-Path $testOut 'core-trace.exe') --traces (Join-Path $taskRoot 'reference/traces/MACHINE-0005') --output (Join-Path $taskRoot 'reference/validation/candidate-attacks.json')
if($LASTEXITCODE){throw 'Candidate attack regression gates failed; see reference/validation/candidate-attacks.json'}

& python (Join-Path $taskRoot 'tools/compare_attack_phase.py') (Join-Path $testOut 'core-trace.exe')
if($LASTEXITCODE){throw 'Phased attack regression failed'}
& python (Join-Path $taskRoot 'tools/compare_attack_phase.py') (Join-Path $testOut 'core-trace.exe') --capture-id PHASE-0002
if($LASTEXITCODE){throw 'Phased attack input-edge regression failed'}
& python (Join-Path $taskRoot 'tools/compare_movement.py') (Join-Path $testOut 'core-trace.exe') --traces (Join-Path $taskRoot 'reference/traces/MACHINE-0007') --output (Join-Path $taskRoot 'reference/validation/candidate-fall.json')
if($LASTEXITCODE){throw 'Fall route report failed'}
& python (Join-Path $taskRoot 'tools/measure_fall.py')
if($LASTEXITCODE){throw 'Measured C64 fall rate changed'}
& python (Join-Path $taskRoot 'tools/analyze_c64_combat.py')
if($LASTEXITCODE){throw 'Native enemy contact evidence failed'}

$combatCommand=$command.Replace('core-trace.exe','combat-trace.exe').Replace('\tests\core_trace.c','\tests\combat_trace.c')+' "'+$taskRoot+'\core\combat.c" "'+$taskRoot+'\core\rooms.c"'
& $env:ComSpec /d /s /c $combatCommand
if($LASTEXITCODE){throw 'Combat host replay compilation failed'}
& python (Join-Path $taskRoot 'tools/compare_combat.py') (Join-Path $testOut 'combat-trace.exe')
if($LASTEXITCODE){throw 'Combat entry/health regression; full mismatch report remains open'}
& python (Join-Path $taskRoot 'tools/compare_enemy_edges.py') (Join-Path $testOut 'combat-trace.exe')
if($LASTEXITCODE){throw 'Native Ninja door exit/return regression'}

$roomCommand=$combatCommand.Replace("combat-trace.exe","rooms-trace.exe").Replace("\tests\combat_trace.c","\tests\rooms_trace.c")
& $env:ComSpec /d /s /c $roomCommand
if($LASTEXITCODE){throw "Room host replay compilation failed"}
& python (Join-Path $taskRoot "tools/compare_rooms.py") (Join-Path $testOut "rooms-trace.exe")
if($LASTEXITCODE){throw "Room interaction regression failed"}
