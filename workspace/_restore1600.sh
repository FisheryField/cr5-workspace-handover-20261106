echo "=== 还原 J6 0x1600:00 = 20 ==="
for i in 1 2 3 4 5; do
  /tmp/ecat_zero wv 8 0x1600 0 20 >/dev/null 2>&1
  sleep 0.2
  v=$(/tmp/ecat_zero rv 8 0x1600 0 2>&1 | tail -1 | sed 's/.*= //')
  echo "  尝试 $i -> 0x1600:00 = $v"
  [ "$v" = "20" ] && break
done
echo
echo "=== 六轴 0x1600:00 对照 ==="
for s in 3 4 5 6 7 8; do printf "  slave %s : " $s; /tmp/ecat_zero rv $s 0x1600 0 2>&1 | tail -1 | sed 's/.*= //'; done
