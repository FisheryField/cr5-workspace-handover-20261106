chmod +x /tmp/ecat_mbx
echo "=== SM 状态（重启后，全新）==="
/tmp/ecat_mbx sregs eth0 0x3f0 | head -3
echo "---"
/tmp/ecat_mbx sregs eth0 0x3eb | head -3
echo
echo "=== 第1次: J1 读 0x6064 ==="
/tmp/ecat_mbx rd eth0 0x3eb 0x6064 0
echo "=== 第2次: J1 读 0x6063 ==="
/tmp/ecat_mbx rd eth0 0x3eb 0x6063 0
echo "=== 第3次: J1 读 0x607C ==="
/tmp/ecat_mbx rd eth0 0x3eb 0x607C 0
