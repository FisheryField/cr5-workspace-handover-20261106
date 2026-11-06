$base='http://192.168.5.1:22000'
function Hit($p,$body,$label){
  try {
    $r = Invoke-WebRequest -Uri ($base+$p) -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 20 -UseBasicParsing
    Write-Output ('--- ' + $label + '  => HTTP ' + $r.StatusCode)
    Write-Output ('    ' + $r.Content.Substring(0, [Math]::Min(1000, $r.Content.Length)))
  } catch {
    $resp = $_.Exception.Response; $code = -2
    if ($resp) { $code = [int]$resp.StatusCode }
    Write-Output ('--- ' + $label + '  => ERR ' + $code + '  ' + $_.Exception.Message)
    if ($resp) { try { $sr = New-Object System.IO.StreamReader($resp.GetResponseStream()); $b=$sr.ReadToEnd(); Write-Output ('    body: ' + $b.Substring(0,[Math]::Min(500,$b.Length))) } catch {} }
  }
}
Hit '/settings/readServoParams' '{"servoNum":6}' 'servoNum=6'
Hit '/settings/readServoParams' '{"key":"H01.17","servoNum":6}' 'key=H01.17 servoNum=6'
Hit '/settings/readServoParams' '{"key":38,"servoNum":6}' 'key=38 servoNum=6'
Hit '/settings/readServoParams' '{"key":"200117","servoNum":6}' 'key=200117 servoNum=6'