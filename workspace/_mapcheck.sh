PID=$(pidof codesyscontrol | awk '{print $1}')
echo "pid=$PID  uptime=$(cat /proc/uptime)"
echo
echo '=== /SYSVe901001b 的所有映射 ==='
grep "SYSVe901001b" /proc/$PID/maps
echo
echo '=== 每个映射在 0x84E24 处的 6 组 (f0,f1) ==='
for L in $(grep "SYSVe901001b" /proc/$PID/maps | awk '{print $1}'); do
  A=$(echo $L | cut -d- -f1); B2=$(echo $L | cut -d- -f2)
  B=$((0x$A)); E=$((0x$B2))
  echo "--- 映射 $A-$B2 (size=$((E-B))) ---"
  for i in 0 1 2 3 4 5; do
    printf "  轴%d  f0=" $((i+1))
    dd if=/proc/$PID/mem bs=1 skip=$((B+0x84E24+40*i)) count=4 2>/dev/null | od -A n -t f4 | tr -d " \n"
    printf "  f1="
    dd if=/proc/$PID/mem bs=1 skip=$((B+0x84E2C+40*i)) count=4 2>/dev/null | od -A n -t f4 | tr -d " \n"
    echo
  done
done
echo
echo '=== 所有 SYSV 段的映射一览 ==='
grep "SYSV" /proc/$PID/maps | awk '{print "  " $1, $5, $6}' | sort -u
