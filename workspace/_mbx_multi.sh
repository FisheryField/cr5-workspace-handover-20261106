echo "=== 单数据报 ==="
/tmp/ecat_mbx peek eth0 0x3f0 0x1a30 512
echo "=== 多数据报 (尾随 BRD) ==="
/tmp/ecat_mbx peekx eth0 0x3f0 0x1a30 512
echo "=== 多数据报 0x1800 ==="
/tmp/ecat_mbx peekx eth0 0x3f0 0x1800 512
echo "=== 多数据报 0x0800 (对照) ==="
/tmp/ecat_mbx peekx eth0 0x3f0 0x0800 8
