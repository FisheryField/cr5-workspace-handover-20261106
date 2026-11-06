param([string]$H = '192.168.5.1', [int]$P = 29999, [string[]]$Cmds = @('GetAngle()'))
foreach ($cmd in $Cmds) {
  try {
    $c = New-Object System.Net.Sockets.TcpClient
    $c.Connect($H, $P)
    $s = $c.GetStream()
    $s.ReadTimeout = 1500
    $buf = New-Object byte[] 8192
    Start-Sleep -Milliseconds 250
    $greet = ''
    while ($s.DataAvailable) { $n = $s.Read($buf,0,8192); if ($n -le 0) { break }; $greet += [Text.Encoding]::ASCII.GetString($buf,0,$n) }
    $nl = [string][char]13 + [string][char]10
    $w = [Text.Encoding]::ASCII.GetBytes($cmd + $nl)
    $s.Write($w,0,$w.Length); $s.Flush()
    Start-Sleep -Milliseconds 350
    $resp = ''
    while ($s.DataAvailable) { $n = $s.Read($buf,0,8192); if ($n -le 0) { break }; $resp += [Text.Encoding]::ASCII.GetString($buf,0,$n) }
    Write-Output ('CMD ' + $cmd + ' -> greet[' + $greet.Trim() + '] resp: ' + $resp.Trim())
    $c.Close()
  } catch {
    Write-Output ('CMD ' + $cmd + ' -> ERROR ' + $_.Exception.Message)
  }
}