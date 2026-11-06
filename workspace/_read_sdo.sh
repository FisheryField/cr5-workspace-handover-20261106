LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== BEFORE ==="; date
echo "--- 当前伺服版本 ---"
grep -a -A14 "settVersion#4492" "$LOG" 2>/dev/null | tail -16
echo "--- 应用栈 ---"
ps | grep -E "codesys|gcontrol" | grep -v grep
echo
echo "=== 停止应用栈（读完会重启控制器恢复）==="
for p in $(pidof codesyscontrol); do kill $p; done
for p in $(pidof gcontrol); do kill $p; done
sleep 6
ps | grep -E "codesys|gcontrol" | grep -v grep || echo "已停止"
ifconfig eth0 | head -3
chmod +x /tmp/ecat_zero 2>/dev/null

echo
echo "=== [对照 1] 必定存在的 32 位对象 ==="
echo -n "0x1018:01 VendorID   "; /tmp/ecat_zero rv 8 0x1018 1
echo -n "0x6064:00 实际位置    "; /tmp/ecat_zero rv 8 0x6064 0

echo
echo "=== [对照 2] 长度敏感性：0x100A 是 24 字节字符串，用 4 字节读必然长度不符 ==="
echo -n "0x100A:00 软件版本串  "; /tmp/ecat_zero rv 8 0x100A 0
echo -n "0x5000:01 模拟量(16位?) "; /tmp/ecat_zero rv 8 0x5000 1

echo
echo "=== [目标] 零点/编码器参数（3.1.5.0 预期不存在）==="
for a in "0x2000 1" "0x2001 14" "0x2001 18" "0x200C 3" "0x200D 8" "0x200D 9"; do
  set -- $a
  echo -n "slave8 $1:$2  "; /tmp/ecat_zero rv 8 $1 $2
done

echo
echo "=== [全轴扫描] 0x2001:18 编码器位置角 ==="
for s in 3 4 5 6 7 8; do echo -n "slave $s  "; /tmp/ecat_zero rv $s 0x2001 18; done

echo
echo "=== DONE ==="
date
