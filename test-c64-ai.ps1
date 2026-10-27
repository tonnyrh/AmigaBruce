#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if(-not $vs){throw 'MSVC Build Tools required for the existing AI adapter audit'}
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/c64-ai-test'
New-Item -ItemType Directory -Force $out | Out-Null
$identity=@('core/c64_sprites.c','core/c64_sprites.h','core/c64_sprite_pose_data.h','core/combat.c','core/combat.h','core/game.h','core/source_wall.c','core/source_wall.h','core/c64_hit_data.h','core/rooms.h','core/c64_rooms.h','core/c64_sfx.h','tests/ai_adapter_bridge.c','tools/audit_c64_ai.py','test-c64-ai.ps1' | ForEach-Object {
    @{path=$_;sha256=(Get-FileHash (Join-Path $taskRoot $_) -Algorithm SHA256).Hash.ToLower()}
})
$identity | ConvertTo-Json | Set-Content (Join-Path $out 'compiled-sources.json') -Encoding UTF8
$command='call "'+$vcvars+'" >nul && cl /nologo /Brepro /LD /O2 /W3 /Fe:"'+$out+'\ai.dll" /Fo"'+$out+'\\" "'+$taskRoot+'\tests\ai_adapter_bridge.c" "'+$taskRoot+'\core\source_wall.c" "'+$taskRoot+'\core\c64_sprites.c" /link /Brepro /INCREMENTAL:NO /EXPORT:bl_ai_adapter /EXPORT:bl_ai_adapter_read'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Existing AI adapter compilation failed'}
& python (Join-Path $taskRoot 'tools/audit_c64_ai.py')
if($LASTEXITCODE){throw 'C64 AI source audit failed'}
