echo "=== J6 (站 0x3f0 = 1008, 伺服 3.1.5.0) ==="
/tmp/ecat_mbx rd eth0 0x3f0 0x6064 0
echo "rc=$?"
/tmp/ecat_mbx rd eth0 0x3f0 0x6063 0
echo "rc=$?"
/tmp/ecat_mbx rd eth0 0x3f0 0x607C 0
echo "rc=$?"
echo
echo "=== J1 (站 0x3eb = 1003, 伺服 3.2.D.8) ==="
/tmp/ecat_mbx rd eth0 0x3eb 0x6064 0
echo "rc=$?"
/tmp/ecat_mbx rd eth0 0x3eb 0x607C 0
echo "rc=$?"
