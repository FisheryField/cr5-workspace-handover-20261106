echo "=== J1 一次完整 sdo2 ==="
/tmp/ecat_mbx sdo2 eth0 0x3eb 0x6064 0
echo
echo "=== FMMU 表（看 3/4 是否被写上）==="
/tmp/ecat_mbx peek eth0 0x3eb 0x0600 112
