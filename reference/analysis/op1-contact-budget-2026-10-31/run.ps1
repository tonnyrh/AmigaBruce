param([Parameter(Mandatory)][ValidateSet('control','timed','sparse','capture','replay','keys')][string]$Mode,
      [Parameter(Mandatory)][ValidatePattern('^[a-z0-9-]+$')][string]$Label,[int]$Warmup=240,
      [string]$Fixture)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$work=Join-Path $root '.tmp/op1-budget';$out=Join-Path $work $Label
if(($Mode -eq 'replay') -ne [bool]$Fixture){throw 'Only replay mode requires a certified fixture'}
if(Test-Path -LiteralPath $out){throw "Run already exists: $Label"}
New-Item -ItemType Directory $out |Out-Null
$program=if($Mode -in @('replay','keys')){"$work/$Mode/bruce_amiga.exe"}else{"$work/bruce_amiga.exe"}
Copy-Item -LiteralPath $program -Destination $out
$modeID=@{control=0;timed=1;sparse=2;capture=3;replay=4;keys=5}[$Mode]
[IO.File]::WriteAllBytes("$out/op0-route.bin",[byte[]]@(0,3,0,$modeID,($Warmup -shr 8),($Warmup -band 255),0,240))
if($Fixture){Copy-Item -LiteralPath $Fixture -Destination "$out/replay.bin"}
(Get-Content "$root/.tmp/bruce-a500.uae") -replace '^filesystem2=rw,dh1:.+$',("filesystem2=rw,dh1:dh1:"+$out+",-128") |Set-Content -Encoding ascii "$out/a500.uae"
$rt="$root/.tmp/session-ui"
$emu=Start-Process -FilePath "$rt/winuae64.exe" -WorkingDirectory $rt -ArgumentList @('-ini',('"'+ "$rt/winuae.ini" +'"'),'-f',('"'+ "$out/a500.uae" +'"')) -WindowStyle Hidden -PassThru
try{
    $limit=(Get-Date).AddMinutes(6)
    do{
        Start-Sleep -Milliseconds 500
        if(Test-Path -LiteralPath "$out/op0-light.txt"){
            $report=Get-Content "$out/op0-light.txt" -Raw
            if($report -match 'finished=1'){break}
        }
        if($emu.HasExited){throw 'Owned emulator exited early'}
    }while((Get-Date)-lt $limit)
    if(!$report -or $report -notmatch 'finished=1'){throw "Incomplete $Label"}
    $values=@{}
    foreach($line in Get-Content "$out/op0-light.txt"){
        $pair=$line.Split('=',2);if($pair.Count -eq 2){$values[$pair[0]]=$pair[1]}
    }
    foreach($key in @('source_fault','audio_fault','dma_fault')){
        if($values[$key] -ne '0'){throw "$key failed in $Label"}
    }
    if($values.restored_os -ne '1'){throw "OS restore failed in $Label"}
    if($Mode -in @('control','timed','sparse','keys') -and $values.steps -ne '240'){throw 'Short timing route'}
    if($Mode -eq 'capture' -and ($values.capture_overflow -ne '0' -or [int]$values.capture_records -lt 5)){throw 'Bad capture'}
    if($Mode -eq 'replay' -and ($values.replay_benchmark.Split(',')[2] -ne '0' -or $values.replay_benchmark.Split(',')[6] -ne '64')){throw 'Replay mismatch'}
    Get-Content "$out/op0-light.txt" | Select-String 'pal_fields=|audio_missed=|contact_lines=|capture_records=|capture_overflow=|profiled_calls='
}finally{if(!$emu.HasExited){Stop-Process -Id $emu.Id}}

