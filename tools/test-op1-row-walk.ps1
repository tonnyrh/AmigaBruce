#Requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9-]+$')][string]$Label,
 [ValidateSet('light','profile')][string]$Variant='light',
 [ValidateRange(1,20)][int]$Room=1,[ValidateRange(0,3)][int]$EnemyMask=3,
 [ValidateRange(0,1)][int]$InputRoute=0,[ValidateRange(0,2000)][int]$WarmupSteps=240,
 [ValidateRange(60,2000)][int]$Steps=240)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$base=Join-Path $taskRoot 'reference/analysis/op1-row-walk-2026-10-31'
$folder=Join-Path $base "runs/$Label"
if(Test-Path -LiteralPath $folder){throw 'Label exists; never overwrite evidence'}
New-Item -ItemType Directory -Path $folder -Force | Out-Null
foreach($ext in @('exe','elf')){Copy-Item -LiteralPath (Join-Path $base "$Variant/bruce_amiga.$ext") -Destination $folder}
[IO.File]::WriteAllBytes((Join-Path $folder 'op0-route.bin'),[byte[]]@(($Room-1),$EnemyMask,$InputRoute,0,($WarmupSteps-shr 8),($WarmupSteps-band 255),($Steps-shr 8),($Steps-band 255)))
$paths=@('tools/build_light_op0_probe.py','tools/test-op1-row-walk.ps1','reference/analysis/op1-row-walk-2026-10-31/rows.s','reference/analysis/op1-row-walk-2026-10-31/build.py','reference/analysis/op1-row-walk-2026-10-31/run-private.ps1',
 'reference/analysis/op0-light-2026-10-31/main.c','reference/analysis/op0-light-2026-10-31/run-private.ps1',
 "reference/analysis/op1-row-walk-2026-10-31/$Variant/inputs.json")
$paths+=@(Get-ChildItem (Join-Path $taskRoot 'core'),(Join-Path $taskRoot 'amiga') -File |
 Where-Object {$_.Extension -in '.c','.h','.s'} | ForEach-Object {$_.FullName.Substring($taskRoot.Length+1).Replace('\','/')})
$paths+=@(Get-ChildItem $folder -File | ForEach-Object {$_.FullName.Substring($taskRoot.Length+1).Replace('\','/')})
$paths+=@('amiga/out/bruce_amiga.exe')
$identity=@($paths | Sort-Object -Unique | ForEach-Object {@{path=$_;sha256=(Get-FileHash -LiteralPath (Join-Path $taskRoot $_)).Hash.ToLower()}})
& (Join-Path $base 'run-private.ps1') -OutputDirectory $folder -Autotest -TestRuns 1 -EmulatorPath (Join-Path $taskRoot '.tmp/session-ui/winuae64.exe') -EmulatorIni (Join-Path $taskRoot '.tmp/session-ui/winuae.ini')
$owned=[int](Get-Content -LiteralPath (Join-Path $folder 'owned.pid'))
try{
 $deadline=(Get-Date).AddMinutes(12);$r=@{}
 while((Get-Date)-lt $deadline){
  $report=Join-Path $folder 'op0-light.txt'
  if(Test-Path -LiteralPath $report){
   $r=@{};foreach($line in Get-Content -LiteralPath $report){$parts=$line.Split('=',2);if($parts.Count-eq 2){$r[$parts[0]]=$parts[1]}}
   if($r['finished']-eq '1'){break}
  }
  if(!(Get-Process -Id $owned -ErrorAction SilentlyContinue)){throw 'Owned emulator exited before report'}
  Start-Sleep -Milliseconds 500
 }
 if($r['finished']-ne '1' -or $r['restored_os']-ne '1' -or $r['steps']-ne [string]$Steps){throw 'Incomplete normal-path measurement'}
 foreach($key in @('source_fault','dma_fault','audio_fault')){if($r[$key]-ne '0'){throw "$key=$($r[$key])"}}
 if($Variant-eq 'profile' -and $r['perf_errors']-ne '0'){throw 'Unbalanced profiler'}
 foreach($i in $identity){if((Get-FileHash -LiteralPath (Join-Path $taskRoot $i.path)).Hash.ToLower()-ne $i.sha256){throw "Input changed: $($i.path)"}}
 @{date='2026-10-31';variant=$Variant;room=$Room;enemy_mask=$EnemyMask;input_route=$InputRoute;warmup=$WarmupSteps;steps=$Steps;
  source_files=$identity;run=$r;autotest=$false;natural_playthrough=$false;edition_verified=$false;realtime_accepted=$false;
  method='Normal BL_AUTOTEST=0 engine/render/audio; diagnostic auto-start, invincibility, room selection, optional enemy exclusion, scripted input and bounded stop. No fixtures, capture, RAM/audio hashes in measured interval.'} |
  ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $folder 'identity.json') -Encoding utf8
 Write-Output "$Label`: $($r.pal_fields) PAL fields / $($r.steps) steps; work=$($r.work_lines), wait=$($r.wait_lines); audio misses=$($r.audio_missed); active=$($r.active_loops)"
}finally{
 if(Get-Process -Id $owned -ErrorAction SilentlyContinue){Stop-Process -Id $owned}
}

