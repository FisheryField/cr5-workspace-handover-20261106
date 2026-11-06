$base='http://192.168.5.1:22000'
for ($i=1; $i -le 3; $i++) {
  try {
    $r = Invoke-WebRequest -Uri ($base+'/protocol/exchange') -Method GET -TimeoutSec 15 -UseBasicParsing
    $j = $r.Content | ConvertFrom-Json
    $jc = $j.jointCoordinate
    Write-Output ('[' + $i + '] controlMode=' + $j.controlMode + '  powerState=' + $j.powerState)
    Write-Output ('     J1..J6 = ' + ($jc | ForEach-Object { '{0,8:N4}' -f $_ }) -join ' ')
    Write-Output ('     alarms = ' + (($j.alarms | ForEach-Object { $_.Count }) -join '/'))
  } catch { Write-Output ('[' + $i + '] ERR ' + $_.Exception.Message) }
  Start-Sleep -Milliseconds 1200
}