$ErrorActionPreference='Stop'
Set-Location 'C:\vscode\_EXT\AmigaBruceLee'
$taskRoot=$PWD.Path
$runtime=Join-Path $taskRoot '.tmp/session-ui'
$base='reference/analysis/audio-service-2026-10-30'
$ready=$false
for($attempt=0;$attempt -lt 10;$attempt++){
 try{& ./amiga-run.ps1 -ConfigOnly -Disk;$ready=$true;break}
 catch{if($_.Exception.Message -notlike '*used by another process*'){throw};Start-Sleep -Seconds 1}
}
if(!$ready){throw 'Startup file still locked after owned process shutdown'}
$disk=Start-Process -FilePath (Join-Path $runtime 'winuae64.exe') -ArgumentList @('-ini',('"'+(Join-Path $runtime 'winuae.ini')+'"'),'-f',('"'+(Join-Path $taskRoot '.tmp/bruce-a500.uae')+'"')) -WorkingDirectory $runtime -WindowStyle Hidden -PassThru
try{
 Start-Sleep -Seconds 15
 & python ("$base/check-boot.py") --pid $disk.Id --log (Join-Path $runtime 'winuaebootlog.txt') --label adf --start-game
 if($LASTEXITCODE){throw 'Current ADF startup failed'}
}finally{if(Get-Process -Id $disk.Id -ErrorAction SilentlyContinue){Stop-Process -Id $disk.Id;Wait-Process -Id $disk.Id -Timeout 10 -ErrorAction SilentlyContinue}}
