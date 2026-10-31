#Requires -Version 5.1
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$runtime=Join-Path $taskRoot '.tmp/session-ui'
$output=Join-Path $taskRoot 'reference/analysis/contact-unroll-2026-10-31'
foreach($disk in @($false,$true)){
    $config=& (Join-Path $taskRoot 'amiga-run.ps1') -ConfigOnly -Disk:$disk
    $process=Start-Process -FilePath (Join-Path $runtime 'winuae64.exe') -ArgumentList @('-ini',('"'+(Join-Path $runtime 'winuae.ini')+'"'),'-f',('"'+$config+'"')) -WorkingDirectory $runtime -WindowStyle Hidden -PassThru
    $owned=$process.Id
    $mode=if($disk){'adf'}else{'cli'}
    try{
        Start-Sleep -Seconds 3
        $args=@((Join-Path $taskRoot 'tools/check_contact_unroll_boot.py'),'--pid',"$owned",'--log',(Join-Path $runtime 'winuaebootlog.txt'),'--label',$mode)
        if($disk){$args+='--start-game'}
        & python @args
        if($LASTEXITCODE){throw "Normal $mode boot failed"}
        if(!$disk){
            & python (Join-Path $taskRoot 'tools/audit_native_animation_frame.py') --pid $owned --log (Join-Path $runtime 'winuaebootlog.txt') --label contact-unroll-r12 --start --samples 12 --frozen --require-coherent
            if($LASTEXITCODE){throw 'Room12 image audit failed'}
            & python (Join-Path $taskRoot 'tools/audit_native_animation_frame.py') --pid $owned --log (Join-Path $runtime 'winuaebootlog.txt') --label contact-unroll-r12-death --death --roundtrip --samples 12 --frozen --require-coherent
            if($LASTEXITCODE){throw 'Death/room transition image audit failed'}
        }
    }finally{
        if(Get-Process -Id $owned -ErrorAction SilentlyContinue){Stop-Process -Id $owned;Wait-Process -Id $owned -ErrorAction SilentlyContinue}
    }
}
& python (Join-Path $taskRoot 'tools/record_contact_unroll_boot.py')
if($LASTEXITCODE){throw 'Normal boot evidence failed'}
