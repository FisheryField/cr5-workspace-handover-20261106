echo "=== 还原 J6 0x607C -> 0 ==="
/tmp/ecat_zero wv 8 0x607C 0 0
echo "--- 回读 ---"
/tmp/ecat_zero rv 8 0x607C 0
/tmp/ecat_zero rv 8 0x6064 0
echo
echo "=== 对照: 其他五轴的 0x607C (应为 0, 未动过) ==="
for s in 3 4 5 6 7; do printf "  slave %s : " $s; /tmp/ecat_zero rv $s 0x607C 0 2>&1 | tail -1; done
echo
echo "=== 顺便再看一眼 J6 的几个关键对象 ==="
for o in 0x6063 0x6064 0x60B0 0x607C; do printf "  %s : " $o; /tmp/ecat_zero rv 8 $o 0 2>&1 | tail -1; done
