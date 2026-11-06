echo "=== 谁加载了 libdataSvr.so ==="
for p in /proc/[0-9]*; do
  if grep -qas "libdataSvr" $p/maps 2>/dev/null; then
    echo "pid $(basename $p) : $(cat $p/comm 2>/dev/null)"
  fi
done
echo
echo "=== 谁在监听 22000 / 22002 ==="
netstat -tlnp 2>/dev/null | grep -aE "22000|22002|4840"
echo
echo "=== 谁加载了 librobotMap / 其他 dobot so ==="
for p in /proc/[0-9]*; do
  m=$(grep -aso "/dobot/[^ ]*\.so" $p/maps 2>/dev/null | head -3)
  if [ -n "$m" ]; then echo "pid $(basename $p) $(cat $p/comm): $m"; fi
done
