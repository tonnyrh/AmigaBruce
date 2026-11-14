param([int]$Port=6537,[string]$Mode='play')
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../..").Path
$meta=Get-Content "$root/reference/manifest.json" -Raw|ConvertFrom-Json
$exe=Join-Path $root $meta.emulator.executable_path
if((Get-FileHash -LiteralPath $exe).Hash -ne $meta.emulator.executable_sha256){throw 'VICE binary mismatch'}
$probe=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,$Port)
try{$probe.Start()}finally{$probe.Stop()}
$proc=Start-Process -FilePath $exe -ArgumentList "-default -model c64 +sound -warp -binarymonitor -binarymonitoraddress 127.0.0.1:$Port" -WindowStyle Hidden -PassThru
try{
    Start-Sleep 2
    & python -u "$PSScriptRoot/vice_trace.py" $Mode $Port
    if($LASTEXITCODE){throw 'C64 trace failed'}
}finally{if(!$proc.HasExited){Stop-Process -Id $proc.Id}}
