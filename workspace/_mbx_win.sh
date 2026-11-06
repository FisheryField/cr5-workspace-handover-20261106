echo "=== SM1 直读 0x1a30 (预期被拒) ==="
/tmp/ecat_mbx peek eth0 0x3eb 0x1a30 16 2>&1 | head -1
echo "=== 开窗读 0x1a20 len=48, 看 +0x10 处有没有刚才那条应答 ==="
/tmp/ecat_mbx peek eth0 0x3eb 0x1a20 48
echo "=== 开窗读 0x1a00 len=96 ==="
/tmp/ecat_mbx peek eth0 0x3eb 0x1a00 96
echo "=== 当前 SM 状态 ==="
/tmp/ecat_mbx sregs eth0 0x3eb | head -3
