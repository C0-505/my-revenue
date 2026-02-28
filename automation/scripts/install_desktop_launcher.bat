@echo off
cd /d %~dp0
powershell -ExecutionPolicy Bypass -File "%~dp0install_desktop_launcher.ps1"
