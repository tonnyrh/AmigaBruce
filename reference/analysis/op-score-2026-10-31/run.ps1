param([Parameter(Mandatory)][ValidatePattern('^[a-z0-9-]+$')][string]$Mode,
      [Parameter(Mandatory)][ValidatePattern('^[a-z0-9-]+$')][string]$Label,
      [ValidateRange(1,20)][int]$Room=1,[ValidateRange(0,3)][int]$Mask=3,[ValidateRange(0,2)][int]$Route=0,
      [ValidatePattern('^[a-z0-9-]+$')][string]$StageName='op-score',
      [ValidateRange(0,255)][int]$Probe=0)
$ErrorActionPreference='Stop'
if(($Room -eq 12 -and $Mask -ne 3) -or ($Room -eq 13 -and $Mask -ne 1)){throw 'Use the standard stair and Yamo routes'}
$root=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$stage=Join-Path (Join-Path $root '.tmp') $StageName
$isProof=($Mode -eq 'proof' -or $Mode -eq 'combat-proof')
$out=Join-Path $stage $Label
if(Test-Path -LiteralPath $out){throw "Run already exists: $Label"}
New-Item -ItemType Directory $out|Out-Null
Copy-Item -LiteralPath "$stage/$Mode/bruce_amiga.exe" -Destination $out
if($isProof){
    Copy-Item -LiteralPath "$stage/$Mode/cases.bin" -Destination $out
    $report=Join-Path $out 'proof.bin'
}else{
    [IO.File]::WriteAllBytes("$out/op0-route.bin",[byte[]]@(($Room-1),$Mask,$Route,$Probe,0,240,0,240))
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
            if($isProof){
                if((Get-Item $report).Length -eq 12){break}
            }elseif((Get-Content $report -Raw) -match 'finished=1'){break}
        }
        if($emu.HasExited){throw 'Owned emulator exited early'}
    }while((Get-Date) -lt $deadline)
    if($isProof){
        python -c "import struct,sys,pathlib;p=pathlib.Path(sys.argv[1]);n=struct.unpack('>I',(p/'cases.bin').open('rb').read(4))[0];v=struct.unpack('>III',(p/'proof.bin').read_bytes());print(v);assert v==(n,0,1)" $out
        if($LASTEXITCODE){throw 'Native witness failed'}
    }else{
        $values=@{}
        foreach($line in Get-Content -LiteralPath $report){$kv=$line.Split('=',2);if($kv.Count -eq 2){$values[$kv[0]]=$kv[1]}}
        foreach($k in @('source_fault','audio_fault','dma_fault')){if($values[$k] -ne '0'){throw "$k failed"}}
        $enough = if ($Mode -eq 'long' -or $Mode -like 'long-*') {
            [int]$values.pal_fields -ge 6000 -and [int]$values.steps -gt 0
        } else { $values.steps -eq '240' }
        if($values.finished -ne '1' -or $values.restored_os -ne '1' -or !$enough){throw 'Incomplete timing run'}
        Get-Content $report|Select-String 'pal_fields=|audio_missed=|active_loops=|kage_hit'
    }
}finally{if(!$emu.HasExited){Stop-Process -Id $emu.Id}}

