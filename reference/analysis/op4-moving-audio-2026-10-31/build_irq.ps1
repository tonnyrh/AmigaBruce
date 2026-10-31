# Build fresh host copies of the two existing IRQ bridges in the private work area.
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
Push-Location $root
try{
 $vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
 $vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
 $vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
 foreach($mode in @('audit','context')){
  $names=if($mode -eq 'audit'){@('seed','field','copy','regs')}else{@('seed','run','copy','regs','pc','fault','gates')}
  $exports=($names|ForEach-Object{"/EXPORT:bl_irq_${mode}_$_"}) -join ' '
  $cmd='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /w /Fe:.tmp/op4-moving/'+$mode+'.dll /Fo.tmp/op4-moving/'+$mode+'.obj tests/source_irq_'+$mode+'_bridge.c /link '+$exports
  & $env:ComSpec /d /s /c $cmd;if($LASTEXITCODE){throw "Failed to build $mode"}
 }
}finally{Pop-Location}
