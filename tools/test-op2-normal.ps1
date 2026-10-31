#Requires -Version 5.1
[CmdletBinding()]
param([switch]$DiskOnly)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$runtime=Join-Path $taskRoot '.tmp/session-ui'
$output=Join-Path $taskRoot 'reference/analysis/op2-field-2026-10-31'
foreach($disk in @($false,$true)){
    if($DiskOnly -and !$disk){continue}
    if($disk){
        # Reuse the CLI's A500 settings. Boot this check solely from the
        # delivered floppy, independently of any open AmigaDOS shell.
        $config=Join-Path $output 'standalone-adf.uae'
        $settings=@(Get-Content (Join-Path $taskRoot '.tmp/bruce-a500.uae') | Where-Object {$_ -notmatch '^(filesystem2|floppy0|floppy0wp)='})
        $settings+='floppy0='+(Join-Path $taskRoot 'amiga/out/bruce_amiga.adf')
        $settings+='floppy0wp=true'
        $settings | Set-Content -LiteralPath $config -Encoding ascii
    }else{
        $config=& (Join-Path $taskRoot 'amiga-run.ps1') -ConfigOnly
    }
    $process=Start-Process -FilePath (Join-Path $runtime 'winuae64.exe') -ArgumentList @('-ini',('"'+(Join-Path $runtime 'winuae.ini')+'"'),'-f',('"'+$config+'"')) -WorkingDirectory $runtime -WindowStyle Hidden -PassThru
    $owned=$process.Id
    $mode=if($disk){'adf'}else{'cli'}
    try{
        Start-Sleep -Seconds 3
        $args=@((Join-Path $taskRoot 'tools/check_contact_unroll_boot.py'),'--pid',"$owned",'--log',(Join-Path $runtime 'winuaebootlog.txt'),'--label',$mode,'--output-root',(Join-Path $output 'normal-ui'))
        if($disk){$args+='--start-game'}
        & python @args
        if($LASTEXITCODE){throw "Normal $mode boot failed"}
        if(!$disk){
            & python (Join-Path $taskRoot 'tools/audit_native_animation_frame.py') --pid $owned --log (Join-Path $runtime 'winuaebootlog.txt') --label op2-wide-r12 --start --samples 12 --frozen --require-coherent
            if($LASTEXITCODE){throw 'Room12 image audit failed'}
            & python (Join-Path $taskRoot 'tools/audit_native_animation_frame.py') --pid $owned --log (Join-Path $runtime 'winuaebootlog.txt') --label op2-wide-r12-death --death --roundtrip --samples 12 --frozen --require-coherent
            if($LASTEXITCODE){throw 'Death/room transition image audit failed'}
        }
    }finally{
        if(Get-Process -Id $owned -ErrorAction SilentlyContinue){Stop-Process -Id $owned;Wait-Process -Id $owned -ErrorAction SilentlyContinue}
    }
}

