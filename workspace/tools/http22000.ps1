$base = 'http://192.168.5.1:22000'
function Hit($m, $p, $body) {
  try {
    if ($m -eq 'GET') { $r = Invoke-WebRequest -Uri ($base+$p) -Method GET -TimeoutSec 10 -UseBasicParsing }
    else { $r = Invoke-WebRequest -Uri ($base+$p) -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 10 -UseBasicParsing }
    Write-Output ('--- ' + $m + ' ' + $p + ' ---')
    Write-Output ('   HTTP ' + $r.StatusCode + '  ' + $r.Content)
  } catch {
    Write-Output ('--- ' + $m + ' ' + $p + ' ---')
    Write-Output ('   ERROR ' + $_.Exception.Message)
  }
}
Hit GET  '/connection/state' $null
Hit GET  '/properties/controllerType' $null
Hit POST '/settings/version' '{}'
Hit POST '/interface/readCurrentEncoder' '{}'
Hit POST '/interface/readSensorEncoder' '{}'