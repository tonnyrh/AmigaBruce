$ErrorActionPreference='Stop'
Set-Location 'C:\vscode\_EXT\AmigaBruceLee'
$base='reference/analysis/enemy-cost-2026-10-30'
& python tools/build_enemy_cost_probe.py
if($LASTEXITCODE){throw 'Enemy-cost probe generation failed'}
$frozen=@('amiga/main.c','core/c64_rooms.c','core/c64_actor_programs.h',"$base/main.c","$base/build.ps1","$base/scope.json") | ForEach-Object {@{path=$_;sha256=(Get-FileHash -LiteralPath $_).Hash.ToLower()}}
foreach($case in @(@{name='none';mask=0},@{name='yamo';mask=1},@{name='kage';mask=2},@{name='both';mask=3})){
 & ("./$base/build.ps1") -Autotest -SourcePerfTest -SourceProfile -PerfEnemies $case.mask -PerfSourceSteps 360 -TestFrames 1800
 if($LASTEXITCODE){throw 'Enemy-cost profile build failed'}
 & ./test-source-performance.ps1 -Label ('enemy-cost-'+$case.name+'-profile') -Profile -PerfEnemies $case.mask -SourceSteps 360 -TestFrames 1800 -SkipBuild
 if($LASTEXITCODE){throw 'Enemy-cost profile execution failed'}
 $folder='reference/analysis/optimization-2026-10-27/enemy-cost-'+$case.name+'-profile'
 Copy-Item -LiteralPath "$base/main.c" -Destination ($folder+'/compiled-main.c')
 Copy-Item -LiteralPath "$base/build.ps1" -Destination ($folder+'/compiled-build.ps1')
 foreach($entry in $frozen){if((Get-FileHash -LiteralPath $entry.path).Hash.ToLower() -ne $entry.sha256){throw ('Input changed: '+$entry.path)}}
 @{production_changed=$false;actual_inputs=$frozen;mask=$case.mask;stationary_actors=$false;source='current production core';main='compiled-main.c';builder='compiled-build.ps1'} | ConvertTo-Json -Depth 8 | Set-Content ($folder+'/compile-overrides.json') -Encoding utf8
}
