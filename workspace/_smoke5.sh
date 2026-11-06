chmod +x /tmp/ecat_mbx
echo "=== scan J1 H01 组 sub 0..20 ==="
time /tmp/ecat_mbx scan eth0 0x3eb 0x2001 0x2001 20
echo "=== scan J1 0x6060..0x6064 ==="
/tmp/ecat_mbx scan eth0 0x3eb 0x6060 0x6064 0
