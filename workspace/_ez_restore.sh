echo "=== 用 ecat_zero wv 还原 J6 0x1600:00 = 20 ==="
/tmp/ecat_zero wv 8 0x1600 0 20
echo "=== 回读确认 ==="
/tmp/ecat_zero rv 8 0x1600 0
echo
echo "=== 对照: J1(slave 3) 的 0x1600:00 ==="
/tmp/ecat_zero rv 3 0x1600 0
echo
echo "=== 顺便验证 wv/rv 通道可靠性: 读几个对象 ==="
for o in 0x6041 0x6060 0x6061 0x6064 0x607C 0x60B0 0x6098; do
  printf "  J6 %-8s : " $o
  /tmp/ecat_zero rv 8 $o 0 2>&1 | tail -1
done
