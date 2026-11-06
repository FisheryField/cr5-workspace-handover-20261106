echo "=== J6 (0x3f0) SM 寄存器 ==="
/tmp/ecat_mbx sregs eth0 0x3f0
echo
echo "=== J1 (0x3eb) SM 寄存器 ==="
/tmp/ecat_mbx sregs eth0 0x3eb
echo
echo "=== J6 读邮箱 0x1a30 现状 ==="
/tmp/ecat_mbx peek eth0 0x3f0 0x1a30 32
echo
echo "=== J6 写邮箱 0x1800 现状 ==="
/tmp/ecat_mbx peek eth0 0x3f0 0x1800 32
echo
echo "=== J1 读邮箱 0x1a30 现状 ==="
/tmp/ecat_mbx peek eth0 0x3eb 0x1a30 32
