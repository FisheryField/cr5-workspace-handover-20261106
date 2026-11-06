$base='http://192.168.5.1:22000'
function P($body,$label){
  try { $r=Invoke-WebRequest -Uri ($base+'/settings/readServoParams') -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 25 -UseBasicParsing; Write-Output ('POST ' + $label + ' -> ' + $r.Content) } catch { Write-Output ('POST ' + $label + ' ERR ' + $_.Exception.Message) }
  Start-Sleep -Milliseconds 1500
}
P '{"body":[{"key":"200118","servoNum":6}]}' 'key=200118(H01.17) servoNum=6'
P '{"body":[{"key":"200101","servoNum":6}]}' 'key=200101(H01.00) servoNum=6'
P '{"body":[{"key":"200118","servoNum":1}]}' 'key=200118 servoNum=1'