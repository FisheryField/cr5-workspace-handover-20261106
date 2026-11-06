PID=$(pidof codesyscontrol | awk '{print $1}')
SEL=$(grep "SYSVe901001b" /proc/$PID/maps | head -1)
B=$((0x$(echo "$SEL" | cut -d- -f1)))
for O in 0x90000 0xA0000; do
  printf '\000\000\000\000' | dd of=/proc/$PID/mem bs=1 seek=$((B+O)) conv=notrunc 2>/dev/null
done
echo '已清除测试标记:'
dd if=/proc/$PID/mem bs=1 skip=$((B+0x90000)) count=8 2>/dev/null | od -A n -t x1
dd if=/proc/$PID/mem bs=1 skip=$((B+0xA0000)) count=8 2>/dev/null | od -A n -t x1
echo '进程:'; ps | grep codesyscontrol | grep -v grep
