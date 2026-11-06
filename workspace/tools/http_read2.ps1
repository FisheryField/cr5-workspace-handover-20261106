$base='http://192.168.5.1:22000'
function P($p,$body,$label){
  try { $r=Invoke-WebRequest -Uri ($base+$p) -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 20 -UseBasicParsing; Write-Output ('POST ' + $label + ' -> ' + $r.Content) } catch { Write-Output ('POST ' + $label + ' ERR ' + $_.Exception.Message) }
}
function G($p,$label){
  try { $r=Invoke-WebRequest -Uri ($base+$p) -Method GET -TimeoutSec 20 -UseBasicParsing; Write-Output ('GET  ' + $label + ' -> ' + $r.Content.Substring(0,[Math]::Min(900,$r.Content.Length))) } catch { Write-Output ('GET  ' + $label + ' ERR ' + $_.Exception.Message) }
}
P '/settings/readServoParams' '{"servoNum":6}' 'servoNum=6'
Start-Sleep -Milliseconds 800
G '/settings/readServoParams' 'servoNum=6'
Start-Sleep -Milliseconds 500
G '/settings/readServoParams' 'servoNum=6 again'
Start-Sleep -Milliseconds 500
G '/protocol/exchange' 'exchange head'