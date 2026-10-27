#Requires -Version 5.1
$ErrorActionPreference='Stop'
$spawnRoot=$PSScriptRoot
$env:TEMP=Join-Path $spawnRoot '.tmp/compiler-temp';$env:TMP=$env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
& python (Join-Path $spawnRoot 'tools/build_c64_rooms.py')
if($LASTEXITCODE){throw 'Source spawn translation failed'}
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $spawnRoot '.tmp/spawn-test';New-Item -ItemType Directory -Force $out | Out-Null
$sources=@('core/game.c','core/source_wall.c','core/source_climb.c','core/presentation.c','core/c64_sprites.c','core/combat.c','core/rooms.c','core/session.c','core/c64_rooms.c','core/source_audio.c','tests/spawn_bridge.c')
$exports=@('bl_spawn_prepare','bl_spawn_copy','bl_spawn_run','bl_spawn_entry_prepare','bl_spawn_entry_step','bl_spawn_entry_read','bl_spawn_entry_transition','bl_spawn_world_prepare','bl_spawn_world_step','bl_spawn_world_read','bl_spawn_bomb_prepare','bl_spawn_bomb_step','bl_c64_reset','bl_c64_load','bl_c64_read','bl_c64_test_write','bl_c64_field','bl_c64_enemy_remove','bl_c64_spawn_counter')
$quoted=($sources|ForEach-Object {'"'+(Join-Path $spawnRoot $_)+'"'}) -join ' '
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /Fe:"'+$out+'\spawn.dll" /Fo"'+$out+'\\" '+$quoted+' /link '+(($exports|ForEach-Object {'/EXPORT:'+$_}) -join ' ')
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Spawn host compilation failed'}
$identity=@($sources + @('core/c64_rooms.h','core/combat.h','core/game.h','core/c64_room_data.h','core/c64_room_programs.h') | ForEach-Object {
    @{path=$_;sha256=(Get-FileHash (Join-Path $spawnRoot $_) -Algorithm SHA256).Hash.ToLower()}
})
$identity | ConvertTo-Json | Set-Content (Join-Path $out 'compiled-sources.json') -Encoding UTF8
& python (Join-Path $spawnRoot 'tools/audit_spawn.py')
if($LASTEXITCODE){throw 'Original spawn/adapter comparison failed'}
& python (Join-Path $spawnRoot 'tools/audit_spawn_world.py')
if($LASTEXITCODE){throw 'Spawn object/door/bomb integration failed'}
& python (Join-Path $spawnRoot 'tools/build_spawn_fixture.py')
if($LASTEXITCODE){throw 'Source spawn fixture generation failed'}
