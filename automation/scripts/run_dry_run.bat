@echo off
cd /d %~dp0\..\..
if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m automation.main --config automation/config/sites.test.json --dry-run
