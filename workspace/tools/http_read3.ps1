$base='http://192.168.5.1:22000'
function P($body,$label){
  try { $r=Invoke-WebRequest -Uri ($base+'/settings/readServoParams') -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 25 -UseBasicParsing; Write-Output ('POST ' + $label + ' -> ' + $r.Content) } catch { Write-Output ('POST ' + $label + ' ERR ' + $_.Exception.Message) }
}
P '{"key":"J6","servoNum":6}' 'key=J6 servoNum=6'
Start-Sleep -Milliseconds 1500
P '{"key":"J6"}' 'key=J6 only'
Start-Sleep -Milliseconds 1500
P '{"body":[{"key":"J6","servoNum":6}]}' 'body=[{key:J6,servoNum:6}]'