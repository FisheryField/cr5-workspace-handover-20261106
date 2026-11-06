echo '=== 相关进程 ==='
ps 2>/dev/null | grep -E "gcontrol|codesys|dataSvr" | grep -v grep
GP=$(pidof gcontrol | awk '{print $1}')
CP=$(pidof codesyscontrol | awk '{print $1}')
echo "gcontrol PID=$GP   codesyscontrol PID=$CP"
echo
echo '=== 采集脚本盯的那几段，gcontrol 有映射吗？ ==='
for A in 73a00000 69239000 692cb000 69b5e000 71d6d000 7276d000 7316d000; do
  g=$(grep -c "^$A" /proc/$GP/maps 2>/dev/null)
  c=$(grep -c "^$A" /proc/$CP/maps 2>/dev/null)
  echo "  $A : gcontrol=$g  codesyscontrol=$c"
done
echo
echo '=== gcontrol 的可写共享段（rw-s）==='
grep -E "rw.s" /proc/$GP/maps 2>/dev/null | head -20
echo
echo '=== codesyscontrol 的可写共享段（rw-s）==='
grep -E "rw.s" /proc/$CP/maps 2>/dev/null | head -20
echo
echo '=== 两进程共享同一批 SYSV 段吗（按 inode 比较）==='
echo "--- gcontrol ---"; grep "/SYSV" /proc/$GP/maps 2>/dev/null | awk '{print $5, $6}' | sort -u | head
echo "--- codesyscontrol ---"; grep "/SYSV" /proc/$CP/maps 2>/dev/null | awk '{print $5, $6}' | sort -u | head
echo
echo '=== gcontrol 的堆/大块可写匿名段 ==='
grep -E "rw-p" /proc/$GP/maps 2>/dev/null | awk '{split($1,a,"-"); sz=(strtonum("0x" a[2])-strtonum("0x" a[1]))/1024; if (sz>1024) printf "  %s  %d KB  %s\n", $1, sz, $6}' | head -15
