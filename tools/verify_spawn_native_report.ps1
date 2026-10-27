#Requires -Version 5.1
# Reuse every existing native guard for a complete report captured from a
# batch whose second launch was interrupted. No emulator or game mutation.
$ErrorActionPreference='Stop'
$spawnNativeRoot=Split-Path $PSScriptRoot -Parent
$firstPath=Join-Path $spawnNativeRoot 'reference/analysis/spawn-audit-2026-10-26/native-first-run.json'
$first=Get-Content -LiteralPath $firstPath -Raw | ConvertFrom-Json
foreach($source in $first.source_files){
    if((Get-FileHash (Join-Path $spawnNativeRoot $source.path)).Hash.ToLower() -ne $source.sha256){throw "First native source changed: $($source.path)"}
}
foreach($kind in @('exe','adf')){
    $expected=if($kind -eq 'exe'){$first.executable_sha256}else{$first.adf_sha256}
    if((Get-FileHash (Join-Path $spawnNativeRoot "amiga/out/bruce_test.$kind")).Hash.ToLower() -ne $expected){throw 'Native binary changed'}
}
$script=Get-Content (Join-Path $spawnNativeRoot 'test-amiga.ps1') -Raw
$ast=[System.Management.Automation.Language.Parser]::ParseInput($script,[ref]$null,[ref]$null)
foreach($name in @('fighterExpected','spriteExpected','netExpected','climbExpected','introExpected')){
    $assignment=$ast.Find({param($n) $n -is [System.Management.Automation.Language.AssignmentStatementAst] -and $n.Left.Extent.Text -eq ('$'+$name)},$true)
    if(!$assignment){throw "Missing existing guard input: $name"}
    Set-Variable -Name $name -Value (Invoke-Expression ($assignment.Right.Extent.Text.Replace('$PSScriptRoot','$spawnNativeRoot')))
}
$CombatTest=$true;$CollectFrameDrops=$true;$TestFrames=6000
$Disk=$SourceRooms=$RoomTour=$RoomsTest=$EnemyEdgeTest=$GateTest=$RoomLoadTest=$RoomLoadBaseline=$false
$result=@{};foreach($property in $first.run.PSObject.Properties){$result[$property.Name]=[string]$property.Value}
$loop=$ast.Find({param($n) $n -is [System.Management.Automation.Language.ForEachStatementAst] -and $n.Variable.Extent.Text -eq '$result'},$true)
if(!$loop){throw 'Native guard body missing'}
$body=$loop.Body.Extent.Text
& ([scriptblock]::Create($body.Substring(1,$body.Length-2).Replace('$PSScriptRoot','$spawnNativeRoot')))
if([int]$result.chip_largest_loaded -lt 49152){throw 'Native Chip reserve failed'}
$proof=@{status='passed_all_existing_test_amiga_per_run_guards';frames=6000;source_and_binary_identity_verified=$true;
    report_sha256=(Get-FileHash $firstPath).Hash.ToLower();validator_sha256=(Get-FileHash $PSCommandPath).Hash.ToLower();
    guard_sha256=(Get-FileHash (Join-Path $spawnNativeRoot 'test-amiga.ps1')).Hash.ToLower()}
$proof | ConvertTo-Json | Set-Content (Join-Path $spawnNativeRoot 'reference/analysis/spawn-audit-2026-10-26/native-first-validation.json') -Encoding UTF8
Write-Output 'PASS captured first6000-field native run through every existing test-amiga per-run guard; source/binary identity unchanged'
