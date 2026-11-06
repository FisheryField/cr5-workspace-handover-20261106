ls -la /tmp/ecat_zero 2>/dev/null || echo MISSING
echo "=== 写前 ==="
/tmp/ecat_zero rv 8 0x607C 0
echo
echo "=== 写入 0x607C = 19171  (目标: 抵消 20.5° 误差) ==="
/tmp/ecat_zero wv 8 0x607C 0 19171
echo
echo "=== 回读确认 ==="
/tmp/ecat_zero rv 8 0x607C 0
echo
echo "=== 其他五轴保持 0 (对照) ==="
for s in 3 4 5 6 7; do printf "  slave %s 0x607C = " $s; /tmp/ecat_zero rv $s 0x607C 0 2>&1 | tail -1 | sed 's/.*= //'; done
