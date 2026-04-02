# Cleanup script for Windows (PowerShell)

$ErrorActionPreference = "SilentlyContinue"
$root = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Steam Guide Downloader — Cleanup" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$dirs = @("build", "dist")
foreach ($d in $dirs) {
    $p = Join-Path $root $d
    if (Test-Path $p) {
        Remove-Item -Recurse -Force $p
        Write-Host "  Removed: $d/" -ForegroundColor Yellow
    }
}

# __pycache__
Get-ChildItem -Path $root -Recurse -Directory -Filter "__pycache__" |
    ForEach-Object {
        Remove-Item -Recurse -Force $_.FullName
        Write-Host "  Removed: $($_.FullName -replace [regex]::Escape($root), '.')" -ForegroundColor DarkGray
    }

# .pytest_cache
Get-ChildItem -Path $root -Recurse -Directory -Filter ".pytest_cache" |
    ForEach-Object {
        Remove-Item -Recurse -Force $_.FullName
        Write-Host "  Removed: $($_.FullName -replace [regex]::Escape($root), '.')" -ForegroundColor DarkGray
    }

# .spec files
Get-ChildItem -Path $root -Filter "*.spec" -File |
    ForEach-Object {
        Remove-Item -Force $_.FullName
        Write-Host "  Removed: $($_.Name)" -ForegroundColor DarkGray
    }

# Generated checkbox PNGs
Get-ChildItem -Path (Join-Path $root "assets") -Filter "chk_*.png" -File -ErrorAction SilentlyContinue |
    ForEach-Object {
        Remove-Item -Force $_.FullName
        Write-Host "  Removed: assets/$($_.Name)" -ForegroundColor DarkGray
    }

Write-Host ""
Write-Host "  Cleanup complete." -ForegroundColor Green
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""