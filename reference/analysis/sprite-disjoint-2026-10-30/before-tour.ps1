#Requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9-]+$')][string]$Label,[switch]$Baseline)
$ErrorActionPreference='Stop'
$taskRoot='C:\vscode\_EXT\AmigaBruceLee'
$folder=Join-Path $taskRoot ('reference/analysis/optimization-2026-10-27/'+$Label)
if(Test-Path -LiteralPath $folder){throw 'Keep previous measurements; choose a fresh label'}
New-Item -ItemType Directory -Path $folder | Out-Null
$work=Join-Path $taskRoot ('.tmp/source-tour-'+$Label);New-Item -ItemType Directory -Path $work | Out-Null
$generated=Join-Path $work 'main.c'
& python (Join-Path $taskRoot 'tools/build_source_perf_tour.py') --output $generated
if($LASTEXITCODE){throw 'Tour controller generation failed'}
$text=[IO.File]::ReadAllText($generated)
$allocation='if(BL_AUTOTEST){capture=AllocMem(BL_CAPTURE_BYTES,MEMF_PUBLIC|MEMF_CLEAR);tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}'
$guard='(BL_AUTOTEST&&(!capture||!tone))'
if(([regex]::Matches($text,[regex]::Escape($allocation)).Count -ne 1) -or ([regex]::Matches($text,[regex]::Escape($guard)).Count -ne 1)){throw 'Capture-only diagnostic anchors changed'}
$text=$text.Replace($allocation,'if(BL_AUTOTEST){tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}')
$text=$text.Replace($guard,'(BL_AUTOTEST&&!tone)')
[IO.File]::WriteAllText($generated,$text)
$builder=[IO.File]::ReadAllText((Join-Path $taskRoot 'amiga-build.ps1'))
$builder=$builder.Replace('$taskRoot=$PSScriptRoot',('$taskRoot='''+$taskRoot.Replace("'","''")+''''))
$baselineCore=Join-Path $taskRoot 'reference/analysis/final-colors-2026-10-30/before/core/c64_rooms.c'
$override='    $actualPath=Join-Path $taskRoot $source'+"`n"+'    if($source -eq ''amiga/main.c''){$actualPath='''+$generated+''';$sourceFlags+=''-I'+(Join-Path $taskRoot 'amiga')+'''}'
$override+="`n"+'    if($source -eq ''core/c64_rooms.c''){$actualPath=Join-Path $taskRoot ''reference/analysis/sprite-disjoint-2026-10-30/candidate/c64_rooms.c'';$sourceFlags+=''-I''+(Join-Path $taskRoot ''core'')}'
$override+="`n"+'    if($source -eq ''amiga/sprite_copy.s''){$actualPath=Join-Path $taskRoot ''reference/analysis/sprite-disjoint-2026-10-30/before/sprite_copy.s''}'
if($Baseline){$override+="`n"+'    if($source -eq ''core/c64_rooms.c''){$actualPath='''+$baselineCore+'''}'}
$compile='    & $compiler @sourceFlags -c (Join-Path $taskRoot $source) -o $obj'
if([regex]::Matches($builder,[regex]::Escape($compile)).Count -ne 1){throw 'Compiler override anchor changed'}
$builder=$builder.Replace($compile,($override+"`n"+'    & $compiler @sourceFlags -c $actualPath -o $obj'))
$builderPath=Join-Path $work 'build.ps1';[IO.File]::WriteAllText($builderPath,$builder)
& $builderPath -Autotest -SourcePerfTest -SpriteCopyTest -TestFrames 6000
if($LASTEXITCODE){throw 'Tour build failed'}
$files=@(Get-ChildItem (Join-Path $taskRoot 'core'),(Join-Path $taskRoot 'amiga') -File | Where-Object {$_.Extension -in '.c','.h','.s'} | ForEach-Object {$_.FullName})
$files+=@((Join-Path $taskRoot 'amiga-build.ps1'),$PSCommandPath,(Join-Path $taskRoot 'tools/build_source_perf_tour.py'),$generated,$builderPath)
if($Baseline){$files+=@(Get-ChildItem (Split-Path $baselineCore) -File | ForEach-Object {$_.FullName})}
$files+=@('reference/analysis/sprite-disjoint-2026-10-30/candidate/c64_rooms.c','reference/analysis/sprite-disjoint-2026-10-30/candidate/c64_actor_programs.h','reference/analysis/sprite-disjoint-2026-10-30/before/sprite_copy.s') | ForEach-Object {Join-Path $taskRoot $_}
$identity=@($files | Sort-Object -Unique | ForEach-Object {@{path=$_.Substring($taskRoot.Length+1).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_).Hash.ToLower()}})
$build=@('exe','elf','adf') | ForEach-Object {$p=Join-Path $taskRoot ('amiga/out/bruce_test.'+$_);Copy-Item -LiteralPath $p -Destination $folder;@{path=('bruce_test.'+$_);sha256=(Get-FileHash -LiteralPath $p).Hash.ToLower()}}
Copy-Item -LiteralPath $generated -Destination (Join-Path $folder 'compiled-main.c')
Copy-Item -LiteralPath $builderPath -Destination (Join-Path $folder 'build.ps1')
Copy-Item -LiteralPath ([IO.Path]::ChangeExtension($generated,'.json')) -Destination (Join-Path $folder 'controller-generation.json')
$runtime=Join-Path $taskRoot '.tmp/session-ui'
& (Join-Path $taskRoot 'amiga-run.ps1') -Autotest -TestRuns 1 -EmulatorPath (Join-Path $runtime 'winuae64.exe') -EmulatorIni (Join-Path $runtime 'winuae.ini')
$owned=[int](Get-Content (Join-Path $taskRoot '.tmp/winuae-test.pid'));$report=Join-Path $taskRoot 'amiga/out/autotest-1.txt'
try{
 $deadline=(Get-Date).AddMinutes(15);$run=@{}
 while((Get-Date) -lt $deadline){
  if(Test-Path -LiteralPath $report){$run=@{};foreach($line in Get-Content -LiteralPath $report){$v=$line.Split('=',2);if($v.Count -eq 2){$run[$v[0]]=$v[1]}};if($run['parity'] -eq 'PROVISIONAL'){break}}
  if(!(Get-Process -Id $owned -ErrorAction SilentlyContinue)){throw 'Owned tour emulator exited before report'}
  Start-Sleep -Milliseconds 500
 }
 Copy-Item -LiteralPath $report -Destination (Join-Path $folder 'native.txt')
 if($run['source_tour_completed'] -ne '20' -or $run['source_tour_error'] -ne '0'){throw 'Source tour did not complete20 rooms'}
 if([int]$run['frames'] -ge 6000 -or $run['restored_os'] -ne '1'){throw 'Tour exceeded limit or failed OS restore'}
 foreach($key in @('c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','vic_compare_errors','contact_kernel_errors')){if($run[$key] -ne '0'){throw "$key=$($run[$key])"}}
 if($run['contact_kernel_cases'] -ne '710' -or $run['sprite_copy_cases'] -ne '256'){throw 'Missing native reference controls'}
 $rows=@();for($i=0;$i -lt 20;$i++){
  $v=@($run['source_tour_'+$i].Split(',') | ForEach-Object {[long]$_})
  if($v.Count -ne 11 -or $v[0] -ne 120 -or $v[7] -ne $i+1){throw "Invalid room interval$i"}
  if($v[8] -lt 49152){throw "Room$($i+1) Chip reserve below49152"}
  $rows+=@{room=$i+1;steps=$v[0];fields=$v[1];lines=$v[2];missed=$v[3];drawn=$v[4];held=$v[5];preparation_lines=$v[6];chip_largest=$v[8];slow_largest=$v[9];animation_bytes=$v[10]}
 }
 foreach($item in $identity){if((Get-FileHash -LiteralPath (Join-Path $taskRoot $item.path)).Hash.ToLower() -ne $item.sha256){throw "Source changed during tour: $($item.path)"}}
 @{status='passed_scoped_20_room_timing_route';baseline=[bool]$Baseline;source_files=$identity;build=$build;rooms=$rows;run=$run;natural_playthrough=$false;realtime_accepted=$false;compile_overrides=@{main='compiled-main.c';core=$(if($Baseline){'reference/analysis/final-colors-2026-10-30/before/core/c64_rooms.c'}else{'reference/analysis/sprite-disjoint-2026-10-30/candidate/c64_rooms.c'})};method='Actual PAL intervals,120 source steps per room, continuous debug-jump history; setup excluded; unused SourcePerfTest capture allocation omitted; normal main and production allocations untouched'} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $folder 'identity.json') -Encoding utf8
 Write-Output 'PASS20-room source timing route; all Chip margins>=49152; real-time acceptance remains open'
}finally{if(Get-Process -Id $owned -ErrorAction SilentlyContinue){Stop-Process -Id $owned}}
