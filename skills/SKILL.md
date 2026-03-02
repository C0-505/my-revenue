---
name: cafeteria-menu-reminder
description: Set up and maintain Windows cafeteria menu reminders with local popup notifications at fixed times and optional Feishu webhook push. Use when users want date-based cafeteria dish reminders, daily scheduled popups (for example 11:15 and 17:20), monthly menu updates via JSON, or reusable setup that can run on other computers.
---

# Cafeteria Menu Reminder

## Overview
Create a date-based cafeteria reminder system on Windows using a Python popup script and scheduled tasks. Keep monthly menu data in JSON so updates do not require code changes.

## Core Workflow
1. Prepare runtime files in a target folder on the user machine.
2. Configure `menu.json` with date-to-menu entries.
3. Install two daily scheduled tasks.
4. Run a test trigger to verify popup behavior.
5. Optionally enable Feishu webhook push.

## Files To Use
- `scripts/cafeteria_reminder.py`: reminder runtime script.
- `scripts/install_windows_tasks.ps1`: scheduled-task installer.
- `assets/menu.template.json`: starter JSON for monthly menu maintenance.

## Setup Steps
1. Copy `scripts/cafeteria_reminder.py` and `assets/menu.template.json` to a target folder (for example `C:\Users\<user>\Desktop\cafeteria-reminder`).
2. Rename `menu.template.json` to `menu.json`.
3. Edit `menu.json`:
- Add each reminder date under `dates` as `YYYY-MM-DD`.
- Fill `lunch` and `dinner` for each date.
- Optional Feishu: set `feishu.enabled` to `true` and fill `feishu.webhook_url`.
4. Install tasks with default times:
```powershell
powershell -ExecutionPolicy Bypass -File "<skill_dir>\scripts\install_windows_tasks.ps1" -ScriptPath "<target_dir>\cafeteria_reminder.py"
```
5. Install tasks with custom times:
```powershell
powershell -ExecutionPolicy Bypass -File "<skill_dir>\scripts\install_windows_tasks.ps1" -ScriptPath "<target_dir>\cafeteria_reminder.py" -MorningTime "11:15" -EveningTime "17:20"
```

## Validation
1. Trigger one task manually:
```powershell
schtasks /Run /TN "CafeteriaReminder_1115"
```
2. Query status:
```powershell
schtasks /Query /TN "CafeteriaReminder_1115" /V /FO LIST
```
3. Test a specific date without waiting for schedule:
```powershell
$env:CAFETERIA_TEST_DATE='2026-03-02'
python "<target_dir>\cafeteria_reminder.py"
Remove-Item Env:\CAFETERIA_TEST_DATE
```

## Monthly Update Rule
1. Update only `menu.json` each month.
2. Keep script and task definitions unchanged unless reminder times or task names change.

## Feishu Notes
- Use group custom bot webhook URL.
- Keep local popup enabled as the fallback channel.
- If webhook push fails, script still shows local popup.
