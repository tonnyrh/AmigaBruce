#Requires -Version 5.1
[CmdletBinding()]
param([switch]$Check)
$ErrorActionPreference='Stop'
$python = & (Join-Path $PSScriptRoot 'tools/resolve-art-python.ps1') -Editor
$arguments=@((Join-Path $PSScriptRoot 'tools/bruce_graphics_editor.py'))
if($Check){$arguments+='--check'}
& $python @arguments
exit $LASTEXITCODE
