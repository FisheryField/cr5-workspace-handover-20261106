chmod +x /tmp/ecat_mbx
echo "=== 冒烟: J1 H01 组 (0x2001, sub 0..20) ==="
time /tmp/ecat_mbx scan eth0 0x3eb 0x2001 0x2001 20
