
$ErrorActionPreference='Continue'
$u='http://192.168.5.1:22000/settings/readServoParams'
function Hit($m,$b){ try{ $r=Invoke-WebRequest -Uri $u -Method $m -Body $b -ContentType 'application/json' -TimeoutSec 12 -UseBasicParsing; "  [$m] HTTP $($r.StatusCode)  -> $($r.Content)" } catch { "  [$m] ERR $($_.Exception.Message)" } }
$body = '{"body":[{"key":"H01.17","servoNum":"J6"}]}'
$bytes=[System.Text.Encoding]::UTF8.GetBytes($body)
"=== POST body=$body"
Hit 'POST' $bytes
Start-Sleep -Milliseconds 800
"=== GET"
Hit 'GET' $null
"=== POST 第二种 key"
$b2=[System.Text.Encoding]::UTF8.GetBytes('{"body":[{"key":"addr200117","servoNum":"J6"}]}')
Hit 'POST' $b2
Start-Sleep -Milliseconds 800
Hit 'GET' $null
