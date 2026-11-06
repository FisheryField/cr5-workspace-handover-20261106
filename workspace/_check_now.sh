echo '=== 当前六轴伺服版本 ==='
curl -s -X POST http://127.0.0.1:22000/settings/version 2>/dev/null | tr -d ' \t' | grep -E "servo|control"
echo
echo '=== 两进程映射的同一批 SYSV 段（同 inode = 同一块物理内存）==='
GP=$(pidof gcontrol | awk '{print $1}'); CP=$(pidof codesyscontrol | awk '{print $1}')
echo "gcontrol=$GP codesyscontrol=$CP"
echo "--- 共享 inode 及两边的地址 ---"
for i in 851994 720918 0 32769 393228; do
  echo "  inode $i:"
  grep "/SYSV" /proc/$GP/maps 2>/dev/null | grep " $i " | awk '{print "     gcontrol   " $1}'
  grep "/SYSV" /proc/$CP/maps 2>/dev/null | grep " $i " | awk '{print "     codesysctl " $1}'
done
echo
echo '=== 各 SYSV 段的实际大小 ==='
grep "/SYSV" /proc/$CP/maps 2>/dev/null | while read r p o d i n; do
  a=${r%-*}; b=${r#*-}
  printf "  %s  %s KB  %s\n" "$r" "$(( (0x$b - 0x$a) / 1024 ))" "$n"
done
echo
echo '=== gcontrol 的大块可写匿名段（堆等）==='
grep -E "rw-p" /proc/$GP/maps 2>/dev/null | head -20
