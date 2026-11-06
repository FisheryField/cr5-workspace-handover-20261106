chmod +x /tmp/ecat_mbx
echo "=== J1 H01 组 sub 0..20 ==="
/tmp/ecat_mbx scan eth0 0x3eb 0x2001 0x2001 20
