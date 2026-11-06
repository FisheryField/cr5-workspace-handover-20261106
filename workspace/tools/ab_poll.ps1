$out = 'D:\mydata\workspace\data\ab_test\poll.csv'
$dir = Split-Path $out -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
't,controlMode,j1,j2,j3,j4,j5,j6,alarms' | Out-File -FilePath $out -Encoding ascii
$t0 = Get-Date
$i = 0
while ($true) {
  try {
    $r = Invoke-WebRequest -Uri 'http://192.168.5.1:22000/protocol/exchange' -Method GET -TimeoutSec 5 -UseBasicParsing
    $j = $r.Content | ConvertFrom-Json
    $jc = $j.jointCoordinate
    $al = ($j.alarms | ForEach-Object { $_.Count }) -join '/'
    $el = ((Get-Date) - $t0).TotalSeconds
    $line = ('{0:N3},{1},{2:N4},{3:N4},{4:N4},{5:N4},{6:N4},{7:N4},{8}' -f $el, $j.controlMode, $jc[0],$jc[1],$jc[2],$jc[3],$jc[4],$jc[5], $al)
    $line | Out-File -FilePath $out -Append -Encoding ascii
    $i++
    if ($i % 20 -eq 0) { Write-Output $line }
  } catch {
    $el = ((Get-Date) - $t0).TotalSeconds
    ('{0:N3},ERR,,,,,,,' -f $el) | Out-File -FilePath $out -Append -Encoding ascii
  }
  Start-Sleep -Milliseconds 500
}