$base='http://192.168.5.1:22000'
$b = '{"body":[' + ((1..5 | ForEach-Object { '{"key":"2001' + ('{0:D2}' -f $_) + '","servoNum":6}' }) -join ',') + ']}'
Write-Output ('sending: ' + $b)
try { $r=Invoke-WebRequest -Uri ($base+'/settings/readServoParams') -Method POST -Body $b -ContentType 'application/json' -TimeoutSec 25 -UseBasicParsing; Write-Output ('-> ' + $r.Content) } catch { Write-Output ('ERR ' + $_.Exception.Message) }