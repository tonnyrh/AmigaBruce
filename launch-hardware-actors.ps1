#Requires -Version 5.1
[CmdletBinding()]
param([ValidateSet('v5')][string]$Version='v5',[switch]$ShowWindow,[switch]$Disk)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$out=Join-Path $taskRoot "reference/analysis/hardware-bruce-2026-10-31/$Version/sprite/out"
$exe=Join-Path $out 'bruce_amiga.exe'
if(!(Test-Path -LiteralPath $exe)){throw 'Build the selected hardware-sprite test first'}
$runtime=Join-Path $taskRoot $(if($Disk){".tmp/hardware-bruce-$Version-adf-ui"}else{".tmp/hardware-bruce-$Version-ui"})
$boot=Join-Path $runtime 'boot'
New-Item -ItemType Directory -Force $runtime,$boot | Out-Null
$emulator=Join-Path $runtime 'winuae64.exe'
if(!(Test-Path -LiteralPath $emulator)){Copy-Item -LiteralPath (Join-Path $taskRoot '.tmp/session-ui/winuae64.exe') -Destination $emulator}
$baselineConfig=& (Join-Path $taskRoot 'reference/analysis/hardware-bruce-2026-10-31/v5/run-private.ps1') -OutputDirectory $out -ConfigOnly
Copy-Item -LiteralPath (Join-Path $taskRoot '.tmp/session-ui/winuae.ini') -Destination (Join-Path $runtime 'winuae.ini') -Force
Copy-Item -LiteralPath (Join-Path $taskRoot '.tmp/hardware-actors-boot/c'),(Join-Path $taskRoot '.tmp/hardware-actors-boot/s') -Destination $boot -Recurse -Force
Copy-Item -LiteralPath $exe -Destination (Join-Path $boot 'c/start') -Force
$text=[IO.File]::ReadAllText($baselineConfig)
$text=$text.Replace((Join-Path $taskRoot 'amiga/out'),$out).Replace((Join-Path $taskRoot '.tmp/hardware-actors-boot'),$boot)
$text=$text.Replace('gfx_width_windowed=960','gfx_width_windowed=640').Replace('gfx_height_windowed=768','gfx_height_windowed=512')
if($Disk){
    $adf=Join-Path $out 'bruce_amiga.adf'
    if(!(Test-Path -LiteralPath $adf)){throw 'Pack the hardware-sprite ADF first'}
    $text=($text -split "`n" | Where-Object {$_ -notmatch '^filesystem2=rw,dh0:'}) -join "`n"
    $text+="`nfloppy0=$adf`nfloppy0wp=true`n"
}
$config=Join-Path $runtime "hardware-bruce-$Version.uae"
[IO.File]::WriteAllText($config,$text,[Text.Encoding]::ASCII)
$style=if($ShowWindow){'Normal'}else{'Hidden'}
$process=Start-Process -FilePath $emulator -ArgumentList @('-ini',('"'+(Join-Path $runtime 'winuae.ini')+'"'),'-f',('"'+$config+'"')) -WorkingDirectory $runtime -WindowStyle $style -PassThru
$process.Id | Set-Content (Join-Path $runtime 'owned.pid')
Write-Output "Hardware actors $Version PID $($process.Id); own config/boot; normal build retained"
