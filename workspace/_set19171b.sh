chmod +x /tmp/ecat_zero
echo "=== 写前: J6 0x607C / 0x6064 ==="
/tmp/ecat_zero rv 8 0x607C 0 2>&1 | tail -1
/tmp/ecat_zero rv 8 0x6064 0 2>&1 | tail -1
echo
echo "=== 写入 0x607C = 19171 ==="
/tmp/ecat_zero wv 8 0x607C 0 19171
echo
echo "=== 回读 ==="
/tmp/ecat_zero rv 8 0x607C 0 2>&1 | tail -1
echo
echo "=== 五轴对照 (应仍为 0) ==="
for s in 3 4 5 6 7; do printf "  slave %s : " $s; /tmp/ecat_zero rv $s 0x607C 0 2>&1 | tail -1 | sed 's/.*= //'; done
