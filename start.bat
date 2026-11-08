@echo off
REM Start the full system on Windows
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -NoExit -File scripts/start_full_system.ps1
