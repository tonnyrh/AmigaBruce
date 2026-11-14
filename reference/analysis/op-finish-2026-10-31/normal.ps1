param([ValidateSet('cli','adf','render','cross','queued')][string]$Mode,[Parameter(Mandatory)][string]$Label,[ValidateRange(2,120)][int]$Samples=12,[string]$BuildDir)
$ErrorActionPreference='Stop'
if($BuildDir -and $Mode -notin ('cli','adf','cross')){throw 'BuildDir is supported by the normal CLI and disk probes'}
$root=(Resolve-Path "$PSScriptRoot/../../..").Path
$dir=Join-Path "$root/.tmp/op-finish" $Label
if(Test-Path -LiteralPath $dir){throw 'Choose a fresh run label'}
New-Item -ItemType Directory $dir | Out-Null
foreach($name in 'winuae64.exe','winuae.ini'){
    Copy-Item -LiteralPath "$root/.tmp/session-ui/$name" -Destination $dir
}
$config=@(Get-Content -LiteralPath "$root/.tmp/bruce-a500.uae")
if(!$BuildDir){$BuildDir=Join-Path $root 'amiga/out'}
$BuildDir=(Resolve-Path -LiteralPath $BuildDir).Path
$config=$config -replace '^filesystem2=rw,dh1:.+$',("filesystem2=rw,dh1:dh1:$BuildDir,-128")
if($Mode -eq 'queued'){$config=$config -replace '^filesystem2=rw,dh1:.+$',("filesystem2=rw,dh1:dh1:$root/.tmp/op-finish/queue-ui,-128")}
if($Mode -eq 'adf'){
    $config=@($config | Where-Object {$_ -notmatch '^(filesystem2|floppy0|floppy0wp)='})
    $config+="floppy0=$BuildDir/bruce_amiga.adf"
    $config+='floppy0wp=true'
}
$config | Set-Content -LiteralPath "$dir/game.uae" -Encoding ascii
$emu=Start-Process "$dir/winuae64.exe" -WorkingDirectory $dir -WindowStyle Hidden -PassThru -ArgumentList @('-ini',('"'+$dir+'/winuae.ini"'),'-f',('"'+$dir+'/game.uae"'))
try {
    Start-Sleep -Seconds 4
    if($Mode -in ('render','queued')){
        $common=@('--pid',"$($emu.Id)",'--log',"$dir/winuaebootlog.txt")
        & python "$root/tools/check_contact_unroll_boot.py" @common --label cli --output-root "$dir/boot"
        if($LASTEXITCODE){throw 'Normal menu was not complete'}
        $audit="$root/tools/audit_native_animation_frame.py"
        if($Mode -eq 'queued'){$audit="$root/.tmp/op-finish/queue-ui/audit.py";$common+=@('--elf',"$root/.tmp/op-finish/queue-ui/bruce_amiga.elf")}
        & python $audit @common --label "$Label-stairs" --start --samples $Samples --frozen --require-coherent
        $stairsResult=$LASTEXITCODE
        & python $audit @common --label "$Label-death" --death --roundtrip --samples 12 --frozen --require-coherent
        if($stairsResult){throw 'Room 12 frame comparison failed'}
    }else{& python "$PSScriptRoot/normal.py" $dir $emu.Id $Mode $BuildDir}
    if($LASTEXITCODE){throw "Normal $Mode test failed"}
}finally{if(!$emu.HasExited){Stop-Process -Id $emu.Id}}
