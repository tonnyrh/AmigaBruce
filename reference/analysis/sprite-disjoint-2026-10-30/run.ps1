param([ValidateSet('before','candidate')][string]$Variant,[ValidatePattern('^[a-z0-9-]+$')][string]$Suffix='r02')
$ErrorActionPreference='Stop'
Set-Location 'C:\vscode\_EXT\AmigaBruceLee'
$base='reference/analysis/sprite-disjoint-2026-10-30'
$inputs=@("$base/candidate/c64_rooms.c","$base/candidate/c64_actor_programs.h","$base/$Variant/sprite_copy.s","$base/$Variant-build.ps1",'.tmp/compact-delivery/math-main.c')
$frozen=@($inputs | ForEach-Object {@{path=$_;sha256=(Get-FileHash -LiteralPath $_).Hash.ToLower()}})
& ("./$base/$Variant-build.ps1") -Autotest -SourcePerfTest -SpriteCopyTest -PerfSourceSteps 360 -TestFrames 1800
if($LASTEXITCODE){throw 'Private sprite build failed'}
& ./test-source-performance.ps1 -Label ("sprite-disjoint-"+$Variant+"-"+$Suffix) -SpriteCopy -SourceSteps 360 -TestFrames 1800 -SkipBuild
if($LASTEXITCODE){throw 'Private sprite benchmark failed'}
$folder="reference/analysis/optimization-2026-10-27/sprite-disjoint-$Variant-$Suffix"
foreach($entry in $frozen){if((Get-FileHash -LiteralPath $entry.path).Hash.ToLower() -ne $entry.sha256){throw ('Input changed: '+$entry.path)}}
@{production_changed=$false;actual_inputs=$frozen;variant=$Variant;only_measured_difference='sprite_copy.s';native_test_difference='First64 of256 controls now use source glyph region and Y=3*height; other192 alias/tail cases retained'} | ConvertTo-Json -Depth 8 | Set-Content ($folder+'/compile-overrides.json') -Encoding utf8
