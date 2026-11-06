param([int]$P = 30003)
try {
  $c = New-Object System.Net.Sockets.TcpClient
  $c.Connect('192.168.5.1', $P)
  $s = $c.GetStream()
  $s.ReadTimeout = 2000
  $buf = New-Object byte[] 65536
  $acc = New-Object System.Collections.Generic.List[byte]
  $deadline = (Get-Date).AddSeconds(2)
  while ((Get-Date) -lt $deadline -and $acc.Count -lt 1440*2) {
    try { $n = $s.Read($buf,0,$buf.Length) } catch { break }
    if ($n -le 0) { break }
    $acc.AddRange($buf[0..($n-1)])
  }
  Write-Output ('port ' + $P + ' bytes=' + $acc.Count)
  $b = $acc.ToArray()
  $hex = ($b[0..([Math]::Min(63,$b.Count-1))] | ForEach-Object { $_.ToString('x2') }) -join ' '
  Write-Output ('head64: ' + $hex)
  $n2 = [Math]::Min($b.Count, 400)
  for ($o = 0; $o + 8 -le $n2; $o += 8) {
    $d = [BitConverter]::ToDouble($b, $o)
    $u = [BitConverter]::ToUInt64($b, $o)
    Write-Output ('  off ' + $o.ToString('000') + '  double=' + $d.ToString('0.######') + '   u64=' + $u)
  }
  $c.Close()
} catch { Write-Output ('port ' + $P + ' ERROR ' + $_.Exception.Message) }