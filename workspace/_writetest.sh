PID=$(pidof codesyscontrol | awk '{print $1}')
SEL=$(grep "SYSVe901001b" /proc/$PID/maps | head -1)
B=$((0x$(echo "$SEL" | cut -d- -f1)))
echo "pid=$PID base=0x$(printf %x $B)"
# 选一个确认是零的位置：segment 偏移 0x90000（第 144 页）
T=$((B+0x90000))
echo "目标 = base+0x90000"
echo "-- 写前 32 字节 --"
dd if=/proc/$PID/mem bs=1 skip=$T count=32 2>/dev/null | od -A n -t x1
echo "-- 写标记 DE AD BE EF --"
printf '\336\255\276\357' | dd of=/proc/$PID/mem bs=1 seek=$T conv=notrunc 2>&1
echo "-- 立刻回读 32 字节 --"
dd if=/proc/$PID/mem bs=1 skip=$T count=32 2>/dev/null | od -A n -t x1
sleep 2
echo "-- 2 秒后再读 --"
dd if=/proc/$PID/mem bs=1 skip=$T count=32 2>/dev/null | od -A n -t x1
echo
echo "== 对照：另一个位置 base+0xA0000 =="
T2=$((B+0xA0000))
printf '\021\062\123\144' | dd of=/proc/$PID/mem bs=1 seek=$T2 conv=notrunc 2>&1
dd if=/proc/$PID/mem bs=1 skip=$T2 count=16 2>/dev/null | od -A n -t x1
echo
echo "== 进程状态 =="
ps | grep codesyscontrol | grep -v grep || echo "!! 已退出"
