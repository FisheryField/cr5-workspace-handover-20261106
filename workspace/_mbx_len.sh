echo "=== 同一地址不同长度 ==="
for L in 8 16 64 512; do
  printf "FPRD 0x1a30 len=%-4s : " $L
  /tmp/ecat_mbx peek eth0 0x3f0 0x1a30 $L 2>&1 | head -1
done
for L in 8 16 64 512; do
  printf "FPRD 0x1800 len=%-4s : " $L
  /tmp/ecat_mbx peek eth0 0x3f0 0x1800 $L 2>&1 | head -1
done
echo
echo "=== 写方向 FPWR ==="
printf "FPWR 0x1800  8B : "; /tmp/ecat_mbx poke eth0 0x3f0 0x1800 0000000000000000
printf "FPWR 0x1a30  8B : "; /tmp/ecat_mbx poke eth0 0x3f0 0x1a30 0000000000000000
printf "FPWR 0x0800  8B : "; /tmp/ecat_mbx poke eth0 0x3f0 0x0800 0018000226800100
echo
echo "=== 邻近地址细扫 (每 0x10 一格, 0x1a00~0x1a40) ==="
for o in 0x1a00 0x1a10 0x1a20 0x1a30 0x1a40; do
  printf "  %s : " $o
  /tmp/ecat_mbx peek eth0 0x3f0 $o 8 2>&1 | head -1
done
