$ErrorActionPreference='Stop'
Set-Location 'C:\vscode\_EXT\AmigaBruceLee'
& ./amiga-build.ps1
if($LASTEXITCODE){throw 'Audio boundary normal build failed'}
& ./amiga-run.ps1 -ConfigOnly
if($LASTEXITCODE){throw 'CLI command refresh failed'}
& ./test-source-world.ps1 -SkipHost -EmulatorPath 'C:\vscode\_EXT\AmigaBruceLee\.tmp\session-ui\winuae64.exe' -EmulatorIni 'C:\vscode\_EXT\AmigaBruceLee\.tmp\session-ui\winuae.ini'
if($LASTEXITCODE){throw 'Current53-fixture native validation failed'}
& ./reference/analysis/audio-service-2026-10-30/boundary-build.ps1 -Autotest -SourcePerfTest -SpriteCopyTest -PerfSourceSteps 360 -TestFrames 1800
if($LASTEXITCODE){throw 'Current710-control build failed'}
& ./test-source-performance.ps1 -Label audio-boundary-delivered-r01 -SpriteCopy -SourceSteps 360 -TestFrames 1800 -SkipBuild
if($LASTEXITCODE){throw 'Current710-control validation failed'}
& python tools/verify_compact_kernel_linkage.py
if($LASTEXITCODE){throw 'Current primitive linkage failed'}
& ./reference/analysis/audio-service-2026-10-30/ui-run.ps1
if($LASTEXITCODE){throw 'Current normal UI/boot validation failed'}
