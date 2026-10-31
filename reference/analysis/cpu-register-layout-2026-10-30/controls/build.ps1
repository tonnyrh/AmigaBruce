#Requires -Version 5.1
[CmdletBinding()]
param([switch]$CompileOnly)
$ErrorActionPreference='Stop'
$actorRoot='C:\vscode\_EXT\AmigaBruceLee'
$env:TEMP=Join-Path $actorRoot '.tmp/compiler-temp';$env:TMP=$env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $actorRoot '.tmp/cpu-register-layout';New-Item -ItemType Directory -Force $out | Out-Null
$sources=@('reference/analysis/cpu-register-layout-2026-10-30/candidate/c64_rooms.c','tests/source_actor_bridge.c')
$exports=@('bl_actor_copy','bl_actor_prepare','bl_c64_reset','bl_c64_load','bl_c64_actor_seed','bl_c64_actor_test_call','bl_c64_actor_registers','bl_c64_actor_return','bl_c64_read','bl_c64_test_write','bl_c64_fault','bl_c64_field','bl_c64_world_start','bl_c64_world_input','bl_c64_world_ready','bl_c64_world_step','bl_c64_world_jump','bl_c64_world_stat')
$quoted=($sources | ForEach-Object {'"'+(Join-Path $actorRoot $_)+'"'}) -join ' '
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /I"C:\vscode\_EXT\AmigaBruceLee\core" /Fe:"'+$out+'\actors.dll" /Fo"'+$out+'\\" '+$quoted+' /link '+(($exports|ForEach-Object {'/EXPORT:'+$_}) -join ' ')
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Source actor compilation failed'}
$identity=@($sources + @('reference/analysis/cpu-register-layout-2026-10-30/candidate/c64_actor_programs.h','reference/analysis/cpu-register-layout-2026-10-30/candidate/c64_sfx.h','core/c64_rooms.h','core/source_perf.h','core/game.h','core/combat.h','core/c64_actor_data.h','core/c64_actor_programs.h',
    'core/c64_room_data.h','core/c64_room_programs.h','core/c64_sfx.h','core/c64_sound_data.h','tools/build_c64_actors.py',
    'tools/build_c64_rooms.py','test-c64-actors.ps1') | ForEach-Object {
    @{path=$_;sha256=(Get-FileHash (Join-Path $actorRoot $_)).Hash.ToLower()}
})
$identity | ConvertTo-Json | Set-Content (Join-Path $out 'compiled-sources.json') -Encoding UTF8
if(!$CompileOnly){
    & python (Join-Path $actorRoot '.tmp/cpu-register-layout/audit.py')
    if($LASTEXITCODE){throw 'Full source actor comparison failed'}
}
