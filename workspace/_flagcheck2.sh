#!/bin/sh
PID=$(pidof codesyscontrol)
BASE=$(grep -i 'libdataSvr' /proc/$PID/maps | head -1 | cut -d'-' -f1)
B=$((0x$BASE))
for spec in "IsExistSDOWRThd:0x277ed1:1" "SDOWRThd:0x277ed4:4" "SDOWRCount:0x277edc:4" "AllSDOWRStatus:0x277ed8:4"; do
  N=${spec%%:*}; rest=${spec#*:}; OFF=${rest%%:*}; SZ=${rest##*:}
  printf "%-18s = " "$N"
  dd if=/proc/$PID/mem bs=1 skip=$((B+OFF)) count=$SZ 2>/dev/null | od -An -tx1 | tr -d '\n'
  echo
done
echo "--- AllSDOWRInfo 前 64 字节 ---"
dd if=/proc/$PID/mem bs=1 skip=$((B+0x285fe0)) count=64 2>/dev/null | od -A d -tx1
