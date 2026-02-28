@echo off
cd /d %~dp0\..\..
if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate.bat
if "%SEMPLUS_PASSWORD%"=="" (
  echo [ERROR] Please set SEMPLUS_PASSWORD first.
  exit /b 1
)
python -m automation.main --config automation/config/sites.example.yaml --headful
