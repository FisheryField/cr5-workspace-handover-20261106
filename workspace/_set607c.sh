chmod +x /tmp/ecat_zero
echo "=== 写前 ==="
/tmp/ecat_zero rv 8 0x607C 0
/tmp/ecat_zero rv 8 0x6064 0
echo
echo "=== 写 0x607C = -16425 ==="
/tmp/ecat_zero wv 8 0x607C 0 -16425
echo
echo "=== 回读 ==="
/tmp/ecat_zero rv 8 0x607C 0
/tmp/ecat_zero rv 8 0x6064 0
echo
echo "=== 六个轴一起设, 保持一致的处置? 否 — 只动 J6 ==="
/tmp/ecat_zero rv 3 0x607C 0
