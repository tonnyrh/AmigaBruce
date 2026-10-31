$ErrorActionPreference='Stop'
Set-Location 'C:\vscode\_EXT\AmigaBruceLee'
$taskRoot=$PWD.Path
$runtime=Join-Path $taskRoot '.tmp/session-ui'
$exe=Join-Path $runtime 'winuae64.exe'
$ini=Join-Path $runtime 'winuae.ini'
$log=Join-Path $runtime 'winuaebootlog.txt'
$base='reference/analysis/audio-service-2026-10-30'
& python tools/prepare_audio_boundary_ui.py
if($LASTEXITCODE){throw 'Boot checker preparation failed'}
& ./amiga-run.ps1 -ConfigOnly
# Menu controls leave diagnostic toggles set. Use a fresh process for rooms.
$game=Start-Process -FilePath $exe -ArgumentList @('-ini',('"'+$ini+'"'),'-f',('"'+(Join-Path $taskRoot '.tmp/bruce-a500.uae')+'"')) -WorkingDirectory $runtime -WindowStyle Hidden -PassThru
try{
 Start-Sleep -Seconds 15
 & python ("$base/check-boot.py") --pid $game.Id --log $log --label cli
 if($LASTEXITCODE){throw 'Fresh room-test menu readiness failed'}
 & python tools/audit_native_animation_frame.py --pid $game.Id --log $log --label audio-boundary-native --start --samples 12 --frozen --require-coherent
 if($LASTEXITCODE){throw 'Current R12 phase check failed'}
 & python tools/audit_normal_source_clock.py --pid $game.Id --log $log
 if($LASTEXITCODE){throw 'Current source-clock check failed'}
 & python tools/audit_native_animation_frame.py --pid $game.Id --log $log --label audio-boundary-native-death --samples 12 --frozen --death --roundtrip --require-coherent
 if($LASTEXITCODE){throw 'Current death/room-switch check failed'}
}finally{if(Get-Process -Id $game.Id -ErrorAction SilentlyContinue){Stop-Process -Id $game.Id}}
& ./amiga-run.ps1 -ConfigOnly -Disk
$disk=Start-Process -FilePath $exe -ArgumentList @('-ini',('"'+$ini+'"'),'-f',('"'+(Join-Path $taskRoot '.tmp/bruce-a500.uae')+'"')) -WorkingDirectory $runtime -WindowStyle Hidden -PassThru
try{
 Start-Sleep -Seconds 15
 & python ("$base/check-boot.py") --pid $disk.Id --log $log --label adf --start-game
 if($LASTEXITCODE){throw 'Current ADF startup failed'}
}finally{if(Get-Process -Id $disk.Id -ErrorAction SilentlyContinue){Stop-Process -Id $disk.Id}}
