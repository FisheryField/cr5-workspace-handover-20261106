echo "=== BEFORE ==="; date; ps | grep -E "codesys|gcontrol" | grep -v grep
echo "=== 停止应用栈 ==="
for p in $(pidof codesyscontrol); do kill $p; done
for p in $(pidof gcontrol); do kill $p; done
sleep 5
ps | grep -E "codesys|gcontrol" | grep -v grep || echo "stopped"
echo "=== eth0 状态 ==="; ifconfig eth0 | head -4
echo "=== 运行只读 SDO 读取工具 ==="
chmod +x /tmp/ecat_read
/tmp/ecat_read eth0 2>&1
echo "READER_RC=$?"
echo "=== READ_DONE ==="