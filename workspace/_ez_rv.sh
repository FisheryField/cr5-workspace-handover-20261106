echo "=== 逐索引读 0x6064, 建立 索引 -> 轴 映射 ==="
for s in 1 2 3 4 5 6 7 8 9; do
  printf "  slave %d : " $s
  /tmp/ecat_zero rv $s 0x6064 0 2>&1 | tail -1
done
