chmod +x /tmp/ecat_zero
echo "=== 回零前 ==="
for o in 0x6064 0x607C 0x6060 0x6098 0x1600; do printf "  %s : " $o; /tmp/ecat_zero rv 8 $o 0 2>&1 | tail -1 | sed 's/.*= //'; done
echo
echo "=== 执行 ecat_zero home 8 ==="
/tmp/ecat_zero home 8 2>&1 | head -40
echo
echo "=== 回零后 ==="
for o in 0x6064 0x607C 0x1600; do printf "  %s : " $o; /tmp/ecat_zero rv 8 $o 0 2>&1 | tail -1 | sed 's/.*= //'; done
