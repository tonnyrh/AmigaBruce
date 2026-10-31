#Requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$OutputDirectory,[switch]$Autotest,[switch]$Disk,[switch]$ConfigOnly,[switch]$TwoJoysticks,[ValidateRange(1,2)][int]$TestRuns=2,[string]$Kickstart,[string]$EmulatorPath,[string]$EmulatorIni)
$ErrorActionPreference='Stop'
$taskRoot='C:\vscode\_EXT\AmigaBruceLee'
$privateOut=(Resolve-Path -LiteralPath $OutputDirectory).Path
$allowedPrivate=(Join-Path $taskRoot 'reference/analysis/op1-row-walk-2026-10-31')+[IO.Path]::DirectorySeparatorChar
if(!$privateOut.StartsWith($allowedPrivate,[StringComparison]::OrdinalIgnoreCase)){throw 'Only v5 private outputs are allowed'}
$extension=Get-ChildItem -Directory (Join-Path $env:USERPROFILE '.vscode/extensions') -Filter 'bartmanabyss.amiga-debug-*' |
    Sort-Object Name -Descending | Select-Object -First 1
if(-not $extension){throw 'BartmanAbyss toolchain not found'}
if(-not $Kickstart){$Kickstart=Join-Path (Split-Path $taskRoot -Parent) 'harrierattackreloaded/.tools/Amiga/Kick/Kickstart1.3.rom'}
if(-not(Test-Path -LiteralPath $Kickstart)){throw 'Supply -Kickstart with your local Kickstart 1.3 ROM path'}
$privateRuntimeId=[BitConverter]::ToString(([Security.Cryptography.SHA256]::Create()).ComputeHash([Text.Encoding]::UTF8.GetBytes($privateOut))).Replace('-','').Substring(0,8)
$boot=Join-Path $taskRoot $(if($Autotest){'.tmp/op1-row-fixture-boot-test-'+$privateRuntimeId}else{'.tmp/op1-row-fixture-boot'})
New-Item -ItemType Directory -Force $boot,(Join-Path $boot 's') | Out-Null
# Copy the toolchain boot commands locally; never edit its shared startup file.
Copy-Item -LiteralPath (Join-Path $extension.FullName 'bin/dh0/c') -Destination $boot -Recurse -Force
$program=if($Autotest){'bruce_test.exe'}else{'bruce_amiga.exe'}
if(-not(Test-Path (Join-Path $privateOut $program))){throw 'Build the selected executable first'}
if(!$Autotest){
    # A real command works in Kickstart 1.3 CLI without Execute or an alias.
    # Refresh it from the current build on every interactive launch.
    Copy-Item -LiteralPath (Join-Path $privateOut $program) -Destination (Join-Path $boot 'c/start') -Force
}
# Full20-room ADF inspection ran with the DOS default stack. Reserve16KiB
# for CLI runs without consuming another64KiB of scarce Chip RAM.
$startup=@('Stack 16384','cd dh1:',$program)
if($Autotest){
    if(!$ConfigOnly){
        foreach($name in @('autotest-1.txt','autotest-2.txt')){
            $old=Join-Path $privateOut $name
            if(Test-Path -LiteralPath $old){Remove-Item -LiteralPath $old}
        }
    }
    if($TestRuns -eq 2){$startup+=$program}
}
[IO.File]::WriteAllText((Join-Path $boot 's/startup-sequence'),($startup -join "`n")+"`n",[Text.Encoding]::ASCII)
$config=Join-Path $taskRoot $(if($Autotest){'.tmp/op1-row-fixture-a500-test.uae'}else{'.tmp/op1-row-fixture-a500.uae'})
$configLines=@(
    'use_gui=no','win32.start_not_captured=yes','win32.nonotificationicon=yes',
    'boot_rom_uae=min','quickstart=a500,1',"kickstart_rom_file=$Kickstart",
    'cpu_model=68000','cpu_speed=real','cpu_cycle_exact=true','cpu_memory_cycle_exact=true',
    'blitter_cycle_exact=true','cycle_exact=true','ntsc=false','synchronize_clock=no',
    'chipset=ocs','chipmem_size=1','bogomem_size=2','fastmem_size=0',
    # Mix the mono SID reference onto both outputs. Keep a stereo device:
    # some WASAPI drivers reject a one-channel device and fall back to8ch.
    'sound_output=exact','sound_channels=stereo','sound_stereo_separation=0',
    'sound_stereo_mixing_delay=0','sound_frequency=48000',
    'joyport0=mouse','joyport1=kbd1',
    'gfx_filter_autoscale=auto','gfx_width_windowed=960','gfx_height_windowed=768',
    "filesystem2=rw,dh1:dh1:$privateOut,-128"
)
if($TwoJoysticks){$configLines=$configLines -replace '^joyport0=mouse$','joyport0=kbd2'}
if($Disk){
    $diskImage=Join-Path $privateOut ([IO.Path]::ChangeExtension($program,'adf'))
    if(-not(Test-Path -LiteralPath $diskImage)){throw 'Build ADF first'}
    $configLines+="floppy0=$diskImage"
    $configLines+='floppy0wp=true'
}else{$configLines+="filesystem2=rw,dh0:dh0:$boot,0"}
$configLines | Set-Content -LiteralPath $config -Encoding ASCII
if($ConfigOnly){Write-Output $config;return}
$arguments=@('-f',('"'+$config+'"'))
if(!$EmulatorPath){$EmulatorPath=Join-Path $extension.FullName 'bin/win32/winuae-gdb.exe'}
if(!(Test-Path -LiteralPath $EmulatorPath)){throw 'EmulatorPath does not exist'}
if($EmulatorIni){
    if(!(Test-Path -LiteralPath $EmulatorIni)){throw 'EmulatorIni does not exist'}
    $arguments=@('-ini',('"'+$EmulatorIni+'"'))+$arguments
}
$launch=@{FilePath=$EmulatorPath;ArgumentList=$arguments;PassThru=$true}
if($EmulatorIni){$launch.WorkingDirectory=Split-Path $EmulatorIni -Parent}
if($Autotest){$launch.WindowStyle='Hidden'}
$emulator=Start-Process @launch
$emulator.Id | Set-Content (Join-Path $taskRoot $(if($Autotest){'.tmp/op1-row-fixture-test.pid'}else{'.tmp/op1-row-fixture.pid'}))
Write-Output "WinUAE PID $($emulator.Id); PAL OCS 68000, 512 KiB Chip + 512 KiB slow"


