echo "=== 用控制器的 idx 0x8c 读 J1 的 0x1a30 ==="
ECAT_IDX=0x8c /tmp/ecat_mbx peek eth0 0x3eb 0x1a30 512 2>&1 | head -1
echo "=== 多个 idx 值 ==="
for ix in 0x00 0x01 0x81 0x8a 0x8c 0x8b 0xae 0xff; do
  printf "  idx=%-5s : " $ix
  ECAT_IDX=$ix /tmp/ecat_mbx peek eth0 0x3eb 0x1a30 8 2>&1 | head -1 | sed 's/peek //;s/ pkttype.*//'
done
echo "=== 对照: 0x0800 用 idx=0x8c ==="
ECAT_IDX=0x8c /tmp/ecat_mbx peek eth0 0x3eb 0x0800 8 2>&1 | head -1
