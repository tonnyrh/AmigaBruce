param([string]$EvidenceDirectory=$PSScriptRoot,[ValidatePattern('^[a-z0-9-]+$')][string]$StageName='op-score')
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../..").Path
$runtime=Join-Path $root '.tmp/session-ui'
$cli=& "$root/amiga-run.ps1" -ConfigOnly
foreach($mode in @('cli','adf')){
    $config=$cli
    if($mode -eq 'adf'){
        $config="$root/.tmp/$StageName/standalone-adf.uae"
        $settings=@(Get-Content $cli | Where-Object {$_ -notmatch '^(filesystem2|floppy0|floppy0wp)='})
        $settings+="floppy0=$root/amiga/out/bruce_amiga.adf"
        $settings+='floppy0wp=true'
        $settings | Set-Content -LiteralPath $config -Encoding ascii
    }
    $emu=Start-Process "$runtime/winuae64.exe" -WorkingDirectory $runtime -WindowStyle Hidden -PassThru -ArgumentList @('-ini',('"'+$runtime+'/winuae.ini"'),'-f',('"'+$config+'"'))
    try{
        Start-Sleep -Seconds 3
        $arguments=@("$root/tools/check_contact_unroll_boot.py",'--pid',"$($emu.Id)",'--log',"$runtime/winuaebootlog.txt",'--label',$mode,'--output-root',"$EvidenceDirectory/boot")
        if($mode -eq 'adf'){$arguments+='--start-game'}
        & python @arguments
        if($LASTEXITCODE){throw "Normal $mode boot failed"}
    }finally{
        if(!$emu.HasExited){Stop-Process -Id $emu.Id}
    }
}
