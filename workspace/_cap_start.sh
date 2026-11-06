echo "=== 磁盘空间 ==="
df -h /tmp /mToolServer /dobot 2>/dev/null | head -10
echo
echo "=== tcpdump 版本 ==="
/mToolServer/tcpdump --version 2>&1 | head -3
echo
echo "=== 现有抓包文件 ==="
ls -la /tmp/*.pcap /dobot/*.pcap 2>/dev/null
echo
echo "=== 启动后台抓包（只抓 <1100 字节的邮箱帧）==="
rm -f /tmp/ecat_mb.pcap
nohup /mToolServer/tcpdump -i eth0 -s 0 -w /tmp/ecat_mb.pcap -C 40 -W 3 "less 1100" > /tmp/tcpdump.log 2>&1 &
echo "pid=$!"
sleep 6
echo "--- 6 秒后 ---"
ls -la /tmp/ecat_mb.pcap* 2>/dev/null
cat /tmp/tcpdump.log 2>/dev/null | head -10
