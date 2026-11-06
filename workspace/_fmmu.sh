echo "=== FMMU 寄存器 0x0600..0x067F (每个 16 字节) ==="
/tmp/ecat_mbx peek eth0 0x3eb 0x0600 128
echo
echo "=== 对照 J6 ==="
/tmp/ecat_mbx peek eth0 0x3f0 0x0600 128
