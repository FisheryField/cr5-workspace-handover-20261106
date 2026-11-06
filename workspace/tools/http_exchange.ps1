$base='http://192.168.5.1:22000'
foreach ($p in '/protocol/exchange','/settings/controlMode','/protocol/version') {
  foreach ($m in 'GET','POST') {
    try {
      if ($m -eq 'GET') { $r = Invoke-WebRequest -Uri ($base+$p) -Method GET -TimeoutSec 8 -UseBasicParsing }
      else { $r = Invoke-WebRequest -Uri ($base+$p) -Method POST -Body '{}' -ContentType 'application/json' -TimeoutSec 8 -UseBasicParsing }
      Write-Output ('--- ' + $m + ' ' + $p + '  HTTP ' + $r.StatusCode)
      Write-Output ('    ' + $r.Content)
    } catch { Write-Output ('--- ' + $m + ' ' + $p + '  ERR ' + $_.Exception.Message) }
  }
}