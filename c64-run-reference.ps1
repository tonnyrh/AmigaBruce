#Requires -Version 5.1
[CmdletBinding()]
param([ValidateRange(1024,65535)][int]$Port=6522)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$manifest=Get-Content (Join-Path $taskRoot 'reference/manifest.json') -Raw | ConvertFrom-Json
$exe=Join-Path $taskRoot $manifest.emulator.executable_path
if((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLower() -ne $manifest.emulator.executable_sha256){throw 'VICE hash mismatch'}
$probe=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,$Port)
try{$probe.Start()}finally{$probe.Stop()}
New-Item -ItemType Directory -Force (Join-Path $taskRoot '.tmp') | Out-Null
$arguments="-default -model c64 +sound +warp -sidenginemodel 256 -binarymonitor -binarymonitoraddress 127.0.0.1:$Port -windowxpos 10 -windowypos 40 -windowwidth 900 -windowheight 780 -joydev1 1 -joydev2 0 -keyset"
$owned=Start-Process -FilePath $exe -ArgumentList $arguments -PassThru
try{
    Start-Sleep -Seconds 2
    python (Join-Path $taskRoot 'tools/start_c64_reference.py') --port $Port
    if($LASTEXITCODE){throw 'C64 reference restore failed'}
}catch{
    Stop-Process -Id $owned.Id -ErrorAction SilentlyContinue
    throw
}
$owned.Id | Set-Content (Join-Path $taskRoot '.tmp/vice-reference.pid')
Write-Output "VICE reference PID $($owned.Id); local frozen candidate, PAL, numeric keypad, sound disabled"
