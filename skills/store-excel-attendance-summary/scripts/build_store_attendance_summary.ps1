param(
  [Parameter(Mandatory = $true)]
  [string]$InputPath,

  [string]$OutputPath,

  [int]$ExpectedDays = 27,

  [string]$DateHeader = '日期',

  [string]$StoreHeader = '门店',

  [string]$SheetName
)

$ErrorActionPreference = 'Stop'

function Convert-ToDate {
  param([object]$Value)

  if ($null -eq $Value) { return $null }

  if ($Value -is [double] -or $Value -is [int] -or $Value -is [decimal]) {
    return [datetime]::FromOADate([double]$Value).Date
  }

  $text = [string]$Value
  if ([string]::IsNullOrWhiteSpace($text)) { return $null }

  try {
    return [datetime]::Parse($text).Date
  } catch {
    return $null
  }
}

if (-not (Test-Path -LiteralPath $InputPath)) {
  throw "Input file not found: $InputPath"
}

if (-not $OutputPath) {
  $dir = Split-Path -Parent $InputPath
  $OutputPath = Join-Path $dir 'store-attendance-summary.xlsx'
}

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

$wb = $null
$ws = $null
$newWb = $null
$newWs = $null

try {
  $wb = $excel.Workbooks.Open($InputPath)
  if ($SheetName) {
    $ws = $wb.Worksheets.Item($SheetName)
  } else {
    $ws = $wb.Worksheets.Item(1)
  }

  $used = $ws.UsedRange
  $rows = $used.Rows.Count
  $cols = $used.Columns.Count

  $dateCol = $null
  $storeCol = $null

  for ($c = 1; $c -le $cols; $c++) {
    $header = [string]$ws.Cells.Item(1, $c).Text
    if ($header -eq $DateHeader) { $dateCol = $c }
    if ($header -eq $StoreHeader) { $storeCol = $c }
  }

  if (-not $dateCol -or -not $storeCol) {
    throw "Header not found. DateHeader='$DateHeader' StoreHeader='$StoreHeader'"
  }

  $storeDates = @{}
  $allDates = New-Object 'System.Collections.Generic.HashSet[string]'

  for ($r = 2; $r -le $rows; $r++) {
    $dateValue = $ws.Cells.Item($r, $dateCol).Value2
    $store = [string]$ws.Cells.Item($r, $storeCol).Text

    if ([string]::IsNullOrWhiteSpace($store)) { continue }

    $dt = Convert-ToDate -Value $dateValue
    if ($null -eq $dt) { continue }

    $dateString = $dt.ToString('yyyy-MM-dd')
    $allDates.Add($dateString) | Out-Null

    if (-not $storeDates.ContainsKey($store)) {
      $storeDates[$store] = New-Object 'System.Collections.Generic.HashSet[string]'
    }

    $storeDates[$store].Add($dateString) | Out-Null
  }

  if ($allDates.Count -eq 0) {
    throw 'No valid dates found in worksheet.'
  }

  $minDate = ($allDates | ForEach-Object { [datetime]::Parse($_) } | Measure-Object -Minimum).Minimum

  $targetDates = New-Object 'System.Collections.Generic.List[string]'
  for ($i = 0; $i -lt $ExpectedDays; $i++) {
    $targetDates.Add($minDate.AddDays($i).ToString('yyyy-MM-dd'))
  }

  $rowsOut = @()
  foreach ($store in $storeDates.Keys) {
    $set = $storeDates[$store]
    $missing = New-Object System.Collections.Generic.List[string]

    foreach ($d in $targetDates) {
      if (-not $set.Contains($d)) {
        $missing.Add($d)
      }
    }

    $diff = $missing.Count
    $actual = $ExpectedDays - $diff

    $rowsOut += [pscustomobject]@{
      门店 = $store
      实际营业天数 = "$actual"
      差异天数 = "$diff"
      具体日期 = ($missing -join ', ')
    }
  }

  $rowsOut = $rowsOut | Sort-Object -Property @{Expression = '差异天数'; Descending = $true}, '门店'

  $newWb = $excel.Workbooks.Add()
  $newWs = $newWb.Worksheets.Item(1)
  $newWs.Name = '汇总'

  $newWs.Cells.Item(1, 1).Value2 = '门店'
  $newWs.Cells.Item(1, 2).Value2 = '实际营业天数'
  $newWs.Cells.Item(1, 3).Value2 = '差异天数'
  $newWs.Cells.Item(1, 4).Value2 = '具体日期'

  $rowIndex = 2
  foreach ($item in $rowsOut) {
    $newWs.Cells.Item($rowIndex, 1).Value2 = [string]$item.门店
    $newWs.Cells.Item($rowIndex, 2).Value2 = [string]$item.实际营业天数
    $newWs.Cells.Item($rowIndex, 3).Value2 = [string]$item.差异天数
    $newWs.Cells.Item($rowIndex, 4).Value2 = [string]$item.具体日期
    $rowIndex++
  }

  $headerRange = $newWs.Range('A1:D1')
  $headerRange.Font.Bold = $true
  $newWs.Columns.Item('A:D').AutoFit() | Out-Null

  if (Test-Path -LiteralPath $OutputPath) {
    Remove-Item -LiteralPath $OutputPath -Force
  }

  $newWb.SaveAs($OutputPath)

  $missingStores = ($rowsOut | Where-Object { [int]$_.差异天数 -gt 0 }).Count

  Write-Output "created=$OutputPath"
  Write-Output "stores=$($rowsOut.Count)"
  Write-Output "stores_with_diff=$missingStores"
}
finally {
  if ($newWb) { $newWb.Close($true) }
  if ($wb) { $wb.Close($false) }
  $excel.Quit()

  if ($headerRange) { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($headerRange) }
  if ($newWs) { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($newWs) }
  if ($newWb) { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($newWb) }
  if ($ws) { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($ws) }
  if ($wb) { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($wb) }
  [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
  [GC]::Collect()
  [GC]::WaitForPendingFinalizers()
}

