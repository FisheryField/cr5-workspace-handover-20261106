echo "=== uptime ==="
uptime
cat /proc/uptime
echo "=== 22000/22002 监听 ==="
netstat -tlnp 2>/dev/null | grep -aE "22000|22002|4840"
echo "=== 关键进程 ==="
ps w 2>/dev/null | grep -aiE "codesys|mTool|gcontrol|logServer" | grep -av grep
echo "=== /tmp 还在吗 ==="
ls -la /tmp/ecat_mbx /tmp/ecat_mb.pcap* 2>/dev/null
