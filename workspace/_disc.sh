chmod +x /tmp/ecat_mbx
echo "--- 1) rd 0x6064 ---"
/tmp/ecat_mbx rd eth0 0x3eb 0x6064 0 2>&1 | tail -2
echo "--- 2) scan 0x2001 (H01) ---"
/tmp/ecat_mbx scan eth0 0x3eb 0x2001 0x2001 5
echo "--- 3) rd 0x6064 again ---"
/tmp/ecat_mbx rd eth0 0x3eb 0x6064 0 2>&1 | tail -2
echo "--- 4) scan 0x6060..0x6064 (标准对象, 一定有) ---"
/tmp/ecat_mbx scan eth0 0x3eb 0x6060 0x6064 0
echo "--- 5) rd 0x2001 0 (H01.00) 单条 ---"
/tmp/ecat_mbx rd eth0 0x3eb 0x2001 0 2>&1 | tail -2
