$base='http://192.168.5.1:22000'
function P($body,$label){
  try { $r=Invoke-WebRequest -Uri ($base+'/settings/readServoParams') -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 25 -UseBasicParsing; Write-Output ('POST ' + $label + ' -> ' + $r.Content) } catch { Write-Output ('POST ' + $label + ' ERR ' + $_.Exception.Message) }
}
P '{"body":[{"key":"J6","servoNum":38}]}' 'key=J6 servoNum=38(H01.17)'
P '{"body":[{"key":"J1","servoNum":38}]}' 'key=J1 servoNum=38'
P '{"body":[{"key":"J6","servoNum":0}]}'  'key=J6 servoNum=0'
P '{"body":[{"key":"J6","servoNum":1},{"key":"J6","servoNum":2}]}' 'key=J6 servoNum=1,2'