@echo off

REM Cleanup script for Windows (cmd)

echo ═══════════════════════════════════════════
echo   Steam Guide Downloader — Cleanup
echo ═══════════════════════════════════════════

cd /d "%~dp0\.."

echo.
echo [1/5] Removing build/ ...
if exist "build" rd /s /q "build"

echo [2/5] Removing dist/ ...
if exist "dist" rd /s /q "dist"

echo [3/5] Removing __pycache__ ...
for /d /r %%d in (__pycache__) do (
    if exist "%%d" rd /s /q "%%d"
)

echo [4/5] Removing .pytest_cache ...
for /d /r %%d in (.pytest_cache) do (
    if exist "%%d" rd /s /q "%%d"
)

echo [5/5] Removing *.spec files ...
del /q "*.spec" 2>nul
del /q "build\*.spec" 2>nul

echo.
echo   Cleanup complete.
echo ═══════════════════════════════════════════
pause