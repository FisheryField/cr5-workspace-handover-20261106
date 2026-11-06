$base='http://192.168.5.1:22000'
function P($body,$label){
  try { $r=Invoke-WebRequest -Uri ($base+'/settings/readServoParams') -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 25 -UseBasicParsing; Write-Output ('POST ' + $label + ' -> ' + $r.Content) } catch { Write-Output ('POST ' + $label + ' ERR ' + $_.Exception.Message) }
  Start-Sleep -Milliseconds 1200
}
P '{"body":[{"key":"200117","servoNum":6}]}' 'body=[key=200117 servoNum=6]'
P '{"body":[{"key":"200117","servoNum":1}]}' 'body=[key=200117 servoNum=1]'
P '{"body":[{"key":"J6","servoNum":6}]}'      'body=[key=J6 servoNum=6]'
P '{"body":[{"key":"H01.17","servoNum":6}]}' 'body=[key=H01.17 servoNum=6]'