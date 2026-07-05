param([switch]$Apply, [switch]$Check, [switch]$Revert)
Write-Host "Music Generation patch scaffold is present. Manual snippet application is still required in this first pass."
Write-Host "Use --check to verify source files exist; --apply/--revert will be implemented after snippet insertion is finalized."
if ($Check -or $Apply) {
  foreach ($p in @('agent/music_gen_provider.py','agent/music_gen_registry.py','tools/music_generation_tool.py')) {
    if (!(Test-Path -LiteralPath (Join-Path $PSScriptRoot $p))) { throw "Missing $p" }
  }
  Write-Host "Core patch source files found."
}
