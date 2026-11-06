echo "=== 手工: 写请求(0x6064) 到 SM0 ==="
/tmp/ecat_mbx poke eth0 0x3f0 0x1800 0a000000002300204064600000000000
sleep 0.05
echo "=== 读 0x1a20 长 64 (邮箱应在 +0x10) ==="
/tmp/ecat_mbx peek eth0 0x3f0 0x1a20 64
echo
echo "=== SM 状态 ==="
/tmp/ecat_mbx sregs eth0 0x3f0 | head -3
echo
echo "=== 再读一次 0x1a20 ==="
/tmp/ecat_mbx peek eth0 0x3f0 0x1a20 64
