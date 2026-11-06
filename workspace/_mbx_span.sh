echo "=== 跨区读: 起点 0x1a00 长度 512 (覆盖 0x1a00~0x1bff) ==="
/tmp/ecat_mbx peek eth0 0x3f0 0x1a00 512 2>&1 | head -1
echo "=== 起点 0x1a20 长度 512 ==="
/tmp/ecat_mbx peek eth0 0x3f0 0x1a20 512 2>&1 | head -1
echo "=== 起点 0x1a20 长度 48 (跨过 0x1a30 边界) ==="
/tmp/ecat_mbx peek eth0 0x3f0 0x1a20 48 2>&1 | head -3
echo
echo "=== 边界精确定位: 0x1a20 起, 长度 8/16/17/32 ==="
for L in 8 16 17 24 32; do
  printf "  0x1a20 len=%-3s : " $L
  /tmp/ecat_mbx peek eth0 0x3f0 0x1a20 $L 2>&1 | head -1 | sed 's/peek //;s/ pkttype.*//'
done
