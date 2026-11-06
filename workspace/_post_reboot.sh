echo "=== 机器人状态 ==="
wget -q -O - http://127.0.0.1:22000/settings/version 2>/dev/null | head -c 300
echo
echo "=== SM 状态（重启后）==="
/tmp/ecat_mbx sregs eth0 0x3f0 | head -3
/tmp/ecat_mbx sregs eth0 0x3eb | head -3
echo
echo "=== 第一次读 J1 0x6064 ==="
/tmp/ecat_mbx rd eth0 0x3eb 0x6064 0
echo
echo "=== 紧接着第二次读 J1 0x6063 ==="
/tmp/ecat_mbx rd eth0 0x3eb 0x6063 0
