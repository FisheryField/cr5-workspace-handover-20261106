$base='http://192.168.5.1:22000'
function Hit($m,$p,$body){
  try {
    if ($m -eq 'GET') { $r = Invoke-WebRequest -Uri ($base+$p) -Method GET -TimeoutSec 15 -UseBasicParsing }
    else { $r = Invoke-WebRequest -Uri ($base+$p) -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 15 -UseBasicParsing }
    Write-Output ('--- ' + $m + ' ' + $p + '  => HTTP ' + $r.StatusCode)
    Write-Output ('    ' + $r.Content.Substring(0, [Math]::Min(1500, $r.Content.Length)))
  } catch {
    $resp = $_.Exception.Response
    $code = -2
    if ($resp) { $code = [int]$resp.StatusCode }
    Write-Output ('--- ' + $m + ' ' + $p + '  => ERR ' + $code + '  ' + $_.Exception.Message)
    if ($resp) { try { $sr = New-Object System.IO.StreamReader($resp.GetResponseStream()); $b=$sr.ReadToEnd(); Write-Output ('    body: ' + $b.Substring(0,[Math]::Min(800,$b.Length))) } catch {} }
  }
}
Hit GET  '/settings/readServoParams' $null
Hit POST '/settings/readServoParams' '{}'
Hit GET  '/config/servoReadOnlyAddress' $null
Hit GET  '/servoParams' $null