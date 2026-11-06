#!/bin/sh
PID=$(pidof codesyscontrol)
BASE=$(grep -i 'libdataSvr' /proc/$PID/maps | head -1 | cut -d'-' -f1)
B=$((0x$BASE))
# r6 = ((0xf9cfe+4) & ~3) + 0x16fc14 ; GOT entry = r6 + 0x35e4
R6=$(( (0xf9cfe+4) & ~3 ))
R6=$(( R6 + 0x16fc14 ))
GOT=$(( R6 + 0x35e4 ))
echo "r6  = 0x$(printf %x $R6)   (库内偏移)"
echo "GOT = 0x$(printf %x $GOT)  (库内偏移)"
ADDR=$(( B + GOT ))
echo "运行时地址 = 0x$(printf %x $ADDR)"
printf "GOT 内容(4 字节指针) = "
dd if=/proc/$PID/mem bs=1 skip=$ADDR count=4 2>/dev/null | od -An -tx1 | tr -d '\n'
echo
P=$(dd if=/proc/$PID/mem bs=1 skip=$ADDR count=4 2>/dev/null | od -An -tu4 | tr -d ' \n')
echo "解析出指针 P = $P"
if [ -n "$P" ] && [ "$P" -gt 0 ] 2>/dev/null; then
  echo "P 在库内偏移 = 0x$(printf %x $((P - B)))"
  printf "标志字节 = "
  dd if=/proc/$PID/mem bs=1 skip=$P count=1 2>/dev/null | od -An -tu1 | tr -d ' \n'
  echo
  echo "--- 顺带看 P 附近 16 字节 ---"
  dd if=/proc/$PID/mem bs=1 skip=$P count=16 2>/dev/null | od -A d -tx1
fi
