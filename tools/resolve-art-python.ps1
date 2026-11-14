#Requires -Version 5.1
param([string]$PythonExecutable, [switch]$Editor)
$ErrorActionPreference = 'Stop'

# A desktop-launched PowerShell can see only Windows app aliases on PATH.
# Prefer a working installation, including the interpreter explicitly supplied
# by a running editor. Invoke the same console executable at every build step.
$probe = 'import sys; from PIL import Image; sys.exit(sys.version_info < (3, 10))'
if ($Editor) {
    $probe = 'import sys, tkinter; from PIL import Image, ImageTk; sys.exit(sys.version_info < (3, 10))'
}
$candidates = if ($PythonExecutable) {
    $PythonExecutable
} else {
    $onPath = @(Get-Command python.exe -All -CommandType Application -ErrorAction SilentlyContinue)
    $onPath | Where-Object Source -NotMatch '\\WindowsApps\\' | ForEach-Object Source
    foreach ($root in 'HKCU:\Software\Python\PythonCore', 'HKLM:\Software\Python\PythonCore') {
        Get-ChildItem $root -ErrorAction SilentlyContinue | ForEach-Object {
            (Get-ItemProperty -LiteralPath (Join-Path $_.PSPath 'InstallPath') -ErrorAction SilentlyContinue).ExecutablePath
        }
    }
    $onPath | Where-Object Source -Match '\\WindowsApps\\' | ForEach-Object Source
}
foreach ($candidate in $candidates | Where-Object { $_ } | Select-Object -Unique) {
    try {
        & $candidate -c $probe 2>$null
        if ($LASTEXITCODE -eq 0) { return $candidate }
    } catch {
        Write-Verbose "Cannot start Python at $candidate"
    }
}
$required = if ($Editor) { 'Python 3.10+, Pillow and Tkinter' } else { 'Python 3.10+ and Pillow' }
if ($PythonExecutable) { throw "Cannot run $required using '$PythonExecutable'." }
throw "Cannot find a working installation of $required."
