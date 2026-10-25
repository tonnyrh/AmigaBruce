#Requires -Version 5.1
[CmdletBinding()]
param([ValidateRange(1024,65535)][int]$Port=6517)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$m=Get-Content (Join-Path $taskRoot 'reference/manifest.json') -Raw | ConvertFrom-Json
$exe=Join-Path $taskRoot $m.emulator.executable_path
if((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLower() -ne $m.emulator.executable_sha256){throw 'VICE hash mismatch'}
$probe=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,$Port)
try{$probe.Start()}finally{$probe.Stop()}
$p=Start-Process -FilePath $exe -ArgumentList "-default -model c64 +sound -binarymonitor -binarymonitoraddress 127.0.0.1:$Port" -WindowStyle Hidden -PassThru
try {
 Start-Sleep -Seconds 2
 python (Join-Path $taskRoot 'tools/capture_c64_wall.py') --port $Port
 if($LASTEXITCODE){throw 'Combat capture failed'}
} finally {
 Stop-Process -Id $p.Id -ErrorAction SilentlyContinue
 if(-not $p.WaitForExit(10000)){throw 'Owned combat VICE did not exit'}
}
