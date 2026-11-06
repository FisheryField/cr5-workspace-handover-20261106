echo "=== 新的 codesyscontrol pid ==="
PID=$(pidof codesyscontrol 2>/dev/null || ps w | grep -a codesyscontrol | grep -av grep | awk '{print $1}' | head -1)
echo "PID=$PID"
echo "uptime: $(uptime)"
echo
echo "=== 从站 AL 状态是否回到 OP (0x08) ==="
for st in 0x3eb 0x3ec 0x3f0; do
  printf "  st=%s  AL=0x%s\n" $st "$(dd if=/dev/mem bs=1 skip=0 count=0 2>/dev/null; echo NA)"
done
echo
echo "=== 内存映射概况 (按大小排序 top15) ==="
awk '{split($1,a,"-"); sz=(strtonum("0x" a[2])-strtonum("0x" a[1]))/1024; printf "%8d KB  %s  %s\n", sz, $1, $6}' /proc/$PID/maps 2>/dev/null | sort -rn | head -15
