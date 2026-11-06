echo "=== SM 寄存器现状 ==="
/tmp/ecat_mbx sregs eth0 0x3eb | head -3
echo "=== AL 状态 ==="
/tmp/ecat_mbx peek eth0 0x3eb 0x0130 8
echo "=== 单条 rd 还能用吗 ==="
/tmp/ecat_mbx rd eth0 0x3eb 0x6064 0
echo "=== 手工 SM 释放 + 单条扫描 ==="
/tmp/ecat_mbx poke eth0 0x3eb 0x080E 00
/tmp/ecat_mbx poke eth0 0x3eb 0x080E 01
/tmp/ecat_mbx rd eth0 0x3eb 0x6064 0
