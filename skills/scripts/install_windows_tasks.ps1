param(
    [Parameter(Mandatory = $true)]
    [string]$ScriptPath,
    [string]$MorningTime = "11:15",
    [string]$EveningTime = "17:20",
    [string]$TaskPrefix = "CafeteriaReminder"
)

$pythonw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $pythonw) {
    throw "pythonw.exe not found. Install Python first."
}

if (-not (Test-Path -LiteralPath $ScriptPath)) {
    throw "Script not found: $ScriptPath"
}

$morningName = "${TaskPrefix}_1115"
$eveningName = "${TaskPrefix}_1720"
$taskRun = '"' + $pythonw + '" "' + $ScriptPath + '"'

schtasks /Create /SC DAILY /ST $MorningTime /TN $morningName /TR $taskRun /F /IT | Out-Null
schtasks /Create /SC DAILY /ST $EveningTime /TN $eveningName /TR $taskRun /F /IT | Out-Null

Write-Output "Created tasks: $morningName ($MorningTime), $eveningName ($EveningTime)"
Write-Output "Command: $taskRun"
