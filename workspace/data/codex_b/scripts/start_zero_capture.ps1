param([string]$Tag = "zero32_$(Get-Date -Format yyyyMMdd_HHmmss)")
$remote = "/tmp/$Tag.sh"
Write-Host "先把 remote_zero_capture.sh 复制到控制柜："
Write-Host "Get-Content .\remote_zero_capture.sh | ssh root@192.168.5.1 'cat > $remote'"
Write-Host "然后启动采集："
Write-Host "ssh root@192.168.5.1 'chmod 700 $remote; nohup $remote $Tag >/tmp/${Tag}.launcher.log 2>&1 &'"
Write-Host "采集运行约 60 秒；在这 60 秒内完成一次标零。"
Write-Host "完成后取回："
Write-Host "scp root@192.168.5.1:/tmp/$Tag.tar.gz .\dobot-evidence-20260922\"
