ls /tmp/ecat_zero >/dev/null 2>&1 || { rscp 2>/dev/null; }
chmod +x /tmp/ecat_zero 2>/dev/null
echo "=== 回零前 ==="
/tmp/ecat_zero rv 8 0x6064 0
/tmp/ecat_zero rv 8 0x607C 0
/tmp/ecat_zero rv 8 0x6060 0
/tmp/ecat_zero rv 8 0x6098 0
echo
echo "=== 执行 ecat_zero home 8 ==="
/tmp/ecat_zero home 8 2>&1
echo
echo "=== 回零后 ==="
/tmp/ecat_zero rv 8 0x6064 0
/tmp/ecat_zero rv 8 0x607C 0
/tmp/ecat_zero rv 8 0x1600 0
