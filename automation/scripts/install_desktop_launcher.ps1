param(
  [string]$ProjectPath = (Resolve-Path "$PSScriptRoot\..\..").Path
)

$desktop = [Environment]::GetFolderPath("Desktop")
if (-not (Test-Path $desktop)) {
  Write-Error "Desktop path not found: $desktop"
  exit 1
}

$dryRunLauncher = @"
@echo off
cd /d "$ProjectPath"
call automation\scripts\run_dry_run.bat
pause
"@

$realLauncher = @"
@echo off
cd /d "$ProjectPath"
if "%SEMPLUS_PASSWORD%"=="" (
  echo [提示] 先在 PowerShell 设置密码变量：
  echo $env:SEMPLUS_PASSWORD = "你的真实密码"
  pause
  exit /b 1
)
call automation\scripts\run_real_headless.bat
pause
"@

$dryRunPath = Join-Path $desktop "数据自动下载-演练.bat"
$realPath = Join-Path $desktop "数据自动下载-正式.bat"

Set-Content -Path $dryRunPath -Value $dryRunLauncher -Encoding ASCII
Set-Content -Path $realPath -Value $realLauncher -Encoding ASCII

Write-Host "已创建桌面启动程序："
Write-Host "- $dryRunPath"
Write-Host "- $realPath"
