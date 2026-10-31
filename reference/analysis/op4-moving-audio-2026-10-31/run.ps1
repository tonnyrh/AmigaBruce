param([Parameter(Mandatory)][ValidateSet('reference','sites','timed','capture','focused','candidate','proof')][string]$Mode,
      [Parameter(Mandatory)][ValidatePattern('^[a-z0-9-]+$')][string]$Label,
      [ValidateRange(1,20)][int]$Room=1,[ValidateRange(0,3)][int]$Mask=3,[ValidateRange(0,2)][int]$Route=0,[ValidateRange(1,2000)][int]$Warmup=240)
$ErrorActionPreference='Stop'
if(($Room -eq 12 -and $Mask -ne 3) -or ($Room -eq 13 -and $Mask -ne 1)){throw 'Use the standard stair and Yamo routes'}
$root=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$stage=Join-Path $root '.tmp/op4-moving'
$out=Join-Path $stage $Label
if(Test-Path -LiteralPath $out){throw "Run already exists: $Label"}
New-Item -ItemType Directory $out|Out-Null
Copy-Item -LiteralPath "$stage/$Mode/bruce_amiga.exe" -Destination $out
if($Mode -eq 'proof'){
    Copy-Item -LiteralPath "$stage/proof/cases.bin" -Destination $out
    $report=Join-Path $out 'proof.bin'
}else{
    [IO.File]::WriteAllBytes("$out/op0-route.bin",[byte[]]@(($Room-1),$Mask,$Route,0,($Warmup -shr 8),($Warmup -band 255),0,240))
    $report=Join-Path $out 'op0-light.txt'
}
(Get-Content "$root/.tmp/bruce-a500.uae") -replace '^filesystem2=rw,dh1:.+$',("filesystem2=rw,dh1:dh1:"+$out+",-128")|Set-Content -Encoding ascii "$out/a500.uae"
$rt="$root/.tmp/session-ui"
$emu=Start-Process -FilePath "$rt/winuae64.exe" -WorkingDirectory $rt -ArgumentList @('-ini',('"'+ "$rt/winuae.ini"+'"'),'-f',('"'+ "$out/a500.uae"+'"')) -WindowStyle Hidden -PassThru
try{
    $deadline=(Get-Date).AddMinutes(12)
    do{
        Start-Sleep -Milliseconds 500
        if(Test-Path -LiteralPath $report){
            if($Mode -eq 'proof'){
                if((Get-Item $report).Length -eq 12){break}
            }elseif((Get-Content $report -Raw) -match 'finished=1'){break}
        }
        if($emu.HasExited){throw 'Owned emulator exited early'}
    }while((Get-Date) -lt $deadline)
    if($Mode -eq 'proof'){
        python -c "import struct,sys,pathlib;p=pathlib.Path(sys.argv[1]);n=struct.unpack('>I',(p/'cases.bin').open('rb').read(4))[0];v=struct.unpack('>III',(p/'proof.bin').read_bytes());print(v);assert v==(n,0,1)" $out
        if($LASTEXITCODE){throw 'Native witness failed'}
    }else{
        $values=@{}
        foreach($line in Get-Content -LiteralPath $report){$kv=$line.Split('=',2);if($kv.Count -eq 2){$values[$kv[0]]=$kv[1]}}
        foreach($k in @('source_fault','audio_fault','dma_fault')){if($values[$k] -ne '0'){throw "$k failed"}}
        if($values.finished -ne '1' -or $values.restored_os -ne '1' -or ($Mode -ne 'capture' -and $values.steps -ne '240')){throw 'Incomplete timing run'}
        if($Mode -in @('sites','timed') -and !(Test-Path "$out/op4-audio.bin")){throw 'Missing or overflowing trace'}
        if($Mode -eq 'focused' -and !(Test-Path "$out/focus.bin")){throw 'Missing focused trace'}
        if($Mode -eq 'capture' -and ($values.capture_records -ne '2' -or $values.capture_overflow -ne '0')){throw 'Incomplete capture'}
        Get-Content $report|Select-String 'pal_fields=|audio_missed=|active_loops='
    }
}finally{if(!$emu.HasExited){Stop-Process -Id $emu.Id}}

