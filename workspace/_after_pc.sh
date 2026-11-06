chmod +x /tmp/ecat_zero
echo "=== 断电重启后的当前值 ==="
for o in 0x607C 0x6064 0x6063 0x60B0; do printf "  J6 %s : " $o; /tmp/ecat_zero rv 8 $o 0 2>&1 | tail -1; done
echo
echo "=== 还原 J6 0x607C -> 0 ==="
/tmp/ecat_zero wv 8 0x607C 0 0
/tmp/ecat_zero rv 8 0x607C 0
echo
echo "=== 其他五轴 0x607C (应为 0) ==="
for s in 3 4 5 6 7; do printf "  slave %s : " $s; /tmp/ecat_zero rv $s 0x607C 0 2>&1 | tail -1; done
echo
echo "=== 六轴 0x6064 对照 ==="
for s in 3 4 5 6 7 8; do printf "  slave %s : " $s; /tmp/ecat_zero rv $s 0x6064 0 2>&1 | tail -1; done
