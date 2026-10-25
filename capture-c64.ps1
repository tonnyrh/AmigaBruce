#Requires -Version 5.1
[CmdletBinding()]
param([ValidateRange(1024,65535)][int]$Port=6512,[string[]]$Scenario,
      [ValidatePattern('^[A-Z][A-Z0-9-]*$')][string]$CaptureId='MACHINE-0001',
      [string]$ScenarioFile)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$manifest=Get-Content (Join-Path $taskRoot 'reference/manifest.json') -Raw | ConvertFrom-Json
$exe=Join-Path $taskRoot $manifest.emulator.executable_path
if((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLower() -ne $manifest.emulator.executable_sha256){throw 'VICE executable hash mismatch'}
# Refuse an occupied port instead of connecting to another emulator.
$probe=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,$Port)
try{$probe.Start()}finally{$probe.Stop()}
$p=Start-Process -FilePath $exe -ArgumentList "-default -model c64 +sound -binarymonitor -binarymonitoraddress 127.0.0.1:$Port" -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskRoot '.tmp/vice-capture.log') -RedirectStandardError (Join-Path $taskRoot '.tmp/vice-capture-err.log')
try {
    Start-Sleep -Seconds 2
    $captureArgs=@('--port',$Port,'--capture-id',$CaptureId,'--output',(Join-Path $taskRoot "reference/traces/$CaptureId"))
    foreach($name in $Scenario){$captureArgs+=@('--scenario',$name)}
    if($ScenarioFile){$captureArgs+=@('--scenario-file',(Resolve-Path -LiteralPath $ScenarioFile).Path)}
    & python (Join-Path $taskRoot 'tools/capture_c64_movement.py') @captureArgs
    if($LASTEXITCODE){throw 'C64 candidate replay failed'}
} finally {
    # Only terminate the instance created above.
    Stop-Process -Id $p.Id -ErrorAction SilentlyContinue
    if(-not $p.WaitForExit(10000)){throw 'Owned VICE process did not release its monitor port'}
}
