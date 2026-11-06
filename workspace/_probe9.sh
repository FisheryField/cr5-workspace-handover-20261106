ls -la /tmp/ecat_zero
md5sum /tmp/ecat_zero
chmod +x /tmp/ecat_zero
echo "=== 当前应用栈 ==="
ps | grep -E "codesys|gcontrol|mTool" | grep -v grep
echo "=== 机器人状态（只读，不停任何进程）==="
date; cat /proc/uptime
