#!/bin/sh
PID=$(pidof codesyscontrol)
BASE=$(grep -i 'libdataSvr' /proc/$PID/maps | head -1 | cut -d'-' -f1)
B=$((0x$BASE))
echo "=== libdataSvr 全部映射（确认 rw 段范围）==="
grep -i 'libdataSvr' /proc/$PID/maps
echo
# add r6, pc 在 0xf9d08 → PC=(0xf9d08+4)&~3 = 0xf9d0c
R6=$(( (0xf9d08+4) & ~3 ))
R6=$(( R6 + 0x16fc14 ))
GOT=$(( R6 + 0x35e4 ))
echo "r6  = 0x$(printf %x $R6)"
echo "GOT 库内偏移 = 0x$(printf %x $GOT)"
ADDR=$(( B + GOT ))
echo "运行时地址 = 0x$(printf %x $ADDR)"
printf "GOT 内容 = "
dd if=/proc/$PID/mem bs=1 skip=$ADDR count=4 2>/dev/null | od -An -tx1 | tr -d '\n'
echo
P=$(dd if=/proc/$PID/mem bs=1 skip=$ADDR count=4 2>/dev/null | od -An -tu4 | tr -d ' \n')
echo "P = 0x$(printf %x $P)"
if [ -n "$P" ]; then
  echo "P 相对映射: r-x 段 76968000-76bbf000 / rw 段 76bce000-76bd6000"
  printf "P 处字节 = "
  dd if=/proc/$PID/mem bs=1 skip=$P count=1 2>/dev/null | od -An -tu1 | tr -d ' \n'
  echo
fi
echo
echo "=== 用符号表偏移直接读几个候选标志 ==="
for off in 0x277ed1 0x277ed4 0x277ed8 0x277edc; do
  printf "off=%-10s = " "$off"
  dd if=/proc/$PID/mem bs=1 skip=$((B+off)) count=4 2>/dev/null | od -An -tx1 | tr -d '\n'
  echo
done
